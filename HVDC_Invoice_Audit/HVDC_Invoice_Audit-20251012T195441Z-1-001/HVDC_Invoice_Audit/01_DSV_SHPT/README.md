# DSV SHPT Invoice Audit System

**System Type**: Shipment Invoice Processing (Sea + Air)  
**Contract No**: HVDC-SHPT-2025-001  
**Last Updated**: 2025-10-12

---

## 개요

Samsung C&T HVDC Project의 DSV Shipment 인보이스 자동 검증 시스템입니다.

해상 운송(SCT) 및 항공 운송(HE/SIM) 인보이스를 처리하며, Portal Fee 특별 검증, Gate 검증, 증빙문서 매핑 기능을 제공합니다.

---

## 주요 기능

### ✅ 완료된 기능
- **102개 항목 자동 검증** (9월 2025 인보이스)
- **Portal Fee 특별 검증** (±0.5% 엄격한 허용 오차)
- **Gate 검증 시스템** (평균 78.8점)
- **93개 증빙문서 자동 매핑** (BOE, DO, DN)
- **Pass Rate 34.3%** (35/102 PASS)
- **처리 속도 <2초** (목표 10초 대비 5배 빠름)

### 🎯 검증 범위
- **해상 운송 (SCT)**: 7개 시트, 45개 항목
- **항공 운송 (HE/SIM)**: 21개 시트, 57개 항목
- **Total**: 28개 시트, 102개 항목, $21,402.20

---

## 빠른 시작

### 1. 시스템 실행

```bash
cd "C:\cursor mcp\HVDC_Invoice_Audit\01_DSV_SHPT\Core_Systems"
python shpt_sept_2025_enhanced_audit.py
```

### 2. 결과 확인

결과 파일은 `Results/Sept_2025/` 폴더에 생성됩니다:
- **JSON**: `Results/Sept_2025/JSON/shpt_sept_2025_enhanced_result_*.json`
- **CSV**: `Results/Sept_2025/CSV/shpt_sept_2025_enhanced_result_*.csv`
- **Reports**: `Results/Sept_2025/Reports/shpt_sept_2025_enhanced_summary_*.txt`

---

## 폴더 구조

```
01_DSV_SHPT/
├── Core_Systems/         # 핵심 감사 시스템
│   ├── shpt_audit_system.py                      # 메인 시스템 (1003줄)
│   ├── shpt_sept_2025_enhanced_audit.py          # Enhanced 버전 (690줄)
│   └── run_shpt_sept2025.py                      # 실행 스크립트
│
├── Results/              # 검증 결과
│   └── Sept_2025/
│       ├── JSON/         # JSON 결과 파일
│       ├── CSV/          # CSV 결과 파일
│       ├── Reports/      # 요약 보고서
│       └── Logs/         # 실행 로그
│
├── Data/                 # 인보이스 및 증빙문서
│   └── DSV 202509/
│       ├── SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm
│       ├── SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_rev.xlsm
│       └── SCNT Import (Sept 2025) - Supporting Documents/  (57 PDFs)
│
├── Documentation/        # 시스템 문서
│   ├── SHPT_SYSTEM_UPDATE_SUMMARY.md
│   ├── SYSTEM_ARCHITECTURE_FINAL.md
│   └── Technical/
│
├── Utilities/            # 유틸리티
│   ├── joiners_enhanced.py
│   ├── rules_enhanced.py
│   └── sheet_range_analyzer.py
│
└── Legacy/               # 레거시 시스템 (참조용)
    ├── audit_runner.py
    ├── audit_runner_improved.py
    ├── audit_runner_enhanced.py
    └── advanced_audit_runner.py
```

---

## 최신 결과 (2025-10-12 12:11:43)

### 전체 통계
- **파일**: SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm
- **총 시트**: 28개
- **총 항목**: 102개
- **총 금액**: $21,402.20 USD

### 검증 결과
- ✅ **PASS**: 35개 (34.3%)
- ⚠️ **REVIEW**: 66개 (64.7%)
- ❌ **FAIL**: 1개 (1.0%)

### Charge Group 분석
- **Contract**: 64개 (62.7%)
- **AtCost**: 14개 (13.7%)
- **PortalFee**: 4개 (3.9%) ← Enhanced 기능
- **Other**: 20개 (19.6%)

### Gate 검증 결과
- **Gate PASS**: 35개 (34.3%)
- **평균 Gate Score**: 78.8/100
- **Gate-01**: 증빙문서 세트 검증 (93개 PDF 매핑)
- **Gate-07**: 금액 일치 검증

### Portal Fee 검증 (4개)
| 항목 | 청구액 | 기준액 | Delta | 상태 |
|------|--------|--------|-------|------|
| APPOINTMENT FEE | $7.35 | $7.35 | 0.03% | ✅ PASS |
| DPC FEE | $9.53 | $9.53 | 0.00% | ✅ PASS |
| TRUCK APPOINTMENT FEE | $7.35 | $7.35 | 0.03% | ✅ PASS |
| DOCUMENT PROCESSING FEE | $20.01 | $9.53 | 109.97% | ❌ FAIL |

---

## 시스템 특징

### Portal Fee 특별 검증
- **허용 오차**: ±0.5% (일반 항목 3% 대비 엄격)
- **AED 수식 파싱**: `=27/3.6725` 형태 자동 인식
- **고정 요율 매핑**: APPOINTMENT=27 AED, DPC=35 AED
- **검증 항목**: 4개 (PASS 3개, FAIL 1개)

### Gate 검증 시스템
- **Gate-01**: 증빙문서 세트 검증 (BOE, DO, DN 필수)
- **Gate-07**: 금액 일치 검증 (unit_rate × quantity = total)
- **점수 산출**: 각 Gate별 100점 만점, 평균 78.8점

### 증빙문서 매핑
- **총 PDF**: 93개 (BOE 26, DO 23, DN 44)
- **자동 매핑**: Shipment ID 패턴 인식 (SCT-0126, HE-0471 등)
- **연결율**: 59.8% (61개 항목에 증빙문서 연결)

---

## 기술 스펙

### 시스템 정보
- **Language**: Python 3.8+
- **Dependencies**: pandas, openpyxl, pathlib
- **처리 속도**: 68-120 items/sec
- **메모리**: <100MB

### 검증 규칙
- **COST-GUARD 밴드**: PASS (≤2%), WARN (2-5%), HIGH (5-10%), CRITICAL (>10%)
- **FX 환율**: 1 USD = 3.6725 AED (고정)
- **Portal Fee 허용 오차**: ±0.5%
- **일반 항목 허용 오차**: ±3%

---

## 문제 해결

### 자주 발생하는 문제

**Q: "FileNotFoundError: Excel file not found"**  
A: `Data/DSV 202509/` 폴더에 인보이스 파일이 있는지 확인하세요.

**Q: "증빙문서가 연결되지 않음"**  
A: PDF 파일명이 `HVDC-ADOPT-{ShipmentID}_{DocType}.pdf` 형식인지 확인하세요.

**Q: "Portal Fee FAIL 발생"**  
A: AED 수식 컬럼(FORMULA)에 `=금액/3.6725` 형태로 입력되어 있는지 확인하세요.

---

## 업데이트 이력

### v2.0 (2025-10-12)
- ✅ Enhanced 시스템 통합
- ✅ Portal Fee 특별 검증 추가 (±0.5%)
- ✅ Gate 검증 시스템 추가
- ✅ 증빙문서 자동 매핑 완성
- ✅ 9월 2025 인보이스 검증 완료

### v1.0 (2024-09-24)
- ✅ 항공 운송 지원 추가
- ✅ SIM-0092 기준 검증 완료
- ✅ Lane Map 확장 (해상 + 항공)

---

## 연락처

**Project**: Samsung C&T HVDC  
**System**: DSV SHPT Invoice Audit  
**Support**: AI Assistant

---

**시스템 상태**: ✅ Production Ready  
**마지막 검증**: 2025-10-12 12:11:43  
**총 항목**: 102개 | **PASS**: 35개 (34.3%)

