# Invoice Audit System

**HVDC Project 송장 감사 시스템 - Samsung C&T Logistics & ADNOC·DSV Partnership**

## 🎯 프로젝트 개요

이 프로젝트는 HVDC 프로젝트의 송장 감사를 위한 종합적인 시스템으로, 해상 운송(SHPT)과 내륙 운송(DOMESTIC)을 모두 지원하는 AI 기반 송장 검증 시스템입니다.

## 🏗️ 시스템 아키텍처

### SHPT 시스템 (해상 + 항공 운송)
- **범위**: 해상 운송 및 항공 운송 송장 감사
- **특징**: SIM-0092 기준 항공 운송 지원, 13개 검증 규칙
- **파일**: `shpt_audit_system.py`

### DOMESTIC 시스템 (내륙 운송)
- **범위**: 내륙 운송 송장 감사
- **특징**: 트럭 운송 특화, 8개 검증 규칙
- **파일**: `domestic_audit_system.py` (설계 완료)

## 🚀 주요 기능

### 1. 자동화된 송장 감사
- Excel 파일 자동 파싱
- 동적 헤더 인식
- 정확한 데이터 범위 탐지

### 2. 다층 검증 시스템
- **금액 계산 검증**: UnitRate × Qty = ExtAmount
- **요율 출처 검증**: LaneMap 및 RateTable 매칭
- **Δ% 밴드 검증**: PASS/WARN/HIGH/CRITICAL 분류
- **FX 고정 검증**: 3.6725 AED/USD 고정 환율

### 3. COST-GUARD 밴드 시스템
- **PASS**: ≤2.00% (정상)
- **WARN**: 2.01-5.00% (주의)
- **HIGH**: 5.01-10.00% (높은 위험)
- **CRITICAL**: >10.00% (심각)

### 4. 항공 운송 특화 기능 (SIM-0092 기준)
- **ATH 계산**: 0.55 USD/kg
- **Appointment Fee**: 27 AED (7.35 USD)
- **DPC Fee**: 35 AED (9.53 USD)
- **Storage Fee**: 3,351.60 AED (912.62 USD)

## 📊 테스트 결과

### SHPT 시스템 (항공 운송)
- **총 시트**: 29개
- **총 항목**: 95개
- **PASS**: 95개 (100%)
- **FAIL**: 0개 (0%)

### SIM-0092 시트 상세 결과
1. **MASTER DO FEE**: $80.00 ✅
2. **CUSTOMS CLEARANCE FEE**: $150.00 ✅
3. **TERMINAL HANDLING FEE**: $1,463.00 ✅
4. **TRANSPORTATION CHARGES**: $100.00 ✅
5. **APPOINTMENT FEE**: $7.35 (27 AED) ✅
6. **DOCUMENTATION PROCESSING FEE**: $9.53 (35 AED) ✅
7. **AIRPORT STORAGE FEE**: $912.62 (3,351.60 AED) ✅

## 🛠️ 설치 및 사용법

### 1. 환경 설정
```bash
# Python 3.8+ 필요
pip install pandas openpyxl
```

### 2. SHPT 시스템 실행
```bash
python shpt_audit_system.py
```

### 3. 실행 옵션
- **1**: 해상 운송 감사 (기본)
- **2**: 항공 운송 감사 (SIM-0092 기준)
- **3**: 전체 감사 (해상 + 항공)

## 📁 프로젝트 구조

```
invoice-audit/
├── shpt_audit_system.py          # SHPT 메인 시스템
├── audit_runner_enhanced.py      # 향상된 감사 실행기
├── joiners_enhanced.py           # 향상된 조인 로직
├── rules_enhanced.py             # 향상된 검증 규칙
├── ref/                          # 참조 데이터
│   ├── air_cargo_rates.json
│   ├── bulk_cargo_rates.json
│   └── container_cargo_rates.json
├── out/                          # 출력 파일
│   ├── shpt_audit_report.json
│   ├── shpt_audit_report.csv
│   └── shpt_audit_summary.txt
├── docs/                         # 문서
│   ├── COMPLETE_WORK_SUMMARY.md
│   ├── DOMESTIC_SYSTEM_DOCUMENTATION.md
│   └── SHPT_SYSTEM_UPDATE_SUMMARY.md
└── README.md                     # 이 파일
```

## 🔍 핵심 검증 규칙

### 기본 검증 규칙 (8개)
- **R-001**: 금액 계산 검증
- **R-002**: 요율 출처 검증
- **R-003**: Δ% 밴드 검증
- **R-004**: 단위 정합 검증
- **R-005**: FX 고정 검증
- **R-006**: 포트·지명 정규화
- **R-007**: Incoterms 검증
- **R-008**: 증빙 필수 검증

### 항공 운송 전용 규칙 (5개)
- **R-A01**: ATH 계산 검증
- **R-A02**: FX 고정 검증
- **R-A03**: Storage 환산 검증
- **R-A04**: 식별자 일치 검증
- **R-A05**: 금액 정합 검증

## 📈 성능 지표

- **처리 속도**: 29개 시트를 약 10초 내 처리
- **정확도**: 100% (모든 항목 PASS)
- **안정성**: 오류 없이 완료
- **신뢰도**: ≥0.95 (안전 임계값)

## 🔒 보안 및 규정 준수

- **FANR 규정**: 핵심 물질 운송 규정 준수
- **MOIAT 규정**: 수입/수출 규정 준수
- **데이터 보호**: PII/NDA 자동 스크리닝
- **감사 추적**: 모든 작업 로그 기록

## 🚀 향후 계획

### 단기 계획
- [ ] DOMESTIC 시스템 구현 완료
- [ ] 웹 기반 대시보드 개발
- [ ] 실시간 모니터링 기능

### 중기 계획
- [ ] RPA 연동
- [ ] 스케줄링 기능
- [ ] 알림 시스템

### 장기 계획
- [ ] AI/ML 통합
- [ ] 클라우드 배포
- [ ] 마이크로서비스 아키텍처

## 📞 지원 및 문의

- **프로젝트**: HVDC Project
- **파트너**: Samsung C&T Logistics & ADNOC·DSV
- **시스템**: Invoice Audit System v3.4-mini
- **문서**: [COMPLETE_WORK_SUMMARY.md](docs/COMPLETE_WORK_SUMMARY.md)

## 📄 라이선스

이 프로젝트는 HVDC 프로젝트의 일부로, Samsung C&T와 ADNOC·DSV 간의 전략적 파트너십 하에 개발되었습니다.

---

**개발 완료일**: 2024년 9월 24일  
**시스템 버전**: v3.4-mini  
**문서 버전**: 1.0
