# hvdc-agentmd 스킬

HVDC Pipeline 저장소의 `agent.md`를 Commands-first로 생성/갱신하는 Cursor IDE 스킬입니다.

## 설치 상태

✅ **Cursor IDE에 설치 완료**: `.cursor/skills/hvdc-agentmd/`

## 빠른 시작

### 1. agent.md 검증
```bash
python hvdc-agentmd/scripts/audit_agent_md.py --path agent.md
```

### 2. 버전 일치 확인
```bash
python hvdc-agentmd/scripts/check_agent_md_version.py
```

### 3. 문서 동기화 (dry-run)
```bash
python hvdc-agentmd/scripts/sync_agent_docs.py --from-path agent.md --to-path AGENTS.md
```

### 4. 문서 동기화 (적용)
```bash
python hvdc-agentmd/scripts/sync_agent_docs.py --from-path agent.md --to-path AGENTS.md --write
```

## 스크립트 목록

| 스크립트 | 목적 |
|---------|------|
| `audit_agent_md.py` | agent.md 품질 검증 (필수 헤딩, 코드블록, 금지사항) |
| `sync_agent_docs.py` | agent.md ↔ AGENTS.md 동기화 |
| `check_agent_md_version.py` | 버전 불일치 감지 (agent.md vs run_pipeline.py vs config) |
| `update_agent_md_from_template.py` | 템플릿 기반 갱신 제안 (보수적) |

## 사용 시나리오

### 파이프라인 버전 업데이트 시
```bash
# 1. 버전 불일치 확인
python hvdc-agentmd/scripts/check_agent_md_version.py

# 2. agent.md 수동 갱신 (버전 정보 업데이트)

# 3. 검증
python hvdc-agentmd/scripts/audit_agent_md.py --path agent.md
```

### 새 Stage 플래그 추가 시
```bash
# 1. run_pipeline.py에서 실제 플래그 확인
python run/run_pipeline.py -h

# 2. agent.md의 Commands 섹션 업데이트

# 3. 검증
python hvdc-agentmd/scripts/audit_agent_md.py --path agent.md
```

## 참조 문서

- `references/AGENTMD_TEMPLATE.md`: agent.md 템플릿
- `references/CHECKLIST.md`: 갱신 체크리스트
- `references/FULL.md`: 운영 확장 가이드

## 주의사항

⚠️ **버전 불일치 감지됨**:
- agent.md: v4.0.54
- run_pipeline.py: v4.0.44
- pipeline_config.yaml: 2.0.0

각 파일이 다른 버전 체계를 사용할 수 있으므로, 실제 파이프라인 버전을 확인하여 agent.md를 갱신하세요.
