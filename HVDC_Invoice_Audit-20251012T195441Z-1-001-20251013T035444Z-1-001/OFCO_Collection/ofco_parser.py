
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
import re
import json
import argparse
import csv

"""
OFCO Invoice Parser (v0.9)
- Adds robust table-row parser for multi-line descriptions (OFCO layout).
- Expands SUBJECT→Cost Center mapping (~18 rules; placeholders marked "가정: tune with v2.5 dict").
- Improves date parsing (supports unlabelled DD-MMM-YYYY) and Samsung Ref patterns.
- Parses EA/Rate/Amount from tails like: "5% 1.00 490.13 LS 490.13 24.51 514.64".
"""

# ---------- Config ----------
REL_TOL = 0.02
ABS_EPS = 0.01
CURRENCY = "AED"

# ---------- Mapping Rules (expandable) ----------
# 가정: 일부 규칙은 v2.5 딕셔너리 확정 시 조정 필요
SUBJECT_CC_MAP = [
    # Existing rules
    (re.compile(r"SAFEEN", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"PORT HANDLING CHARGE","COST CENTER B":"CHANNEL TRANSIT CHARGES","PRICE CENTER":"CHANNEL TRANSIT CHARGES"}),
    (re.compile(r"\bPHC\b", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"PORT HANDLING CHARGE","COST CENTER B":"PORT HANDLING CHARGES","PRICE CENTER":"PORT HANDLING CHARGE"}),
    (re.compile(r"ADP\s*INV.*Port\s*Dues", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"PORT HANDLING CHARGE","COST CENTER B":"PORT DUES & SERVICES CHARGES","PRICE CENTER":"PORT DUES"}),
    (re.compile(r"Cargo\s*Clearance", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"CONTRACT(AF FOR CC)","COST CENTER B":"AF FOR CC","PRICE CENTER":"AGENCY FEE FOR CARGO CLEARANCE"}),
    (re.compile(r"(FW\s*Supply|Arranging\s*FW\s*Supply)", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"CONTRACT","COST CENTER B":"AF FOR FW SA","PRICE CENTER":"SUPPLY WATER 5000IG"}),
    (re.compile(r"Berthing\s*Arrangement", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"CONTRACT(AF FOR BA)","COST CENTER B":"CONTRACT","PRICE CENTER":"AGENCY FEE FOR BERTHING ARRANGEMENT"}),
    (re.compile(r"5000\s*IG\s*FW|Supply\s*of\s*5000\s*IG\s*FW", re.I), {"COST MAIN":"AT COST","COST CENTER A":"AT COST","COST CENTER B":"AT COST(WATER SUPPLY)","PRICE CENTER":"SUPPLY WATER 5000IG"}),
    # Expanded (가정)
    (re.compile(r"Handling\s*Fee|Handling\s*Charge", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"CONTRACT","COST CENTER B":"HANDLING FEE 10%","PRICE CENTER":"HANDLING FEE"}),
    (re.compile(r"Port\s*Charge|Port\s*Charges", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"PORT HANDLING CHARGE","COST CENTER B":"PORT CHARGES","PRICE CENTER":"PORT CHARGES"}),
    (re.compile(r"\bPTW\b|Permit\s*To\s*Work|Gate\s*Permit", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"CONTRACT","COST CENTER B":"PTW APPLICATION","PRICE CENTER":"PTW APPLICATION"}),
    (re.compile(r"Man\s*power|Manpower|Supervisor|Foreman|Rigger", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"MANPOWER","COST CENTER B":"LABOUR CHARGES","PRICE CENTER":"MANPOWER"}),
    (re.compile(r"Crane\s*(?:\d+\s*T)?", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"EQUIPMENT CHARGES","COST CENTER B":"CRANE","PRICE CENTER":"CRANE"}),
    (re.compile(r"Fork\s*lift|Forklift", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"EQUIPMENT CHARGES","COST CENTER B":"FORKLIFT","PRICE CENTER":"FORKLIFT"}),
    (re.compile(r"\bMGO\b|Fuel\s*Supply|Gas\s*Oil", re.I), {"COST MAIN":"AT COST","COST CENTER A":"AT COST","COST CENTER B":"FUEL (MGO)","PRICE CENTER":"MGO FUEL"}),
    (re.compile(r"Consumables?|Packing\s*Material", re.I), {"COST MAIN":"AT COST","COST CENTER A":"AT COST","COST CENTER B":"CONSUMABLES","PRICE CENTER":"CONSUMABLES"}),
    (re.compile(r"Gate\s*Pass", re.I), {"COST MAIN":"CONTRACT","COST CENTER A":"DOCUMENTATION","COST CENTER B":"GATE PASS","PRICE CENTER":"GATE PASS"}),
    (re.compile(r"Yard\s*Storage|Port\s*Storage|Laydown\s*Storage", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"STORAGE","COST CENTER B":"YARD STORAGE","PRICE CENTER":"STORAGE"}),
    (re.compile(r"Pilotage|Pilot\s*Launch", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"PILOTAGE","COST CENTER B":"PILOT LAUNCH","PRICE CENTER":"PILOTAGE"}),
    (re.compile(r"Waste", re.I), {"COST MAIN":"PORT HANDLING","COST CENTER A":"WASTE HANDLING","COST CENTER B":"WASTE","PRICE CENTER":"WASTE HANDLING"}),
]

PRICE_CENTER_HEURISTICS = [
    (re.compile(r"Pilotage", re.I), "PILOTAGE"),
    (re.compile(r"Pilot\s*Launch", re.I), "PILOT LAUNCH"),
    (re.compile(r"Berthing|Unberthing|Shifting", re.I), "BERTHING/SHIFTING"),
    (re.compile(r"Crane|(\d{2,3})\s*T", re.I), "CRANE"),
    (re.compile(r"Fork\s*lift|Forklift", re.I), "FORKLIFT"),
    (re.compile(r"Gate\s*Pass", re.I), "GATE PASS"),
    (re.compile(r"Waste", re.I), "WASTE HANDLING"),
    (re.compile(r"PTW", re.I), "PTW APPLICATION"),
    (re.compile(r"Storage", re.I), "STORAGE"),
    (re.compile(r"MGO|Fuel", re.I), "MGO FUEL"),
]

@dataclass
class InvoiceMeta:
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    customer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    samsung_ref: Optional[str] = None
    vat_percent: Optional[float] = None
    currency: str = CURRENCY
    total_amount: Optional[float] = None
    # BUSHRA format additional fields
    vessel_name: Optional[str] = None
    rotation_no: Optional[str] = None
    voyage_no: Optional[str] = None
    grt: Optional[str] = None
    dwt: Optional[str] = None
    loa: Optional[str] = None
    customer_reg_no: Optional[str] = None

@dataclass
class LineItem:
    subject: str
    ea_rates: List[Tuple[float, float]]
    amount: Optional[float] = None
    notes: Optional[str] = None
    cost_main: Optional[str] = None
    cost_center_a: Optional[str] = None
    cost_center_b: Optional[str] = None
    price_center: Optional[str] = None

@dataclass
class ParseAudit:
    total_amount_from_items: float
    total_deviation_pct: Optional[float]
    within_tolerance: bool
    item_ea_rate_checks: List[Dict[str, Any]]

@dataclass
class OFCOPayload:
    meta: InvoiceMeta
    items: List[LineItem]
    audit: ParseAudit

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception as e:
        with open(pdf_path, "rb") as f:
            data = f.read()
        return data.decode("utf-8", errors="ignore")

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def parse_invoice_number(text: str) -> Optional[str]:
    # Try OFCO-INV pattern first
    m = re.search(r"\b(OFCO-INV-\d{6,})\b", text, re.I)
    if m: return m.group(1)
    
    # Try Invoice No: pattern
    m = re.search(r"Invoice\s*(?:No\.?|Number)\s*[:\-]?\s*(OFCO-INV-\d{6,})", text, re.I)
    if m: return m.group(1)
    
    # Try BUSHRA format - look for invoice number in different locations
    m = re.search(r"Invoice\s*number\s*[:\-]?\s*([A-Z0-9\-]+)", text, re.I)
    if m: return m.group(1)
    
    # Try rotation number as invoice identifier for BUSHRA format
    m = re.search(r"Rotation\s*No\s*(\d+)", text, re.I)
    if m: return f"ROT-{m.group(1)}"
    
    return None

def parse_invoice_date(text: str) -> Optional[str]:
    for pat in [
        r"Invoice\s*Date\s*[:\-]?\s*([0-3]?\d-[A-Za-z]{3}-\d{2,4})",
        r"INVOICE\s*DATE\s*[:\-]?\s*([0-3]?\d-[A-Za-z]{3}-\d{2,4})",
        r"Invoice\s*Date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
        r"Invoice\s*Date\s*[:\-]?\s*([0-3]?\d[./-][01]?\d[./-]\d{2,4})",
    ]:
        m = re.search(pat, text, re.I)
        if m: return m.group(1)
    m = re.search(r"\b([0-3]?\d-[A-Za-z]{3}-\d{4})\b", text)
    return m.group(1) if m else None

def parse_vat_percent(text: str) -> Optional[float]:
    m = re.search(r"\bVAT\s*(?:Rate|%)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)\s*%?\b", text, re.I)
    if m: 
        try: return float(m.group(1))
        except: return None
    m2 = re.search(r"\b(\d{1,2}(?:\.\d+)?)\s*%\b", text)
    try: return float(m2.group(1)) if m2 else None
    except: return None

def parse_total_amount(text: str) -> Optional[float]:
    pats = [
        r"Amount\s*incl\.\s*VAT\s*[:\-]?\s*AED?\s*([\d,]+\.\d+|\d+)",
        r"Grand\s*Total.*?(?:AED)?\s*[:\-]?\s*([\d,]+\.\d+|\d+)",
        r"Total\s*Amount.*?(?:AED)?\s*[:\-]?\s*([\d,]+\.\d+|\d+)",
        r"\bTotal\s*[:\-]?\s*(?:AED)?\s*([\d,]+\.\d+|\d+)",
        # BUSHRA format - look for "Total (Inc. VAT)" column
        r"Total\s*\(Inc\.\s*VAT\)\s*([\d,]+\.\d+|\d+)",
        # Look for amount patterns in table rows
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*0\s*0\.00\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            try: 
                # For the last pattern, use the second group (total amount)
                amount_str = m.group(2) if len(m.groups()) > 1 else m.group(1)
                return float(amount_str.replace(",", ""))
            except: pass
    return None

def parse_samsung_ref(text: str) -> Optional[str]:
    pats = [
        r"\b(HVDC-[A-Z0-9\-_/]{3,})\b",
        r"\b(HVDC/[A-Z0-9/\-_.]{3,})\b",
        r"\b(ADOPT-[A-Z0-9\-_/]{3,})\b",
        # BUSHRA format - Voyage Number
        r"Voyage\s*No\.\s*([A-Z0-9\-]+)",
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m: return m.group(1)
    return None

def parse_vessel_info(text: str) -> Dict[str, Optional[str]]:
    """Extract vessel information from BUSHRA format"""
    vessel_info = {
        "vessel_name": None,
        "rotation_no": None,
        "voyage_no": None,
        "grt": None,
        "dwt": None,
        "loa": None,
        "customer_reg_no": None
    }
    
    # Vessel name (usually at the top)
    m = re.search(r"^([A-Z]+)\s*$", text, re.MULTILINE)
    if m:
        vessel_info["vessel_name"] = m.group(1)
    
    # Rotation Number
    m = re.search(r"Rotation\s*No\s*(\d+)", text, re.I)
    if m:
        vessel_info["rotation_no"] = m.group(1)
    
    # Voyage Number
    m = re.search(r"Voyage\s*No\.\s*([A-Z0-9\-]+)", text, re.I)
    if m:
        vessel_info["voyage_no"] = m.group(1)
    
    # GRT/DWT
    m = re.search(r"GRT/DWT\s*([\d.]+)/([\d.]+)", text, re.I)
    if m:
        vessel_info["grt"] = m.group(1)
        vessel_info["dwt"] = m.group(2)
    
    # LOA
    m = re.search(r"LOA\s*([\d.]+)", text, re.I)
    if m:
        vessel_info["loa"] = m.group(1)
    
    # Customer Registration Number
    m = re.search(r"Customer\s*REG\.\s*No\s*:\s*(\d+)", text, re.I)
    if m:
        vessel_info["customer_reg_no"] = m.group(1)
    
    return vessel_info

TAIL_NUMERIC = re.compile(r"""
    (?P<tax>\d{1,2}(?:\.\d+)?%)\s*
    (?P<qty>\d+(?:\.\d+)?)\s+
    (?P<rate>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<uom>[A-Za-z]{1,6})\s*
    (?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<vat>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<total>\d{1,3}(?:,\d{3})*(?:\.\d+)?)
    \s*$
""", re.X)

# BUSHRA format table pattern - more flexible
BUSHRA_TABLE_PATTERN = re.compile(r"""
    (?P<sno>\d+)\s+
    (?P<tar_code>[\d.]+)\s+
    (?P<description>.*?)\s+
    (?P<amount>[\d,]+\.\d+)\s+
    (?P<vat_pct>\d+)\s+
    (?P<vat_amount>[\d,]+\.\d+)\s+
    (?P<total>[\d,]+\.\d+)
""", re.X | re.MULTILINE | re.DOTALL)

def parse_bushra_table(text: str) -> List[Dict[str, Any]]:
    """Parse BUSHRA format table with S No, Tar. Code, Description, Amount, VAT%, VAT Amount, Total columns"""
    rows = []
    
    # Simple and effective pattern for BUSHRA table
    pattern = r"(\d+)\s+([\d.]+)\s+(.*?)\s+([\d,]+\.\d+)\s+(\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)"
    
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    for match in matches:
        sno, tar_code, description, amount, vat_pct, vat_amount, total = match
        rows.append({
            "s_no": int(sno),
            "tar_code": tar_code,
            "description": _norm(description),
            "amount": float(amount.replace(",", "")),
            "vat_pct": int(vat_pct),
            "vat_amount": float(vat_amount.replace(",", "")),
            "total_incl_vat": float(total.replace(",", "")),
            "qty": 1.0,  # Default quantity for BUSHRA format
            "rate": float(amount.replace(",", "")),  # Rate = Amount for BUSHRA
            "uom": "LS",  # Default UOM
            "tax_rate": f"{vat_pct}%"
        })
    
    return rows

def parse_table_rows(text: str) -> List[Dict[str, Any]]:
    # Check if this is Samsung OFCO format first (has OFCO-INV pattern)
    if "OFCO-INV-" in text:
        # Use original OFCO format for Samsung invoices
        lines = [l.rstrip() for l in text.splitlines()]
        start_idx = None
        for i, ln in enumerate(lines):
            if ("Description" in ln and "Amount" in ln) or ("S N" in ln and "Description" in ln):
                start_idx = i + 1
                break
        if start_idx is None:
            return []
        rows = []
        buf_desc = ""
        for ln in lines[start_idx:]:
            if not ln.strip():
                continue
            m = TAIL_NUMERIC.search(ln)
            if m:
                head = ln[:m.start()].strip()
                desc = " ".join([d for d in [buf_desc.strip(), head] if d])
                buf_desc = ""
                def f2(x): return float(x.replace(",", ""))
                row = {
                    "description": _norm(desc),
                    "tax_rate": m.group("tax"),
                    "qty": f2(m.group("qty")),
                    "rate": f2(m.group("rate")),
                    "uom": m.group("uom"),
                    "amount": f2(m.group("amount")),
                    "vat": f2(m.group("vat")),
                    "total_incl_vat": f2(m.group("total")),
                }
                rows.append(row)
            else:
                buf_desc += (" " + ln.strip())
            if len(rows) > 0 and re.search(r"\b(Total|Bank|Terms|Notes)\b", ln, re.I):
                break
        return rows
    
    # Try BUSHRA format for non-Samsung invoices
    bushra_rows = parse_bushra_table(text)
    if bushra_rows:
        return bushra_rows
    
    # Fallback to original OFCO format
    lines = [l.rstrip() for l in text.splitlines()]
    start_idx = None
    for i, ln in enumerate(lines):
        if ("Description" in ln and "Amount" in ln) or ("S N" in ln and "Description" in ln):
            start_idx = i + 1
            break
    if start_idx is None:
        return []
    rows = []
    buf_desc = ""
    for ln in lines[start_idx:]:
        if not ln.strip():
            continue
        m = TAIL_NUMERIC.search(ln)
        if m:
            head = ln[:m.start()].strip()
            desc = " ".join([d for d in [buf_desc.strip(), head] if d])
            buf_desc = ""
            def f2(x): return float(x.replace(",", ""))
            row = {
                "description": _norm(desc),
                "tax_rate": m.group("tax"),
                "qty": f2(m.group("qty")),
                "rate": f2(m.group("rate")),
                "uom": m.group("uom"),
                "amount": f2(m.group("amount")),
                "vat": f2(m.group("vat")),
                "total_incl_vat": f2(m.group("total")),
            }
            rows.append(row)
        else:
            buf_desc += (" " + ln.strip())
        if len(rows) > 0 and re.search(r"\b(Total|Bank|Terms|Notes)\b", ln, re.I):
            break
    return rows

def find_subject_lines(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidates = []
    for l in lines:
        if any(k in l for k in ["Agency fee", "ADP", "SAFEEN", "Supply of", "Berthing", "Pilotage", "Man-power", "Forklift", "Crane", "Port Dues", "Channel", "Gate Pass", "Waste", "PTW", "Storage", "MGO"]):
            candidates.append(_norm(l))
    seen, out = set(), []
    for c in candidates:
        lc = c.lower()
        if lc not in seen:
            out.append(c); seen.add(lc)
    return out

def map_cost_centers_from_subject(subject: str) -> Dict[str, Optional[str]]:
    for pat, mp in SUBJECT_CC_MAP:
        if pat.search(subject):
            return {
                "COST MAIN": mp.get("COST MAIN"),
                "COST CENTER A": mp.get("COST CENTER A"),
                "COST CENTER B": mp.get("COST CENTER B"),
                "PRICE CENTER": mp.get("PRICE CENTER"),
            }
    pc = None
    for pat, name in PRICE_CENTER_HEURISTICS:
        if pat.search(subject):
            pc = name; break
    return {"COST MAIN": None,"COST CENTER A": None,"COST CENTER B": None,"PRICE CENTER": pc}

def build_items(text: str) -> List['LineItem']:
    items: List[LineItem] = []
    rows = parse_table_rows(text)
    if rows:
        for r in rows:
            cc = map_cost_centers_from_subject(r["description"])
            items.append(LineItem(
                subject=r["description"],
                ea_rates=[(r["qty"], r["rate"])],
                amount=r["amount"],
                notes=f"UOM={r['uom']}; VAT={r['tax_rate']}; TotalInclVAT={r['total_incl_vat']}",
                cost_main=cc.get("COST MAIN"),
                cost_center_a=cc.get("COST CENTER A"),
                cost_center_b=cc.get("COST CENTER B"),
                price_center=cc.get("PRICE CENTER"),
            ))
        return items
    subjects = find_subject_lines(text)
    for sj in subjects:
        block_pat = re.compile(re.escape(sj) + r"(?:.*\n){0,3}", re.I)
        m = block_pat.search(text); block = sj if not m else m.group(0)
        m2 = TAIL_NUMERIC.search(block)
        ea_rates = []; amt = None
        if m2:
            qty = float(m2.group("qty")); rate = float(m2.group("rate").replace(",", ""))
            ea_rates = [(qty, rate)]; amt = float(m2.group("amount").replace(",", ""))
        cc = map_cost_centers_from_subject(sj)
        items.append(LineItem(subject=sj, ea_rates=ea_rates, amount=amt,
                              cost_main=cc.get("COST MAIN"), cost_center_a=cc.get("COST CENTER A"),
                              cost_center_b=cc.get("COST CENTER B"), price_center=cc.get("PRICE CENTER")))
    return items

def ea_rate_amount_check(item: LineItem) -> Dict[str, Any]:
    if item.amount is None or not item.ea_rates:
        return {"subject": item.subject, "status": "SKIP", "reason": "missing EA/Rate or Amount"}
    total = sum(ea*rate for ea, rate in item.ea_rates)
    dev = abs(total - item.amount)
    ok = (dev <= ABS_EPS) or (item.amount > 0 and dev/item.amount <= REL_TOL)
    return {"subject": item.subject, "calc": round(total,2), "amount": round(item.amount or 0,2),
            "dev": round(dev,2), "ok": ok}

def compute_audit(meta: InvoiceMeta, items: List[LineItem]) -> ParseAudit:
    total_items = round(sum(i.amount or 0.0 for i in items), 2)
    if meta.total_amount and meta.total_amount > 0:
        dev_pct = round(abs(total_items - meta.total_amount)/meta.total_amount*100, 2)
        within = dev_pct/100 <= REL_TOL
    else:
        dev_pct = None; within = True
    checks = [ea_rate_amount_check(i) for i in items]
    return ParseAudit(total_amount_from_items=total_items, total_deviation_pct=dev_pct,
                      within_tolerance=within, item_ea_rate_checks=checks)

def parse_ofco_invoice(pdf_path: str) -> OFCOPayload:
    text = extract_text_from_pdf(pdf_path)
    
    # Parse vessel information for BUSHRA format
    vessel_info = parse_vessel_info(text)
    
    meta = InvoiceMeta(
        invoice_number=parse_invoice_number(text),
        invoice_date=parse_invoice_date(text),
        samsung_ref=parse_samsung_ref(text),
        vat_percent=parse_vat_percent(text),
        currency=CURRENCY,
        total_amount=parse_total_amount(text),
        # BUSHRA format fields
        vessel_name=vessel_info.get("vessel_name"),
        rotation_no=vessel_info.get("rotation_no"),
        voyage_no=vessel_info.get("voyage_no"),
        grt=vessel_info.get("grt"),
        dwt=vessel_info.get("dwt"),
        loa=vessel_info.get("loa"),
        customer_reg_no=vessel_info.get("customer_reg_no"),
    )
    items = build_items(text)
    audit = compute_audit(meta, items)
    return OFCOPayload(meta=meta, items=items, audit=audit)

def payload_to_json_dict(payload: OFCOPayload) -> Dict[str, Any]:
    return {
        "meta": asdict(payload.meta),
        "items": [{
            "SUBJECT": it.subject,
            "EA_RATE_PAIRS": [(round(ea,2), round(rate,2)) for ea, rate in it.ea_rates],
            "Amount (AED)": round(it.amount,2) if it.amount is not None else None,
            "COST MAIN": it.cost_main,
            "COST CENTER A": it.cost_center_a,
            "COST CENTER B": it.cost_center_b,
            "PRICE CENTER": it.price_center,
            "NOTES": it.notes
        } for it in payload.items],
        "audit": asdict(payload.audit)
    }

def flatten_payload_to_csv_rows(payload: OFCOPayload) -> List[List[str]]:
    """Convert OFCOPayload to CSV rows with all metadata, items, and audit info"""
    rows = []
    
    # Header row
    header = [
        "Invoice Number", "Date", "Samsung Ref", "VAT%", "Currency", "Total Amount",
        "Vessel Name", "Rotation No", "Voyage No", "GRT", "DWT", "LOA", "Customer Reg No",
        "Item#", "Subject", "EA", "Rate", "Amount (AED)",
        "Cost Main", "Cost Center A", "Cost Center B", "Price Center",
        "UOM", "Tax Rate", "Total Incl VAT", "Notes"
    ]
    rows.append(header)
    
    # Extract metadata
    meta = payload.meta
    
    # Data rows - one per line item
    for idx, item in enumerate(payload.items, 1):
        # Extract EA and Rate (use first pair if multiple)
        ea = item.ea_rates[0][0] if item.ea_rates else ""
        rate = item.ea_rates[0][1] if item.ea_rates else ""
        
        # Parse notes for UOM, Tax Rate, Total Incl VAT
        uom = tax_rate = total_incl_vat = ""
        if item.notes:
            uom_match = re.search(r"UOM=([^;]+)", item.notes)
            if uom_match: uom = uom_match.group(1).strip()
            tax_match = re.search(r"VAT=([^;]+)", item.notes)
            if tax_match: tax_rate = tax_match.group(1).strip()
            total_match = re.search(r"TotalInclVAT=([^;]+)", item.notes)
            if total_match: total_incl_vat = total_match.group(1).strip()
        
        row = [
            meta.invoice_number or "",
            meta.invoice_date or "",
            meta.samsung_ref or "",
            str(meta.vat_percent) if meta.vat_percent is not None else "",
            meta.currency or "",
            str(meta.total_amount) if meta.total_amount is not None else "",
            meta.vessel_name or "",
            meta.rotation_no or "",
            meta.voyage_no or "",
            meta.grt or "",
            meta.dwt or "",
            meta.loa or "",
            meta.customer_reg_no or "",
            str(idx),
            item.subject or "",
            str(ea) if ea else "",
            str(rate) if rate else "",
            str(item.amount) if item.amount is not None else "",
            item.cost_main or "",
            item.cost_center_a or "",
            item.cost_center_b or "",
            item.price_center or "",
            uom,
            tax_rate,
            total_incl_vat,
            item.notes or ""
        ]
        rows.append(row)
    
    # Add blank row
    rows.append([""] * len(header))
    
    # Audit summary rows
    audit = payload.audit
    rows.append(["AUDIT SUMMARY:"] + [""] * (len(header) - 1))
    rows.append(["Items Total:", "", "", "", "", str(audit.total_amount_from_items)] + [""] * (len(header) - 6))
    rows.append(["Invoice Total:", "", "", "", "", str(meta.total_amount or "")] + [""] * (len(header) - 6))
    rows.append(["Deviation %:", "", "", "", "", str(audit.total_deviation_pct) if audit.total_deviation_pct is not None else "N/A"] + [""] * (len(header) - 6))
    rows.append(["Within Tolerance:", "", "", "", "", "PASS" if audit.within_tolerance else "FAIL"] + [""] * (len(header) - 6))
    
    passed_checks = sum(1 for chk in audit.item_ea_rate_checks if chk.get('ok', False))
    total_checks = len(audit.item_ea_rate_checks)
    rows.append(["EA×Rate Checks Passed:", "", "", "", "", f"{passed_checks}/{total_checks}"] + [""] * (len(header) - 6))
    
    return rows

def write_csv(rows: List[List[str]], output_path: str):
    """Write rows to CSV file"""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"[OK] Wrote CSV: {output_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("--out", default=None, help="JSON output file path")
    ap.add_argument("--csv", default=None, help="CSV output file path")
    args = ap.parse_args()
    from pprint import pprint
    payload = parse_ofco_invoice(args.pdf_path)
    out = payload_to_json_dict(payload)
    
    # JSON output
    if args.out:
        js = json.dumps(out, ensure_ascii=False, indent=2)
        with open(args.out, "w", encoding="utf-8") as f: f.write(js)
        print(f"[OK] Wrote JSON: {args.out}")
    
    # CSV output
    if args.csv:
        csv_rows = flatten_payload_to_csv_rows(payload)
        write_csv(csv_rows, args.csv)
    
    # If no output specified, print JSON
    if not args.out and not args.csv:
        js = json.dumps(out, ensure_ascii=False, indent=2)
        print(js)

if __name__ == "__main__":
    main()
