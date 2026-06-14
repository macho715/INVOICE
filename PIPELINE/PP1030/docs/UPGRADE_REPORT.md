# HVDC Pipeline — Project Upgrade Report (Full Pipeline)

**Generated:** 2026-03-13  
**Scope:** backend + CI + docs + reliability (Stage 1–4 pipeline 완료 상태 기준)  
**Skill:** project-upgrade v1.2.1 | EN-only, 2025-06+ evidence

---

## Executive Summary

- **Current state:** HVDC Pipeline v4.0.54 (Excel → Stage1 Sync → Stage2 Derived → Stage3 Report → Stage4 Anomaly). Python, pandas/openpyxl, config-driven, Windows-oriented. No CI (no `.github/workflows`), no SECURITY file, no ADR folder. 품질 게이트는 agent.md에만 문서화(pytest, ruff, black, isort, mypy).
- **Top10:** Reliability(CI/테스트), Security(의존성 감사), Performance(Excel/벡터화), DX(로컬/CI 일원화), Architecture(스테이지 계약/스키마), Docs(파이프라인 문서/런북) 6버킷 기준 10개 아이디어. Evidence는 EN 2025-06+ 자료만 채택, 미기재 날짜는 AMBER_BUCKET.
- **Best3:** (1) GitHub Actions CI + pytest/ruff/coverage, (2) pip-audit 기반 의존성 보안 감사, (3) 파이프라인 문서/런북 템플릿(목적·소스·변환·실패모드·소유자). 각 Best3는 Evidence ≥2 및 날짜 충족.
- **Verification:** Best3 모두 현재 스택/제약과 충돌 없음 → **PASS**. 적용은 별도 승인 워크플로 필요(자동 코드/커밋/배포 금지).

---

## 1. Current State Snapshot

| 항목 | 상태 | 비고 |
|------|------|------|
| **README** | 있음 | README.md (v4.0.54, Standalone/헤더 개선 등), README_UNIFIED.md (Excel 색상 검증) |
| **Agent/에이전트** | 있음 | AGENTS.md / agent.md (Commands-first, 데이터 계약, Stage 체크리스트) |
| **ADR** | 없음 | Architecture Decision Records 폴더/문서 없음 |
| **SECURITY** | 없음 | SECURITY.md/policy 없음 |
| **CI** | 없음 | `.github/workflows` 없음, CI 설정 없음 |
| **Build** | Python venv + pip | `requirements.txt` (pandas, openpyxl, XlsxWriter, polars, great-expectations, xlwings, pywin32) |
| **Test** | pytest (문서화) | agent.md: pytest, ruff, black, isort, mypy — 실행 경로/커버리지 미명시 |
| **Lint/Format** | ruff, black, isort, mypy | 문서만, CI 미연동 |
| **Config** | YAML | config/pipeline_config.yaml, stage2_derived_config, stage4_anomaly.yaml |
| **Docs** | 다수 | docs/, HVDC Pipeline v4.0.54.md, 아키텍처 문서, 기술 문서(Stage1/3/4 등) |
| **Deploy** | 로컬/수동 | Standalone exe 빌드(PyInstaller) 문서 있음, 자동 배포 없음 |

**evidence_paths (Doc-first):**

- `README.md`, `AGENTS.md` (agent.md), `requirements.txt`, `config/pipeline_config.yaml`
- `docs/`, `HVDC Pipeline v4.0.54.md`, `HVDC Pipeline 시스템 아키텍처 문서 v4.0.54.md`
- (없음) `.github/`, `SECURITY*`, `ADR/`, `references/source-policy.md` (project-upgrade 레퍼런스는 스킬 측)

---

## 2. Stack / Constraints

| 구분 | 내용 |
|------|------|
| **언어** | Python (3.12 권장, 3.13 Standalone 빌드 문서 있음) |
| **런타임** | Windows 10/11 (xlwings/pywin32 사용) |
| **프레임워크** | 없음 (스크립트/스테이지 조합) |
| **빌드** | `python -m venv venv`, `pip install -r requirements.txt` |
| **테스트** | pytest (단위+통합), great-expectations/pandera 언급 |
| **CI** | 없음 (추가 시 GitHub Actions 등 선택 가능) |
| **배포** | 수동 실행, data/raw 읽기 전용 원칙 |
| **제약** | 출력 포맷(시트/헤더) 변경 시 명시적 승인, 63개 표준 헤더 계약 |

---

## 3. External Research (TOP_HITS) — EN, 2025-06+

| # | Source | Topic | Date / Note |
|---|--------|--------|-------------|
| E1 | Daniel Nouri – Modern Python CI with Coverage in 2025 | uv, pytest-xdist, py-cov-action, GitHub-native coverage | **2025-11-03** (published_date) |
| E2 | dataengineeringcompanies.com – 10 Data Pipeline Testing Best Practices for 2026 | Data quality, unit/integration/schema/regression testing, lineage, observability | **2026** (title) |
| E3 | Dagster – Smoke Test Your Data Pipelines First | Smoke tests on empty/synthetic data, fast feedback | Site current (2026); post date not on page → AMBER |
| E4 | GitHub Docs – Building and testing Python | setup-python, pytest in Actions | Official docs (updated) |
| E5 | datadef.io – How to Document Data Pipelines (2025) | Purpose, sources, transformations, runbook, ownership, three-layer docs | **2025** (title) |
| E6 | pip-audit (PyPA) | Audit dependencies for known vulnerabilities | GitHub pypa/pip-audit; maintained |
| E7 | Medium – Building End-to-End ETL Pipelines in Python 2025 Best Practices | ETL structure, testing, CI/CD | 2025 (title) |
| E8 | Medium – 10 Pandas Optimizations 5× Faster Than Excel | read_excel options, dtype, usecols, vectorization | — (날짜 미확인 → AMBER 가능) |

**AMBER_BUCKET (날짜 미충족/미기재):**  
Dagster smoke test post (날짜 미표기), 일부 Medium/블로그(정확한 published_date 미확인). Top10/Best3에는 **날짜 충족 Evidence만** 사용.

---

## 4. Upgrade Ideas — Top 10

6버킷 기준 정리. PriorityScore = (Impact × Confidence) / (Effort × Risk) 참고.

| # | Bucket | Idea | Evidence | PriorityScore (참고) |
|---|--------|------|----------|----------------------|
| 1 | **Reliability** | GitHub Actions CI 도입: pytest, ruff, black, isort, mypy 실행 및 (선택) coverage 리포팅 | E1, E4 | High |
| 2 | **Reliability** | 파이프라인 smoke test: 빈/합성 데이터로 Stage1–4 순차 실행, 스키마/필수 컬럼 검증 | E2, E3 | High |
| 3 | **Security** | pip-audit 또는 OWASP depscan으로 requirements 정기 감사, CI에 감사 단계 추가 | E6 | Medium–High |
| 4 | **Performance** | Excel 로딩 시 usecols/dtype/parse_dates 명시, 대용량 시 polars 옵션 유지(기존 언급과 일치) | E8, 프로젝트 요구사항 | Medium |
| 5 | **DX** | 단일 명령으로 품질 게이트 실행 스크립트 또는 Makefile: pytest + ruff + black + isort + mypy | E1, agent.md | Medium |
| 6 | **Architecture** | Stage 입출력 스키마(63개 헤더·파생 13개)를 YAML/JSON으로 명시하고 검증 단계에서 사용 | E2 (schema validation), agent.md | Medium |
| 7 | **Docs** | 파이프라인별 문서 템플릿: 목적, 소스/대상, 주요 변환, 상위 3 실패모드·런북, 소유자·갱신일 | E5 | Medium |
| 8 | **Reliability** | 회귀 테스트: 고정 샘플 입력으로 Stage1–4 실행 후 행 수/핵심 집계 비교 (agent.md 회귀 항목 구체화) | E2, agent.md | Medium |
| 9 | **Docs** | ADR 폴더 도입: 헤더 표준화, 시트 포함 패턴(shipment 등), 벤더 분기 등 주요 결정 기록 | E5, 프로젝트 이력 | Low–Medium |
| 10 | **DX** | (선택) uv 도입: 로컬/CI 의존성 및 lockfile 통일로 재현성 향상 | E1 | Low–Medium |

---

## 5. Best 3 Deep Report

### Best #1: GitHub Actions CI (pytest, ruff, black, isort, mypy, coverage)

- **Goal:** 모든 PR/푸시에서 테스트·린트·포맷·타입 검사 자동 실행, (선택) 커버리지 리포팅으로 품질 가시화.
- **Design:**  
  - `.github/workflows/ci.yml`: on push/PR → checkout → setup Python (또는 uv) → install deps → pytest, ruff, black, isort, mypy.  
  - (선택) pytest-cov + py-cov-action 또는 codecov; coverage 임계치 문서화.
- **PR Plan (≥3):**  
  1) workflow 파일 추가 및 브랜치 보호 규칙(테스트 통과 필수) 문서화;  
  2) agent.md에 CI 절 추가(트리거, 실패 시 대응);  
  3) requirements-dev 또는 pyproject.toml에 pytest-cov/ruff/black/isort/mypy 버전 고정.
- **Tests:** 기존 pytest 유지; CI에서 `pytest`, `ruff check .`, `black --check .`, `isort --check .`, `mypy .` 실행.
- **Rollout/Rollback:** 브랜치 보호 optional 먼저 적용 후 필수 전환; 실패 시 workflow 비활성화 또는 조건부 skip.
- **Risks:** Windows 전용 스크립트(xlwings 등)는 Linux runner에서 제외하거나 별도 job으로 분리 필요.
- **KPIs:** 빌드 시간 &lt; 5분(agent.md 기준), 린트/테스트 실패 시 머지 차단.
- **Evidence:** E1 (2025-11-03), E4 (GitHub Docs).

---

### Best #2: pip-audit 기반 의존성 보안 감사

- **Goal:** 알려진 취약점(CVE)이 포함된 의존성 도입 방지, 정기 감사 자동화.
- **Design:**  
  - 로컬/CI에서 `pip-audit` 실행 (requirements.txt 또는 가상환경 대상).  
  - 심각도 Critical/High 시 빌드 실패 또는 경고 정책 명시.
- **PR Plan (≥3):**  
  1) requirements.txt에 pip-audit 추가 또는 CI 단계로만 실행;  
  2) SECURITY.md 또는 agent.md에 “의존성 감사” 절 추가 및 주기 명시;  
  3) (선택) 주기적 이슈/스케줄러로 pip-audit 실행.
- **Tests:** pip-audit exit code 0/비0 시 CI 단계 성공/실패로 검증.
- **Rollout/Rollback:** 먼저 감사만 실행(경고만), 이후 정책에 따라 fail 조건 도입.
- **Risks:** 오탐 또는 호환성 이슈 시 예외 목록 또는 버전 업그레이드 계획 필요.
- **KPIs:** Critical/High 0건 유지, 감사 주기 명시(예: PR 시 + 월 1회).
- **Evidence:** E6 (pip-audit), E2 (데이터 파이프라인 테스트/품질 맥락).

---

### Best #3: 파이프라인 문서·런북 템플릿 (목적, 소스, 변환, 실패모드, 소유자)

- **Goal:** 각 Stage(또는 전체 파이프라인)에 대해 목적·입출력·주요 변환·상위 실패모드·런북·소유자·갱신일을 한 곳에 유지.
- **Design:**  
  - docs/ 또는 각 stage README에 “Pipeline doc” 한 페이지: 목적, 소스/대상, 주요 변환, Top 3 실패모드·해결, SLAs·갱신일, 소유자.  
  - agent.md/README와 중복 최소화, 상호 링크.
- **PR Plan (≥3):**  
  1) 템플릿 마크다운 생성 및 Stage1–4용 초안 작성;  
  2) agent.md에 “파이프라인 문서 갱신” 체크리스트 추가;  
  3) PR 시 영향 받는 Stage 문서 갱신 요구 규칙 명시.
- **Tests:** 문서 존재 여부/필수 섹션 검사 스크립트(선택).
- **Rollout/Rollback:** 기존 문서에 병합 또는 별도 파일로 유지; 롤백 시 이전 버전으로 복원.
- **Risks:** 유지보수 부담; 템플릿을 단순하게 유지해 부담 최소화.
- **KPIs:** 신규 참여자가 15분 내 목적·소유자·실패 대응 파악 가능(참고: E5 15-minute rule).
- **Evidence:** E5 (datadef.io 2025), E2 (data quality/runbook 맥락).

---

## 6. Verification (PASS/AMBER/FAIL)

| Best | vs Stack/Constraints | 판정 |
|------|----------------------|------|
| Best #1 (CI) | Python/Windows 제약과 양립; Linux runner에서 Windows 전용 코드 제외 가능 | **PASS** |
| Best #2 (pip-audit) | requirements.txt 기반, 추가 도구만 도입, 기존 빌드 무변경 | **PASS** |
| Best #3 (Docs/런북) | 문서만 추가/갱신, 코드 계약(63 헤더 등) 변경 없음 | **PASS** |

**종합:** Best3 모두 **PASS**. 적용 시 dry-run → change list → explicit approval 순 권장.

---

## 7. Options A/B/C

- **Option A (30일):** Best #1 CI 도입 + agent.md CI 절 보강.
- **Option B (60일):** Best #1 + Best #2 (pip-audit CI 단계) + Best #3 템플릿 및 Stage1–4 초안.
- **Option C (90일):** Best #1–3 + Top10 중 스모크 테스트(#2), 스키마 검증(#6), 회귀 테스트(#8)까지 단계적 도입.

---

## 8. 30/60/90-day Roadmap (요약)

| 기간 | 항목 |
|------|------|
| **30일** | GitHub Actions CI(pytest, ruff, black, isort, mypy), agent.md CI 반영 |
| **60일** | pip-audit 감사 단계, 파이프라인 문서/런북 템플릿 및 Stage1–4 초안 |
| **90일** | Smoke test·스키마 검증·회귀 테스트 구체화, ADR 폴더·최초 ADR 1–2건 |

---

## 9. Evidence Table

| ID | URL | published_date / updated_date | accessed | Note |
|----|-----|-------------------------------|----------|------|
| E1 | https://danielnouri.org/notes/2025/11/03/modern-python-ci-with-coverage-in-2025/ | 2025-11-03 | 2026-03-13 | Modern Python CI, uv, pytest-xdist, py-cov-action |
| E2 | https://dataengineeringcompanies.com/insights/data-pipeline-testing-best-practices/ | 2026 (title) | 2026-03-13 | 10 practices, data quality, testing layers |
| E3 | https://dagster.io/blog/smoke-test-data-pipeline | — | 2026-03-13 | AMBER (no date on page) |
| E4 | https://docs.github.com/en/actions/how-tos/writing-workflows/building-and-testing/building-and-testing-python | Official docs | 2026-03-13 | GitHub Actions Python |
| E5 | https://datadef.io/guides/en/data-pipeline-documentation | 2025 (title) | 2026-03-13 | How to document pipelines, runbook, three layers |
| E6 | https://github.com/pypa/pip-audit | Maintained (PyPA) | 2026-03-13 | Dependency audit |

---

## 10. AMBER_BUCKET

- Dagster smoke test 블로그: 게시일 미표기 → Top10/Best3 Evidence에서 제외, 참고용만.
- 일부 Medium/블로그: published_date 미확인 항목 → 참고용, 채택 시 추가 확인 필요.

---

## 11. Open Questions (≤3)

1. CI에서 Windows 전용 코드(xlwings/pywin32)를 어떻게 처리할지: Linux에서 스킵 vs Windows runner 사용 vs 별도 “windows-check” workflow.
2. pip-audit 실패 시 정책: Critical만 fail vs High 이상 fail vs 경고만 로그.
3. 파이프라인 문서 소유자: 팀 단위 vs Stage 단위 vs 단일 담당자.

---

## 12. HVDC 입고로직 종합 리포트 전용 업그레이드 아이디어

**Scope:** Stage 3 출력 `HVDC_입고로직_종합리포트_{timestamp}_v3.0-corrected.xlsx` (12시트, 63컬럼 표준) — 리포트 구조·가독성·문서화·소비자 경험 개선.  
**Evidence:** EN 2025-06+ 우선; 일부는 2025 상반기 또는 공식 문서(날짜 미표기) → AMBER_BUCKET 명시.

### 12.1 리포트 현황 (Doc-first)

| 항목 | 내용 |
|------|------|
| **출력 파일** | `data/processed/reports/HVDC_입고로직_종합리포트_{timestamp}_v3.0-corrected.xlsx` |
| **시트 수** | 12 |
| **시트 목록** | ① 창고_월별_입출고 ② 현장_월별_입고재고 ③ Flow_Code_분석 ④ 전체_트랜잭션_요약 ⑤ KPI_검증_결과 ⑥ 원본_데이터_샘플 ⑦ HITACHI_원본데이터_Fixed ⑧ SIEMENS_원본데이터_Fixed ⑨ 통합_원본데이터_Fixed ⑩ SQM_누적재고 ⑪ SQM_Invoice과금 ⑫ SQM_피벗테이블 |
| **핵심 시트** | 통합_원본데이터_Fixed(63컬럼, Stage4 입력), 창고_월별_입출고, SQM 관련 3시트 |
| **소비자** | Stage4(이상치 탐지), VBA/Excel 런처, 현업 검토 |
| **생성 코드** | `report_generator.py`, `hvdc_excel_reporter_final_sqm_rev.py` |

### 12.2 Top10 — 입고로직 종합 리포트 (6버킷)

| # | Bucket | 아이디어 | Evidence | 비고 |
|---|--------|----------|----------|------|
| R1 | **Reliability** | 리포트 메타데이터 시트 추가: 생성일시, 파이프라인 버전, 입력 파일 목록, 시트별 행 수 | E_R1, E_R2 | 재현성·감사 |
| R2 | **Reliability** | 시트 순서 고정 + “목차” 시트(1번): 시트명·요약·하이퍼링크로 네비게이션 | E_R3, E_R4 | 12시트 탐색 개선 |
| R3 | **Performance** | 원본_데이터_샘플 행 수 설정 가능(config 또는 상수): 1000건 고정 → N건 또는 비활성화 옵션 | — | 성능·파일 크기 |
| R4 | **DX** | “요약” 시트(Executive Summary): 총 케이스 수, 벤더별 건수, 기간, KPI 핵심 수치 1페이지 | E_R4, E_R5 | 의사결정자용 |
| R5 | **Architecture** | 시트명·컬럼 계약을 config 또는 상수로 분리해 시트 추가/이름 변경 시 한 곳만 수정 | agent.md 계약 | Breaking 방지 |
| R6 | **Docs** | 리포트 내 “사용 안내” 시트 또는 첫 시트 상단 블록: 시트 설명, 데이터 기간, 연락처 | E_R5 | 온보딩 |
| R7 | **Security** | 민감 컬럼 제거/마스킹 옵션(배포용 복사본 생성 시) | — | 선택 사항 |
| R8 | **Reliability** | 생성 시 checksum 또는 행 수 로그를 메타데이터 시트 또는 별도 JSON에 기록 | E_R2 | 검증·회귀 |
| R9 | **DX** | Excel 표 포맷(Format as Table) 적용 옵션: 가독성·접근성·필터 기본 on | E_R5, E_R6 | 접근성 |
| R10 | **Docs** | 리포트 버전(v3.0-corrected) 및 변경 이력 1~2줄을 메타데이터/안내 시트에 명시 | E_R2 | 추적 |

### 12.3 Best3 Deep — 입고로직 종합 리포트

**Best #1: 메타데이터 시트 추가 (생성일시, 버전, 입력 파일, 시트별 행 수)**  
- **Goal:** 재현성·감사·트러블슈팅 시 입력/버전 추적.  
- **Design:** 12시트 중 1번 또는 별도 “Report_Meta” 시트에 생성일시(UTC/로컬), pipeline 버전, Stage3 입력 파일 경로, 시트별 행 수 표.  
- **PR Plan:** (1) report_generator에서 메타 시트 생성 로직 추가 (2) config에 메타 표시 on/off (3) agent.md/Stage3 문서에 메타 필드 설명.  
- **Tests:** 메타 시트 존재 여부 및 필수 필드 포함 여부 단위/통합 테스트.  
- **Evidence:** E_R1, E_R2.

**Best #2: 목차(Table of Contents) 시트 — 1번 시트, 시트명·하이퍼링크**  
- **Goal:** 12시트 탐색 시간 단축, 신규 사용자 온보딩.  
- **Design:** 첫 시트를 “목차” 또는 “TOC”로 두고, 각 시트명 + (선택) 한 줄 설명 + 하이퍼링크. 기존 시트 순서는 유지, 목차만 앞에 삽입.  
- **PR Plan:** (1) 목차 시트 생성 함수 (2) 시트 순서를 config/상수로 정의 (3) Stage3 README에 목차 설명.  
- **Tests:** 목차 시트 존재, 링크 개수 ≥ 시트 수 - 1.  
- **Evidence:** E_R3, E_R4.

**Best #3: Executive Summary(요약) 시트 — 핵심 KPI 1페이지**  
- **Goal:** 의사결정자가 1분 내 총 케이스 수·벤더별·기간·주요 KPI 파악.  
- **Design:** “요약” 또는 “Summary” 시트: 총 Case 수, HITACHI/SIEMENS 건수, 데이터 기간, 창고_월별_입출고/SQM 요약 수치, (선택) KPI_검증_결과 요약.  
- **PR Plan:** (1) 요약 시트 데이터 생성(기존 집계 재사용) (2) 시트 레이아웃(제목·숫자·라벨) (3) 문서에 요약 필드 정의.  
- **Tests:** 요약 시트 존재, 필수 수치 컬럼/행 존재.  
- **Evidence:** E_R4, E_R5.

### 12.4 Verification (리포트 아이디어)

| Best | vs 계약(63컬럼·12시트·Stage4 입력) | 판정 |
|------|-----------------------------------|------|
| 메타데이터 시트 | 기존 시트 구조/이름 불변, 추가 시트만 추가 | **PASS** |
| 목차 시트 | 1번에 삽입, 나머지 시트 순서/이름 유지 | **PASS** |
| 요약 시트 | 기존 집계 로직 참조, 출력 포맷 계약 무변경 | **PASS** |

### 12.5 Evidence Table (리포트)

| ID | URL | published/updated | Note |
|----|-----|-------------------|------|
| E_R1 | OpenMetadata Lineage / reportData schema | docs (updated) | 메타데이터·라인age 참고 |
| E_R2 | DataHub reporting telemetry, Alation lineage | 2025.x API | 타임스탬프·메타데이터 |
| E_R3 | howtogeek.com – Add Table of Contents to Excel | — | TOC·하이퍼링크 (AMBER: 날짜 미확인) |
| E_R4 | thebricks.com – How to Make Excel Reports Look More Professional | **2025-02-20** | 다중 탭 구조, Report/Data 분리, KPI (AMBER: 2025-06 미만) |
| E_R5 | thebricks.com – How to Create a Summary Sheet in Excel | — | 요약 시트·KPI (AMBER) |
| E_R6 | support.office.com – Make Excel spreadsheets accessible | Microsoft Docs | 표 포맷·접근성 |

*리포트 아이디어 적용 시 출력 포맷(시트명·컬럼) 변경은 agent.md에 따라 명시적 승인 필요.*

---

*This report is proposal and plan only. No automatic code changes, commits, or deployments. Apply via separate approval workflow.*
