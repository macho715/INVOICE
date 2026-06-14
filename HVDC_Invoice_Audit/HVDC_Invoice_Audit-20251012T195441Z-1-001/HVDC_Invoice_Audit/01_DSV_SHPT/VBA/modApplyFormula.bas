Attribute VB_Name = "modApplyFormula"
Option Explicit
'==========================
' Module: modApplyFormula (Step 2 - ���� �ϼ� ����)
'==========================

'--- ��� ��� ---
Private Const HDR_REMARK As String = "REMARK"
Private Const HDR_TOTAL As String = "TOTAL (USD)"
Private Const HDR_RATE As String = "RATE"
Private Const HDR_QTY As String = "Q'TY"
Private Const HDR_REV1 As String = "REV RATE"
Private Const HDR_REV2 As String = "REV TOTAL"
Private Const HDR_DIFF As String = "DIFFERENCE"
Private Const EXCLUDE_SHEET1 As String = "SUMMARY"
Private Const EXCLUDE_SHEET2 As String = "DEC"
Private Const EXCLUDE_SHEET3 As String = "MasterData"

'--- ���� �Լ� ---
Private Function FindHeaderCol(ByVal ws As Worksheet, ByVal headerRow As Long, ByVal headerText As String) As Long
    Dim c As Range
    On Error Resume Next
    Set c = ws.Rows(headerRow).Find(What:=headerText, LookIn:=xlValues, LookAt:=xlWhole, MatchCase:=False)
    On Error GoTo 0
    If Not c Is Nothing Then FindHeaderCol = c.Column
End Function

'--- ���� ���� ���ν��� ---
Public Sub ApplyFormula_ByDynamicRemark_ExactTotal_Safe()
    Dim t0 As Single: t0 = Timer
    On Error GoTo ErrH
    AppBegin "ApplyFormula"
    LogActionSafe "ApplyFormula", "BEGIN"

    ApplyFormula_Impl

    LogActionSafe "ApplyFormula", "END " & Format(Timer - t0, "0.00s")
Done:
    AppEnd
    Exit Sub
ErrH:
    LogActionSafe "ApplyFormula", "ERR: " & Err.description & " (" & Err.Number & ")"
    Resume Done
End Sub

'--- ���� ���� ������ ---
Private Sub ApplyFormula_Impl()
    Dim ws As Worksheet, remarkCell As Range, totalCell As Range
    Dim headerRow As Long, revCol As Long
    Dim lLastRow As Long
    Dim rateCol As Long, qtyCol As Long, totalCol As Long, descCol As Long

    For Each ws In ThisWorkbook.Worksheets
        If ws.Visible = xlSheetVisible And UCase(ws.Name) <> EXCLUDE_SHEET1 And UCase(ws.Name) <> EXCLUDE_SHEET2 And UCase(ws.Name) <> EXCLUDE_SHEET3 Then

            Set remarkCell = SafeFind(ws, HDR_REMARK, True)
            If remarkCell Is Nothing Then GoTo NextWs

            headerRow = remarkCell.Row

            ' [GEMINI FIX] ������ ���� �Ǵ� ������ 'DESCRIPTION' ���� ����
            descCol = FindHeaderCol(ws, headerRow, "DESCRIPTION")
            If descCol = 0 Then GoTo NextWs ' DESCRIPTION ����� ������ ��ŵ

            lLastRow = lastDataRow(ws, descCol)

            If lLastRow <= headerRow Then GoTo NextWs

            rateCol = FindHeaderCol(ws, headerRow, HDR_RATE)
            qtyCol = FindHeaderCol(ws, headerRow, HDR_QTY)
            totalCol = FindHeaderCol(ws, headerRow, HDR_TOTAL)

            If rateCol = 0 Or qtyCol = 0 Or totalCol = 0 Then GoTo NextWs

            revCol = remarkCell.Column + 1
            ws.Cells(headerRow, revCol).Value = HDR_REV1
            ws.Cells(headerRow, revCol + 1).Value = HDR_REV2
            ws.Cells(headerRow, revCol + 2).Value = HDR_DIFF
            ' ws.Range(ws.Cells(headerRow, revCol), ws.Cells(headerRow, revCol + 2)).Font.Bold = True  ' 제거됨

            ClearRange ws.Range(ws.Cells(headerRow + 1, revCol), ws.Cells(lLastRow, revCol + 2))

            ws.Range(ws.Cells(headerRow + 1, revCol), ws.Cells(lLastRow, revCol)).FormulaR1C1 = "=ROUND(RC" & rateCol & ",2)"
            ws.Range(ws.Cells(headerRow + 1, revCol + 1), ws.Cells(lLastRow, revCol + 1)).FormulaR1C1 = "=RC[-1]*RC" & qtyCol
            ws.Range(ws.Cells(headerRow + 1, revCol + 2), ws.Cells(lLastRow, revCol + 2)).FormulaR1C1 = "=RC[-1]-RC" & totalCol

            Set totalCell = SafeFind(ws, "TOTAL", True)

            If Not totalCell Is Nothing Then
                With ws.Cells(totalCell.Row, revCol + 1)
                    .FormulaR1C1 = "=SUM(R" & (headerRow + 1) & "C:R[-1]C)"
                    ' .Font.Color = RGB(255, 0, 0)  ' 제거됨
                    ' .Font.Bold = True  ' 제거됨
                End With
                With ws.Cells(totalCell.Row, revCol + 2)
                    .FormulaR1C1 = "=SUM(R" & (headerRow + 1) & "C:R[-1]C)"
                    ' .Font.Color = RGB(255, 0, 0)  ' 제거됨
                    ' .Font.Bold = True  ' 제거됨
                End With
            End If

            Dim formatEndRow As Long
            If totalCell Is Nothing Then
                formatEndRow = lLastRow
            Else
                formatEndRow = totalCell.Row
            End If

            ' ws.Range(ws.Cells(headerRow + 1, revCol), ws.Cells(formatEndRow, revCol + 2)).NumberFormat = "#,##0.00"  ' 제거됨

        End If
NextWs:
    Next ws
End Sub
