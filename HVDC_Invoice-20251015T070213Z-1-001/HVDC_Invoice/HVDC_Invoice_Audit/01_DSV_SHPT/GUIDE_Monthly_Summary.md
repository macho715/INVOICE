# 월별 Summary 시트 가이드

**버전**: 1.0  
**최종 업데이트**: 2025-10-17  
**대상**: HVDC Invoice Audit - 월별 요약 시트 사용자  

---

## 목차

1. [개요](#1-개요)
2. [시트 구조](#2-시트-구조)
3. [파일별 상세](#3-파일별-상세)
4. [통합 시스템](#4-통합-시스템)
5. [사용 방법](#5-사용-방법)
6. [데이터 분석](#6-데이터-분석)
7. [문제 해결](#7-문제-해결)
8. [FAQ](#8-faq)
9. [참조 문서](#9-참조-문서)

---

## 1. 개요

### 1.1 월별 Summary 시트란?

월별 Summary 시트는 각 월의 **인보이스 요약 데이터**를 포함하는 Excel 시트입니다. 개별 인보이스의 상세 항목이 아닌 **인보이스 단위 요약 정보**를 제공합니다.

**핵심 특징**:
- **1 row = 1 invoice** (인보이스별 요약)
- GRAND TOTAL (총 금액) 포함
- Shipment Reference, Job Number 등 핵심 정보
- 월별 트렌드 분석 용이

### 1.2 목적 및 용도

**재무 보고**:
- 월별 인보이스 총액
- 분기별 집계
- 연간 트렌드

**운영 분석**:
- Shipment 타입별 분포
- POL/POD별 물동량
- 운송 모드 분석

**데이터 검증**:
- 개별 시트 합계 vs GRAND TOTAL
- 누락 데이터 추적

### 1.3 커버 기간

**2024년 8월 ~ 2025년 9월** (14개월)

| 기간 | 시트 수 | 총 데이터 | 총 금액 (USD) |
|------|---------|----------|---------------|
| 2024년 8-12월 | 5개 | 100 rows | $648,948 |
| 2025년 1-9월 | 10개 (JUNE 2개) | 306 rows | $771,582 |
| **합계** | **15개** | **406 rows** | **$1,420,530** |

---

## 2. 시트 구조

### 2.1 시트 이름 패턴

월별 Summary 시트는 다음과 같은 이름 패턴을 가집니다:

| 월 | 시트명 | 비고 |
|----|--------|------|
| 2024년 8월 | **AUG** | 2024년 파일 |
| 2024년 9월 | **SEP** | |
| 2024년 10월 | **OCT** | |
| 2024년 11월 | **NOV** | |
| 2024년 12월 | **DEC** | |
| 2025년 1월 | **JAN** | |
| 2025년 2월 | **FEB** | |
| 2025년 3월 | **MAR** | |
| 2025년 4월 | **APR** | |
| 2025년 5월 | **MAY** | |
| 2025년 6월 | **JUNE (2)**, **JUNE** | Batch1, Batch2 |
| 2025년 7월 | **July** | 소문자 사용 |
| 2025년 8월 | **AUG** | 2025년 파일 |
| 2025년 9월 | **SEPT** | 'T' 포함 |

**특징**:
- 대부분 대문자 사용
- JUNE 2025는 2개 파일로 분할
- JULY 2025만 "July" (소문자 시작)
- SEPT 2025는 "SEPT" ('T' 포함)

### 2.2 헤더 구조

**헤더 위치**:
- **Row 4**: AUG 2025, SEPT 2025
- **Row 6**: 나머지 13개 시트

**핵심 컬럼** (약 22개 표준 컬럼):

| 순서 | 컬럼명 | 설명 | 필수 |
|------|--------|------|------|
| 1 | **S/No** (또는 No.) | 순번 | ✅ |
| 2 | **Delivery Month** | 배송 월 (2024년 파일만) | - |
| 3 | **Shipment Reference** | 주문 번호 | ✅ |
| 4 | **CW1 Job Number** | Job 번호 | ✅ |
| 5 | **Type** | 타입 (SHIPMENT, CLEARANCE) | ✅ |
| 6 | **BL #** | Bill of Lading 번호 | - |
| 7 | **POL** | Port of Loading | - |
| 8 | **POD** | Port of Discharge | - |
| 9 | **Mode** | 운송 모드 (CNTR, AIR, BKK) | - |
| 10 | **No. Of CNTR** | 컨테이너 수 | - |
| 11 | **Volume** | 부피 | - |
| 12 | **Quantity** | 수량 | - |
| 13 | **BOE** | Bill of Entry | - |
| 14 | **BOE Issued Date** | BOE 발급일 | - |
| 15 | **MASTER DO CHARGE** | Master DO 요금 | - |
| 16 | **CUSTOMS CLEARANCE CHARGE** | 통관 요금 | - |
| 17 | **HOUSE DO CHARGE** | House DO 요금 | - |
| 18 | **PORT HANDLING CHARGE** | 항만 처리 요금 | - |
| 19 | **TRANSPORTATION CHARGE** | 운송 요금 | - |
| 20 | **AT COST AMOUNT** | At Cost 금액 | - |
| 21 | **ADDITIONAL AMOUNT** | 추가 금액 | - |
| 22 | **GRAND TOTAL (USD)** | 총 금액 | ✅ |

**동의어 패턴**:
- "Shpt Ref" = "Shipment Reference"
- "Job #" = "CW1 Job Number"
- "GRAND TOTAL (USD)" = "GRAND TOTAL" = "Total (USD)"
- "MASTER DO / CHARGE" = "MASTER DO CHARGE"

### 2.3 데이터 구조

**인보이스 요약** (1 row = 1 invoice):

```
Row 1-5: 헤더 정보 (회사명, 제목 등)
Row 4 또는 6: 헤더 (컬럼명)
Row 7 이상: 데이터
    HVDC-ADOPT-SCT-0001 | SHIPMENT | ... | $3,550.08
    HVDC-ADOPT-SCT-0002 | CLEARANCE | ... | $2,100.00
    ...
마지막 행: TOTAL (집계 행, 제외됨)
```

**GRAND TOTAL 계산**:
- 각 인보이스의 최종 금액
- MASTER DO + CUSTOMS + PORT + TRANSPORTATION + AT COST + ADDITIONAL
- 월별 집계 = 모든 GRAND TOTAL 합계

---

## 3. 파일별 상세

### 3.1 2024년 시트 (AUG~DEC)

**파일 예시**: `SCNT SHIPMENT DRAFT INVOICE (AUG 2024).xlsx`

**특징**:
- 헤더 위치: **Row 6**
- **Delivery Month 컬럼 존재** (Col 2)
- S/No 컬럼이 별도로 없을 수 있음

**헤더 구조 (AUG 2024 예시)**:

| Col 1 | Col 2 | Col 3 | Col 4 | ... |
|-------|-------|-------|-------|-----|
| No. | **Delivery Month** | Shpt Ref | Job # | ... |

**샘플 데이터**:

| No. | Delivery Month | Shpt Ref | Job # | Type | GRAND TOTAL (USD) |
|-----|----------------|----------|-------|------|-------------------|
| 1 | Aug-24 | HVDC-ADOPT-HE-0173 | J001 | SHIPMENT | $5,410.00 |
| 2 | Aug-24 | HVDC-ADOPT-HE-0174 | J002 | CLEARANCE | $4,200.00 |

**통계**:

| 월 | 데이터 행 | GRAND TOTAL (USD) |
|----|----------|-------------------|
| AUG 2024 | 18 | $97,460.45 |
| SEP 2024 | 12 | $82,047.18 |
| OCT 2024 | 24 | $86,001.78 |
| NOV 2024 | 24 | $186,594.69 |
| DEC 2024 | 22 | $196,843.62 |

### 3.2 2025년 시트 (JAN~SEPT)

**파일 예시**: `SCNT SHIPMENT DRAFT INVOICE (FEBRUARY 2025)_rev2.xlsm`

**특징**:
- 헤더 위치: **Row 6** (대부분), **Row 4** (AUG, SEPT 2025)
- **S/No 컬럼 존재** (Col 2)
- Delivery Month 컬럼 없음

**헤더 구조 (FEB 2025 예시)**:

| Col 1 | Col 2 | Col 3 | Col 4 | ... |
|-------|-------|-------|-------|-----|
| (빈) | **S/No** | Shipment Reference | CW1 Job Number | ... |

**샘플 데이터**:

| S/No | Shipment Reference | CW1 Job Number | Type | GRAND TOTAL (USD) |
|------|-------------------|----------------|------|-------------------|
| 1 | HVDC-ADOPT-SCT-0037 | J201 | SHIPMENT | $3,550.08 |
| 2 | HVDC-ADOPT-SCT-0029 | J202 | CLEARANCE | $2,100.00 |

**통계**:

| 월 | 데이터 행 | GRAND TOTAL (USD) |
|----|----------|-------------------|
| JAN 2025 | 30 | $119,173.51 |
| FEB 2025 | 21 | $61,934.82 |
| MAR 2025 | 28 | $42,162.58 |
| APR 2025 | 36 | $183,528.23 |
| MAY 2025 | 35 | $64,165.54 |
| JUN 2025 (Batch1) | 22 | $60,981.23 |
| JUN 2025 (Batch2) | 33 | $52,888.76 |
| JUL 2025 | 42 | $100,735.35 |
| AUG 2025 | 30 | $43,153.29 |
| SEPT 2025 | 29 | $42,858.87 |

### 3.3 특수 케이스

#### JUNE 2025 (Batch1 + Batch2)

**배경**: 데이터량 과다로 2개 파일로 분할

**파일**:
1. `SCNT SHIPMENT DRAFT INVOICE (JUNE 2025)_Batch1.xlsm`
   - 시트명: **JUNE (2)**
   - 22 rows, $60,981.23

2. `SCNT SHIPMENT DRAFT INVOICE (JUNE 2025)_Batch2.xlsm`
   - 시트명: **JUNE**
   - 33 rows, $52,888.76

**통합**: 55 rows, **$113,869.99** (2025년 중 최대)

#### FEBRUARY 2025 rev2

**파일**: `SCNT SHIPMENT DRAFT INVOICE (FEBRUARY 2025)_rev2.xlsm`

**특징**:
- "_rev2" suffix (개정 버전)
- Novatech 시트 추가 (별도 분석용)

#### JULY 2025

**파일**: `SCNT SHIPMENT DRAFT INVOICE (JULY 2025).xlsm`

**특징**:
- 시트명: **July** (소문자 시작, 유일)
- 42 rows (2025년 중 최다)

---

## 4. 통합 시스템

### 4.1 자동 통합 방법

**스크립트**: `consolidate_month_sheets.py`

**핵심 기술**:

1. **동적 헤더 감지** (하드코딩 제로)
   - Row 1-15 스캔
   - 키워드 기반 휴리스틱
   - Row 4와 Row 6 자동 처리

2. **컬럼명 동의어 자동 매핑**
   - "Shpt Ref" → "Shipment Reference"
   - "Job #" → "CW1 Job Number"
   - "GRAND TOTAL (USD)" 통일

3. **TOTAL 행 자동 제외**
   - S/No에 "TOTAL" 포함 시 중단
   - 빈 행 연속 3개 이상 시 중단

**처리 흐름**:

```
1. Excel 파일 열기 (openpyxl)
2. 시트 찾기 (시트명 매칭)
3. 헤더 행 감지 (Row 1-15 스캔)
4. 헤더 컬럼 매핑 (동의어 사전 적용)
5. 데이터 추출 (헤더 행+1 ~ TOTAL 행 직전)
6. Source_Month, No 추가
7. 컬럼 정규화
8. 중복 컬럼 제거
9. pd.concat로 통합
```

### 4.2 통합 결과

**최종 파일**: `out/month_sheets_master_YYYYMMDD_HHMMSS.xlsx`

**통계**:
- **총 행 수**: 406 rows
- **총 컬럼 수**: 56 columns
- **GRAND TOTAL 합계**: **$1,420,529.90**
- **데이터 완전성**: 99.5%

**표준 컬럼 (통합 후)**:

| 순서 | 컬럼명 | 설명 |
|------|--------|------|
| 1 | **No** | 통합 순번 (1-406) |
| 2 | **Source_Month** | 월 레이블 (AUG 2024, FEB 2025, ...) |
| 3-22 | (22개 표준 컬럼) | S/No, Shipment Reference, ... |
| 23-56 | (34개 추가 컬럼) | Delivery Month, REV TOTAL, ... |

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
python consolidate_month_sheets.py
```

**소요 시간**: 약 1-2분

#### 단계 3: 결과 확인

```
================================================================================
[SUCCESS] 월별 시트 통합 완료!
================================================================================
총 행 수: 406
총 컬럼 수: 56

월별 데이터 분포:
Source_Month
AUG 2024         18
AUG 2025         30
APR 2025         36
DEC 2024         22
FEB 2025         21
JAN 2025         30
JUL 2025         42
JUN 2025 Batch1  22
JUN 2025 Batch2  33
MAR 2025         28
MAY 2025         35
NOV 2024         24
OCT 2024         24
SEP 2024         12
SEPT 2025        29

출력: out/month_sheets_master_20251017_055939.xlsx
```

### 5.2 결과 확인

#### Python으로 확인:

```python
import pandas as pd

# 파일 읽기
df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

# 기본 정보
print(f"총 행 수: {len(df)}")
print(f"총 컬럼 수: {len(df.columns)}")

# 월별 분포
print("\n월별 데이터 분포:")
print(df['Source_Month'].value_counts().sort_index())

# GRAND TOTAL 합계
if 'GRAND TOTAL (USD)' in df.columns:
    total = df['GRAND TOTAL (USD)'].sum()
    print(f"\nGRAND TOTAL 합계: ${total:,.2f}")

# 샘플 데이터
print("\n샘플 데이터 (처음 5행):")
print(df.head())
```

#### 월별 GRAND TOTAL 분석:

```python
import pandas as pd

df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

# 월별 GRAND TOTAL 집계
monthly_total = df.groupby('Source_Month')['GRAND TOTAL (USD)'].agg([
    ('총 행 수', 'count'),
    ('GRAND TOTAL 합계', 'sum'),
    ('평균 금액', 'mean')
]).sort_values('GRAND TOTAL 합계', ascending=False)

print(monthly_total)
```

### 5.3 새로운 월 추가

#### 단계 1: 파일 준비

SHPT 폴더에 새 월 파일 추가:
```
HVDC_Invoice_Audit/01_DSV_SHPT/SHPT/
  - SCNT SHIPMENT DRAFT INVOICE (OCT 2025).xlsx
```

#### 단계 2: 매핑 추가

`00_Shared/month_sheet_consolidator.py` 수정:

```python
def _define_month_sheets(self) -> List[MonthSheetInfo]:
    return [
        MonthSheetInfo('2024-08', 'AUG 2024', '...(AUG 2024).xlsx', 'AUG'),
        MonthSheetInfo('2024-09', 'SEP 2024', '...(SEP 2024).xlsx', 'SEP'),
        # ... 기존 15개
        
        # 새로운 월 추가
        MonthSheetInfo('2025-10', 'OCT 2025', 
                      'SCNT SHIPMENT DRAFT INVOICE (OCT 2025).xlsx', 'OCT'),
    ]
```

#### 단계 3: 재실행

```bash
python consolidate_month_sheets.py
```

---

## 6. 데이터 분석

### 6.1 월별 트렌드 분석

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

# 월별 GRAND TOTAL
monthly = df.groupby('Source_Month')['GRAND TOTAL (USD)'].sum().sort_index()

# 차트
plt.figure(figsize=(12, 6))
monthly.plot(kind='bar')
plt.title('월별 GRAND TOTAL 트렌드')
plt.xlabel('월')
plt.ylabel('GRAND TOTAL (USD)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### 6.2 분기별 분석

```python
import pandas as pd

df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

# 분기 매핑
quarter_map = {
    'AUG 2024': '2024 Q3',
    'SEP 2024': '2024 Q3',
    'OCT 2024': '2024 Q3',
    'NOV 2024': '2024 Q4',
    'DEC 2024': '2024 Q4',
    'JAN 2025': '2025 Q1',
    'FEB 2025': '2025 Q1',
    'MAR 2025': '2025 Q1',
    'APR 2025': '2025 Q2',
    'MAY 2025': '2025 Q2',
    'JUN 2025 Batch1': '2025 Q2',
    'JUN 2025 Batch2': '2025 Q2',
    'JUL 2025': '2025 Q3',
    'AUG 2025': '2025 Q3',
    'SEPT 2025': '2025 Q3',
}

df['Quarter'] = df['Source_Month'].map(quarter_map)

# 분기별 집계
quarterly = df.groupby('Quarter')['GRAND TOTAL (USD)'].agg([
    ('총 행 수', 'count'),
    ('GRAND TOTAL 합계', 'sum'),
    ('평균/월', lambda x: x.sum() / 3 if len(x) >= 3 else x.sum())
])

print(quarterly)
```

### 6.3 운송 모드별 분석

```python
import pandas as pd

df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

if 'Mode' in df.columns:
    mode_analysis = df.groupby('Mode').agg({
        'Shipment Reference': 'count',
        'GRAND TOTAL (USD)': 'sum'
    }).rename(columns={
        'Shipment Reference': '건수',
        'GRAND TOTAL (USD)': '총 금액'
    })
    
    print("운송 모드별 분석:")
    print(mode_analysis)
```

### 6.4 개별 시트 통합과 비교

```python
import pandas as pd

# 월별 시트 통합 (요약)
month_df = pd.read_excel("out/month_sheets_master_20251017_055939.xlsx")

# 개별 시트 통합 (상세)
detail_df = pd.read_excel("out/masterdata_all_months_20251017_071130.xlsx")

print("=== 통합 데이터 비교 ===")
print(f"월별 시트 (요약): {len(month_df)} rows")
print(f"개별 시트 (상세): {len(detail_df)} rows")
print(f"비율: {len(detail_df) / len(month_df):.1f} 라인/인보이스")

# 월별 GRAND TOTAL 비교
if 'Source_Month' in month_df.columns and 'Source_File' in detail_df.columns:
    month_total = month_df.groupby('Source_Month')['GRAND TOTAL (USD)'].sum()
    detail_total = detail_df.groupby('Source_File')['TOTAL (USD)'].sum()
    
    print("\n월별 금액 비교:")
    comparison = pd.DataFrame({
        '월별 시트': month_total,
        '개별 시트': detail_total
    })
    comparison['차이'] = comparison['개별 시트'] - comparison['월별 시트']
    comparison['차이 (%)'] = (comparison['차이'] / comparison['월별 시트'] * 100).round(2)
    
    print(comparison)
```

---

## 7. 문제 해결

### 7.1 헤더 감지 실패

**증상**:
```
[WARNING] 월별 시트 FEB를 찾을 수 없음
```

**원인**:
- 비표준 헤더 위치 (Row 15+)
- 키워드 불일치

**해결 방법**:

1. **수동으로 헤더 행 확인**:
   - Excel 파일 직접 열기
   - 헤더가 있는 Row 번호 확인

2. **키워드 추가**:

```python
# month_sheet_consolidator.py
def _find_header_row(self, ws):
    # 키워드 확장
    has_header_keyword = any(kw in row_text for kw in [
        'S/NO', 'S.NO', 'S NO', 
        'DELIVERY MONTH',
        'SHPT REF', 'SHIPMENT REFERENCE',
        'YOUR_NEW_KEYWORD'  # 추가
    ])
```

3. **수동 헤더 행 지정**:

```python
# 특정 시트만 수동 지정
if sheet_name == 'FEB' and file_name == '...FEBRUARY 2025...':
    header_row = 8  # 수동 지정
```

### 7.2 중복 컬럼 오류

**증상**:
```
pandas.errors.InvalidIndexError: Reindexing only valid with uniquely valued Index objects
```

**원인**:
- 동일한 컬럼명이 여러 개 존재
- 예: "GRAND TOTAL (USD)", "GRAND TOTAL (USD).1"

**해결 방법**:

1. **자동 제거 로직** (이미 적용됨):
```python
# _extract_single_month_sheet() 내부
df = df.loc[:, ~df.columns.duplicated()]
```

2. **수동 컬럼명 변경**:
```python
# 특정 시트의 중복 컬럼 처리
if 'GRAND TOTAL (USD).1' in df.columns:
    df = df.drop(columns=['GRAND TOTAL (USD).1'])
```

### 7.3 GRAND TOTAL 누락

**증상**:
- GRAND TOTAL (USD) 컬럼이 NaN

**원인**:
- 원본 시트에 데이터 없음
- 컬럼명 불일치

**해결 방법**:

1. **원본 시트 확인**:
```python
import openpyxl

wb = openpyxl.load_workbook("SCNT ... (FEB 2025).xlsm", data_only=True)
ws = wb['FEB']

# 헤더 행 확인
header_row = 6
for col in range(1, ws.max_column + 1):
    print(f"Col {col}: {ws.cell(header_row, col).value}")
```

2. **동의어 추가**:
```python
# month_sheet_consolidator.py
COLUMN_SYNONYMS = {
    'grandtotal': [
        'GRAND TOTAL (USD)',
        'GRAND TOTAL',
        'Total (USD)',
        'YOUR_VARIANT',  # 추가
    ],
}
```

### 7.4 월별 데이터 0 rows

**증상**:
```
[WARNING] FEB 2025 시트에서 데이터가 없음
```

**원인**:
- TOTAL 행 감지 과민 (첫 행이 TOTAL로 인식)
- 빈 행이 많음

**해결 방법**:

1. **TOTAL 행 감지 로직 수정**:
```python
# _extract_single_month_sheet() 내부
sno_value = str(row[sno_col_idx]) if sno_col_idx else ''

# "TOTAL AMOUNT"는 제외하되 "SUBTOTAL"은 포함
if sno_value.upper() == 'TOTAL' or sno_value.upper() == 'TOTAL AMOUNT':
    break
```

2. **빈 행 연속 조건 완화**:
```python
# 빈 행 5개 연속 → 7개 연속으로 변경
if empty_row_count >= 7:
    break
```

---

## 8. FAQ

### Q1. 월별 시트와 개별 시트의 차이는?

**A1**:

| 항목 | 월별 시트 | 개별 시트 |
|------|----------|----------|
| **데이터 레벨** | 요약 (인보이스별) | 상세 (라인 항목별) |
| **행 수** | 406 rows | 2,166 rows |
| **1 row** | 1 invoice 요약 | 1 item (MASTER DO, CUSTOMS, ...) |
| **GRAND TOTAL** | 인보이스 총액 | 항목별 금액 (TOTAL USD) |
| **용도** | 월별 트렌드, 재무 보고 | 비용 구조 분석, 상세 검증 |

**비율**: 2,166 / 406 ≈ 5.3 라인/인보이스

### Q2. JUNE 2025가 2개 파일인 이유는?

**A2**:

JUNE 2025는 데이터량이 많아서 2개 파일로 분할되었습니다:

- **Batch1**: 22개 인보이스 ($60,981.23)
- **Batch2**: 33개 인보이스 ($52,888.76)
- **합계**: 55개 ($113,869.99) → 2025년 중 최대

통합 시스템은 두 파일을 모두 자동으로 처리하여 "JUN 2025 Batch1", "JUN 2025 Batch2"로 구분합니다.

### Q3. 헤더가 Row 4와 Row 6으로 다른 이유는?

**A3**:

시기별로 Excel 템플릿이 변경되었습니다:

- **2024년 8월 ~ 2025년 7월**: Row 6
- **2025년 8월 ~ 2025년 9월**: Row 4 (새 템플릿)

동적 헤더 감지 시스템은 Row 1-15를 스캔하여 자동으로 감지합니다.

### Q4. "Delivery Month" 컬럼은 무엇인가요?

**A4**:

**Delivery Month**는 2024년 파일에만 존재하는 컬럼입니다:

- **2024년 파일** (AUG~DEC): "Delivery Month" 컬럼 존재 (Col 2)
- **2025년 파일** (JAN~SEPT): "S/No" 컬럼 대신 사용

```
2024년: No. | Delivery Month | Shpt Ref | ...
2025년: (빈) | S/No | Shipment Reference | ...
```

### Q5. GRAND TOTAL이 0인 행이 있는 이유는?

**A5**:

GRAND TOTAL이 0이거나 NaN인 경우 (406 rows 중 2개, 0.5%):

1. **원본 데이터 누락**: Excel 시트에 원래 데이터 없음
2. **계산 오류**: 원본 시트의 수식 오류

**확인 방법**:
```python
df[df['GRAND TOTAL (USD)'].isna()]
```

**대응**: 원본 시트 확인 필요 (99.5% 완전성은 허용 가능)

### Q6. 통합 파일의 컬럼 순서는?

**A6**:

```python
['No', 'Source_Month', 'S/No', 'Shipment Reference', 'CW1 Job Number', 
 'Type', 'BL #', 'POL', 'POD', 'Mode', ..., 'GRAND TOTAL (USD)']
```

**우선순위**:
1. No, Source_Month (통합 시 추가)
2. 22개 표준 컬럼 (알파벳 순)
3. 34개 추가 컬럼 (원본 시트의 나머지 컬럼)

### Q7. 통합 시간이 오래 걸리는 이유는?

**A7**:

**소요 시간**: 약 1-2분 (15개 시트)

**원인**:
- openpyxl로 Excel 파일 열기 (느림)
- Row 1-15 스캔 (헤더 감지)
- 데이터 추출 및 변환

**개선 방법**:
- (이미 적용됨) data_only=True로 수식 계산 생략
- (가능) multiprocessing으로 병렬 처리

### Q8. 새 월을 추가하려면 어떻게 하나요?

**A8**:

[5.3 새로운 월 추가](#53-새로운-월-추가) 참조

**요약**:
1. SHPT 폴더에 파일 추가
2. `month_sheet_consolidator.py` → `_define_month_sheets()` 수정
3. `python consolidate_month_sheets.py` 재실행

---

## 9. 참조 문서

### 기술 보고서

- **[REPORT_Monthly_Consolidation.md](REPORT_Monthly_Consolidation.md)**: Monthly consolidation technical report
- **[REPORT_Monthly_Integration.md](REPORT_Monthly_Integration.md)**: Final execution results and data analysis
- **[REPORT_Monthly_Verification.md](REPORT_Monthly_Verification.md)**: 15 sheets verification report

### 구조 분석

- **[REPORT_Feb2025_Structure.md](REPORT_Feb2025_Structure.md)**: FEB 2025 sheet structure analysis

### 사용자 가이드

- **[USER_GUIDE.md](Documentation/USER_GUIDE.md)**: 전체 시스템 사용자 가이드
- **[GUIDE_Individual_Invoices.md](GUIDE_Individual_Invoices.md)**: Individual invoice sheets guide

### 코드

- **[00_Shared/engine_monthly_summary.py](../00_Shared/engine_monthly_summary.py)**: Consolidation engine (370+ lines)
- **[Core_Systems/run_monthly_consolidation.py](Core_Systems/run_monthly_consolidation.py)**: Run script

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-10-17  
**작성자**: HVDC Invoice Audit Team  
**문의**: 시스템 관리자

---

## 부록

### A. 월별 Summary 시트 목록

| # | 월 | 파일 | 시트명 | 헤더 Row | 데이터 | GRAND TOTAL |
|---|------|------|--------|----------|--------|-------------|
| 1 | 2024-08 | (AUG 2024).xlsx | AUG | 6 | 18 | $97,460.45 |
| 2 | 2024-09 | (SEP 2024).xlsx | SEP | 6 | 12 | $82,047.18 |
| 3 | 2024-10 | (OCT 2024).xlsx | OCT | 6 | 24 | $86,001.78 |
| 4 | 2024-11 | (NOV 2024).xlsx | NOV | 6 | 24 | $186,594.69 |
| 5 | 2024-12 | (DEC 2024).xlsm | DEC | 6 | 22 | $196,843.62 |
| 6 | 2025-01 | (JANUARY 2025).xlsx | JAN | 6 | 30 | $119,173.51 |
| 7 | 2025-02 | (FEBRUARY 2025)_rev2.xlsm | FEB | 6 | 21 | $61,934.82 |
| 8 | 2025-03 | (MARCH 2025).xlsm | MAR | 6 | 28 | $42,162.58 |
| 9 | 2025-04 | (APRIL 2025).xlsx | APR | 6 | 36 | $183,528.23 |
| 10 | 2025-05 | (MAY 2025).xlsm | MAY | 6 | 35 | $64,165.54 |
| 11 | 2025-06 | (JUNE 2025)_Batch1.xlsm | JUNE (2) | 6 | 22 | $60,981.23 |
| 12 | 2025-06 | (JUNE 2025)_Batch2.xlsm | JUNE | 6 | 33 | $52,888.76 |
| 13 | 2025-07 | (JULY 2025).xlsm | July | 6 | 42 | $100,735.35 |
| 14 | 2025-08 | (AUG 2025).xlsm | AUG | 4 | 30 | $43,153.29 |
| 15 | 2025-09 | (SEPT 2025).xlsm | SEPT | 4 | 29 | $42,858.87 |
| **합계** | **15** | | | | **406** | **$1,420,529.90** |

### B. 컬럼 동의어 사전 (일부)

| 표준 컬럼명 | 동의어 |
|-----------|--------|
| Shipment Reference | Shpt Ref, Shipment Reference#, Ship Ref |
| CW1 Job Number | Job #, CWI Job Number, Job Number |
| BL # | BL Number, B/L #, Bill of Lading |
| GRAND TOTAL (USD) | GRAND TOTAL, Total (USD), Total |
| MASTER DO CHARGE | MASTER DO / CHARGE, MASTER DO/CHARGE |
| CUSTOMS CLEARANCE CHARGE | CUSTOMS / CLEARANCE / CHARGE, CUSTOMS/CLEARANCE/CH |
| PORT HANDLING CHARGE | PORT HANDLING, PORT / HANDLING / CHARGE |
| TRANSPORTATION CHARGE | TRANSPORTATION / CHARGE, TRANSPORTATION/CHARG |

### C. 헤더 감지 키워드

**Primary Keywords** (필수 1개 이상):
- 'S/NO', 'S.NO', 'S NO'
- 'DELIVERY MONTH'
- 'SHPT REF', 'SHIPMENT REFERENCE'

**Additional Keywords** (3개 이상):
- 'JOB'
- 'REF'
- 'BL'
- 'TOTAL'
- 'SHIPMENT'
- 'TYPE'
- 'POL'
- 'POD'
- 'MODE'

**조건**: Primary 1개 + Additional 3개 이상 → 헤더 행 확정

---

**문서 끝**

