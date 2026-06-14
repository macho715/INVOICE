Attribute VB_Name = "modCompileMaster"
Option Explicit

'================================================================
' Module: modCompileMaster
' Purpose: ��� ��Ʈ�� ��ȸ�ϸ� '������ ��'�� ���͸��Ͽ� ������ ��Ʈ�� ����
'================================================================

'--- ���� ���� ���ν��� ---
Public Sub CompileAllSheets()
    Dim t0 As Single: t0 = Timer

    '--- 1. ȯ�� ���� �� ��� ��Ʈ �غ� ---
    On Error GoTo ErrH
    Application.ScreenUpdating = False

    Dim outWS As Worksheet
    On Error Resume Next
    Set outWS = ThisWorkbook.Worksheets("MasterData")
    If outWS Is Nothing Then
        Set outWS = ThisWorkbook.Worksheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        outWS.Name = "MasterData"
    End If
    On Error GoTo ErrH
    outWS.Cells.Clear

    '--- 2. ������ ��Ʈ�� ��� �ۼ� ---
    Dim headers As Variant
    headers = Array("CWI Job Number", "Order Ref. Number", "S/No", "RATE SOURCE", "DESCRIPTION", "RATE", "Formula", "Q'TY", "TOTAL (USD)", "REMARK", "REV RATE", "REV TOTAL", "DIFFERENCE")
    outWS.Range("A1").Resize(1, UBound(headers) + 1).Value = headers
    ' outWS.Rows(1).Font.Bold = True  ' 제거됨

    '--- 3. ��� ��Ʈ�� ��ȸ�ϸ� ������ ���� ---
    Dim ws As Worksheet
    Dim writeRow As Long: writeRow = 2

    For Each ws In ThisWorkbook.Worksheets
        ' ������ ��Ʈ�̰ų� ������ ��Ʈ�� �ǳʶٱ�
        If ws.Name <> outWS.Name And ws.Visible = xlSheetVisible Then

            '--- 4. ��Ʈ ����� ��� ���� ���� ---
            Dim jobNum As String, orderRef As String
            jobNum = GetValueFromLabel(ws, "CW1 Job Number")
            orderRef = GetValueFromLabel(ws, "Order Ref. Number")

            '--- 5. [���� ����] ��Ʈ�� ��� ���� �˻��Ͽ� ������ �ุ ���� ---
            Dim firstHeaderRow As Long, lastUsedRow As Long
            Dim snCol As Long, lastCol As Long
            Dim r As Long

            ' S/No ����� ã�� ���� ���� ����
            firstHeaderRow = FindHeaderRow(ws, "S/No")
            If firstHeaderRow > 0 Then
                snCol = FindCol(ws, firstHeaderRow, "S/No")
                lastCol = ws.Cells(firstHeaderRow, ws.Columns.Count).End(xlToLeft).Column
                lastUsedRow = ws.Cells(ws.Rows.Count, snCol).End(xlUp).Row

                ' ��� �Ʒ����� ������ ���� ����� ��ȸ
                For r = firstHeaderRow + 1 To lastUsedRow
                    ' S/No ���� ���ڰ� �ִ� �ุ ������ ������ ����
                    If IsNumeric(ws.Cells(r, snCol).Value) And Not IsEmpty(ws.Cells(r, snCol).Value) Then
                        ' ��� ���� ����
                        outWS.Cells(writeRow, 1).Value = jobNum
                        outWS.Cells(writeRow, 2).Value = orderRef

                        ' ������ �� ��ü ����
                        ws.Range(ws.Cells(r, snCol), ws.Cells(r, lastCol)).Copy
                        outWS.Cells(writeRow, 3).PasteSpecial xlPasteValues

                        writeRow = writeRow + 1
                    End If
                Next r
            End If
        End If
    Next ws

    '--- 6. ������ (서식 코드 제거됨) ---
    Application.CutCopyMode = False
    ' outWS.Columns.AutoFit  ' 제거됨
    Application.ScreenUpdating = True
    MsgBox "��� ��Ʈ�� ������ �� ���� �Ϸ�!", vbInformation, "�۾� �Ϸ�"
    Exit Sub

ErrH:
    Application.CutCopyMode = False
    Application.ScreenUpdating = True
    MsgBox "���� �߻�: " & Err.description, vbCritical, "����"
End Sub


'--- ���� �Լ� (Helper Functions) ---

Private Function GetValueFromLabel(ws As Worksheet, labelText As String) As String
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.UsedRange.Find(What:=labelText, LookIn:=xlValues, LookAt:=xlPart)
    On Error GoTo 0

    If Not foundCell Is Nothing Then
        GetValueFromLabel = CStr(foundCell.Offset(0, 1).Value)
    Else
        GetValueFromLabel = ""
    End If
End Function

Private Function FindHeaderRow(ws As Worksheet, headerText As String) As Long
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.UsedRange.Find(What:=headerText, LookIn:=xlValues, LookAt:=xlWhole)
    On Error GoTo 0

    If Not foundCell Is Nothing Then
        FindHeaderRow = foundCell.Row
    Else
        FindHeaderRow = 0
    End If
End Function

Private Function FindCol(ws As Worksheet, r As Long, headerText As String) As Long
    Dim foundCell As Range
    On Error Resume Next
    Set foundCell = ws.Rows(r).Find(What:=headerText, LookIn:=xlValues, LookAt:=xlWhole)
    On Error GoTo 0

    If Not foundCell Is Nothing Then
        FindCol = foundCell.Column
    Else
        FindCol = 0
    End If
End Function
