"""
DSV PDF Parser Module
=====================

BOE, DO, DN, Carrier Invoice 등 DSV 문서 전용 PDF 파서

Author: HVDC Logistics Team
Version: 1.0.0
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from .pdf_utils import extract_text_pages, extract_pattern, extract_all_patterns


# 날짜 파싱 패턴
DATE_PATTERNS = [
    r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b",  # 15-09-2025
    r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",  # 9/21/2025
    r"\b(\d{1,2})-([A-Za-z]{3})-(\d{4})\b",  # 22-Sep-2025
    r"\b(\d{4})-(\d{2})-(\d{2})\b",  # 2025-09-15
]

MONTH_ABBR = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _parse_any_date(s: str) -> str:
    """
    다양한 날짜 포맷을 ISO 형식(YYYY-MM-DD)으로 변환

    Args:
        s: 날짜 문자열

    Returns:
        str: ISO 형식 날짜 또는 빈 문자열
    """
    if not s:
        return ""

    for pat in DATE_PATTERNS:
        m = re.search(pat, s)
        if not m:
            continue

        g = m.groups()

        # 22-Sep-2025 형식
        if len(g) == 3 and g[1].isalpha():
            d, mon_str, y = int(g[0]), g[1][:3].title(), int(g[2])
            mon = MONTH_ABBR.get(mon_str, 0)
            if mon:
                return f"{y:04d}-{mon:02d}-{d:02d}"

        # 2025-09-15 형식 (이미 ISO)
        elif len(g) == 3 and len(g[0]) == 4:
            y, mo, d = int(g[0]), int(g[1]), int(g[2])
            return f"{y:04d}-{mo:02d}-{d:02d}"

        # 15-09-2025 형식 (dd-mm-yyyy)
        elif "-" in m.group(0) and len(g) == 3:
            d, mo, y = int(g[0]), int(g[1]), int(g[2])
            return f"{y:04d}-{mo:02d}-{d:02d}"

        # 9/21/2025 형식 (mm/dd/yyyy 미국식)
        elif "/" in m.group(0) and len(g) == 3:
            mo, d, y = int(g[0]), int(g[1]), int(g[2])
            return f"{y:04d}-{mo:02d}-{d:02d}"

    return ""


def parse_boe(pdf_path: str) -> Dict[str, Any]:
    """
    BOE (Bill of Entry) PDF 파싱

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        Dict: 파싱된 BOE 데이터
    """
    pages = extract_text_pages(pdf_path)
    blob = "\n".join(pages)
    out: Dict[str, Any] = {}

    # DEC NO - 통관신고번호
    dec_no = extract_pattern(blob, r"\bDEC\s*NO\b.*?(\d{11,})")
    if not dec_no:
        dec_no = extract_pattern(blob, r"\bDEC\s*NO\s*[: ]\s*(\d{11,})")
    if dec_no:
        out["dec_no"] = dec_no

    # DEC DATE - 통관신고일자
    dec_date_match = extract_pattern(blob, r"\bDEC\s*DATE\b.*?([^\n]+)")
    if dec_date_match:
        parsed_date = _parse_any_date(dec_date_match)
        if parsed_date:
            out["dec_date"] = parsed_date

    # MBL/B/L Number
    mbl_no = extract_pattern(blob, r"\b(MBL|B/L)\s*No\.?\s*[: ]\s*([A-Z0-9/]+)")
    if mbl_no:
        out["mbl_no"] = mbl_no

    # Vessel Name
    vessel = extract_pattern(blob, r"\bVessel\b.*?([A-Z0-9 \-]+)")
    if vessel:
        out["vessel"] = vessel.strip()

    # Voyage Number
    voyage = extract_pattern(blob, r"\bVoy(?:age|\.?)\s*No\b.*?([A-Z0-9\-]+)")
    if voyage:
        out["voyage_no"] = voyage.strip()

    # HS Code (첫 번째 항목)
    hs_code = extract_pattern(blob, r"\bH\.?S\.?\s*CODE\b.*?(\d{6,10})")
    if hs_code:
        out["hs_code"] = hs_code

    # Container Numbers (표준 형식: 4글자 + 7숫자)
    containers = extract_all_patterns(blob, r"\b([A-Z]{4}\d{7})\b")
    if containers:
        out["containers"] = sorted(set(containers))

    # Weights
    gross_weight = extract_pattern(blob, r"\bGROSS\s*WEIGHT\b.*?([\d\.]+)\s*Kgs?")
    if gross_weight:
        try:
            out["gross_weight_kg"] = float(gross_weight)
        except ValueError:
            pass

    net_weight = extract_pattern(blob, r"\bNET\s*WEIGHT\b.*?([\d\.]+)\s*Kgs?")
    if net_weight:
        try:
            out["net_weight_kg"] = float(net_weight)
        except ValueError:
            pass

    # Duty and VAT
    duty = extract_pattern(blob, r"\bDUTY\b.*?([\d\.]+)")
    if duty:
        try:
            out["duty_aed"] = float(duty)
        except ValueError:
            pass

    vat = extract_pattern(blob, r"\bVAT\b.*?([\d\.]+)")
    if vat:
        try:
            out["vat_aed"] = float(vat)
        except ValueError:
            pass

    return out


def parse_do(pdf_path: str) -> Dict[str, Any]:
    """
    DO (Delivery Order) PDF 파싱

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        Dict: 파싱된 DO 데이터
    """
    pages = extract_text_pages(pdf_path)
    blob = "\n".join(pages)
    out: Dict[str, Any] = {}

    # DO Number
    do_number = extract_pattern(blob, r"\bDO\s*Number\b.*?([A-Z0-9/\-]+)")
    if do_number:
        out["do_number"] = do_number.strip()

    # DO Date
    do_date_match = extract_pattern(blob, r"\bDO\s*Date\b.*?([^\n]+)")
    if do_date_match:
        parsed_date = _parse_any_date(do_date_match)
        if parsed_date:
            out["do_date"] = parsed_date

    # Delivery Valid Until
    validity_match = extract_pattern(blob, r"\bDelivery\s*Valid\s*Until\b.*?([^\n]+)")
    if validity_match:
        parsed_date = _parse_any_date(validity_match)
        if parsed_date:
            out["delivery_valid_until"] = parsed_date

    # MBL Number
    mbl_no = extract_pattern(blob, r"\bMBL\s*No\b.*?([A-Z0-9/]+)")
    if mbl_no:
        out["mbl_no"] = mbl_no

    # Vessel
    vessel = extract_pattern(blob, r"\bEx\.?M\.?V\.?\s*[: ]\s*([A-Z0-9 \-]+)")
    if vessel:
        out["vessel"] = vessel.strip()

    # Voyage Number
    voyage = extract_pattern(blob, r"\bVoy\.?No\b.*?([A-Z0-9\-]+)")
    if voyage:
        out["voyage_no"] = voyage.strip()

    # Container/Seal/Weight/Volume/Quantity 복합 정보
    container_matches = re.findall(
        r"Container:\s*([A-Z]{4}\d{7}).*?Seal:\s*([A-Z0-9]+).*?Weight:\s*([\d\.]+)\s*Vol:\s*([\d\.]+).*?PK\s*(\d+)",
        blob,
        re.DOTALL | re.IGNORECASE,
    )

    containers: List[Dict[str, Any]] = []
    for container_no, seal_no, weight, volume, quantity in container_matches:
        containers.append({"container_no": container_no, "seal_no": seal_no})
        # 첫 번째 컨테이너 정보를 전체 정보로 사용
        if not out.get("weight_kg"):
            try:
                out["weight_kg"] = float(weight)
                out["volume_cbm"] = float(volume)
                out["quantity"] = int(quantity)
            except ValueError:
                pass

    if containers:
        out["containers"] = containers

    return out


def parse_dn(pdf_path: str) -> Dict[str, Any]:
    """
    DN (Delivery Note) PDF 파싱

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        Dict: 파싱된 DN 데이터
    """
    pages = extract_text_pages(pdf_path)
    blob = "\n".join(pages)
    out: Dict[str, Any] = {}

    # DO Number
    do_number = extract_pattern(blob, r"\bDO\s*#\s*:\s*([A-Z0-9/\-]+)")
    if do_number:
        out["do_number"] = do_number.strip()

    # DO Validity
    validity_match = extract_pattern(blob, r"\bDO\s*Validity\s*:\s*([^\n]+)")
    if validity_match:
        parsed_date = _parse_any_date(validity_match)
        if parsed_date:
            out["delivery_valid_until"] = parsed_date

    # Container Number
    container_no = extract_pattern(blob, r"\bContainer\s*#\s*:\s*([A-Z]{4}\d{7})")
    if container_no:
        out["container_no"] = container_no

    # Waybill Number
    waybill = extract_pattern(blob, r"\bWaybill\s*(?:No|Number)\s*[: ]\s*([A-Z0-9\-]+)")
    if waybill:
        out["waybill_no"] = waybill

    # Loading Date
    loading_date_match = extract_pattern(blob, r"\bLoading\s*Date\s*[: ]\s*([^\n]+)")
    if loading_date_match:
        parsed_date = _parse_any_date(loading_date_match)
        if parsed_date:
            out["loading_date"] = parsed_date

    # Driver Name
    driver = extract_pattern(blob, r"\bDriver\s*(?:Name)?\s*[: ]\s*([A-Za-z\s]+)")
    if driver:
        out["driver_name"] = driver.strip()

    return out


def parse_carrier_invoice(pdf_path: str) -> Dict[str, Any]:
    """
    Carrier Invoice PDF 파싱

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        Dict: 파싱된 Carrier Invoice 데이터
    """
    pages = extract_text_pages(pdf_path)
    blob = "\n".join(pages)
    out: Dict[str, Any] = {}

    # Invoice Number
    invoice_no = extract_pattern(blob, r"\bInvoice\s*(?:no|number)\b[: ]\s*(\S+)")
    if invoice_no:
        out["invoice_no"] = invoice_no

    # Vessel
    vessel = extract_pattern(blob, r"\bVessel\b[: ]\s*([A-Z0-9 \-]+)")
    if vessel:
        out["vessel"] = vessel.strip()

    # B/L Number
    bl_number = extract_pattern(blob, r"\bB/L\s*(?:No|Number)\b[: ]\s*([A-Z0-9/]+)")
    if bl_number:
        out["bl_number"] = bl_number

    # Total Amount
    total = extract_pattern(blob, r"\bTotal\s*(?:Incl\.?\s*Tax|Amount)\b.*?([\d,\.]+)")
    if total:
        try:
            # 쉼표 제거 후 float 변환
            out["total_incl_tax"] = float(total.replace(",", ""))
        except ValueError:
            pass

    # Currency
    currency = extract_pattern(blob, r"\b(USD|AED|EUR|GBP)\b")
    if currency:
        out["currency"] = currency

    return out


def parse_pdf_by_type(pdf_path: str, doc_type: str) -> Dict[str, Any]:
    """
    문서 타입에 따른 PDF 파싱

    Args:
        pdf_path: PDF 파일 경로
        doc_type: 문서 타입 (BOE, DO, DN, CarrierInvoice)

    Returns:
        Dict: 파싱된 데이터
    """
    doc_type_upper = doc_type.upper()

    if doc_type_upper == "BOE":
        return parse_boe(pdf_path)
    elif doc_type_upper == "DO":
        return parse_do(pdf_path)
    elif doc_type_upper == "DN":
        return parse_dn(pdf_path)
    elif doc_type_upper == "CARRIERINVOICE":
        return parse_carrier_invoice(pdf_path)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
