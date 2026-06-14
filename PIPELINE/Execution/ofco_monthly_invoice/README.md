# OFCO 인보이스 자동 처리 시스템

**작성자**: MACHO-GPT v3.4-mini  
**작성일**: 2025-11-10  
**버전**: 1.0

---

## 📋 개요

OFCO (Offshore Operations) 인보이스를 매달 자동으로 처리하는 시스템입니다. SAFEEN, ADP, OFCO 자체 인보이스를 통합 처리하며, Cost Center 3-Way 매핑, EA 슬롯 분해, 검증을 자동화합니다.

### 주요 기능

- ✅ **COST CENTER 자동 매핑**: COST MAIN → COST CENTER A → COST CENTER B → PRICE CENTER
- ✅ **SAFEEN/ADP 특화 처리**: Provider별 맞춤 로직
- ✅ **EA 슬롯 자동 분해**: 1~4개 RatePair 자동 생성
- ✅ **3중 검증 시스템**: calc_check, vat_check, pc_check
- ✅ **월간 배치 처리**: 한 번의 명령으로 전체 월 처리
- ✅ **자동 수정 기능**: calc_check 경고 자동 해결

---

## 📁 파일 구조

```
ofco_monthly_invoice/
├── config.py                    # 설정 파일
├── cost_center_mapper.py        # Cost Center 매핑 모듈
├── safeen_adp_handler.py        # SAFEEN/ADP 특화 처리
├── invoice_processor.py         # 메인 프로세서
├── monthly_runner.py            # 월간 실행 스크립트
├── README.md                    # 본 파일
│
├── output/                      # 출력 디렉토리
│   ├── OFCO_INVOICE_2024-11_Processed_20251110_143000.xlsx
│   └── ...
│
└── logs/                        # 로그 디렉토리
    └── ...
```

---

## 🚀 사용법

### 1. 단일 월 처리

```bash
# 2024년 11월 인보이스 처리
python monthly_runner.py --month 2024-11
```

### 2. 자동 수정 포함 처리

```bash
# calc_check 경고를 자동으로 수정하며 처리
python monthly_runner.py --month 2024-11 --auto-fix
```

### 3. 모든 월 처리

```bash
# 2024년 1월~12월 전체 처리
python monthly_runner.py --all-months
```

### 4. 로그 레벨 변경

```bash
# DEBUG 모드로 상세 로그 확인
python monthly_runner.py --month 2024-11 --log-level DEBUG
```

---

## 📊 처리 흐름

```
┌──────────────────────────────────────────────────────────────┐
│                    1. 템플릿 로드                             │
│  OFCO INVOICE.xlsx → DataFrame (889행 × 153컬럼)             │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    2. 월별 필터링                             │
│  INVOICE DATE_YEAR_MONTH == '2024-11'                       │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    3. 라인별 처리                             │
│  ├─ SUBJECT 파싱                                             │
│  ├─ Provider 식별 (SAFEEN/ADP/OFCO)                         │
│  ├─ Cost Center 3-Way 매핑                                   │
│  ├─ Price Center 할당                                        │
│  ├─ EA 슬롯 분해 (1~4개)                                     │
│  └─ 통화 변환 (AED → USD)                                    │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    4. 검증                                    │
│  ├─ calc_check: Σ(EA_i) ≈ Total_Amount_AED (±2%)            │
│  ├─ vat_check: VAT_USD ≈ Amount_USD × 5% (±0.01 USD)        │
│  └─ pc_check: Σ(Price Center) ≈ Total_Amount_AED (±1 AED)   │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    5. 저장                                    │
│  output/OFCO_INVOICE_2024-11_Processed_*.xlsx                │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 COST CENTER 매핑 구조

### 1. COST CENTER → 컬럼 범위 관계

| COST CENTER A | Excel 범위 | 컬럼 인덱스 | 주요 Price Center |
|---------------|-----------|------------|-------------------|
| **CONTRACT** | L:W | 12-23 | AGENCY_FEE_FOR_CARGO_CLEARANCE<br>AGENCY_FEE_FOR_BERTHING_ARRANGEMENT<br>OFCO_HANDLING_FEE |
| **AT COST** | X:AG | 24-33 | SUPPLY_WATER_5000IG<br>FORKLIFT_HIRE_CHARGE<br>DIESEL_VESSEL |
| **PORT HANDLING CHARGE** | AH:CU | 34-99 | BULK_MATERIAL<br>CHANNEL_TRANSIT_CHARGES<br>PORT_DUES<br>Manpower/Equipment |

### 2. L:CU (Price Center) vs CZ:DG (EA) 관계

- **L:CU (컬럼 11-99)**: Price Center별 QTY/AMOUNT 분해 (Pivot 구조)
- **CZ:DG (컬럼 103-110)**: EA 슬롯 (RatePair) 저장

```
Price Center (L:CU)          →  EA Slots (CZ:DG)
─────────────────────────────────────────────────
CARGO_CLEARANCE_AMOUNT: 500  →  EA_1: Qty=1, Rate=500
BERTHING_AMOUNT: 2000        →  EA_1: Qty=1, Rate=2000
CHANNEL_TRANSIT_AMOUNT: 6621 →  EA_1: Qty=2, Rate=3091.25
                             →  EA_2: Qty=2, Rate=100.00
                             →  EA_3: Qty=1, Rate=239.00
```

---

## 🏢 Provider별 처리 로직

### SAFEEN 인보이스

**식별 패턴**: SAFEEN, Channel Crossing, Channel Transit

**매핑 로직**:
```python
COST MAIN: PORT HANDLING
COST CENTER A: PORT HANDLING CHARGE
COST CENTER B: CHANNEL TRANSIT CHARGES
PRICE CENTER: CHANNEL TRANSIT CHARGES

EA Template: CHANNEL_CROSSING_3WAY (3개 슬롯)
```

**EA 분해 예시**:
```
Total: 6621.52 AED
├─ EA_1: Qty=2.0, Rate=3091.25 → 6182.50 (93.5%)
├─ EA_2: Qty=2.0, Rate=100.00  → 200.00 (3.0%)
└─ EA_3: Qty=1.0, Rate=239.00  → 239.00 (3.5%)
```

### ADP 인보이스

**식별 패턴**: ADP, ABU DHABI PORTS, Port Dues, Pilotage

**매핑 로직**:
```python
COST MAIN: PORT HANDLING
COST CENTER A: PORT HANDLING CHARGE
COST CENTER B: PORT DUES & SERVICES CHARGES (Port Dues)
              BULK CARGO HANDLING CHARGES (Bulk Material)
PRICE CENTER: PORT DUES, BULK MATERIAL, Pilotage, GATE PASS

EA Template: PORT_DUES_SIMPLE (1개 슬롯)
```

**EA 분해 예시**:
```
Total: 3500.00 AED
└─ EA_1: Qty=1.0, Rate=3500.00 → 3500.00 (100%)
```

### OFCO 자체 인보이스

**식별 패턴**: OFCO, Agency Fee, Cargo Clearance, Berthing Arrangement

**매핑 로직**:
```python
COST MAIN: CONTRACT
COST CENTER A: CONTRACT
COST CENTER B: AF FOR CC (Cargo Clearance)
              AF FOR BA (Berthing)
              AF FOR FW SA (FW Supply)
PRICE CENTER: AGENCY_FEE_FOR_CARGO_CLEARANCE
              AGENCY_FEE_FOR_BERTHING_ARRANGEMENT
              SUPPLY_WATER_5000IG

EA Template: AGENCY_FEE_1WAY (1개 슬롯)
```

**EA 분해 예시**:
```
Total: 500.00 AED
└─ EA_1: Qty=1.0, Rate=500.00 → 500.00 (100%)
```

---

## 🔍 검증 시스템

### 1. calc_check (EA 계산 검증)

**규칙**: `Σ(EA_i_Qty × EA_i_Rate) ≈ Total_Amount_AED (±2.00%)`

```python
EA_Total = (EA_1_Qty × EA_1_Rate) + 
           (EA_2_Qty × EA_2_Rate) + 
           (EA_3_Qty × EA_3_Rate) + 
           (EA_4_Qty × EA_4_Rate)

diff_pct = |EA_Total - Total_Amount_AED| / Total_Amount_AED

if diff_pct > 0.02:
    calc_check = diff_pct  # 경고
else:
    calc_check = NaN  # 통과
```

### 2. vat_check (VAT 검증)

**규칙**: `VAT_USD ≈ Amount_USD × 5% (±0.01 USD)`

```python
expected_vat = Amount_USD × 0.05
vat_diff = |VAT_USD - expected_vat|

if vat_diff > 0.01:
    vat_check = vat_diff  # 경고
else:
    vat_check = NaN  # 통과
```

### 3. pc_check (Price Center 합계 검증)

**규칙**: `Σ(Price Center AMOUNT) ≈ Total_Amount_AED (±1.00 AED)`

```python
pc_sum = Σ(모든 Price Center AMOUNT 컬럼)
pc_diff = |pc_sum - Total_Amount_AED|

if pc_diff > 1.00:
    pc_check = pc_diff  # 경고
else:
    pc_check = NaN  # 통과
```

---

## 📈 성능 지표

### 현재 성능 (OFCO INVOICE.xlsx 기준)

| 지표 | 값 | 목표 |
|------|-----|------|
| 총 라인 수 | 889 | - |
| SAFEEN 라인 | 88 (9.9%) | - |
| ADP 라인 | 149 (16.8%) | - |
| OFCO 라인 | 652 (73.3%) | - |
| **calc_check 통과율** | 94.8% | 98%+ |
| **vat_check 통과율** | 94.8% | 98%+ |
| **pc_check 통과율** | 100.0% | 100% |
| 처리 속도 | ~1분/889행 | <30초 목표 |

### 개선 로드맵

**Phase 1 (현재)**:
- Rule-based 패턴 매칭
- 3-Way Cost Center 매핑
- Simple EA 템플릿

**Phase 2 (1개월 후)**:
- ML 기반 SUBJECT 분류 (95%+ 정확도)
- 동적 EA 템플릿 학습
- 자동 경고 수정 고도화

**Phase 3 (3개월 후)**:
- BERT fine-tuned 모델 (98%+ 정확도)
- 실시간 API 연동 (PortCall, SAFEEN, ADP)
- COST-GUARD 시스템 통합

---

## 🛠️ 설정 변경

### config.py 주요 설정

```python
# 파일 경로
FILE_PATHS = {
    'input_dir': r'C:\pipeline_execution_scripts\data',
    'output_dir': r'C:\pipeline_execution_scripts\ofco_monthly_invoice\output',
    'template': r'C:\pipeline_execution_scripts\OFCO INVOICE.xlsx',
}

# 통화 환율
CURRENCY_CONFIG = {
    'base_currency': 'AED',
    'exchange_rates': {
        'USD': 3.6725,  # 변경 가능
    },
    'vat_rate': 0.05,  # 5% UAE VAT
}

# 검증 허용 오차
VALIDATION_RULES = {
    'calc_check': {'tolerance': 0.02},  # ±2.00%
    'vat_check': {'tolerance': 0.01},   # ±0.01 USD
    'pc_check': {'tolerance': 1.00},    # ±1.00 AED
}

# 처리 옵션
PROCESSING_OPTIONS = {
    'auto_fix_calc_warnings': True,
    'auto_fill_missing_ea': True,
    'generate_validation_report': True,
    'backup_original': True,
}
```

---

## 🐛 트러블슈팅

### Q1: calc_check 경고가 많이 발생합니다

**원인**: 원본 PDF 데이터 품질 문제 (금액 누락)

**해결책**:
```bash
# 자동 수정 옵션 사용
python monthly_runner.py --month 2024-11 --auto-fix
```

### Q2: SAFEEN 인보이스가 잘못 분류됩니다

**원인**: SUBJECT 패턴이 예상과 다름

**해결책**:
1. `config.py`의 `SAFEEN_PATTERNS['subject_keywords']`에 키워드 추가
2. `cost_center_mapper.py`의 `_map_safeen()` 함수 수정

### Q3: 특정 Price Center가 누락됩니다

**원인**: Price Center 이름 → 컬럼명 변환 실패

**해결책**:
1. `config.py`의 `COST_CENTER_MAPPING`에 Price Center 추가
2. Excel 템플릿에 해당 컬럼 확인

---

## 📞 지원

**문의**: MACHO-GPT v3.4-mini  
**이메일**: cha@samsung.com  
**문서**: `C:\pipeline_execution_scripts\ofco_monthly_invoice\`

---

**© 2025 Samsung C&T Corporation - HVDC Logistics Project**
