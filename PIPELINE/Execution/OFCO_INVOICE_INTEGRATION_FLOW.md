# OFCO INVOICE 통합 프로세스 흐름도 문서

**작성일**: 2025-11-04  
**분석 대상**: `ofco_integrate_pipeline_to_excel.py` 통합 프로세스  
**소스**: Standard_Lines 시트 (21개 컬럼)  
**대상**: OFCO INVOICE.xlsx Sheet1 시트 (153개 컬럼)

---

## Executive Summary

이 문서는 Standard_Lines 시트의 데이터를 OFCO INVOICE.xlsx 형식으로 변환하는 통합 프로세스의 전체 흐름을 설명합니다.

**주요 단계**:
1. 데이터 읽기 단계
2. 변환 단계 (transform_row)
3. 정렬 단계 (HeaderCore)
4. 저장 단계

---

## 1. 통합 프로세스 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                    [입력] Standard_Lines 시트                    │
│                      (21개 컬럼, N행)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 1] 소스 파일 읽기                            │
│  - Standard_Lines 시트 읽기                                     │
│  - Invoice Number 추출                                          │
│  - 날짜 정보 확인 (Complete_Pipeline 또는 매핑)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 2] 대상 파일 읽기                            │
│  - OFCO INVOICE.xlsx Sheet1 시트 읽기 (템플릿)                   │
│  - 기존 데이터 확인 (Invoice Number 기준)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 3] 기존 데이터 삭제                           │
│  - Invoice Number 기준으로 기존 데이터 필터링                    │
│  - 기존 데이터 삭제 (handle_existing_data)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 4] 데이터 변환 (transform_row)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.1 기본 정보 매핑                                        │  │
│  │    - invoice_no → INVOICE NUMBER                          │  │
│  │    - invoice_date → INVOICE DATE, INVOICE DATE_YEAR_MONTH │  │
│  │    - line_no → NO                                         │  │
│  │    - description → SUBJECT                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.2 Cost/Price Center 매핑                                 │  │
│  │    - cost_main → COST MAIN                                │  │
│  │    - cost_center_a/b → COST CENTER A/B                    │  │
│  │    - price_center_name/a/b → PRICE CENTER                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.3 EA 슬롯 매핑                                          │  │
│  │    - EA_1~EA_4 Name, Qty, Rate, Amount                   │  │
│  │    - EA_Total_Amount 자동 계산                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.4 Price Center별 QTY/AMOUNT 매핑                        │  │
│  │    - PRICE CENTER 값 기반                                  │  │
│  │    - find_price_center_columns + normalize_price_center  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.5 금액 정보 매핑 (통화 변환)                             │  │
│  │    - amount_excl_tax → Total_Amount_AED, Amount_A_AED     │  │
│  │    - convert_currency (USD ↔ AED)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4.6 검증 컬럼 매핑                                        │  │
│  │    - calc_check, calc_status                             │  │
│  │    - vat_check, total_check                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 5] HeaderCore 적용 (reorder_dataframe)        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 5.1 기준 헤더 순서 로드                                   │  │
│  │    - OFCO INVOICE.xlsx에서 헤더 순서 읽기 (153개)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 5.2 컬럼명 매핑 (map_column_names)                       │  │
│  │    - invoice_no → INVOICE NUMBER                          │  │
│  │    - invoice_date → INVOICE DATE                          │  │
│  │    - voyage_no → Voyage No                                │  │
│  │    - description → SUBJECT                                 │  │
│  │    - line_no → NO                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 5.3 컬럼 순서 재정렬                                      │  │
│  │    - 기준 헤더 순서 (153개) 적용                           │  │
│  │    - Phase별 추가 헤더 처리                               │  │
│  │    - 누락 컬럼 추가 (None 값으로)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              [Step 6] 데이터 저장                                │
│  - 새 데이터 추가 (변환된 행들)                                  │
│  - 순번 재계산 (전체 순번, 청구 회차, NO)                        │
│  - 파일 저장                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    [출력] OFCO INVOICE.xlsx                     │
│                    Sheet1 시트 (153개 컬럼)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 단계별 상세 흐름

### 2.1 데이터 읽기 단계

**소스 파일 읽기**:
```python
src_df = pd.read_excel(source_path, sheet_name='Standard_Lines')
```

**처리 내용**:
1. Standard_Lines 시트 읽기
2. Invoice Number 추출 (`invoice_no` 또는 `INVOICE NUMBER` 컬럼)
3. 날짜 정보 확인:
   - Complete_Pipeline 시트에서 `invoice_date` 가져오기 시도
   - 실패 시 Invoice 번호 매핑 사용 (예: `'OFCO-INV-0001178'` → `'15 October, 2025'`)
   - 모든 행에 날짜 정보 추가

**대상 파일 읽기**:
```python
target_df = pd.read_excel(target_path, sheet_name='Sheet1')
```

**처리 내용**:
1. OFCO INVOICE.xlsx Sheet1 시트 읽기 (템플릿)
2. 기존 데이터 확인 (Invoice Number 기준)

### 2.2 변환 단계 (transform_row)

**변환 프로세스**:
```python
for idx, row in src_df.iterrows():
    transformed_row = transform_row(row, target_df)
    transformed_rows.append(transformed_row)
```

**변환 단계별 처리**:

**2.2.1 기본 정보 매핑**:
- `invoice_no` → `INVOICE NUMBER` (직접 매핑)
- `invoice_date` → `INVOICE DATE` (convert_date 함수)
- `invoice_date` → `INVOICE DATE_YEAR_MONTH` (convert_date + strftime)
- `voyage_no` → `Voyage No` (pd.notna 체크)
- `description` → `SUBJECT` (직접 매핑)
- `line_no` → `NO` (int 변환)

**2.2.2 Cost/Price Center 매핑**:
- `cost_main` → `COST MAIN`
- `cost_center_a` → `COST CENTER A`
- `cost_center_b` → `COST CENTER B`
- `price_center_name/a/b` → `PRICE CENTER` (우선순위: name > a > b)

**2.2.3 EA 슬롯 매핑**:
- EA_1~EA_4 Name, Qty, Rate, Amount 직접 매핑
- EA_Total_Amount 자동 계산

**2.2.4 Price Center별 QTY/AMOUNT 매핑**:
- PRICE CENTER 값 확인
- normalize_price_center로 정규화
- find_price_center_columns로 QTY/AMOUNT 컬럼 찾기
- 소스의 Price Center별 컬럼에서 값 추출 (없으면 EA_1에서 추출)
- 대상의 Price Center별 QTY/AMOUNT 컬럼에 매핑

**2.2.5 금액 정보 매핑**:
- `amount_excl_tax` → `Total_Amount_AED`, `Amount_A_AED` (통화 변환)
- `tax_amount_lines` → `VAT_USD` (통화 변환)
- `total_incl_tax` → `Total_Amount_USD` (통화 변환)
- `amount_excl_tax` → `Amount_USD` (통화 변환)

**2.2.6 검증 컬럼 매핑**:
- `calc_check` → `calc_check`
- `calc_status` → `calc_status`
- `vat_check` → `vat_check`
- `total_check` → `total_check`

**2.2.7 기타 컬럼 초기화**:
- 대상 파일에 있는 모든 컬럼이 없으면 `None`으로 초기화

### 2.3 정렬 단계 (HeaderCore)

**HeaderCore 적용**:
```python
header_core = get_header_core(reference_file=target_file)
result_df = header_core.reorder_dataframe(transformed_df)
```

**정렬 단계별 처리**:

**2.3.1 기준 헤더 순서 로드**:
- OFCO INVOICE.xlsx에서 헤더 순서 읽기 (153개)
- `load_base_headers()` 함수 사용

**2.3.2 컬럼명 매핑**:
- `invoice_no` → `INVOICE NUMBER`
- `invoice_date` → `INVOICE DATE`
- `voyage_no` → `Voyage No`
- `description` → `SUBJECT`
- `line_no` → `NO`

**2.3.3 컬럼 순서 재정렬**:
- 기준 헤더 순서 (153개) 적용
- Phase별 추가 헤더 처리 (현재: 0개)
- 누락 컬럼 추가 (None 값으로)

### 2.4 저장 단계

**데이터 저장**:
```python
# 기존 데이터 삭제
target_df = handle_existing_data(target_df, invoice_no)

# 새 데이터 추가
target_df = pd.concat([target_df, result_df], ignore_index=True)

# 순번 재계산
target_df = recalculate_sequence_numbers(target_df)

# 파일 저장
target_df.to_excel(target_path, sheet_name='Sheet1', index=False)
```

**저장 단계별 처리**:

**2.4.1 기존 데이터 삭제**:
- Invoice Number 기준으로 기존 데이터 필터링
- 기존 데이터 삭제

**2.4.2 새 데이터 추가**:
- 변환된 데이터 추가
- DataFrame concat 사용

**2.4.3 순번 재계산**:
- 전체 순번: 1부터 시작
- 청구 회차: Invoice Number별로 그룹핑하여 1부터 시작
- NO: Invoice Number별로 그룹핑하여 1부터 시작

**2.4.4 파일 저장**:
- OFCO INVOICE.xlsx Sheet1 시트에 저장
- 인덱스 제외

---

## 3. 컬럼 매핑 흐름도

### 3.1 기본 정보 매핑 흐름

```
소스 컬럼                    변환 로직                    대상 컬럼
─────────────────────────────────────────────────────────────────
invoice_no        ──────→  직접 매핑          ──────→  INVOICE NUMBER
invoice_date      ──────→  convert_date       ──────→  INVOICE DATE
invoice_date      ──────→  convert_date       ──────→  INVOICE DATE_YEAR_MONTH
                  ──────→  + strftime         ──────→  (YYYY-MM-01)
voyage_no         ──────→  pd.notna 체크       ──────→  Voyage No
description       ──────→  직접 매핑          ──────→  SUBJECT
line_no           ──────→  int 변환           ──────→  NO
```

### 3.2 Price Center 매핑 흐름

```
소스 컬럼                    변환 로직                    대상 컬럼
─────────────────────────────────────────────────────────────────
PRICE CENTER 값   ──────→  normalize_price_center  ──────→  PRICE CENTER
                  ──────→  (정규화)                ──────→  (예: AGENCY_FEE_FOR_CARGO_CLEARANCE)
                  │
                  ├──────→  find_price_center_columns  ──────→  {PRICE_CENTER}_QTY
                  │       ──────→  (컬럼 찾기)        ──────→  (예: AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY)
                  │
                  └──────→  find_price_center_columns  ──────→  {PRICE_CENTER}_AMOUNT
                          ──────→  (컬럼 찾기)        ──────→  (예: AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT)
```

### 3.3 EA 슬롯 매핑 흐름

```
소스 컬럼                    변환 로직                    대상 컬럼
─────────────────────────────────────────────────────────────────
EA_1_Name         ──────→  pd.notna 체크       ──────→  EA_1_Name
EA_1_Qty          ──────→  pd.notna 체크       ──────→  EA_1_Qty
EA_1_Rate         ──────→  pd.notna 체크       ──────→  EA_1_Rate
EA_1_Amount       ──────→  pd.notna 체크       ──────→  EA_1_Amount
EA_2_Name         ──────→  pd.notna 체크       ──────→  EA_2_Name
EA_2_Qty          ──────→  pd.notna 체크       ──────→  EA_2_Qty
EA_2_Rate         ──────→  pd.notna 체크       ──────→  EA_2_Rate
EA_2_Amount       ──────→  pd.notna 체크       ──────→  EA_2_Amount
... (EA_3, EA_4 동일)
                  │
EA_1~4_Amount     ──────→  자동 계산           ──────→  EA_Total_Amount
                  ──────→  (합계)              ──────→  (EA_1 + EA_2 + EA_3 + EA_4)
```

### 3.4 금액 정보 매핑 흐름

```
소스 컬럼                    변환 로직                    대상 컬럼
─────────────────────────────────────────────────────────────────
amount_excl_tax   ──────→  convert_currency    ──────→  Total_Amount_AED
                  ──────→  (USD ↔ AED)         ──────→  Amount_A_AED
                  │
                  ├──────→  convert_currency    ──────→  Amount_USD
                  │       ──────→  (USD ↔ AED)  ──────→
                  │
tax_amount_lines  ──────→  convert_currency    ──────→  VAT_USD
                  ──────→  (USD ↔ AED)         ──────→
                  │
total_incl_tax    ──────→  convert_currency    ──────→  Total_Amount_USD
                  ──────→  (USD ↔ AED)         ──────→
```

---

## 4. 데이터 변환 예시

### 4.1 입력 데이터 (Standard_Lines)

```python
{
    'invoice_no': 'OFCO-INV-0001178',
    'invoice_date': '15 October, 2025',
    'line_no': 1,
    'description': 'Agency Fee for Cargo Clearance',
    'cost_main': 'COST1',
    'cost_center_a': 'COST_A',
    'price_center_name': 'AGENCY FEE FOR CARGO CLEARANCE',
    'EA_1_Name': 'Agency Fee',
    'EA_1_Qty': 1.0,
    'EA_1_Rate': 500.0,
    'EA_1_Amount': 500.0,
    'amount_excl_tax': 500.0,
    'tax_amount_lines': 0.0,
    'total_incl_tax': 500.0,
    'currency': 'AED',
    'calc_check': True,
    'vat_check': True,
    'total_check': True
}
```

### 4.2 변환 과정

**Step 1: 기본 정보 매핑**:
- `INVOICE NUMBER` = `'OFCO-INV-0001178'`
- `INVOICE DATE` = `datetime(2025, 10, 15)`
- `INVOICE DATE_YEAR_MONTH` = `'2025-10-01'`
- `NO` = `1`
- `SUBJECT` = `'Agency Fee for Cargo Clearance'`

**Step 2: Cost/Price Center 매핑**:
- `COST MAIN` = `'COST1'`
- `COST CENTER A` = `'COST_A'`
- `PRICE CENTER` = `'AGENCY FEE FOR CARGO CLEARANCE'`

**Step 3: EA 슬롯 매핑**:
- `EA_1_Name` = `'Agency Fee'`
- `EA_1_Qty` = `1.0`
- `EA_1_Rate` = `500.0`
- `EA_1_Amount` = `500.0`
- `EA_Total_Amount` = `500.0` (자동 계산)

**Step 4: Price Center별 QTY/AMOUNT 매핑**:
- `normalize_price_center('AGENCY FEE FOR CARGO CLEARANCE')` = `'AGENCY_FEE_FOR_CARGO_CLEARANCE'`
- `AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY` = `1.0`
- `AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT` = `500.0`

**Step 5: 금액 정보 매핑**:
- `Total_Amount_AED` = `500.0` (AED이므로 그대로)
- `Amount_A_AED` = `500.0`
- `Amount_USD` = `136.24` (500.0 / 3.67)
- `VAT_USD` = `0.0`
- `Total_Amount_USD` = `136.24`

**Step 6: 검증 컬럼 매핑**:
- `calc_check` = `True`
- `vat_check` = `True`
- `total_check` = `True`

### 4.3 출력 데이터 (OFCO INVOICE.xlsx)

```python
{
    'INVOICE NUMBER': 'OFCO-INV-0001178',
    'INVOICE DATE': datetime(2025, 10, 15),
    'INVOICE DATE_YEAR_MONTH': '2025-10-01',
    'NO': 1,
    'SUBJECT': 'Agency Fee for Cargo Clearance',
    'COST MAIN': 'COST1',
    'COST CENTER A': 'COST_A',
    'PRICE CENTER': 'AGENCY FEE FOR CARGO CLEARANCE',
    'EA_1_Name': 'Agency Fee',
    'EA_1_Qty': 1.0,
    'EA_1_Rate': 500.0,
    'EA_1_Amount': 500.0,
    'EA_Total_Amount': 500.0,
    'AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY': 1.0,
    'AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT': 500.0,
    'Total_Amount_AED': 500.0,
    'Amount_A_AED': 500.0,
    'Amount_USD': 136.24,
    'VAT_USD': 0.0,
    'Total_Amount_USD': 136.24,
    'calc_check': True,
    'vat_check': True,
    'total_check': True,
    # ... 기타 153개 컬럼 (나머지는 None)
}
```

---

## 5. 주요 함수 및 역할

### 5.1 transform_row

**역할**: 소스 행을 대상 행 형식으로 변환  
**입력**: `src_row` (pd.Series), `target_template` (pd.DataFrame)  
**출력**: `target_row` (dict)

**주요 처리**:
- 기본 정보 매핑
- Cost/Price Center 매핑
- EA 슬롯 매핑
- Price Center별 QTY/AMOUNT 매핑
- 금액 정보 매핑 (통화 변환)
- 검증 컬럼 매핑
- 기타 컬럼 초기화

### 5.2 HeaderCore.reorder_dataframe

**역할**: DataFrame 컬럼 순서를 기준 헤더 순서에 맞게 재정렬  
**입력**: `df` (pd.DataFrame), `phase` (Optional[int])  
**출력**: `result_df` (pd.DataFrame)

**주요 처리**:
- 기준 헤더 순서 로드
- 컬럼명 매핑
- 컬럼 순서 재정렬
- 누락 컬럼 추가

### 5.3 convert_date

**역할**: 날짜 문자열을 datetime 객체로 변환  
**입력**: `date_str` (Any)  
**출력**: `datetime` 객체 또는 `None`

**지원 형식**:
- `"15 October, 2025"`
- `"2025-10-15"`
- `datetime` 객체

### 5.4 normalize_price_center

**역할**: Price Center 이름을 컬럼명 형식으로 정규화  
**입력**: `price_center` (str)  
**출력**: 정규화된 문자열

**변환 규칙**:
- 대문자로 변환
- 특수문자 제거
- 공백을 언더스코어로 변경

### 5.5 find_price_center_columns

**역할**: Price Center에 해당하는 QTY/AMOUNT 컬럼 찾기  
**입력**: `price_center` (str), `target_df` (pd.DataFrame)  
**출력**: `(qty_col, amt_col)` 튜플 또는 `(None, None)`

**매칭 방식**:
1. normalize_price_center로 정규화
2. `"{normalized}_QTY"`, `"{normalized}_AMOUNT"` 컬럼명 생성
3. 대상 DataFrame에서 컬럼명 매칭
4. PRICE_CENTER_TO_COLUMNS 규칙 사용 (fallback)

### 5.6 convert_currency

**역할**: USD ↔ AED 통화 변환  
**입력**: `amount` (float), `from_currency` (str), `to_currency` (str)  
**출력**: 변환된 금액 (float)

**변환 규칙**:
- USD → AED: `amount * rate` (기본 환율: 3.67)
- AED → USD: `amount / rate` (기본 환율: 3.67)
- 동일 통화: 그대로 반환

---

## 참고 문서

- [OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md](OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md) - 통합 프로세스 매핑 보고서
- [OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md](OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md) - 구조 상세 분석
- [M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md](M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md) - M:CV ↔ DA:DH 상관관계 분석

---

**작성 완료일**: 2025-11-04  
**분석 도구**: `analyze_integration_mapping.py`, `analyze_headercore_application.py`, `analyze_transformation_validation.py`

