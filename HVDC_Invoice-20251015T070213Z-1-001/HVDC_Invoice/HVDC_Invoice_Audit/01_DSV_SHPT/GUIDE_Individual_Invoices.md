# 개별 인보이스 시트 가이드

**버전**: 1.0  
**최종 업데이트**: 2025-10-17  
**대상**: HVDC Invoice Audit - 개별 인보이스 시트 사용자  

---

## 목차

1. [개요](#1-개요)
2. [시트 구조](#2-시트-구조)
3. [월별 특징](#3-월별-특징)
4. [통합 시스템](#4-통합-시스템)
5. [사용 방법](#5-사용-방법)
6. [데이터 분석](#6-데이터-분석)
7. [문제 해결](#7-문제-해결)
8. [고급 기능](#8-고급-기능)
9. [FAQ](#9-faq)
10. [참조 문서](#10-참조-문서)

---

## 1. 개요

### 1.1 개별 인보이스 시트란?

개별 인보이스 시트는 각 인보이스의 **상세 라인 항목 데이터**를 포함하는 Excel 시트입니다. 인보이스 요약이 아닌 **항목별 상세 정보**를 제공합니다.

**핵심 특징**:
- **1 row = 1 item** (Master DO, Customs, THC 등 개별 항목)
- 상세 비용 구조 (RATE SOURCE, DESCRIPTION, RATE, Q'TY, TOTAL)
- Order Ref별 상세 분석 가능
- 평균 6.1 라인/인보이스

### 1.2 목적 및 용도

**비용 분석**:
- RATE SOURCE별 비용 구조 (Contract vs At Cost)
- DESCRIPTION별 항목 분석
- RATE 분포 및 이상치 탐지

**데이터 검증**:
- 개별 항목 합계 vs 월별 시트 GRAND TOTAL
- 누락 항목 추적
- 계산 오류 검증

**상세 보고**:
- Order Ref별 상세 내역
- 항목별 단가 분석
- 계약 vs 실제 비용 비교

### 1.3 커버 기간

**2024년 8월 ~ 2025년 9월** (14개월)

| 기간 | 시트 수 | 총 데이터 | 유니크 Order Ref |
|------|---------|----------|------------------|
| 2024년 8-12월 | ~130개 | 625 rows | ~90개 |
| 2025년 1-9월 | ~277개 | 1,541 rows | ~266개 |
| **합계** | **407+** | **2,166 rows** | **356개** |

---

## 2. 시트 구조

### 2.1 시트 이름 패턴

개별 인보이스 시트는 다음과 같은 이름 패턴을 가집니다:

| 접두사 | 의미 | 예시 | 특징 |
|--------|------|------|------|
| **SCT** | Standard Container | SCT0001, SCT0029 | 일반 컨테이너 운송 |
| **SIM** | Simulation/Special | SIM0017, SIM0021-DG | 특수 시뮬레이션 |
| **HE** | Heavy Equipment | HE0173, HE0185 | 중장비 운송 |
| **SEI** | Special Equipment | SEI0006, SEI0017-1 | 특수 장비 |
| **ZEN** | Zenith | ZEN0001, ZEN0003 | Zenith 프로젝트 |

**이름 패턴**:
- 기본: `PREFIX0000` (예: SCT0001)
- 특수: `PREFIX0000-SUFFIX` (예: SEI0017-1, SIM0021-DG)
- 복합: `PREFIX0000,0000` (예: SCT0082,0084)

**전체 407+ 시트 예시**:
```
SCT0001, SCT0015, SCT0029, SCT0037, SCT0050~SCT0134
SIM0006DG, SIM0017, SIM0021-DG, SIM0024-DG, SIM0038-DG
HE0173~0244, HE0301-0310, HE0350~HE0502
SEI0006, SEI0011, SEI0014, SEI0017-1, SEI0021T-L
ZEN0001~ZEN0018
```

### 2.2 헤더 구조

**VBA 기준 15개 표준 헤더**:

| 순서 | 컬럼명 | 설명 | 필수 |
|------|--------|------|------|
| 1 | **Source_File** | 파일명 (AUG 2024, FEB 2025, ...) | ✅ |
| 2 | **No** | 통합 순번 (1-2166) | ✅ |
| 3 | **Month** | 월 (2024-08, 2025-02, ...) | ✅ |
| 4 | **CWI Job Number** | Job 번호 | - |
| 5 | **Order Ref. Number** | 주문 번호 (HVDC-ADOPT-SCT-0001) | ✅ |
| 6 | **S/No** | 항목 순번 (1, 2, 3, ...) | ✅ |
| 7 | **DESCRIPTION** | 항목 설명 (Master DO Charges, ...) | ✅ |
| 8 | **RATE SOURCE** | 요금 출처 (Contract, At Cost) | ✅ |
| 9 | **RATE** | 단가 (150, 0.01, ...) | ✅ |
| 10 | **Formula** | 계산 수식 | - |
| 11 | **Q'TY** | 수량 (1, 1000, ...) | - |
| 12 | **TOTAL (USD)** | 총 금액 (150.00, ...) | ✅ |
| 13 | **REV RATE** | 수정 단가 | - |
| 14 | **REV TOTAL** | 수정 총액 | - |
| 15 | **DIFFERENCE** | 차이 | - |

**추가 컬럼** (원본 시트의 167개):
- Container #, IN Date, OUT Date, Amount
- BOE, BOE Issued Date, Delivery Date
- POL, POD, Mode, Type
- 기타 프로젝트별 커스텀 컬럼

**헤더 위치 (월별 다름)**:
- **Row 7**: OCT~DEC 2024, JAN 2025
- **Row 8**: FEB~JUN 2025
- **Row 12-13**: JUL~SEP 2025

### 2.3 데이터 구조

**상세 라인 항목** (1 row = 1 item):

```
헤더 Row (7, 8, 또는 12-13): S/No | RATE SOURCE | DESCRIPTION | RATE | Q'TY | TOTAL (USD)
데이터 Row 1: 1 | Contract | Master DO Charges | 150 | 1 | 150.00
데이터 Row 2: 2 | At Cost | Customs Clearance Charges | 150 | 1 | 150.00
데이터 Row 3: 3 | Contract | THC | 0.01 | 3550.08 | 3550.08
...
```

**샘플 데이터 (SCT0037 예시)**:

| S/No | RATE SOURCE | DESCRIPTION | RATE | Q'TY | TOTAL (USD) |
|------|-------------|-------------|------|------|-------------|
| 1 | Contract | Master DO Charges | 150 | 1 | 150.00 |
| 2 | At Cost | Customs Clearance Charges | 150 | 1 | 150.00 |
| 3 | Contract | THC | 0.01 | 3550.08 | 3550.08 |
| 4 | At Cost | Transportation Charges | 0.01 | 3550.08 | 3550.08 |
| ... | ... | ... | ... | ... | ... |

**평균 통계**:
- **평균 6.1 라인/인보이스** (2,166 rows / 356 Order Ref)
- 최소: 1 라인 (단순 인보이스)
- 최대: 28 라인 (복잡한 인보이스)

---

## 3. 월별 특징

### 3.1 헤더 위치 분포

**월별로 헤더 행이 다름**:

| 월 | 헤더 Row | 시트 수 | 비고 |
|----|---------|---------|------|
| **AUG 2024** | Row 12 | 11개 | 2024년 후반 |
| **SEP 2024** | Row 7 | 11개 | |
| **OCT 2024** | Row 7 | 24개 | |
| **NOV 2024** | Row 7 | 24개 | |
| **DEC 2024** | Row 7-8 | 23개 | 혼재 |
| **JAN 2025** | Row 7 | 30개 | |
| **FEB 2025** | Row 8 | 25개 | 2025년 전반 |
| **MAR 2025** | Row 8 | 36개 | |
| **APR 2025** | Row 8 | 37개 | |
| **MAY 2025** | Row 8 | 36개 | |
| **JUN 2025** | Row 8 | 57개 (Batch1+2) | |
| **JUL 2025** | Row 12 | 42개 | 2025년 후반 |
| **AUG 2025** | Row 12 | 31개 | |
| **SEP 2025** | Row 12 | 29개 | |

**검증 결과**: ✅ **헤더 감지 성공률 100%** (407+ 시트 모두 성공)

### 3.2 S/No 패턴

**S/No 존재 여부**:

| 패턴 | 시트 수 | 비율 | 처리 방법 |
|------|---------|------|----------|
| **S/No 있음** | ~380개 | 91% | `_extract_with_sno()` |
| **S/No 없음** | ~27개 | 9% | `_extract_without_sno()` + 자동 생성 |

**S/No 없는 시트 예시**:
- OCT 2024: SCT0016, SCT0017 (RATE SOURCE부터 시작)
- DEC 2024: SCT0023, SCT0022 (RATE SOURCE부터 시작)
- JAN 2025: SCT0026, SCT0028 (RATE SOURCE부터 시작)

**자동 S/No 생성**:
```python
# S/No 없는 시트는 1부터 자동 번호 생성
df['S/No'] = range(1, len(df) + 1)
```

### 3.3 RATE SOURCE 패턴

**RATE SOURCE 분포** (2,166 rows 기준):

| RATE SOURCE | 개수 | 비율 | 의미 |
|-------------|------|------|------|
| **Contract** | 955 | 44.1% | 계약 단가 |
| **At Cost** | 652 | 30.1% | 실비 정산 |
| **CONTRACT** (대문자) | 257 | 11.9% | 계약 단가 (표기 차이) |
| **AT COST** (대문자) | 120 | 5.5% | 실비 정산 (표기 차이) |
| **Cost** | 58 | 2.7% | 비용 |
| **As per offer** | 39 | 1.8% | 제안서 기준 |
| **At cost** (소문자) | 29 | 1.3% | 실비 정산 (표기 차이) |
| **DUTY** | 21 | 1.0% | 관세 |
| 기타 (10종) | 32 | 1.5% | DSV Service, Contact, ... |
| **NaN** | **3** | **0.1%** | 누락 |

**표준화 권장**:
- "Contract" + "CONTRACT" = 1,212 (55.9%)
- "At Cost" + "AT COST" + "At cost" = 801 (37.0%)

### 3.4 DESCRIPTION 패턴

**주요 DESCRIPTION 항목**:

| DESCRIPTION | 빈도 | 비고 |
|-------------|------|------|
| Master DO Charges | 높음 | 기본 항목 |
| Customs Clearance Charges | 높음 | 기본 항목 |
| THC (Terminal Handling Charge) | 높음 | 기본 항목 |
| Transportation Charges | 높음 | 운송비 |
| Port Handling Charges | 중간 | 항만 처리 |
| House DO Charges | 중간 | |
| Storage Charges | 낮음 | 보관료 |
| Duty | 낮음 | 관세 |

---

## 4. 통합 시스템

### 4.1 핵심 기술

#### 1. Robust Header Detection

**Fuzzy 매칭 기반 동적 헤더 감지**:

```python
from rapidfuzz import fuzz

class HeaderDetector:
    def __init__(self, df_preview, threshold=78):
        self.df_preview = df_preview
        self.threshold = threshold
    
    def find_header_row(self):
        """
        Row 1-25 스캔하여 헤더 행 자동 감지
        
        특징:
        - Fuzzy 매칭으로 오타/변형 처리
        - 단일행/2행 조합 헤더 지원
        - 동의어 자동 매핑
        """
        for row_idx in range(1, 26):
            score = self._calculate_header_score(row_idx)
            if score >= self.threshold:
                return row_idx
        return None
```

**지원 기능**:
- **오타 처리**: "RATE SORUCE" → "RATE SOURCE"
- **변형 처리**: "Q'TY" → "QTY", "TOTAL(USD)" → "TOTAL (USD)"
- **2행 조합**: Row N + Row N+1 자동 조합

#### 2. 자동 S/No 생성

**S/No 없는 시트 자동 처리**:

```python
def _extract_without_sno(self, ws, sheet_name, month, file_name):
    """
    S/No가 없는 시트 처리
    
    1. 필수 컬럼(DESCRIPTION, RATE, TOTAL) 기반 헤더 감지
    2. 데이터 추출
    3. S/No 자동 생성 (1, 2, 3, ...)
    """
    # 필수 컬럼으로 헤더 행 찾기
    header_row = self._find_header_by_required_columns(ws)
    
    # 데이터 추출
    df = self._extract_data(ws, header_row)
    
    # S/No 자동 생성
    df['S/No'] = range(1, len(df) + 1)
    
    return df
```

#### 3. VBA 로직 준수 표준화

**VBA 기준 15개 표준 헤더 적용**:

```python
# VBA 로직 (modCompileMaster.bas)
headers = Array(
    "CWI Job Number", "Order Ref. Number", "S/No", 
    "RATE SOURCE", "DESCRIPTION", "RATE", 
    "Formula", "Q'TY", "TOTAL (USD)", 
    "REV RATE", "REV TOTAL", "DIFFERENCE"
)

# Python 표준화
standard_columns = [
    'Source_File', 'No', 'Month',  # 통합 시 추가
    'CWI Job Number', 'Order Ref. Number', 'S/No',
    'DESCRIPTION', 'RATE SOURCE', 'RATE',
    'Formula', "Q'TY", 'TOTAL (USD)',
    'REV RATE', 'REV TOTAL', 'DIFFERENCE'
]
```

**컬럼명 정규화**:
```python
# 다양한 변형을 표준명으로 통일
column_mapping = {
    'RATE SORUCE': 'RATE SOURCE',  # 오타
    'TOTAL(USD)': 'TOTAL (USD)',
    'TOTAL (INR)': 'TOTAL (USD)',
    'Q ty': "Q'TY",
    'Qty': "Q'TY",
    'QTY': "Q'TY",
}
```

### 4.2 통합 방법

**스크립트**: `consolidate_all_months.py`

**핵심 클래스**: `InvoiceConsolidatorV2`

**처리 흐름**:

```
1. Excel 파일 열기 (openpyxl)
2. 인보이스 시트 필터링
   - 제외: Summary, FEB, MAR, APR, ... (월별 시트)
   - 포함: SCT*, SIM*, HE*, SEI*, ZEN*
3. 각 시트별 처리:
   a. S/No 키워드 검색 (Row 1-25)
      → 있으면: _extract_with_sno()
      → 없으면: 다음 단계
   b. Robust Header Detection (Fuzzy 매칭)
      → 성공하면: apply_header()
      → 실패하면: 다음 단계
   c. 필수 컬럼 기반 폴백
      → _extract_without_sno()
4. 데이터 병합 (pd.concat)
5. 컬럼 표준화
   - 컬럼명 정규화
   - VBA 로직 순서 적용
   - 중복 컬럼 제거
6. Source_File, No, Month 추가
7. Excel 출력
```

### 4.3 통합 결과

**최종 파일**: `out/masterdata_all_months_YYYYMMDD_HHMMSS.xlsx`

**통계**:
- **총 행 수**: 2,166 rows
- **총 컬럼 수**: 182 columns
- **처리 시트 수**: 407+ sheets
- **유니크 Order Ref**: 356개

**데이터 품질**:

| 항목 | 데이터 있음 | 비율 | 상태 |
|------|------------|------|------|
| Source_File | 2166 / 2166 | 100.0% | ✅ |
| Month | 2166 / 2166 | 100.0% | ✅ |
| Order Ref. Number | 2166 / 2166 | 100.0% | ✅ |
| DESCRIPTION | 2166 / 2166 | 100.0% | ✅ |
| RATE | 2164 / 2166 | 99.9% | ✅ |
| TOTAL (USD) | 2161 / 2166 | 99.8% | ✅ |
| **RATE SOURCE** | **2163 / 2166** | **99.9%** | ✅ |

**파일 위치**: `HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems/out/`

---

## 5. 사용 방법

### 5.1 통합 실행

#### 단계 1: 환경 준비

```bash
cd HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems
```

#### 단계 2: 통합 실행

```bash
python consolidate_all_months.py
```

**소요 시간**: 약 2-3분 (407+ 시트 처리)

#### 단계 3: 결과 확인

```
================================================================================
[SUCCESS] MULTI-MONTH CONSOLIDATION COMPLETE!
================================================================================
Total rows: 2166
Total months: 14
Total columns: 182

Months covered:
  - 2024-08 (AUG 2024): 93 rows
  - 2024-09 (SEP 2024): 81 rows
  - 2024-10 (OCT 2024): 124 rows
  - 2024-11 (NOV 2024): 175 rows
  - 2024-12 (DEC 2024): 152 rows
  - 2025-01 (JANUARY 2025): 249 rows
  - 2025-02 (FEBRUARY 2025): 142 rows
  - 2025-03 (MARCH 2025): 143 rows
  - 2025-04 (APRIL 2025): 150 rows
  - 2025-05 (MAY 2025): 151 rows
  - 2025-06 (JUNE 2025): 300 rows
  - 2025-07 (JULY 2025): 171 rows
  - 2025-08 (AUG 2025): 133 rows
  - 2025-09 (SEPT 2025): 102 rows

Output: out/masterdata_all_months_20251017_071130.xlsx
```

### 5.2 결과 확인

#### Python으로 확인:

```python
import pandas as pd

# 파일 읽기
df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# 기본 정보
print(f"총 행 수: {len(df)}")
print(f"총 컬럼 수: {len(df.columns)}")
print(f"유니크 Order Ref: {df['Order Ref. Number'].nunique()}")

# 월별 분포
print("\n월별 데이터 분포:")
print(df['Source_File'].value_counts().sort_index())

# 필수 컬럼 체크
print("\n필수 컬럼 완전성:")
for col in ['DESCRIPTION', 'RATE SOURCE', 'RATE', 'TOTAL (USD)']:
    if col in df.columns:
        completeness = (df[col].notna().sum() / len(df) * 100)
        print(f"  {col}: {completeness:.1f}%")
```

#### 샘플 데이터 확인:

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# 샘플 데이터 (처음 5행)
print("샘플 데이터:")
print(df[['Source_File', 'Order Ref. Number', 'DESCRIPTION', 
         'RATE SOURCE', 'RATE', 'TOTAL (USD)']].head())
```

### 5.3 검증

#### 월별 통계 확인:

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# 월별 통계
monthly_stats = df.groupby('Source_File').agg({
    'Order Ref. Number': 'nunique',
    'RATE': 'count',
    'TOTAL (USD)': 'sum'
}).rename(columns={
    'Order Ref. Number': '유니크 Order Ref',
    'RATE': '총 행 수',
    'TOTAL (USD)': 'TOTAL 합계'
})

print(monthly_stats)
```

#### RATE SOURCE 분포 확인:

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# RATE SOURCE 분포
rate_source_dist = df['RATE SOURCE'].value_counts()
print("RATE SOURCE 분포:")
print(rate_source_dist)

# 비율
print("\nRATE SOURCE 비율:")
print((rate_source_dist / len(df) * 100).round(1))
```

### 5.4 새로운 월 추가

#### 단계 1: 파일 준비

SHPT 폴더에 새 월 파일 추가:
```
HVDC_Invoice_Audit/01_DSV_SHPT/SHPT/
  - SCNT SHIPMENT DRAFT INVOICE (OCT 2025).xlsx
```

#### 단계 2: 재실행

```bash
python consolidate_all_months.py
```

**자동 감지**: 새 파일이 파일명 패턴 (`SCNT SHIPMENT DRAFT INVOICE (월 연도).*`)에 맞으면 자동으로 포함됨

#### 단계 3: 결과 확인

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_*.xlsx")

# 새 월 확인
print(df['Source_File'].unique())
```

---

## 6. 데이터 분석

### 6.1 Order Ref별 분석

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# Order Ref별 라인 수
order_lines = df.groupby('Order Ref. Number').size().sort_values(ascending=False)

print("라인 수 Top 10:")
print(order_lines.head(10))

# Order Ref별 총액
order_totals = df.groupby('Order Ref. Number')['TOTAL (USD)'].sum().sort_values(ascending=False)

print("\n총액 Top 10:")
print(order_totals.head(10))
```

### 6.2 RATE SOURCE별 비용 분석

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# RATE SOURCE별 총액
rate_source_totals = df.groupby('RATE SOURCE')['TOTAL (USD)'].sum().sort_values(ascending=False)

# 차트
plt.figure(figsize=(10, 6))
rate_source_totals.head(10).plot(kind='barh')
plt.title('RATE SOURCE별 총액 Top 10')
plt.xlabel('TOTAL (USD)')
plt.ylabel('RATE SOURCE')
plt.tight_layout()
plt.show()
```

### 6.3 DESCRIPTION별 빈도 분석

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# DESCRIPTION 빈도
desc_freq = df['DESCRIPTION'].value_counts()

print("DESCRIPTION 빈도 Top 20:")
print(desc_freq.head(20))

# DESCRIPTION별 평균 RATE
desc_avg_rate = df.groupby('DESCRIPTION')['RATE'].mean().sort_values(ascending=False)

print("\nDESCRIPTION별 평균 RATE Top 10:")
print(desc_avg_rate.head(10))
```

### 6.4 월별 트렌드 분석

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# 월별 총액
monthly_totals = df.groupby('Source_File')['TOTAL (USD)'].sum().sort_index()

# 차트
plt.figure(figsize=(14, 6))
monthly_totals.plot(kind='bar')
plt.title('월별 TOTAL (USD) 트렌드')
plt.xlabel('월')
plt.ylabel('TOTAL (USD)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### 6.5 개별 시트 vs 월별 시트 비교

```python
import pandas as pd

# 개별 시트 통합 (상세)
detail_df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

# 월별 시트 통합 (요약)
month_df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

print("=== 데이터 비교 ===")
print(f"개별 시트 (상세): {len(detail_df)} rows")
print(f"월별 시트 (요약): {len(month_df)} rows")
print(f"비율: {len(detail_df) / len(month_df):.1f} 라인/인보이스")

# 월별 금액 비교
detail_monthly = detail_df.groupby('Source_File')['TOTAL (USD)'].sum()
month_monthly = month_df.groupby('Source_Month')['GRAND TOTAL (USD)'].sum()

comparison = pd.DataFrame({
    '개별 시트 합계': detail_monthly,
    '월별 시트 GRAND TOTAL': month_monthly
})
comparison['차이'] = comparison['개별 시트 합계'] - comparison['월별 시트 GRAND TOTAL']
comparison['차이 (%)'] = (comparison['차이'] / comparison['월별 시트 GRAND TOTAL'] * 100).round(2)

print("\n월별 금액 비교:")
print(comparison)
```

---

## 7. 문제 해결

### 7.1 헤더 감지 실패

**증상**:
```
[WARNING] 시트 SCT0099 처리 실패: 헤더를 찾을 수 없음
```

**원인**:
1. 비표준 헤더 위치 (Row 15+)
2. S/No 키워드 없음 + 필수 컬럼 부족
3. Robust Header Detection 임계값 미달

**해결 방법**:

#### 1단계: 원본 시트 확인

```python
import openpyxl

wb = openpyxl.load_workbook("SCNT ... (월 연도).xlsx", data_only=True)
ws = wb['SCT0099']

# Row 1-20 스캔
for row in range(1, 21):
    row_data = []
    for col in range(1, 15):
        val = ws.cell(row, col).value
        row_data.append(str(val)[:20] if val else '')
    print(f"Row {row}: {' | '.join(row_data)}")
```

#### 2단계: 수동 헤더 행 지정

```python
# invoice_consolidator_v2.py 수정
def _extract_sheet_data(self, ws, sheet_name, month, file_name):
    # 특정 시트만 수동 지정
    if sheet_name == 'SCT0099' and 'MAY 2025' in file_name:
        header_row = 15  # 수동 지정
        return self._manual_extract(ws, header_row, ...)
    
    # 기존 자동 감지 로직
    ...
```

#### 3단계: 키워드 확장

```python
# invoice_consolidator_v2.py
# _find_header_by_required_columns() 메서드 수정
required_headers = {
    'DESCRIPTION': ['DESCRIPTION', 'DESCRIPTN', 'DESC', 'DESCRIPTION OF CHARGES'],
    'RATE': ['RATE', 'UNIT PRICE', 'PRICE'],
    'TOTAL': ['TOTAL', 'TOTAL (USD)', 'TOTAL(USD)', 'AMOUNT'],
    'QTY': ["Q'TY", 'QTY', 'QUANTITY', 'Q TY'],
    'RATE SOURCE': ['RATE SOURCE', 'RATE SORUCE', 'SOURCE', 'RATE_SOURCE'],
}
```

### 7.2 RATE SOURCE 누락

**증상**:
- RATE SOURCE 데이터 < 95%

**원인**:
1. 헤더 매핑 실패
2. 빈 Column 1로 인한 컬럼 인덱스 오류
3. "RATE SORUCE" 오타

**해결 방법**:

#### 1단계: 컬럼 매핑 확인

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_*.xlsx")

# RATE SOURCE 누락 확인
missing = df[df['RATE SOURCE'].isna()]
print(f"RATE SOURCE 누락: {len(missing)} rows ({len(missing)/len(df)*100:.1f}%)")

# 누락된 월 확인
print("\n월별 누락:")
print(missing['Source_File'].value_counts())

# 누락된 Order Ref 확인
print("\n누락된 Order Ref:")
print(missing['Order Ref. Number'].unique())
```

#### 2단계: 원본 시트 확인

```python
import openpyxl

# 특정 시트의 RATE SOURCE 컬럼 확인
wb = openpyxl.load_workbook("...(월 연도).xlsx", data_only=True)
ws = wb['SCT0001']

# 헤더 행 찾기
header_row = 8
for col in range(1, ws.max_column + 1):
    header = ws.cell(header_row, col).value
    print(f"Col {col}: {header}")
    
# RATE SOURCE 데이터 확인
rate_source_col = 4  # 예시
print(f"\nRATE SOURCE 데이터 (Col {rate_source_col}):")
for row in range(header_row + 1, header_row + 10):
    print(f"  Row {row}: {ws.cell(row, rate_source_col).value}")
```

#### 3단계: Robust Header Detection 적용

**이미 적용됨** (v2부터):
- Fuzzy 매칭으로 "RATE SORUCE" → "RATE SOURCE" 자동 매핑
- 빈 Column 1 자동 처리
- 동의어 자동 인식

### 7.3 중복 컬럼 오류

**증상**:
```
pandas.errors.InvalidIndexError: Reindexing only valid with uniquely valued Index objects
```

**원인**:
- 동일한 컬럼명이 여러 개 존재
- 예: "TOTAL (USD)", "TOTAL (USD).1", "TOTAL (USD).2"

**해결 방법**:

#### 자동 제거 로직 (이미 적용됨):

```python
# invoice_consolidator_v2.py
def apply_header(res, ws, ...):
    # ...
    
    # 중복 컬럼명 처리
    def make_unique_columns(cols):
        seen = {}
        result = []
        for col in cols:
            if col in seen:
                seen[col] += 1
                result.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                result.append(col)
        return result
    
    df.columns = make_unique_columns(df.columns.tolist())
```

#### 수동 제거 (필요 시):

```python
import pandas as pd

df = pd.read_excel("out/masterdata_all_months_*.xlsx")

# 중복 컬럼 확인
duplicates = [col for col in df.columns if '.1' in col or '_1' in col]
print(f"중복 컬럼: {duplicates}")

# 중복 컬럼 제거
df = df.loc[:, ~df.columns.duplicated()]
```

### 7.4 타입 오류

**증상**:
```
TypeError: '<' not supported between instances of 'str' and 'int'
```

**원인**:
- RATE 컬럼에 문자열 포함 (숫자 비교 실패)
- 컬럼명에 정수가 섞임 (정렬 실패)

**해결 방법** (이미 적용됨):

```python
# invoice_consolidator_v2.py
def _validate_extracted_data(self, df):
    # RATE 컬럼 타입 안전성
    if 'RATE' in df.columns:
        negative_rate = len(df[pd.to_numeric(df['RATE'], errors='coerce') < 0])
    
    # ...

# multi_month_consolidator.py
def _standardize_output(self, df):
    # 컬럼명 타입 안전성
    remaining_columns = sorted([str(col) for col in df.columns if col not in standard_columns])
```

### 7.5 데이터 손실

**증상**:
- 특정 컬럼 데이터가 대부분 NaN (예: TOTAL (USD) 3.3%)

**원인**:
- 컬럼명 변형 (TOTAL(USD), TOTAL (INR), ...)이 병합되지 않음
- 표준화 로직 미적용

**해결 방법** (이미 적용됨):

```python
# multi_month_consolidator.py
def _standardize_output(self, df):
    # TOTAL (USD) 변형들 병합 (coalesce)
    total_variants = [
        'TOTAL (USD)', 'TOTAL(USD)', 'TOTAL (INR)',
        'TOTAL', 'Total (USD)', 'Total'
    ]
    
    # 첫 번째 non-null 값 사용
    for variant in total_variants:
        if variant in df.columns and variant != 'TOTAL (USD)':
            df['TOTAL (USD)'] = df['TOTAL (USD)'].fillna(df[variant])
            df = df.drop(columns=[variant])
```

---

## 8. 고급 기능

### 8.1 Robust Header Detection 사용

```python
from invoice_consolidator_v2 import HeaderDetector
import openpyxl
import pandas as pd

# Excel 파일 열기
wb = openpyxl.load_workbook("...(월 연도).xlsx", data_only=True)
ws = wb['SCT0001']

# DataFrame 미리보기 생성 (처음 25행)
preview_data = []
for row in ws.iter_rows(min_row=1, max_row=25, values_only=True):
    preview_data.append(row)
df_preview = pd.DataFrame(preview_data)

# Robust Header Detection 실행
detector = HeaderDetector(df_preview, threshold=78)
result = detector.find_header_row()

if result.success:
    print(f"헤더 행 감지 성공: Row {result.row_idx}")
    print(f"감지 방법: {result.method}")
    print(f"감지된 컬럼: {list(result.col_map.keys())}")
else:
    print("헤더 감지 실패")
```

### 8.2 커스텀 동의어 추가

```python
# invoice_consolidator_v2.py 수정

# 동의어 사전 확장
_SYNONYMS = {
    'sno': ['s/no', 's.no', 'serial no', 's no', 'item no', 'no.'],  # 추가: 'item no'
    'ratesource': ['rate source', 'rate soruce', 'source', 'rate_source', 'price source'],  # 추가
    'description': ['description', 'descriptn', 'desc', 'item', 'item description'],  # 추가
    'rate': ['rate', 'unit price', 'price', 'unit rate', 'cost'],  # 추가
    # ...
}
```

### 8.3 특정 시트만 처리

```python
# consolidate_all_months.py 수정

from pathlib import Path
from invoice_consolidator_v2 import InvoiceConsolidatorV2

# 특정 월/시트만 처리
target_month = 'FEBRUARY 2025'
target_sheets = ['SCT0037', 'SCT0029', 'SCT0038']

shpt_folder = Path("../SHPT")
file_path = shpt_folder / f"SCNT SHIPMENT DRAFT INVOICE ({target_month})_rev2.xlsm"

consolidator = InvoiceConsolidatorV2()
result = consolidator.process_file(file_path, target_sheets)

print(f"처리된 시트: {len(result)} rows")
result.to_excel(f"out/partial_{target_month}.xlsx", index=False)
```

### 8.4 로그 레벨 조정

```python
import logging

# 로그 레벨 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 파일 핸들러 추가
file_handler = logging.FileHandler('consolidation_debug.log')
file_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(file_handler)

# 통합 실행
from multi_month_consolidator import MultiMonthConsolidator

consolidator = MultiMonthConsolidator(shpt_folder)
result = consolidator.consolidate_all_months()
```

---

## 9. FAQ

### Q1. 개별 시트와 월별 시트의 차이는?

**A1**: [GUIDE_Monthly_Summary.md Q1](GUIDE_Monthly_Summary.md#q1-월별-시트와-개별-시트의-차이는) reference

| 항목 | 개별 시트 | 월별 시트 |
|------|----------|----------|
| 데이터 레벨 | 상세 (라인 항목) | 요약 (인보이스별) |
| 행 수 | 2,166 rows | 406 rows |
| 1 row | 1 item | 1 invoice |

### Q2. Robust Header Detection이 무엇인가요?

**A2**:

**Robust Header Detection**은 Fuzzy 매칭 기반 동적 헤더 감지 시스템입니다.

**주요 기능**:
- **오타 처리**: "RATE SORUCE" → "RATE SOURCE" (78% 유사도로 자동 매칭)
- **2행 조합**: Row N + Row N+1 자동 조합 (머지셀 처리)
- **동의어 인식**: "Q'TY", "Qty", "QTY" → 모두 "Q'TY"로 통일
- **휴리스틱 폴백**: Fuzzy 매칭 실패 시 텍스트 비율 기반 휴리스틱

**적용 전 (4.6% RATE SOURCE) vs 적용 후 (99.6% RATE SOURCE)**

### Q3. S/No가 없는 시트는 어떻게 처리되나요?

**A3**:

**자동 S/No 생성**:

```python
# S/No 없는 시트 예시: SCT0016, SCT0017 (OCT 2024)
# 원본 시트: RATE SOURCE | DESCRIPTION | RATE | ...

# 처리 후:
# S/No | RATE SOURCE | DESCRIPTION | RATE | ...
# 1    | Contract    | Master DO   | 150  | ...
# 2    | At Cost     | Customs     | 150  | ...
# 3    | Contract    | THC         | 0.01 | ...
```

**영향**: 없음 (자동 번호는 1부터 시작, 시트별 독립적)

### Q4. RATE SOURCE가 99.9%인데 100%가 아닌 이유는?

**A4**:

**누락 3 rows (0.1%)**:
- 원본 Excel 시트에서 이미 비어있음
- 특정 인보이스의 특정 항목만 누락

**확인 방법**:
```python
df = pd.read_excel("out/masterdata_all_months_*.xlsx")
missing = df[df['RATE SOURCE'].isna()]
print(missing[['Source_File', 'Order Ref. Number', 'DESCRIPTION']])
```

**대응**: 99.9% 완전성은 허용 가능 (원본 데이터 확인 필요)

### Q5. 헤더가 Row 7, 8, 12로 다른 이유는?

**A5**:

**시기별 Excel 템플릿 변경**:

- **2024년 9월 ~ 2025년 1월**: Row 7 (초기 템플릿)
- **2025년 2월 ~ 2025년 6월**: Row 8 (중간 템플릿)
- **2024년 8월, 2025년 7-9월**: Row 12 (후기 템플릿)

**자동 감지**: Row 1-25 스캔으로 자동 처리 (하드코딩 제로)

### Q6. TOTAL (USD)가 99.8%인 이유는?

**A6**:

**누락 5 rows (0.2%)**:
- 원본 시트에 데이터 없음
- 또는 계산 수식 오류

**확인**:
```python
df = pd.read_excel("out/masterdata_all_months_*.xlsx")
missing = df[df['TOTAL (USD)'].isna()]
print(missing[['Source_File', 'Order Ref. Number', 'DESCRIPTION', 'RATE', "Q'TY"]])
```

**대응**: 원본 시트 확인 후 수동 수정 또는 계산 수식 확인

### Q7. 통합 시간이 오래 걸리는 이유는?

**A7**:

**소요 시간**: 약 2-3분 (407+ 시트)

**주요 원인**:
1. **openpyxl 느림**: Excel 파일 열기가 느림
2. **Robust Header Detection**: Fuzzy 매칭 계산
3. **데이터 추출**: 각 시트별 헤더 감지 + 데이터 추출

**개선 가능**:
- (적용됨) data_only=True로 수식 계산 생략
- (가능) multiprocessing으로 병렬 처리 (복잡도 증가)

### Q8. 새 월을 추가하려면?

**A8**:

1. SHPT 폴더에 파일 추가
2. `python consolidate_all_months.py` 재실행
3. 자동 감지 및 통합

**파일명 패턴**: `SCNT SHIPMENT DRAFT INVOICE (월 연도).*`

**예시**: `SCNT SHIPMENT DRAFT INVOICE (OCT 2025).xlsx`

---

## 10. 참조 문서

### 기술 보고서

- **[REPORT_Individual_Verification.md](REPORT_Individual_Verification.md)**: Individual invoice verification final report
- **[REPORT_Header_Detection.md](REPORT_Header_Detection.md)**: Robust Header Detection patch report
- **[REPORT_RateSource_Fix.md](REPORT_RateSource_Fix.md)**: RATE SOURCE data fix report

### 구조 분석

- **[Core_Systems/INVOICE_STRUCTURE_VERIFICATION_REPORT.md](Core_Systems/INVOICE_STRUCTURE_VERIFICATION_REPORT.md)**: 15개 파일 407+ 시트 구조 검증 보고서

### 사용자 가이드

- **[USER_GUIDE.md](Documentation/USER_GUIDE.md)**: 전체 시스템 사용자 가이드
- **[GUIDE_Monthly_Summary.md](GUIDE_Monthly_Summary.md)**: Monthly summary sheets guide

### 코드

- **[00_Shared/engine_individual_sheets.py](../00_Shared/engine_individual_sheets.py)**: Consolidation engine (700+ lines)
  - Robust Header Detection system
  - Fuzzy matching logic
  - Auto S/No generation

- **[00_Shared/engine_multi_month.py](../00_Shared/engine_multi_month.py)**: Multi-month processor (280+ lines)
  - 14-month orchestration
  - VBA logic standardization
  - Column coalescing

- **[Core_Systems/run_individual_consolidation.py](Core_Systems/run_individual_consolidation.py)**: Run script

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-10-17  
**작성자**: HVDC Invoice Audit Team  
**문의**: 시스템 관리자

---

## 부록

### A. 시트 이름 패턴 전체 목록

#### SCT (Standard Container) - 약 100+ 시트

```
SCT0001, SCT0011, SCT0012, SCT0015, SCT0016, SCT0017, SCT0018, SCT0019,
SCT0020, SCT0021, SCT0022, SCT0023, SCT0024, SCT0025, SCT0026, SCT0027,
SCT0028, SCT0029, SCT0030, SCT0031, SCT0032, SCT0033, SCT0034, SCT0035,
SCT0036, SCT0037, SCT0038, SCT0040, SCT0041, SCT0042, SCT0043, SCT0044,
SCT0045, SCT0046, SCT0047, SCT0048, SCT0049, SCT0050, SCT0051, SCT0052,
...
SCT0130, SCT0131, SCT0134
```

#### SIM (Simulation/Special) - 약 80+ 시트

```
SIM0006DG, SIM0009-2, SIM0010DG, SIM0012, SIM0013, SIM0014, SIM0015DG,
SIM0016, SIM0017, SIM0017 (2), SIM0018, SIM0019, SIM0020, SIM0021DG,
SIM0024DG, SIM0025, SIM0027DG, SIM0028A, SIM0028B, SIM0029,0034,
SIM0030, SIM0032, SIM0033DG, SIM0035, SIM0038DG, SIM0039, SIM0041DG,
...
```

#### HE (Heavy Equipment) - 약 150+ 시트

```
HE0140, HE0173, HE0174, HE0178, HE0180, HE0181, HE0182, HE0183,0184,
HE0185, HE0186,0202, HE0187, HE0188,0190, HE0189, HE0194,0196,
HE0195,0192,0189, HE0198~HE0213, HE0214, HE0215,0232, HE0223, HE0224,
...
HE0499L1, HE0499L2, HE0499L3, HE0500, HE0501, HE0502
```

#### SEI (Special Equipment) - 약 30+ 시트

```
SEI0006, SEI0008, SEI0009DG, SEI0011, SEI0012, SEI0013, SEI0014,
SEI0015DG, SEI0017-1, SEI0017-2, SEI0018, SEI0021T-L
```

#### ZEN (Zenith) - 약 18+ 시트

```
ZEN0001, ZEN0002, ZEN0003, ZEN0004, ZEN0005, ZEN0007, ZEN0009,
ZEN0010, ZEN0011, ZEN0012, ZEN0014, ZEN0015, ZEN0016, ZEN0017, ZEN0018
```

### B. VBA vs Python 헤더 매핑

| VBA 헤더 (modCompileMaster.bas) | Python 표준 헤더 | 비고 |
|--------------------------------|-----------------|------|
| (추가됨) | Source_File | 통합 시 추가 |
| (추가됨) | No | 통합 시 추가 |
| (추가됨) | Month | 통합 시 추가 |
| CWI Job Number | CWI Job Number | 동일 |
| Order Ref. Number | Order Ref. Number | 동일 |
| S/No | S/No | 동일 |
| RATE SOURCE | RATE SOURCE | 동일 |
| DESCRIPTION | DESCRIPTION | 동일 |
| RATE | RATE | 동일 |
| Formula | Formula | 동일 |
| Q'TY | Q'TY | 동일 |
| TOTAL (USD) | TOTAL (USD) | 동일 |
| REMARK | (제거됨) | 사용자 요청으로 제거 |
| REV RATE | REV RATE | 동일 |
| REV TOTAL | REV TOTAL | 동일 |
| DIFFERENCE | DIFFERENCE | 동일 |

**총 15개 표준 헤더** (VBA 13개 + Source_File, No, Month - REMARK)

### C. Robust Header Detection 임계값

| 임계값 | 의미 | 비고 |
|--------|------|------|
| **78%** | Fuzzy 매칭 임계값 | 기본값 |
| 90%+ | 정확한 매칭 | 오타 없음 |
| 80-89% | 경미한 오타 | 1-2자 차이 |
| 70-79% | 중간 오타 | 3-4자 차이 |
| <70% | 매칭 실패 | 휴리스틱 폴백 |

**예시**:
- "RATE SOURCE" vs "RATE SOURCE": 100% (정확)
- "RATE SOURCE" vs "RATE SORUCE": 91% (오타 1자)
- "RATE SOURCE" vs "RATE_SOURCE": 85% (언더스코어)
- "RATE SOURCE" vs "PRICE SOURCE": 50% (다른 단어)

### D. 월별 행 수 분포

| 월 | 행 수 | 비율 | 유니크 Order Ref |
|----|-------|------|------------------|
| JANUARY 2025 | 249 | 11.5% | 30 |
| JUNE 2025 | 300 | 13.8% | 51 (Batch1+2) |
| NOV 2024 | 175 | 8.1% | 24 |
| JULY 2025 | 171 | 7.9% | 39 |
| DEC 2024 | 152 | 7.0% | 22 |
| MAY 2025 | 151 | 7.0% | 32 |
| APRIL 2025 | 150 | 6.9% | 18 |
| MARCH 2025 | 143 | 6.6% | 36 |
| FEBRUARY 2025 | 142 | 6.6% | 25 |
| AUG 2025 | 133 | 6.1% | 28 |
| OCT 2024 | 124 | 5.7% | 23 |
| SEPT 2025 | 102 | 4.7% | 28 |
| AUG 2024 | 93 | 4.3% | 11 |
| SEP 2024 | 81 | 3.7% | 11 |
| **합계** | **2,166** | **100%** | **356** |

### E. 데이터 품질 체크리스트

- [ ] 총 행 수: 2,166 rows ✅
- [ ] 총 컬럼 수: 182 columns ✅
- [ ] 유니크 Order Ref: 356개 ✅
- [ ] Source_File: 100.0% ✅
- [ ] Month: 100.0% ✅
- [ ] Order Ref. Number: 100.0% ✅
- [ ] DESCRIPTION: 100.0% ✅
- [ ] RATE: 99.9% ✅
- [ ] TOTAL (USD): 99.8% ✅
- [ ] RATE SOURCE: 99.9% ✅
- [ ] 헤더 감지 성공률: 100% ✅
- [ ] 표준 헤더 완료: 100% (15/15) ✅

---

**문서 끝**

