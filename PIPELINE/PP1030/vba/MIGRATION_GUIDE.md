# VBA 런처 마이그레이션 가이드

**작성일**: 2025-12-21  
**버전**: v2.0 (p2.md 기반 완전 교체)  
**상태**: ✅ 완료

---

## 개요

기존 `modPipelineLauncher.bas`를 p2.md 기반의 고급 설계로 완전 교체한 `modPipelineControl.bas`로 업그레이드합니다.

## 주요 변경사항

### 1. 구조 개선

#### 기존 (modPipelineLauncher.bas)
- 간단한 셀 주소 직접 참조 (B2, B3, ...)
- 기본 실행 기능만

#### 신규 (modPipelineControl.bas)
- **이름 정의(Name) 사용**: `n_ProjectRoot`, `n_PythonExe` 등
- **템플릿 자동 생성**: `UI_InitTemplate` 버튼으로 CONTROL/LOG 시트 자동 생성
- **Stage 표**: Stage별 Enabled/LastRun/Output 표시
- **출력 경로 자동 업데이트**: 실행 후 자동으로 최신 경로 반영

### 2. 실행 방식

#### 기존
- 개별 스크립트 직접 호출 (가정)
- `--config` 옵션 필요

#### 신규
- **통합 진입점 사용**: `run\run_pipeline.py --stage X`
- 설정 파일 자동 로드 (--config 불필요)
- 추가 옵션만 지원 (예: `--stage4-visualize`)

### 3. 추가 기능

1. **raw 파일 자동 복사/백업**
   - Stage1 실행 전 Master/Warehouse 파일을 `data/raw`로 자동 복사
   - 기존 파일은 `_backup` 폴더로 백업

2. **출력 경로 자동 감지**
   - Stage3: 패턴 매칭으로 최신 리포트 파일 찾기
   - Stage4: 여러 가능한 경로 중 존재하는 파일 선택

3. **실행 시간 표시**
   - StatusBar에 실시간 경과 시간 표시

4. **추가 버튼**
   - `INIT / RESET`: 템플릿 초기화
   - `Open Latest Output`: 최신 결과 파일 열기
   - `Open Log Folder`: 로그 폴더 열기
   - `Clear LOG`: LOG 시트 클리어

## 마이그레이션 단계

### Step 1: 기존 모듈 백업 (선택)

```vb
' 기존 modPipelineLauncher.bas를 modPipelineLauncher_old.bas로 이름 변경
```

### Step 2: 새 모듈 추가

1. VBE 열기 (Alt+F11)
2. 표준 모듈 추가
3. 모듈 이름: `modPipelineControl`
4. `vba/modPipelineControl.bas` 내용 붙여넣기

### Step 3: 템플릿 초기화

1. Excel로 돌아가기
2. 매크로 실행: `UI_InitTemplate`
3. CONTROL/LOG 시트 자동 생성 확인

### Step 4: 설정 입력

CONTROL 시트에서 다음 필수 항목 입력:

- **B4 (Project Root)**: 프로젝트 루트 경로 (예: `C:\PP1030`)
- **B5 (Python EXE)**: `py` 또는 `python.exe` 경로
- **B11 (Master Folder)**: `Case List*.xlsx` 있는 폴더
- **B12 (Warehouse File)**: 원본 Warehouse Excel 파일

### Step 5: 기존 버튼 업데이트 (필요시)

기존 버튼이 있다면 매크로 연결을 새 함수명으로 변경:

| 기존 매크로 | 신규 매크로 |
|------------|-----------|
| `Run_Stage1` | `UI_RunStage1` |
| `Run_Stage2` | `UI_RunStage2` |
| `Run_Stage3` | `UI_RunStage3` |
| `Run_Stage4` | `UI_RunStage4` |
| `Run_All` | `UI_RunAll` |

또는 `UI_InitTemplate` 실행 시 버튼이 자동 생성됩니다.

## 기능 비교

| 기능 | 기존 (modPipelineLauncher) | 신규 (modPipelineControl) |
|------|---------------------------|--------------------------|
| 템플릿 자동 생성 | ❌ | ✅ |
| 이름 정의(Name) | ❌ | ✅ |
| Stage 표 | ❌ | ✅ |
| raw 파일 복사 | ❌ | ✅ |
| 출력 경로 자동 업데이트 | ❌ | ✅ |
| 실행 시간 표시 | ❌ | ✅ |
| 최신 결과 열기 | ❌ | ✅ |
| 로그 폴더 열기 | ❌ | ✅ |
| LOG 시트 클리어 | ❌ | ✅ |
| 실행 방식 | 개별 스크립트 | `run_pipeline.py` |

## 호환성

### 기존 Excel 파일과의 호환성

- **기존 CONTROL 시트**: 수동으로 새 레이아웃에 맞게 데이터 복사 필요
- **기존 버튼**: 매크로 연결만 변경하면 됨
- **기존 LOG 시트**: 그대로 사용 가능

### 권장 마이그레이션 방법

1. **새 Excel 파일 생성** (권장)
   - 새 `.xlsm` 파일 생성
   - `modPipelineControl.bas` 임포트
   - `UI_InitTemplate` 실행

2. **기존 파일 업데이트**
   - 기존 모듈 백업
   - 새 모듈 추가
   - `UI_InitTemplate` 실행하여 CONTROL 시트 재생성
   - 데이터 수동 복사

## 문제 해결

### "이름 정의를 찾을 수 없습니다"

**원인**: CONTROL 시트가 템플릿으로 초기화되지 않음

**해결**: `UI_InitTemplate` 실행

### "Stage 스크립트를 찾지 못했습니다"

**원인**: Project Root 경로가 잘못됨

**해결**: B4 셀에 올바른 프로젝트 루트 경로 입력

### 버튼이 작동하지 않음

**원인**: 매크로 연결이 잘못됨

**해결**: 
1. 버튼 우클릭 → 매크로 지정
2. 올바른 함수명 선택 (예: `UI_RunStage1`)

## 다음 단계

### 선택적 기능 추가

1. **xlwings 통합**
   - `vba/python_bridge.py`와 연동
   - 실시간 상태 업데이트

2. **Config 자동 반영**
   - CONTROL 시트 입력을 YAML에 자동 반영
   - 백업 포함

3. **고급 모니터링**
   - 진행률 표시
   - 실시간 로그 스트리밍

---

**참고 문서**:
- [p2.md 설계 문서](p2.md)
- [VBA 런처 가이드](../docs/technical/vba.md)
- [xlwings 통합 가이드](XLWINGS_INTEGRATION_GUIDE.md)

