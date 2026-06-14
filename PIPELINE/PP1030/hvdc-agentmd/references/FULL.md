# hvdc-agentmd — 운영 확장판(Full)

## 1) 원칙: "명령/경로/플래그는 반드시 증거로 확정"
- CLI 인자: help 출력 또는 argparse 정의에서 확정한다.
- 폴더/파일: repo 실존 기준으로만 문서화한다.
- 불확실: `TODO:`로 남기고, 사용자가 제공하면 즉시 반영한다.

## 2) agent.md를 Commands-first로 유지하는 규칙
- README에서 설명이 길어져도 agent.md는:
  - Setup / Run / Test / Lint
  - Data Contract
  - Safety & Permissions
  - PR 규칙
  - Troubleshooting
  위 5개가 항상 상단에 오도록 유지한다.

## 3) Stage별 "검증 포인트" 최소 세트(권장)
- Stage1: row count, vendor coverage, header match rate
- Stage2: derived columns 생성률, SQM 계산률, null/범위 이상치
- Stage3: 12시트 존재, 주요 합계 불변, 시트명/컬럼명 고정
- Stage4: anomaly count/분포 급변 감지(허용 오차 정의)

## 4) 문서 미러링 전략(agent.md ↔ AGENTS.md)
- 운영 SSOT는 1개로 고정(권장: agent.md).
- 미러 파일은 내용이 항상 동일해야 하며,
  - 변경 시 `scripts/sync_agent_docs.py --dry-run`로 diff 확인
  - 승인 후 `--write`로 반영한다.

## 5) 보안/안전 가드레일(강제)
- 원본 Excel/현장 데이터는 외부 공유 금지.
- `data/raw/`는 절대 수정/삭제 금지.
- 신규 의존성/출력 포맷 변경은 사전 승인 필요.

## 6) 유지보수 루틴(권장)
- 매 릴리즈/주요 변경 시 checklist 실행
- 문서 감사 스크립트 통과를 PR 필수 체크로 둔다(선택)
