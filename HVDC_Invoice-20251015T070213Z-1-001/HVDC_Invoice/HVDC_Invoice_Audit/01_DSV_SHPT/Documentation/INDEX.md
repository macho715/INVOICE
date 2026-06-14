# 📚 HVDC Invoice Audit - 문서 인덱스

**최종 업데이트**: 2025-10-17  
**프로젝트**: HVDC ADOPT - DSV Shipment Invoice Validation & Data Consolidation

---

## 📖 사용자 가이드

### 핵심 가이드

| 문서 | 설명 | 대상 |
|------|------|------|
| **[USER_GUIDE.md](USER_GUIDE.md)** | 전체 시스템 사용자 가이드 | 모든 사용자 |
| **[GUIDE_Monthly_Summary.md](../GUIDE_Monthly_Summary.md)** | Monthly summary sheets consolidation guide (406 rows, $1.4M) | Financial analysts, Report writers |
| **[GUIDE_Individual_Invoices.md](../GUIDE_Individual_Invoices.md)** | Individual invoice sheets consolidation guide (2,166 rows, 407+ sheets) | Cost analysts, Auditors |
| **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** | 설정 파일 관리 가이드 | 시스템 관리자 |

---

## 📊 데이터 통합 보고서

### 월별 Summary 시트

| 문서 | 내용 |
|------|------|
| **[REPORT_Monthly_Consolidation.md](../REPORT_Monthly_Consolidation.md)** | Consolidation system technical report |
| **[REPORT_Monthly_Integration.md](../REPORT_Monthly_Integration.md)** | Final execution results and data analysis |
| **[REPORT_Monthly_Verification.md](../REPORT_Monthly_Verification.md)** | 15 sheets verification report |
| **[REPORT_Feb2025_Structure.md](../REPORT_Feb2025_Structure.md)** | FEB 2025 sheet structure analysis |

### 개별 인보이스 시트

| 문서 | 내용 |
|------|------|
| **[REPORT_Individual_Verification.md](../REPORT_Individual_Verification.md)** | Individual invoice verification final report |
| **[REPORT_Header_Detection.md](../REPORT_Header_Detection.md)** | Robust Header Detection patch report |
| **[REPORT_RateSource_Fix.md](../REPORT_RateSource_Fix.md)** | RATE SOURCE data fix report |
| **[Core_Systems/INVOICE_STRUCTURE_VERIFICATION_REPORT.md](../Core_Systems/INVOICE_STRUCTURE_VERIFICATION_REPORT.md)** | 15개 파일 407+ 시트 구조 검증 보고서 |

---

## 🎯 최종 요약 문서

| 문서 | 내용 |
|------|------|
| **[SUMMARY_Project_Complete.md](../SUMMARY_Project_Complete.md)** | Project completion final summary |
| **[HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md](../HVDC_INVOICE_AUDIT_COMPLETE_MASTER_REPORT.md)** | 전체 시스템 마스터 보고서 |

---

## 🔧 시스템 아키텍처

| 문서 | 내용 |
|------|------|
| **[SYSTEM_ARCHITECTURE_FINAL.md](SYSTEM_ARCHITECTURE_FINAL.md)** | 시스템 전체 아키텍처 |

---

## 📈 데이터 통합 시스템

### 개요

HVDC Invoice Audit 시스템은 **2가지 레벨의 데이터 통합**을 지원합니다:

#### 1. 월별 Summary 시트 통합

**목적**: 인보이스 요약 데이터 (GRAND TOTAL 포함)

**특징**:
- 1 row = 1 invoice
- 406 rows (15개 월별 시트)
- GRAND TOTAL: $1,420,529.90
- 용도: 월별 트렌드, 재무 보고

**Guide**: [GUIDE_Monthly_Summary.md](../GUIDE_Monthly_Summary.md)

**실행**:
```bash
cd Core_Systems
python run_monthly_consolidation.py
```

---

#### 2. 개별 인보이스 시트 통합

**목적**: 상세 라인 항목 데이터 (RATE SOURCE, DESCRIPTION, RATE 포함)

**특징**:
- 1 row = 1 item (Master DO, Customs, THC, ...)
- 2,166 rows (407+ 개별 시트)
- RATE SOURCE 99.9%
- 용도: 비용 구조 분석, 상세 검증

**Guide**: [GUIDE_Individual_Invoices.md](../GUIDE_Individual_Invoices.md)

**실행**:
```bash
cd Core_Systems
python run_individual_consolidation.py
```

---

### 데이터 레벨 비교

| 항목 | 월별 Summary | 개별 인보이스 |
|------|-------------|--------------|
| **데이터 레벨** | 요약 | 상세 |
| **행 수** | 406 rows | 2,166 rows |
| **1 row** | 1 invoice | 1 item |
| **주요 컬럼** | GRAND TOTAL | RATE SOURCE, DESCRIPTION, RATE |
| **비율** | - | 5.3 라인/인보이스 |

---

## 🗂️ 문서 카테고리

### 사용자 가이드 (4개)
- USER_GUIDE.md
- 월별 Summary 시트 가이드
- 개별 인보이스 시트 가이드
- CONFIGURATION_GUIDE.md

### 기술 보고서 (10+ 개)
- 월별 시트 통합 (4개)
- 개별 시트 통합 (4개)
- 최종 요약 (2개)

### 시스템 문서 (2개)
- SYSTEM_ARCHITECTURE_FINAL.md
- 00_DOCUMENTATION_INDEX.md (본 문서)

---

## 🚀 빠른 시작

### 1. 시스템 이해

1. [USER_GUIDE.md](USER_GUIDE.md) - 전체 시스템 개요
2. [WORK_COMPLETION_FINAL_SUMMARY.md](../WORK_COMPLETION_FINAL_SUMMARY.md) - 작업 완료 요약

### 2. 데이터 통합

**월별 요약이 필요하면**:
- [월별 Summary 시트 가이드](../MONTH_SUMMARY_SHEETS_GUIDE.md) 참조

**상세 분석이 필요하면**:
- [개별 인보이스 시트 가이드](../INDIVIDUAL_INVOICE_SHEETS_GUIDE.md) 참조

### 3. 문제 해결

각 가이드 문서의 "문제 해결" 섹션 참조:
- 월별 시트: [7. 문제 해결](../MONTH_SUMMARY_SHEETS_GUIDE.md#7-문제-해결)
- 개별 시트: [7. 문제 해결](../INDIVIDUAL_INVOICE_SHEETS_GUIDE.md#7-문제-해결)

---

## 📞 문의

### 기술 지원

- **이메일**: hvdc-support@example.com
- **담당자**: HVDC Invoice Audit Team

### 긴급 문의

- **긴급 핫라인**: +82-XXX-XXXX-XXXX
- **업무 시간**: 월-금 09:00-18:00 (KST)

---

**문서 인덱스 버전**: 1.0  
**최종 업데이트**: 2025-10-17  
**작성자**: HVDC Invoice Audit Team

---

## 변경 이력

| 일자 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-10-17 | 1.0 | 최초 작성, 2개 가이드 문서 추가 |
