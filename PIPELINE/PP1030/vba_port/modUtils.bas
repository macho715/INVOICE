Attribute VB_Name = "modUtils"
Option Explicit

' ==============================================================================
' Utility Functions
' ==============================================================================

Public Function SelectFile(title As String) As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)
    With fd
        .title = title
        .Filters.Clear
        .Filters.Add "Excel Files", "*.xlsx; *.xlsm; *.xls"
        .AllowMultiSelect = False
        If .Show = -1 Then
            SelectFile = .SelectedItems(1)
        Else
            SelectFile = ""
        End If
    End With
End Function

Public Function FindColumnIndex(ws As Worksheet, headerRow As Long, semanticKey As String) As Long
    Dim aliases As Variant
    Dim col As Long, lastCol As Long
    Dim cellVal As String
    Dim i As Long
    
    aliases = modConfig.GetHeaderAliases(semanticKey)
    lastCol = ws.Cells(headerRow, ws.Columns.Count).End(xlToLeft).Column
    
    For col = 1 To lastCol
        cellVal = Trim(ws.Cells(headerRow, col).Value)
        For i = LBound(aliases) To UBound(aliases)
            If LCase(Replace(cellVal, " ", "")) = LCase(Replace(aliases(i), " ", "")) Then
                FindColumnIndex = col
                Exit Function
            End If
        Next i
    Next col
    
    FindColumnIndex = 0
End Function

Public Function DetectHeaderRow(ws As Worksheet) As Long
    Dim r As Long, c As Long
    Dim val As String
    Dim matchCount As Integer
    Dim lastCol As Long
    
    ' Check first 10 rows
    For r = 1 To 10
        matchCount = 0
        lastCol = ws.Cells(r, ws.Columns.Count).End(xlToLeft).Column
        If lastCol > 1 Then
            For c = 1 To lastCol
                val = LCase(Replace(Trim(ws.Cells(r, c).Value), " ", ""))
                ' Check for key headers
                If InStr(val, "site") > 0 Or _
                   InStr(val, "eqno") > 0 Or _
                   InStr(val, "caseno") > 0 Or _
                   InStr(val, "packageno") > 0 Or _
                   InStr(val, "sctref.no") > 0 Or _
                   InStr(val, "description") > 0 Or _
                   InStr(val, "weight") > 0 Or _
                   InStr(val, "q'ty") > 0 Or _
                   InStr(val, "qty") > 0 Then
                    matchCount = matchCount + 1
                End If
            Next c
            
            ' If we found at least 3 key headers, assume this is the header row
            If matchCount >= 3 Then
                DetectHeaderRow = r
                Exit Function
            End If
        End If
    Next r
    
    ' Fallback to 1 if not found
    DetectHeaderRow = 1
End Function

Public Sub LogMessage(msg As String)
    Debug.Print Format(Now, "yyyy-mm-dd hh:mm:ss") & " - " & msg
    ' Ideally, write to a log sheet or file here
End Sub

Public Function IsDate(val As Variant) As Boolean
    IsDate = VBA.IsDate(val)
End Function
