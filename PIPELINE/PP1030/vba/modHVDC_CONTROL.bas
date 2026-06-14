Option Explicit

' Ref: Excel VBA Object Model
' https://learn.microsoft.com/en-us/office/vba/api/overview/excel/object-model

Public Const SHEET_CONTROL As String = "CONTROL"
Public Const SHEET_LOG As String = "LOG"
Public Const BACKUP_SUBFOLDER As String = "_backup"

' LED 상태 상수 (p5.md 추가) - 이모지를 텍스트로 대체 (인코딩 문제 방지)
Private Const LED_IDLE As String = "[ ]"
Private Const LED_RUNNING As String = "[*]"
Private Const LED_OK As String = "[OK]"
Private Const LED_FAIL As String = "[X]"

'========================
' 0) 설치 (템플릿 생성)
'========================
Public Sub CTRL_Install()
    On Error GoTo CleanFail
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    Dim ws As Worksheet, logWs As Worksheet
    Set ws = EnsureSheet(SHEET_CONTROL, True)
    Set logWs = EnsureSheet(SHEET_LOG, False)
    InitLogSheet logWs
    
    BuildControlLayout ws
    DefineAllNames ws
    AddAllButtons ws
    
    LogInfo "CTRL_Install", "CONTROL 템플릿 생성 완료"
    MsgBox "CONTROL 템플릿 생성 완료", vbInformation

CleanExit:
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    Exit Sub

CleanFail:
    Application.DisplayAlerts = True
    Application.ScreenUpdating = True
    MsgBox "CTRL_Install 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "CTRL_Install", Err.Number, Err.Description
    Resume CleanExit
End Sub

'========================
' 1) YAML 저장 (+백업)
'========================
Public Sub CTRL_SaveAllYAML()
    On Error GoTo CleanFail
    
    ' LED 업데이트: 실행중 (p5.md 추가)
    SetLED "CONFIG_SYNC", LED_RUNNING
    SetBoard "CONFIG_SYNC", Now, "YAML 저장 중...", ""
    
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    
    Dim root As String: root = Trim$(CStr(ws.Range("B4").Value))
    If Len(root) = 0 Then Err.Raise vbObjectError + 100, , "Project Root(B4)가 비었습니다."
    
    Dim pipelineYaml As String: pipelineYaml = Trim$(CStr(ws.Range("B6").Value))
    Dim stage2Yaml As String: stage2Yaml = Trim$(CStr(ws.Range("B7").Value))
    Dim stage4Yaml As String: stage4Yaml = Trim$(CStr(ws.Range("B8").Value))
    
    If Len(pipelineYaml) = 0 Or Len(stage2Yaml) = 0 Or Len(stage4Yaml) = 0 Then
        Err.Raise vbObjectError + 101, , "Config YAML 경로(B6~B8)가 비었습니다."
    End If
    
    ' 폴더 보장
    EnsureFolder GetParentFolder(pipelineYaml)
    EnsureFolder GetParentFolder(stage2Yaml)
    EnsureFolder GetParentFolder(stage4Yaml)
    
    ' 백업 폴더 (pipelineYaml 기준)
    Dim backupDir As String
    backupDir = GetParentFolder(pipelineYaml) & "\" & BACKUP_SUBFOLDER
    EnsureFolder backupDir
    
    BackupFile pipelineYaml, backupDir
    BackupFile stage2Yaml, backupDir
    BackupFile stage4Yaml, backupDir
    
    ' YAML 내용 생성
    Dim yPipeline As String: yPipeline = BuildPipelineConfigYaml(root)
    Dim yStage2 As String: yStage2 = BuildStage2Yaml(root)
    Dim yStage4 As String: yStage4 = BuildStage4Yaml(root)
    
    ' 저장 (UTF-8)
    WriteTextUtf8 pipelineYaml, yPipeline
    WriteTextUtf8 stage2Yaml, yStage2
    WriteTextUtf8 stage4Yaml, yStage4
    
    LogInfo "CTRL_SaveAllYAML", "YAML 저장 완료: " & pipelineYaml
    LogInfo "CTRL_SaveAllYAML", "YAML 저장 완료: " & stage2Yaml
    LogInfo "CTRL_SaveAllYAML", "YAML 저장 완료: " & stage4Yaml
    
    ' LED 업데이트: 성공 (p5.md 추가)
    SetLED "CONFIG_SYNC", LED_OK
    SetBoard "CONFIG_SYNC", Now, "YAML 저장(+백업) 완료", pipelineYaml
    
    MsgBox "YAML 저장(+백업) 완료" & vbCrLf & _
           pipelineYaml & vbCrLf & stage2Yaml & vbCrLf & stage4Yaml, vbInformation
    Exit Sub

CleanFail:
    ' LED 업데이트: 실패 (p5.md 추가)
    SetLED "CONFIG_SYNC", LED_FAIL
    SetBoard "CONFIG_SYNC", Now, "YAML 저장 실패: " & Err.Description, ""
    MsgBox "CTRL_SaveAllYAML 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "CTRL_SaveAllYAML", Err.Number, Err.Description
End Sub

'========================
' 2) Browse 버튼 (공용)
'   - Shape.AlternativeText = "타겟이름정의|mode|filter"
'     예: "cfg_project_root|folder|"
'         "cfg_python_exe|file|exe"
'========================
Public Sub CTRL_BrowsePath()
    On Error GoTo CleanFail
    
    Dim caller As String: caller = CStr(Application.caller)
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    
    Dim shp As Shape: Set shp = ws.Shapes(caller)
    Dim tag As String: tag = CStr(shp.AlternativeText)
    
    If Len(tag) = 0 Then Err.Raise vbObjectError + 200, , "버튼 AlternativeText가 비었습니다: " & caller
    
    Dim parts() As String: parts = Split(tag, "|")
    Dim targetName As String: targetName = parts(0)
    Dim mode As String: mode = IIf(UBound(parts) >= 1, parts(1), "file")
    Dim filter As String: filter = IIf(UBound(parts) >= 2, parts(2), "")
    
    Dim picked As String
    If LCase$(mode) = "folder" Then
        picked = PickFolder("폴더 선택")
    Else
        picked = PickFile("파일 선택", filter)
    End If
    
    If Len(picked) = 0 Then Exit Sub 'cancel
    
    SetNamedValue targetName, picked
    LogInfo "CTRL_BrowsePath", caller & " -> " & targetName & " = " & picked
    Exit Sub

CleanFail:
    MsgBox "CTRL_BrowsePath 오류: " & Err.Number & vbCrLf & Err.Description, vbExclamation
    LogError "CTRL_BrowsePath", Err.Number, Err.Description
End Sub

'========================
' 3) Stage 실행 버튼 (p4.md 추가)
'   - run_pipeline.py --stage X 실행
'========================
Public Sub BTN_RunStage1()
    RunPipelineStage 1
End Sub

Public Sub BTN_RunStage2()
    RunPipelineStage 2
End Sub

Public Sub BTN_RunStage3()
    RunPipelineStage 3
End Sub

Public Sub BTN_RunStage4()
    RunPipelineStage 4
End Sub

Public Sub BTN_RunAll()
    ' 전체 파이프라인 순차 실행 (p5.md 추가)
    On Error GoTo CleanFail
    
    ' 1) YAML 저장
    If MsgBox("전체 파이프라인을 실행합니다." & vbCrLf & vbCrLf & _
              "1. YAML 저장" & vbCrLf & _
              "2. Stage 1 실행" & vbCrLf & _
              "3. Stage 2 실행" & vbCrLf & _
              "4. Stage 3 실행" & vbCrLf & _
              "5. Publish (S3→S4)" & vbCrLf & _
              "6. Stage 4 실행" & vbCrLf & vbCrLf & _
              "계속하시겠습니까?", vbYesNo + vbQuestion, "RUN ALL") = vbNo Then
        Exit Sub
    End If
    
    ' YAML 저장
    Call CTRL_SaveAllYAML
    If MsgBox("YAML 저장 완료. Stage 1을 실행하시겠습니까?", vbYesNo + vbQuestion) = vbNo Then Exit Sub
    
    ' Stage 1~4 순차 실행
    Call BTN_RunStage1
    If MsgBox("Stage 1 완료. Stage 2를 실행하시겠습니까?", vbYesNo + vbQuestion) = vbNo Then Exit Sub
    
    Call BTN_RunStage2
    If MsgBox("Stage 2 완료. Stage 3을 실행하시겠습니까?", vbYesNo + vbQuestion) = vbNo Then Exit Sub
    
    Call BTN_RunStage3
    If MsgBox("Stage 3 완료. Publish를 실행하시겠습니까?", vbYesNo + vbQuestion) = vbNo Then Exit Sub
    
    Call BTN_PublishStage3To4
    If MsgBox("Publish 완료. Stage 4를 실행하시겠습니까?", vbYesNo + vbQuestion) = vbNo Then Exit Sub
    
    Call BTN_RunStage4
    MsgBox "전체 파이프라인 실행 완료!", vbInformation
    Exit Sub

CleanFail:
    MsgBox "BTN_RunAll 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "BTN_RunAll", Err.Number, Err.Description
End Sub

Public Sub BTN_OpenLogsFolder()
    ' 로그 폴더 열기 (p5.md 추가)
    On Error GoTo CleanFail
    
    Dim root As String: root = Trim$(CStr(GetNamedValue("cfg_project_root")))
    Dim logDir As String: logDir = Trim$(CStr(GetNamedValue("cfg_log_dir")))
    
    If Len(root) = 0 Then
        Err.Raise vbObjectError + 600, , "Project Root가 설정되지 않았습니다(B4)."
    End If
    
    Dim absLogDir As String
    If FolderExists(logDir) Then
        absLogDir = logDir
    Else
        absLogDir = CombinePath(root, logDir)
    End If
    
    If Not FolderExists(absLogDir) Then
        EnsureFolder absLogDir
    End If
    
    Dim wsh As Object: Set wsh = CreateObject("WScript.Shell")
    wsh.Run "explorer.exe """ & absLogDir & """", 1, False
    
    LogInfo "BTN_OpenLogsFolder", "Opened: " & absLogDir
    Exit Sub

CleanFail:
    MsgBox "BTN_OpenLogsFolder 오류: " & Err.Number & vbCrLf & Err.Description, vbExclamation
    LogError "BTN_OpenLogsFolder", Err.Number, Err.Description
End Sub

Private Sub RunPipelineStage(ByVal stageNum As Long)
    On Error GoTo CleanFail
    
    Dim stageName As String
    Select Case stageNum
        Case 1: stageName = "STAGE1"
        Case 2: stageName = "STAGE2"
        Case 3: stageName = "STAGE3"
        Case 4: stageName = "STAGE4"
        Case Else: Exit Sub
    End Select
    
    ' LED 업데이트: 실행중 (p5.md 추가)
    SetLED stageName, LED_RUNNING
    SetBoard stageName, Now, "실행 중...", ""
    
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    
    Dim pyExe As String: pyExe = Trim$(CStr(GetNamedValue("cfg_python_exe")))
    Dim root As String: root = Trim$(CStr(GetNamedValue("cfg_project_root")))
    Dim logDir As String: logDir = Trim$(CStr(GetNamedValue("cfg_log_dir")))
    
    If Len(pyExe) = 0 Or Dir(pyExe) = "" Then
        Err.Raise vbObjectError + 400, , "Python EXE 경로가 유효하지 않습니다(B9)."
    End If
    If Len(root) = 0 Or Not FolderExists(root) Then
        Err.Raise vbObjectError + 401, , "Project Root 경로가 유효하지 않습니다(B4)."
    End If
    
    EnsureFolder logDir
    
    Dim scriptPath As String: scriptPath = CombinePath(root, "run\run_pipeline.py")
    If Not FileExists(scriptPath) Then
        Err.Raise vbObjectError + 402, , "run_pipeline.py를 찾을 수 없습니다: " & scriptPath
    End If
    
    Dim logFile As String
    logFile = logDir & "\stage" & stageNum & "_" & Format(Now, "yyyymmdd_hhnnss") & ".log"
    
    Dim cmd As String
    cmd = Q(pyExe) & " " & Q(scriptPath) & " --stage " & stageNum
    
    Dim wsh As Object: Set wsh = CreateObject("WScript.Shell")
    LogInfo "RunPipelineStage", "START Stage" & stageNum & ": " & cmd
    
    Application.StatusBar = "Running Stage " & stageNum & " ..."
    
    Dim rc As Long
    rc = wsh.Run(cmd, 1, True) 'visible, wait
    
    Application.StatusBar = False
    
    If rc = 0 Then
        ' LED 업데이트: 성공 (p5.md 추가)
        SetLED stageName, LED_OK
        SetBoard stageName, Now, "Stage " & stageNum & " 실행 완료", logFile
        LogInfo "RunPipelineStage", "DONE Stage" & stageNum & " (log: " & logFile & ")"
        MsgBox "Stage " & stageNum & " 실행 완료", vbInformation
    Else
        ' LED 업데이트: 실패 (p5.md 추가)
        SetLED stageName, LED_FAIL
        Dim errMsg As String: errMsg = MapExitCode(rc, stageName)
        SetBoard stageName, Now, errMsg & " (rc=" & rc & ")", logFile
        LogError "RunPipelineStage", rc, "FAIL Stage" & stageNum & " (log: " & logFile & ")"
        MsgBox errMsg & vbCrLf & "ExitCode: " & rc & vbCrLf & "로그 확인: " & logFile, vbExclamation
    End If
    
    Exit Sub

CleanFail:
    Application.StatusBar = False
    ' LED 업데이트: 실패 (p5.md 추가)
    SetLED stageName, LED_FAIL
    SetBoard stageName, Now, "VBA 오류: " & Err.Description, ""
    MsgBox "RunPipelineStage 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "RunPipelineStage", Err.Number, Err.Description
End Sub

'========================
' 4) Stage3 최신 리포트 → Stage4 publish (p4.md 추가)
'   - Stage3 Output 폴더에서 최신 리포트 찾기
'   - Stage4 Input에 자동 설정 + YAML 재저장
'========================
Public Sub BTN_PublishStage3To4()
    On Error GoTo CleanFail
    
    ' LED 업데이트: 실행중 (p5.md 추가)
    SetLED "PUBLISH", LED_RUNNING
    SetBoard "PUBLISH", Now, "Publish 중...", ""
    
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    
    Dim s3Out As String: s3Out = Trim$(CStr(GetNamedValue("st3_report_pattern")))
    If Len(s3Out) = 0 Then
        Err.Raise vbObjectError + 500, , "Stage3 Report Pattern이 비어있습니다(B40)."
    End If
    
    ' 패턴에서 폴더 경로 추출
    Dim root As String: root = Trim$(CStr(GetNamedValue("cfg_project_root")))
    Dim reportDir As String
    Dim patternFile As String
    
    ' 패턴 예: "data/processed/reports/HVDC_입고로직_종합리포트_*.xlsx"
    ' 또는 절대 경로
    If InStr(1, s3Out, ":\", vbTextCompare) > 0 Or Left$(s3Out, 2) = "\\" Then
        ' 절대 경로
        Dim lastSlash As Long: lastSlash = InStrRev(s3Out, "\")
        If lastSlash > 0 Then
            reportDir = Left$(s3Out, lastSlash - 1)
            patternFile = Mid$(s3Out, lastSlash + 1)
        Else
            Err.Raise vbObjectError + 501, , "Stage3 Report Pattern 형식이 올바르지 않습니다."
        End If
    Else
        ' 상대 경로
        reportDir = CombinePath(root, Left$(s3Out, InStrRev(s3Out, "\") - 1))
        patternFile = Mid$(s3Out, InStrRev(s3Out, "\") + 1)
    End If
    
    If Not FolderExists(reportDir) Then
        Err.Raise vbObjectError + 502, , "Stage3 Report 폴더가 존재하지 않습니다: " & reportDir
    End If
    
    ' 패턴에서 와일드카드 제거하여 Like 패턴 생성
    Dim likePattern As String: likePattern = patternFile
    
    ' 파일 검색
    Dim fso As Object: Set fso = CreateObject("Scripting.FileSystemObject")
    Dim fld As Object: Set fld = fso.GetFolder(reportDir)
    
    Dim latestFile As String: latestFile = ""
    Dim latestTime As Date: latestTime = #1/1/2000#
    Dim fil As Object
    
    For Each fil In fld.Files
        If fil.Name Like likePattern Then
            If fil.DateLastModified > latestTime Then
                latestTime = fil.DateLastModified
                latestFile = fil.Path
            End If
        End If
    Next fil
    
    If Len(latestFile) = 0 Then
        MsgBox "Stage3 리포트를 찾을 수 없습니다." & vbCrLf & _
               "폴더: " & reportDir & vbCrLf & _
               "패턴: " & likePattern, vbExclamation
        Exit Sub
    End If
    
    ' Stage4 Input에 설정 (상대 경로로 변환)
    Dim s4InputRel As String
    If LCase$(Left$(latestFile, Len(root))) = LCase$(root) Then
        s4InputRel = Mid$(latestFile, Len(root) + 1)
        ' Windows 경로를 슬래시로 변환 (YAML용)
        s4InputRel = Replace(s4InputRel, "\", "/")
        If Left$(s4InputRel, 1) = "/" Then s4InputRel = Mid$(s4InputRel, 2)
    Else
        s4InputRel = latestFile
    End If
    
    SetNamedValue "st4_input_file", s4InputRel
    
    ' YAML 재저장
    Call CTRL_SaveAllYAML
    
    ' LED 업데이트: 성공 (p5.md 추가)
    SetLED "PUBLISH", LED_OK
    SetBoard "PUBLISH", Now, "Published: " & latestFile, s4InputRel
    
    LogInfo "BTN_PublishStage3To4", "Published: " & latestFile & " -> " & s4InputRel
    MsgBox "Stage3 최신 리포트를 Stage4 Input으로 설정했습니다:" & vbCrLf & _
           latestFile & vbCrLf & vbCrLf & _
           "YAML이 자동으로 저장되었습니다.", vbInformation
    
    Exit Sub

CleanFail:
    ' LED 업데이트: 실패 (p5.md 추가)
    SetLED "PUBLISH", LED_FAIL
    SetBoard "PUBLISH", Now, "Publish 실패: " & Err.Description, ""
    MsgBox "BTN_PublishStage3To4 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "BTN_PublishStage3To4", Err.Number, Err.Description
End Sub

'========================
' 5) Python으로 Config 검증 (선택)
'   - tools/config_validator.py 를 실행
'========================
Public Sub CTRL_ValidateConfigPython()
    On Error GoTo CleanFail
    
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    
    Dim pyExe As String: pyExe = Trim$(CStr(GetNamedValue("cfg_python_exe")))
    Dim validatorPy As String: validatorPy = Trim$(CStr(GetNamedValue("cfg_validator_py")))
    Dim root As String: root = Trim$(CStr(GetNamedValue("cfg_project_root")))
    
    Dim pipelineYaml As String: pipelineYaml = Trim$(CStr(GetNamedValue("cfg_pipeline_yaml")))
    Dim stage2Yaml As String: stage2Yaml = Trim$(CStr(GetNamedValue("cfg_stage2_yaml")))
    Dim stage4Yaml As String: stage4Yaml = Trim$(CStr(GetNamedValue("cfg_stage4_yaml")))
    
    Dim logDir As String: logDir = Trim$(CStr(GetNamedValue("cfg_log_dir")))
    EnsureFolder logDir
    
    If Len(pyExe) = 0 Or Dir(pyExe) = "" Then Err.Raise vbObjectError + 300, , "Python EXE 경로가 유효하지 않습니다(B9)."
    If Len(validatorPy) = 0 Or Dir(validatorPy) = "" Then Err.Raise vbObjectError + 301, , "Validator 스크립트 경로가 유효하지 않습니다(B11)."
    
    Dim outJson As String
    outJson = logDir & "\config_validation_" & Format(Now, "yyyymmdd_hhnnss") & ".json"
    
    Dim cmd As String
    cmd = Q(pyExe) & " " & Q(validatorPy) & _
          " --project_root " & Q(root) & _
          " --pipeline_yaml " & Q(pipelineYaml) & _
          " --stage2_yaml " & Q(stage2Yaml) & _
          " --stage4_yaml " & Q(stage4Yaml) & _
          " --out_json " & Q(outJson)
    
    Dim wsh As Object: Set wsh = CreateObject("WScript.Shell")
    LogInfo "CTRL_ValidateConfigPython", "RUN: " & cmd
    
    Dim rc As Long
    rc = wsh.Run(cmd, 0, True) 'wait
    
    If rc = 0 Then
        LogInfo "CTRL_ValidateConfigPython", "OK (결과): " & outJson
        MsgBox "Config 검증 OK" & vbCrLf & outJson, vbInformation
    Else
        LogError "CTRL_ValidateConfigPython", rc, "Config 검증 FAIL (결과): " & outJson
        MsgBox "Config 검증 FAIL (rc=" & rc & ")" & vbCrLf & outJson, vbExclamation
    End If
    
    Exit Sub

CleanFail:
    MsgBox "CTRL_ValidateConfigPython 오류: " & Err.Number & vbCrLf & Err.Description, vbCritical
    LogError "CTRL_ValidateConfigPython", Err.Number, Err.Description
End Sub

'========================
' A) YAML 빌더 로직
'========================
Private Function BuildPipelineConfigYaml(ByVal projectRoot As String) As String
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets(SHEET_CONTROL)
    Dim rootNorm As String: rootNorm = NormalizeRoot(projectRoot)
    
    Dim s As String: s = ""
    
    '--- stage1 ---
    Dim st1Enabled As Boolean: st1Enabled = ParseBool(GetNamedValue("st1_enabled"), True)
    Dim masterFile As String: masterFile = Trim$(CStr(GetNamedValue("st1_master_file")))
    Dim whFile As String: whFile = NormalizePathForYaml(CStr(GetNamedValue("st1_warehouse_file")), rootNorm)
    Dim outFile As String: outFile = NormalizePathForYaml(CStr(GetNamedValue("st1_output_file")), rootNorm)
    
    Dim sortingEnabled As Boolean: sortingEnabled = ParseBool(GetNamedValue("st1_sorting_enabled"), True)
    Dim sortByMaster As Boolean: sortByMaster = ParseBool(GetNamedValue("st1_sort_by_master_no"), True)
    Dim strictKey As Boolean: strictKey = ParseBool(GetNamedValue("st1_strict_case_key"), True)
    Dim includeAll As Boolean: includeAll = ParseBool(GetNamedValue("st1_include_all_sheets"), True)
    Dim headerFallback As Boolean: headerFallback = ParseBool(GetNamedValue("st1_header_fallback"), True)
    
    Dim patternsText As String: patternsText = CStr(GetNamedValue("st1_include_patterns"))
    Dim patterns() As String: patterns = SplitLines(patternsText)
    
    s = s & "stages:" & vbCrLf
    s = s & "  stage1:" & vbCrLf
    s = s & "    description: " & YamlString("Data synchronization") & vbCrLf
    s = s & "    enabled: " & YamlBool(st1Enabled) & vbCrLf
    s = s & "    io:" & vbCrLf
    s = s & "      master_file: " & YamlStringOrAuto(masterFile) & vbCrLf
    s = s & "      warehouse_file: " & YamlString(whFile) & vbCrLf
    s = s & "      output_file: " & YamlString(outFile) & vbCrLf
    
    s = s & "    include_sheet_patterns:" & vbCrLf
    Dim i As Long
    For i = LBound(patterns) To UBound(patterns)
        If Len(Trim$(patterns(i))) > 0 Then
            s = s & "      - " & YamlString(Trim$(patterns(i))) & vbCrLf
        End If
    Next i
    
    s = s & "    sorting:" & vbCrLf
    s = s & "      enabled: " & YamlBool(sortingEnabled) & vbCrLf
    s = s & "      sort_by_master_no: " & YamlBool(sortByMaster) & vbCrLf
    
    s = s & "    options:" & vbCrLf
    s = s & "      strict_case_key: " & YamlBool(strictKey) & vbCrLf
    s = s & "      include_all_sheets: " & YamlBool(includeAll) & vbCrLf
    s = s & "      header_fallback: " & YamlBool(headerFallback) & vbCrLf
    
    '--- stage3 ---
    Dim st3Enabled As Boolean: st3Enabled = ParseBool(GetNamedValue("st3_enabled"), True)
    Dim derivedFile As String: derivedFile = NormalizePathForYaml(CStr(GetNamedValue("st3_derived_file")), rootNorm)
    Dim reportPattern As String: reportPattern = NormalizePathForYaml(CStr(GetNamedValue("st3_report_pattern")), rootNorm)
    
    s = s & "  stage3:" & vbCrLf
    s = s & "    description: " & YamlString("종합 보고서 생성") & vbCrLf
    s = s & "    enabled: " & YamlBool(st3Enabled) & vbCrLf
    s = s & "    io:" & vbCrLf
    s = s & "      derived_file: " & YamlString(derivedFile) & vbCrLf
    s = s & "      report_file: " & YamlString(reportPattern) & vbCrLf
    
    ' warehouse_config from table
    Dim rng As Range: Set rng = ThisWorkbook.Names("st3_wh_table").RefersToRange
    Dim r As Long
    
    s = s & "    warehouse_config:" & vbCrLf
    s = s & "      base_capacity_sqm:" & vbCrLf
    For r = 2 To rng.Rows.Count ' row1 header
        Dim wh As String: wh = Trim$(CStr(rng.Cells(r, 1).Value))
        If Len(wh) = 0 Then Exit For
        Dim cap As Variant: cap = rng.Cells(r, 2).Value
        s = s & "        " & YamlKey(wh) & ": " & YamlNumber(cap) & vbCrLf
    Next r
    
    s = s & "      billing_mode:" & vbCrLf
    For r = 2 To rng.Rows.Count
        wh = Trim$(CStr(rng.Cells(r, 1).Value))
        If Len(wh) = 0 Then Exit For
        Dim mode As String: mode = Trim$(CStr(rng.Cells(r, 3).Value))
        If Len(mode) = 0 Then mode = "rate"
        s = s & "        " & YamlKey(wh) & ": " & YamlString(mode) & vbCrLf
    Next r
    
    s = s & "      sqm_rates:" & vbCrLf
    For r = 2 To rng.Rows.Count
        wh = Trim$(CStr(rng.Cells(r, 1).Value))
        If Len(wh) = 0 Then Exit For
        Dim rate As Variant: rate = rng.Cells(r, 4).Value
        If Len(Trim$(CStr(rate))) > 0 Then
            s = s & "        " & YamlKey(wh) & ": " & YamlNumber(rate) & vbCrLf
        End If
    Next r
    
    BuildPipelineConfigYaml = s
End Function

Private Function BuildStage2Yaml(ByVal projectRoot As String) As String
    Dim rootNorm As String: rootNorm = NormalizeRoot(projectRoot)
    
    Dim syncedFile As String: syncedFile = NormalizePathForYaml(CStr(GetNamedValue("st2_synced_file")), rootNorm)
    Dim derivedFile As String: derivedFile = NormalizePathForYaml(CStr(GetNamedValue("st2_derived_file")), rootNorm)
    Dim preserveColors As Boolean: preserveColors = ParseBool(GetNamedValue("st2_preserve_colors"), True)
    Dim backupEnabled As Boolean: backupEnabled = ParseBool(GetNamedValue("st2_backup_enabled"), True)
    
    Dim s As String
    s = ""
    s = s & "stage:" & vbCrLf
    s = s & "  name: " & YamlString("Derived Columns") & vbCrLf
    s = s & "  version: " & YamlString("2.0.0") & vbCrLf
    s = s & "  description: " & YamlString("13개 파생 컬럼 계산 및 처리") & vbCrLf
    s = s & vbCrLf
    
    s = s & "input:" & vbCrLf
    s = s & "  synced_file: " & YamlString(syncedFile) & vbCrLf
    s = s & "  backup_enabled: " & YamlBool(backupEnabled) & vbCrLf
    s = s & vbCrLf
    
    s = s & "output:" & vbCrLf
    s = s & "  derived_file: " & YamlString(derivedFile) & vbCrLf
    s = s & "  preserve_colors: " & YamlBool(preserveColors) & vbCrLf
    s = s & "  backup_enabled: " & YamlBool(backupEnabled) & vbCrLf
    s = s & vbCrLf
    
    ' 문서 예시(고정): columns/processing/validation
    s = s & "columns:" & vbCrLf
    s = s & "  status_columns:" & vbCrLf
    s = s & "    - Status_SITE" & vbCrLf
    s = s & "    - Status_WAREHOUSE" & vbCrLf
    s = s & "    - Status_Current" & vbCrLf
    s = s & "    - Status_Location" & vbCrLf
    s = s & "    - Status_Location_Date" & vbCrLf
    s = s & "    - Status_Storage" & vbCrLf
    s = s & vbCrLf
    
    s = s & "  handling_columns:" & vbCrLf
    s = s & "    - Site_AGI_handling" & vbCrLf
    s = s & "    - WH_AGI_handling" & vbCrLf
    s = s & "    - Total_AGI_handling" & vbCrLf
    s = s & "    - Minus" & vbCrLf
    s = s & "    - Final_AGI_handling" & vbCrLf
    s = s & vbCrLf
    
    s = s & "  analysis_columns:" & vbCrLf
    s = s & "    - Stack_Status" & vbCrLf
    s = s & "    - SQM" & vbCrLf
    s = s & vbCrLf
    
    s = s & "processing:" & vbCrLf
    s = s & "  vectorization_enabled: true" & vbCrLf
    s = s & "  performance_optimization: true" & vbCrLf
    s = s & "  error_handling: " & YamlString("strict") & vbCrLf
    s = s & vbCrLf
    
    s = s & "validation:" & vbCrLf
    s = s & "  required_columns_check: true" & vbCrLf
    s = s & "  data_type_validation: true" & vbCrLf
    s = s & "  null_value_handling: " & YamlString("skip") & vbCrLf
    
    BuildStage2Yaml = s
End Function

Private Function BuildStage4Yaml(ByVal projectRoot As String) As String
    Dim rootNorm As String: rootNorm = NormalizeRoot(projectRoot)
    
    Dim inputFile As String: inputFile = NormalizePathForYaml(CStr(GetNamedValue("st4_input_file")), rootNorm)
    Dim sheetName As String: sheetName = Trim$(CStr(GetNamedValue("st4_sheet_name")))
    Dim excelOut As String: excelOut = NormalizePathForYaml(CStr(GetNamedValue("st4_excel_output")), rootNorm)
    Dim jsonOut As String: jsonOut = NormalizePathForYaml(CStr(GetNamedValue("st4_json_output")), rootNorm)
    
    Dim vizEnable As Boolean: vizEnable = ParseBool(GetNamedValue("st4_viz_enable"), False)
    Dim caseCol As String: caseCol = Trim$(CStr(GetNamedValue("st4_case_column")))
    Dim backupEnabled As Boolean: backupEnabled = ParseBool(GetNamedValue("st4_backup_enabled"), True)
    
    Dim contamination As Variant: contamination = GetNamedValue("st4_contamination")
    Dim randomState As Variant: randomState = GetNamedValue("st4_random_state")
    Dim usePyod As Boolean: usePyod = ParseBool(GetNamedValue("st4_use_pyod_first"), True)
    
    Dim iqrK As Variant: iqrK = GetNamedValue("st4_iqr_k")
    Dim madK As Variant: madK = GetNamedValue("st4_mad_k")
    Dim minGroup As Variant: minGroup = GetNamedValue("st4_min_group_size")
    Dim ruleBoost As Variant: ruleBoost = GetNamedValue("st4_rule_boost")
    Dim statHigh As Variant: statHigh = GetNamedValue("st4_stat_boost_high")
    Dim statMed As Variant: statMed = GetNamedValue("st4_stat_boost_med")
    Dim minRisk As Variant: minRisk = GetNamedValue("st4_min_risk_to_alert")
    
    Dim s As String: s = ""
    s = s & "stage4:" & vbCrLf
    s = s & "  io:" & vbCrLf
    s = s & "    input_file: " & YamlString(inputFile) & vbCrLf
    s = s & "    sheet_name: " & YamlString(sheetName) & vbCrLf
    s = s & "    excel_output: " & YamlString(excelOut) & vbCrLf
    s = s & "    json_output: " & YamlString(jsonOut) & vbCrLf
    
    s = s & "  visualization:" & vbCrLf
    s = s & "    enable_by_default: " & YamlBool(vizEnable) & vbCrLf
    s = s & "    case_column: " & YamlString(caseCol) & vbCrLf
    s = s & "    backup_enabled: " & YamlBool(backupEnabled) & vbCrLf
    
    s = s & "  model:" & vbCrLf
    s = s & "    contamination: " & YamlNumber(contamination) & vbCrLf
    s = s & "    random_state: " & YamlNumber(randomState) & vbCrLf
    s = s & "    use_pyod_first: " & YamlBool(usePyod) & vbCrLf
    
    s = s & "  detector:" & vbCrLf
    s = s & "    iqr_k: " & YamlNumber(iqrK) & vbCrLf
    s = s & "    mad_k: " & YamlNumber(madK) & vbCrLf
    s = s & "    min_group_size: " & YamlNumber(minGroup) & vbCrLf
    s = s & "    rule_boost: " & YamlNumber(ruleBoost) & vbCrLf
    s = s & "    stat_boost_high: " & YamlNumber(statHigh) & vbCrLf
    s = s & "    stat_boost_med: " & YamlNumber(statMed) & vbCrLf
    s = s & "    min_risk_to_alert: " & YamlNumber(minRisk) & vbCrLf
    
    BuildStage4Yaml = s
End Function

'========================
' B) 템플릿 작성/이름정의/버튼 생성
'========================
Private Sub BuildControlLayout(ByVal ws As Worksheet)
    ws.Cells.Clear
    On Error Resume Next
    Dim shp As Shape
    For Each shp In ws.Shapes
        shp.Delete
    Next shp
    On Error GoTo 0
    
    ' 제목 (전체 너비)
    ws.Range("A1:L1").Merge
    ws.Range("A1").Value = "HVDC PIPELINE CONTROL (Excel Only Ops)"
    ws.Range("A1").Font.Size = 16
    ws.Range("A1").Font.Bold = True
    
    ' 컬럼 너비 조정 (p5.md 설계 기준: A:C 입력, D/I 간격, E:H 상태보드, J:L 버튼)
    ws.Columns("A").ColumnWidth = 26      ' 라벨
    ws.Columns("B").ColumnWidth = 75     ' 입력 값
    ws.Columns("C").ColumnWidth = 12     ' Browse 버튼용
    ws.Columns("D").ColumnWidth = 3      ' 간격
    ws.Columns("E").ColumnWidth = 14     ' STAGE
    ws.Columns("F").ColumnWidth = 8      ' LED
    ws.Columns("G").ColumnWidth = 20     ' LAST_RUN
    ws.Columns("H").ColumnWidth = 60     ' MESSAGE / ARTIFACT
    ws.Columns("I").ColumnWidth = 3      ' 간격
    ws.Columns("J").ColumnWidth = 18     ' 버튼
    ws.Columns("K").ColumnWidth = 18     ' 버튼
    ws.Columns("L").ColumnWidth = 18     ' 버튼
    
    ' 섹션 헤더 (A:C열만 병합, p5.md 설계 기준)
    ws.Range("A3:C3").Merge: ws.Range("A3").Value = "1) PATH SETTINGS"
    ws.Range("A14:C14").Merge: ws.Range("A14").Value = "2) STAGE 1 (pipeline_config.yaml)"
    ws.Range("A31:C31").Merge: ws.Range("A31").Value = "3) STAGE 2 (stage2_derived_config.yaml)"
    ws.Range("A37:C37").Merge: ws.Range("A37").Value = "4) STAGE 3 (pipeline_config.yaml)"
    ws.Range("A62:C62").Merge: ws.Range("A62").Value = "5) STAGE 4 (stage4_anomaly.yaml)"
    
    ws.Range("A3:C3").Font.Bold = True
    ws.Range("A14:C14").Font.Bold = True
    ws.Range("A31:C31").Font.Bold = True
    ws.Range("A37:C37").Font.Bold = True
    ws.Range("A62:C62").Font.Bold = True
    
    ' PATH labels
    ws.Range("A4").Value = "Project Root"
    ws.Range("A5").Value = "Config Dir"
    ws.Range("A6").Value = "pipeline_config.yaml"
    ws.Range("A7").Value = "stage2_derived_config.yaml"
    ws.Range("A8").Value = "stage4_anomaly.yaml"
    ws.Range("A9").Value = "Python EXE"
    ws.Range("A10").Value = "Scripts Dir"
    ws.Range("A11").Value = "Validator Py"
    ws.Range("A12").Value = "Log Dir"
    
    ' 기본 수식/값
    ws.Range("B5").Formula = "=IF(B4="""","""",B4 & ""\config"")"
    ws.Range("B6").Formula = "=IF(B5="""","""",B5 & ""\pipeline_config.yaml"")"
    ws.Range("B7").Formula = "=IF(B5="""","""",B5 & ""\stage2_derived_config.yaml"")"
    ws.Range("B8").Formula = "=IF(B5="""","""",B5 & ""\stage4_anomaly.yaml"")"
    ws.Range("B10").Formula = "=IF(B4="""","""",B4 & ""\scripts"")"
    ws.Range("B11").Formula = "=IF(B4="""","""",B4 & ""\tools\config_validator.py"")"
    ws.Range("B12").Formula = "=IF(B4="""","""",B4 & ""\logs"")"
    
    ' Stage1 defaults (문서 기반)
    ws.Range("A15").Value = "Enabled": ws.Range("B15").Value = True
    ws.Range("A16").Value = "Master File": ws.Range("B16").Value = "auto"
    ws.Range("A17").Value = "Warehouse File": ws.Range("B17").Value = "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx"
    ws.Range("A18").Value = "Output File (multi-sheet)": ws.Range("B18").Value = "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
    ws.Range("A19").Value = "Output File (merged)": ws.Range("B19").Formula = "=IF(B18="""","""",LEFT(B18,LEN(B18)-5) & ""_merged.xlsx"")"
    
    ws.Range("A20").Value = "Include Patterns (1 line = 1 item)"
    ws.Range("B20:C24").Merge
    ws.Range("B20").Value = "Case List" & vbCrLf & "RIL" & vbCrLf & "HE Local" & vbCrLf & "HE-0214,0252" & vbCrLf & _
                            "SHU" & vbCrLf & "MIR" & vbCrLf & "DAS" & vbCrLf & "AGI"
    ws.Range("B20").WrapText = True
    
    ws.Range("A25").Value = "Sorting Enabled": ws.Range("B25").Value = True
    ws.Range("A26").Value = "Sort by Master No": ws.Range("B26").Value = True
    ws.Range("A27").Value = "Strict Case Key": ws.Range("B27").Value = True
    ws.Range("A28").Value = "Include All Sheets": ws.Range("B28").Value = True
    ws.Range("A29").Value = "Header Fallback": ws.Range("B29").Value = True
    
    ' Stage2 defaults
    ws.Range("A32").Value = "Synced(merged) Input": ws.Range("B32").Formula = "=B19"
    ws.Range("A33").Value = "Derived Output": ws.Range("B33").Value = "data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx"
    ws.Range("A34").Value = "Preserve Colors": ws.Range("B34").Value = True
    ws.Range("A35").Value = "Backup Enabled": ws.Range("B35").Value = True
    
    ' Stage3 defaults
    ws.Range("A38").Value = "Enabled": ws.Range("B38").Value = True
    ws.Range("A39").Value = "Derived File": ws.Range("B39").Formula = "=B33"
    ws.Range("A40").Value = "Report Pattern": ws.Range("B40").Value = "data/processed/reports/HVDC_입고로직_종합리포트_*.xlsx"
    
    ' Stage3 warehouse table header
    ws.Range("A44").Value = "Warehouse"
    ws.Range("B44").Value = "BaseCapacitySQM"
    ws.Range("C44").Value = "BillingMode"
    ws.Range("D44").Value = "SqmRate (blank=omit)"
    ws.Range("A44:D44").Font.Bold = True
    
    ' 문서 예시 기반 기본값
    ws.Range("A45:D54").ClearContents
    ws.Range("A45").Value = "DSV Al Markaz": ws.Range("B45").Value = 12000: ws.Range("C45").Value = "rate": ws.Range("D45").Value = 47#
    ws.Range("A46").Value = "DSV Indoor": ws.Range("B46").Value = 8500: ws.Range("C46").Value = "rate": ws.Range("D46").Value = 47#
    ws.Range("A47").Value = "DSV Outdoor": ws.Range("B47").Value = 15000: ws.Range("C47").Value = "rate": ws.Range("D47").Value = 18#
    ws.Range("A48").Value = "DSV MZP": ws.Range("B48").Value = 1000: ws.Range("C48").Value = "rate": ws.Range("D48").Value = 33#
    ws.Range("A49").Value = "DSV MZD": ws.Range("B49").Value = 1000: ws.Range("C49").Value = "rate"
    ws.Range("A50").Value = "AAA Storage": ws.Range("B50").Value = 2000: ws.Range("C50").Value = "passthrough"
    ws.Range("A51").Value = "Hauler Indoor": ws.Range("B51").Value = 1000: ws.Range("C51").Value = "passthrough"
    ws.Range("A52").Value = "JDN MZD": ws.Range("B52").Value = 1000: ws.Range("C52").Value = "rate": ws.Range("D52").Value = 33#
    ws.Range("A53").Value = "MOSB": ws.Range("B53").Value = 10000: ws.Range("C53").Value = "no-charge"
    ws.Range("A54").Value = "DHL Warehouse": ws.Range("B54").Value = 1000: ws.Range("C54").Value = "passthrough"
    
    ' Stage4 defaults (문서 예시 기반)
    ws.Range("A63").Value = "Input Report File": ws.Range("B63").Value = "reports/HVDC_입고로직_종합리포트_latest.xlsx"
    ws.Range("A64").Value = "Sheet Name": ws.Range("B64").Value = "통합_원본데이터_Fixed"
    ws.Range("A65").Value = "Excel Output": ws.Range("B65").Value = "reports/anomalies/anomaly_list.xlsx"
    ws.Range("A66").Value = "JSON Output": ws.Range("B66").Value = "reports/anomalies/anomaly_list.json"
    ws.Range("A67").Value = "Viz enable_by_default": ws.Range("B67").Value = False
    ws.Range("A68").Value = "Viz case_column": ws.Range("B68").Value = "Case No."
    ws.Range("A69").Value = "Backup Enabled": ws.Range("B69").Value = True
    ws.Range("A70").Value = "contamination": ws.Range("B70").Value = 0.02
    ws.Range("A71").Value = "random_state": ws.Range("B71").Value = 42
    ws.Range("A72").Value = "use_pyod_first": ws.Range("B72").Value = True
    ws.Range("A73").Value = "iqr_k": ws.Range("B73").Value = 1.5
    ws.Range("A74").Value = "mad_k": ws.Range("B74").Value = 3.5
    ws.Range("A75").Value = "min_group_size": ws.Range("B75").Value = 10
    ws.Range("A76").Value = "rule_boost": ws.Range("B76").Value = 0.25
    ws.Range("A77").Value = "stat_boost_high": ws.Range("B77").Value = 0.15
    ws.Range("A78").Value = "stat_boost_med": ws.Range("B78").Value = 0.08
    ws.Range("A79").Value = "min_risk_to_alert": ws.Range("B79").Value = 0.9
    
    ' 데이터 검증 (간단)
    AddBoolValidation ws.Range("B15,B25,B26,B27,B28,B29,B34,B35,B38,B67,B69,B72")
    AddListValidation ws.Range("C45:C60"), "rate,passthrough,no-charge"
    
    ' --------------------
    ' STATUS BOARD (E:H) - p5.md 추가
    ' --------------------
    With ws.Range("E3:H3")
        .Merge
        .Value = "STATUS BOARD"
        .Font.Bold = True
        .HorizontalAlignment = xlCenter
    End With
    
    ws.Range("E4").Value = "STAGE"
    ws.Range("F4").Value = "LED"
    ws.Range("G4").Value = "LAST_RUN"
    ws.Range("H4").Value = "MESSAGE / ARTIFACT"
    ws.Range("E4:H4").Font.Bold = True
    
    ' 상태보드 초기화
    InitStatusRow ws, 5, "CONFIG_SYNC"
    InitStatusRow ws, 6, "STAGE1"
    InitStatusRow ws, 7, "STAGE2"
    InitStatusRow ws, 8, "STAGE3"
    InitStatusRow ws, 9, "PUBLISH"
    InitStatusRow ws, 10, "STAGE4"
    
    ' 컬럼 너비 조정
    ws.Columns("E").ColumnWidth = 14
    ws.Columns("F").ColumnWidth = 8
    ws.Columns("G").ColumnWidth = 20
    ws.Columns("H").ColumnWidth = 60
    
    ' 테두리
    ws.Range("E4:H10").Borders.LineStyle = xlContinuous
    
    ws.Range("A1").Select
End Sub

Private Sub DefineAllNames(ByVal ws As Worksheet)
    ' System
    AddOrReplaceName "cfg_project_root", ws.Range("B4")
    AddOrReplaceName "cfg_config_dir", ws.Range("B5")
    AddOrReplaceName "cfg_pipeline_yaml", ws.Range("B6")
    AddOrReplaceName "cfg_stage2_yaml", ws.Range("B7")
    AddOrReplaceName "cfg_stage4_yaml", ws.Range("B8")
    AddOrReplaceName "cfg_python_exe", ws.Range("B9")
    AddOrReplaceName "cfg_scripts_dir", ws.Range("B10")
    AddOrReplaceName "cfg_validator_py", ws.Range("B11")
    AddOrReplaceName "cfg_log_dir", ws.Range("B12")
    
    ' Stage1
    AddOrReplaceName "st1_enabled", ws.Range("B15")
    AddOrReplaceName "st1_master_file", ws.Range("B16")
    AddOrReplaceName "st1_warehouse_file", ws.Range("B17")
    AddOrReplaceName "st1_output_file", ws.Range("B18")
    AddOrReplaceName "st1_output_merged_file", ws.Range("B19")
    AddOrReplaceName "st1_include_patterns", ws.Range("B20")
    AddOrReplaceName "st1_sorting_enabled", ws.Range("B25")
    AddOrReplaceName "st1_sort_by_master_no", ws.Range("B26")
    AddOrReplaceName "st1_strict_case_key", ws.Range("B27")
    AddOrReplaceName "st1_include_all_sheets", ws.Range("B28")
    AddOrReplaceName "st1_header_fallback", ws.Range("B29")
    
    ' Stage2
    AddOrReplaceName "st2_synced_file", ws.Range("B32")
    AddOrReplaceName "st2_derived_file", ws.Range("B33")
    AddOrReplaceName "st2_preserve_colors", ws.Range("B34")
    AddOrReplaceName "st2_backup_enabled", ws.Range("B35")
    
    ' Stage3
    AddOrReplaceName "st3_enabled", ws.Range("B38")
    AddOrReplaceName "st3_derived_file", ws.Range("B39")
    AddOrReplaceName "st3_report_pattern", ws.Range("B40")
    AddOrReplaceName "st3_wh_table", ws.Range("A44:D60")
    
    ' Stage4
    AddOrReplaceName "st4_input_file", ws.Range("B63")
    AddOrReplaceName "st4_sheet_name", ws.Range("B64")
    AddOrReplaceName "st4_excel_output", ws.Range("B65")
    AddOrReplaceName "st4_json_output", ws.Range("B66")
    AddOrReplaceName "st4_viz_enable", ws.Range("B67")
    AddOrReplaceName "st4_case_column", ws.Range("B68")
    AddOrReplaceName "st4_backup_enabled", ws.Range("B69")
    AddOrReplaceName "st4_contamination", ws.Range("B70")
    AddOrReplaceName "st4_random_state", ws.Range("B71")
    AddOrReplaceName "st4_use_pyod_first", ws.Range("B72")
    AddOrReplaceName "st4_iqr_k", ws.Range("B73")
    AddOrReplaceName "st4_mad_k", ws.Range("B74")
    AddOrReplaceName "st4_min_group_size", ws.Range("B75")
    AddOrReplaceName "st4_rule_boost", ws.Range("B76")
    AddOrReplaceName "st4_stat_boost_high", ws.Range("B77")
    AddOrReplaceName "st4_stat_boost_med", ws.Range("B78")
    AddOrReplaceName "st4_min_risk_to_alert", ws.Range("B79")
End Sub

Private Sub AddAllButtons(ByVal ws As Worksheet)
    ' 버튼 영역 헤더 (J:L열, p5.md 설계 기준)
    With ws.Range("J3:L3")
        .Merge
        .Value = "ACTIONS"
        .Font.Bold = True
        .HorizontalAlignment = xlCenter
    End With
    
    ' 버튼 배치 (J열, 상태보드와 같은 행에 맞춤) - 이모지 제거 (인코딩 문제 방지)
    AddButton ws, ws.Range("J4"), 180, 28, "btnInitTemplate", "[SETUP] CONTROL", "CTRL_Install", ""
    AddButton ws, ws.Range("J5"), 180, 28, "btnSaveYamlAll", "[SAVE] YAML 반영(백업)", "CTRL_SaveAllYAML", ""
    AddButton ws, ws.Range("J6"), 180, 28, "btnRunStage1", "[RUN] Stage1", "BTN_RunStage1", ""
    AddButton ws, ws.Range("J7"), 180, 28, "btnRunStage2", "[RUN] Stage2", "BTN_RunStage2", ""
    AddButton ws, ws.Range("J8"), 180, 28, "btnRunStage3", "[RUN] Stage3", "BTN_RunStage3", ""
    AddButton ws, ws.Range("J9"), 180, 28, "btnPublish", "[PUBLISH] S3→S4", "BTN_PublishStage3To4", ""
    AddButton ws, ws.Range("J10"), 180, 28, "btnRunStage4", "[RUN] Stage4", "BTN_RunStage4", ""
    AddButton ws, ws.Range("J11"), 180, 28, "btnRunAll", "[RUN ALL] 1→4", "BTN_RunAll", ""
    AddButton ws, ws.Range("J12"), 180, 28, "btnOpenLogs", "[LOGS] Open", "BTN_OpenLogsFolder", ""
    
    ' Browse buttons (C열, AlternativeText로 타겟 지정)
    AddButton ws, ws.Range("C4"), 70, 18, "btnBrowseProjectRoot", "Browse", "CTRL_BrowsePath", "cfg_project_root|folder|"
    AddButton ws, ws.Range("C9"), 70, 18, "btnBrowsePythonExe", "Browse", "CTRL_BrowsePath", "cfg_python_exe|file|exe"
    AddButton ws, ws.Range("C16"), 70, 18, "btnBrowseMaster", "Browse", "CTRL_BrowsePath", "st1_master_file|file|xlsx"
    AddButton ws, ws.Range("C17"), 70, 18, "btnBrowseWarehouse", "Browse", "CTRL_BrowsePath", "st1_warehouse_file|file|xlsx"
End Sub

'========================
' C) 유틸(파일/폴더/로그/검증)
'========================
Private Function EnsureSheet(ByVal name As String, ByVal clearAll As Boolean) As Worksheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(name)
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Worksheets(ThisWorkbook.Worksheets.Count))
        ws.name = name
    End If
    
    If clearAll Then
        ws.Cells.Clear
        On Error Resume Next
        Dim shp As Shape
        For Each shp In ws.Shapes
            shp.Delete
        Next shp
        On Error GoTo 0
    End If
    
    Set EnsureSheet = ws
End Function

Private Sub InitLogSheet(ByVal ws As Worksheet)
    If ws.Cells(1, 1).Value = "" Then
        ws.Range("A1:E1").Value = Array("Timestamp", "Level", "Procedure", "Code", "Message")
        ws.Rows(1).Font.Bold = True
        ws.Columns("A").ColumnWidth = 22
        ws.Columns("B").ColumnWidth = 10
        ws.Columns("C").ColumnWidth = 24
        ws.Columns("D").ColumnWidth = 10
        ws.Columns("E").ColumnWidth = 120
    End If
End Sub

Private Sub LogInfo(ByVal proc As String, ByVal msg As String)
    LogWrite "INFO", proc, 0, msg
End Sub

Private Sub LogError(ByVal proc As String, ByVal code As Long, ByVal msg As String)
    LogWrite "ERROR", proc, code, msg
End Sub

Private Sub LogWrite(ByVal level As String, ByVal proc As String, ByVal code As Long, ByVal msg As String)
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets(SHEET_LOG)
    On Error GoTo 0
    If ws Is Nothing Then Exit Sub
    
    Dim r As Long
    r = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
    ws.Cells(r, 1).Value = Now
    ws.Cells(r, 2).Value = level
    ws.Cells(r, 3).Value = proc
    ws.Cells(r, 4).Value = code
    ws.Cells(r, 5).Value = msg
End Sub

Private Sub AddOrReplaceName(ByVal nm As String, ByVal rng As Range)
    On Error Resume Next
    ThisWorkbook.Names(nm).Delete
    On Error GoTo 0
    ThisWorkbook.Names.Add name:=nm, RefersTo:=rng
End Sub

Private Function GetNamedValue(ByVal nm As String) As Variant
    On Error GoTo Fail
    GetNamedValue = ThisWorkbook.Names(nm).RefersToRange.Value
    Exit Function
Fail:
    GetNamedValue = vbNullString
End Function

Private Sub SetNamedValue(ByVal nm As String, ByVal v As Variant)
    On Error GoTo Fail
    ThisWorkbook.Names(nm).RefersToRange.Value = v
    Exit Sub
Fail:
    Err.Raise vbObjectError + 910, , "이름정의가 없거나 범위 참조 실패: " & nm
End Sub

Private Sub AddButton(ByVal ws As Worksheet, ByVal topLeft As Range, ByVal w As Double, ByVal h As Double, _
                      ByVal btnName As String, ByVal caption As String, ByVal macroName As String, ByVal altText As String)
    Dim shp As Shape
    On Error Resume Next
    ws.Shapes(btnName).Delete
    On Error GoTo 0
    
    Set shp = ws.Shapes.AddFormControl(xlButtonControl, topLeft.Left, topLeft.Top, w, h)
    shp.name = btnName
    shp.OnAction = macroName
    shp.TextFrame.Characters.text = caption
    shp.AlternativeText = altText
End Sub

Private Sub EnsureFolder(ByVal folderPath As String)
    If Len(folderPath) = 0 Then Exit Sub
    Dim fso As Object: Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FolderExists(folderPath) Then
        fso.CreateFolder folderPath
    End If
End Sub

Private Sub BackupFile(ByVal filePath As String, ByVal backupDir As String)
    If Len(filePath) = 0 Then Exit Sub
    If Dir(filePath) = "" Then Exit Sub
    
    EnsureFolder backupDir
    
    Dim ts As String: ts = Format(Now, "yyyymmdd_hhnnss")
    Dim base As String: base = GetFileBaseName(filePath)
    Dim ext As String: ext = GetFileExt(filePath)
    
    Dim dst As String
    dst = backupDir & "\" & base & "_" & ts & ".bak." & ext
    
    Dim fso As Object: Set fso = CreateObject("Scripting.FileSystemObject")
    fso.CopyFile filePath, dst, True
End Sub

Private Sub WriteTextUtf8(ByVal filePath As String, ByVal text As String)
    Dim stm As Object: Set stm = CreateObject("ADODB.Stream")
    stm.Type = 2 'text
    stm.Charset = "utf-8"
    stm.Open
    stm.WriteText text
    stm.SaveToFile filePath, 2 'overwrite
    stm.Close
End Sub

Private Function GetParentFolder(ByVal path As String) As String
    Dim p As Long: p = InStrRev(path, "\")
    If p = 0 Then
        GetParentFolder = ""
    Else
        GetParentFolder = Left$(path, p - 1)
    End If
End Function

Private Function CombinePath(ByVal basePath As String, ByVal relPath As String) As String
    If Len(basePath) = 0 Then
        CombinePath = relPath
        Exit Function
    End If
    If Right$(basePath, 1) = "\" Or Right$(basePath, 1) = "/" Then
        CombinePath = basePath & relPath
    Else
        CombinePath = basePath & "\" & relPath
    End If
End Function

Private Function FolderExists(ByVal folderPath As String) As Boolean
    On Error Resume Next
    Dim fso As Object: Set fso = CreateObject("Scripting.FileSystemObject")
    FolderExists = fso.FolderExists(folderPath)
    On Error GoTo 0
End Function

Private Function FileExists(ByVal filePath As String) As Boolean
    On Error Resume Next
    FileExists = (Len(Dir$(filePath, vbNormal)) > 0)
    On Error GoTo 0
End Function

Private Function GetFileBaseName(ByVal path As String) As String
    Dim fn As String: fn = path
    Dim p As Long: p = InStrRev(fn, "\")
    If p > 0 Then fn = Mid$(fn, p + 1)
    Dim d As Long: d = InStrRev(fn, ".")
    If d > 0 Then fn = Left$(fn, d - 1)
    GetFileBaseName = fn
End Function

Private Function GetFileExt(ByVal path As String) As String
    Dim fn As String: fn = path
    Dim d As Long: d = InStrRev(fn, ".")
    If d > 0 Then
        GetFileExt = Mid$(fn, d + 1)
    Else
        GetFileExt = ""
    End If
End Function

Private Function Q(ByVal s As String) As String
    Q = """" & s & """"
End Function

Private Function PickFolder(ByVal title As String) As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFolderPicker)
    fd.title = title
    If fd.Show = -1 Then
        PickFolder = fd.SelectedItems(1)
    Else
        PickFolder = ""
    End If
End Function

Private Function PickFile(ByVal title As String, Optional ByVal filter As String = "") As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    fd.title = title
    fd.AllowMultiSelect = False
    fd.Filters.Clear
    
    Dim f As String: f = LCase$(Trim$(filter))
    If f = "xlsx" Then
        fd.Filters.Add "Excel", "*.xlsx;*.xlsm;*.xls"
    ElseIf f = "exe" Then
        fd.Filters.Add "Executable", "*.exe"
    ElseIf Len(f) > 0 Then
        fd.Filters.Add "Files", "*." & f
    Else
        fd.Filters.Add "All", "*.*"
    End If
    
    If fd.Show = -1 Then
        PickFile = fd.SelectedItems(1)
    Else
        PickFile = ""
    End If
End Function

Private Sub AddBoolValidation(ByVal rng As Range)
    On Error Resume Next
    rng.Validation.Delete
    rng.Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:="TRUE,FALSE"
    On Error GoTo 0
End Sub

Private Sub AddListValidation(ByVal rng As Range, ByVal csv As String)
    On Error Resume Next
    rng.Validation.Delete
    rng.Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Operator:=xlBetween, Formula1:=csv
    On Error GoTo 0
End Sub

Private Function ParseBool(ByVal v As Variant, Optional ByVal defaultVal As Boolean = False) As Boolean
    Dim s As String: s = UCase$(Trim$(CStr(v)))
    If s = "TRUE" Or s = "1" Or s = "YES" Or s = "Y" Then
        ParseBool = True
    ElseIf s = "FALSE" Or s = "0" Or s = "NO" Or s = "N" Then
        ParseBool = False
    Else
        ParseBool = defaultVal
    End If
End Function

Private Function NormalizeRoot(ByVal root As String) As String
    root = Replace(root, "/", "\")
    If Right$(root, 1) <> "\" Then root = root & "\"
    NormalizeRoot = root
End Function

Private Function NormalizePathForYaml(ByVal pathVal As String, ByVal rootNorm As String) As String
    Dim p As String: p = Trim$(pathVal)
    If Len(p) = 0 Then NormalizePathForYaml = "": Exit Function
    
    ' auto(그대로), YAML 출력 함수에서 별도 처리
    If LCase$(p) = "auto" Then NormalizePathForYaml = "auto": Exit Function
    
    ' 일단 Windows 스타일로 정규화
    p = Replace(p, "/", "\")
    
    Dim isAbs As Boolean
    isAbs = (InStr(1, p, ":\", vbTextCompare) > 0) Or (Left$(p, 2) = "\\")
    
    Dim rel As String
    If isAbs Then
        If Len(rootNorm) > 0 And LCase$(Left$(p, Len(rootNorm))) = LCase$(rootNorm) Then
            rel = Mid$(p, Len(rootNorm) + 1)
        Else
            rel = p
        End If
    Else
        rel = p
    End If
    
    ' YAML은 "/"로 통일
    NormalizePathForYaml = Replace(rel, "\", "/")
End Function

Private Function YamlBool(ByVal b As Boolean) As String
    If b Then YamlBool = "true" Else YamlBool = "false"
End Function

Private Function YamlNumber(ByVal v As Variant) As String
    If IsNumeric(v) Then
        YamlNumber = CStr(v)
    Else
        YamlNumber = "0"
    End If
End Function

Private Function YamlKey(ByVal s As String) As String
    ' warehouse name처럼 공백이 있는 키는 반드시 따옴표
    YamlKey = YamlString(s)
End Function

Private Function YamlString(ByVal s As String) As String
    Dim t As String: t = CStr(s)
    t = Replace(t, """", "\""")  ' " -> \"
    YamlString = """" & t & """"
End Function

Private Function YamlStringOrAuto(ByVal s As String) As String
    Dim t As String: t = LCase$(Trim$(CStr(s)))
    If t = "auto" Then
        YamlStringOrAuto = "auto"
    Else
        YamlStringOrAuto = YamlString(NormalizePathForYaml(CStr(s), NormalizeRoot(CStr(GetNamedValue("cfg_project_root")))))
    End If
End Function

Private Function SplitLines(ByVal s As String) As String()
    Dim t As String: t = Replace(s, vbCrLf, vbLf)
    t = Replace(t, vbCr, vbLf)
    SplitLines = Split(t, vbLf)
End Function

'========================
' STATUS BOARD (p5.md 추가)
'========================
Private Sub InitStatusRow(ByVal ws As Worksheet, ByVal r As Long, ByVal stage As String)
    ws.Cells(r, "E").Value = stage
    ws.Cells(r, "F").Value = LED_IDLE
    ws.Cells(r, "G").Value = ""
    ws.Cells(r, "H").Value = ""
End Sub

Private Sub SetLED(ByVal stage As String, ByVal led As String)
    Dim r As Long: r = BoardRow(stage)
    With ThisWorkbook.Worksheets(SHEET_CONTROL)
        .Cells(r, "F").Value = led
    End With
End Sub

Private Sub SetBoard(ByVal stage As String, ByVal dt As Date, ByVal message As String, ByVal artifact As String)
    Dim r As Long: r = BoardRow(stage)
    With ThisWorkbook.Worksheets(SHEET_CONTROL)
        .Cells(r, "G").Value = Format(dt, "yyyy-mm-dd hh:nn:ss")
        .Cells(r, "H").Value = message
        
        ' Artifact를 하이퍼링크로 추가 (파일 존재 시)
        If Len(artifact) > 0 Then
            On Error Resume Next
            .Cells(r, "H").Hyperlinks.Delete
            On Error GoTo 0
            If FileExists(artifact) Then
                .Hyperlinks.Add Anchor:=.Cells(r, "H"), Address:=artifact, _
                    TextToDisplay:=message & vbCrLf & artifact
            End If
        End If
    End With
End Sub

Private Function BoardRow(ByVal stage As String) As Long
    Select Case UCase$(stage)
        Case "CONFIG_SYNC": BoardRow = 5
        Case "STAGE1": BoardRow = 6
        Case "STAGE2": BoardRow = 7
        Case "STAGE3": BoardRow = 8
        Case "PUBLISH": BoardRow = 9
        Case "STAGE4": BoardRow = 10
        Case Else: BoardRow = 10
    End Select
End Function

'========================
' EXIT CODE → MSG (p5.md 추가)
'========================
Private Function MapExitCode(ByVal code As Long, ByVal stage As String) As String
    Select Case code
        Case 10: MapExitCode = "CONFIG 오류 (YAML 파싱/경로 누락)"
        Case 11: MapExitCode = "입력 파일 없음/패턴 매칭 실패"
        Case 12: MapExitCode = "출력/로그 폴더 생성 실패"
        Case 20: MapExitCode = "Stage1 실행 실패"
        Case 30: MapExitCode = "Stage2 실행 실패"
        Case 40: MapExitCode = "Stage3 실행 실패"
        Case 50: MapExitCode = "Stage4 실행 실패"
        Case 60: MapExitCode = "Publish 실패 (Stage3 최신 리포트 탐색/복사 실패)"
        Case 90: MapExitCode = "예상치 못한 오류"
        Case Else: MapExitCode = "실행 실패 (ExitCode=" & code & ")"
    End Select
End Function