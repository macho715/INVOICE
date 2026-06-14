# 버전 동기화 보고서

**생성일**: 2026-01-25  
**작업**: agent.md 버전 통일 및 AGENTS.md 미러 생성

## 📊 버전 현황

### 프로젝트 버전 정보
- **프로젝트 문서 버전**: v4.0.54 (README.md, HVDC Pipeline v4.0.54.md)
- **agent.md 버전**: v4.0.54 ✅ (일치)
- **run_pipeline.py 버전**: v4.0.44 (스크립트 내부 주석)
- **pipeline_config.yaml 버전**: 2.0.0 (다른 버전 체계)

### 결론
`agent.md`는 프로젝트 문서 버전(v4.0.54)과 일치합니다. `run_pipeline.py`와 `pipeline_config.yaml`의 버전은 다른 버전 체계를 사용하므로 불일치는 정상입니다.

## ✅ 완료된 작업

### 1. 버전 확인
- ✅ 프로젝트 문서 버전 확인: v4.0.54
- ✅ agent.md 버전 확인: v4.0.54 (일치)
- ✅ 버전 불일치 분석 완료

### 2. agent.md 수정
- ✅ `--contamination` 플래그 제거 (실제로는 config 파일에서 설정)
- ✅ 주석으로 변경: `# contamination은 config/stage4_anomaly.yaml에서 설정 (기본값: 0.02)`

### 3. 미러 파일 생성
- ✅ `AGENTS.md` 생성 (대문자, 업계 표준)
- ✅ `agents.md` 동기화 확인 (소문자, 기존 파일)

### 4. 검증
- ✅ `audit_agent_md.py`: 모든 검증 통과
- ✅ `sync_agent_docs.py`: 동기화 완료

## 📁 파일 상태

| 파일명 | 상태 | 크기 | 최종 수정 |
|--------|------|------|----------|
| `agent.md` | SSOT (원본) | 8,479 bytes | 2026-01-25 |
| `AGENTS.md` | 미러 (대문자) | 동일 | 동기화됨 |
| `agents.md` | 미러 (소문자) | 8,481 bytes | 동기화됨 |

## 🔄 동기화 명령어

### 미래 갱신 시 사용
```bash
# agent.md 수정 후 AGENTS.md 동기화
python hvdc-agentmd/scripts/sync_agent_docs.py --from-path agent.md --to-path AGENTS.md --write

# agents.md 동기화
python hvdc-agentmd/scripts/sync_agent_docs.py --from-path agent.md --to-path agents.md --write

# 검증
python hvdc-agentmd/scripts/audit_agent_md.py --path agent.md
python hvdc-agentmd/scripts/audit_agent_md.py --path AGENTS.md
```

## 📝 권장 사항

1. **SSOT 원칙**: `agent.md`를 단일 진실의 원천(SSOT)으로 유지
2. **자동 동기화**: PR 시 자동으로 미러 파일 동기화 검증
3. **버전 관리**: 파이프라인 버전 업데이트 시 `agent.md` 버전도 함께 업데이트

## ⚠️ 주의사항

- `run_pipeline.py`의 버전(v4.0.44)은 스크립트 자체 버전이며, 프로젝트 버전과 다를 수 있습니다.
- `pipeline_config.yaml`의 버전(2.0.0)은 설정 파일 버전 체계로, 프로젝트 버전과 별개입니다.
- `agent.md`는 프로젝트 문서 버전(v4.0.54)을 따릅니다.
