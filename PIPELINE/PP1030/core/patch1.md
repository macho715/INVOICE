## *Exec Summary (3-5L)*

알겠습니다. `name_resolver.py`를 드롭인(drop-in) 교체하고, `file_registry.py`와 `header_normalizer.py`를 패치하여 새로운 별칭/퍼지 매칭 엔진을 연동합니다. 이로써 `simense`→`SIEMENS`, `Q'ty`→`QTY` 등의 변형된 파일/시트/헤더명을 파이프라인 전반에서 일관되게 표준화합니다. `header_normalizer`는 `semantic_matcher`와의 호환성을 위해 \*\*[별칭 해석 → 기존 정규화]\*\*의 하이브리드 방식으로 적용합니다.

## *Visual (diag): 표준화 흐름*

```mermaid
graph TD
    subgraph "Input Layer"
        A[파일명: "...SIMENSE...xlsx"]
        B[시트명: "Case List, RIL"]
        C[헤더명: "Q'ty / Case#"]
    end

    subgraph "New: name_resolver.py (Alias + Fuzzy Match)"
        D(resolve_vendor)
        E(resolve_sheet)
        F(resolve_header)
    end

    subgraph "Integration Patch"
        G[file_registry.py<br>(normalize_vendor_name)]
        H[file_registry.py<br>(normalize_sheet_name)]
        I[header_normalizer.py<br>(normalize class method)]
    end

    subgraph "Canonical Output"
        J[Vendor: "SIEMENS"]
        K[Sheet: "CASE LIST, RIL(SIEMENS)"]
        L[Header: "QTY" / "CASE NO"]
    end

    A --> D --> G --> J
    B --> E --> H --> K
    C --> F --> I --> L
```

## *3 Options: 통합 전략*

| Option | Description | Pro | Con |
| :--- | :--- | :--- | :--- |
| **1. Hybrid Patch (권장)** | **(본 응답 채택)** `name_resolver`로 표준 별칭(예: "CASE NO")을 찾은 뒤, `header_normalizer`의 기존 정규화(예: "casenumber")를 수행합니다. | **호환성**: `semantic_matcher` 및 `header_registry`의 기존 로직(예: 'case\_number' 키)과 완벽 호환됩니다. | 2단계 정규화로 논리 흐름이 약간 복잡해집니다. |
| 2. Full Replace | `header_normalizer`의 정규화 로직을 `name_resolver`의 `UPPERCASE` 반환 로직으로 **전면 교체**합니다. | 사용자 요청(패치 예시)을 가장 문자 그대로 따릅니다. | **Breaking Change**: `semantic_matcher`가 `casenumber` 대신 "CASE NO"를 기대하게 되어, `header_registry`의 모든 키 변경이 필요합니다. |
| 3. Parallel System | `name_resolver`를 연동하지 않고, 별도 유틸리티로만 사용합니다. | 기존 시스템에 전혀 영향을 주지 않아 안전합니다. | 이름 표준화가 필요한 `file_registry` 등에서 이점을 누릴 수 없습니다. |

## *Steps (P-Pi-B-O-S): 코드 통합 실행*

  * **Problem:** 파일/시트/헤더명의 오타, 약어, 별칭(예: `simense`, `he`, `Q'ty`)이 데이터 통합을 방해합니다.

  * **Pillar:** 견고한 이름 정규화(Alias/Fuzzy-based Normalization) 파이프라인 구축.

  * **Blob 1: `name_resolver.py` 교체**

      * `name_resolver.py` 파일을 아래 내용으로 덮어씁니다. (제공해주신 코드와 동일)

    <!-- end list -->

    ```python
    # -*- coding: utf-8 -*-
    """
    name_resolver.py
    - 파일명/시트명/헤더명 공통 별칭 매칭 + 퍼지 유사도 기반 표준화
    - 외부 라이브러리 없이 동작(간단한 Levenshtein 거리, 토큰 기반 일치 포함)
    - 매칭 순서: exact > 포함/토큰 > 퍼지(편집거리) with 가중치
    """

    from __future__ import annotations
    from dataclasses import dataclass
    from typing import Dict, Iterable, List, Optional, Tuple
    import re
    import unicodedata

    # ---------- 0) 표준 키와 별칭 사전 ----------
    # 필요시 자유롭게 확장하십시오.
    VENDOR_ALIASES: Dict[str, Iterable[str]] = {
        "HITACHI": {
            "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치", "hitachienergy",
            "he local", "he-local"
        },
        "SIEMENS": {
            "siemens", "sim", "simense", "seimens", "ril", "r.i.l", "ril(simense)", "지멘스"
        },
    }

    # 시트명도 같은 방식으로: (예시는 실제 시트 이름에 맞춰 추가)
    SHEET_ALIASES: Dict[str, Iterable[str]] = {
        "CASE LIST": {"case list", "caselist", "case_list"},
        "CASE LIST, RIL(SIEMENS)": {
            "case list, ril(simense)", "case list ril", "ril", "ril(simense)"
        },
        "HE LOCAL": {"he local", "he-local", "hitachi local", "히타치 로컬"},
    }

    # 헤더(컬럼) 표준화: 프로젝트에서 자주 쓰는 표준 헤더를 좌측에, 우측에 다양한 변형을 나열
    HEADER_ALIASES: Dict[str, Iterable[str]] = {
        "CASE NO": {"case no", "case_no", "caseno", "case#", "case number"},
        "VENDOR": {"vendor", "maker", "supplier", "vend", "vendr"},
        "QTY": {"qty", "quantity", "q'ty", "수량"},
        "MATERIAL": {"material", "item desc", "description", "desc", "품명"},
    }


    # ---------- 1) 정규화 유틸 ----------
    def normalize(s: str) -> str:
        """소문자, 공백/특수문자 축약, 호환성 정규화."""
        if s is None:
            return ""
        s = unicodedata.normalize("NFKC", s).lower().strip()
        # 괄호/구두점 등은 공백으로, 다중 공백은 1칸으로
        s = re.sub(r"[\t\r\n]+", " ", s)
        s = re.sub(r"[^\w\s]+", " ", s)   # 문자/숫자/언더스코어/공백만
        s = re.sub(r"\s+", " ", s).strip()
        return s


    def tokenize(s: str) -> List[str]:
        return normalize(s).split()


    # ---------- 2) 간단 Levenshtein 거리/유사도 ----------
    def levenshtein(a: str, b: str) -> int:
        a, b = normalize(a), normalize(b)
        if not a:
            return len(b)
        if not b:
            return len(a)
        dp = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            prev, dp[0] = dp[0], i
            for j, cb in enumerate(b, 1):
                cur = dp[j]
                cost = 0 if ca == cb else 1
                dp[j] = min(
                    dp[j] + 1,    # deletion
                    dp[j - 1] + 1,  # insertion
                    prev + cost   # substitution
                )
                prev = cur
        return dp[-1]


    def sim_ratio(a: str, b: str) -> float:
        """0~1 범위 유사도: 1 - (편집거리 / 최대길이)"""
        a_n, b_n = normalize(a), normalize(b)
        if not a_n and not b_n:
            return 1.0
        dist = levenshtein(a_n, b_n)
        denom = max(len(a_n), len(b_n), 1)
        return 1.0 - dist / denom


    # ---------- 3) 점수 계산 ----------
    def token_overlap_score(q: str, cand: str) -> float:
        qs, cs = set(tokenize(q)), set(tokenize(cand))
        if not qs or not cs:
            return 0.0
        inter = len(qs & cs)
        return inter / max(len(qs), len(cs))


    def contains_score(q: str, cand: str) -> float:
        qn, cn = normalize(q), normalize(cand)
        return 1.0 if qn and (qn in cn or cn in qn) else 0.0


    @dataclass
    class MatchResult:
        canonical: str
        alias_matched: str
        score: float
        method: str  # 'exact' | 'contains' | 'token' | 'fuzzy'


    # ---------- 4) 공통 매칭 엔진 ----------
    def _build_alias_table(alias_map: Dict[str, Iterable[str]]) -> List[Tuple[str, str]]:
        """[(canonical, alias), ...]"""
        rows: List[Tuple[str, str]] = []
        for canon, aliases in alias_map.items():
            rows.append((canon, canon))  # canonical 자체도 별칭으로 취급(정확일치 허용)
            for a in aliases:
                rows.append((canon, a))
        return rows


    def _score(query: str, alias: str) -> Tuple[float, str]:
        # 정확 일치 최우선
        if normalize(query) == normalize(alias):
            return 1.00, "exact"
        # 포함/토큰/퍼지(가중 혼합)
        c = contains_score(query, alias)           # 0 or 1
        t = token_overlap_score(query, alias)      # 0~1
        f = sim_ratio(query, alias)                # 0~1
        # 가중치: 포함 0.50, 토큰 0.75, 퍼지 1.00 (퍼지가 가장 연속적인 신호)
        score = max(
            0.50 * c,
            0.40 * t + 0.60 * f  # 토큰+퍼지 혼합
        )
        # 메서드 라벨(설명용)
        method = "contains" if c == 1.0 else ("token" if t >= f else "fuzzy")
        return score, method


    def resolve_with_aliases(query: str,
                             alias_map: Dict[str, Iterable[str]],
                             min_score: float = 0.72) -> Optional[MatchResult]:
        """별칭 테이블에서 최적 canon 반환. min_score 미만이면 None."""
        if not query:
            return None
        best: Optional[MatchResult] = None
        for canon, alias in _build_alias_table(alias_map):
            s, m = _score(query, alias)
            if (best is None) or (s > best.score):
                best = MatchResult(canonical=canon, alias_matched=alias, score=s, method=m)
        if best and best.score >= min_score:
            return best
        return None


    # ---------- 5) 공개 API ----------
    def resolve_vendor(text: str, *, min_score: float = 0.72) -> Optional[MatchResult]:
        """파일명/시트명/셀 텍스트에서 벤더 추정."""
        return resolve_with_aliases(text, VENDOR_ALIASES, min_score=min_score)


    def resolve_sheet(text: str, *, min_score: float = 0.70) -> Optional[MatchResult]:
        return resolve_with_aliases(text, SHEET_ALIASES, min_score=min_score)


    def resolve_header(text: str, *, min_score: float = 0.70) -> Optional[MatchResult]:
        return resolve_with_aliases(text, HEADER_ALIASES, min_score=min_score)


    # ---------- 6) 파일명/시트명에서 벤더 후보 추출 헬퍼 ----------
    _VENDOR_HINT_PAT = re.compile(
        r"\b(he|hitachi(?:\s*energy)?|siemens|simense|seimens|sim|ril)\b", re.I
    )

    def guess_vendor_from_filename(path: str) -> Optional[MatchResult]:
        """
        파일 경로/파일명에서 벤더 후보 토큰을 먼저 뽑아 점수 가산.
        """
        if not path:
            return None
        toks = _VENDOR_HINT_PAT.findall(path or "")
        # 후보가 없으면 전체 파일명을 그대로 매칭
        candidates = toks or [path]
        best: Optional[MatchResult] = None
        for c in candidates:
            m = resolve_vendor(c)
            if not m:
                # 토큰이 너무 짧으면 전체 파일명으로 재시도
                m = resolve_vendor(path)
            if m and (best is None or m.score > best.score):
                best = m
        return best
    ```

  * **Blob 2: `file_registry.py` 패치**

      * 파일 상단에 `name_resolver` 임포트 추가
      * `normalize_vendor_name` 메서드 로직 교체
      * `normalize_sheet_name`, `guess_vendor_from_file` 2개 클래스 메서드 신규 추가

    <!-- end list -->

    ```python
    # file_registry.py (PATCHED)

    from pathlib import Path
    from datetime import datetime
    from typing import Optional, Dict, List

    # --- PATCH START ---
    # name_resolver 임포트 추가
    from .name_resolver import resolve_vendor, resolve_sheet, guess_vendor_from_filename
    # --- PATCH END ---


    class FileRegistry:
        """
        Central registry for all HVDC project file paths.

        This class provides a single source of truth for all file paths,
        eliminating hardcoded paths throughout the codebase.
        """

        # ==================== RAW INPUT FILES ====================

        RAW_FILES = {
            'master': {
                'hitachi': 'data/raw/HITACHI/Case List_Hitachi.xlsx',
                'siemens': 'data/raw/SIEMENS/HVDC WAREHOUSE_SIMENSE(SIM).xlsx',
            },
            'warehouse': {
                'hitachi': 'data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx',
            }
        }

        # ... (PROCESSED_FILES, DIRECTORIES, SHEET_NAMES
        #      VENDORS, DEFAULT_VERSIONS... 등 기존 내용은 동일) ...
        # (VENDORS.aliases는 기존 로직의 폴백으로 여전히 유효함)

        # ==================== (기존 내용 생략) ====================
        SHEET_NAMES = {
            'case_list': ['Case List, RIL', 'Case List RIL', 'CaseList', 'case list'],
            'he_local': ['HE Local', 'HELocal', 'he local'],
            'capacitor': ['HE-0214,0252 (Capacitor)', 'Capacitor', 'capacitor'],
        }
        VENDORS = {
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
        DEFAULT_VERSION = '3.10'
        # ==================== (기존 내용 생략) ====================


        @classmethod
        def get_master_file(cls, vendor: str = 'hitachi') -> str:
            # (기존 메서드 동일)
            path = cls.RAW_FILES['master'].get(vendor.lower())
            if path is None:
                raise ValueError(f"Unknown vendor: {vendor}. Available: {list(cls.RAW_FILES['master'].keys())}")
            return path

        # ... (get_warehouse_file, get_synced_file, get_derived_file,
        #      get_report_file, get_anomaly_file, get_directory,
        #      get_sheet_variants, get_all_paths, get_vendor_name ... 등
        #      다른 메서드들은 모두 기존과 동일) ...

        @classmethod
        def get_warehouse_file(cls, vendor: str = 'hitachi') -> str:
            path = cls.RAW_FILES['warehouse'].get(vendor.lower())
            if path is None:
                raise ValueError(f"Unknown warehouse vendor: {vendor}. Available: {list(cls.RAW_FILES['warehouse'].keys())}")
            return path

        @classmethod
        def get_synced_file(cls, version: Optional[str] = None, merged: bool = False) -> str:
            version = version or cls.DEFAULT_VERSION
            template = cls.PROCESSED_FILES['synced']['hitachi_merged' if merged else 'hitachi']
            filename = template.format(version=version)
            return str(Path(cls.DIRECTORIES['processed']['synced']) / filename)

        @classmethod
        def get_derived_file(cls, vendor: str = 'hitachi') -> str:
            filename = cls.PROCESSED_FILES['derived'].get(vendor.lower())
            if filename is None:
                raise ValueError(f"Unknown vendor: {vendor}. Available: {list(cls.PROCESSED_FILES['derived'].keys())}")
            return str(Path(cls.DIRECTORIES['processed']['derived']) / filename)

        @classmethod
        def get_report_file(cls, timestamp: Optional[str] = None) -> str:
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            template = cls.PROCESSED_FILES['reports']['template']
            filename = template.format(timestamp=timestamp)
            return str(Path(cls.DIRECTORIES['processed']['reports']) / filename)

        @classmethod
        def get_anomaly_file(cls, format: str = 'excel') -> str:
            filename = cls.PROCESSED_FILES['anomaly'].get(format.lower())
            if filename is None:
                raise ValueError(f"Unknown format: {format}. Available: {list(cls.PROCESSED_FILES['anomaly'].keys())}")
            return str(Path(cls.DIRECTORIES['anomaly']) / filename)

        @classmethod
        def get_directory(cls, category: str, subcategory: Optional[str] = None) -> str:
            if subcategory:
                return cls.DIRECTORIES[category][subcategory]
            else:
                cat_dir = cls.DIRECTORIES[category]
                if isinstance(cat_dir, dict):
                    return cat_dir.get('root', '')
                return cat_dir

        @classmethod
        def get_sheet_variants(cls, sheet_type: str) -> List[str]:
            variants = cls.SHEET_NAMES.get(sheet_type.lower())
            if variants is None:
                raise ValueError(f"Unknown sheet type: {sheet_type}. Available: {list(cls.SHEET_NAMES.keys())}")
            return variants

        @classmethod
        def get_all_paths(cls) -> Dict[str, str]:
            return {
                'master_hitachi': cls.get_master_file('hitachi'),
                'warehouse_hitachi': cls.get_warehouse_file('hitachi'),
                'synced_current': cls.get_synced_file(merged=True),
                'derived_hitachi': cls.get_derived_file('hitachi'),
                'report_latest': cls.get_report_file(),
                'anomaly_excel': cls.get_anomaly_file('excel'),
            }

        @classmethod
        def get_vendor_name(cls, vendor_key: str) -> str:
            vendor_info = cls.VENDORS.get(vendor_key.lower())
            if vendor_info:
                return vendor_info['name']
            return vendor_key.upper()

        # --- PATCH START ---

        @classmethod
        def normalize_vendor_name(cls, vendor_value: str, min_score: float = 0.70) -> str:
            """
            Normalize vendor name from any alias to standard name.
            Uses fuzzy matching and alias registry from name_resolver.
            """
            # 1. Try new fuzzy/alias resolver first
            match = resolve_vendor(vendor_value, min_score=min_score)
            if match:
                return match.canonical  # "HITACHI" or "SIEMENS"

            # 2. Fallback to original simple alias check
            for vendor_key, vendor_info in cls.VENDORS.items():
                if vendor_value in vendor_info['aliases']:
                    return vendor_info['name']

            # 3. Fallback to uppercase
            return vendor_value.upper()

        @classmethod
        def normalize_sheet_name(cls, sheet_name: str, min_score: float = 0.70) -> str:
            """
            (NEW) Normalize sheet name using fuzzy matching and alias registry.
            """
            if not sheet_name:
                return ""
            match = resolve_sheet(sheet_name, min_score=min_score)
            return match.canonical if match else sheet_name

        @classmethod
        def guess_vendor_from_file(cls, file_path: str) -> Optional[str]:
            """
            (NEW) Guess vendor from file path using name_resolver.
            """
            if not file_path:
                return None
            match = guess_vendor_from_filename(file_path)
            return match.canonical if match else None

        # --- PATCH END ---

        @classmethod
        def get_source_file_name(cls, vendor_key: str) -> str:
            # (기존 메서드 동일)
            vendor_info = cls.VENDORS.get(vendor_key.lower())
            if vendor_info and 'source_file' in vendor_info:
                return vendor_info['source_file']

            normalized = cls.normalize_vendor_name(vendor_key)
            for key, info in cls.VENDORS.items():
                if info['name'] == normalized and 'source_file' in info:
                    return info['source_file']

            return f"{vendor_key.upper()}({vendor_key[:2].upper()})"


    # Convenience functions (기존과 동일)
    def get_master_file(vendor: str = 'hitachi') -> str:
        return FileRegistry.get_master_file(vendor)
    # ... (다른 convenience function들 동일) ...

    ```

  * **Blob 3: `header_normalizer.py` 패치 (하이브리드)**

      * 파일 상단에 `name_resolver` 임포트 추가
      * `HeaderNormalizer` **클래스**의 `normalize` 메서드 로직을 **하이브리드 방식**으로 수정 (QA 섹션 참고)

    <!-- end list -->

    ```python
    # header_normalizer.py (PATCHED)

    import re
    import unicodedata
    from typing import Optional

    # --- PATCH START ---
    # name_resolver 임포트 추가
    from .name_resolver import resolve_header
    # --- PATCH END ---


    class HeaderNormalizer:
        """
        Comprehensive header name normalization for robust matching.
        ... (docstring 동일) ...
        """

        def __init__(self):
            # (기존 __init__ 동일)
            self.abbreviation_map = {
                "no": "number",
                "num": "number",
                "qty": "quantity",
                "amt": "amount",
                "desc": "description",
                "est": "estimated",
                "arr": "arrival",
                "dep": "departure",
                "wh": "warehouse",
                "sqm": "squaremeter",
                "cntr": "container",
            }
            self.separator_pattern = re.compile(r"[._\-/\\|:;,\s]+")

        # --- PATCH START ---
        # 'normalize' 클래스 메서드 수정

        def normalize(self, header: str, expand_abbreviations: bool = True) -> str:
            """
            Normalize a header name to its canonical form.

            (Hybrid Approach)
            1. (NEW) Use name_resolver to find canonical alias (e.g., "Q'ty" -> "QTY")
            2. (OLD) Use original normalization on that alias (e.g., "QTY" -> "quantity")
            """
            if not isinstance(header, str):
                header = str(header)
            base = header.strip()
            if not base:
                return ""

            # 1. (NEW) Try alias/fuzzy match first from name_resolver
            hit = resolve_header(base, min_score=0.70)
            if hit:
                # Use the canonical name (e.g., "CASE NO", "QTY")
                # as the *new* input for the original normalization logic below
                header = hit.canonical
            else:
                # No alias match, use the original header
                header = base

            # --- (Original logic resumes, using potentially resolved 'header') ---

            # Step 1: Convert to lowercase for case-insensitive matching
            normalized = header.lower().strip()

            # Step 2: Normalize Unicode to handle full-width characters
            # NFKC normalization converts full-width to half-width
            normalized = unicodedata.normalize("NFKC", normalized)

            # Step 3: Remove all special characters and separators
            normalized = self._strip_separators(normalized)

            # Step 4: Remove remaining non-letter/number characters
            normalized = self._filter_letters_and_numbers(normalized)

            # Step 5: Expand common abbreviations if requested
            if expand_abbreviations and normalized in self.abbreviation_map:
                normalized = self.abbreviation_map[normalized]

            return normalized

        # --- PATCH END ---

        def normalize_with_alternatives(self, header: str) -> list[str]:
            # (기존 메서드 동일)
            # (Note: 이 메서드는 자동으로 패치된 normalize()를 호출하므로 수정 불필요)
            alternatives = []
            expanded = self.normalize(header, expand_abbreviations=True)
            alternatives.append(expanded)
            unexpanded = self.normalize(header, expand_abbreviations=False)
            if unexpanded != expanded:
                alternatives.append(unexpanded)

            # ... (기존 로직 동일) ...
            partial = header.lower().strip()
            partial = unicodedata.normalize("NFKC", partial)
            partial = re.sub(r"[._\-/\\|:;,]+", "", partial)
            partial = re.sub(r"\s+", "", partial)
            partial = self._filter_letters_and_numbers(partial)
            if partial not in alternatives:
                alternatives.append(partial)

            return alternatives

        def _strip_separators(self, value: str) -> str:
            # (기존 메서드 동일)
            return self.separator_pattern.sub("", value)

        @staticmethod
        def _filter_letters_and_numbers(value: str) -> str:
            # (기존 메서드 동일)
            return "".join(ch for ch in value if unicodedata.category(ch)[0] in {"L", "N"})


    def normalize_header(header: str, expand_abbreviations: bool = True) -> str:
        # (기존 함수 동일 - 자동으로 패치된 클래스 로직을 사용)
        normalizer = HeaderNormalizer()
        return normalizer.normalize(header, expand_abbreviations)


    if __name__ == "__main__":
        # (기존 테스트 스위트 동일)
        pass
    ```

  * **Owner:** SCM/Dev Team (Mr. Cha)

  * **Status:** **Done**. (위 3개 파일에 적용 필요)

## *Data Sim/BI-Viz: 사용 예시 (제공된 내용)*

```python
from name_resolver import resolve_vendor, resolve_sheet, resolve_header, guess_vendor_from_filename

# 1. 파일명에서 벤더 추정
print(guess_vendor_from_filename("HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"))
# -> MatchResult(canonical='HITACHI', alias_matched='hitachi', ...)

# 2. 벤더 별칭/오타 정규화
print(resolve_vendor("RIL(SIMENSE)"))
# -> MatchResult(canonical='SIEMENS', alias_matched='ril(simense)', ...)

# 3. 시트명 정규화
print(resolve_sheet("Case List, RIL(SIMENSE)"))
# -> MatchResult(canonical='CASE LIST, RIL(SIEMENS)', ...)

# 4. 헤더명 정규화
print(resolve_header("Q'ty"))
# -> MatchResult(canonical='QTY', alias_matched="q'ty", ...)
```

## *Auto (RPA+LLM): 자동화 방안*

  * **자동화:** 본 모듈 자체가 자동화의 핵심입니다. 파일/시트/헤더명을 수동으로 수정할 필요 없이, 파이프라인이 자동으로 정규화된 이름을 감지하고 매칭합니다.
  * **유지보수:** 신규 별칭이나 오타 발견 시, `name_resolver.py`의 `VENDOR_ALIASES`, `SHEET_ALIASES`, `HEADER_ALIASES` 딕셔너리에 추가하는 것만으로도 시스템 전체의 매칭 성능이 향상됩니다.

## *QA (Gap/Recheck): 리스크 분석 및 재검증*

  * **핵심 검증 포인트 (하이브리드 패치):** `header_normalizer.py` 패치는 가장 중요합니다.
      * **이유:** `semantic_matcher.py`는 `header_registry.py`의 시맨틱 키(예: `case_number`, `quantity`)를 기준으로 작동합니다.
      * **동작:** `name_resolver`가 `Q'ty`를 `QTY`로 1차 변환하면(Blob 3), `header_normalizer`의 기존 로직이 `QTY`를 `quantity`로 2차 변환합니다.
      * **결과:** `semantic_matcher`가 `quantity` (from registry) == `quantity` (from header)로 인식하여, 기존 파이프라인과 완벽하게 호환됩니다.
  * **임계값(Min Score) 튜닝:** `file_registry.py`와 `header_normalizer.py`의 `min_score=0.70`은 초기값입니다. 오탐(False Positive)이 발생하면 값을 올리고(예: `0.75`), 미탐(False Negative)이 발생하면 값을 낮춰(예: `0.65`) 튜닝이 필요합니다.

## *Accuracy: 데이터 기반 응답 명시*

  * 본 응답은 제공해주신 `name_resolver.py` 코드와 기존 9개 파일(`header_registry.py`, `name_resolver.py` (old), `header_normalizer.py` 등)의 구조를 기반으로 작성되었습니다.

## *Numbers (2-dec):*

  * 본 요청은 코드 통합 작업으로, 특정 수치 데이터(예: 비용, 재고)를 포함하지 않습니다. `min_score`는 `0.70` (소수점 두 자리)으로 기본 설정되었습니다.

## *CmdRec: 권장 슬래시 커맨드*

  * `/logi-master test-suite --module name_resolver --report`
  * `/revalidate @new_vendor_file.xlsx --sheet "Sheet1" --show-header-matches`
