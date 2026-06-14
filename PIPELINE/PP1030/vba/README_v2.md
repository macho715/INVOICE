# HVDC 파이프라인 Excel 런처 v3.0 (p3+p4+p5 통합)

**작성일**: 2025-12-21  
**버전**: v3.0  
**기반**: p3.md + p4.md + p5.md 통합 설계

---

## 개요

p3.md (YAML 관리), p4.md (파이프라인 운영 콘솔), p5.md (LED 상태보드) 설계를 통합한 Excel 기반 파이프라인 제어 시스템입니다. Excel CONTROL 시트에서 YAML 설정 자동 생성, Stage 실행, 상태 모니터링을 한 번에 수행할 수 있습니다.

## 주요 특징

### ✅ p3.md 기반: YAML 자동 관리

1. **YAML 3종 자동 생성**
   - `pipeline_config.yaml` (Stage 1, 3 설정)
   - `stage2_derived_config.yaml` (Stage 2 설정)
   - `stage4_anomaly.yaml` (Stage 4 설정)

2. **YAML 백업 기능**
   - 저장 전 기존 YAML을 `_backup` 폴더로 자동 백업
   - 타임스탬프 포함 파일명

3. **Config 검증**
   - Python `config_validator.py`를 통한 자동 검증
   - 경로 존재 여부, 패턴 매칭 확인

### ✅ p4.md 기반: 파이프라인 운영 콘솔

1. **Stage 실행 버튼**
   - `[RUN] Stage1~4`: 개별 Stage 실행
   - `[RUN ALL] 1→4`: 전체 파이프라인 순차 실행
   - `[PUBLISH] S3→S4`: Stage3 최신 리포트 → Stage4 Input 자동 설정

2. **실행 상태 표시**
   - StatusBar에 실시간 경과 시간 표시
   - 로그 파일 자동 생성 (`logs\stageX_YYYYMMDD_HHMMSS.log`)

3. **에러 코드 매핑**
   - Python Exit Code → 사용자 친화적 메시지
   - Exit Code 10~90 범위별 상세 메시지

### ✅ p5.md 기반: LED 상태보드

1. **LED 상태 표시 (E:H열)**
   - `[ ]` 대기 (LED_IDLE)
   - `[*]` 실행중 (LED_RUNNING)
   - `[OK]` 성공 (LED_OK)
   - `[X]` 실패 (LED_FAIL)

2. **상태보드 자동 업데이트**
   - Stage별 실행 상태 실시간 반영
   - 마지막 실행 시간 기록
   - 결과 파일 하이퍼링크 자동 생성

3. **Artifact 링크**
   - 실행 성공 시 결과 파일 경로를 하이퍼링크로 표시
   - 클릭 시 파일 자동 열기

## 파일 구조

```
vba/
├── modHVDC_CONTROL.bas      # ✅ 통합 VBA 모듈 (p3+p4+p5)
├── modPipelineLauncher.bas   # 기존 모듈 (v1.0, 호환성 유지)
├── python_bridge.py         # xlwings 브리지 (선택적)
├── README.md                # v1.0 가이드 (레거시)
├── README_v2.md             # 이 문서 (v3.0 가이드)
├── P3_INTEGRATION_SUMMARY.md
├── P4_INTEGRATION_SUMMARY.md
├── P5_INTEGRATION_SUMMARY.md
└── CONTROL_SHEET_TEMPLATE.csv  # 참고용 템플릿
```

## 빠른 시작

### 1. Excel 파일 준비

1. 새 Excel 파일 생성 (`.xlsm` 형식)
2. 파일명: `HVDC_Pipeline_Launcher.xlsm` (권장)

### 2. VBA 모듈 임포트

1. **VBE 열기**: `Alt + F11`
2. **모듈 추가**: 삽입 → 모듈
3. **모듈 이름**: `modHVDC_CONTROL`
4. **코드 붙여넣기**: `vba/modHVDC_CONTROL.bas` 내용 전체 복사
5. **저장**: `Ctrl + S`

### 3. 템플릿 초기화

1. Excel로 돌아가기
2. **매크로 실행**: `Alt + F8` → `CTRL_Install` 선택 → 실행
3. CONTROL/LOG 시트 자동 생성 확인

### 4. 필수 설정 입력

CONTROL 시트에서 다음 입력:

| 셀 | 이름 정의 | 값 예시 | 필수 |
|----|----------|---------|------|
| B4 | `cfg_project_root` | `C:\PP1030` | ✅ |
| B9 | `cfg_python_exe` | `py` | ✅ |
| B16 | `st1_master_file` | `C:\...\Case List*.xlsx` | ✅ |
| B17 | `st1_warehouse_file` | `C:\...\HVDC WAREHOUSE_*.xlsx` | ✅ |

### 5. YAML 저장

1. `[SAVE] YAML 반영(백업)` 버튼 클릭
2. YAML 3종 자동 생성 및 백업 확인
3. 상태보드에서 `CONFIG_SYNC` LED가 `[OK]`로 변경 확인

### 6. 실행

1. **전체 실행**: `[RUN ALL] 1→4` 버튼 클릭
2. **개별 실행**: `[RUN] Stage1`, `[RUN] Stage2` 등 버튼 클릭
3. **Publish**: Stage3 완료 후 `[PUBLISH] S3→S4` 버튼 클릭

## CONTROL 시트 레이아웃

### 입력 영역 (A:C열)

**1) PATH SETTINGS (A3:C3)**
- **B4**: Project Root (프로젝트 루트 경로)
- **B5**: Config Dir (자동 계산: `B4\config`)
- **B6**: pipeline_config.yaml (자동 계산)
- **B7**: stage2_derived_config.yaml (자동 계산)
- **B8**: stage4_anomaly.yaml (자동 계산)
- **B9**: Python EXE (`py` 또는 `python.exe`)
- **B10**: Scripts Dir (자동 계산: `B4\scripts`)
- **B11**: Validator Py (자동 계산: `B4\tools\config_validator.py`)
- **B12**: Log Dir (자동 계산: `B4\logs`)

**2) STAGE 1 (A14:C14)**
- **B15**: Enabled (TRUE/FALSE)
- **B16**: Master File (경로 또는 "auto")
- **B17**: Warehouse File (상대 경로)
- **B18**: Output File (multi-sheet)
- **B19**: Output File (merged, 자동 계산)
- **B20**: Include Patterns (1줄=1항목)
- **B25~B29**: Sorting, Strict Case Key 등 옵션

**3) STAGE 2 (A31:C31)**
- **B32**: Synced(merged) Input (자동: `B19`)
- **B33**: Derived Output
- **B34**: Preserve Colors
- **B35**: Backup Enabled

**4) STAGE 3 (A37:C37)**
- **B38**: Enabled
- **B39**: Derived File (자동: `B33`)
- **B40**: Report Pattern
- **A44:D44**: Warehouse 테이블 (BaseCapacitySQM, BillingMode, SqmRate)

**5) STAGE 4 (A62:C62)**
- **B63**: Enabled
- **B64**: Report File (Stage3 리포트 경로)
- **B65**: Anomaly Output
- **B66**: Visualize Enabled

### 상태보드 영역 (E:H열)

**헤더 (E4:H4)**
- E4: STAGE
- F4: LED
- G4: LAST_RUN
- H4: MESSAGE / ARTIFACT

**상태 행 (E5:H10)**
- 행 5: CONFIG_SYNC (YAML 저장 상태)
- 행 6: STAGE1
- 행 7: STAGE2
- 행 8: STAGE3
- 행 9: PUBLISH
- 행 10: STAGE4

**LED 상태**
- `[ ]`: 대기 (LED_IDLE)
- `[*]`: 실행중 (LED_RUNNING)
- `[OK]`: 성공 (LED_OK)
- `[X]`: 실패 (LED_FAIL)

### 버튼 영역 (J:L열)

**헤더 (J3:L3)**: ACTIONS

**버튼 (J4:J12)**
- J4: `[SETUP] CONTROL` → `CTRL_Install`
- J5: `[SAVE] YAML 반영(백업)` → `CTRL_SaveAllYAML`
- J6: `[RUN] Stage1` → `BTN_RunStage1`
- J7: `[RUN] Stage2` → `BTN_RunStage2`
- J8: `[RUN] Stage3` → `BTN_RunStage3`
- J9: `[PUBLISH] S3→S4` → `BTN_PublishStage3To4`
- J10: `[RUN] Stage4` → `BTN_RunStage4`
- J11: `[RUN ALL] 1→4` → `BTN_RunAll`
- J12: `[LOGS] Open` → `BTN_OpenLogsFolder`

**Browse 버튼 (C열)**
- C4: Project Root Browse
- C9: Python EXE Browse
- C16: Master File Browse
- C17: Warehouse File Browse

## 버튼 기능

| 버튼 | 매크로 | 기능 |
|------|--------|------|
| `[SETUP] CONTROL` | `CTRL_Install` | CONTROL/LOG 시트 재생성 |
| `[SAVE] YAML 반영(백업)` | `CTRL_SaveAllYAML` | YAML 3종 생성 및 백업 |
| `[RUN] Stage1` | `BTN_RunStage1` | Stage 1만 실행 |
| `[RUN] Stage2` | `BTN_RunStage2` | Stage 2만 실행 |
| `[RUN] Stage3` | `BTN_RunStage3` | Stage 3만 실행 |
| `[PUBLISH] S3→S4` | `BTN_PublishStage3To4` | Stage3 최신 리포트 → Stage4 Input 설정 |
| `[RUN] Stage4` | `BTN_RunStage4` | Stage 4만 실행 |
| `[RUN ALL] 1→4` | `BTN_RunAll` | Stage 1~4 순차 실행 (Publish 포함) |
| `[LOGS] Open` | `BTN_OpenLogsFolder` | 로그 폴더 열기 |

## 실행 흐름

### YAML 저장 시

1. **백업 생성**
   - 기존 YAML 파일을 `config\_backup\` 폴더로 복사
   - 타임스탬프 포함 파일명

2. **YAML 생성**
   - CONTROL 시트 값 기반으로 YAML 3종 생성
   - `pipeline_config.yaml`, `stage2_derived_config.yaml`, `stage4_anomaly.yaml`

3. **검증**
   - Python `config_validator.py` 실행
   - 경로 존재 여부, 패턴 매칭 확인

4. **상태보드 업데이트**
   - `CONFIG_SYNC` LED: `[*]` → `[OK]` 또는 `[X]`
   - 실행 시간, 메시지 기록

### Stage 실행 시

1. **검증**
   - Python EXE 경로 확인
   - Project Root 경로 확인
   - `run\run_pipeline.py` 존재 확인

2. **Python 실행**
   - `py run\run_pipeline.py --stage X`
   - 로그: `logs\stageX_YYYYMMDD_HHMMSS.log`

3. **상태보드 업데이트**
   - 해당 Stage LED: `[*]` → `[OK]` 또는 `[X]`
   - 실행 시간, 결과 파일 경로 기록
   - 결과 파일이 존재하면 하이퍼링크 생성

### Publish 시

1. **Stage3 리포트 검색**
   - Report Pattern에서 폴더 경로 추출
   - `HVDC_입고로직_종합리포트_*.xlsx` 패턴으로 파일 검색
   - 최종 수정일 기준 최신 파일 선택

2. **Stage4 Input 설정**
   - Stage4 Input에 상대 경로로 설정
   - YAML 자동 재저장

3. **상태보드 업데이트**
   - `PUBLISH` LED: `[*]` → `[OK]` 또는 `[X]`
   - 실행 시간, 파일 경로 기록

## 출력 파일 경로

실행 성공 시 다음 파일들이 생성되고 상태보드에 자동 반영됩니다:

- **Stage 1**:
  - Main: `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`
  - Extra: `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx`

- **Stage 2**:
  - Main: `data\processed\derived\HVDC WAREHOUSE_HITACHI(HE).xlsx`

- **Stage 3**:
  - Main: `data\processed\reports\HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx`

- **Stage 4**:
  - Main: `data\anomaly\HVDC_anomaly_report.xlsx`

## 에러 코드 매핑

Python Exit Code가 다음 메시지로 변환됩니다:

- **Exit Code 10**: CONFIG 오류 (YAML 파싱/경로 누락)
- **Exit Code 11**: 입력 파일 없음/패턴 매칭 실패
- **Exit Code 12**: 출력/로그 폴더 생성 실패
- **Exit Code 20**: Stage1 실행 실패
- **Exit Code 30**: Stage2 실행 실패
- **Exit Code 40**: Stage3 실행 실패
- **Exit Code 50**: Stage4 실행 실패
- **Exit Code 60**: Publish 실패
- **Exit Code 90**: 예상치 못한 오류

## 문제 해결

### "이름 정의를 찾을 수 없습니다"

**원인**: CONTROL 시트가 템플릿으로 초기화되지 않음

**해결**: 
1. `Alt + F8` → `CTRL_Install` 실행
2. 또는 버튼 `[SETUP] CONTROL` 클릭

### "Master File이 유효하지 않습니다"

**원인**: B16 셀에 올바른 파일 경로가 입력되지 않음

**해결**: 
1. B16 셀에 `Case List*.xlsx` 파일 경로 입력
2. 또는 "auto" 입력 (자동 검색)
3. `C16` Browse 버튼 사용

### "Stage 스크립트를 찾지 못했습니다"

**원인**: Project Root 경로가 잘못됨

**해결**: 
1. B4 셀에 올바른 프로젝트 루트 경로 입력 (예: `C:\PP1030`)
2. `run\run_pipeline.py` 파일이 존재하는지 확인

### LED가 업데이트되지 않음

**원인**: 상태보드 레이아웃이 손상됨

**해결**: 
1. `CTRL_Install` 실행하여 레이아웃 재생성
2. 기존 설정값은 유지됨 (이름 정의 기반)

## 기존 모듈과의 차이점

| 기능 | modPipelineLauncher (v1) | modHVDC_CONTROL (v3) |
|------|-------------------------|----------------------|
| 기반 설계 | vba.md | p3.md + p4.md + p5.md |
| YAML 자동 생성 | ❌ | ✅ |
| YAML 백업 | ❌ | ✅ |
| LED 상태보드 | ❌ | ✅ |
| 에러 코드 매핑 | ❌ | ✅ |
| Publish 기능 | ❌ | ✅ |
| 이름 정의(Name) | ❌ | ✅ |
| Browse 버튼 | ❌ | ✅ |
| 실행 방식 | `run_pipeline.py --stage X` | `run_pipeline.py --stage X` |

## 마이그레이션

기존 `modPipelineLauncher.bas` 사용자라면:

1. **새 모듈 추가**: `modHVDC_CONTROL.bas` 임포트
2. **템플릿 초기화**: `CTRL_Install` 실행
3. **데이터 복사**: 기존 CONTROL 시트 데이터를 새 레이아웃에 맞게 복사
4. **버튼 업데이트**: 기존 버튼 매크로 연결 변경 또는 새 버튼 사용

## 참고 문서

- [p3.md 설계 문서](p3.md) - YAML 관리
- [p4.md 설계 문서](p4.md) - 파이프라인 운영 콘솔
- [p5.md 설계 문서](p5.md) - LED 상태보드
- [P3_INTEGRATION_SUMMARY.md](P3_INTEGRATION_SUMMARY.md)
- [P4_INTEGRATION_SUMMARY.md](P4_INTEGRATION_SUMMARY.md)
- [P5_INTEGRATION_SUMMARY.md](P5_INTEGRATION_SUMMARY.md)
- [기존 가이드 (v1)](README.md)
- [xlwings 통합 가이드](XLWINGS_INTEGRATION_GUIDE.md) (선택적)

---

**최종 업데이트**: 2025-12-21  
**버전**: v3.0 (p3+p4+p5 통합)
