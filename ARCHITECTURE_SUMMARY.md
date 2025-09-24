# 🏗️ Invoice Audit System Architecture Summary

## 📋 시스템 개요

### 1. 기존 시스템 (변경 없음)
- **audit_runner_enhanced.py**: 기존 송장 감사 시스템
- **joiners_enhanced.py**: 데이터 조인 및 분류 로직
- **rules_enhanced.py**: 검증 규칙 및 밴드 시스템
- **AUDIT LOGIC.MD**: 핵심 감사 로직 명세서

### 2. 새로 추가된 DOMESTIC INVOICE 시스템

#### 2.1 domestic_invoice_system.py
- **목적**: DOMESTIC INVOICE 내륙 운송 전용 감사 시스템
- **특징**:
  - 내륙 운송 전용 Lane Map (DSV Yard→MIRFA, DSV Yard→SHUWEIHAT 등)
  - COST-GUARD 밴드 시스템 (PASS/WARN/HIGH/CRITICAL)
  - FX 고정 환율 (1 USD = 3.6725 AED)
  - 내륙 운송 계약 정보 (HVDC-ITC-2025-001)

#### 2.2 enhanced_domestic_system.py
- **목적**: 개선된 DOMESTIC INVOICE 시스템 (데이터 추출 문제 해결)
- **개선사항**:
  - 다양한 헤더 패턴 인식
  - 정확한 송장 항목 추출
  - 강화된 데이터 검증
  - 상세한 로깅 및 오류 처리

#### 2.3 updated_architecture_system.py
- **목적**: 표준 보고서 기반 통합 아키텍처 시스템
- **특징**:
  - 표준 보고서 형식 (Executive Summary, Contract Map, Line Items 등)
  - 다중 요율 테이블 지원 (Inland Trucking, Container, Air, Bulk)
  - 정규화 맵 시스템
  - 예외 등록부 및 KPI 추적

## 🔧 시스템 아키텍처

### 1. 데이터 흐름
```
Excel 파일 → 시트별 파싱 → 송장 항목 추출 → 데이터 정규화 → 표준 요율 조회 → Delta % 계산 → COST-GUARD 밴드 결정 → 검증 결과 생성 → 보고서 출력
```

### 2. 핵심 컴포넌트

#### 2.1 Lane Map 시스템
```json
{
  "DSV_YD_MIRFA": {"lane_id": "L38", "rate": 420.00, "route": "DSV Yard→MIRFA"},
  "DSV_YD_SHUWEIHAT": {"lane_id": "L44", "rate": 600.00, "route": "DSV Yard→SHUWEIHAT"},
  "MOSB_DSV_YD": {"lane_id": "L33", "rate": 200.00, "route": "MOSB→DSV Yard"},
  "KP_DSV_YD": {"lane_id": "L01", "rate": 252.00, "route": "Khalifa Port→Storage Yard"}
}
```

#### 2.2 COST-GUARD 밴드 시스템
```python
cost_guard_bands = {
    "PASS": {"max_delta": 2.00, "description": "≤2.00%"},
    "WARN": {"max_delta": 5.00, "description": "2.01-5.00%"},
    "HIGH": {"max_delta": 10.00, "description": "5.01-10.00%"},
    "CRITICAL": {"max_delta": float('inf'), "description": ">10.00%"}
}
```

#### 2.3 정규화 맵 시스템
```python
normalization_map = {
    "port": {"Khalifa Port": "KP", "Abu Dhabi Airport": "AUH"},
    "destination": {"MIRFA SITE": "MIRFA", "SHUWEIHAT Site": "SHUWEIHAT"},
    "unit": {"per truck": "per truck", "per RT": "per truck"}
}
```

## 📊 표준 보고서 구조

### 1. Executive Summary
- Reference locked: Inland Trucking 표준요율 + O/D Lane Map + Δ% 밴드
- FX & bands: 1 USD = 3.6725 AED, Δ≤2.00% PASS
- Lane medians: 승인 레인 중앙값을 표준소스로 사용
- Compliance: Incoterms 2020 적용 (DDP Site-delivery)

### 2. Contract Map
- Contract No: HVDC-ITC-2025-001
- Scope: DOMESTIC INVOICE - Inland Transportation Only
- Incoterm: DDP (assumed)
- Currency/FX: USD; 1.00 USD = 3.6725 AED
- Validity: 2025-01-01 ~ 2025-12-31
- Parties: Samsung C&T / ADNOC L&S / DSV (3PL)

### 3. Line Item Specification
- TRK-KP-DSV: Transportation (Khalifa Port→Storage Yard) - 252.00 USD
- TRK-DSV-MIR: Transportation (DSV Yard→MIRFA, Flatbed) - 420.00 USD
- TRK-DSV-SHU: Transportation (DSV Yard→SHUWEIHAT, Flatbed) - 600.00 USD
- TRK-MOSB-DSV: Transportation (MOSB→DSV Yard, Flatbed) - 200.00 USD

### 4. Rate Source Matrix
- KP→Storage Yard: RateTable(Container) - 2025-01-01
- DSV→MIRFA Flatbed: ApprovedLaneMap L38 median - 2025-08-19
- DSV→SHU Flatbed: ApprovedLaneMap L44 median - 2025-08-19

### 5. Validation Rulebook
- R-001: 금액계산 (ExtAmount = ROUND(UnitRate*Qty,2))
- R-002: 요율출처 (JOIN key={Category,Port,Destination,Unit})
- R-003: Δ% 밴드 (Δ% = (Draft−Std)/Std → PASS/WARN/HIGH/CRITICAL)
- R-004: 단위정합 (per RT↔per truck 불일치 시 변환금지)
- R-005: FX고정 (통화는 USD 유지, 병기 시 USD×3.6725=AED)

## 🎯 시스템 특징

### 1. 표준 보고서 기반
- **자동화 설계·검증용 표준 보고서** 형식 준수
- 수치 2자리, USD 기준, FX 고정
- 가정/불확실 데이터는 "가정:"으로 명시

### 2. 내륙 운송 전용
- **DOMESTIC INVOICE** 범위로 제한
- TRK 카테고리 중심
- Lane Map 기반 요율 조회

### 3. 다중 검증 레이어
- RateTable → LaneMap → COST-GUARD 3-layer 검증
- 정규화 맵을 통한 데이터 표준화
- 예외 등록부를 통한 특수 케이스 관리

### 4. 감사 추적성
- Δ·키·레인ID·소스파일을 함께 기록
- 검증 타임스탬프 및 시스템 유형 표시
- 상세한 로깅 및 오류 처리

## 📁 파일 구조

```
invoice-audit/
├── domestic_invoice_system.py          # DOMESTIC INVOICE 기본 시스템
├── enhanced_domestic_system.py         # 개선된 DOMESTIC INVOICE 시스템
├── updated_architecture_system.py      # 표준 보고서 기반 통합 시스템
├── audit_runner_enhanced.py            # 기존 송장 감사 시스템 (변경 없음)
├── joiners_enhanced.py                 # 기존 조인 로직 (변경 없음)
├── rules_enhanced.py                   # 기존 규칙 시스템 (변경 없음)
├── ref/
│   └── inland_trucking_rates.json      # 내륙 운송 요율 테이블
├── out/
│   ├── domestic_invoice_audit_report.json
│   ├── enhanced_domestic_invoice_audit_report.json
│   └── updated_audit_report.json
└── ARCHITECTURE_SUMMARY.md             # 이 파일
```

## 🚀 사용법

### 1. DOMESTIC INVOICE 기본 시스템
```bash
python domestic_invoice_system.py
```

### 2. 개선된 DOMESTIC INVOICE 시스템
```bash
python enhanced_domestic_system.py
```

### 3. 표준 보고서 기반 통합 시스템
```bash
python updated_architecture_system.py
```

## 📈 향후 개선 방향

### 1. 데이터 추출 개선
- 더 정확한 송장 항목 인식
- 다양한 Excel 형식 지원
- OCR 통합 고려

### 2. 보고서 기능 확장
- 실시간 대시보드
- 시각화 차트
- 자동 알림 시스템

### 3. 통합 시스템 구축
- 기존 시스템과의 통합
- 웹 인터페이스 개발
- API 서비스 제공

---

**생성일**: 2025-01-25  
**버전**: v1.0  
**시스템 유형**: DOMESTIC INVOICE - Inland Transportation  
**기반**: 표준 보고서 기반 자동화 설계·검증 시스템
