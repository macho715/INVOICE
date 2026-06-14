VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsDerivedCols"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

' ==============================================================================
' Stage 2: Derived Columns Generation
' ==============================================================================

Private pWs As Worksheet
Private pHeaderRow As Long

Public Sub Initialize(ws As Worksheet)
    Set pWs = ws
    pHeaderRow = modUtils.DetectHeaderRow(pWs)
    modUtils.LogMessage "Stage 2 Detected Header Row: " & pHeaderRow
End Sub

Public Sub ProcessDerivedColumns()
    Dim lastRow As Long
    Dim i As Long
    Dim colMap As Object
    Dim whCols As Variant, siteCols As Variant
    
    modUtils.LogMessage "Starting Stage 2 Derived Columns..."
    
    lastRow = pWs.Cells(pWs.Rows.Count, 1).End(xlUp).Row
    modUtils.LogMessage "Stage 2 Input Rows (Column 1): " & lastRow
    
    If lastRow <= pHeaderRow Then
        modUtils.LogMessage "WARNING: No data found in Stage 2 input."
        Exit Sub
    End If
    
    ' 1. Map Columns
    Set colMap = CreateObject("Scripting.Dictionary")
    MapColumns colMap
    modUtils.LogMessage "Mapped " & colMap.Count & " columns for Stage 2."
    
    ' 2. Add Derived Columns if missing
    AddMissingColumns colMap
    
    ' 3. Process Rows
    whCols = modConfig.GetWarehouseColumns()
    siteCols = modConfig.GetSiteColumns()
    
    For i = pHeaderRow + 1 To lastRow
        ProcessRow i, colMap, whCols, siteCols
    Next i
    
    modUtils.LogMessage "Stage 2 Completed."
End Sub

Private Sub MapColumns(colMap As Object)
    ' Map existing columns
    Dim cols As Variant
    Dim c As Variant
    Dim idx As Long
    
    ' Warehouse & Site Columns
    cols = modConfig.GetWarehouseColumns()
    For Each c In cols
        idx = modUtils.FindColumnIndex(pWs, pHeaderRow, CStr(c))
        If idx > 0 Then colMap.Add CStr(c), idx
    Next c
    
    cols = modConfig.GetSiteColumns()
    For Each c In cols
        idx = modUtils.FindColumnIndex(pWs, pHeaderRow, CStr(c))
        If idx > 0 Then colMap.Add CStr(c), idx
    Next c
    
    ' Other required columns
    idx = modUtils.FindColumnIndex(pWs, pHeaderRow, "L(CM)")
    If idx > 0 Then colMap.Add "L", idx
    idx = modUtils.FindColumnIndex(pWs, pHeaderRow, "W(CM)")
    If idx > 0 Then colMap.Add "W", idx
    idx = modUtils.FindColumnIndex(pWs, pHeaderRow, "Pkg")
    If idx > 0 Then colMap.Add "Pkg", idx
End Sub

Private Sub AddMissingColumns(colMap As Object)
    Dim derivedCols As Variant
    Dim c As Variant
    Dim lastCol As Long
    Dim idx As Long
    
    derivedCols = Array(modConfig.COL_STATUS_WAREHOUSE, modConfig.COL_STATUS_SITE, _
                        modConfig.COL_STATUS_CURRENT, modConfig.COL_STATUS_LOCATION, _
                        modConfig.COL_STATUS_LOCATION_DATE, modConfig.COL_STATUS_STORAGE, _
                        modConfig.COL_WH_HANDLING, modConfig.COL_SITE_HANDLING, _
                        modConfig.COL_TOTAL_HANDLING, modConfig.COL_MINUS, _
                        modConfig.COL_FINAL_HANDLING, modConfig.COL_SQM, modConfig.COL_STACK_STATUS)
                        
    lastCol = pWs.Cells(pHeaderRow, pWs.Columns.Count).End(xlToLeft).Column
    
    For Each c In derivedCols
        idx = modUtils.FindColumnIndex(pWs, pHeaderRow, CStr(c))
        If idx = 0 Then
            lastCol = lastCol + 1
            pWs.Cells(pHeaderRow, lastCol).Value = c
            colMap.Add CStr(c), lastCol
        Else
            colMap.Add CStr(c), idx
        End If
    Next c
End Sub

Private Sub ProcessRow(rowIdx As Long, colMap As Object, whCols As Variant, siteCols As Variant)
    Dim hasWh As Boolean, hasSite As Boolean
    Dim latestDate As Date
    Dim latestLoc As String
    Dim whCount As Long, siteCount As Long
    Dim c As Variant
    Dim cellVal As Variant
    Dim colIdx As Long
    
    hasWh = False
    hasSite = False
    latestDate = 0
    latestLoc = "Pre Arrival"
    whCount = 0
    siteCount = 0
    
    ' Check Warehouse Columns
    For Each c In whCols
        If colMap.Exists(CStr(c)) Then
            colIdx = colMap(CStr(c))
            cellVal = pWs.Cells(rowIdx, colIdx).Value
            If modUtils.IsDate(cellVal) Then
                hasWh = True
                whCount = whCount + 1
                If CDate(cellVal) >= latestDate Then
                    latestDate = CDate(cellVal)
                    latestLoc = CStr(c)
                End If
            End If
        End If
    Next c
    
    ' Check Site Columns
    For Each c In siteCols
        If colMap.Exists(CStr(c)) Then
            colIdx = colMap(CStr(c))
            cellVal = pWs.Cells(rowIdx, colIdx).Value
            If modUtils.IsDate(cellVal) Then
                hasSite = True
                siteCount = siteCount + 1
                If CDate(cellVal) >= latestDate Then
                    latestDate = CDate(cellVal)
                    latestLoc = CStr(c)
                End If
            End If
        End If
    Next c
    
    ' Set Status Columns
    pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_WAREHOUSE)).Value = IIf(hasWh, 1, "")
    pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_SITE)).Value = IIf(hasSite, 1, "")
    
    If hasSite Then
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_CURRENT)).Value = "site"
    ElseIf hasWh Then
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_CURRENT)).Value = "warehouse"
    Else
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_CURRENT)).Value = "Pre Arrival"
    End If
    
    pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_LOCATION)).Value = latestLoc
    If latestDate > 0 Then
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_LOCATION_DATE)).Value = latestDate
    Else
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_LOCATION_DATE)).Value = ""
    End If
    
    ' Storage Status (Simplified)
    If InStr(1, LCase(latestLoc), "site") > 0 Or latestLoc = "MIR" Or latestLoc = "SHU" Then
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_STORAGE)).Value = "site"
    ElseIf latestLoc = "Pre Arrival" Then
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_STORAGE)).Value = "Pre Arrival"
    Else
        pWs.Cells(rowIdx, colMap(modConfig.COL_STATUS_STORAGE)).Value = "warehouse"
    End If
    
    ' Handling Counts
    pWs.Cells(rowIdx, colMap(modConfig.COL_WH_HANDLING)).Value = whCount
    pWs.Cells(rowIdx, colMap(modConfig.COL_SITE_HANDLING)).Value = siteCount
    pWs.Cells(rowIdx, colMap(modConfig.COL_TOTAL_HANDLING)).Value = whCount + siteCount
    pWs.Cells(rowIdx, colMap(modConfig.COL_MINUS)).Value = siteCount - whCount
    pWs.Cells(rowIdx, colMap(modConfig.COL_FINAL_HANDLING)).Value = (whCount + siteCount) + (siteCount - whCount)
    
    ' SQM Calculation
    Dim L As Double, W As Double, Pkg As Double, SQM As Double
    L = 0: W = 0: Pkg = 0: SQM = 0
    
    If colMap.Exists("L") Then L = Val(pWs.Cells(rowIdx, colMap("L")).Value)
    If colMap.Exists("W") Then W = Val(pWs.Cells(rowIdx, colMap("W")).Value)
    If colMap.Exists("Pkg") Then Pkg = Val(pWs.Cells(rowIdx, colMap("Pkg")).Value)
    If Pkg = 0 Then Pkg = 1
    
    If L > 0 And W > 0 Then
        SQM = (L * W) / 10000
    Else
        SQM = Pkg * 1.5 ' Fallback estimate
    End If
    
    pWs.Cells(rowIdx, colMap(modConfig.COL_SQM)).Value = Round(SQM, 2)
    
End Sub
