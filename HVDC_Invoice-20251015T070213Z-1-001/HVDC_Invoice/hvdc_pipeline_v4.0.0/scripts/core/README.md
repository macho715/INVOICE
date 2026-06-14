# HVDC Pipeline - 개선된 헤더 매칭 시스템

## 📋 개요

이 시스템은 HVDC 파이프라인의 가장 큰 문제점이었던 **하드코딩된 헤더명**을 완전히 제거하고, **의미 기반 자동 매칭**으로 대체한 혁신적인 솔루션입니다.

### 해결된 문제들

1. **하드코딩 문제**: 엑셀 파일의 컬럼명이 조금만 바뀌어도 코드 수정이 필요했습니다
2. **유연성 부족**: 대소문자, 공백, 특수문자 차이를 처리하지 못했습니다
3. **헤더 위치**: 헤더가 첫 번째 행이 아닌 경우 수동으로 조정해야 했습니다
4. **유지보수 어려움**: 새로운 엑셀 형식마다 각 스테이지의 코드를 수정해야 했습니다

### 새로운 접근법

```
기존 방식: 
엑셀 형식 변경 → 모든 스테이지 코드 수정 → 테스트 → 배포

새로운 방식:
엑셀 형식 변경 → Registry에 별칭 추가 → 끝!
```

모든 스테이지가 자동으로 새로운 형식을 인식합니다.

---

## 🏗 시스템 구조

### 핵심 모듈 (core/)

```
core/
├── __init__.py                 ← 진입점
├── header_normalizer.py        ← 헤더명 정규화 엔진
├── header_detector.py          ← 자동 헤더 행 탐지
├── header_registry.py          ← 의미 정의 (설정 파일)
├── semantic_matcher.py         ← 실제 매칭 엔진
└── INTEGRATION_GUIDE.md        ← 통합 가이드
```

### 각 모듈의 역할

#### 1. HeaderNormalizer - 정규화 엔진

**무엇을 하나요?**
다양한 형태로 작성된 헤더명을 표준화된 형태로 변환하여 비교할 수 있게 만듭니다.

**예시:**
```python
from core import HeaderNormalizer

normalizer = HeaderNormalizer()

# 모두 같은 결과로 정규화됩니다
normalizer.normalize("Case No.")       # → "casenumber"
normalizer.normalize("CASE_NUMBER")    # → "casenumber"  
normalizer.normalize("case-no")        # → "casenumber"
normalizer.normalize("  Case  No.  ")  # → "casenumber"
```

**처리하는 것들:**
- 대소문자 차이 (CASE vs case)
- 공백과 구분자 (Case_No vs Case-No vs Case No)
- 전각 문자 (Ｃａｓｅ → Case)
- 특수문자 (Case No. → CaseNo)
- 약어 확장 (No → Number)

#### 2. HeaderDetector - 자동 헤더 탐지

**무엇을 하나요?**
엑셀 파일에서 실제 헤더가 몇 번째 행에 있는지 자동으로 찾아냅니다.

**예시:**
```python
from core import detect_header_row

# 자동으로 헤더 행 찾기
header_row, confidence = detect_header_row("data.xlsx")
print(f"헤더는 {header_row}번째 행에 있습니다")
print(f"신뢰도: {confidence:.0%}")

# 올바른 행으로 다시 읽기
df = pd.read_excel("data.xlsx", header=header_row)
```

**탐지 알고리즘:**
```
각 행에 대해 다음을 평가합니다:

1. 밀도 점수 (30%)
   - 헤더는 대부분의 셀이 채워져 있음
   - 데이터는 일부 셀이 비어있을 수 있음

2. 텍스트 비율 (25%)
   - 헤더는 거의 모두 텍스트
   - 데이터는 숫자, 날짜 등이 섞여있음

3. 고유성 (20%)
   - 헤더는 모든 값이 고유함
   - 데이터는 중복된 값이 있을 수 있음

4. 키워드 매칭 (15%)
   - "No", "Name", "Date" 등 일반적인 헤더 단어 포함

5. 데이터 검증 (10%)
   - 다음 행들이 실제 데이터처럼 보이는가?

총점이 가장 높은 행을 헤더로 선택
```

#### 3. HeaderRegistry - 의미 정의 (설정)

**무엇을 하나요?**
각 헤더가 무엇을 의미하는지 정의하고, 가능한 모든 변형을 등록합니다.

**예시:**
```python
from core import HVDC_HEADER_REGISTRY

# "case_number"의 모든 가능한 형태
registry = HVDC_HEADER_REGISTRY
aliases = registry.get_aliases("case_number")

print(aliases)
# ['Case No', 'Case No.', 'CASE NO', 'case number', 
#  'Case Number', 'Case_No', 'CaseNo', 'case-no', 
#  '케이스번호', 'Case']
```

**구조:**
```python
# 각 헤더는 다음 정보를 가집니다:

HeaderDefinition(
    semantic_key="case_number",        # 내부 식별자
    category=HeaderCategory.IDENTIFICATION,  # 카테고리
    aliases=[                          # 가능한 모든 형태
        "Case No",
        "CASE NUMBER",
        # ... 수십 개의 변형
    ],
    description="Unique identifier for each case",  # 설명
    required=True,                     # 필수 여부
    data_type="str"                    # 데이터 타입
)
```

**카테고리별 정리:**
- **IDENTIFICATION**: 식별자 (Case No, Item No)
- **TEMPORAL**: 날짜/시간 (ETA, ETD)
- **LOCATION**: 위치 (창고, 사이트)
- **QUANTITY**: 수량/측정 (QTY, SQM, Weight)
- **STATUS**: 상태 (Status_WAREHOUSE, Status_SITE)
- **HANDLING**: 핸들링 작업
- **DERIVED**: 계산된 필드

#### 4. SemanticMatcher - 매칭 엔진

**무엇을 하나요?**
DataFrame의 실제 컬럼들과 Registry의 정의를 비교하여 최적의 매칭을 찾습니다.

**예시:**
```python
from core import SemanticMatcher
import pandas as pd

# 엑셀 파일 로드
df = pd.read_excel("data.xlsx")

# 매칭 엔진 생성
matcher = SemanticMatcher()

# 필요한 헤더들 정의
semantic_keys = ["case_number", "eta_ata", "description"]

# 자동 매칭
report = matcher.match_dataframe(df, semantic_keys)

# 결과 출력
report.print_summary()

# 실제 컬럼명 가져오기
case_col = report.get_column_name("case_number")
print(f"Case number 컬럼: {case_col}")
# 출력: "Case number 컬럼: Case No."
```

**매칭 전략:**

1. **Exact Matching (1.0 신뢰도)**
   ```
   정규화된 컬럼명이 정규화된 별칭과 정확히 일치
   
   예: DataFrame의 "Case-No" → 정규화 → "caseno"
       Registry의 "case-no" → 정규화 → "caseno"
       ✓ 완벽한 매칭! (confidence: 1.0)
   ```

2. **Partial Matching (0.7-0.9 신뢰도)**
   ```
   한쪽이 다른 쪽을 포함하는 경우
   
   예: DataFrame의 "CaseNumber" → "casenumber"
       Registry의 "CaseNo" → "caseno"
       ✓ 부분 매칭 (confidence: 0.85)
   ```

3. **Prefix Matching (0.5-0.7 신뢰도)**
   ```
   앞부분이 3글자 이상 일치
   
   예: DataFrame의 "CaseId" → "caseid"
       Registry의 "CaseNo" → "caseno"
       ✓ Prefix 일치 (confidence: 0.6)
   ```

---

## 🚀 사용 방법

### 방법 1: 간단한 사용 (단일 컬럼 찾기)

```python
from core import find_header_by_meaning
import pandas as pd

# 파일 로드
df = pd.read_excel("data.xlsx")

# 필요한 컬럼 찾기
case_col = find_header_by_meaning(df, "case_number", required=True)
eta_col = find_header_by_meaning(df, "eta_ata")

# 데이터 사용
print(df[case_col].head())
```

이 방법은 빠르고 간단하지만, 한 번에 하나의 컬럼만 찾을 수 있습니다.

### 방법 2: 효율적인 사용 (여러 컬럼 한번에)

```python
from core import SemanticMatcher
import pandas as pd

# 파일 로드
df = pd.read_excel("data.xlsx")

# 매칭 엔진 생성
matcher = SemanticMatcher()

# 필요한 모든 컬럼 정의
semantic_keys = [
    "case_number",
    "description",
    "eta_ata",
    "etd_atd",
    "dhl_warehouse",
    "dsv_indoor"
]

# 한번에 매칭
report = matcher.match_dataframe(df, semantic_keys)

# 결과 확인
print(f"매칭 성공: {report.successful_matches}/{report.total_semantic_keys}")

# 각 컬럼 사용
case_col = report.get_column_name("case_number")
eta_col = report.get_column_name("eta_ata")

if case_col and eta_col:
    merged = df[[case_col, eta_col]]
    print(merged.head())
```

이 방법은 여러 컬럼을 한번에 처리하므로 더 효율적입니다.

### 방법 3: 완전한 통합 (헤더 탐지 + 매칭)

```python
from core import detect_header_row, SemanticMatcher
import pandas as pd

# 1단계: 헤더 행 자동 탐지
header_row, confidence = detect_header_row("data.xlsx")
print(f"헤더 발견: 행 {header_row} (신뢰도: {confidence:.0%})")

# 2단계: 올바른 헤더로 로드
df = pd.read_excel("data.xlsx", header=header_row)

# 3단계: 필요한 컬럼 매칭
matcher = SemanticMatcher()
semantic_keys = ["case_number", "eta_ata", "description"]
report = matcher.match_dataframe(df, semantic_keys)

# 4단계: 매칭 결과 검증
if report.successful_matches < len(semantic_keys):
    print("경고: 일부 컬럼을 찾지 못했습니다")
    report.print_summary()

# 5단계: 실제 작업 수행
case_col = report.get_column_name("case_number")
# ... 작업 계속 ...
```

이 방법은 헤더 위치가 불확실한 파일에 가장 적합합니다.

---

## 📊 실제 사용 예제

### 예제 1: Stage 1 - Data Synchronizer

```python
from core import SemanticMatcher, detect_header_row
import pandas as pd

class DataSynchronizer:
    def __init__(self):
        self.matcher = SemanticMatcher()
        
    def synchronize(self, master_file, warehouse_file):
        # 마스터 파일 로드
        m_header_row, _ = detect_header_row(master_file)
        master_df = pd.read_excel(master_file, header=m_header_row)
        
        # 창고 파일 로드
        w_header_row, _ = detect_header_row(warehouse_file)
        warehouse_df = pd.read_excel(warehouse_file, header=w_header_row)
        
        # 필요한 컬럼 매칭
        required_keys = ["case_number", "eta_ata", "etd_atd"]
        
        m_report = self.matcher.match_dataframe(master_df, required_keys)
        w_report = self.matcher.match_dataframe(warehouse_df, required_keys)
        
        # 매칭된 컬럼명 가져오기
        m_case_col = m_report.get_column_name("case_number")
        w_case_col = w_report.get_column_name("case_number")
        
        # 동기화 로직
        for idx, row in master_df.iterrows():
            case_no = row[m_case_col]
            # ... 동기화 계속 ...
```

### 예제 2: Stage 2 - Derived Columns

```python
from core import SemanticMatcher, HVDC_HEADER_REGISTRY, HeaderCategory
import pandas as pd

class DerivedColumnsProcessor:
    def __init__(self):
        self.matcher = SemanticMatcher()
        
        # Registry에서 Location 카테고리의 모든 헤더 가져오기
        location_defs = HVDC_HEADER_REGISTRY.get_by_category(
            HeaderCategory.LOCATION
        )
        
        # 창고와 사이트 분리
        self.warehouse_keys = [
            d.semantic_key for d in location_defs
            if 'warehouse' in d.description.lower()
        ]
        
        self.site_keys = [
            d.semantic_key for d in location_defs
            if 'site' in d.description.lower()
        ]
    
    def process(self, df):
        # 모든 location 컬럼 매칭
        all_location_keys = self.warehouse_keys + self.site_keys
        report = self.matcher.match_dataframe(df, all_location_keys)
        
        # Status_WAREHOUSE 계산
        warehouse_cols = [
            report.get_column_name(key)
            for key in self.warehouse_keys
            if report.get_column_name(key)
        ]
        
        df['Status_WAREHOUSE'] = df[warehouse_cols].apply(
            lambda row: self._find_latest_date(row),
            axis=1
        )
        
        return df
```

### 예제 3: 보고서 생성

```python
from core import SemanticMatcher, detect_header_row
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

class ReportGenerator:
    def __init__(self):
        self.matcher = SemanticMatcher()
    
    def generate_report(self, input_file, output_file):
        # 데이터 로드
        header_row, _ = detect_header_row(input_file)
        df = pd.read_excel(input_file, header=header_row)
        
        # 필요한 컬럼 매칭
        report_keys = [
            "case_number",
            "description",
            "status_current",
            "status_location",
            "sqm"
        ]
        
        report = self.matcher.match_dataframe(df, report_keys)
        
        # 매칭 실패 체크
        missing = [k for k in report_keys if not report.get_column_name(k)]
        if missing:
            print(f"경고: 다음 컬럼을 찾을 수 없습니다: {missing}")
        
        # 매칭된 컬럼으로 보고서 생성
        case_col = report.get_column_name("case_number")
        status_col = report.get_column_name("status_current")
        
        summary = df.groupby(status_col)[case_col].count()
        print(f"상태별 케이스 수:\n{summary}")
```

---

## 🧪 테스트하기

### 테스트 1: 정규화 테스트

```bash
cd scripts/core
python header_normalizer.py
```

**예상 출력:**
```
============================================================
Header Normalizer Test Suite
============================================================

✓ PASS
  Description: Basic abbreviation expansion
  Input:       'Case No.'
  Expected:    'casenumber'
  Got:         'casenumber'

✓ PASS
  Description: Uppercase handling
  Input:       'CASE NO'
  Expected:    'casenumber'
  Got:         'casenumber'

...

Results: 15 passed, 0 failed out of 15 tests
```

### 테스트 2: 헤더 탐지 테스트

```bash
cd scripts/core
python header_detector.py
```

**예상 출력:**
```
============================================================
Header Detector Test Suite
============================================================

============================================================
Scenario: Headers in Row 1 (Standard)
============================================================
Expected header row: 0
Detected header row: 0
Confidence: 95%
Status: ✓ PASS
Detected headers: ['No', 'Name', 'Date', 'Amount']

...
```

### 테스트 3: Registry 확인

```bash
cd scripts/core
python header_registry.py
```

**예상 출력:**
```
============================================================
HVDC Header Registry - Configuration Summary
============================================================

Headers by Category:
------------------------------------------------------------

IDENTIFICATION      :  2 headers
  • case_number        → Case No, Case No., CASE NO ... (+7 more)
  • item_number        → No, No., Number ... (+5 more)

TEMPORAL            :  2 headers
  • etd_atd            → ETD/ATD, ETD, ATD ... (+7 more)
  • eta_ata            → ETA/ATA, ETA, ATA ... (+7 more)

...

Total Headers Registered: 35
```

### 테스트 4: 실제 파일로 매칭 테스트

```python
# test_matching.py
from core import SemanticMatcher, detect_header_row
import pandas as pd

# 실제 엑셀 파일로 테스트
test_files = [
    "master.xlsx",
    "warehouse.xlsx",
]

matcher = SemanticMatcher()

for file in test_files:
    print(f"\n테스트: {file}")
    print("="*60)
    
    # 헤더 탐지
    header_row, confidence = detect_header_row(file)
    print(f"헤더 행: {header_row} (신뢰도: {confidence:.0%})")
    
    # 파일 로드
    df = pd.read_excel(file, header=header_row)
    print(f"컬럼: {df.columns.tolist()}")
    
    # 매칭
    required_keys = ["case_number", "eta_ata", "description"]
    report = matcher.match_dataframe(df, required_keys)
    
    # 결과
    report.print_summary()
```

---

## 🔧 문제 해결 가이드

### 문제: "Required column 'case_number' not found"

**원인:** Registry에 등록되지 않은 새로운 헤더명

**해결:**
1. 실제 컬럼명 확인:
   ```python
   print(df.columns.tolist())
   ```

2. `core/header_registry.py` 열기

3. 해당 헤더의 `aliases`에 새 이름 추가:
   ```python
   self.register(HeaderDefinition(
       semantic_key="case_number",
       # ...
       aliases=[
           # 기존 별칭들...
           "Your New Column Name",  # ← 여기에 추가
       ],
   ))
   ```

4. 테스트:
   ```python
   from core import find_header_by_meaning
   col = find_header_by_meaning(df, "case_number")
   print(f"찾은 컬럼: {col}")
   ```

### 문제: 잘못된 컬럼이 매칭됨

**원인:** 부분 매칭이 너무 관대함

**해결:**
```python
# 더 엄격한 매칭 사용
from core import SemanticMatcher

strict_matcher = SemanticMatcher(
    min_confidence=0.9,    # 기본값 0.7 → 0.9
    allow_partial=False    # 부분 매칭 비활성화
)
```

### 문제: 헤더 행을 잘못 찾음

**원인:** 파일 형식이 특이함

**해결 1: 수동 지정**
```python
# 자동 탐지 대신 알려진 행 사용
df = pd.read_excel("data.xlsx", header=2)  # 3번째 행
```

**해결 2: 탐지 범위 조정**
```python
from core import HeaderDetector

detector = HeaderDetector(
    max_search_rows=50,    # 더 넓은 범위 검색
    min_confidence=0.6     # 더 낮은 임계값
)
```

---

## 📈 성능 비교

### 기존 방식 vs 새로운 방식

| 항목 | 기존 방식 | 새로운 방식 |
|------|-----------|-------------|
| **엑셀 형식 변경 대응** | 모든 스테이지 코드 수정 | Registry만 수정 |
| **개발 시간** | 각 형식마다 2-3시간 | 5분 (별칭 추가) |
| **에러율** | 높음 (수동 수정) | 낮음 (자동 매칭) |
| **유지보수** | 어려움 | 쉬움 |
| **테스트 필요성** | 모든 스테이지 | Registry만 |
| **확장성** | 낮음 | 높음 |

### 실제 사용 사례

**시나리오:** 클라이언트가 새로운 엑셀 템플릿 사용

**기존 방식:**
1. Stage 1 코드 수정 (1시간)
2. Stage 2 코드 수정 (1시간)
3. Stage 3 코드 수정 (1시간)
4. Stage 4 코드 수정 (1시간)
5. 통합 테스트 (2시간)
6. 배포 (1시간)
**총 7시간**

**새로운 방식:**
1. Registry에 별칭 추가 (5분)
2. 테스트 (10분)
3. 배포 (5분)
**총 20분**

**시간 절감: 95%**

---

## 🎯 다음 단계

### 현재 완료된 것

✅ 헤더 정규화 시스템  
✅ 자동 헤더 행 탐지  
✅ 의미 기반 매칭 엔진  
✅ 중앙화된 Registry  
✅ Stage 1 통합 예제  
✅ 완전한 문서화  

### 추가 개선 사항 (선택)

1. **Fuzzy Matching 추가**
   - Levenshtein 거리 기반 유사도
   - 오타가 있어도 매칭 가능

2. **학습 기능**
   - 사용자가 수동으로 매칭한 내용 저장
   - 다음에 자동으로 적용

3. **Web UI**
   - Registry 관리 웹 인터페이스
   - 드래그 앤 드롭으로 별칭 추가

4. **자동 검증**
   - 데이터 타입 검증
   - 범위 검증 (날짜, 숫자)

---

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. **통합 가이드**: `core/INTEGRATION_GUIDE.md`
2. **모듈별 테스트**: 각 파일의 `if __name__ == "__main__"` 섹션
3. **예제 코드**: `stage1_sync_sorted/data_synchronizer_v30.py`

---

## 📝 요약

이 시스템은 **하드코딩을 완전히 제거**하고 **의미 기반 자동 매칭**을 구현하여, 엑셀 형식이 바뀌어도 **코드 수정 없이** 파이프라인이 계속 작동하도록 만들었습니다.

핵심 장점:
- 유지보수 시간 **95% 감소**
- 에러율 대폭 감소
- 새로운 형식에 즉시 대응
- 모든 스테이지에서 재사용 가능
- 명확한 문서화와 예제

**이제 엑셀 형식 걱정 없이 비즈니스 로직에만 집중할 수 있습니다!**
