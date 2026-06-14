Attribute VB_Name = "modPipelineLauncher"
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
    cmd = BuildCmd(root, pyExe, relScript, args, logFile)

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

Private Function BuildCmd(ByVal workDir As String, ByVal pyExe As String, ByVal relScript As String, ByVal args As String, ByVal logFile As String) As String
    ' cmd /c "cd /d <workDir> && <pyExe> <script> <args> > <log> 2>&1"
    ' 타임스탬프가 파일명에 포함되어 있으므로 매번 새 파일 생성 (overwrite 모드)
    ' relScript에는 전체 명령어가 포함될 수 있음 (예: "run\run_pipeline.py --stage 1")
    Dim inner As String
    inner = "cd /d " & Q(workDir) & " && " & QuoteExe(pyExe) & " " & relScript
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

