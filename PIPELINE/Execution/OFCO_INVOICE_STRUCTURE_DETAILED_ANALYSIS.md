# OFCO INVOICE.xlsx 구조 상세 분석 보고서

**작성일**: 2025-11-04  
**분석 대상**: `OFCO INVOICE.xlsx` (Sheet1 시트)  
**데이터 기준**: 기존 데이터 (OFCO-INV-0001178 제외, 843행)  
**전체 데이터**: 889행 (843행 기존 + 46행 OFCO-INV-0001178)

---

## Executive Summary

`OFCO INVOICE.xlsx` 파일의 구조를 상세히 분석한 결과:

- **전체 컬럼 수**: 153개 (HeaderCore 기준 129개 + 추가 24개)
- **컬럼 그룹**: 기본 정보(14개), Price Center(86개), EA 슬롯(18개), 계산 컬럼(14개), 검증 컬럼(6개), 기타(15개)
- **M:CV 범위**: 88개 컬럼 (Price Center별 QTY/AMOUNT, 44개 Price Center × 2)
- **DA:DH 범위**: 8개 컬럼 (EA 슬롯 Qty/Rate, EA_1~EA_4 × 2)
- **데이터 입력 패턴**: 주로 단일 Price Center (72%), 다중 Price Center도 존재 (28%)

---

## 1. 전체 헤더 구조

### 1.1 컬럼 개수 및 분류

**전체 컬럼 수**: 153개

**컬럼 그룹별 분류**:
| 그룹 | 개수 | 설명 |
|------|------|------|
| 기본 정보 | 14개 | 전체 순번, 청구 회차, NO, Invoice 정보, COST, PRICE CENTER |
| Price Center | 86개 | 44개 Price Center × 2 (QTY + AMOUNT) |
| EA 슬롯 | 18개 | EA_1~EA_4 (Qty, Rate, Amount, Name) + EA_Total_Amount, EA_Mapped_Count |
| 계산 컬럼 | 14개 | Total_Amount, Sum_B_K_to_BA, Diff_A_B 등 |
| 검증 컬럼 | 6개 | calc_check, vat_check, total_check 등 |
| 기타 | 15개 | EA1_Total, TotalCost_K, pc_sum 등 |

### 1.2 컬럼 순서 구조

```
[1-12] 기본 정보 컬럼
├── 전체 순번
├── 청구 회차
├── NO
├── Voyage No
├── SUBJECT
├── INVOICE NUMBER
├── INVOICE DATE
├── INVOICE DATE_YEAR_MONTH
├── COST MAIN
├── COST CENTER A
├── COST CENTER B
└── PRICE CENTER

[13-100] M:CV 범위 (Price Center QTY/AMOUNT)
├── 44개 Price Center × 2 (QTY + AMOUNT) = 88개 컬럼
└── 예: AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY, AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT

[101-104] 금액 정보 컬럼
├── Total_Amount_AED
├── Amount_USD
├── VAT_USD
└── Total_Amount_USD

[105-112] DA:DH 범위 (EA 슬롯 Qty/Rate)
├── EA_1_Qty, EA_1_Rate
├── EA_2_Qty, EA_2_Rate
├── EA_3_Qty, EA_3_Rate
└── EA_4_Qty, EA_4_Rate

[113-153] 계산/검증/기타 컬럼 (41개)
├── Amount_A_AED
├── Sum_B_K_to_BA
├── Sum_C_BB_to_BI
├── Diff_A_B, Diff_A_C, Diff_B_C
├── EA_1_Amount ~ EA_4_Amount
├── EA_Total_Amount
├── calc_check, vat_check, total_check
└── 기타 검증/계산 컬럼
```

### 1.3 데이터 타입 분포

**데이터 타입 분포** (기존 데이터 843행 기준):
- **float64**: 140개 (91.5%)
- **object**: 9개 (5.9%)
- **int64**: 3개 (2.0%)
- **datetime64[ns]**: 1개 (0.7%)

**결측값 분석**:
- 대부분의 컬럼에서 결측값 존재
- 일부 컬럼은 100% 결측 (예: BULK_MATERIAL_BAGGED_CARGO_15_QTY, EA_1_Amount 등)
- 이는 해당 Price Center가 사용되지 않았거나, 자동 생성 컬럼임을 의미

---

## 2. 기본 정보 컬럼 상세

### 2.1 컬럼 목록 및 통계

| 컬럼명 | 값이 있는 행 | 고유값 개수 | 설명 |
|--------|-------------|------------|------|
| 전체 순번 | 843/843 (100%) | 843 | 전체 데이터 순번 (1~843) |
| 청구 회차 | 843/843 (100%) | 4 | 청구 회차 (1~4) |
| NO | 843/843 (100%) | 133 | Invoice별 Line 번호 (SN, 1~133) |
| Voyage No | 807/843 (95.7%) | 95 | 항해 번호 |
| SUBJECT | 842/843 (99.9%) | 587 | 항목 설명 |
| INVOICE NUMBER | 843/843 (100%) | 14 | Invoice 번호 |
| INVOICE DATE | 843/843 (100%) | 12 | Invoice 날짜 |
| INVOICE DATE_YEAR_MONTH | 843/843 (100%) | 12 | Invoice 년월 (YYYY-MM-01) |
| COST MAIN | 843/843 (100%) | 3 | 비용 메인 |
| COST CENTER A | 843/843 (100%) | 7 | 비용 센터 A |
| COST CENTER B | 842/843 (99.9%) | 22 | 비용 센터 B |
| PRICE CENTER | 842/843 (99.9%) | 27 | Price Center 이름 |

### 2.2 Invoice 분포

**상위 10개 Invoice** (행 수 기준):
1. OFCO-INV-0425-051: 133행
2. OFCO-INV-0425-001: 101행
3. OFCO-INV-0425-052: 87행
4. OFCO-INV-0000-181: 82행
5. OFCO-INV-1024-191: 68행
6. OFCO-INV-1124-145: 61행
7. OFCO-INV-0000-416: 58행
8. OFCO-INV-1224-202: 55행
9. OFCO-INV-0000-845: 55행
10. OFCO-INV-0125-198: 46행

### 2.3 날짜 분포

**INVOICE DATE_YEAR_MONTH 분포**:
- 2025-02-01: 133행
- 2025-03-01: 110행
- 2025-01-01: 101행
- 2025-04-01: 81행
- 2024-08-01: 68행
- 2024-09-01: 61행
- 2025-05-01: 58행
- 2024-10-01: 55행
- 2025-07-01: 55행
- 2024-12-01: 47행

---

## 3. M:CV 범위 (Price Center) 상세

### 3.1 구조

**Excel 컬럼**: M (13번째) ~ CV (100번째)  
**총 컬럼 수**: 88개  
**구조**: 44개 Price Center × 2 (QTY + AMOUNT)

### 3.2 Price Center 목록

**사용되는 Price Center**: 43개 (44개 중)

**상위 15개 Price Center** (사용 빈도 기준):

| 순위 | Price Center | 사용 행 | 합계 | 평균 |
|------|-------------|---------|------|------|
| 1 | CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT | 190행 | 763,393.50 | 4,017.86 |
| 2 | GENERAL_WASTE_SERVICE | 176행 | 18,000.00 | 102.27 |
| 3 | PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT | 176행 | 161,500.00 | 917.61 |
| 4 | CHANNEL_TRANSIT_CROSSING_REQUEST | 126행 | 13,400.00 | 106.35 |
| 5 | AGENCY_FEE_FOR_BERTHING_ARRANGEMENT | 90행 | 167,340.00 | 1,859.33 |
| 6 | OFCO_HANDLING_FEE | 77행 | 192,947.40 | 2,505.81 |
| 7 | DOCUMENT_PROCESSING_CHARGE | 76행 | 2,660.00 | 35.00 |
| 8 | PEC_CHANGES | 75행 | 44,000.00 | 586.67 |
| 9 | AGENCY_FEE_FOR_CARGO_CLEARANCE | 74행 | 37,500.00 | 506.76 |
| 10 | BUNKERING_LUBE_OIL_SLUDGE_SULPHUR_BILGE_TRANSFER_BUNKERING_PERMIT | 72행 | 1,200.00 | 16.67 |
| 11 | BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY | 56행 | 240,240.32 | 4,290.01 |
| 12 | MANPOWER_BANKSMAN | 38행 | 15,281.21 | 402.14 |
| 13 | MANPOWER_RIGGER | 36행 | 54,439.83 | 1,512.22 |
| 14 | MANPOWER_SUPERVISOR | 36행 | 35,280.16 | 980.00 |
| 15 | AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT | 34행 | 6,800.00 | 200.00 |

### 3.3 Price Center 개수 분포

**Price Center 개수별 행 수**:
- **1개**: 607행 (72.0%) - 가장 일반적
- **2개**: 204행 (24.2%)
- **3개**: 29행 (3.4%)
- **4개**: 3행 (0.4%)

---

## 4. DA:DH 범위 (EA 슬롯) 상세

### 4.1 구조

**Excel 컬럼**: DA (105번째) ~ DH (112번째)  
**총 컬럼 수**: 8개  
**구조**: EA_1~EA_4 × 2 (Qty + Rate)

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

### 4.2 EA 슬롯 사용 통계

**EA 슬롯별 사용 통계** (기존 데이터 843행):

| EA 슬롯 | 사용 행 | 사용률 | Qty 평균 | Rate 평균 |
|---------|---------|--------|----------|-----------|
| EA_1 | 843행 | 100% | 324.79 | 2,977.04 |
| EA_2 | 256행 | 30.4% | 170.31 | 1,041.18 |
| EA_3 | 56행 | 6.6% | 31.74 | 330.55 |
| EA_4 | 26행 | 3.1% | 0.31 | 887.57 |

### 4.3 EA 슬롯 개수 분포

**EA 슬롯 개수별 행 수**:
- **1개**: 599행 (71.1%) - 가장 일반적
- **2개**: 203행 (24.1%)
- **3개**: 33행 (3.9%)
- **4개**: 8행 (0.9%)

### 4.4 M:CV ↔ DA:DH 변환 로직

**변환 규칙**:
1. **단일 Price Center → 단일 EA 슬롯** (1:1 매핑)
   - Price Center QTY → EA_X_Qty
   - Price Center AMOUNT / QTY → EA_X_Rate
   - 예: `AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY=1.0, AMOUNT=500.0` → `EA_1_Qty=1.0, EA_1_Rate=500.0`

2. **다중 Price Center → 다중 EA 슬롯** (N:N 매핑)
   - 각 Price Center가 하나의 EA 슬롯에 매핑
   - 우선순위: EA_1 → EA_2 → EA_3 → EA_4

**변환 패턴 통계** (샘플 기준):
- **1PC→1EA**: 55%
- **2PC→2EA**: 35%
- **3PC→3EA**: 10%

자세한 내용은 [M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md](M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md) 참조.

---

## 5. 계산 컬럼 상세

### 5.1 계산 컬럼 목록

**주요 계산 컬럼**:
1. **Sum_B_K_to_BA**: K~BA 범위의 AMOUNT 컬럼 합계
2. **Sum_C_BB_to_BI**: BB~BI 범위의 AMOUNT 컬럼 합계
3. **Amount_A_AED**: EA_Total_Amount (EA 슬롯 금액 합계)
4. **Diff_A_B**: Amount_A_AED - Sum_B_K_to_BA
5. **Diff_A_C**: Amount_A_AED - Sum_C_BB_to_BI
6. **Diff_B_C**: Sum_B_K_to_BA - Sum_C_BB_to_BI
7. **TotalCost_K**: K열의 AMOUNT 값
8. **Remaining_After_K**: Diff_A_B와 동일

### 5.2 계산 컬럼 통계

**계산 컬럼 통계** (기존 데이터 843행):

| 컬럼명 | 값이 있는 행 | 평균 | 범위 |
|--------|-------------|------|------|
| Sum_B_K_to_BA | 843/843 (100%) | 5,065.51 | 10.00 ~ 309,396.00 |
| Sum_C_BB_to_BI | 843/843 (100%) | 4,702.40 | 10.00 ~ 137,280.03 |
| Amount_A_AED | 843/843 (100%) | 4,702.40 | 9.99 ~ 137,280.00 |
| Diff_A_B | 843/843 (100%) | -363.11 | -306,104.04 ~ 0.64 |
| Diff_A_C | 843/843 (100%) | 0.00 | -0.56 ~ 0.59 |
| Diff_B_C | 843/843 (100%) | -363.11 | -306,104.04 ~ 0.64 |
| TotalCost_K | 843/843 (100%) | 4,702.40 | 10.00 ~ 137,280.03 |
| Remaining_After_K | 843/843 (100%) | 0.00 | -0.56 ~ 0.59 |

**자동 생성 여부**: 모든 계산 컬럼이 100% 값 존재 → 자동 생성됨

### 5.3 계산 로직

**Sum_B_K_to_BA**:
```
Sum_B_K_to_BA = Σ(K~BA 범위의 모든 _AMOUNT 컬럼 값)
범위: Excel 컬럼 K (11) ~ BA (53)
M:CV 범위 포함 (M~CV는 K~BA의 확장)
```

**Sum_C_BB_to_BI**:
```
Sum_C_BB_to_BI = Σ(BB~BI 범위의 모든 _AMOUNT 컬럼 값)
범위: Excel 컬럼 BB (54) ~ BI (61)
M:CV 범위와 겹치지 않음
```

**차이 계산**:
```
Diff_A_B = Amount_A_AED - Sum_B_K_to_BA
Diff_A_C = Amount_A_AED - Sum_C_BB_to_BI
Diff_B_C = Sum_B_K_to_BA - Sum_C_BB_to_BI
```

---

## 6. 검증 컬럼 상세

### 6.1 검증 컬럼 목록

**주요 검증 컬럼**:
1. **calc_check**: 계산 검증 (bool)
2. **calc_status**: 계산 상태 (str)
3. **calc_diff**: 계산 차이 (float)
4. **vat_check**: VAT 검증 (bool)
5. **vat_diff**: VAT 차이 (float)
6. **total_check**: 총액 검증 (bool)
7. **total_diff**: 총액 차이 (float)

### 6.2 검증 로직

**calc_check**:
- Price Center AMOUNT 합계 = EA_Total_Amount (오차 ≤ 0.01)
- 또는 unit_product × rate = amount_excl_tax (오차 허용)

**vat_check**:
- VAT 계산 검증
- tax_amount = amount_excl_tax × tax_rate_pct / 100

**total_check**:
- 총액 검증
- total_incl_tax = amount_excl_tax + tax_amount

---

## 7. 데이터 입력 구조

### 7.1 입력 흐름

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

### 7.2 입력 패턴

**Price Center 개수 분포**:
- 1개: 72.0% (가장 일반적)
- 2개: 24.2%
- 3개: 3.4%
- 4개: 0.4%

**EA 슬롯 개수 분포**:
- 1개: 71.1% (가장 일반적)
- 2개: 24.1%
- 3개: 3.9%
- 4개: 0.9%

### 7.3 데이터 무결성

**검증 항목**:
1. **EA_Total_Amount 검증**: Price Center AMOUNT 합계 = EA_Total_Amount
2. **EA Rate 계산 검증**: Rate = Amount / Qty
3. **계산 컬럼 검증**: Diff_A_C ≈ 0 (거의 완벽한 일치)

---

## 8. HeaderCore 기준 헤더 비교

### 8.1 헤더 개수 비교

**HeaderCore 기준 헤더**: 129개  
**실제 파일 헤더**: 153개  
**차이**: 24개 추가

### 8.2 추가된 헤더

추가된 24개 헤더는 주로:
- EA 슬롯 관련 컬럼 (EA_1_Amount, EA_1_Name 등)
- 검증 컬럼 (calc_status, calc_diff 등)
- 기타 계산 컬럼 (EA1_Total, EA2_Total 등)

---

## 9. 결론

### 9.1 핵심 발견

1. **전체 구조**: 153개 컬럼, 6개 그룹으로 분류
2. **M:CV 범위**: 88개 컬럼 (Price Center별 QTY/AMOUNT)
3. **DA:DH 범위**: 8개 컬럼 (EA 슬롯 Qty/Rate)
4. **변환 로직**: Price Center → EA 슬롯 (1:1 또는 N:N)
5. **계산 컬럼**: 자동 생성 (100% 값 존재)
6. **입력 패턴**: 주로 단일 Price Center (72%)

### 9.2 데이터 입력 규칙

1. **Price Center 입력**: M:CV 범위에 QTY/AMOUNT 쌍으로 입력
2. **EA 슬롯 변환**: Price Center 데이터를 EA 슬롯으로 변환
3. **계산 컬럼**: 자동 생성 (수동 입력 불필요)
4. **검증 컬럼**: 자동 생성 (수동 입력 불필요)

### 9.3 주요 특징

- **M:CV 범위**: Price Center별 데이터 저장 (입력 영역)
- **DA:DH 범위**: EA 슬롯 데이터 저장 (변환 영역)
- **계산 관계**: M:CV 범위가 K~BA 계산에 포함
- **데이터 무결성**: Diff_A_C ≈ 0 (거의 완벽한 일치)

---

## 참고 문서

- [M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md](M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md) - M:CV ↔ DA:DH 상관관계 상세 분석
- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - 통합 가이드
- [PIPELINE_INTEGRATION_COMPLETE_REPORT.md](PIPELINE_INTEGRATION_COMPLETE_REPORT.md) - 통합 완료 보고서

---

**분석 완료일**: 2025-11-04  
**분석 도구**: `analyze_header_structure_detailed.py`, `analyze_data_input_structure.py`  
**데이터 기준**: OFCO INVOICE.xlsx (Sheet1, 889행, OFCO-INV-0001178 제외 843행)

