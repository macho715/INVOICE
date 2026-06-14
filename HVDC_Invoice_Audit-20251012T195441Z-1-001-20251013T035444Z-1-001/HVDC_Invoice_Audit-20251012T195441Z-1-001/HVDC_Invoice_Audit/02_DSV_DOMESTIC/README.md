# DSV DOMESTIC Invoice Audit System

**System Type**: Inland Transportation Invoice Processing  
**Contract No**: HVDC-ITC-2025-001  
**Status**: ✅ Ready (2025-10-12)

---

## 개요

Samsung C&T HVDC Project의 DSV Domestic (내륙 운송) 인보이스 자동 검증 시스템입니다.

Khalifa Port, Abu Dhabi Airport에서 MIRFA, SHUWEIHAT, DSV Yard로의 내륙 운송 인보이스를 처리합니다.

---

## 주요 기능

### ✅ 구현 완료
- **내륙 운송 라인 검증** (Port → Destination)
- **Lane Map 기반 요율 검증** (Exact Match → Similarity ≥0.60)
- **COST-GUARD 밴드 적용** (PASS/WARN/HIGH/CRITICAL)
- **트럭 운송비 자동 계산** (Δ% 자동 산출)
- **정규화 시스템** (O/D/Vehicle/Unit Canonical 매핑)
- **이상치 탐지** (Per-km Robust Z-score)
- **PRISM 증명** (recap.card + proof.artifact SHA256)

### 🎯 검증 범위
- **출발지**: Khalifa Port, Abu Dhabi Airport, DSV Mussafah Yard, MOSB
- **도착지**: MIRFA SITE, SHUWEIHAT Site, DSV Yard, Mina Zayed
- **단위**: per truck, per RT (Round Trip)
- **통화**: USD 기준 (AED 고정환율 3.6725)

---

## 폴더 구조

```
02_DSV_DOMESTIC/
├── Core_Systems/         # 핵심 감사 시스템 ✅
│   ├── domestic_audit_system.py          (577줄, 메인 검증 로직)
│   ├── domestic_sept_2025_audit.py       (9월 실행 래퍼)
│   └── run_domestic_sept2025.py          (간단 CLI)
│
├── Results/              # 검증 결과 ✅
│   └── Sept_2025/
│       ├── JSON/domestic_sept_2025_result_{timestamp}.json
│       ├── CSV/domestic_sept_2025_result_{timestamp}.csv
│       ├── Reports/DOMESTIC_SEPT_2025_FINAL_REPORT.md
│       └── Logs/domestic_audit_{timestamp}.log
│
├── Data/                 # 내륙 운송 인보이스
│   └── DSV 202509/
│       ├── SCNT HVDC DRAFT INVOICE FOR DOMESTIC DELIVERY SEPTEMBER 2025.xlsx
│       └── SCNT Domestic (Sept 2025) - Supporting Documents/  (36 PDFs)
│
├── Documentation/        # 시스템 문서
│   ├── DOMESTIC_SYSTEM_DOCUMENTATION.md
│   └── Technical/
│       ├── Lane_Map.md
│       └── Rate_Validation.md
│
├── DOMESTIC_with_distances.xlsx  # 참조 레인 데이터 ✅
└── README.md             # 본 문서
```

---

## Lane Map (내륙 운송)

### 주요 운송 구간

| Lane ID | Route | Rate (USD) | Unit |
|---------|-------|------------|------|
| D01 | Khalifa Port → DSV Yard | 252.00 | per truck |
| D02 | DSV Yard → MIRFA | 420.00 | per truck |
| D03 | DSV Yard → SHUWEIHAT | 600.00 | per truck |
| D04 | Mussafah → DSV Yard | 200.00 | per truck |
| D05 | AUH Airport → DSV Mussafah | 100.00 | per truck |

---

## SHPT vs DOMESTIC 차이점

| 구분 | SHPT | DOMESTIC |
|------|------|----------|
| **범위** | Shipment (해상+항공) | Inland Transportation |
| **계약번호** | HVDC-SHPT-2025-001 | HVDC-ITC-2025-001 |
| **Incoterm** | FOB (assumed) | DDP (assumed) |
| **검증규칙** | 8개 (R-001~R-008) | 5개 (R-001~R-005) |
| **주요 문서** | BOE, DO, DN | DN (Delivery Note) |
| **특별 검증** | Portal Fee (±0.5%) | Lane Rate 매칭 |

---

## 🚀 빠른 시작

### 1. 시스템 실행

```powershell
cd "C:\cursor mcp\HVDC_Invoice_Audit\02_DSV_DOMESTIC\Core_Systems"
python domestic_sept_2025_audit.py
```

**또는 간단 실행기:**

```powershell
python run_domestic_sept2025.py
```

### 2. 예상 출력

```
=== recap.card ===
P:: invoice-validate · join-ref · cost-guard
R:: Δ% bands ≤2/5/10 · ±3% contract · FX USD=3.6725AED
I:: {total:8, pass:5, warn:0, high:1, critical:2}
S:: normalize→join(exact→sim≥0.60)→score→decide→export
M:: {result.table, recap.card, proof.artifact.json}

✅ 감사 완료!
총 8개 항목 처리 (1.35초)
```

### 3. 결과 확인

```powershell
# 최종 보고서
cat Results/Sept_2025/Reports/DOMESTIC_SEPT_2025_FINAL_REPORT.md

# CSV 결과
Import-Csv Results/Sept_2025/CSV/domestic_sept_2025_result_*.csv | Out-GridView

# Excel 결과 (자세한 분석)
Results/Sept_2025/domestic_sept_2025_result_*.xlsx
```

---

## 개발 로드맵

### Phase 1: 기본 시스템 구축 ✅
- [x] `domestic_audit_system.py` 생성 (577줄)
- [x] Lane Map 정의 및 구현
- [x] 기본 검증 로직 구현
- [x] COST-GUARD 밴드 적용
- [x] 정규화 시스템 구현

### Phase 2: 고도화 ✅
- [x] 유사도 기반 Lane Join (≥0.60)
- [x] 이상치 탐지 (Robust Z-score)
- [x] PRISM 증명 시스템
- [x] 리포트 자동 생성
- [x] 결과 파일 자동 저장 (JSON/CSV/Excel)

### Phase 3: 추가 기능 (계획)
- [ ] DN (Delivery Note) 증빙문서 매핑
- [ ] Gate 검증 시스템
- [ ] Dashboard 개발
- [ ] 자동화 스케줄링

---

## 시스템 특징

### Lane Map 기반 검증
- **자동 매칭**: Origin/Destination/Vehicle/Unit 기준
- **정규화**: Canonical 매핑 (Mussafah → Storage Yard 등)
- **Delta 계산**: (청구 요율 - 기준 요율) / 기준 요율 × 100
- **Exact Match 우선** → **Similarity Join (≥0.60)** 폴백

### 유사도 가중치
- **Origin**: 0.35
- **Destination**: 0.35
- **Vehicle**: 0.10
- **Distance**: 0.10 (≤15km decay)
- **Rate**: 0.10 (±30% decay)

### COST-GUARD 밴드
- **PASS**: ≤2.00% (통과)
- **WARN**: 2.01-5.00% (경고)
- **HIGH**: 5.01-10.00% (높음)
- **CRITICAL**: >10.00% (심각)
- **세이프가드**: |Δ%| > 15% → 자동 FAIL

---

## 참조 문서

- **SHPT 시스템**: `../01_DSV_SHPT/README.md`
- **시스템 아키텍처**: `Documentation/DOMESTIC_SYSTEM_DOCUMENTATION.md`

---

## 연락처

**Project**: Samsung C&T HVDC  
**System**: DSV DOMESTIC Invoice Audit  
**Status**: ✅ Operational

---

**시스템 상태**: ✅ Ready  
**최근 검증**: 2025-10-12 13:35:51  
**처리 항목**: 8개 | **PASS**: 5 (62.5%) | **처리시간**: 1.35초

