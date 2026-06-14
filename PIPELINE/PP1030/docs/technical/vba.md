아래 설계는 **Stage1~Stage4 파이프라인을 “엑셀 버튼(VBA) → 파이썬 실행 → 결과 파일/로그 갱신”** 구조로 고정해서, 실무자가 엑셀만으로 돌릴 수 있게 만드는 런처(Launcher) 설계입니다. (Stage1 동기화, Stage2 파생컬럼, Stage3 리포트 12시트, Stage4 이상치 탐지/색상표시 흐름 기준)    

---

## 1) 핵심요약(2–4줄)

* **엑셀(Control 시트)에서 경로만 지정하고 버튼 클릭**하면 Stage1~4 파이프라인을 순차 실행하도록 VBA를 설계합니다. 
* 실제 로직(시맨틱 헤더 매칭/63표준헤더/리포트/이상치 탐지)은 파이썬이 담당하고, VBA는 **실행·로그·결과 열기·실패 시 Fail-Safe**만 담당합니다. 
* 기대효과: 운영자는 엑셀 버튼만 사용(경로 오입력/누락 자동 검증, 로그 자동 축적).

---

## 2) 구조(시각화)

```
[CONTROL(경로/옵션)] 
   → (VBA 버튼: Run Stage1/2/3/4/All)
      → cmd/py로 Python 스크립트 실행
         → 결과 파일 생성/갱신( synched / derived / report / anomaly )
            → [LOG 시트 + logs\*.log] 기록
               → (완료 시) 결과 파일/폴더 열기
```

* Stage1: Master + Warehouse 동기화 → 멀티시트 + merged 출력(Stage2 입력) 
* Stage2: 13 파생컬럼 + 63 표준헤더 재정렬 + 검증 
* Stage3: 12개 시트 종합리포트 생성 
* Stage4: Stage3 리포트 기반 이상치 탐지 + (선택) 색상 시각화  

---

## 3) 코드 (VBA 전체 → Python(필요시))

### 3-A) 엑셀 시트 설계 (필수)

**시트 2개를 만드세요.**

1. `CONTROL` 시트 (권장 셀 예시)

**레이아웃 (A열: 레이블, B열: 값)**:

| A열 (레이블) | B열 (값) | 설명 |
|-------------|---------|------|
| ProjectRoot | `C:\PP1030` | 프로젝트 루트 경로 (예: `C:\PP1030` 또는 `D:\HVDC_PIPELINE`) |
| PythonExe | `py` | Python 실행 파일 (예: `py`, `python`, 또는 전체 경로 `C:\PP1030\.venv\Scripts\python.exe`) |
| Stage1Script | `run\run_pipeline.py --stage 1` | Stage 1 실행 명령 (통합 진입점 사용) |
| Stage2Script | `run\run_pipeline.py --stage 2` | Stage 2 실행 명령 |
| Stage3Script | `run\run_pipeline.py --stage 3` | Stage 3 실행 명령 |
| Stage4Script | `run\run_pipeline.py --stage 4` | Stage 4 실행 명령 |
| ArgsStage1 | (비워둠) | Stage 1 추가 옵션 (선택, 설정 파일은 자동 로드됨) |
| ArgsStage2 | (비워둠) | Stage 2 추가 옵션 (선택) |
| ArgsStage3 | (비워둠) | Stage 3 추가 옵션 (선택) |
| ArgsStage4 | `--stage4-visualize` | Stage 4 추가 옵션 (선택, 예: `--stage4-visualize` 또는 `--stage4-no-visualize`) |
| (빈 행) | | |
| OpenAfterRun | `TRUE` | 실행 완료 후 결과 폴더 자동 열기 (TRUE/FALSE)

**셀 주소 매핑**:
* A2, B2: ProjectRoot
* A3, B3: PythonExe
* A4, B4: Stage1Script
* A5, B5: Stage2Script
* A6, B6: Stage3Script
* A7, B7: Stage4Script
* A8, B8: ArgsStage1
* A9, B9: ArgsStage2
* A10, B10: ArgsStage3
* A11, B11: ArgsStage4
* A13, B13: OpenAfterRun

> ⚠️ **중요**: 실제 파이프라인은 `run\run_pipeline.py`를 통합 진입점으로 사용합니다. 설정 파일(`config\pipeline_config.yaml` 등)은 자동으로 로드되므로 `ArgsStageX`는 추가 옵션만 지정하면 됩니다.

2. `LOG` 시트

* A:E 컬럼: `Timestamp | Level | Proc | Message | Ref(명령/파일)`

> ⚠️ **중요**: 실제 파이프라인은 `run\run_pipeline.py`를 통합 진입점으로 사용하며, 설정 파일(`config\pipeline_config.yaml`, `config\stage2_derived_config.yaml` 등)은 자동으로 로드됩니다. `ArgsStageX`는 추가 옵션(예: `--stage4-visualize`, `--stage4-no-visualize`)만 지정하면 됩니다.

---

### 3-B) VBA 모듈 전체 (표준 모듈 `modPipelineLauncher`에 붙여넣기)

```vb
Option Explicit

' ====== Sheet Names ======
Private Const SH_CONTROL As String = "CONTROL"
Private Const SH_LOG As String = "LOG"

' CONTROL sheet cell map
Private Const C_PROJECT_ROOT As String = "B2"
Private Const C_PYTHON_EXE As String = "B3"
Private Const C_STAGE1_SCRIPT As String = "B4"
Private Const C_STAGE2_SCRIPT As String = "B5"
Private Const C_STAGE3_SCRIPT As String = "B6"
Private Const C_STAGE4_SCRIPT As String = "B7"
Private Const C_ARGS_STAGE1 As String = "B8"
Private Const C_ARGS_STAGE2 As String = "B9"
Private Const C_ARGS_STAGE3 As String = "B10"
Private Const C_ARGS_STAGE4 As String = "B11"
Private Const C_OPEN_AFTER As String = "B13"

' ====== Public Macros (assign to buttons) ======
Public Sub Run_Stage1()
    RunStage 1
End Sub

Public Sub Run_Stage2()
    RunStage 2
End Sub

Public Sub Run_Stage3()
    RunStage 3
End Sub

Public Sub Run_Stage4()
    RunStage 4
End Sub

Public Sub Run_All()
    Dim ok As Boolean
    ok = RunStage(1)
    If Not ok Then Exit Sub
    ok = RunStage(2)
    If Not ok Then Exit Sub
    ok = RunStage(3)
    If Not ok Then Exit Sub
    ok = RunStage(4)
    If Not ok Then Exit Sub
End Sub

' ====== Core Runner ======
Private Function RunStage(ByVal stageNo As Long) As Boolean
    On Error GoTo EH

    EnsureSheets
    Application.ScreenUpdating = False
    Application.EnableEvents = False

    Dim wsC As Worksheet: Set wsC = ThisWorkbook.Worksheets(SH_CONTROL)
    Dim root As String: root = Trim$(wsC.Range(C_PROJECT_ROOT).Value2)
    Dim pyExe As String: pyExe = Trim$(wsC.Range(C_PYTHON_EXE).Value2)

    If Len(root) = 0 Then Err.Raise vbObjectError + 101, , "ProjectRoot(B2)가 비어있습니다."
    If Len(pyExe) = 0 Then pyExe = "py"

    Dim relScript As String, args As String
    relScript = GetStageScript(wsC, stageNo)
    args = GetStageArgs(wsC, stageNo)

    ' 스크립트 경로 검증 (--stage 옵션이 포함된 경우 첫 번째 토큰만 확인)
    Dim scriptPath As String
    Dim scriptParts() As String
    scriptParts = Split(relScript, " ")
    scriptPath = JoinPath(root, scriptParts(0))
    If Dir$(scriptPath, vbNormal) = vbNullString Then
        Err.Raise vbObjectError + 102, , "스크립트 파일이 없습니다: " & scriptPath
    End If

    Dim logDir As String: logDir = JoinPath(root, "logs")
    EnsureFolder logDir

    Dim logFile As String
    logFile = JoinPath(logDir, "pipeline_" & Format$(Now, "yyyymmdd_hhnnss") & ".log")

    Dim cmd As String
    cmd = BuildCmd(root, pyExe, scriptPath, args, logFile)

    LogWrite "INFO", "RunStage" & stageNo, "START", cmd

    Application.StatusBar = "Running Stage " & stageNo & " ..."

    Dim exitCode As Long
    exitCode = RunCmdWait(cmd)

    If exitCode <> 0 Then
        LogWrite "ERROR", "RunStage" & stageNo, "FAILED (exit=" & exitCode & ")", logFile
        MsgBox "Stage " & stageNo & " 실패. LOG 시트/로그파일 확인: " & logFile, vbCritical
        RunStage = False
        GoTo CleanUp
    End If

    LogWrite "INFO", "RunStage" & stageNo, "DONE", logFile
    RunStage = True

    If CBoolSafe(wsC.Range(C_OPEN_AFTER).Value2) Then
        OpenFileOrFolder root
    End If

CleanUp:
    Application.StatusBar = False
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Exit Function

EH:
    LogWrite "ERROR", "RunStage" & stageNo, "EXCEPTION: " & Err.Number & " - " & Err.Description, ""
    MsgBox "오류: " & Err.Description, vbCritical
    RunStage = False
    Resume CleanUp
End Function

' ====== Helpers ======
Private Function GetStageScript(ByVal wsC As Worksheet, ByVal stageNo As Long) As String
    Select Case stageNo
        Case 1: GetStageScript = Trim$(wsC.Range(C_STAGE1_SCRIPT).Value2)
        Case 2: GetStageScript = Trim$(wsC.Range(C_STAGE2_SCRIPT).Value2)
        Case 3: GetStageScript = Trim$(wsC.Range(C_STAGE3_SCRIPT).Value2)
        Case 4: GetStageScript = Trim$(wsC.Range(C_STAGE4_SCRIPT).Value2)
        Case Else: Err.Raise vbObjectError + 103, , "지원하지 않는 stage: " & stageNo
    End Select
    If Len(GetStageScript) = 0 Then Err.Raise vbObjectError + 104, , "Stage" & stageNo & "Script 셀이 비어있습니다."
End Function

Private Function GetStageArgs(ByVal wsC As Worksheet, ByVal stageNo As Long) As String
    Select Case stageNo
        Case 1: GetStageArgs = Trim$(wsC.Range(C_ARGS_STAGE1).Value2)
        Case 2: GetStageArgs = Trim$(wsC.Range(C_ARGS_STAGE2).Value2)
        Case 3: GetStageArgs = Trim$(wsC.Range(C_ARGS_STAGE3).Value2)
        Case 4: GetStageArgs = Trim$(wsC.Range(C_ARGS_STAGE4).Value2)
        Case Else: GetStageArgs = vbNullString
    End Select
End Function

Private Function BuildCmd(ByVal workDir As String, ByVal pyExe As String, ByVal scriptPath As String, ByVal args As String, ByVal logFile As String) As String
    ' cmd /c "cd /d <workDir> && <pyExe> <script> <args> > <log> 2>&1"
    ' 타임스탬프가 파일명에 포함되어 있으므로 매번 새 파일 생성 (overwrite 모드)
    Dim inner As String
    inner = "cd /d " & Q(workDir) & " && " & QuoteExe(pyExe) & " " & Q(scriptPath)
    If Len(args) > 0 Then inner = inner & " " & args
    inner = inner & " >" & Q(logFile) & " 2>&1"
    BuildCmd = "cmd /c " & Q(inner)
End Function

Private Function RunCmdWait(ByVal cmd As String) As Long
    Dim sh As Object: Set sh = CreateObject("WScript.Shell")
    ' 0=hidden window, True=wait
    RunCmdWait = sh.Run(cmd, 0, True)
End Function

Private Sub EnsureSheets()
    If SheetExists(SH_CONTROL) = False Then
        Err.Raise vbObjectError + 201, , "CONTROL 시트가 없습니다."
    End If
    If SheetExists(SH_LOG) = False Then
        Dim ws As Worksheet
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        ws.Name = SH_LOG
        ws.Range("A1:E1").Value = Array("Timestamp", "Level", "Proc", "Message", "Ref")
        ws.Columns("A:E").EntireColumn.AutoFit
    End If
End Sub

Private Function SheetExists(ByVal name As String) As Boolean
    On Error Resume Next
    SheetExists = Not ThisWorkbook.Worksheets(name) Is Nothing
    On Error GoTo 0
End Function

Private Sub LogWrite(ByVal level As String, ByVal proc As String, ByVal msg As String, ByVal ref As String)
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SH_LOG)
    Dim r As Long: r = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
    ws.Cells(r, 1).Value2 = Now
    ws.Cells(r, 2).Value2 = level
    ws.Cells(r, 3).Value2 = proc
    ws.Cells(r, 4).Value2 = msg
    ws.Cells(r, 5).Value2 = ref
End Sub

Private Sub EnsureFolder(ByVal folderPath As String)
    If Len(Dir$(folderPath, vbDirectory)) = 0 Then
        MkDir folderPath
    End If
End Sub

Private Function JoinPath(ByVal basePath As String, ByVal relPath As String) As String
    If Right$(basePath, 1) = "\" Or Right$(basePath, 1) = "/" Then
        JoinPath = basePath & relPath
    Else
        JoinPath = basePath & "\" & relPath
    End If
End Function

Private Function Q(ByVal s As String) As String
    Q = """" & Replace(s, """", """""") & """"
End Function

Private Function QuoteExe(ByVal exe As String) As String
    ' "py" 같이 PATH 명령도 허용. 공백이 있으면 쿼트.
    If InStr(1, exe, " ", vbTextCompare) > 0 Or InStr(1, exe, ":", vbTextCompare) > 0 Then
        QuoteExe = Q(exe)
    Else
        QuoteExe = exe
    End If
End Function

Private Function CBoolSafe(ByVal v As Variant) As Boolean
    On Error GoTo EH
    If VarType(v) = vbBoolean Then
        CBoolSafe = v
    Else
        CBoolSafe = (UCase$(Trim$(CStr(v))) = "TRUE" Or Trim$(CStr(v)) = "1" Or UCase$(Trim$(CStr(v))) = "Y")
    End If
    Exit Function
EH:
    CBoolSafe = False
End Function

Private Sub OpenFileOrFolder(ByVal path As String)
    Dim cmd As String
    cmd = "explorer.exe " & Q(path)
    Shell cmd, vbNormalFocus
End Sub
```

---

### 3-C) (참고) 파이썬 실행 구조

**통합 진입점**: `run\run_pipeline.py`
- 모든 Stage는 이 스크립트를 통해 실행됩니다.
- 설정 파일은 자동으로 로드되므로 `ArgsStageX`는 추가 옵션만 지정하면 됩니다.

**사용 가능한 추가 옵션** (ArgsStageX에 지정):
- Stage 4: `--stage4-visualize` (색상 시각화 활성화)
- Stage 4: `--stage4-no-visualize` (색상 시각화 비활성화)
- Stage 4: `--stage4-excel-out <경로>` (Excel 출력 경로 재정의)
- Stage 4: `--stage4-json-out <경로>` (JSON 출력 경로 재정의)
- Stage 3: `--stage3-report-dir <경로>` (보고서 출력 디렉터리 재정의)

**설정 파일 자동 로드**:
- `config\pipeline_config.yaml` (Stage 1, 3, 4)
- `config\stage2_derived_config.yaml` (Stage 2) 

---

## 4) 실행 단계

### 4-1) CONTROL 시트 생성

1. **새 시트 생성** 후 이름을 `CONTROL`로 변경
2. **A열에 레이블, B열에 값 입력** (위 표 참조)
3. **실제 프로젝트 경로 예시** (`C:\PP1030` 기준):
   - B2: `C:\PP1030`
   - B3: `py` (또는 `python`, 또는 가상환경 경로)
   - B4: `run\run_pipeline.py --stage 1`
   - B5: `run\run_pipeline.py --stage 2`
   - B6: `run\run_pipeline.py --stage 3`
   - B7: `run\run_pipeline.py --stage 4`
   - B8: (비워둠)
   - B9: (비워둠)
   - B10: (비워둠)
   - B11: `--stage4-visualize` (색상 시각화 원하는 경우)
   - B13: `TRUE` (실행 후 폴더 자동 열기)

### 4-2) VBA 모듈 추가

1. **VBE 열기**: Alt+F11
2. **모듈 추가**: 삽입 → 모듈
3. **모듈 이름 변경**: 속성 창에서 `modPipelineLauncher`로 변경
4. **코드 붙여넣기**: 위의 VBA 코드 전체를 복사하여 붙여넣기

### 4-3) 버튼 생성 및 매크로 연결

1. **CONTROL 시트로 이동**
2. **개발자 탭 활성화**: 파일 → 옵션 → 리본 사용자 지정 → 개발자 체크
3. **버튼 추가**: 개발자 → 삽입 → 양식 컨트롤 → 단추(양식 컨트롤)
4. **버튼 5개 생성**:
   - "Run Stage 1" → 매크로: `Run_Stage1`
   - "Run Stage 2" → 매크로: `Run_Stage2`
   - "Run Stage 3" → 매크로: `Run_Stage3`
   - "Run Stage 4" → 매크로: `Run_Stage4`
   - "Run All" → 매크로: `Run_All`

### 4-4) 테스트

   * Stage1 실행 → `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx` 생성 확인
   * Stage2 실행 → `data\processed\derived\HVDC WAREHOUSE_HITACHI(HE).xlsx` 생성 확인
   * Stage3 실행 → `data\processed\reports\HVDC_입고로직_종합리포트_*.xlsx` (12시트) 생성 확인
   * Stage4 실행 → `data\anomaly\HVDC_anomaly_report.xlsx`, `HVDC_anomaly_report.json` 생성 확인

**출력 파일 경로 (검증용)**:
- **Stage 1**: `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx` (멀티시트)
- **Stage 1 (병합)**: `data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx` (Stage 2 입력용)
- **Stage 2**: `data\processed\derived\HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **Stage 3**: `data\processed\reports\HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx` (12개 시트)
- **Stage 4**: `data\anomaly\HVDC_anomaly_report.xlsx`, `data\anomaly\HVDC_anomaly_report.json` 

---

## 5) 검증·주의·옵션

### Fail-Safe(필수)

* VBA는 **ExitCode != 0이면 즉시 중단**하고, `LOG 시트 + logs\pipeline_*.log`에 남깁니다.
* Stage1은 날짜 변경 셀 Orange / 신규행 Yellow로 시각화가 들어가므로, 결과 파일 열어서 색상 반영을 확인하세요. 
* Stage4는 심각도별 색상 시각화(빨강/주황/노랑/연두)를 옵션으로 적용합니다. 

### A/B/C 운영안(추천)

* **A안(추천)**: 지금 설계처럼 “VBA 런처 + Python 스크립트” (가장 안정/유지보수 쉬움)
* **B안**: VBA로 일부 로직까지 구현(예: 파일 병합/정렬). 단, Stage1의 시맨틱 매칭/표준헤더/멀티시트 처리까지 VBA로 옮기면 규모가 커집니다. 
* **C안**: 배치(.bat/Task Scheduler)로 야간 자동 실행 + 엑셀은 결과 뷰어만

---

---

## 6) CONTROL 시트 레이아웃 예시

### 권장 레이아웃

```
┌─────────────────────────────────────────────────────────┐
│ CONTROL 시트                                            │
├──────────┬──────────────────────────────────────────────┤
│ A열      │ B열                                          │
├──────────┼──────────────────────────────────────────────┤
│          │                                              │
│ ProjectRoot │ C:\PP1030                                │
│ PythonExe   │ py                                       │
│ Stage1Script│ run\run_pipeline.py --stage 1            │
│ Stage2Script│ run\run_pipeline.py --stage 2            │
│ Stage3Script│ run\run_pipeline.py --stage 3            │
│ Stage4Script│ run\run_pipeline.py --stage 4            │
│ ArgsStage1 │ (비워둠)                                   │
│ ArgsStage2 │ (비워둠)                                   │
│ ArgsStage3 │ (비워둠)                                   │
│ ArgsStage4 │ --stage4-visualize                        │
│            │                                            │
│ OpenAfterRun│ TRUE                                     │
│            │                                            │
│ [Run Stage 1] [Run Stage 2] [Run Stage 3] [Run Stage 4]│
│ [Run All]                                              │
└─────────────────────────────────────────────────────────┘
```

### 버튼 배치 권장사항

- **위치**: CONTROL 시트의 D열~H열, 2행~6행
- **크기**: 각 버튼 너비 100px, 높이 30px
- **정렬**: 가로로 나란히 배치

---

## 7) 문제 해결

### 일반적인 오류

1. **"스크립트 파일이 없습니다"**
   - 원인: `StageXScript` 경로가 잘못됨
   - 해결: `run\run_pipeline.py` 경로 확인, 프로젝트 루트 경로 확인

2. **"ProjectRoot(B2)가 비어있습니다"**
   - 원인: B2 셀이 비어있음
   - 해결: B2에 프로젝트 루트 경로 입력 (예: `C:\PP1030`)

3. **Python 실행 오류**
   - 원인: Python이 PATH에 없거나 가상환경 경로가 잘못됨
   - 해결: B3에 `py`, `python`, 또는 전체 경로 입력

4. **로그 파일 생성 실패**
   - 원인: `logs` 폴더 권한 문제
   - 해결: 프로젝트 루트에 `logs` 폴더 생성 권한 확인

### 디버깅 팁

- **LOG 시트 확인**: 각 실행마다 타임스탬프와 함께 로그 기록
- **로그 파일 확인**: `logs\pipeline_YYYYMMDD_HHMMSS.log` 파일 확인
- **StatusBar 확인**: Excel 하단 상태 표시줄에 실행 상태 표시
