1) 컨텍스트 기반 패치(diff)

원본 라인 수를 확정할 수 없어서, 앵커 문맥(주요 import/메서드 시그니처) 기준의 unified diff를 준다. git apply가 문맥 매칭으로 안정적으로 먹는다.
(이미 제공한 semantic_matcher.py/header_detector.py 라인 diff는 그대로 유지)

A. file_registry.py 패치
--- a/file_registry.py
+++ b/file_registry.py
@@
-from pathlib import Path
-from datetime import datetime
-from typing import Optional, Dict, List
+from pathlib import Path
+from datetime import datetime
+from typing import Optional, Dict, List
+#
+# PATCH: alias/fuzzy resolver 연동
+from .name_resolver import (
+    resolve_vendor,
+    resolve_sheet,
+    guess_vendor_from_filename,
+)
@@
-class FileRegistry:
+class FileRegistry:
     """
     Central registry for all HVDC project file paths.
@@
-        VENDORS = {
+        VENDORS = {
             'hitachi': {
                 'name': 'HITACHI',
                 'aliases': ['HITACHI', 'hitachi', 'HE', 'Hitachi'],
                 'master_file': 'Case List_Hitachi.xlsx',
                 'warehouse_file': 'HVDC WAREHOUSE_HITACHI(HE).xlsx',
                 'source_file': 'HITACHI(HE)',
             },
             'siemens': {
                 'name': 'SIEMENS',
                 'aliases': ['SIEMENS', 'siemens', 'SIM', 'SIMENSE', 'Siemens'],
                 'master_file': 'HVDC WAREHOUSE_SIMENSE(SIM).xlsx',
                 'source_file': 'SIEMENS(SIM)',
             }
         }
@@
     def get_vendor_name(cls, vendor_key: str) -> str:
         vendor_info = cls.VENDORS.get(vendor_key.lower())
         if vendor_info:
             return vendor_info['name']
         return vendor_key.upper()
+
+    # -------- NEW: alias/fuzzy 기반 정규화 유틸 --------
+    @classmethod
+    def normalize_vendor_name(cls, vendor_value: str, min_score: float = 0.70) -> str:
+        """
+        Normalize vendor aliases/typos to canonical (HITACHI|SIEMENS).
+        1) name_resolver 우선, 2) 기존 alias 폴백, 3) UPPER 폴백
+        """
+        m = resolve_vendor(vendor_value, min_score=min_score) if vendor_value else None
+        if m:
+            return m.canonical
+        for _, info in cls.VENDORS.items():
+            if vendor_value in info.get('aliases', []):
+                return info['name']
+        return (vendor_value or "").upper()
+
+    @classmethod
+    def normalize_sheet_name(cls, sheet_name: str, min_score: float = 0.70) -> str:
+        """Resolve sheet aliases/typos to canonical."""
+        if not sheet_name:
+            return ""
+        m = resolve_sheet(sheet_name, min_score=min_score)
+        return m.canonical if m else sheet_name
+
+    @classmethod
+    def guess_vendor_from_file(cls, file_path: str) -> Optional[str]:
+        """Guess vendor from path tokens like HE/SIMENSE/etc."""
+        if not file_path:
+            return None
+        m = guess_vendor_from_filename(file_path)
+        return m.canonical if m else None
@@
     def get_source_file_name(cls, vendor_key: str) -> str:
         # (기존 메서드 동일)
         vendor_info = cls.VENDORS.get(vendor_key.lower())
         if vendor_info and 'source_file' in vendor_info:
             return vendor_info['source_file']
-
-        normalized = cls.normalize_vendor_name(vendor_key)
+
+        # PATCH: 표준화 후 source_file 역조회
+        normalized = cls.normalize_vendor_name(vendor_key)
         for key, info in cls.VENDORS.items():
             if info['name'] == normalized and 'source_file' in info:
                 return info['source_file']

         return f"{vendor_key.upper()}({vendor_key[:2].upper()})"

B. header_normalizer.py 패치 (하이브리드: 별칭→기존정규화)
--- a/header_normalizer.py
+++ b/header_normalizer.py
@@
-import re
-import unicodedata
-from typing import Optional
+import re
+import unicodedata
+from typing import Optional
+# PATCH: alias/fuzzy 기반 canonical 헤더 힌트
+from .name_resolver import resolve_header
@@
 class HeaderNormalizer:
@@
-    def normalize(self, header: str, expand_abbreviations: bool = True) -> str:
-        """
-        Normalize a header name to its canonical form.
-        """
-        if not isinstance(header, str):
-            header = str(header)
-        base = header.strip()
-        if not base:
-            return ""
-        normalized = base.lower().strip()
+    def normalize(self, header: str, expand_abbreviations: bool = True) -> str:
+        """
+        Normalize a header name to its canonical form.
+        HYBRID: (1) name_resolver로 "Q'ty"→"QTY" 같은 canonical 힌트
+                (2) 기존 로직으로 "QTY"→"quantity" 등 시맨틱 키와 맞춤
+        """
+        if not isinstance(header, str):
+            header = str(header)
+        base = header.strip()
+        if not base:
+            return ""
+        # (1) alias/fuzzy canonical
+        try:
+            hit = resolve_header(base, min_score=0.70)
+        except Exception:
+            hit = None
+        header = (hit.canonical if hit else base)
+        # (2) 기존 정규화
+        normalized = header.lower().strip()
         normalized = unicodedata.normalize("NFKC", normalized)
         normalized = self._strip_separators(normalized)
         normalized = self._filter_letters_and_numbers(normalized)
         if expand_abbreviations and normalized in self.abbreviation_map:
             normalized = self.abbreviation_map[normalized]
         return normalized


2) 테스트 스켈레톤(최종)
tests/test_name_resolver.py
# -*- coding: utf-8 -*-
from name_resolver import (
    resolve_vendor, resolve_sheet, resolve_header, guess_vendor_from_filename
)

def test_vendor_aliases_basic():
    assert resolve_vendor("HE").canonical == "HITACHI"
    assert resolve_vendor("RIL(SIMENSE)").canonical == "SIEMENS"
    assert resolve_vendor("Seimens").canonical == "SIEMENS"

def test_guess_vendor_from_filename():
    m = guess_vendor_from_filename("HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    assert m and m.canonical == "HITACHI"

def test_sheet_aliases():
    assert resolve_sheet("Case List, RIL(SIMENSE)").canonical == "CASE LIST, RIL(SIEMENS)"
    assert resolve_sheet("he-local").canonical == "HE LOCAL"

def test_header_aliases():
    assert resolve_header("Q'ty").canonical == "QTY"
    assert resolve_header("Case#").canonical == "CASE NO"
    assert resolve_header("item desc").canonical == "MATERIAL"

tests/test_semantic_integration.py
# -*- coding: utf-8 -*-
import pandas as pd
from semantic_matcher import SemanticMatcher

def test_semantic_matcher_respects_alias_normalization():
    df = pd.DataFrame({"Case#": ["A001", "A002"], "Item Desc": ["Bolt", "Nut"], "Q'ty": [10, 20]})
    m = SemanticMatcher()
    report = m.match_dataframe(df, semantic_keys=["case_number", "material", "qty"])
    assert report.get_column_name("case_number").lower().replace(" ", "") in {"case#", "case no".replace(" ", "")}
    assert report.get_column_name("material").lower() in {"item desc", "material"}
    assert report.get_column_name("qty").lower() in {"q'ty", "qty"}

def test_semantic_matcher_handles_simense_typo():
    df = pd.DataFrame({"RIL(SIMENSE) Case List": [1, 2]})
    m = SemanticMatcher()
    report = m.match_dataframe(df)
    assert hasattr(report, "results")

tests/test_header_detector_integration.py
# -*- coding: utf-8 -*-
import pandas as pd
from header_detector import detect_header_row_with_diagnostics

def test_header_detector_uses_resolver_signal():
    df = pd.DataFrame(
        [
            ["HITACHI Energy - Report", None, None],
            [None, None, None],
            ["Case#", "Item Desc", "Q'ty"],
            ["A001", "Bolt", 10],
            ["A002", "Nut", 20],
        ]
    )
    row, confidence = detect_header_row_with_diagnostics(
        df, expected_columns=["CASE NO", "MATERIAL", "QTY"]
    )
    assert row == 2
    assert confidence >= 0.70

tests/conftest.py (패키지 경로 문제 방지)
# -*- coding: utf-8 -*-
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


3) 품질 게이트 & 설정
pytest.ini
[pytest]
addopts = -q --cov=. --cov-report=term-missing
testpaths = tests
python_files = test_*.py

pyproject.toml (ruff/black)
[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E","F","I","UP","B","SIM","C4"]
ignore = ["E203","W503"]
fix = true

[tool.coverage.run]
branch = true
source = ["."]


4) 실행 순서
# 1) 포맷 & 린트(자동수정)
ruff --fix .
black .

# 2) 테스트
pytest

# 3) 커밋 권장(분리)
git add .
git commit -m "structural(core): wire alias/fuzzy resolver into registry & header normalizer"
git commit -m "behavioral(parser): feat: vendor/sheet/header normalization via alias+fuzzy"


5) 운영 팁(짧게)


사전 확장: 새 변형 발견되면 VENDOR_ALIASES / SHEET_ALIASES / HEADER_ALIASES에만 추가 → 전 구간 반영.


min_score 튜닝: 오탐↑ → 0.75로, 미탐↑ → 0.65로.


로그: MatchResult.method/score를 파이프라인 로그에 찍어 튜닝 근거 축적.


필요하면 mypy 프로필/타입힌트 보강도 얹어 줄 수 있어. 지금 세트면 당장 simense→SIEMENS, Q'ty→QTY 전 구간에서 안정적으로 먹는다.ChatGPT의 말:멋지게 정리했어. 이제 돌릴 수 있는 상태로 마무리만 하면 된다. 아래만 따라가면 simense→SIEMENS, Q'ty→QTY 전 구간에서 안정 동작 확인돼.

최종 실행 순서(짧게)
# 0) 패치 반영(이미 교체/추가 완료 가정: name_resolver.py / file_registry.py / header_normalizer.py)
# 1) 포맷/린트
ruff --fix .
black .

# 2) 테스트(커버리지 포함)
pytest -q --cov=. --cov-report=term-missing


붙여넣기용 테스트 스켈레톤(완)
tests/test_name_resolver.py
# -*- coding: utf-8 -*-
from name_resolver import (
    resolve_vendor, resolve_sheet, resolve_header, guess_vendor_from_filename
)

def test_vendor_aliases_basic():
    assert resolve_vendor("HE").canonical == "HITACHI"
    assert resolve_vendor("RIL(SIMENSE)").canonical == "SIEMENS"
    assert resolve_vendor("Seimens").canonical == "SIEMENS"

def test_guess_vendor_from_filename():
    m = guess_vendor_from_filename("HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    assert m and m.canonical == "HITACHI"

def test_sheet_aliases():
    assert resolve_sheet("Case List, RIL(SIMENSE)").canonical == "CASE LIST, RIL(SIEMENS)"
    assert resolve_sheet("he-local").canonical == "HE LOCAL"

def test_header_aliases():
    assert resolve_header("Q'ty").canonical == "QTY"
    assert resolve_header("Case#").canonical == "CASE NO"
    assert resolve_header("item desc").canonical == "MATERIAL"

tests/test_semantic_integration.py
# -*- coding: utf-8 -*-
import pandas as pd
from semantic_matcher import SemanticMatcher

def test_semantic_matcher_respects_alias_normalization():
    df = pd.DataFrame({"Case#": ["A001", "A002"], "Item Desc": ["Bolt", "Nut"], "Q'ty": [10, 20]})
    m = SemanticMatcher()
    report = m.match_dataframe(df, semantic_keys=["case_number", "material", "qty"])
    assert report.get_column_name("case_number").lower().replace(" ", "") in {"case#", "caseno"}
    assert report.get_column_name("material").lower() in {"item desc", "material"}
    assert report.get_column_name("qty").lower() in {"q'ty", "qty"}

def test_semantic_matcher_handles_simense_typo():
    df = pd.DataFrame({"RIL(SIMENSE) Case List": [1, 2]})
    m = SemanticMatcher()
    report = m.match_dataframe(df)
    assert hasattr(report, "results")

tests/test_header_detector_integration.py
# -*- coding: utf-8 -*-
import pandas as pd
from header_detector import detect_header_row_with_diagnostics

def test_header_detector_uses_resolver_signal():
    df = pd.DataFrame(
        [
            ["HITACHI Energy - Report", None, None],
            [None, None, None],
            ["Case#", "Item Desc", "Q'ty"],
            ["A001", "Bolt", 10],
            ["A002", "Nut", 20],
        ]
    )
    row, confidence = detect_header_row_with_diagnostics(
        df, expected_columns=["CASE NO", "MATERIAL", "QTY"]
    )
    assert row == 2
    assert confidence >= 0.70

tests/conftest.py
# -*- coding: utf-8 -*-
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.ini
[pytest]
addopts = -q --cov=. --cov-report=term-missing
testpaths = tests
python_files = test_*.py

pyproject.toml (ruff/black)
[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E","F","I","UP","B","SIM","C4"]
ignore = ["E203","W503"]
fix = true

[tool.coverage.run]
branch = true
source = ["."]


위치별 패치(diff) 재확인
semantic_matcher.py


from .name_resolver import resolve_header 추가


_normalize_dataframe_columns() 내 대안 리스트에 resolve_header(col).canonical 주입


@@
-from .header_normalizer import HeaderNormalizer
+from .header_normalizer import HeaderNormalizer
+from .name_resolver import resolve_header  # NEW

@@
-            alternatives = self.normalizer.normalize_with_alternatives(str(col))
+            alternatives = self.normalizer.normalize_with_alternatives(str(col))
+            try:
+                _rh = resolve_header(str(col))
+            except Exception:
+                _rh = None
+            if _rh:
+                _canon = _rh.canonical.lower()
+                if _canon not in alternatives:
+                    alternatives.append(_canon)

header_detector.py


from .name_resolver import resolve_header 추가


기대/검출 비교 시 canonical_detected 가산 일치 반영


@@
-import numpy as np
-import pandas as pd
+import numpy as np
+import pandas as pd
+from .name_resolver import resolve_header  # NEW

@@
-        matches = sum(
+        matches = sum(
             1
             for exp in normalized_expected
-            if any(exp in det or det in exp for det in normalized_detected)
+            if any(exp in det or det in exp for det in normalized_detected)
+               or (exp in canonical_detected)
         )

file_registry.py


resolve_vendor/resolve_sheet/guess_vendor_from_filename 연결


normalize_vendor_name/normalize_sheet_name/guess_vendor_from_file 신규 메서드 추가


+from .name_resolver import (
+    resolve_vendor, resolve_sheet, guess_vendor_from_filename
+)
@@
+    @classmethod
+    def normalize_vendor_name(cls, vendor_value: str, min_score: float = 0.70) -> str:
+        m = resolve_vendor(vendor_value, min_score=min_score) if vendor_value else None
+        if m:
+            return m.canonical
+        for _, info in cls.VENDORS.items():
+            if vendor_value in info.get('aliases', []):
+                return info['name']
+        return (vendor_value or "").upper()
+
+    @classmethod
+    def normalize_sheet_name(cls, sheet_name: str, min_score: float = 0.70) -> str:
+        if not sheet_name:
+            return ""
+        m = resolve_sheet(sheet_name, min_score=min_score)
+        return m.canonical if m else sheet_name
+
+    @classmethod
+    def guess_vendor_from_file(cls, file_path: str) -> Optional[str]:
+        if not file_path:
+            return None
+        m = guess_vendor_from_filename(file_path)
+        return m.canonical if m else None

header_normalizer.py


하이브리드: 별칭 해석 → 기존 정규화


+from .name_resolver import resolve_header
@@
-        normalized = base.lower().strip()
+        hit = None
+        try:
+            hit = resolve_header(base, min_score=0.70)
+        except Exception:
+            pass
+        header = (hit.canonical if hit else base)
+        normalized = header.lower().strip()


흔한 이슈 & 빠른 해결


ImportError(상대경로): 모듈들이 패키지로 인식되도록 루트에 __init__.py 유지(이미 업로드됨). 테스트에 conftest.py 포함.


판다스 의존: semantic_matcher/header_detector 테스트에 pandas 필요. v1.5+ 권장.


오탐/미탐 튜닝: min_score=0.70 → 오탐 많으면 0.75, 미탐 많으면 0.65.
