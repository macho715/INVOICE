## HVDC 파이프라인 Excel 런처 실행 방법

### Step 1: Excel 파일 준비

1. Excel 파일 열기
   - `C:\PP1030\vba\HVDC_Pipeline_Launcher.xlsx` 열기
   - 또는 새 `.xlsm` 파일 생성

2. `.xlsm` 형식으로 저장 (필요시)
   - 파일 > 다른 이름으로 저장
   - 파일 형식: Excel 매크로 사용 통합 문서 (*.xlsm)
   - 저장

### Step 2: VBA 모듈 임포트

1. VBE 열기: `Alt + F11`
2. 모듈 추가:
   - 삽입 → 모듈
   - 또는 프로젝트 탐색기에서 우클릭 → 삽입 → 모듈
3. 모듈 이름 변경:
   - 속성 창(F4)에서 `modHVDC_CONTROL`로 변경
4. 코드 붙여넣기:
   - `C:\PP1030\vba\modHVDC_CONTROL.bas` 파일 열기
   - 전체 내용 복사 (Ctrl+A, Ctrl+C)
   - VBE 코드 창에 붙여넣기 (Ctrl+V)
5. 저장: `Ctrl + S` (Excel 파일 저장)

### Step 3: 템플릿 초기화

1. Excel로 돌아가기: `Alt + F11` (또는 Excel 창 클릭)
2. 매크로 실행:
   - `Alt + F8` (또는 개발 도구 > 매크로)
   - `CTRL_Install` 선택
   - 실행
3. 확인:
   - "CONTROL 템플릿 생성 완료" 메시지 확인
   - CONTROL 시트와 LOG 시트 생성 확인
   - 버튼 자동 생성 확인

### Step 4: 필수 경로 설정

CONTROL 시트에서 다음 셀 입력:

| 셀 | 항목 | 값 예시 | 필수 |
|----|------|---------|------|
| **B4** | Project Root | `C:\PP1030` | ✅ |
| **B5** | Config Dir | (자동 계산됨) | - |
| **B6** | pipeline_config.yaml | (자동 계산됨) | - |
| **B7** | stage2_derived_config.yaml | (자동 계산됨) | - |
| **B8** | stage4_anomaly.yaml | (자동 계산됨) | - |
| **B9** | Python EXE | `py` 또는 `C:\Python311\python.exe` | ✅ |
| **B10** | Scripts Dir | (자동 계산됨) | - |
| **B11** | Validator Py | (자동 계산됨) | - |
| **B12** | Log Dir | (자동 계산됨) | - |

Stage1 입력 파일 (필요시):
- **B16**: Master File (`auto` 또는 경로)
- **B17**: Warehouse File (`data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx`)

### Step 5: YAML 생성 및 저장

1. `02) YAML 저장(+백업)` 버튼 클릭 (F3)
2. 확인:
   - "YAML 저장(+백업) 완료" 메시지
   - `config\pipeline_config.yaml` 생성 확인
   - `config\stage2_derived_config.yaml` 생성 확인
   - `config\stage4_anomaly.yaml` 생성 확인
   - `config\_backup\` 폴더에 백업 생성 확인

### Step 6: 파이프라인 실행

#### 방법 A: 개별 Stage 실행

1. Stage 1 실행
   - `▶ Run Stage 1` 버튼 클릭 (F5)
   - 실행 완료 메시지 확인
   - StatusBar에서 진행 상태 확인

2. Stage 2 실행
   - `▶ Run Stage 2` 버튼 클릭 (F6)
   - 실행 완료 메시지 확인

3. Stage 3 실행
   - `▶ Run Stage 3` 버튼 클릭 (F7)
   - 실행 완료 메시지 확인

4. Stage3 → Stage4 Publish
   - `📤 Publish Latest → Stage4` 버튼 클릭 (F8)
   - 최신 리포트 자동 탐색 및 설정
   - YAML 자동 저장 확인

5. Stage 4 실행
   - `▶ Run Stage 4` 버튼 클릭 (F9)
   - 실행 완료 메시지 확인

#### 방법 B: 전체 실행 (수동)

각 Stage를 순서대로 실행:
1. Run Stage 1 → 완료 대기
2. Run Stage 2 → 완료 대기
3. Run Stage 3 → 완료 대기
4. Publish Latest → Stage4 → 완료 대기
5. Run Stage 4 → 완료 대기

### Step 7: 결과 확인

1. 출력 파일 확인:
   - Stage 1: `data\processed\synced\*.xlsx`
   - Stage 2: `data\processed\derived\*.xlsx`
   - Stage 3: `data\processed\reports\HVDC_입고로직_종합리포트_*.xlsx`
   - Stage 4: `data\anomaly\HVDC_anomaly_report.xlsx`

2. 로그 확인:
   - LOG 시트: Excel 내부 로그
   - 로그 파일: `logs\stageX_YYYYMMDD_HHMMSS.log`

3. YAML 확인:
   - `config\pipeline_config.yaml`
   - `config\stage2_derived_config.yaml`
   - `config\stage4_anomaly.yaml`

## 버튼 위치 및 기능

| 위치 | 버튼 | 기능 |
|------|------|------|
| F2 | 01) TEMPLATE 생성 | CONTROL/LOG 시트 재생성 |
| F3 | 02) YAML 저장(+백업) | YAML 3종 생성 및 백업 |
| F4 | 03) Config 검증(Python) | YAML 검증 (선택) |
| F5 | ▶ Run Stage 1 | Stage 1 실행 |
| F6 | ▶ Run Stage 2 | Stage 2 실행 |
| F7 | ▶ Run Stage 3 | Stage 3 실행 |
| F8 | 📤 Publish Latest → Stage4 | Stage3 최신 리포트 → Stage4 Input |
| F9 | ▶ Run Stage 4 | Stage 4 실행 |

## 문제 해결

### "Python EXE 경로가 유효하지 않습니다"
- B9 셀에 올바른 Python 경로 입력
- `py` 또는 전체 경로 (`C:\Python311\python.exe`)

### "run_pipeline.py를 찾을 수 없습니다"
- B4 (Project Root) 경로 확인
- `run\run_pipeline.py` 파일 존재 확인

### "Stage3 리포트를 찾을 수 없습니다"
- Stage3 실행 완료 확인
- B40 (Report Pattern) 경로 확인
- `data\processed\reports\` 폴더에 리포트 파일 존재 확인

### 버튼이 보이지 않음
- `CTRL_Install` 실행하여 버튼 재생성

## 빠른 체크리스트

- [ ] Excel 파일 열기 (`.xlsm` 형식)
- [ ] VBA 모듈 임포트 (`modHVDC_CONTROL.bas`)
- [ ] `CTRL_Install` 실행
- [ ] B4에 Project Root 입력
- [ ] B9에 Python EXE 입력
- [ ] `02) YAML 저장(+백업)` 클릭
- [ ] `▶ Run Stage 1~4` 순서대로 실행
- [ ] `📤 Publish Latest → Stage4` 클릭 (Stage3 후)

모든 단계를 완료하면 Excel에서 파이프라인을 실행할 수 있습니다.