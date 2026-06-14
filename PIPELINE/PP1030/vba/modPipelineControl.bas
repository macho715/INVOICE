Attribute VB_Name = "modPipelineControl"
Option Explicit

' =========================================================
' HVDC Pipeline CONTROL (Excel LTSC 2021)
' - CONTROL 시트 템플릿 생성
' - Python Stage1~4 실행/모니터링
' - LOG 시트 기록 + 텍스트 로그 파일
' - p2.md 기반 완전 교체 버전
' =========================================================

' ---- Sheet Names
Private Const SH_CONTROL As String = "CONTROL"
Private Const SH_LOG As String = "LOG"

' ---- Named Ranges (CONTROL)
Private Const NR_PROJECT_ROOT As String = "n_ProjectRoot"
Private Const NR_PYTHON_EXE As String = "n_PythonExe"
Private Const NR_PIPELINE_CFG As String = "n_PipelineConfig"
Private Const NR_STAGE2_CFG As String = "n_Stage2Config"
Private Const NR_STAGE4_CFG As String = "n_Stage4Config"
Private Const NR_USE_CLI_ARGS As String = "n_UseCliArgs"

Private Const NR_MASTER_FOLDER As String = "n_MasterFolder"
Private Const NR_WAREHOUSE_FILE As String = "n_WarehouseFile"
Private Const NR_LOG_FOLDER As String = "n_LogFolder"
Private Const NR_OPEN_AFTER_RUN As String = "n_OpenAfterRun"

Private Const NR_STG1_EN As String = "n_Stg1Enabled"
Private Const NR_STG1_LAST As String = "n_Stg1LastRun"
Private Const NR_STG1_OUT_MAIN As String = "n_Stg1OutMain"
Private Const NR_STG1_OUT_EXTRA As String = "n_Stg1OutExtra"

Private Const NR_STG2_EN As String = "n_Stg2Enabled"
Private Const NR_STG2_LAST As String = "n_Stg2LastRun"
Private Const NR_STG2_OUT_MAIN As String = "n_Stg2OutMain"

Private Const NR_STG3_EN As String = "n_Stg3Enabled"
Private Const NR_STG3_LAST As String = "n_Stg3LastRun"
Private Const NR_STG3_OUT_MAIN As String = "n_Stg3OutMain"

Private Const NR_STG4_EN As String = "n_Stg4Enabled"
Private Const NR_STG4_LAST As String = "n_Stg4LastRun"
Private Const NR_STG4_OUT_MAIN As String = "n_Stg4OutMain"

' ---- Project-relative conventions (docs 기준 기본값)
Private Const REL_RAW_DIR As String = "data\raw"
Private Const REL_SYNCED_DIR As String = "data\processed\synced"
Private Const REL_DERIVED_DIR As String = "data\processed\derived"
Private Const REL_REPORT_DIR As String = "data\processed\reports"
Private Const REL_ANOMALY_DIR As String = "data\anomaly"

Private Const EXPECT_WAREHOUSE_NAME As String = "HVDC WAREHOUSE_HITACHI(HE).xlsx"
Private Const PATTERN_MASTER As String = "Case List*.xlsx"

' Stage output (docs 기준)
Private Const REL_STAGE1_MULTI As String = "data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
Private Const REL_STAGE1_MERGED As String = "data\processed\synced\HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
Private Const REL_STAGE2_DERIVED As String = "data\processed\derived\HVDC WAREHOUSE_HITACHI(HE).xlsx"
Private Const REL_STAGE3_REPORT_PATTERN As String = "data\processed\reports\HVDC_입고로직_종합리포트_*.xlsx"
Private Const REL_STAGE4_ANOMALY_XLSX As String = "data\anomaly\HVDC_anomaly_report.xlsx"

' Stage scripts (run_pipeline.py 통합 진입점 사용)
Private Const REL_STAGE1_SCRIPT As String = "run\run_pipeline.py --stage 1"
Private Const REL_STAGE2_SCRIPT As String = "run\run_pipeline.py --stage 2"
Private Const REL_STAGE3_SCRIPT As String = "run\run_pipeline.py --stage 3"
Private Const REL_STAGE4_SCRIPT As String = "run\run_pipeline.py --stage 4"

' =========================================================
'  UI Buttons (OnAction targets)
' =========================================================
Public Sub UI_InitTemplate()
    BuildTemplates True
    MsgBox "CONTROL/LOG 템플릿 생성 완료", vbInformation
End Sub

Public Sub UI_RunAll()
    Dim ok As Boolean
    ok = RunStagesSequential(True, True, True, True)
    If ok Then
        MsgBox "RUN ALL 완료", vbInformation
    Else
        MsgBox "RUN ALL 중 오류 발생. LOG 시트/로그파일 확인", vbExclamation
    End If
End Sub

Public Sub UI_RunStage1(): Call RunSingleStage("stage1"): End Sub
Public Sub UI_RunStage2(): Call RunSingleStage("stage2"): End Sub
Public Sub UI_RunStage3(): Call RunSingleStage("stage3"): End Sub
Public Sub UI_RunStage4(): Call RunSingleStage("stage4"): End Sub

Public Sub UI_ClearLog()
    Dim ws As Worksheet: Set ws = GetOrCreateSheet(SH_LOG)
    ws.Range("A2:E" & ws.Rows.Count).ClearContents
    MsgBox "LOG cleared", vbInformation
End Sub

Public Sub UI_OpenLogFolder()
    Dim p As String: p = GetNRText(NR_LOG_FOLDER, "")
    If Len(p) = 0 Then
        MsgBox "Log Folder가 비어있습니다.", vbExclamation
        Exit Sub
    End If
    OpenFolder p
End Sub

Public Sub UI_OpenLatestOutput()
    ' 우선순위: Stage4 > Stage3 > Stage2 > Stage1(merged)
    Dim p As String
    p = GetNRText(NR_STG4_OUT_MAIN, "")
    If FileExists(p) Then OpenFile p: Exit Sub
    p = GetNRText(NR_STG3_OUT_MAIN, "")
    If FileExists(p) Then OpenFile p: Exit Sub
    p = GetNRText(NR_STG2_OUT_MAIN, "")
    If FileExists(p) Then OpenFile p: Exit Sub
    p = GetNRText(NR_STG1_OUT_MAIN, "")
    If FileExists(p) Then OpenFile p: Exit Sub

    MsgBox "열 수 있는 결과 파일을 찾지 못했습니다. (경로/실행여부 확인)", vbExclamation
End Sub

' =========================================================
'  Main Runners
' =========================================================
Private Sub RunSingleStage(ByVal stageId As String)
    Dim ok As Boolean

    Select Case LCase$(stageId)
        Case "stage1": ok = RunStagesSequential(True, False, False, False)
        Case "stage2": ok = RunStagesSequential(False, True, False, False)
        Case "stage3": ok = RunStagesSequential(False, False, True, False)
        Case "stage4": ok = RunStagesSequential(False, False, False, True)
        Case Else
            MsgBox "Unknown stage: " & stageId, vbExclamation
            Exit Sub
    End Select

    If ok Then
        MsgBox stageId & " 완료", vbInformation
    Else
        MsgBox stageId & " 실패. LOG 확인", vbExclamation
    End If
End Sub

Private Function RunStagesSequential(ByVal do1 As Boolean, ByVal do2 As Boolean, ByVal do3 As Boolean, ByVal do4 As Boolean) As Boolean
    On Error GoTo EH

    EnsureTemplatesExist

    If do1 And GetNRBool(NR_STG1_EN, True) Then
        If Not RunStage("stage1") Then RunStagesSequential = False: Exit Function
    End If
    If do2 And GetNRBool(NR_STG2_EN, True) Then
        If Not RunStage("stage2") Then RunStagesSequential = False: Exit Function
    End If
    If do3 And GetNRBool(NR_STG3_EN, True) Then
        If Not RunStage("stage3") Then RunStagesSequential = False: Exit Function
    End If
    If do4 And GetNRBool(NR_STG4_EN, True) Then
        If Not RunStage("stage4") Then RunStagesSequential = False: Exit Function
    End If

    RunStagesSequential = True
    Exit Function

EH:
    LogMsg "ERROR", "RunStagesSequential", Err.Description, "Err#" & Err.Number
    RunStagesSequential = False
End Function

Private Function RunStage(ByVal stageId As String) As Boolean
    On Error GoTo EH

    Dim root As String: root = Trim$(GetNRText(NR_PROJECT_ROOT, ""))
    Dim pyExe As String: pyExe = Trim$(GetNRText(NR_PYTHON_EXE, "py"))
    Dim logDir As String: logDir = Trim$(GetNRText(NR_LOG_FOLDER, ""))

    If Len(root) = 0 Or Not FolderExists(root) Then
        MsgBox "Project Root 폴더가 유효하지 않습니다: " & root, vbExclamation
        RunStage = False
        Exit Function
    End If

    If Len(logDir) = 0 Then
        logDir = CombinePath(root, "logs")
        SetNRText NR_LOG_FOLDER, logDir
    End If
    EnsureFolder logDir

    Application.StatusBar = "Running " & stageId & " ..."
    LogMsg "INFO", "RunStage", "START " & stageId, ""

    ' Stage1이면 raw 준비(복사/백업)
    If LCase$(stageId) = "stage1" Then
        If Not PrepareRawInputs(root) Then
            RunStage = False
            Exit Function
        End If
    End If

    Dim scriptRel As String, args As String
    scriptRel = StageScript(stageId)
    args = GetStageArgs(stageId)

    ' 스크립트 경로 검증 (--stage 옵션이 포함된 경우 첫 번째 토큰만 확인)
    Dim scriptPath As String
    Dim scriptParts() As String
    scriptParts = Split(scriptRel, " ")
    scriptPath = CombinePath(root, scriptParts(0))
    If Not FileExists(scriptPath) Then
        MsgBox "Stage 스크립트를 찾지 못했습니다: " & scriptPath, vbExclamation
        LogMsg "ERROR", "RunStage", "Script not found", scriptPath
        RunStage = False
        Exit Function
    End If

    ' command build
    Dim logFile As String
    logFile = CombinePath(logDir, stageId & "_" & Format(Now, "yyyymmdd_hhnnss") & ".log")

    Dim cmd As String
    cmd = BuildCmd(pyExe, root, scriptRel, args, logFile)

    Dim exitCode As Long
    exitCode = ExecAndMonitor(cmd, stageId)

    If exitCode <> 0 Then
        LogMsg "ERROR", "RunStage", "FAIL " & stageId & " (exit=" & exitCode & ")", logFile
        Application.StatusBar = False
        RunStage = False
        Exit Function
    End If

    LogMsg "INFO", "RunStage", "DONE " & stageId, logFile
    UpdateAfterStage root, stageId

    If GetNRBool(NR_OPEN_AFTER_RUN, True) Then
        OpenLatestOutputSilently
    End If

    Application.StatusBar = False
    RunStage = True
    Exit Function

EH:
    LogMsg "ERROR", "RunStage(" & stageId & ")", Err.Description, "Err#" & Err.Number
    Application.StatusBar = False
    RunStage = False
End Function

' =========================================================
'  Stage Helpers
' =========================================================
Private Function StageScript(ByVal stageId As String) As String
    Select Case LCase$(stageId)
        Case "stage1": StageScript = REL_STAGE1_SCRIPT
        Case "stage2": StageScript = REL_STAGE2_SCRIPT
        Case "stage3": StageScript = REL_STAGE3_SCRIPT
        Case "stage4": StageScript = REL_STAGE4_SCRIPT
        Case Else: StageScript = vbNullString
    End Select
End Function

Private Function GetStageArgs(ByVal stageId As String) As String
    ' run_pipeline.py는 설정 파일을 자동 로드하므로 --config 옵션 불필요
    ' 추가 옵션만 반환 (예: --stage4-visualize)
    ' 필요시 Stage별 추가 옵션 반환 가능
    GetStageArgs = vbNullString
End Function

Private Function PrepareRawInputs(ByVal projectRoot As String) As Boolean
    On Error GoTo EH

    Dim masterFolder As String: masterFolder = Trim$(GetNRText(NR_MASTER_FOLDER, ""))
    Dim whFile As String: whFile = Trim$(GetNRText(NR_WAREHOUSE_FILE, ""))

    If Len(masterFolder) = 0 Or Not FolderExists(masterFolder) Then
        MsgBox "Master Folder가 유효하지 않습니다: " & masterFolder, vbExclamation
        PrepareRawInputs = False
        Exit Function
    End If
    If Len(whFile) = 0 Or Not FileExists(whFile) Then
        MsgBox "Warehouse File이 유효하지 않습니다: " & whFile, vbExclamation
        PrepareRawInputs = False
        Exit Function
    End If

    Dim rawDir As String: rawDir = CombinePath(projectRoot, REL_RAW_DIR)
    EnsureFolder rawDir

    ' 1) Master: Case List*.xlsx 복사
    CopyFilesWithBackup masterFolder, PATTERN_MASTER, rawDir

    ' 2) Warehouse: 지정 파일을 data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx 로 복사(이름 고정)
    CopySingleFileWithBackup whFile, CombinePath(rawDir, EXPECT_WAREHOUSE_NAME)

    LogMsg "INFO", "PrepareRawInputs", "raw inputs prepared", rawDir
    PrepareRawInputs = True
    Exit Function

EH:
    LogMsg "ERROR", "PrepareRawInputs", Err.Description, "Err#" & Err.Number
    PrepareRawInputs = False
End Function

Private Sub UpdateAfterStage(ByVal root As String, ByVal stageId As String)
    On Error GoTo EH

    Select Case LCase$(stageId)
        Case "stage1"
            SetNRText NR_STG1_LAST, Format(Now, "yyyy-mm-dd hh:nn:ss")
            SetNRText NR_STG1_OUT_MAIN, CombinePath(root, REL_STAGE1_MERGED)
            SetNRText NR_STG1_OUT_EXTRA, CombinePath(root, REL_STAGE1_MULTI)

        Case "stage2"
            SetNRText NR_STG2_LAST, Format(Now, "yyyy-mm-dd hh:nn:ss")
            SetNRText NR_STG2_OUT_MAIN, CombinePath(root, REL_STAGE2_DERIVED)

        Case "stage3"
            SetNRText NR_STG3_LAST, Format(Now, "yyyy-mm-dd hh:nn:ss")
            Dim latest As String
            latest = FindLatestFile(CombinePath(root, REL_REPORT_DIR), "HVDC_입고로직_종합리포트_*.xlsx")
            If Len(latest) > 0 Then
                SetNRText NR_STG3_OUT_MAIN, latest
            Else
                ' 패턴 못 찾으면 패턴 문자열이라도 기록
                SetNRText NR_STG3_OUT_MAIN, CombinePath(root, REL_STAGE3_REPORT_PATTERN)
            End If

        Case "stage4"
            SetNRText NR_STG4_LAST, Format(Now, "yyyy-mm-dd hh:nn:ss")
            ' stage4 출력은 문서에 2종(예시 config 포함) 흔들림이 있어, 대표 경로 우선 체크
            Dim p1 As String, p2 As String
            p1 = CombinePath(root, REL_STAGE4_ANOMALY_XLSX)
            p2 = CombinePath(root, "reports\anomalies\anomaly_list.xlsx") ' 예시 config
            If FileExists(p1) Then
                SetNRText NR_STG4_OUT_MAIN, p1
            ElseIf FileExists(p2) Then
                SetNRText NR_STG4_OUT_MAIN, p2
            Else
                SetNRText NR_STG4_OUT_MAIN, p1
            End If
    End Select

    Exit Sub

EH:
    LogMsg "ERROR", "UpdateAfterStage(" & stageId & ")", Err.Description, "Err#" & Err.Number
End Sub

' =========================================================
'  Command Exec
' =========================================================
Private Function BuildCmd(ByVal pyExe As String, ByVal root As String, ByVal scriptRel As String, ByVal args As String, ByVal logFile As String) As String
    Dim inner As String
    
    ' run_pipeline.py는 설정 파일을 자동 로드하므로 --config 옵션 불필요
    ' scriptRel에는 이미 "run\run_pipeline.py --stage X" 형식으로 포함됨
    ' scriptRel은 공백이 포함되어 있으므로 전체를 Q()로 감싸야 함
    ' args는 추가 옵션만 (예: --stage4-visualize)
    inner = "cd /d " & Q(root) & " && " & QuoteExe(pyExe) & " " & Q(scriptRel)
    If Len(args) > 0 Then inner = inner & " " & args
    inner = inner & " > " & Q(logFile) & " 2>&1"
    BuildCmd = "cmd /c " & Q(inner)
End Function

Private Function ExecAndMonitor(ByVal cmd As String, ByVal stageId As String) As Long
    On Error GoTo EH

    Dim wsh As Object: Set wsh = CreateObject("WScript.Shell")
    Dim ex As Object: Set ex = wsh.Exec(cmd)

    Dim t0 As Double: t0 = Timer
    Do While ex.Status = 0
        DoEvents
        Application.StatusBar = "Running " & stageId & " ... " & Format(ElapsedSeconds(t0), "0.0") & "s"
    Loop

    ExecAndMonitor = CLng(ex.ExitCode)
    Exit Function

EH:
    LogMsg "ERROR", "ExecAndMonitor", Err.Description, cmd
    ExecAndMonitor = -1
End Function

Private Function ElapsedSeconds(ByVal startT As Double) As Double
    Dim nowT As Double: nowT = Timer
    If nowT < startT Then
        ElapsedSeconds = (86400# - startT) + nowT
    Else
        ElapsedSeconds = nowT - startT
    End If
End Function

' =========================================================
'  Template Builder
' =========================================================
Private Sub BuildTemplates(ByVal overwrite As Boolean)
    Application.ScreenUpdating = False
    On Error GoTo EH

    BuildControlSheet overwrite
    BuildLogSheet overwrite

    Application.ScreenUpdating = True
    Exit Sub

EH:
    Application.ScreenUpdating = True
    MsgBox "Template build failed: " & Err.Description, vbExclamation
End Sub

Private Sub EnsureTemplatesExist()
    If Not SheetExists(SH_CONTROL) Or Not SheetExists(SH_LOG) Then
        BuildTemplates True
    End If
End Sub

Private Sub BuildControlSheet(ByVal overwrite As Boolean)
    Dim ws As Worksheet: Set ws = GetOrCreateSheet(SH_CONTROL)

    If overwrite Then
        ws.Cells.Clear
        DeleteAllShapes ws
    End If

    ' column widths
    ws.Columns("A").ColumnWidth = 30
    ws.Columns("B").ColumnWidth = 80
    ws.Columns("C").ColumnWidth = 30
    ws.Columns("D").ColumnWidth = 60
    ws.Columns("E").ColumnWidth = 60
    ws.Columns("G").ColumnWidth = 24

    ' Title
    ws.Range("A1:E1").Merge
    ws.Range("A1").Value = "HVDC PIPELINE CONTROL"
    ws.Range("A1").Font.Bold = True
    ws.Range("A1").Font.Size = 16

    ' Section labels + fields
    ws.Range("A3").Value = "환경/경로"
    ws.Range("A3").Font.Bold = True

    ws.Range("A4").Value = "Project Root"
    ws.Range("A5").Value = "Python EXE (py 또는 python.exe)"
    ws.Range("A6").Value = "pipeline_config.yaml"
    ws.Range("A7").Value = "stage2_derived_config.yaml"
    ws.Range("A8").Value = "stage4_anomaly.yaml"
    ws.Range("A9").Value = "CLI args 사용(TRUE/FALSE)"

    ws.Range("A11").Value = "Master Folder (Case List*.xlsx)"
    ws.Range("A12").Value = "Warehouse File"
    ws.Range("A15").Value = "Log Folder"
    ws.Range("A16").Value = "완료 후 결과 자동 열기(TRUE/FALSE)"

    ' Defaults
    ws.Range("B4").Value = ThisWorkbook.Path
    ws.Range("B5").Value = "py"
    ws.Range("B6").Value = CombinePath(ThisWorkbook.Path, "config\pipeline_config.yaml")
    ws.Range("B7").Value = CombinePath(ThisWorkbook.Path, "config\stage2_derived_config.yaml")
    ws.Range("B8").Value = CombinePath(ThisWorkbook.Path, "config\stage4_anomaly.yaml")
    ws.Range("B9").Value = False

    ws.Range("B15").Value = CombinePath(ThisWorkbook.Path, "logs")
    ws.Range("B16").Value = True

    ' Stage table header
    ws.Range("A18").Value = "Stage"
    ws.Range("B18").Value = "Enabled"
    ws.Range("C18").Value = "LastRun"
    ws.Range("D18").Value = "Main Output"
    ws.Range("E18").Value = "Extra Output"
    ws.Range("A18:E18").Font.Bold = True

    ' Stage rows (fixed)
    ws.Range("A19").Value = "Stage1 Sync"
    ws.Range("A20").Value = "Stage2 Derived"
    ws.Range("A21").Value = "Stage3 Report"
    ws.Range("A22").Value = "Stage4 Anomaly"

    ws.Range("B19").Value = True
    ws.Range("B20").Value = True
    ws.Range("B21").Value = True
    ws.Range("B22").Value = True

    ws.Range("D19").Value = CombinePath(ThisWorkbook.Path, REL_STAGE1_MERGED)
    ws.Range("E19").Value = CombinePath(ThisWorkbook.Path, REL_STAGE1_MULTI)
    ws.Range("D20").Value = CombinePath(ThisWorkbook.Path, REL_STAGE2_DERIVED)
    ws.Range("D21").Value = CombinePath(ThisWorkbook.Path, REL_STAGE3_REPORT_PATTERN)
    ws.Range("D22").Value = CombinePath(ThisWorkbook.Path, REL_STAGE4_ANOMALY_XLSX)

    ' Input cells style
    StyleInputCell ws.Range("B4:B9")
    StyleInputCell ws.Range("B11:B12")
    StyleInputCell ws.Range("B15:B16")
    StyleInputCell ws.Range("B19:B22")

    ' Data validation for TRUE/FALSE
    ApplyBoolValidation ws.Range("B9")
    ApplyBoolValidation ws.Range("B16")
    ApplyBoolValidation ws.Range("B19:B22")

    ' Define named ranges (workbook scope)
    DefineName NR_PROJECT_ROOT, ws.Range("B4")
    DefineName NR_PYTHON_EXE, ws.Range("B5")
    DefineName NR_PIPELINE_CFG, ws.Range("B6")
    DefineName NR_STAGE2_CFG, ws.Range("B7")
    DefineName NR_STAGE4_CFG, ws.Range("B8")
    DefineName NR_USE_CLI_ARGS, ws.Range("B9")

    DefineName NR_MASTER_FOLDER, ws.Range("B11")
    DefineName NR_WAREHOUSE_FILE, ws.Range("B12")
    DefineName NR_LOG_FOLDER, ws.Range("B15")
    DefineName NR_OPEN_AFTER_RUN, ws.Range("B16")

    DefineName NR_STG1_EN, ws.Range("B19")
    DefineName NR_STG1_LAST, ws.Range("C19")
    DefineName NR_STG1_OUT_MAIN, ws.Range("D19")
    DefineName NR_STG1_OUT_EXTRA, ws.Range("E19")

    DefineName NR_STG2_EN, ws.Range("B20")
    DefineName NR_STG2_LAST, ws.Range("C20")
    DefineName NR_STG2_OUT_MAIN, ws.Range("D20")

    DefineName NR_STG3_EN, ws.Range("B21")
    DefineName NR_STG3_LAST, ws.Range("C21")
    DefineName NR_STG3_OUT_MAIN, ws.Range("D21")

    DefineName NR_STG4_EN, ws.Range("B22")
    DefineName NR_STG4_LAST, ws.Range("C22")
    DefineName NR_STG4_OUT_MAIN, ws.Range("D22")

    ' Buttons (fixed anchor cells)
    AddButton ws, "G4", "btn_InitTemplate", "INIT / RESET", "UI_InitTemplate"
    AddButton ws, "G6", "btn_RunAll", "RUN ALL (1→4)", "UI_RunAll"
    AddButton ws, "G8", "btn_RunStage1", "Run Stage1", "UI_RunStage1"
    AddButton ws, "G9", "btn_RunStage2", "Run Stage2", "UI_RunStage2"
    AddButton ws, "G10", "btn_RunStage3", "Run Stage3", "UI_RunStage3"
    AddButton ws, "G11", "btn_RunStage4", "Run Stage4", "UI_RunStage4"
    AddButton ws, "G13", "btn_OpenOutput", "Open Latest Output", "UI_OpenLatestOutput"
    AddButton ws, "G14", "btn_OpenLogFolder", "Open Log Folder", "UI_OpenLogFolder"
    AddButton ws, "G15", "btn_ClearLog", "Clear LOG", "UI_ClearLog"

    ws.Activate
    ws.Range("B4").Select
End Sub

Private Sub BuildLogSheet(ByVal overwrite As Boolean)
    Dim ws As Worksheet: Set ws = GetOrCreateSheet(SH_LOG)

    If overwrite Then ws.Cells.Clear

    ws.Range("A1").Value = "Timestamp"
    ws.Range("B1").Value = "Level"
    ws.Range("C1").Value = "Procedure"
    ws.Range("D1").Value = "Message"
    ws.Range("E1").Value = "Details"
    ws.Range("A1:E1").Font.Bold = True

    ws.Columns("A").ColumnWidth = 22
    ws.Columns("B").ColumnWidth = 10
    ws.Columns("C").ColumnWidth = 24
    ws.Columns("D").ColumnWidth = 60
    ws.Columns("E").ColumnWidth = 60

    ws.Range("A2").Select
End Sub

Private Sub StyleInputCell(ByVal rng As Range)
    With rng
        .Interior.ColorIndex = 2 ' white
        .Borders.LineStyle = xlContinuous
    End With
End Sub

Private Sub ApplyBoolValidation(ByVal rng As Range)
    On Error Resume Next
    rng.Validation.Delete
    On Error GoTo 0
    With rng.Validation
        .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="TRUE,FALSE"
        .IgnoreBlank = True
        .InCellDropdown = True
    End With
End Sub

Private Sub AddButton(ByVal ws As Worksheet, ByVal anchorCell As String, ByVal shapeName As String, ByVal caption As String, ByVal macroName As String)
    Dim r As Range: Set r = ws.Range(anchorCell)

    ' delete if exists
    On Error Resume Next
    ws.Shapes(shapeName).Delete
    On Error GoTo 0

    Dim shp As Shape
    Set shp = ws.Shapes.AddFormControl(xlButtonControl, r.Left, r.Top, 170, 24)
    shp.Name = shapeName
    shp.ControlFormat.Caption = caption
    shp.OnAction = macroName
End Sub

Private Sub DeleteAllShapes(ByVal ws As Worksheet)
    Dim i As Long
    For i = ws.Shapes.Count To 1 Step -1
        ws.Shapes(i).Delete
    Next i
End Sub

' =========================================================
'  Logging
' =========================================================
Private Sub LogMsg(ByVal level As String, ByVal proc As String, ByVal msg As String, ByVal details As String)
    On Error Resume Next

    Dim ws As Worksheet: Set ws = GetOrCreateSheet(SH_LOG)
    Dim nextRow As Long
    nextRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row + 1

    ws.Cells(nextRow, "A").Value = Now
    ws.Cells(nextRow, "B").Value = level
    ws.Cells(nextRow, "C").Value = proc
    ws.Cells(nextRow, "D").Value = msg
    ws.Cells(nextRow, "E").Value = details
End Sub

' =========================================================
'  File/Folder Utilities
' =========================================================
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

Private Function CombinePath(ByVal a As String, ByVal b As String) As String
    If Len(a) = 0 Then CombinePath = b: Exit Function
    If Right$(a, 1) = "\" Or Right$(a, 1) = "/" Then
        CombinePath = a & b
    Else
        CombinePath = a & "\" & b
    End If
End Function

Private Function FileExists(ByVal path As String) As Boolean
    On Error Resume Next
    FileExists = (Len(Dir$(path, vbNormal)) > 0)
End Function

Private Function FolderExists(ByVal path As String) As Boolean
    On Error Resume Next
    FolderExists = (Len(Dir$(path, vbDirectory)) > 0)
End Function

Private Sub EnsureFolder(ByVal path As String)
    If Len(path) = 0 Then Exit Sub
    If FolderExists(path) Then Exit Sub
    MkDir path
End Sub

Private Sub CopyFilesWithBackup(ByVal srcFolder As String, ByVal pattern As String, ByVal dstFolder As String)
    Dim f As String
    f = Dir$(CombinePath(srcFolder, pattern))
    Do While Len(f) > 0
        CopySingleFileWithBackup CombinePath(srcFolder, f), CombinePath(dstFolder, f)
        f = Dir$()
    Loop
End Sub

Private Sub CopySingleFileWithBackup(ByVal srcFile As String, ByVal dstFile As String)
    Dim dstDir As String: dstDir = Left$(dstFile, InStrRev(dstFile, "\") - 1)
    EnsureFolder dstDir

    If FileExists(dstFile) Then
        Dim backupDir As String: backupDir = CombinePath(dstDir, "_backup")
        EnsureFolder backupDir
        Dim backupName As String
        backupName = CombinePath(backupDir, _
                    Left$(Mid$(dstFile, InStrRev(dstFile, "\") + 1), 200) & "." & Format(Now, "yyyymmdd_hhnnss") & ".bak")
        On Error Resume Next
        Name dstFile As backupName
        On Error GoTo 0
    End If

    FileCopy srcFile, dstFile
End Sub

Private Function FindLatestFile(ByVal folderPath As String, ByVal pattern As String) As String
    On Error GoTo EH

    Dim f As String, best As String
    Dim bestTime As Date, t As Date

    If Not FolderExists(folderPath) Then
        FindLatestFile = vbNullString
        Exit Function
    End If

    f = Dir$(CombinePath(folderPath, pattern))
    Do While Len(f) > 0
        t = FileDateTime(CombinePath(folderPath, f))
        If best = vbNullString Or t > bestTime Then
            bestTime = t
            best = CombinePath(folderPath, f)
        End If
        f = Dir$()
    Loop

    FindLatestFile = best
    Exit Function

EH:
    FindLatestFile = vbNullString
End Function

Private Sub OpenFolder(ByVal folderPath As String)
    If Not FolderExists(folderPath) Then
        MsgBox "Folder not found: " & folderPath, vbExclamation
        Exit Sub
    End If
    Shell "explorer.exe " & Q(folderPath), vbNormalFocus
End Sub

Private Sub OpenFile(ByVal filePath As String)
    If Not FileExists(filePath) Then
        MsgBox "File not found: " & filePath, vbExclamation
        Exit Sub
    End If
    Workbooks.Open filePath
End Sub

Private Sub OpenLatestOutputSilently()
    On Error Resume Next
    UI_OpenLatestOutput
End Sub

' =========================================================
'  Workbook/Sheet/Name helpers
' =========================================================
Private Function SheetExists(ByVal name As String) As Boolean
    On Error Resume Next
    SheetExists = Not ThisWorkbook.Worksheets(name) Is Nothing
    On Error GoTo 0
End Function

Private Function GetOrCreateSheet(ByVal name As String) As Worksheet
    On Error Resume Next
    Set GetOrCreateSheet = ThisWorkbook.Worksheets(name)
    On Error GoTo 0
    If GetOrCreateSheet Is Nothing Then
        Set GetOrCreateSheet = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        GetOrCreateSheet.Name = name
    End If
End Function

Private Sub DefineName(ByVal nm As String, ByVal rng As Range)
    On Error Resume Next
    ThisWorkbook.Names(nm).Delete
    On Error GoTo 0
    ThisWorkbook.Names.Add Name:=nm, RefersTo:="=" & rng.Address(External:=True)
End Sub

Private Function GetNRText(ByVal nm As String, ByVal defaultValue As String) As String
    On Error GoTo EH
    GetNRText = CStr(ThisWorkbook.Names(nm).RefersToRange.Value)
    Exit Function
EH:
    GetNRText = defaultValue
End Function

Private Sub SetNRText(ByVal nm As String, ByVal v As String)
    On Error Resume Next
    ThisWorkbook.Names(nm).RefersToRange.Value = v
End Sub

Private Function GetNRBool(ByVal nm As String, ByVal defaultValue As Boolean) As Boolean
    On Error GoTo EH
    GetNRBool = CBool(ThisWorkbook.Names(nm).RefersToRange.Value)
    Exit Function
EH:
    GetNRBool = defaultValue
End Function

