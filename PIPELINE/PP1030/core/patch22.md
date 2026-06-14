1) core/name_resolver.py — 별칭 사전 확장 패치

라인 주석은 네가 제시한 범위(17–30, 33–37, 40–45)에 맞춰 위치 앵커를 넣었어. 기존 함수/유틸은 건들지 않음.

--- a/core/name_resolver.py
+++ b/core/name_resolver.py
@@ -17,30 +17,43 @@
-VENDOR_ALIASES: Dict[str, Iterable[str]] = {
-    "HITACHI": {
-        "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치", "hitachienergy",
-        "he local", "he-local"
-    },
-    "SIEMENS": {
-        "siemens", "sim", "simense", "seimens", "ril", "r.i.l", "ril(simense)", "지멘스"
-    },
-}
+VENDOR_ALIASES: Dict[str, Iterable[str]] = {
+    "HITACHI": {
+        "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치", "hitachienergy",
+        "he local", "he-local",
+        # namepatch.md: case variations
+        "Hitachi", "HITACHI ENERGY", "H.E", "HE-LOCAL"
+    },
+    "SIEMENS": {
+        "siemens", "sim", "simense", "seimens", "ril", "r.i.l", "ril(simense)", "지멘스",
+        # namepatch.md: case variations
+        "Siemens", "SIMENSE", "RIL(SIMENSE)", "RIL(SIEMENS)", "R.I.L"
+    },
+}
@@ -33,37 +46,72 @@
-SHEET_ALIASES: Dict[str, Iterable[str]] = {
-    "CASE LIST": {"case list", "caselist", "case_list"},
-    "CASE LIST, RIL(SIEMENS)": {
-        "case list, ril(simense)", "case list ril", "ril", "ril(simense)"
-    },
-    "HE LOCAL": {"he local", "he-local", "hitachi local", "히타치 로컬"},
-}
+SHEET_ALIASES: Dict[str, Iterable[str]] = {
+    # CASE LIST (expand)
+    "CASE LIST": {
+        "case list", "caselist", "case_list",
+        "Case List", "CaseList", "CASE LIST"
+    },
+    # CASE LIST, RIL(SIEMENS) (expand)
+    "CASE LIST, RIL(SIEMENS)": {
+        "case list, ril(simense)", "case list ril", "ril", "ril(simense)",
+        "Case List, RIL", "Case List RIL", "CASE LIST, RIL", "Case List, RIL(SIEMENS)"
+    },
+    # HE LOCAL (expand)
+    "HE LOCAL": {
+        "he local", "he-local", "hitachi local", "히타치 로컬",
+        "HE Local", "HELocal", "HE-LOCAL"
+    },
+    # NEW: Capacitor
+    "HE-0214,0252 (CAPACITOR)": {
+        "he-0214,0252", "he-0214,0252 (capacitor)", "capacitor",
+        "HE-0214,0252", "Capacitor"
+    },
+    # NEW: Report sheets (6)
+    "통합_원본데이터_FIXED": {"통합_원본데이터_fixed"},
+    "HITACHI_원본데이터_FIXED": {"hitachi_원본데이터_fixed"},
+    "SIEMENS_원본데이터_FIXED": {"siemens_원본데이터_fixed"},
+    "창고_월별_입출고": {"창고_월별_입출고"},
+    "현장_월별_입고재고": {"현장_월별_입고재고"},
+    "FLOW_CODE_분석": {"flow_code_분석"},
+}
@@ -40,45 +88,126 @@
-HEADER_ALIASES: Dict[str, Iterable[str]] = {
-    "CASE NO": {"case no", "case_no", "caseno", "case#", "case number"},
-    "VENDOR": {"vendor", "maker", "supplier", "vend", "vendr"},
-    "QTY": {"qty", "quantity", "q'ty", "수량"},
-    "MATERIAL": {"material", "item desc", "description", "desc", "품명"},
-}
+HEADER_ALIASES: Dict[str, Iterable[str]] = {
+    # CASE NO (expand 18+)
+    "CASE NO": {
+        "case no", "case_no", "caseno", "case#", "case number",
+        "Case No", "Case No.", "CASE NO", "Case Number", "Case_No",
+        "CaseNo", "case-no", "CASE_NUMBER", "케이스번호", "케이스 번호",
+        "Case", "Package No", "Package No.", "PACKAGE NO", "PackageNo", "packageno", "Package_No"
+    },
+    # VENDOR (expand)
+    "VENDOR": {
+        "vendor", "maker", "supplier", "vend", "vendr",
+        "Vendor", "VENDOR", "Source_Vendor", "SourceVendor", "Source Vendor"
+    },
+    # QTY (expand)
+    "QTY": {
+        "qty", "quantity", "q'ty", "수량",
+        "QTY", "Qty", "Quantity", "Q'ty", "Qty.", "QUANTITY",
+        "Amount", "Count", "Pkg", "pkg", "Pkg_Quantity", "pkg_quantity"
+    },
+    # MATERIAL (expand)
+    "MATERIAL": {
+        "material", "item desc", "description", "desc", "품명",
+        "Material", "MATERIAL", "Item Desc", "Item Description", "Description",
+        "Desc", "DESC", "Detail", "Details", "Name", "Item Name", "설명", "상세"
+    },
+    # NEW: Time headers
+    "ETD/ATD": {
+        "etd/atd", "etd", "atd", "etd_atd", "etd-atd", "etd / atd",
+        "Estimated Departure", "Actual Departure", "Departure Date", "Departure", "출발일"
+    },
+    "ETA/ATA": {
+        "eta/ata", "eta", "ata", "eta_ata", "eta-ata", "eta / ata",
+        "Estimated Arrival", "Actual Arrival", "Arrival Date", "Arrival", "도착일"
+    },
+    # NEW: Warehouse headers
+    "DHL WAREHOUSE": {"dhl wh", "dhl warehouse", "DHL WH", "DHL Warehouse"},
+    "DSV INDOOR": {"dsv indoor", "DSV Indoor"},
+    "DSV AL MARKAZ": {"dsv al markaz", "DSV Al Markaz", "dsv almarkaz"},
+    "DSV OUTDOOR": {"dsv outdoor", "DSV Outdoor"},
+    "AAA STORAGE": {"aaa storage", "AAA Storage", "AAA_STORAGE"},
+    "HAULER INDOOR": {"hauler indoor", "Hauler Indoor", "HAULER_INDOOR"},
+    "MOSB": {"mosb", "MOSB"},
+    # NEW: Site headers
+    "MIR": {"mir", "MIR", "MIR Site"},
+    "SHU": {"shu", "SHU", "SHU Site"},
+    "DAS": {"das", "DAS", "DAS Site"},
+    "AGI": {"agi", "AGI", "AGI Site"},
+    # NEW: KPI headers
+    "SQM": {"sqm", "SQM", "Square Meter", "Square Meterage"},
+    "STACK_STATUS": {"stack_status", "Stack_Status", "STACK_STATUS"},
+}

2) tests/test_name_resolver_extended.py — 새 테스트 파일

요청대로 core.name_resolver 경로에서 import.

# -*- coding: utf-8 -*-
from core.name_resolver import resolve_sheet, resolve_header, resolve_vendor

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

3) pytest.ini — 커버리지 HTML + 임계치 85%
[pytest]
addopts = -q --cov=. --cov-report=term-missing --cov-report=html:coverage_html --cov-fail-under=85
testpaths = tests
python_files = test_*.py

4) 실행 순서
ruff check --fix .
black .
pytest -q
# (HTML 리포트: coverage_html/index.html)
