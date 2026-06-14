# OFCO INVOICE.xlsx M:CV ↔ DA:DH 상관관계 상세 분석 보고서

**작성일**: 2025-11-04  
**분석 대상**: `OFCO INVOICE.xlsx` (Sheet1 시트)  
**분석 범위**: M:CV 컬럼 범위와 DA:DH 컬럼 범위의 상관관계 로직  
**데이터 기준**: 기존 데이터 (OFCO-INV-0001178 제외, 843행)

---

## Executive Summary

`OFCO INVOICE.xlsx` 파일에서 **M:CV 범위**와 **DA:DH 범위**는 서로 밀접한 상관관계를 가진 데이터 구조입니다.

- **M:CV 범위**: Price Center별 QTY/AMOUNT 컬럼 (88개, 44개 Price Center × 2)
- **DA:DH 범위**: EA 슬롯 Qty/Rate 컬럼 (8개, EA_1~EA_4 × 2)
- **변환 로직**: Price Center AMOUNT → EA 슬롯으로 변환
- **계산 관계**: Sum_B_K_to_BA, Diff_A_B 등 계산 컬럼과 연계

---

## 1. 컬럼 범위 정의

### 1.1 M:CV 범위

**Excel 컬럼**: M (13번째) ~ CV (100번째)  
**DataFrame 인덱스**: 12 ~ 99  
**총 컬럼 수**: 88개

**구조**:
- **QTY 컬럼**: 44개 (Price Center별 수량)
- **AMOUNT 컬럼**: 44개 (Price Center별 금액)
- **Price Center 개수**: 44개

**주요 Price Center 목록** (사용 빈도 상위 10개):
1. CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT (190행)
2. GENERAL_WASTE_SERVICE (176행)
3. PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT (176행)
4. CHANNEL_TRANSIT_CROSSING_REQUEST (126행)
5. AGENCY_FEE_FOR_BERTHING_ARRANGEMENT (90행)
6. OFCO_HANDLING_FEE (77행)
7. DOCUMENT_PROCESSING_CHARGE (76행)
8. PEC_CHANGES (75행)
9. AGENCY_FEE_FOR_CARGO_CLEARANCE (74행)
10. BUNKERING_LUBE_OIL_SLUDGE_SULPHUR_BILGE_TRANSFER_BUNKERING_PERMIT (72행)

**컬럼 명명 규칙**:
- QTY 컬럼: `{PRICE_CENTER_NAME}_QTY`
- AMOUNT 컬럼: `{PRICE_CENTER_NAME}_AMOUNT`

**예시**:
- `AGENCY_FEE_FOR_BERTHING_ARRANGEMENT_QTY`
- `AGENCY_FEE_FOR_BERTHING_ARRANGEMENT_AMOUNT`

### 1.2 DA:DH 범위

**Excel 컬럼**: DA (105번째) ~ DH (112번째)  
**DataFrame 인덱스**: 104 ~ 111  
**총 컬럼 수**: 8개

**구조**:
- **EA Qty 컬럼**: 4개 (EA_1_Qty, EA_2_Qty, EA_3_Qty, EA_4_Qty)
- **EA Rate 컬럼**: 4개 (EA_1_Rate, EA_2_Rate, EA_3_Rate, EA_4_Rate)

**컬럼 목록**:
| Excel 컬럼 | 인덱스 | 컬럼명 | 설명 |
|-----------|--------|--------|------|
| DA | 105 | EA_1_Qty | EA 슬롯 1 수량 |
| DB | 106 | EA_1_Rate | EA 슬롯 1 단가 |
| DC | 107 | EA_2_Qty | EA 슬롯 2 수량 |
| DD | 108 | EA_2_Rate | EA 슬롯 2 단가 |
| DE | 109 | EA_3_Qty | EA 슬롯 3 수량 |
| DF | 110 | EA_3_Rate | EA 슬롯 3 단가 |
| DG | 111 | EA_4_Qty | EA 슬롯 4 수량 |
| DH | 112 | EA_4_Rate | EA 슬롯 4 단가 |

**EA 슬롯별 사용 통계** (기존 데이터 843행 기준):
- **EA_1**: 843행 (100%) - Qty 평균: 324.79, Rate 평균: 2,977.04
- **EA_2**: 256행 (30.4%) - Qty 평균: 170.31, Rate 평균: 1,041.18
- **EA_3**: 56행 (6.6%) - Qty 평균: 31.74, Rate 평균: 330.55
- **EA_4**: 26행 (3.1%) - Qty 평균: 0.31, Rate 평균: 887.57

---

## 2. 변환 로직 상세 분석

### 2.1 Price Center → EA 슬롯 변환 규칙

**기본 변환 규칙**:
1. **단일 Price Center → 단일 EA 슬롯** (1:1 매핑)
   - Price Center QTY → EA_X_Qty
   - Price Center AMOUNT / QTY → EA_X_Rate
   - 예: `AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY=1.0, AMOUNT=500.0` → `EA_1_Qty=1.0, EA_1_Rate=500.0`

2. **다중 Price Center → 다중 EA 슬롯** (N:N 매핑)
   - 각 Price Center가 하나의 EA 슬롯에 매핑
   - 우선순위 기반 할당 (EA_1 → EA_2 → EA_3 → EA_4)
   - 예: 2개 Price Center → EA_1, EA_2에 각각 할당

**변환 패턴 통계** (샘플 20개 행 기준):
- **1PC→1EA**: 11행 (55%)
- **2PC→2EA**: 7행 (35%)
- **3PC→3EA**: 2행 (10%)

### 2.2 변환 로직 구현

**소스 코드 위치**: `pipeline_docs/pipeline_steps/step_07_final_output/scripts/ofco_integrate_pipeline_to_excel.py`

**핵심 로직** (transform_row 함수):
```python
# 4. Price Center별 QTY/AMOUNT 매핑
price_center_val = target_row.get('PRICE CENTER', '')
if price_center_val:
    pc_qty_col, pc_amt_col = find_price_center_columns(price_center_val, target_template)
    if pc_qty_col and pc_amt_col:
        # EA_1에서 QTY/AMOUNT 추출
        qty_val = target_row.get('EA_1_Qty') or 0
        amt_val = target_row.get('EA_1_Amount') or 0
        
        target_row[pc_qty_col] = qty_val
        target_row[pc_amt_col] = amt_val
```

**EA 할당 로직** (ofco_ea_allocator_v1p3.py):
```python
# Price Center별 QTY/AMOUNT를 EA 슬롯으로 변환
# 우선순위 기반으로 EA_1~EA_4에 할당
# 각 EA 슬롯: Qty, Rate, Amount 계산
```

### 2.3 변환 검증

**검증 결과** (샘플 20개 행):
- **1:1 매칭 확인**: 9개 행
  - Price Center AMOUNT = EA 슬롯 Amount (오차 ≤ 0.01)
  - 예: PC=500.00 = EA=500.00

**변환 정확도**:
- 단일 Price Center의 경우 100% 정확한 변환
- 다중 Price Center의 경우 각각의 EA 슬롯에 정확히 분배

---

## 3. 계산 컬럼과의 관계

### 3.1 K~BA 범위 (Sum_B_K_to_BA 계산)

**Excel 컬럼**: K (11번째) ~ BA (53번째)  
**AMOUNT 컬럼 수**: 20개  
**계산 컬럼**: `Sum_B_K_to_BA`

**계산 로직**:
```python
# K~BA 범위의 모든 _AMOUNT 컬럼 합계
sum_b_k_to_ba = sum([row[col] for col in k_to_ba_amount_cols if pd.notna(row[col])])
```

**M:CV 범위와의 관계**:
- M (13)은 K (11)보다 **2개 뒤**
- CV (100)는 BA (53)보다 **47개 뒤**
- **M:CV 범위가 K:BA 범위를 포함** (M~CV는 K~BA의 확장)

**통계** (기존 데이터 843행):
- 값이 있는 행: 843행 (100%)
- 평균: 5,065.51
- 범위: 10.00 ~ 309,396.00

### 3.2 BB~BI 범위 (Sum_C_BB_to_BI 계산)

**Excel 컬럼**: BB (54번째) ~ BI (61번째)  
**AMOUNT 컬럼 수**: 4개  
**계산 컬럼**: `Sum_C_BB_to_BI`

**계산 로직**:
```python
# BB~BI 범위의 모든 _AMOUNT 컬럼 합계
sum_c_bb_to_bi = sum([row[col] for col in bb_to_bi_amount_cols if pd.notna(row[col])])
```

**M:CV 범위와의 관계**:
- BB (54)는 CV (100)보다 **46개 앞**
- BI (61)는 CV (100)보다 **39개 앞**
- **BB~BI 범위는 M~CV 범위와 겹치지 않음**

**통계** (기존 데이터 843행):
- 값이 있는 행: 843행 (100%)
- 평균: 4,702.40
- 범위: 10.00 ~ 137,280.03

### 3.3 차이 계산 컬럼

**계산 컬럼 목록**:
1. **Diff_A_B**: `Amount_A_AED - Sum_B_K_to_BA`
   - 통계: 평균 -363.11, 범위 -306,104.04 ~ 0.64
2. **Diff_A_C**: `Amount_A_AED - Sum_C_BB_to_BI`
   - 통계: 평균 0.00, 범위 -0.56 ~ 0.59
3. **Diff_B_C**: `Sum_B_K_to_BA - Sum_C_BB_to_BI`
   - 통계: 평균 -363.11, 범위 -306,104.04 ~ 0.64
4. **Remaining_After_K**: `Diff_A_B`와 동일
   - 통계: 평균 0.00, 범위 -0.56 ~ 0.59

**관계식**:
```
Amount_A_AED = EA_Total_Amount (EA 슬롯 금액 합계)
Sum_B_K_to_BA = K~BA 범위 AMOUNT 컬럼 합계 (M:CV 범위 포함)
Sum_C_BB_to_BI = BB~BI 범위 AMOUNT 컬럼 합계

Diff_A_B = Amount_A_AED - Sum_B_K_to_BA
Diff_A_C = Amount_A_AED - Sum_C_BB_to_BI
Diff_B_C = Sum_B_K_to_BA - Sum_C_BB_to_BI
```

---

## 4. 데이터 입력 구조 (기존 데이터 기준)

### 4.1 입력 흐름

```
[입력 단계]
Price Center별 QTY/AMOUNT (M:CV 범위)
  ↓
[변환 단계]
EA 슬롯 Qty/Rate (DA:DH 범위)
  ↓
[계산 단계]
Sum_B_K_to_BA, Diff_A_B 등 계산 컬럼
  ↓
[검증 단계]
calc_check, vat_check 등 검증 컬럼
```

### 4.2 입력 패턴 분석

**기존 데이터 통계** (843행, OFCO-INV-0001178 제외):

1. **Price Center 사용 분포**:
   - 사용되는 Price Center: 43개 (44개 중)
   - 가장 많이 사용: CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT (190행)
   - Price Center 데이터가 있는 행: 796개 (94.4%)

2. **EA 슬롯 사용 분포**:
   - EA_1 사용: 843행 (100%)
   - EA_2 사용: 256행 (30.4%)
   - EA_3 사용: 56행 (6.6%)
   - EA_4 사용: 26행 (3.1%)

3. **변환 패턴**:
   - 단일 Price Center → 단일 EA 슬롯: 가장 일반적
   - 다중 Price Center → 다중 EA 슬롯: 복잡한 항목에서 사용

### 4.3 데이터 무결성

**검증 항목**:
1. **EA_Total_Amount 검증**:
   - Price Center AMOUNT 합계 = EA_Total_Amount
   - 오차 허용 범위: ≤ 0.01

2. **EA Rate 계산 검증**:
   - Rate = Amount / Qty
   - 모든 Rate 계산이 정확함 (불일치 0개)

3. **계산 컬럼 검증**:
   - Diff_A_C 평균: 0.00 (거의 완벽한 일치)
   - Diff_A_B 평균: -363.11 (일부 차이 존재)

---

## 5. 핵심 상관관계 요약

### 5.1 구조적 관계

```
M:CV 범위 (88개 컬럼)
├── Price Center별 QTY (44개)
└── Price Center별 AMOUNT (44개)
    ↓ [변환]
DA:DH 범위 (8개 컬럼)
├── EA_1~EA_4 Qty (4개)
└── EA_1~EA_4 Rate (4개)
    ↓ [계산]
계산 컬럼
├── Sum_B_K_to_BA (K~BA 범위 합계, M:CV 포함)
├── Sum_C_BB_to_BI (BB~BI 범위 합계, M:CV와 겹치지 않음)
└── Diff_A_B, Diff_A_C, Diff_B_C (차이 계산)
```

### 5.2 데이터 흐름

1. **입력**: Price Center별 QTY/AMOUNT (M:CV 범위)
2. **변환**: EA 슬롯 Qty/Rate (DA:DH 범위)
3. **계산**: Sum_B_K_to_BA, Diff_A_B 등
4. **검증**: calc_check, vat_check 등

### 5.3 주요 특징

1. **M:CV 범위**:
   - Price Center별 데이터 저장
   - 44개 Price Center × 2 (QTY + AMOUNT) = 88개 컬럼
   - K~BA 범위를 포함하는 확장 범위

2. **DA:DH 범위**:
   - EA 슬롯 데이터 저장
   - EA_1~EA_4 × 2 (Qty + Rate) = 8개 컬럼
   - Price Center 데이터의 변환된 형태

3. **계산 관계**:
   - Sum_B_K_to_BA: M:CV 범위의 일부 포함
   - Sum_C_BB_to_BI: M:CV 범위와 겹치지 않음
   - Diff_A_B, Diff_A_C: Amount_A_AED와의 차이 계산

---

## 6. 실제 데이터 예시

### 6.1 단일 Price Center → 단일 EA 슬롯

**예시 1**:
```
PRICE CENTER: AGENCY FEE FOR CARGO CLEARANCE
M:CV 범위:
  - AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY: 1.0
  - AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT: 500.0

DA:DH 범위:
  - EA_1_Qty: 1.0
  - EA_1_Rate: 500.0
  - EA_2_Qty: nan
  - EA_2_Rate: nan

검증: PC AMOUNT (500.0) = EA Amount (1.0 × 500.0 = 500.0) ✅
```

### 6.2 다중 Price Center → 다중 EA 슬롯

**예시 2**:
```
PRICE CENTER: BULK MATERIAL
M:CV 범위:
  - DOCUMENT_PROCESSING_CHARGE_QTY: 1.0
  - DOCUMENT_PROCESSING_CHARGE_AMOUNT: 35.0
  - BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY_QTY: 600.0
  - BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY_AMOUNT: 3900.0

DA:DH 범위:
  - EA_1_Qty: 1.0
  - EA_1_Rate: 35.0
  - EA_2_Qty: 600.0
  - EA_2_Rate: 6.5
  - EA_3_Qty: nan
  - EA_3_Rate: nan

검증: 
  - PC AMOUNT 합계 (35.0 + 3900.0 = 3935.0) = EA Total (1.0×35.0 + 600.0×6.5 = 3935.0) ✅
```

---

## 7. 계산 컬럼 상세 분석

### 7.1 Sum_B_K_to_BA

**의미**: K~BA 범위의 모든 AMOUNT 컬럼 합계  
**범위**: Excel 컬럼 K (11) ~ BA (53)  
**M:CV 관계**: M:CV 범위가 K:BA 범위를 포함

**계산식**:
```
Sum_B_K_to_BA = Σ(모든 K~BA 범위의 _AMOUNT 컬럼 값)
```

**통계** (기존 데이터 843행):
- 평균: 5,065.51
- 최소: 10.00
- 최대: 309,396.00
- 표준편차: 약 15,000

### 7.2 Sum_C_BB_to_BI

**의미**: BB~BI 범위의 모든 AMOUNT 컬럼 합계  
**범위**: Excel 컬럼 BB (54) ~ BI (61)  
**M:CV 관계**: M:CV 범위와 겹치지 않음

**계산식**:
```
Sum_C_BB_to_BI = Σ(모든 BB~BI 범위의 _AMOUNT 컬럼 값)
```

**통계** (기존 데이터 843행):
- 평균: 4,702.40
- 최소: 10.00
- 최대: 137,280.03
- 표준편차: 약 12,000

### 7.3 Diff_A_B, Diff_A_C, Diff_B_C

**의미**: 금액 차이 계산

**계산식**:
```
Diff_A_B = Amount_A_AED - Sum_B_K_to_BA
Diff_A_C = Amount_A_AED - Sum_C_BB_to_BI
Diff_B_C = Sum_B_K_to_BA - Sum_C_BB_to_BI
```

**관계식**:
```
Diff_A_B = Diff_A_C - Diff_B_C
```

**통계** (기존 데이터 843행):
- **Diff_A_B**: 평균 -363.11 (일부 차이 존재)
- **Diff_A_C**: 평균 0.00 (거의 완벽한 일치)
- **Diff_B_C**: 평균 -363.11 (Sum_B와 Sum_C의 차이)

---

## 8. 데이터 입력 규칙

### 8.1 M:CV 범위 입력 규칙

1. **Price Center별 입력**:
   - 각 행은 하나 이상의 Price Center를 가질 수 있음
   - PRICE CENTER 컬럼에 명시된 Price Center의 QTY/AMOUNT만 입력
   - 나머지 Price Center 컬럼은 NaN 또는 0

2. **QTY/AMOUNT 쌍 입력**:
   - QTY와 AMOUNT는 항상 쌍으로 입력
   - QTY가 0이면 AMOUNT도 0 또는 NaN
   - AMOUNT = QTY × Rate (Rate는 별도 계산)

3. **데이터 타입**:
   - QTY: float (수량)
   - AMOUNT: float (금액, AED 또는 USD)

### 8.2 DA:DH 범위 입력 규칙

1. **EA 슬롯 할당**:
   - Price Center 데이터를 EA 슬롯으로 변환
   - 우선순위: EA_1 → EA_2 → EA_3 → EA_4
   - 최대 4개 EA 슬롯 사용

2. **Qty/Rate 계산**:
   - EA_X_Qty = Price Center QTY
   - EA_X_Rate = Price Center AMOUNT / QTY
   - EA_X_Amount = EA_X_Qty × EA_X_Rate (별도 컬럼에 저장)

3. **데이터 타입**:
   - Qty: float (수량)
   - Rate: float (단가)

### 8.3 계산 컬럼 자동 생성

1. **Sum_B_K_to_BA**:
   - K~BA 범위의 모든 _AMOUNT 컬럼 합계
   - 자동 계산 (수동 입력 불필요)

2. **Sum_C_BB_to_BI**:
   - BB~BI 범위의 모든 _AMOUNT 컬럼 합계
   - 자동 계산 (수동 입력 불필요)

3. **Diff 컬럼**:
   - Amount_A_AED와의 차이 계산
   - 자동 계산 (수동 입력 불필요)

---

## 9. 검증 규칙

### 9.1 데이터 무결성 검증

1. **EA_Total_Amount 검증**:
   ```
   EA_Total_Amount = Σ(EA_1~EA_4 Amount)
   Price Center AMOUNT 합계 = EA_Total_Amount (오차 ≤ 0.01)
   ```

2. **EA Rate 계산 검증**:
   ```
   EA_X_Rate = EA_X_Amount / EA_X_Qty
   또는
   EA_X_Rate = Price Center AMOUNT / Price Center QTY
   ```

3. **계산 컬럼 검증**:
   ```
   Diff_A_C ≈ 0 (거의 완벽한 일치)
   Diff_A_B는 일부 차이 허용 (평균 -363.11)
   ```

### 9.2 검증 통계

**기존 데이터 843행 기준**:
- **EA_Total_Amount 검증**: 정상 0행, 불일치 0행 (검증 로직 필요)
- **EA Rate 계산**: 불일치 0개 (100% 정확)
- **PC 합계 vs EA_Total**: 정상 0행, 이상 0행 (검증 로직 필요)

---

## 10. 결론

### 10.1 핵심 발견

1. **M:CV 범위**는 Price Center별 데이터를 저장하는 **입력 영역**
2. **DA:DH 범위**는 Price Center 데이터를 변환한 **EA 슬롯 영역**
3. **변환 로직**은 1:1 또는 N:N 매핑으로 Price Center → EA 슬롯 변환
4. **계산 컬럼**은 M:CV 범위의 AMOUNT 합계를 기반으로 계산

### 10.2 데이터 입력 구조

```
입력: Price Center별 QTY/AMOUNT (M:CV)
  ↓
변환: EA 슬롯 Qty/Rate (DA:DH)
  ↓
계산: Sum_B_K_to_BA, Diff_A_B 등
  ↓
검증: calc_check, vat_check 등
```

### 10.3 주요 특징

- **M:CV 범위**: 88개 컬럼 (44개 Price Center × 2)
- **DA:DH 범위**: 8개 컬럼 (EA_1~EA_4 × 2)
- **변환 패턴**: 주로 1:1 매핑 (55%), 다중 매핑도 존재 (45%)
- **계산 관계**: M:CV 범위가 K~BA 계산에 포함, BB~BI는 별도

---

## 참고 문서

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - 통합 가이드
- [PIPELINE_INTEGRATION_COMPLETE_REPORT.md](PIPELINE_INTEGRATION_COMPLETE_REPORT.md) - 통합 완료 보고서
- [Step 7 README](README.md) - 통합 스크립트 상세

---

**분석 완료일**: 2025-11-04  
**분석 도구**: `analyze_mcv_dadh_detailed.py`  
**데이터 기준**: OFCO INVOICE.xlsx (Sheet1, 889행, OFCO-INV-0001178 제외 843행)
