
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Iterable
import pandas as pd

Q2 = lambda x: Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
TOL = Decimal("0.01")

PRIORITY_ORDER = [
    "AGENCY_FEE_FOR_CARGO_CLEARANCE",
    "AGENCY_FEE_FOR_BERTHING_ARRANGEMENT",
    "AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT",
    "AGENCY_FOR_ARRANGEMENT_PTW",
    "PORT_DUES", "PORT_DUE",
    "CHANNEL", "CROSSING", "TRANSIT",
    "PILOTAGE", "PILOT_LAUNCH",
    "WASTE_HANDLING", "GENERAL_WASTE_SERVICE",
    "OFCO_HANDLING_FEE",
    "DOCUMENT_PROCESSING_CHARGE",
    "BULK_MATERIAL",
    "HEAVY_LIFT",
    "GENERAL_CARGO",
    "MANPOWER",
    "EQUIPMENT", "FORKLIFT",
    "CONSUMABLES", "DIESEL_VESSEL", "BUNKERING", "ANCHORAGE", "PEC_CHANGES",
    "OTHERS"
]

def priority_fn(name: str) -> int:
    u = name.upper()
    for i, kw in enumerate(PRIORITY_ORDER):
        if kw in u:
            return i
    return len(PRIORITY_ORDER) + 1

def to_dec(val) -> Optional[Decimal]:
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if s.upper() in {"", "-", "—", "N/A", "NONE", "NULL", "NAN"}:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        try:
            return Decimal(str(float(s)))
        except Exception:
            return None

@dataclass
class Item:
    name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal
    priority: int
    flags: Dict[str, int] = field(default_factory=dict)

def build_items(row: dict, bases: Iterable[str]) -> List[Item]:
    items: List[Item] = []
    for b in bases:
        qraw = row.get(f"{b}_QTY")
        araw = row.get(f"{b}_AMOUNT")
        has_q = qraw is not None and str(qraw).strip() != ""
        has_a = araw is not None and str(araw).strip() != ""

        if not has_q and not has_a:
            continue

        q = to_dec(qraw)
        a = to_dec(araw)
        flags: Dict[str, int] = {}

        if q is not None and a is not None and q != 0:
            r = Q2(a / q)
            amt = Q2(q * r)
            if a is not None and Q2(a) != amt:
                flags["FLAG_AMOUNT_ROUNDED"] = 1
                amt = Q2(a)
        elif a is not None and (q is None or q == 0):
            q = Decimal("1.00")
            r = Q2(a)
            amt = Q2(q * r)
            flags["FLAG_QTY_ASSUMED"] = 1
            if qraw is not None and to_dec(qraw) == 0:
                flags["FLAG_ZERO_QTY_FIX"] = 1
        elif q is not None and a is None:
            # qty only -> insufficient evidence
            continue
        else:
            continue

        items.append(Item(
            name=b,
            qty=Q2(q),
            rate=r,
            amount=amt,
            priority=priority_fn(b),
            flags=flags
        ))

    # priority asc, name asc, |amount| desc
    items.sort(key=lambda it: (it.priority, it.name, -abs(it.amount)))
    return items

def pack_ea(items: List[Item], max_slots: int = 4) -> Tuple[List[Item], List[Item]]:
    return items[:max_slots], items[max_slots:]

def guess_ref_amount(row: dict) -> Optional[Decimal]:
    for c in ("amount_excl_tax","line_amount","amount","subtotal","total_excl_tax"):
        if c in row and str(row[c]).strip() != "":
            d = to_dec(row[c])
            if d is not None:
                return Q2(d)
    # fallback: sum of *_AMOUNT
    s = Decimal("0.00")
    found = False
    for k, v in row.items():
        k_str = str(k)
        if k_str.endswith("_AMOUNT") and not k_str.startswith("EA_"):
            dv = to_dec(v)
            if dv is not None:
                found = True
                s += dv
    return Q2(s) if found else None

def validate_line(ea_items: List[Item], ref: Optional[Decimal],
                  tax_rate: Optional[Decimal], tax_amount: Optional[Decimal],
                  total_incl: Optional[Decimal]) -> dict:
    ea_total = Q2(sum((it.amount for it in ea_items), Decimal("0.00")))
    out = {
        "EA_Total_Amount": ea_total,
        "calc_status": "",
        "calc_check": None,
        "calc_diff": None,
        "expected_vat": None,
        "vat_check": None,
        "vat_diff": None,
        "expected_total": None,
        "total_check": None,
        "total_diff": None
    }
    if ref is not None:
        diff = Q2(ea_total - ref)
        out["calc_diff"] = diff
        out["calc_check"] = abs(diff) <= TOL
        if abs(diff) == Decimal("0.00"):
            out["calc_status"] = "EXACT"
        elif abs(diff) <= TOL:
            out["calc_status"] = "WITHIN_TOL"
        else:
            out["calc_status"] = "FAIL"

    if (tax_rate is not None) and (ref is not None):
        exp_vat = Q2(ref * (tax_rate/Decimal(100)))
        out["expected_vat"] = exp_vat
        if tax_amount is not None:
            vd = Q2(exp_vat - Q2(tax_amount))
            out["vat_diff"] = vd
            out["vat_check"] = abs(vd) <= TOL

    if (tax_amount is not None) and (ref is not None) and (total_incl is not None):
        exp_total = Q2(ref + Q2(tax_amount))
        out["expected_total"] = exp_total
        td = Q2(exp_total - Q2(total_incl))
        out["total_diff"] = td
        out["total_check"] = abs(td) <= TOL

    return out

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # bases discovery
    # 컬럼명을 문자열로 변환하여 처리
    df_cols_str = [str(c) for c in df.columns]
    qty_cols = [c for c in df_cols_str if c.endswith("_QTY") and not c.startswith("EA_")]
    amt_cols = [c for c in df_cols_str if c.endswith("_AMOUNT") and not c.startswith("EA_")]
    bases = sorted(set([c[:-4] for c in qty_cols]) | set([c[:-7] for c in amt_cols]))

    rows_out = []
    for _, row in df.astype("string").iterrows():
        row_dict = row.to_dict()
        # 컬럼명을 문자열로 정규화 (정수 컬럼명 처리)
        row_dict_str = {str(k): v for k, v in row_dict.items()}
        items = build_items(row_dict_str, bases)

        # fiscal references
        ref = guess_ref_amount(row_dict_str)
        tr = to_dec(row_dict_str.get("tax_rate_pct")) if "tax_rate_pct" in row_dict_str else None
        ta = to_dec(row_dict_str.get("tax_amount")) if "tax_amount" in row_dict_str else None
        ti = to_dec(row_dict_str.get("total_incl_tax")) if "total_incl_tax" in row_dict_str else None

        # split by 4
        chunks = [items[i:i+4] for i in range(0, len(items), 4)] or [[]]

        for cidx, chunk in enumerate(chunks):
            out = row_dict_str.copy()
            out["split_suffix"] = chr(ord('A') + cidx)
            out["FLAG_SPLIT"] = 1 if len(items) > 4 else 0

            # EA slots
            for i in range(4):
                if i < len(chunk):
                    it = chunk[i]
                    out[f"EA_{i+1}_Name"] = it.name
                    out[f"EA_{i+1}_Qty"] = f"{it.qty:.2f}"
                    out[f"EA_{i+1}_Rate"] = f"{it.rate:.2f}"
                    out[f"EA_{i+1}_Amount"] = f"{it.amount:.2f}"
                else:
                    out[f"EA_{i+1}_Name"] = ""
                    out[f"EA_{i+1}_Qty"] = ""
                    out[f"EA_{i+1}_Rate"] = ""
                    out[f"EA_{i+1}_Amount"] = ""

            # validation: single-chunk uses ref; split → use chunk sum as ref (same VAT rate)
            if len(items) <= 4:
                v = validate_line(chunk, ref, tr, ta, ti)
            else:
                chunk_ref = Q2(sum((it.amount for it in chunk), Decimal("0.00")))
                if tr is not None:
                    chunk_ta = Q2(chunk_ref * (tr/Decimal(100)))
                    chunk_ti = Q2(chunk_ref + chunk_ta)
                else:
                    chunk_ta = None; chunk_ti = None
                v = validate_line(chunk, chunk_ref, tr, chunk_ta, chunk_ti)

            for k, val in v.items():
                out[k] = f"{val:.2f}" if isinstance(val, Decimal) else ("" if val is None else val)
            out["EA_Mapped_Count"] = len(chunk)
            rows_out.append(out)

    df_out = pd.DataFrame(rows_out)
    return df_out

def process_csv(src_csv: str, out_csv: str, out_xlsx: Optional[str] = None) -> None:
    df = pd.read_csv(src_csv, dtype=str)
    df_out = process_dataframe(df)
    df_out.to_csv(out_csv, index=False)
    if out_xlsx:
        df_out.to_excel(out_xlsx, index=False)
