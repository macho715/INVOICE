# HVDC 입고로직 종합 리포트 — 업그레이드 계획서

**문서 버전:** 1.0  
**작성일:** 2026-03-13  
**Skill:** project-upgrade v1.2.1  
**Scope:** Stage 3 출력 `HVDC_입고로직_종합리포트_*.xlsx` (12시트) — 구조·가독성·문서화·소비자 경험

---

## Executive Summary

- **대상:** 입고로직 종합 리포트(Excel 12시트, 63컬럼 표준). Stage 3에서 생성, Stage4·VBA·현업이 소비.
- **현황:** 시트 순서·구성은 코드 내 하드코딩, 메타데이터·목차·요약 시트 없음. 12시트 탐색·재현성 추적·의사결정자용 1페이지 요약이 부족.
- **Top10:** Reliability(메타·목차·checksum), Performance(샘플 행 수), DX(요약 시트·표 포맷), Architecture(시트명 config), Docs(안내·버전 이력), Security(마스킹 옵션).
- **Best3:** (1) 메타데이터 시트 (2) 목차(TOC) 시트 (3) Executive Summary 시트. 각 Evidence ≥2, Verification PASS.
- **적용 원칙:** 제안·계획만 문서화. 출력 포맷(시트명·컬럼) 변경 시 agent.md에 따라 명시적 승인 필요.

---

## 1. Current State Snapshot

| 항목 | 내용 |
|------|------|
| **출력 파일** | `data/processed/reports/HVDC_입고로직_종합리포트_{timestamp}_v3.0-corrected.xlsx` |
| **시트 수** | 12 (고정) |
| **시트 순서** | ① 창고_월별_입출고 ② 현장_월별_입고재고 ③ Flow_Code_분석 ④ 전체_트랜잭션_요약 ⑤ KPI_검증_결과 ⑥ 원본_데이터_샘플 ⑦ HITACHI_원본데이터_Fixed ⑧ SIEMENS_원본데이터_Fixed ⑨ 통합_원본데이터_Fixed ⑩ SQM_누적재고 ⑪ SQM_Invoice과금 ⑫ SQM_피벗테이블 |
| **표준 헤더** | 63개 (통합_원본데이터_Fixed 등). agent.md 계약. |
| **핵심 시트** | 통합_원본데이터_Fixed(Stage4 입력), 창고_월별_입출고, SQM 3시트 |
| **입력** | Stage2 derived: HVDC WAREHOUSE_HITACHI(HE).xlsx, (선택) SIMENSE |
| **생성 코드** | `scripts/stage3_report/report_generator.py`, `hvdc_excel_reporter_final_sqm_rev.py` |
| **설정** | `config/pipeline_config.yaml` (stage3), flow_ledger 등 |
| **메타데이터** | 파일명에 timestamp 포함, 리포트 내부 메타 시트 없음 |
| **목차/요약** | 없음 |
| **문서** | `docs/technical/PIPELINE_STAGE3_TECHNICAL.md`, `scripts/stage3_report/README.md` |

**evidence_paths:**  
`docs/technical/PIPELINE_STAGE3_TECHNICAL.md`, `scripts/stage3_report/report_generator.py`, `config/pipeline_config.yaml`, `AGENTS.md`(데이터 계약).

---

## 2. Stack / Constraints

| 구분 | 내용 |
|------|------|
| **출력 형식** | Excel (.xlsx), openpyxl/XlsxWriter |
| **시트/컬럼 계약** | 12시트·63컬럼 변경 시 Stage4·VBA 영향 → Breaking Change 절차 필요 |
| **런타임** | Windows 10/11, Python 3.12+ |
| **성능** | Stage3 약 115초 수준 유지 목표 |
| **제약** | agent.md: 출력 포맷 변경 시 config/core/문서 동시 수정, 회귀 테스트, PR "Breaking Change" 표기 |

---

## 3. Upgrade Ideas — Top 10 (6 buckets)

| # | Bucket | 아이디어 | Evidence | PriorityScore 참고 |
|---|--------|----------|----------|--------------------|
| 1 | **Reliability** | 리포트 메타데이터 시트 추가: 생성일시(UTC/로컬), 파이프라인 버전, 입력 파일 목록, 시트별 행 수 | E1, E2 | High |
| 2 | **Reliability** | 시트 순서 고정 + "목차" 시트(1번): 시트명·한 줄 설명·하이퍼링크 | E3, E4 | High |
| 3 | **Performance** | 원본_데이터_샘플 행 수 설정 가능(config): 1000건 고정 → N건 또는 비활성화 | — | Medium |
| 4 | **DX** | "요약" 시트(Executive Summary): 총 케이스 수, 벤더별 건수, 데이터 기간, KPI 핵심 1페이지 | E4, E5 | High |
| 5 | **Architecture** | 시트명·시트 순서를 config 또는 단일 상수/모듈로 분리 | agent.md | Medium |
| 6 | **Docs** | 리포트 내 "사용 안내" 시트 또는 첫 시트 상단: 시트 설명, 데이터 기간, 연락처 | E5 | Medium |
| 7 | **Security** | 배포용 복사본 생성 시 민감 컬럼 제거/마스킹 옵션 | — | Low (선택) |
| 8 | **Reliability** | 생성 시 시트별 행 수·checksum을 메타데이터 시트 또는 JSON에 기록 | E2 | Medium |
| 9 | **DX** | Excel 표 포맷(Format as Table) 적용 옵션: 가독성·접근성·필터 | E4, E6 | Medium |
| 10 | **Docs** | 리포트 버전(v3.0-corrected) 및 변경 이력 1~2줄을 메타/안내 시트에 명시 | E2 | Medium |

---

## 4. Best 3 Deep Report

### Best #1: 메타데이터 시트 추가

| 항목 | 내용 |
|------|------|
| **Goal** | 재현성·감사·트러블슈팅 시 입력/버전 추적. |
| **Design** | 별도 시트 "Report_Meta" 또는 "메타데이터": 생성일시(ISO8601), pipeline 버전, Stage3 입력 파일 경로(또는 이름), 시트별 행 수 테이블. 기존 12시트 앞 또는 뒤에 추가. |
| **PR Plan** | (1) report_generator에 메타 시트 생성 함수 추가 (2) config에 `report_include_meta_sheet: true/false` (3) Stage3 기술 문서에 메타 필드 정의 |
| **Tests** | 메타 시트 존재, 필수 필드(생성일시, 버전, 시트별 행 수) 포함 검증 |
| **Rollout** | 기본 true, 문제 시 config로 비활성화 |
| **Risks** | 시트 수 12→13 시 VBA/Stage4가 시트 인덱스로 접근하면 영향 → 인덱스 대신 시트명으로 접근 권장 문서화 |
| **KPIs** | 동일 입력 재실행 시 메타 시트 생성일시·행 수 일치 |
| **Evidence** | E1 (OpenMetadata reportData), E2 (DataHub/Alation lineage·타임스탬프) |

---

### Best #2: 목차(Table of Contents) 시트

| 항목 | 내용 |
|------|------|
| **Goal** | 12시트 탐색 시간 단축, 신규 사용자 온보딩. |
| **Design** | 첫 시트 "목차" 또는 "TOC": 시트명 | 한 줄 설명(선택) | 하이퍼링크. 기존 12시트는 2~13번으로 밀림. 통합_원본데이터_Fixed 등 시트명 유지. |
| **PR Plan** | (1) 목차 시트 생성 함수(시트명 목록·하이퍼링크) (2) 시트 순서를 config/상수로 정의 (3) Stage3 README에 목차 사용법 |
| **Tests** | 목차 시트 존재, 링크 개수 ≥ 12 |
| **Rollout** | 메타 시트와 함께 또는 단독 적용 가능하도록 분리 |
| **Risks** | 시트 인덱스 변경 시 Stage4/VBA 점검 필요(시트명 기준이면 무영향) |
| **KPIs** | 12개 시트 모두 목차에서 클릭 한 번에 이동 |
| **Evidence** | E3 (howtogeek TOC), E4 (thebricks 다중 탭·Report/Data 분리) |

---

### Best #3: Executive Summary(요약) 시트

| 항목 | 내용 |
|------|------|
| **Goal** | 의사결정자가 1분 내 총 케이스 수·벤더별·기간·주요 KPI 파악. |
| **Design** | "요약" 또는 "Summary" 시트: 총 Case 수, HITACHI/SIEMENS 건수, 데이터 기간(최소~최대 날짜), 창고_월별_입출고/SQM 요약 수치, KPI_검증_결과 요약(선택). 기존 집계 로직 재사용. |
| **PR Plan** | (1) 요약용 집계 함수 또는 기존 DataFrame 요약 (2) 시트 레이아웃(제목·라벨·숫자) (3) 문서에 요약 필드 정의 |
| **Tests** | 요약 시트 존재, 필수 수치(총 케이스, 벤더별 건수) 존재 |
| **Rollout** | 목차 다음(2번) 또는 메타 다음에 배치 |
| **Risks** | 집계 로직 오류 시 숫자 불일치 → 기존 KPI_검증_결과 등과 교차 검증 권장 |
| **KPIs** | 요약 시트 수치 = 통합_원본데이터_Fixed 등과 일치 |
| **Evidence** | E4 (thebricks KPI·다중 탭), E5 (Summary sheet·KPI 카드) |

---

## 5. Verification (PASS/AMBER/FAIL)

| Best | vs 계약(63컬럼·기존 시트명·Stage4 입력) | 판정 |
|------|----------------------------------------|------|
| #1 메타데이터 시트 | 기존 12시트 구조/이름 불변, 추가 시트만 추가. Stage4는 시트명 "통합_원본데이터_Fixed" 사용 시 무영향 | **PASS** |
| #2 목차 시트 | 1번에 삽입, 나머지 시트 순서·이름 유지. 인덱스 0→1 등으로 밀리므로 시트 인덱스 의존 코드만 점검 | **PASS** |
| #3 요약 시트 | 기존 집계 참조, 출력 포맷 계약 무변경 | **PASS** |

**종합:** Best3 모두 **PASS**. 적용 시 dry-run → change list → explicit approval 권장.

---

## 6. Options A/B/C & Roadmap

| Option | 기간 | 내용 |
|--------|------|------|
| **A** | 30일 | Best #1 메타데이터 시트 + config 옵션 + 문서 반영 |
| **B** | 60일 | Best #1 + #2 목차 시트 + #3 요약 시트 + 시트 순서 config화 |
| **C** | 90일 | Best #1~#3 + Top10 중 R3(샘플 행 수), R5(시트명 config), R6(사용 안내), R9(표 포맷 옵션) 단계 도입 |

**30/60/90-day Roadmap (요약):**

- **30일:** 메타데이터 시트, `report_include_meta_sheet`, Stage3 문서 갱신  
- **60일:** 목차 시트, 요약 시트, 시트 순서 상수/config 정리  
- **90일:** 샘플 행 수 설정, 사용 안내, 표 포맷 옵션, ADR 1건(리포트 시트 추가 결정)

---

## 7. Evidence Table

| ID | URL / 출처 | published_date / updated | 비고 |
|----|------------|---------------------------|------|
| E1 | OpenMetadata reportData schema (docs.open-metadata.org) | docs updated | 메타데이터·식별자·타임스탬프 |
| E2 | DataHub reporting telemetry, Alation lineage API v2025.1 | 2025 | 타임스탬프·메타데이터·라인age |
| E3 | How to Add a Table of Contents to Excel (howtogeek.com) | — | TOC·하이퍼링크 (AMBER: 날짜 미확인) |
| E4 | How to Make Excel Reports Look More Professional (thebricks.com) | 2025-02-20 | 다중 탭·Report/Data 분리·KPI (AMBER: 2025-06 미만) |
| E5 | How to Create a Summary Sheet in Excel (thebricks.com) | — | 요약 시트·KPI (AMBER) |
| E6 | Make your Excel spreadsheets accessible (support.office.com) | Microsoft Docs | 표 포맷·접근성 |

*2025-06+ 엄격 적용 시 E4(2025-02-20), E3·E5(날짜 미확인)는 AMBER_BUCKET. 본 계획에서는 리포트 전용 참고 Evidence로 활용.*

---

## 8. AMBER_BUCKET

- **E3, E5:** published_date 미기재 → Top10/Best3 Evidence로 사용 시 AMBER. 아이디어 자체는 채택 가능.
- **E4:** 2025-02-20 (2025-06 미만) → 2025-06+ 규칙상 AMBER. 다중 탭·KPI 참고용으로 인용.

---

## 9. Open Questions (≤3)

1. **시트 추가 시 인덱스:** 목차·메타·요약 추가 시 시트가 15개 수준이 됨. Stage4/VBA가 "첫 시트" 또는 인덱스 0으로 통합 시트를 참조하는지 확인 후, 시트명 기준으로 통일할지 결정.
2. **요약 시트 데이터 소스:** KPI_검증_결과·창고_월별_입출고 등 기존 시트에서 수치만 가져올지, report_generator 내부에서 별도 집계할지(중복 방지).
3. **메타 시트 언어:** 필드명·라벨을 한글 vs 영문으로 할지(현업·해외 파트너 사용 고려).

---

## 10. 적용 시 주의사항

- 본 문서는 **제안·계획만** 포함. 자동 코드 변경/커밋/배포 금지.
- 시트명·컬럼 수·시트 순서 등 **출력 포맷** 변경 시 agent.md: config·core·문서 동시 수정, 회귀 테스트, PR "Breaking Change" 표기.
- Best3 적용 후 Stage4·VBA·현업 검토용 체크리스트 1회 수행 권장.

---

*문서 끝.*
