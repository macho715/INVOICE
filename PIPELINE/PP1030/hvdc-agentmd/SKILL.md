---
name: hvdc-agentmd
description: HVDC Pipeline(Excel→Stage1~4) 저장소에서 agent.md(AGENTS.md 계열) 운영 지침을 Commands-first로 생성/갱신한다. setup/run/test/lint 명령, data contract(입출력 폴더), Stage 체크리스트, 보안/권한 경계, PR 규칙을 "추측 없이" 정리·검증할 때 사용.
compatibility: Cursor IDE / OpenAI Codex 등 Agent Skills 호환 에이전트. Repo 파일 읽기/쓰기 권한 필요(원본 데이터 수정 금지).
metadata:
  owner: samsung-ct-hvdc
  version: "1.0.0"
  updated: "2026-01-25"
---

## 목적(What)
- 이 스킬은 **HVDC Pipeline 운영 지침(agent.md)** 을 "실행 중심(Commands-first)"으로 **생성/갱신**한다.
- README/설계문서는 인간용이며, agent.md는 **에이전트가 설치/실행/검증을 바로 수행**하도록 최적화한다.

## 사용 시점/트리거(When)
다음 키워드/요청이 나오면 이 스킬을 사용한다:
- "agent.md/AGENTS.md 만들어줘", "온보딩 문서", "setup/run/test/lint", "Stage1~4", "data contract", "추측 없이 실행 가능하게"
- 파이프라인 버전 변경(v4.x), Stage 플래그 변경, I/O 폴더 변경, 품질 도구(ruff/black/pytest/mypy) 변경

## 입력(Inputs)
- (권장) repo 루트에서 다음을 탐색:
  - `agent.md` 또는 `AGENTS.md`(기존 파일)
  - `README.md`, `requirements.txt`/`pyproject.toml`
  - 실행 엔트리(예: `run/run_pipeline.py`, `run/run_pipeline.py -h`)
  - 설정(예: `config/*.yaml`)
  - 데이터 폴더(예: `data/raw`, `data/processed`, `data/anomaly`)
- 사용자 제공 "HVDC Pipeline v4.0.54" 요약(있으면 최우선 참고)

## 출력(Outputs)
- `agent.md` (SSOT 권장)
- (선택) `AGENTS.md` 미러(동일 내용)
- (선택) 검증 로그/리포트: `scripts/audit_agent_md.py` 결과

## 절차(Workflow) — 무조건 이 순서
1) **SSOT 확인**
   - 기본: `agent.md` = SSOT, `AGENTS.md` = mirror
   - repo에 이미 관례가 있으면 그 관례를 따른다(단, SSOT는 1개로 고정).

2) **추측 금지 스캔**
   - 명령/경로/플래그는 반드시 파일에서 확인한다.
   - 확인 방법(예):
     - 실행 파일 존재 확인: `run/run_pipeline.py`
     - 인자 확인: `python run/run_pipeline.py -h` 또는 argparse 정의 검색
     - 품질 도구 확인: `requirements.txt`, `pyproject.toml`, `ruff.toml` 등

3) **agent.md 생성/갱신(템플릿 기반)**
   - `references/AGENTMD_TEMPLATE.md` 구조를 유지한다.
   - 섹션: Project Overview → Commands(Setup/Run/Test/Lint) → Data Contract → Stage 체크리스트 → Config(SSOT) → Security/Permissions → PR 규칙 → Troubleshooting
   - "존재하지 않는 명령/폴더/파일"은 쓰지 말고 `TODO:`로 남긴다.

4) **미러 동기화(선택)**
   - `scripts/sync_agent_docs.py` 사용(기본은 `--dry-run`).
   - 문서가 커지면(예: 32KiB 이상) 섹션을 줄이거나 하위 디렉토리로 분리한다.

5) **검증(필수)**
   - `scripts/audit_agent_md.py` 로 필수 헤딩/코드블록/금지사항을 점검한다.
   - 실패 시: 수정 후 재검증(통과 전까지 PR/커밋 금지).

## 예시(Examples)
- "HVDC Pipeline v4.0.55로 올라갔고 Stage4 플래그가 바뀌었어. hvdc-agentmd로 agent.md 갱신해."
- "새로 ruff 규칙을 추가했어. setup/test/lint 명령과 Troubleshooting을 agent.md에 반영해."

## 엣지 케이스/주의(Edge cases)
- 모노레포: 서브폴더별로 운영이 다르면 **하위 agent.md(또는 AGENTS.md) 분리**를 고려(가장 가까운 파일 우선).
- Windows/Unix 차이: 명령은 OS별 블록으로 분리하되, repo에서 확인된 것만 기재.
- 파이프라인 인자/출력 포맷이 변했는데 테스트가 없으면: **Breaking Change**로 표시하고 회귀 체크리스트를 추가.

## 안전/보안(Safety)
- `data/raw/` 원본 Excel은 **읽기 전용**. 수정/삭제/덮어쓰기 금지.
- 로그/문서에 행 단위 원본 데이터 덤프 금지(필요 시 마스킹/샘플링).
- 새 의존성 추가/대규모 리팩토링/출력 포맷(시트명/헤더) 변경은 **사전 승인**이 필요.

## 참조(References)
- 템플릿: `references/AGENTMD_TEMPLATE.md`
- 갱신 체크리스트: `references/CHECKLIST.md`
- 확장판/운영 가이드: `references/FULL.md`
- 동기화 스크립트: `scripts/sync_agent_docs.py`
- 문서 감사 스크립트: `scripts/audit_agent_md.py`
