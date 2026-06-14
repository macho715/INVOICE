# OFCO INVOICE 통합 프로세스 매핑 보고서

**작성일**: 2025-11-04  
**분석 대상**: `ofco_integrate_pipeline_to_excel.py` 통합 스크립트  
**소스**: Standard_Lines 시트 (21개 컬럼)  
**대상**: OFCO INVOICE.xlsx Sheet1 시트 (153개 컬럼)

---

## Executive Summary

`ofco_integrate_pipeline_to_excel.py` 스크립트는 Standard_Lines 시트의 데이터를 OFCO INVOICE.xlsx 형식으로 변환하는 통합 프로세스를 수행합니다.

- **소스 컬럼 수**: 21개 (Standard_Lines)
- **대상 컬럼 수**: 153개 (OFCO INVOICE.xlsx)
- **매핑 규칙 수**: 37개
- **변환 함수**: 4개 (convert_date, normalize_price_center, find_price_center_columns, convert_currency)

---

## 1. Standard_Lines → OFCO INVOICE.xlsx 컬럼 매핑 테이블

### 1.1 기본 정보 매핑

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `invoice_no` | `INVOICE NUMBER` | 직접 매핑 | `''` | 문자열 | `'OFCO-INV-0001178'` |
| `invoice_date` | `INVOICE DATE` | `convert_date` 함수 | `None` | datetime | `2025-10-15` |
| `invoice_date` | `INVOICE DATE_YEAR_MONTH` | `convert_date` + `strftime('%Y-%m-01')` | `None` | datetime | `2025-10-01` |
| `voyage_no` | `Voyage No` | `pd.notna` 체크 | `None` | 문자열 또는 None | `'V12345'` |
| `description` | `SUBJECT` | 직접 매핑 | `''` | 문자열 | `'Agency Fee'` |
| `line_no` | `NO` | `int` 변환 (`pd.notna` 체크) | `None` | 정수 또는 None | `1` |

### 1.2 Cost/Price Center 매핑

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `cost_main` | `COST MAIN` | `pd.notna` 체크 | `''` | 문자열 | `'COST1'` |
| `cost_center_a` | `COST CENTER A` | `pd.notna` 체크 | `''` | 문자열 | `'COST_A'` |
| `cost_center_b` | `COST CENTER B` | `pd.notna` 체크 | `''` | 문자열 | `'COST_B'` |
| `price_center_name/a/b` | `PRICE CENTER` | 우선순위: `name > a > b` | `''` | 문자열 | `'AGENCY FEE FOR CARGO CLEARANCE'` |

**PRICE CENTER 우선순위**:
```python
price_center = (
    src_row.get('price_center_name') or
    src_row.get('price_center_a') or
    src_row.get('price_center_b') or
    ''
)
```

### 1.3 EA 슬롯 매핑

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `EA_1_Name` | `EA_1_Name` | `pd.notna` 체크 | `None` | 문자열 또는 None | `'Agency Fee'` |
| `EA_1_Qty` | `EA_1_Qty` | `pd.notna` 체크 | `None` | float 또는 None | `1.0` |
| `EA_1_Rate` | `EA_1_Rate` | `pd.notna` 체크 | `None` | float 또는 None | `500.0` |
| `EA_1_Amount` | `EA_1_Amount` | `pd.notna` 체크 | `None` | float 또는 None | `500.0` |
| `EA_2_Name` | `EA_2_Name` | `pd.notna` 체크 | `None` | 문자열 또는 None | `'Port Dues'` |
| `EA_2_Qty` | `EA_2_Qty` | `pd.notna` 체크 | `None` | float 또는 None | `1.0` |
| `EA_2_Rate` | `EA_2_Rate` | `pd.notna` 체크 | `None` | float 또는 None | `1000.0` |
| `EA_2_Amount` | `EA_2_Amount` | `pd.notna` 체크 | `None` | float 또는 None | `1000.0` |
| `EA_3_Name` | `EA_3_Name` | `pd.notna` 체크 | `None` | 문자열 또는 None | - |
| `EA_3_Qty` | `EA_3_Qty` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_3_Rate` | `EA_3_Rate` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_3_Amount` | `EA_3_Amount` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_4_Name` | `EA_4_Name` | `pd.notna` 체크 | `None` | 문자열 또는 None | - |
| `EA_4_Qty` | `EA_4_Qty` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_4_Rate` | `EA_4_Rate` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_4_Amount` | `EA_4_Amount` | `pd.notna` 체크 | `None` | float 또는 None | - |
| `EA_1~4_Amount 합계` | `EA_Total_Amount` | 자동 계산 | `0.0` | float | `1500.0` |

**EA_Total_Amount 계산 로직**:
```python
ea_amounts = [
    target_row.get('EA_1_Amount') or 0,
    target_row.get('EA_2_Amount') or 0,
    target_row.get('EA_3_Amount') or 0,
    target_row.get('EA_4_Amount') or 0
]
ea_amounts = [float(amt) if pd.notna(amt) and amt is not None else 0.0 for amt in ea_amounts]
target_row['EA_Total_Amount'] = sum(ea_amounts)
```

### 1.4 Price Center별 QTY/AMOUNT 매핑 (M:CV 범위)

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `PRICE CENTER` 값 기반 | `{PRICE_CENTER}_QTY` | `find_price_center_columns` + `normalize_price_center` | `0` | float | `AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY` |
| `PRICE CENTER` 값 기반 | `{PRICE_CENTER}_AMOUNT` | `find_price_center_columns` + `normalize_price_center` | `0` | float | `AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT` |

**Price Center 매핑 로직**:
1. `PRICE CENTER` 컬럼 값 확인
2. `normalize_price_center`로 정규화 (예: `'AGENCY FEE FOR CARGO CLEARANCE'` → `'AGENCY_FEE_FOR_CARGO_CLEARANCE'`)
3. `find_price_center_columns`로 QTY/AMOUNT 컬럼 찾기
4. 소스의 `{normalized}_QTY`, `{normalized}_AMOUNT` 컬럼에서 값 추출 (없으면 EA_1에서 추출)
5. 대상의 Price Center별 QTY/AMOUNT 컬럼에 매핑

### 1.5 금액 정보 매핑

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `amount_excl_tax` | `Total_Amount_AED` | 통화 변환 (`convert_currency`) | `0.0` | float | `500.0` |
| `amount_excl_tax` | `Amount_A_AED` | 통화 변환 (`convert_currency`) | `0.0` | float | `500.0` |
| `tax_amount_lines` | `VAT_USD` | 통화 변환 (`convert_currency`) | `0.0` | float | `50.0` |
| `total_incl_tax` | `Total_Amount_USD` | 통화 변환 (`convert_currency`) | `0.0` | float | `550.0` |
| `amount_excl_tax` | `Amount_USD` | 통화 변환 (`convert_currency`) | `0.0` | float | `500.0` |

**통화 변환 로직**:
- 원본 통화가 `USD`인 경우: AED로 변환 (환율 3.67)
- 원본 통화가 `AED`인 경우: USD로 변환 (환율 3.67)
- 기본 통화: `AED` (소스에 `currency` 컬럼이 없으면 AED로 가정)

### 1.6 검증 컬럼 매핑

| 소스 컬럼 | 대상 컬럼 | 변환 로직 | 기본값 | 데이터 타입 | 예시 |
|-----------|----------|----------|--------|------------|------|
| `calc_check` | `calc_check` | `pd.notna` 체크 | `False` | bool | `True` |
| `calc_status` | `calc_status` | `pd.notna` 체크 | `''` | 문자열 | `'OK'` |
| `vat_check` | `vat_check` | `pd.notna` 체크 | `False` | bool | `True` |
| `total_check` | `total_check` | `pd.notna` 체크 | `False` | bool | `True` |

---

## 2. 데이터 변환 로직 상세

### 2.1 날짜 변환 (convert_date)

**함수**: `convert_date(date_str: Any) -> Optional[datetime]`

**지원 형식**:
1. `"15 October, 2025"` → `datetime.strptime(date_str, "%d %B, %Y")`
2. `"2025-10-15"` → `datetime.strptime(date_str.split()[0], "%Y-%m-%d")`
3. `datetime` 객체 → 그대로 반환
4. 기타 형식 → `pd.to_datetime(date_str)` 시도

**INVOICE DATE_YEAR_MONTH 변환**:
```python
if invoice_date:
    target_row['INVOICE DATE'] = invoice_date
    target_row['INVOICE DATE_YEAR_MONTH'] = invoice_date.strftime('%Y-%m-01')
```

**예시**:
- 입력: `"15 October, 2025"` → 출력: `datetime(2025, 10, 15)`
- 입력: `datetime(2025, 10, 15)` → 출력: `datetime(2025, 10, 15)`
- INVOICE DATE_YEAR_MONTH: `"2025-10-01"`

### 2.2 Price Center 매핑 (normalize_price_center, find_price_center_columns)

**함수 1**: `normalize_price_center(price_center: str) -> str`

**변환 규칙**:
1. 대문자로 변환
2. 특수문자 제거: `re.sub(r'[^\w\s]', '', ...)`
3. 공백을 언더스코어로 변경: `re.sub(r'\s+', '_', ...)`

**예시**:
- 입력: `"AGENCY FEE FOR CARGO CLEARANCE"` → 출력: `"AGENCY_FEE_FOR_CARGO_CLEARANCE"`
- 입력: `"Port Dues (Vessels)"` → 출력: `"PORT_DUES_VESSELS"`
- 입력: `"Bulk Material - Solids"` → 출력: `"BULK_MATERIAL_SOLIDS"`

**함수 2**: `find_price_center_columns(price_center: str, target_df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]`

**매칭 방식**:
1. `normalize_price_center`로 정규화
2. `"{normalized}_QTY"`, `"{normalized}_AMOUNT"` 컬럼명 생성
3. 대상 DataFrame에서 컬럼명 매칭 (대소문자/공백 차이 고려)
4. `PRICE_CENTER_TO_COLUMNS` 규칙 사용 (fallback)

**예시**:
- 입력: `"AGENCY FEE FOR CARGO CLEARANCE"` → 출력: `("AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY", "AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT")`

### 2.3 EA 슬롯 매핑

**EA 슬롯 매핑 규칙**:
- EA_1~EA_4 Name, Qty, Rate, Amount 직접 매핑
- EA_Total_Amount 자동 계산: `EA_1_Amount + EA_2_Amount + EA_3_Amount + EA_4_Amount`

**EA_Total_Amount 계산**:
```python
ea_amounts = [
    target_row.get('EA_1_Amount') or 0,
    target_row.get('EA_2_Amount') or 0,
    target_row.get('EA_3_Amount') or 0,
    target_row.get('EA_4_Amount') or 0
]
ea_amounts = [float(amt) if pd.notna(amt) and amt is not None else 0.0 for amt in ea_amounts]
target_row['EA_Total_Amount'] = sum(ea_amounts)
```

### 2.4 금액 변환 (convert_currency)

**함수**: `convert_currency(amount: float, from_currency: str, to_currency: str, rate: Optional[float] = None) -> float`

**변환 규칙**:
- USD → AED: `amount * rate` (기본 환율: 3.67)
- AED → USD: `amount / rate` (기본 환율: 3.67)
- 동일 통화: 그대로 반환

**환율 소스**:
- 환경 변수 `USD_TO_AED_RATE` 또는 기본값 `3.67`

**예시**:
- 입력: `100.0 USD → AED` → 출력: `367.0`
- 입력: `367.0 AED → USD` → 출력: `100.0`

---

## 3. HeaderCore 적용 방식

### 3.1 기준 헤더 로드 (load_base_headers)

**함수**: `HeaderCore.load_base_headers() -> List[str]`

**동작 방식**:
1. OFCO INVOICE.xlsx 파일에서 헤더만 읽기 (`nrows=0`)
2. 기준 헤더 순서 저장 (`self.base_headers`)
3. 기준 헤더 개수: 153개

**예시**:
```python
df = pd.read_excel(self.reference_file, nrows=0)
self.base_headers = list(df.columns)
```

### 3.2 컬럼 순서 정렬 (reorder_dataframe)

**함수**: `HeaderCore.reorder_dataframe(df: pd.DataFrame, phase: Optional[int] = None, fill_missing: bool = True, map_columns: bool = True) -> pd.DataFrame`

**동작 방식**:
1. 기준 헤더 순서 로드 (`load_base_headers`)
2. Phase별 추가 헤더 처리 (`phase1/2/3_headers`)
3. 추가 컬럼 처리 (`extra_headers`)
4. 컬럼명 매핑 (`map_column_names`)
5. 기준 순서에 맞게 컬럼 재정렬
6. 누락 컬럼 추가 (None 값으로)

**컬럼명 매핑 규칙**:
```python
COLUMN_MAPPING = {
    "invoice_no": "INVOICE NUMBER",
    "invoice_date": "INVOICE DATE",
    "voyage_no": "Voyage No",
    "description": "SUBJECT",
    "line_no": "NO",
}
```

### 3.3 Phase별 추가 헤더 처리

**Phase 1 추가 헤더**: 0개  
**Phase 2 추가 헤더**: 0개  
**Phase 3 추가 헤더**: 0개

**전체 순서 헤더**: 153개 (기준 헤더 153개 + Phase 추가 헤더)

---

## 4. 예외 처리 및 기본값 규칙

### 4.1 누락 컬럼 처리

**규칙**:
- 대상 파일에 있는 모든 컬럼이 없으면 `None`으로 초기화
- `pd.notna` 체크 후 기본값 적용

**예시**:
```python
for col in target_template.columns:
    if col not in target_row:
        target_row[col] = None
```

### 4.2 NaN 값 처리

**규칙**:
- `pd.notna(value)` 체크 후 기본값 적용
- 문자열: 기본값 `''`
- 숫자: 기본값 `0` 또는 `0.0`
- 불린: 기본값 `False`
- 날짜: 기본값 `None`

**예시**:
```python
target_row['Voyage No'] = src_row.get('voyage_no') if pd.notna(src_row.get('voyage_no')) else None
```

### 4.3 기본값 규칙

| 데이터 타입 | 기본값 | 적용 컬럼 예시 |
|-----------|--------|---------------|
| 문자열 | `''` | `INVOICE NUMBER`, `SUBJECT`, `COST MAIN` |
| 숫자 (정수) | `None` | `NO` |
| 숫자 (실수) | `0.0` | `EA_Total_Amount`, 금액 컬럼 |
| 불린 | `False` | `calc_check`, `vat_check`, `total_check` |
| 날짜 | `None` | `INVOICE DATE`, `INVOICE DATE_YEAR_MONTH` |

---

## 5. 통합 프로세스 흐름

### 5.1 전체 흐름

```
[입력] Standard_Lines 시트 (21개 컬럼)
  ↓
[변환] transform_row 함수
  ├── 기본 정보 매핑
  ├── Cost/Price Center 매핑
  ├── EA 슬롯 매핑
  ├── Price Center별 QTY/AMOUNT 매핑
  ├── 금액 정보 매핑 (통화 변환)
  └── 검증 컬럼 매핑
  ↓
[정렬] HeaderCore.reorder_dataframe
  ├── 기준 헤더 순서 적용
  ├── Phase별 추가 헤더 처리
  └── 컬럼명 매핑
  ↓
[출력] OFCO INVOICE.xlsx Sheet1 시트 (153개 컬럼)
```

### 5.2 단계별 상세 흐름

**1. 데이터 읽기 단계**:
- 소스 파일: `Standard_Lines` 시트 읽기
- 대상 파일: `OFCO INVOICE.xlsx` Sheet1 시트 읽기 (템플릿)

**2. 변환 단계 (transform_row)**:
- 각 행을 `transform_row` 함수로 변환
- 소스 컬럼 → 대상 컬럼 매핑
- 데이터 타입 변환 및 기본값 적용

**3. 정렬 단계 (HeaderCore)**:
- `reorder_dataframe` 함수로 컬럼 순서 정렬
- 기준 헤더 순서 (153개) 적용
- 누락 컬럼 추가 (None 값으로)

**4. 저장 단계**:
- 기존 데이터 삭제 (Invoice 번호 기준)
- 새 데이터 추가
- 파일 저장

---

## 6. 검증 결과

### 6.1 변환 로직 검증

**날짜 변환**: ✓ 모든 테스트 케이스 통과  
**Price Center 매핑**: ✓ 모든 테스트 케이스 통과  
**EA 슬롯 매핑**: ✓ EA_Total_Amount 계산 정확  
**금액 변환**: ✓ 환율 변환 정확 (USD ↔ AED)

### 6.2 HeaderCore 적용 검증

**기준 헤더 로드**: ✓ 153개 컬럼 정상 로드  
**실제 파일과 비교**: ✓ 모든 헤더 순서 일치 (153개)  
**컬럼명 매핑**: ✓ 5개 매핑 규칙 정상 작동

### 6.3 통합 변환 검증

**실제 데이터 샘플**: ✓ 처음 3행 변환 정상  
- INVOICE NUMBER: ✓
- SUBJECT: ✓
- NO: ✓

---

## 참고 문서

- [OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md](OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md) - 구조 상세 분석
- [M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md](M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md) - M:CV ↔ DA:DH 상관관계 분석
- [integration_mapping_table.csv](integration_mapping_table.csv) - 매핑 테이블 (CSV)

---

**분석 완료일**: 2025-11-04  
**분석 도구**: `analyze_integration_mapping.py`, `analyze_headercore_application.py`, `analyze_transformation_validation.py`

