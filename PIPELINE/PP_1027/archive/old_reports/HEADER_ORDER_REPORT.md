# HVDC Pipeline 헤더 정렬 순서 분석 보고서

## 📋 Executive Summary

HVDC Pipeline은 3단계(Stage 1, 2, 3)에 걸쳐 각기 다른 헤더 정렬 순서를 사용합니다. 각 단계별로 데이터 처리 목적에 맞게 최적화된 컬럼 순서가 정의되어 있습니다.

---

## 🔍 Stage별 헤더 정렬 순서

### Stage 1: Data Synchronization (data_synchronizer_v30.py)

**목적**: HITACHI와 SIEMENS 원본 데이터 병합 및 정규화

**정렬 방식**: 기능별 그룹화
```
base_cols + WAREHOUSE_ORDER + Shifting + SITE_ORDER + Source_Sheet
```

#### 창고 컬럼 순서 (WAREHOUSE_ORDER)
```python
WAREHOUSE_ORDER = [
    "DHL WH",          # 1
    "DSV Indoor",      # 2
    "DSV Al Markaz",   # 3
    "Hauler Indoor",   # 4
    "DSV Outdoor",     # 5
    "DSV MZP",         # 6
    "HAULER",          # 7
    "JDN MZD",         # 8
    "MOSB",            # 9
    "AAA Storage",     # 10
]
```

#### 현장 컬럼 순서 (SITE_ORDER)
```python
SITE_ORDER = [
    "MIR",  # 1
    "SHU",  # 2
    "AGI",  # 3
    "DAS",  # 4
]
```

#### 최종 컬럼 구조
1. **기본 컬럼** (base_cols): 식별 정보, 치수, 날짜 등
2. **창고 컬럼** (10개): WAREHOUSE_ORDER
3. **Shifting 컬럼** (1개)
4. **현장 컬럼** (4개): SITE_ORDER
5. **Source_Sheet** (1개): 메타데이터

**로그 확인 (성공 케이스)**:
```
[OK] Column order: base + warehouses(10) + Shifting + sites(4) + Source_Sheet
```

---

### Stage 2: Derived Columns (STAGE2_HEADER_ORDER)

**목적**: 파생 컬럼 추가 (SQM, Stack_Status, Status_* 등)

**표준 순서** (총 64개 컬럼):

```python
STAGE2_HEADER_ORDER = [
    # 1-9: 기본 식별 정보
    "no.",
    "Shipment Invoice No.",
    "SCT Ref.No",          # ⭐ 3번째 위치 (중요)
    "Site",
    "EQ No",
    "Case No.",
    "Pkg",
    "Storage",
    "Description",
    
    # 10-15: 치수 정보
    "L(CM)",
    "W(CM)",
    "H(CM)",
    "CBM",
    "N.W(kgs)",
    "G.W(kgs)",
    
    # 16-24: 물류 정보
    "Stack",
    "HS Code",
    "Currency",
    "Price",
    "Vessel",
    "COE",
    "POL",
    "POD",
    "ETD/ATD",
    "ETA/ATA",
    
    # 25-34: 창고 컬럼 (10개) - Stage 1과 동일
    "DHL WH",
    "DSV Indoor",
    "DSV Al Markaz",
    "Hauler Indoor",
    "DSV Outdoor",
    "DSV MZP",
    "HAULER",
    "JDN MZD",
    "MOSB",
    "AAA Storage",
    
    # 35: Shifting
    "Shifting",
    
    # 36-39: 현장 컬럼 (4개)
    "MIR",
    "SHU",
    "AGI",
    "DAS",
    
    # 40: 메타데이터
    "Source_Sheet",
    
    # 41-46: 상태 정보 (파생 컬럼)
    "Status_WAREHOUSE",
    "Status_SITE",
    "Status_Current",
    "Status_Location",
    "Status_Location_Date",
    "Status_Storage",
    
    # 47-51: Handling 정보 (파생 컬럼)
    "wh handling",          # ⚠️ Stage 2 원본 (공백 1개)
    "site  handling",       # ⚠️ Stage 2 원본 (공백 2개)
    "total handling",
    "minus",
    "final handling",
    
    # 52-53: SQM 계산 (파생 컬럼)
    "SQM",                  # L × W × H / 10000
    "Stack_Status",         # Stack 필드 파싱
]
```

**특이 사항**:
- `"wh handling"`: 공백 1개
- `"site  handling"`: 공백 2개 (의도적)
- Stage 3에서 추가되는 컬럼은 제외됨

---

### Stage 3: Final Report (STANDARD_HEADER_ORDER)

**목적**: 최종 통합 보고서 생성 (통합_원본데이터_Fixed 시트)

**표준 순서** (총 64개 컬럼 + 추가 메타 컬럼):

```python
STANDARD_HEADER_ORDER = [
    # 1-25: Stage 2와 동일 (기본 식별 ~ 물류 정보)
    
    # 26-35: 창고 컬럼 (10개) - Stage 1/2와 동일
    "DHL WH",
    "DSV Indoor",
    "DSV Al Markaz",
    "Hauler Indoor",
    "DSV Outdoor",
    "DSV MZP",
    "HAULER",
    "JDN MZD",
    "MOSB",
    "AAA Storage",
    
    # 36: Shifting
    "Shifting",
    
    # 37-40: 현장 컬럼 (4개)
    "MIR",
    "SHU",
    "AGI",
    "DAS",
    
    # 41: 메타데이터
    "Source_Sheet",
    
    # 42-47: 상태 정보
    "Status_WAREHOUSE",
    "Status_SITE",
    "Status_Current",
    "Status_Location",
    "Status_Location_Date",
    "Status_Storage",
    
    # 48-52: Handling 정보 (⚠️ 정규화됨)
    "wh_handling_legacy",   # ⭐ Stage 3에서 "wh handling" → 변경
    "site handling",        # ⭐ 공백 1개로 정규화
    "total handling",
    "minus",
    "final handling",
    
    # 53-55: SQM 및 Stack
    "SQM",
    "Stack_Status",
    "Total sqm",            # ⭐ Stage 3 추가: PKG × SQM × Stack_Status
    
    # 56-64: Stage 3 추가 메타 컬럼
    "Vendor",
    "Source_File",
    "Status_Location_YearMonth",
    "site_handling_original",
    "total_handling_original",
    "wh_handling_original",
    "FLOW_CODE",
    "FLOW_DESCRIPTION",
    "Final_Location",
    
    # 65: 입고일자
    "입고일자",
]
```

**주요 변경 사항**:
- `"wh handling"` → `"wh_handling_legacy"` (언더스코어 사용)
- `"site  handling"` (공백 2개) → `"site handling"` (공백 1개)
- `"Total sqm"` 추가: PKG × SQM × Stack_Status
- 9개 메타 컬럼 추가 (FLOW_CODE, Final_Location 등)

---

## 🔄 헤더 매칭 메커니즘

### FlexibleHeaderMatcher (core/standard_header_order.py)

**3단계 매칭 전략**:

1. **정확 매칭** (Exact Match)
   - 대소문자 구분 없이 정확히 일치
   - 예: `"Case No."` = `"Case No."`

2. **정규화 매칭** (Normalized Match)
   - HeaderNormalizer 사용
   - 공백, 대소문자, 특수문자 정규화
   - 예: `"AAA  Storage"` → `"AAA Storage"`

3. **의미론적 매칭** (Semantic Match)
   - difflib.SequenceMatcher 사용
   - 유사도 임계값: 0.8
   - 예: `"site  handling"` ≈ `"site handling"` (유사도: 0.96)

### HeaderNormalizer (core/header_normalizer.py)

**정규화 규칙**:
```python
def normalize(header: str) -> str:
    # 1. 소문자 변환
    # 2. 공백 정규화 (다중 공백 → 단일 공백)
    # 3. 특수문자 제거
    # 4. 양끝 공백 제거
```

---

## 📊 실제 실행 로그 분석

### Stage 1 출력 (SIEMENS 통합 성공)

```
[OK] Merged 'Case List, RIL': HITACHI(5853) + SIEMENS(2303) = 8156 rows
[INFO] Master and Warehouse are the same file - using merged Master data
- 합쳐진 데이터: 8388행, 51컬럼
[OK] Column order: base + warehouses(10) + Shifting + sites(4) + Source_Sheet
```

**분석**:
- ✅ HITACHI + SIEMENS 병합 성공
- ✅ 창고 10개 + 현장 4개 컬럼 순서 유지
- ✅ Source_Sheet 컬럼 끝에 배치

---

### Stage 3 출력 (헤더 재정렬)

```
🔄 헤더 재정렬 시작 (Stage 3): 73개 컬럼
헤더 매칭 완료: 66/73개 (90.4%)
✅ 헤더 재정렬 완료: 65개 표준 순서, 8개 추가 컬럼
```

**분석**:
- ✅ 73개 컬럼 중 66개 매칭 성공 (90.4%)
- ✅ 65개 컬럼은 표준 순서로 정렬
- ✅ 8개 컬럼은 추가 컬럼으로 끝에 배치
- ⚠️ 7개 컬럼 매칭 실패 (표준 순서에 없는 컬럼)

---

### Stage 3 SQM/Stack 검증

```
[SUCCESS] SQM: 7971개 계산됨 (95.0%)
[SUCCESS] Stack_Status: 8316개 파싱됨 (99.1%)
```

**분석**:
- ✅ SQM 계산: 8388행 중 7971행 (95.0%) 성공
- ✅ Stack_Status 파싱: 8388행 중 8316행 (99.1%) 성공
- ℹ️ 누락 원인: 원본 데이터 치수 정보 없음 (L, W, H)

---

## 🎯 핵심 정렬 규칙 요약

### 공통 원칙

1. **창고 우선** (Warehouse First)
   - 창고 10개 → Shifting → 현장 4개
   - 모든 Stage에서 동일한 순서 유지

2. **메타데이터 후순위** (Metadata Last)
   - Source_Sheet는 항상 끝에 배치
   - Stage 3 추가 메타 컬럼도 끝에 배치

3. **기본 정보 선순위** (Core Info First)
   - 식별 정보 (no., Invoice, Case No. 등)
   - 치수 정보 (L, W, H, CBM 등)
   - 물류 정보 (ETD, ETA 등)

### Stage별 차이점

| 항목 | Stage 1 | Stage 2 | Stage 3 |
|------|---------|---------|---------|
| **컬럼 수** | ~51개 | ~64개 | ~73개 |
| **정렬 방식** | 그룹화 | 표준 순서 | 표준 순서 + 추가 |
| **wh handling** | - | "wh handling" | "wh_handling_legacy" |
| **site handling** | - | "site  handling" (공백 2개) | "site handling" (공백 1개) |
| **Total sqm** | - | ❌ | ✅ (추가) |
| **Flow/Location** | - | ❌ | ✅ (추가) |

---

## 🔧 사용 방법

### Stage 2에서 헤더 재정렬

```python
from scripts.core.standard_header_order import reorder_dataframe_columns

# Stage 2 출력 재정렬
df_stage2 = reorder_dataframe_columns(df, is_stage2=True)
```

### Stage 3에서 헤더 재정렬

```python
# Stage 3 출력 재정렬
df_stage3 = reorder_dataframe_columns(df, is_stage2=False)
```

### 유연한 매칭 비활성화

```python
# 의미론적 매칭 비활성화 (정확 매칭만 사용)
df = reorder_dataframe_columns(df, use_semantic_matching=False)
```

---

## ⚠️ 주의 사항

1. **공백 민감성**
   - `"site handling"` (공백 1개) ≠ `"site  handling"` (공백 2개)
   - HeaderNormalizer가 자동 정규화하지만, 원본 컬럼명 확인 필요

2. **SCT Ref.No 위치**
   - 항상 3번째 위치 유지 (중요)
   - 임의로 순서 변경 금지

3. **Stage 3 추가 컬럼**
   - Stage 2 출력에 Stage 3 전용 컬럼 포함 금지
   - 예: Total sqm, FLOW_CODE, Final_Location

4. **매칭 실패 시**
   - keep_unlisted=True (기본값): 끝에 추가
   - keep_unlisted=False: 제거

---

## 📈 성능 지표

| 항목 | 값 | 비고 |
|------|-----|------|
| **헤더 매칭률** | 90.4% | Stage 3 기준 |
| **표준 순서 컬럼** | 65개 | 73개 중 |
| **추가 컬럼** | 8개 | 표준 순서에 없음 |
| **SQM 계산률** | 95.0% | 8388행 중 7971행 |
| **Stack 파싱률** | 99.1% | 8388행 중 8316행 |

---

## 🎉 결론

HVDC Pipeline은 3단계에 걸쳐 점진적으로 컬럼을 추가하고 정렬하는 전략을 사용합니다:

1. **Stage 1**: 원본 데이터 병합 및 기본 정렬 (그룹화)
2. **Stage 2**: 파생 컬럼 추가 및 표준 순서 적용
3. **Stage 3**: 최종 메타 컬럼 추가 및 완전한 표준 순서 적용

각 Stage는 독립적인 헤더 순서를 유지하면서도, **창고 10개 + Shifting + 현장 4개**의 핵심 순서는 모든 Stage에서 일관되게 유지됩니다.

**핵심 성공 요소**:
- ✅ SIEMENS 통합 성공 (8,388행)
- ✅ 헤더 매칭률 90.4% (66/73개)
- ✅ SQM/Stack 계산률 95%+ 
- ✅ 전체 파이프라인 성공 (321.43초)

---

**생성일**: 2025-10-26  
**버전**: HVDC Pipeline v3.6 (SIEMENS Integration)


