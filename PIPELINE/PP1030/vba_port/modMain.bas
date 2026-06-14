Attribute VB_Name = "modMain"
Option Explicit

' ==============================================================================
' HVDC Pipeline - Main Entry Point
' ==============================================================================

Public Sub RunPipeline()
    Dim masterPath As String, whPath As String
    Dim wbMaster As Workbook, wbWh As Workbook, wbOut As Workbook
    Dim wsMaster As Worksheet, wsWh As Worksheet, wsOut As Worksheet
    Dim dataSync As clsDataSync
    Dim derivedCols As clsDerivedCols
    Dim startTime As Double
    
    startTime = Timer
    
    ' 1. Select Files
    MsgBox "Select MASTER File (Previous Synced File)", vbInformation
    masterPath = modUtils.SelectFile("Select Master File")
    If masterPath = "" Then Exit Sub
    
    MsgBox "Select WAREHOUSE File (New Data)", vbInformation
    whPath = modUtils.SelectFile("Select Warehouse File")
    If whPath = "" Then Exit Sub
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    ' 2. Open Workbooks
    modUtils.LogMessage "Opening files..."
    Set wbMaster = Workbooks.Open(masterPath, ReadOnly:=True)
    Set wbWh = Workbooks.Open(whPath, ReadOnly:=True)
    
    ' Assume data is in the first sheet for now
    Set wsMaster = wbMaster.Sheets(1)
    Set wsWh = wbWh.Sheets(1)
    
    ' 3. Create Output Workbook
    Set wbOut = Workbooks.Add
    Set wsOut = wbOut.Sheets(1)
    wsOut.Name = "Synced_Data"
    
    ' 4. Run Stage 1: Data Sync
    modUtils.LogMessage "Running Stage 1..."
    Set dataSync = New clsDataSync
    dataSync.Initialize wsMaster, wsWh, wsOut
    dataSync.Synchronize
    
    ' 5. Run Stage 2: Derived Columns
    modUtils.LogMessage "Running Stage 2..."
    Set derivedCols = New clsDerivedCols
    derivedCols.Initialize wsOut
    derivedCols.ProcessDerivedColumns
    
    ' 6. Cleanup and Save
    wbMaster.Close SaveChanges:=False
    wbWh.Close SaveChanges:=False
    
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    modUtils.LogMessage "Pipeline Completed in " & Format(Timer - startTime, "0.00") & " seconds."
    MsgBox "Pipeline Completed Successfully!", vbInformation
    
End Sub

Public Sub RunSimpleDateUpdate()
    ' Simplified version for updating dates only (no new rows)
    Dim masterPath As String, whPath As String
    Dim wbMaster As Workbook, wbWh As Workbook, wbOut As Workbook
    Dim wsMaster As Worksheet, wsWh As Worksheet, wsOut As Worksheet
    Dim dataSync As clsDataSync
    Dim derivedCols As clsDerivedCols
    Dim startTime As Double
    
    startTime = Timer
    
    MsgBox "Select MASTER File", vbInformation
    masterPath = modUtils.SelectFile("Select Master File")
    If masterPath = "" Then Exit Sub
    
    MsgBox "Select MINI Update File (Case No + Dates)", vbInformation
    whPath = modUtils.SelectFile("Select Mini Update File")
    If whPath = "" Then Exit Sub
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    Set wbMaster = Workbooks.Open(masterPath, ReadOnly:=True)
    Set wbWh = Workbooks.Open(whPath, ReadOnly:=True)
    Set wsMaster = wbMaster.Sheets(1)
    Set wsWh = wbWh.Sheets(1)
    
    Set wbOut = Workbooks.Add
    Set wsOut = wbOut.Sheets(1)
    wsOut.Name = "Synced_Data"
    
    modUtils.LogMessage "Running Simple Date Update..."
    Set dataSync = New clsDataSync
    dataSync.Initialize wsMaster, wsWh, wsOut
    dataSync.OnlyUpdate = True ' <--- Key Change: Do not add new rows
    dataSync.Synchronize
    
    ' Still run derived columns to update Status based on new dates
    modUtils.LogMessage "Updating Derived Columns..."
    Set derivedCols = New clsDerivedCols
    derivedCols.Initialize wsOut
    derivedCols.ProcessDerivedColumns
    
    wbMaster.Close SaveChanges:=False
    wbWh.Close SaveChanges:=False
    
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    modUtils.LogMessage "Simple Update Completed in " & Format(Timer - startTime, "0.00") & " seconds."
    MsgBox "Simple Update Completed Successfully!", vbInformation
End Sub

Public Sub TestHeaderMatching()
    ' Simple test to verify alias lookup
    Dim aliases As Variant
    aliases = modConfig.GetHeaderAliases("DHL WH")
    Debug.Print "Aliases for DHL WH: " & Join(aliases, ", ")
    
    aliases = modConfig.GetHeaderAliases("Case No")
    Debug.Print "Aliases for Case No: " & Join(aliases, ", ")
End Sub
