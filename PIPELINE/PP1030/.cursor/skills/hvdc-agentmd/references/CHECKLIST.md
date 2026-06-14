# agent.md 갱신 체크리스트(운영형)

## A. 변경 감지(Trigger)
- [ ] 파이프라인 버전 변경(예: v4.0.54 → v4.0.55)
- [ ] 실행 엔트리/인자 변경(`--stage4-visualize` 등)
- [ ] I/O 폴더 구조 변경(`data/processed/*`)
- [ ] 품질 도구 변경(pytest/ruff/black/isort/mypy)

## B. 추측 금지 확인(필수)
- [ ] `{{PIPELINE_ENTRY}}` 실제 존재 확인
- [ ] `python {{PIPELINE_ENTRY}} -h` 로 옵션 확인(또는 argparse 코드 확인)
- [ ] `requirements.txt`/`pyproject.toml` 로 도구 확인

## C. 문서 업데이트(필수)
- [ ] Commands(Setup/Run/Test/Lint) 최신화
- [ ] Data Contract(입력 읽기 전용/출력 경로) 최신화
- [ ] Stage 체크리스트(핵심 리스크 + 검증 포인트) 최신화
- [ ] Security/Permissions(금지/승인 필요) 최신화

## D. 동기화/검증(필수)
- [ ] (선택) `AGENTS.md` 미러 동기화(dry-run → write)
- [ ] `python scripts/audit_agent_md.py --path agent.md`
- [ ] 변경이 "출력 포맷"이면 PR에 Breaking Change 라벨/근거 포함
