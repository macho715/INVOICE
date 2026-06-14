from core.name_resolver import (
    resolve_header,
    resolve_sheet,
    resolve_vendor,
)


def test_report_sheets_and_capacitor():
    assert resolve_sheet("HE-0214,0252").canonical == "HE-0214,0252 (CAPACITOR)"
    assert resolve_sheet("현장_월별_입고재고").canonical == "현장_월별_입고재고"


def test_warehouse_and_site_headers():
    assert resolve_header("DHL WH").canonical == "DHL WAREHOUSE"
    assert resolve_header("DSV Al Markaz").canonical == "DSV AL MARKAZ"
    assert resolve_header("AGI Site").canonical == "AGI"


def test_time_headers():
    assert resolve_header("ETD / ATD").canonical == "ETD/ATD"
    assert resolve_header("ETA-ATA").canonical == "ETA/ATA"


def test_vendor_ril_path():
    assert resolve_vendor("RIL(SIMENSE)").canonical == "SIEMENS"
    assert resolve_vendor("HE-LOCAL").canonical == "HITACHI"
