Attribute VB_Name = "modConfig"
Option Explicit

' ==============================================================================
' HVDC Pipeline Configuration (VBA Port)
' ==============================================================================

' Column Headers (Semantic Keys)
Public Const COL_CASE_NO As String = "Case No"
Public Const COL_ITEM_NO As String = "Item No"
Public Const COL_ETD_ATD As String = "ETD/ATD"
Public Const COL_ETA_ATA As String = "ETA/ATA"

' Warehouse Columns
Public Const COL_DHL_WH As String = "DHL WH"
Public Const COL_DSV_INDOOR As String = "DSV Indoor"
Public Const COL_DSV_AL_MARKAZ As String = "DSV Al Markaz"
Public Const COL_AAA_STORAGE As String = "AAA Storage"
Public Const COL_DSV_OUTDOOR As String = "DSV Outdoor"
Public Const COL_DSV_MZP As String = "DSV MZP"
Public Const COL_MOSB As String = "MOSB"
Public Const COL_HAULER_INDOOR As String = "Hauler Indoor"
Public Const COL_JDN_MZD As String = "JDN MZD"

' Site Columns
Public Const COL_MIR As String = "MIR"
Public Const COL_SHU As String = "SHU"
Public Const COL_AGI As String = "AGI"
Public Const COL_DAS As String = "DAS"

' Derived Columns
Public Const COL_STATUS_WAREHOUSE As String = "Status_WAREHOUSE"
Public Const COL_STATUS_SITE As String = "Status_SITE"
Public Const COL_STATUS_CURRENT As String = "Status_Current"
Public Const COL_STATUS_LOCATION As String = "Status_Location"
Public Const COL_STATUS_LOCATION_DATE As String = "Status_Location_Date"
Public Const COL_STATUS_STORAGE As String = "Status_Storage"
Public Const COL_WH_HANDLING As String = "wh handling"
Public Const COL_SITE_HANDLING As String = "site handling"
Public Const COL_TOTAL_HANDLING As String = "total handling"
Public Const COL_MINUS As String = "minus"
Public Const COL_FINAL_HANDLING As String = "final handling"
Public Const COL_SQM As String = "SQM"
Public Const COL_STACK_STATUS As String = "Stack_Status"

' Colors
Public Const COLOR_BLUE As Long = 15773696 ' RGB(0, 176, 240) - Light Blue
Public Const COLOR_YELLOW As Long = 65535 ' RGB(255, 255, 0)
Public Const COLOR_PURPLE As Long = 12566463 ' RGB(255, 128, 192) - Light Purple/Magenta

' Header Aliases (Simulating Python's Semantic Matching)
Public Function GetHeaderAliases(semanticKey As String) As Variant
    Select Case semanticKey
        Case COL_CASE_NO
            GetHeaderAliases = Array("Case No", "Case No.", "CASE NO", "case number", "Case Number", "Case_No", "CaseNo", "Package No")
        Case COL_ETD_ATD
            GetHeaderAliases = Array("ETD/ATD", "ETD", "ATD", "ETD_ATD", "Estimated Departure", "Actual Departure")
        Case COL_ETA_ATA
            GetHeaderAliases = Array("ETA/ATA", "ETA", "ATA", "ETA_ATA", "Estimated Arrival", "Actual Arrival")
        Case COL_DHL_WH
            GetHeaderAliases = Array("DHL WH", "DHL", "DHL Warehouse", "DHL_WH", "DHL_Warehouse")
        Case COL_DSV_INDOOR
            GetHeaderAliases = Array("DSV Indoor", "DSV_Indoor", "DSV In", "DSV실내")
        Case COL_DSV_AL_MARKAZ
            GetHeaderAliases = Array("DSV Al Markaz", "DSV_Al_Markaz", "DSV AlMarkaz", "DSV Al-Markaz")
        Case COL_DSV_OUTDOOR
            GetHeaderAliases = Array("DSV Outdoor", "DSV_Outdoor", "DSV Out", "DSV실외")
        Case COL_DSV_MZP
            GetHeaderAliases = Array("DSV MZP", "DSV_MZP", "MZP", "DSV MZD")
        Case COL_JDN_MZD
            GetHeaderAliases = Array("JDN MZD", "JDN_MZD", "JDN", "MZD")
        Case COL_HAULER_INDOOR
            GetHeaderAliases = Array("Hauler Indoor", "Hauler_Indoor", "Hauler In", "HAULER", "Hauler")
        Case COL_AAA_STORAGE
            GetHeaderAliases = Array("AAA Storage", "AAA  Storage", "AAA_Storage", "AAA")
        Case COL_MOSB
            GetHeaderAliases = Array("MOSB", "MOS B", "MOS-B")
        Case COL_MIR
            GetHeaderAliases = Array("MIR", "MIR Site", "MIR_Site")
        Case COL_SHU
            GetHeaderAliases = Array("SHU", "SHU Site", "SHU_Site")
        Case COL_AGI
            GetHeaderAliases = Array("AGI", "AGI Site", "AGI_Site")
        Case COL_DAS
            GetHeaderAliases = Array("DAS", "DAS Site", "DAS_Site")
        Case Else
            GetHeaderAliases = Array(semanticKey)
    End Select
End Function

Public Function GetWarehouseColumns() As Variant
    GetWarehouseColumns = Array(COL_DHL_WH, COL_DSV_INDOOR, COL_DSV_AL_MARKAZ, COL_AAA_STORAGE, _
                                COL_DSV_OUTDOOR, COL_DSV_MZP, COL_MOSB, COL_HAULER_INDOOR, COL_JDN_MZD)
End Function

Public Function GetSiteColumns() As Variant
    GetSiteColumns = Array(COL_MIR, COL_SHU, COL_AGI, COL_DAS)
End Function
