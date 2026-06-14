# 📘 Invoice Validation System - User Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-14
**Project**: HVDC ADOPT - DSV Shipment Invoice Validation

---

## 목차

1. [시스템 개요](#시스템-개요)
2. [빠른 시작](#빠른-시작)
3. [새 인보이스 검증 절차](#새-인보이스-검증-절차)
4. [Configuration 관리](#configuration-관리)
5. [결과 해석](#결과-해석)
6. [문제 해결](#문제-해결)
7. [추가 가이드](#추가-가이드)

---

## 시스템 개요

### 목적
DSV 및 기타 포워더의 인보이스를 자동으로 검증하여 계약 요율 대비 청구 요율의 정확성을 확인합니다.

### 주요 기능
- ✅ 계약 요율 자동 조회 및 비교
- ✅ PDF 첨부 파일 자동 매칭 및 추출
- ✅ COST-GUARD 밴드 자동 분류
- ✅ Gate Score 기반 종합 검증
- ✅ Excel 보고서 자동 생성 (조건부 서식 포함)

### 지원 범위
- **포워더**: DSV (MAERSK 등 추가 예정)
- **화물 유형**: Container (FCL/LCL), Air, Bulk
- **검증 항목**: 102+ 개 (Sept 2025 기준)

---

## 빠른 시작

### 1. 필수 파일 준비

```
HVDC_Invoice_Audit/01_DSV_SHPT/
├── Core_Systems/
│   └── SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm
├── SCNT Import (Sept 2025) - Supporting Documents/
│   ├── 01. HVDC-ADOPT-SCT-0121/
│   │   ├── BOE_xxx.pdf
│   │   └── DO_xxx.pdf
│   └── 02. HVDC-ADOPT-SCT-0122/
│       └── ... (PDF files)
└── Rate/
    ├── config_shpt_lanes.json
    ├── config_contract_rates.json
    ├── config_cost_guard_bands.json
    └── config_validation_rules.json
```

### 2. 실행 명령어

```bash
cd HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems
python validate_masterdata_with_config_251014.py
```

### 3. 출력 파일 확인

```
Core_Systems/out/
├── masterdata_validated_YYYYMMDD_HHMMSS.csv
└── masterdata_validated_YYYYMMDD_HHMMSS.xlsx

Results/
└── SCNT_SHIPMENT_SEPT2025_VALIDATED_YYYYMMDD_HHMMSS.xlsx (최종 보고서)
```

---

## 새 인보이스 검증 절차

### Scenario 1: 같은 프로젝트, 다른 월 (예: October 2025)

#### Step 1: 인보이스 파일 배치
```
01_DSV_SHPT/Core_Systems/
└── SCNT SHIPMENT DRAFT INVOICE (OCT 2025)_FINAL.xlsm
```

#### Step 2: Configuration 업데이트

**`Rate/config_metadata.json` 수정:**
```json
{
    "applicable_period": "2025-10",  // 변경
    "currency_fx_date": "2025-10-31",  // 변경
    "fx_rates": {
        "USD_AED": 3.6725,  // 최신 환율로 업데이트
        "last_updated": "2025-10-31"  // 변경
    }
}
```

#### Step 3: 검증 실행
```python
# validate_masterdata_with_config_251014.py 내부
excel_file = "SCNT SHIPMENT DRAFT INVOICE (OCT 2025)_FINAL.xlsm"  # 파일명 변경
```

또는 스크립트 실행 시 인자로 전달:
```bash
python validate_masterdata_with_config_251014.py --file "SCNT SHIPMENT DRAFT INVOICE (OCT 2025)_FINAL.xlsm"
```

#### Step 4: 결과 확인
- `Results/` 디렉토리에서 최신 Excel 파일 확인
- Validation Status, Gate Score 검토

---

### Scenario 2: 같은 월, 다른 포워더 (예: MAERSK)

#### Step 1: Forwarder Adapter 생성 (추후 구현)
```python
# forwarder_adapters/maersk_adapter.py
class MAERSKAdapter(ForwarderAdapter):
    def parse_order_ref(self, ref: str) -> dict:
        """MAERSK specific order ref parsing"""
        pattern = r'MAE-(?P<mode>\w+)-(?P<number>\d+)'
        match = re.match(pattern, ref)
        if match:
            return match.groupdict()
        return {}
```

#### Step 2: Configuration 복사 및 수정
```bash
cp Rate/config_shpt_lanes.json Rate/config_maersk_lanes.json
# Edit config_maersk_lanes.json for MAERSK-specific routes
```

#### Step 3: Excel Schema 확인
```json
// excel_schema.json에서 MAERSK 필드 매핑 확인
"forwarder_specific_mappings": {
    "MAERSK": {
        "order_ref_column": "Booking Number",
        "masterdata_sheet": "Invoice"
    }
}
```

---

### Scenario 3: 신규 프로젝트 (예: ADNOC-XYZ)

#### Step 1: Configuration 복사
```bash
mkdir Rate/archives/2025-09-HVDC
cp Rate/config_*.json Rate/archives/2025-09-HVDC/

# 새 프로젝트용 설정 생성
cp Rate/config_metadata.json Rate/config_metadata_ADNOC_XYZ.json
```

#### Step 2: 프로젝트별 설정 수정

**`config_metadata_ADNOC_XYZ.json`:**
```json
{
    "project": "ADNOC_XYZ",
    "destinations": ["ADNOC_SITE_A", "ADNOC_SITE_B"],
    ...
}
```

**`config_shpt_lanes.json` 추가:**
```json
"ADNOC_ROUTE_1": {
    "lane_id": "ADNOC_01",
    "rate": 350.00,
    "route": "Jebel Ali Port → ADNOC SITE A",
    ...
}
```

---

## Configuration 관리

### Configuration 파일 구조

```
Rate/
├── config_metadata.json         # 메타데이터 (월, 프로젝트, 포워더)
├── config_template.json         # 변경 항목 템플릿
├── config_shpt_lanes.json       # Lane Map (운송 경로 요율)
├── config_contract_rates.json   # 계약 고정 요율
├── config_cost_guard_bands.json # COST-GUARD 밴드 정의
├── config_validation_rules.json # 검증 규칙
└── excel_schema.json            # Excel 구조 정의
```

### 월별 업데이트 체크리스트

- [ ] `config_metadata.json` → `applicable_period` 변경
- [ ] `config_metadata.json` → `fx_rates.USD_AED` 최신 환율로 업데이트
- [ ] `config_metadata.json` → `fx_rates.last_updated` 날짜 변경
- [ ] 인보이스 파일명 변경 (스크립트 또는 CLI 인자)
- [ ] 검증 실행 및 결과 확인
- [ ] 이전 월 configuration을 `archives/` 디렉토리로 백업

### 요율 업데이트 절차

#### 신규 Lane 추가
```json
// config_shpt_lanes.json
"NEW_ROUTE_ID": {
    "lane_id": "L99",
    "rate": 500.00,
    "route": "Port A → Destination B",
    "category": "Container",
    "port": "Port A",
    "destination": "Destination B",
    "unit": "per truck",
    "description": "New route description"
}
```

#### 고정 요율 수정
```json
// config_contract_rates.json -> fixed_fees
"DO_FEE_CONTAINER": {
    "rate": 150.00,  // 변경 시 이 값만 수정
    "unit": "per shipment",
    ...
}
```

---

## 결과 해석

### Validation Status

| Status | 의미 | 조치 |
|--------|------|------|
| **PASS** | 계약 요율 범위 내 | 승인 |
| **REVIEW_NEEDED** | 허용 오차 초과, 수동 검토 필요 | 담당자 확인 |
| **FAIL** | Ref Rate 없음 또는 심각한 오차 | 재협상 또는 정정 |

### COST-GUARD Band

| Band | Delta 범위 | 의미 |
|------|------------|------|
| **PASS** | 0% ~ ±3% | 계약 준수 |
| **REVIEW** | ±3% ~ ±10% | 경미한 초과 |
| **WARNING** | ±10% ~ ±15% | 주의 필요 |
| **CRITICAL** | ±15% 이상 | 긴급 검토 |

### Gate Score

**계산식:**
```
Gate Score = (ref_rate_found * 40) + (within_tolerance * 30) + (pdf_found * 30)
```

**기준:**
- **PASS**: Gate Score ≥ 75
- **FAIL**: Gate Score < 75

---

## 문제 해결

### Q1: "No contract rate found" 메시지가 많이 나옵니다

**원인:**
- Lane Map에 해당 경로가 등록되지 않음
- Normalization이 제대로 작동하지 않음

**해결:**
```bash
# 1. 실패한 항목의 경로 확인
python analyze_transportation_251014.py

# 2. config_shpt_lanes.json에 해당 경로 추가
# 3. 재검증
python validate_masterdata_with_config_251014.py
```

### Q2: PDF 매칭이 안 됩니다

**원인:**
- PDF 파일 경로 구조가 다름
- Order Ref. Number 형식이 다름

**해결:**
```bash
# PDF 매칭 디버깅
python debug_pdf_matching_251014.py

# 경로 정규화 로직 확인
# map_masterdata_to_pdf 메서드 수정
```

### Q3: Portal Fee 요율이 이상합니다

**원인:**
- 통화 변환 오류 (AED/USD 혼동)
- Configuration에 Portal Fee 미등록

**해결:**
```json
// config_contract_rates.json -> portal_fees_aed
"APPOINTMENT_FEE": {
    "rate_aed": 27.00,
    "rate_usd": 7.35,  // 확인
    "tolerance_percent": 0.5
}
```

### Q4: Transport Mode 인식이 잘못되었습니다

**원인:**
- SEPT 시트의 Mode 정보 미활용
- Order Ref 패턴 매칭 실패

**해결:**
1. SEPT 시트 존재 여부 확인
2. `_identify_transport_mode` 메서드 로직 확인
3. Order Ref 패턴 수정

---

## 고급 사용법

### 커스텀 Tolerance 적용
```python
# config_validation_rules.json
{
    "tolerance_by_category": {
        "DOC": 0.0,      // DO FEE: 정확히 일치
        "CUS": 2.0,      // Customs: ±2%
        "TRN": 3.0,      // Transportation: ±3%
        "PortalFee": 0.5 // Portal Fee: ±0.5%
    }
}
```

### Batch Processing (여러 인보이스 동시 처리)
```python
# batch_validate.py (추후 구현)
invoices = [
    "SEPT_2025.xlsm",
    "OCT_2025.xlsm",
    "NOV_2025.xlsm"
]

for invoice in invoices:
    validator = MasterDataValidator()
    results = validator.validate(invoice)
    generate_report(results, invoice)
```

---

## 시스템 구조

### 핵심 컴포넌트

```
01_DSV_SHPT/
├── Core_Systems/
│   ├── validate_masterdata_with_config_251014.py  # 메인 검증 로직
│   ├── invoice_pdf_integration.py                 # PDF 통합
│   └── generate_final_report_pandas_251014.py     # 보고서 생성
├── 00_Shared/
│   ├── config_manager.py                          # Configuration 관리자
│   └── pdf_integration/                           # PDF 파싱
└── Rate/
    ├── config_metadata.json                       # 메타데이터
    ├── config_shpt_lanes.json                     # Lane Map
    ├── config_contract_rates.json                 # 계약 요율
    ├── config_cost_guard_bands.json               # COST-GUARD
    └── excel_schema.json                          # Excel 스키마
```

### 데이터 흐름

```
[Excel Invoice]
      ↓
[MasterData Sheet 로드]
      ↓
[각 Item별 검증]
      ├─→ Charge Group 분류
      ├─→ Ref Rate 조회 (Config/PDF)
      ├─→ Delta % 계산
      ├─→ COST-GUARD 밴드 결정
      ├─→ PDF 매칭
      ├─→ Gate Score 계산
      └─→ Validation Status 결정
      ↓
[Excel 보고서 생성]
      ├─→ MasterData_Validated (원본 + 검증 결과)
      ├─→ Validation_Summary (통계)
      └─→ VBA_vs_Python (비교)
```

---

## 버전 히스토리

### v1.0.0 (2025-10-14)
- 초기 USER_GUIDE 작성
- TRANSPORTATION Lane Map 통합 완료
- 재사용성 검증 체계 수립

---

## 문의 및 지원

**기술 지원**: MACHO-GPT v3.4-mini
**문서 위치**: `01_DSV_SHPT/Documentation/`
**추가 가이드**:
- `CONFIGURATION_GUIDE.md` (설정 상세 가이드)
- `TROUBLESHOOTING.md` (문제 해결 가이드)
- `API_REFERENCE.md` (개발자용 API 문서)

