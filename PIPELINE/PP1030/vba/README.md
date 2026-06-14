# HVDC 파이프라인 Excel 런처 설정 가이드 (v1.0 레거시)

## ⚠️ 중요: 이 문서는 v1.0 레거시 버전입니다

**현재 권장 버전**: [README_v2.md](README_v2.md) (v3.0, p3+p4+p5 통합)

이 문서는 초기 버전(`modPipelineLauncher.bas`) 기준으로 작성되었습니다. 새로운 프로젝트는 `modHVDC_CONTROL.bas` (v3.0)를 사용하시기 바랍니다.

## 개요

이 폴더에는 HVDC 파이프라인을 Excel에서 실행할 수 있도록 하는 VBA 런처 파일들이 포함되어 있습니다.

## 파일 목록

- **`modPipelineLauncher.bas`**: VBA 모듈 파일 (v1.0, 레거시)
- **`modHVDC_CONTROL.bas`**: VBA 모듈 파일 (v3.0, 권장) ⭐
- **`CONTROL_SHEET_TEMPLATE.csv`**: CONTROL 시트 데이터 템플릿 (v1.0용)
- **`README.md`**: 이 파일 (v1.0 사용 가이드)
- **`README_v2.md`**: v3.0 사용 가이드 (권장) ⭐

## 설정 단계

### 1. Excel 파일 준비

1. 새 Excel 파일 생성
2. **파일 형식**: Excel 매크로 사용 통합 문서 (`.xlsm`)
3. **파일명**: `HVDC_Pipeline_Launcher.xlsm` (권장)

### 2. VBA 모듈 임포트

1. **VBE 열기**: `Alt + F11`
2. **모듈 추가**: 
   - 삽입 → 모듈
   - 또는 프로젝트 탐색기에서 우클릭 → 삽입 → 모듈
3. **모듈 이름 변경**:
   - 속성 창에서 `modPipelineLauncher`로 변경
   - (속성 창이 보이지 않으면 `F4` 키)
4. **코드 붙여넣기**:
   - `modPipelineLauncher.bas` 파일의 내용을 전체 복사
   - VBE의 코드 창에 붙여넣기
5. **저장**: `Ctrl + S` (Excel 파일 저장)

### 3. CONTROL 시트 생성

1. **새 시트 생성**: 시트 탭에서 `+` 버튼 클릭
2. **시트 이름 변경**: `CONTROL`로 변경
3. **데이터 입력**:

   **방법 A: CSV 템플릿 사용 (권장)**
   - Excel에서 `CONTROL_SHEET_TEMPLATE.csv` 파일 열기
   - 데이터 복사 (A1부터)
   - CONTROL 시트의 A1 셀에 붙여넣기
   - B열 값 확인 및 필요시 수정

   **방법 B: 수동 입력**
   - A열에 레이블, B열에 값 입력 (아래 표 참조)

| A열 (레이블) | B열 (값) | 설명 |
|-------------|---------|------|
| ProjectRoot | `C:\PP1030` | 프로젝트 루트 경로 |
| PythonExe | `py` | Python 실행 파일 (`py`, `python`, 또는 전체 경로) |
| Stage1Script | `run\run_pipeline.py --stage 1` | Stage 1 실행 명령 |
| Stage2Script | `run\run_pipeline.py --stage 2` | Stage 2 실행 명령 |
| Stage3Script | `run\run_pipeline.py --stage 3` | Stage 3 실행 명령 |
| Stage4Script | `run\run_pipeline.py --stage 4` | Stage 4 실행 명령 |
| ArgsStage1 | (비워둠) | Stage 1 추가 옵션 |
| ArgsStage2 | (비워둠) | Stage 2 추가 옵션 |
| ArgsStage3 | (비워둠) | Stage 3 추가 옵션 |
| ArgsStage4 | `--stage4-visualize` | Stage 4 추가 옵션 (선택) |
| (빈 행) | | |
| OpenAfterRun | `TRUE` | 실행 완료 후 폴더 자동 열기 |

### 4. LOG 시트 생성 (자동 생성됨)

- LOG 시트는 VBA 코드가 자동으로 생성합니다.
- 수동으로 생성할 필요는 없지만, 필요시 수동 생성도 가능합니다.
- 컬럼: `Timestamp | Level | Proc | Message | Ref`

### 5. 버튼 생성 및 매크로 연결

1. **개발자 탭 활성화** (필요시):
   - 파일 → 옵션 → 리본 사용자 지정
   - "개발자" 체크박스 선택 → 확인

2. **CONTROL 시트로 이동**

3. **버튼 추가**:
   - 개발자 → 삽입 → 양식 컨트롤 → 단추(양식 컨트롤)
   - CONTROL 시트에 드래그하여 버튼 생성

4. **버튼 5개 생성 및 매크로 연결**:
   - **"Run Stage 1"** → 우클릭 → 매크로 지정 → `Run_Stage1` 선택
   - **"Run Stage 2"** → 우클릭 → 매크로 지정 → `Run_Stage2` 선택
   - **"Run Stage 3"** → 우클릭 → 매크로 지정 → `Run_Stage3` 선택
   - **"Run Stage 4"** → 우클릭 → 매크로 지정 → `Run_Stage4` 선택
   - **"Run All"** → 우클릭 → 매크로 지정 → `Run_All` 선택

5. **버튼 배치** (권장):
   - 위치: D열~H열, 2행~6행
   - 크기: 각 버튼 너비 100px, 높이 30px
   - 정렬: 가로로 나란히 배치

### 6. 파일 저장

- `Ctrl + S`로 Excel 파일 저장
- `.xlsm` 형식으로 저장되었는지 확인

## 사용 방법

### 개별 Stage 실행

1. CONTROL 시트에서 해당 Stage 버튼 클릭
2. Excel 하단 상태 표시줄에 "Running Stage X ..." 표시
3. 실행 완료 후 LOG 시트에서 결과 확인

### 전체 파이프라인 실행

1. "Run All" 버튼 클릭
2. Stage 1 → Stage 2 → Stage 3 → Stage 4 순차 실행
3. 중간에 실패하면 해당 Stage에서 중단

### 로그 확인

- **LOG 시트**: Excel 내부 로그 (타임스탬프, 레벨, 프로세스, 메시지, 참조)
- **로그 파일**: `logs\pipeline_YYYYMMDD_HHMMSS.log` (프로젝트 루트의 logs 폴더)

## 출력 파일 경로

실행 성공 시 다음 파일들이 생성됩니다:

- **Stage 1**: 
  - `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx` (멀티시트)
  - `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx` (병합 파일)

- **Stage 2**: 
  - `data\processed\derived\HVDC WAREHOUSE_HITACHI(HE).xlsx`

- **Stage 3**: 
  - `data\processed\reports\HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx` (12개 시트)

- **Stage 4**: 
  - `data\anomaly\HVDC_anomaly_report.xlsx`
  - `data\anomaly\HVDC_anomaly_report.json`

## 문제 해결

### 일반적인 오류

#### 1. "스크립트 파일이 없습니다"
- **원인**: `StageXScript` 경로가 잘못됨
- **해결**: 
  - B4~B7 셀의 경로 확인
  - `run\run_pipeline.py` 파일이 프로젝트 루트에 있는지 확인
  - 프로젝트 루트 경로(B2)가 올바른지 확인

#### 2. "ProjectRoot(B2)가 비어있습니다"
- **원인**: B2 셀이 비어있음
- **해결**: B2에 프로젝트 루트 경로 입력 (예: `C:\PP1030`)

#### 3. Python 실행 오류
- **원인**: Python이 PATH에 없거나 가상환경 경로가 잘못됨
- **해결**: 
  - B3에 `py`, `python`, 또는 전체 경로 입력
  - 명령 프롬프트에서 `py --version` 또는 `python --version`으로 확인

#### 4. "CONTROL 시트가 없습니다"
- **원인**: CONTROL 시트가 생성되지 않음
- **해결**: 시트 이름이 정확히 `CONTROL`인지 확인 (대소문자 구분)

#### 5. Stage 실행 실패 (ExitCode != 0)
- **원인**: Python 스크립트 실행 중 오류 발생
- **해결**: 
  - LOG 시트에서 오류 메시지 확인
  - `logs\pipeline_*.log` 파일 확인
  - Python 스크립트를 직접 실행하여 오류 확인

### 디버깅 팁

1. **LOG 시트 확인**: 각 실행마다 타임스탬프와 함께 로그 기록
2. **로그 파일 확인**: `logs\pipeline_YYYYMMDD_HHMMSS.log` 파일 확인
3. **StatusBar 확인**: Excel 하단 상태 표시줄에 실행 상태 표시
4. **수동 실행 테스트**: 명령 프롬프트에서 직접 Python 스크립트 실행하여 문제 확인

## 추가 옵션

### Stage 4 시각화 옵션

- **색상 시각화 활성화**: B11에 `--stage4-visualize` 입력
- **색상 시각화 비활성화**: B11에 `--stage4-no-visualize` 입력
- **기본값**: 비워두면 설정 파일의 기본값 사용

### 실행 후 폴더 자동 열기

- **활성화**: B13에 `TRUE` 입력
- **비활성화**: B13에 `FALSE` 입력 또는 비워두기

## 참고 문서

- **상세 기술 문서**: `docs\technical\vba.md`
- **파이프라인 개요**: `docs\common\PIPELINE_OVERVIEW.md`
- **Stage별 가이드**: `docs\common\STAGE_BY_STAGE_GUIDE.md`

## 지원

문제가 발생하면 다음을 확인하세요:

1. Excel 파일이 `.xlsm` 형식으로 저장되었는지
2. VBA 모듈이 정상적으로 임포트되었는지
3. CONTROL 시트의 모든 필수 셀이 채워졌는지
4. Python 및 프로젝트 경로가 올바른지

## v3.0으로 마이그레이션

새로운 프로젝트나 기존 프로젝트 업그레이드를 원하시면:

1. **[README_v2.md](README_v2.md) 참조** - v3.0 가이드
2. **`modHVDC_CONTROL.bas` 사용** - YAML 자동 생성, LED 상태보드, 에러 매핑 등 추가 기능
3. **기존 설정 마이그레이션** - CONTROL 시트 데이터를 새 레이아웃에 복사

---

**최종 업데이트**: 2025-12-21  
**버전**: v1.0 (레거시)  
**현재 권장 버전**: v3.0 ([README_v2.md](README_v2.md) 참조)

