from core.name_resolver import (
    guess_vendor_from_filename,
    resolve_header,
    resolve_sheet,
    resolve_vendor,
)


def test_vendor_aliases_basic():
    assert resolve_vendor("HE").canonical == "HITACHI"
    assert resolve_vendor("RIL(SIMENSE)").canonical == "SIEMENS"
    assert resolve_vendor("Seimens").canonical == "SIEMENS"


def test_guess_vendor_from_filename():
    m = guess_vendor_from_filename("HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    assert m and m.canonical == "HITACHI"


def test_sheet_aliases():
    assert resolve_sheet("Case List, RIL(SIMENSE)").canonical == "CASE LIST, RIL(SIEMENS)"
    assert resolve_sheet("he-local").canonical == "HE LOCAL"


def test_header_aliases():
    assert resolve_header("Q'ty").canonical == "QTY"
    assert resolve_header("Case#").canonical == "CASE NO"
    assert resolve_header("item desc").canonical == "MATERIAL"
