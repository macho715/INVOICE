VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsDataSync"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = False
Attribute VB_Exposed = False
Option Explicit

' ==============================================================================
' Stage 1: Data Synchronization
' ==============================================================================

Private pMasterWs As Worksheet
Private pWarehouseWs As Worksheet
Private pOutputWs As Worksheet
Private pHeaderRow As Long
Private pOnlyUpdate As Boolean

Public Property Let OnlyUpdate(val As Boolean)
    pOnlyUpdate = val
End Property

Public Sub Initialize(masterWs As Worksheet, warehouseWs As Worksheet, outputWs As Worksheet)
    Set pMasterWs = masterWs
    Set pWarehouseWs = warehouseWs
    Set pOutputWs = outputWs
    
    ' Detect Header Rows
    Dim mHeader As Long, wHeader As Long
    mHeader = modUtils.DetectHeaderRow(pMasterWs)
    wHeader = modUtils.DetectHeaderRow(pWarehouseWs)
    
    ' Use the larger one (or assume they match, but safer to detect individually)
    ' For simplicity in this port, we'll use the Master's header row for logic, 
    ' but we should really respect each file's structure.
    pHeaderRow = mHeader
    
    modUtils.LogMessage "Detected Master Header Row: " & mHeader
    modUtils.LogMessage "Detected Warehouse Header Row: " & wHeader
    
    If mHeader <> wHeader Then
        modUtils.LogMessage "WARNING: Header rows differ. Using Master: " & mHeader
    End If
End Sub

Public Sub Synchronize()
    Dim masterLastRow As Long, whLastRow As Long
    Dim masterCaseCol As Long, whCaseCol As Long
    Dim masterData As Variant, whData As Variant
    Dim masterDict As Object
    Dim i As Long, j As Long
    Dim caseNo As String
    Dim whCols As Collection
    Dim colMap As Object ' Map semantic key to column index
    Dim wHeaderRow As Long
    
    wHeaderRow = modUtils.DetectHeaderRow(pWarehouseWs)
    
    modUtils.LogMessage "Starting Stage 1 Synchronization..."
    
    ' 1. Identify Columns
    masterCaseCol = modUtils.FindColumnIndex(pMasterWs, pHeaderRow, modConfig.COL_CASE_NO)
    whCaseCol = modUtils.FindColumnIndex(pWarehouseWs, wHeaderRow, modConfig.COL_CASE_NO)
    
    modUtils.LogMessage "Master Case Column Index: " & masterCaseCol
    modUtils.LogMessage "Warehouse Case Column Index: " & whCaseCol
    
    If masterCaseCol = 0 Or whCaseCol = 0 Then
        MsgBox "Error: Case No column not found in one of the files.", vbCritical
        Exit Sub
    End If
    
    ' 2. Load Master Data into Dictionary
    masterLastRow = pMasterWs.Cells(pMasterWs.Rows.Count, masterCaseCol).End(xlUp).Row
    modUtils.LogMessage "Master File Rows: " & masterLastRow
    
    Set masterDict = CreateObject("Scripting.Dictionary")
    
    ' Store Row Index for each Case No
    For i = pHeaderRow + 1 To masterLastRow
        caseNo = Trim(CStr(pMasterWs.Cells(i, masterCaseCol).Value))
        If Len(caseNo) > 0 And Not masterDict.Exists(caseNo) Then
            masterDict.Add caseNo, i
        End If
    Next i
    
    modUtils.LogMessage "Loaded " & masterDict.Count & " unique cases from Master."
    
    ' 3. Map Warehouse Columns to Master Columns
    Set colMap = CreateObject("Scripting.Dictionary")
    Dim semanticKeys As Variant
    semanticKeys = Array(modConfig.COL_ETD_ATD, modConfig.COL_ETA_ATA, _
                         modConfig.COL_DHL_WH, modConfig.COL_DSV_INDOOR, modConfig.COL_DSV_AL_MARKAZ, _
                         modConfig.COL_AAA_STORAGE, modConfig.COL_DSV_OUTDOOR, modConfig.COL_DSV_MZP, _
                         modConfig.COL_MOSB, modConfig.COL_HAULER_INDOOR, modConfig.COL_JDN_MZD, _
                         modConfig.COL_MIR, modConfig.COL_SHU, modConfig.COL_AGI, modConfig.COL_DAS)
                         
    For i = LBound(semanticKeys) To UBound(semanticKeys)
        Dim mCol As Long, wCol As Long
        mCol = modUtils.FindColumnIndex(pMasterWs, pHeaderRow, CStr(semanticKeys(i)))
        wCol = modUtils.FindColumnIndex(pWarehouseWs, wHeaderRow, CStr(semanticKeys(i)))
        
        If mCol > 0 And wCol > 0 Then
            colMap.Add CStr(mCol), wCol ' Key: Master Col Index, Value: Warehouse Col Index
            modUtils.LogMessage "Mapped " & semanticKeys(i) & ": Master Col " & mCol & " <- WH Col " & wCol
        Else
            modUtils.LogMessage "WARNING: Could not map " & semanticKeys(i) & " (Master=" & mCol & ", WH=" & wCol & ")"
        End If
    Next i
    
    ' 4. Process Warehouse Data
    whLastRow = pWarehouseWs.Cells(pWarehouseWs.Rows.Count, whCaseCol).End(xlUp).Row
    modUtils.LogMessage "Warehouse File Rows: " & whLastRow
    
    ' Copy Master to Output first (as a base)
    pMasterWs.Cells.Copy Destination:=pOutputWs.Cells(1, 1)
    
    Dim outLastRow As Long
    outLastRow = pOutputWs.Cells(pOutputWs.Rows.Count, masterCaseCol).End(xlUp).Row
    modUtils.LogMessage "Initial Output Rows (Copy of Master): " & outLastRow
    
    For i = wHeaderRow + 1 To whLastRow
        caseNo = Trim(CStr(pWarehouseWs.Cells(i, whCaseCol).Value))
        
        If masterDict.Exists(caseNo) Then
            ' Update Existing Record
            Dim rowIdx As Long
            rowIdx = masterDict(caseNo)
            
            Dim key As Variant
            For Each key In colMap.Keys
                Dim mColIdx As Long, wColIdx As Long
                mColIdx = CLng(key)
                wColIdx = colMap(key)
                
                Dim mVal As Variant, wVal As Variant
                mVal = pOutputWs.Cells(rowIdx, mColIdx).Value
                wVal = pWarehouseWs.Cells(i, wColIdx).Value
                
                ' Normalize empty values for comparison
                Dim mValStr As String, wValStr As String
                mValStr = ""
                wValStr = ""
                
                If Not IsEmpty(mVal) And Not IsNull(mVal) Then
                    If IsDate(mVal) Then
                        mValStr = Format(mVal, "yyyy-mm-dd")
                    Else
                        mValStr = Trim(CStr(mVal))
                    End If
                End If
                
                If Not IsEmpty(wVal) And Not IsNull(wVal) Then
                    If IsDate(wVal) Then
                        wValStr = Format(wVal, "yyyy-mm-dd")
                    Else
                        wValStr = Trim(CStr(wVal))
                    End If
                End If
                
                ' Update if different and warehouse has a value
                If mValStr <> wValStr And Len(wValStr) > 0 Then
                    pOutputWs.Cells(rowIdx, mColIdx).Value = wVal
                    
                    ' COMPLETELY clear all formatting to ensure our color is visible
                    On Error Resume Next
                    pOutputWs.Cells(rowIdx, mColIdx).FormatConditions.Delete
                    On Error GoTo 0
                    
                    With pOutputWs.Cells(rowIdx, mColIdx).Interior
                        .Pattern = xlSolid
                        .PatternColorIndex = xlAutomatic
                        .TintAndShade = 0
                        ' Use PURPLE for SimpleDateUpdate, BLUE for regular sync
                        If pOnlyUpdate Then
                            .Color = modConfig.COLOR_PURPLE
                            modUtils.LogMessage "PURPLE: Updated Row " & rowIdx & ", Col " & mColIdx & " from [" & mValStr & "] to [" & wValStr & "]"
                        Else
                            .Color = modConfig.COLOR_BLUE
                            modUtils.LogMessage "BLUE: Updated Row " & rowIdx & ", Col " & mColIdx & " from [" & mValStr & "] to [" & wValStr & "]"
                        End If
                    End With
                End If
            Next key
        Else
            ' Append New Record (Only if pOnlyUpdate is False)
            If Not pOnlyUpdate Then
                outLastRow = outLastRow + 1
                
                ' Copy ENTIRE row from Warehouse to Output
                Dim lastCol As Long
                lastCol = pWarehouseWs.Cells(wHeaderRow, pWarehouseWs.Columns.Count).End(xlToLeft).Column
                
                ' Copy all cell values from warehouse row to output row
                Dim c As Long
                For c = 1 To lastCol
                    pOutputWs.Cells(outLastRow, c).Value = pWarehouseWs.Cells(i, c).Value
                Next c
                
                ' Highlight new row (entire row up to last column)
                pOutputWs.Range(pOutputWs.Cells(outLastRow, 1), pOutputWs.Cells(outLastRow, lastCol)).Interior.Color = modConfig.COLOR_YELLOW
                
                modUtils.LogMessage "YELLOW: Added new row " & outLastRow & " for Case No [" & caseNo & "]"
            End If
        End If
    Next i
    
    modUtils.LogMessage "Stage 1 Synchronization Completed."
End Sub
