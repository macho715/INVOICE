
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Patch — Standard_Lines 변환 (ADP/SAFEEN + OFCO 동시 병합)
- 규격: OFCO Zayed Port Lines Guide v1.3
- 고정 컬럼: invoice_no, line_no, tariff_id, description, unit1, unit2, unit3, rate,
             amount_excl_tax, tax_rate_pct, tax_amount, total_incl_tax, calc_check, evidence
- 수치: 2 decimals, AED 고정
- EA×RatePair 최대 4 → 필요 시 multi-row expand
- VAT/합계 검증(calc_check), Evidence 필수
Usage:
  python step03_ofco_to_standard_lines_excel_patched_v2.py --input phase1_payload.json --out xlsx_out.xlsx
"""
from __future__ import annotations
import json, math, re, argparse
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

COLS = [
    "invoice_no","line_no","tariff_id","description",
    "unit1","unit2","unit3","rate",
    "amount_excl_tax","tax_rate_pct","tax_amount","total_incl_tax",
    "calc_check","evidence"
]

def D(x) -> Decimal:
    try:
        if x is None or (isinstance(x, str) and x.strip()==""):
            return Decimal("0")
        if isinstance(x, (int, float)):
            return Decimal(str(x))
        # strip commas and spaces
        s = str(x).replace(',', '').strip()
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal("0")

def r2(x: Decimal) -> Decimal:
    return x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

@dataclass
class StdLine:
    invoice_no: str
    line_no: int
    tariff_id: str
    description: str
    unit1: Decimal
    unit2: Decimal
    unit3: Decimal
    rate: Decimal
    amount_excl_tax: Decimal
    tax_rate_pct: Decimal
    tax_amount: Decimal
    total_incl_tax: Decimal
    calc_check: bool
    evidence: str

    def to_row(self) -> Dict[str, Any]:
        row = asdict(self)
        # Ensure types for DataFrame / Excel
        row['unit1'] = float(r2(self.unit1))
        row['unit2'] = float(r2(self.unit2))
        row['unit3'] = float(r2(self.unit3))
        row['rate'] = float(r2(self.rate))
        row['amount_excl_tax'] = float(r2(self.amount_excl_tax))
        row['tax_rate_pct'] = float(r2(self.tax_rate_pct))
        row['tax_amount'] = float(r2(self.tax_amount))
        row['total_incl_tax'] = float(r2(self.total_incl_tax))
        row['calc_check'] = bool(self.calc_check)
        return row

# ---- Pattern helpers (Tariff & Subject hints) ----
_LABOUR_CODES = {'802.3A', '802.5A'}
_HEAVY_LIFT_CODES = {'703.1'}

def _decompose_units(tariff_id: str, ea: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
    t = (tariff_id or '').upper().strip()
    if t in _HEAVY_LIFT_CODES:
        # 703.1 Heavy Lift: unit1=FRT(=ea), unit2=1, unit3=1
        return (ea, Decimal('1'), Decimal('1'))
    if t in _LABOUR_CODES:
        # Labour/Foreman: unit1=0, unit2=persons(=ea), unit3=hours=1 (unknown → 1.00)
        # Caller may split if hours provided as another RatePair upstream.
        return (Decimal('0'), ea, Decimal('1'))
    # Default: single-factor quantity
    return (ea if ea != 0 else Decimal('1'), Decimal('1'), Decimal('1'))

def _calc_amount(u1: Decimal, u2: Decimal, u3: Decimal, rate: Decimal) -> Decimal:
    return r2(u1 * u2 * u3 * rate)

def _calc_tax(amount_excl: Decimal, vat_pct: Decimal) -> Tuple[Decimal, Decimal]:
    tax = r2(amount_excl * (vat_pct/Decimal('100')))
    total = r2(amount_excl + tax)
    return tax, total

def _bool_calc_check(amount_excl: Decimal, u1: Decimal, u2: Decimal, u3: Decimal, rate: Decimal) -> bool:
    expected = _calc_amount(u1,u2,u3,rate)
    return abs(expected - r2(amount_excl)) <= Decimal('0.01')

# ---- Core transformers ----
def expand_ratepairs_to_stdlines(base: Dict[str, Any]) -> List[StdLine]:
    """
    base includes: invoice_no, line_no, tariff_id, description, vat, evidence, ratepairs(list of {ea,rate})
    If no ratepairs present, fallback: EA=1.00, Rate=Amount_excl_tax (as per rule-of-thumb)
    """
    invoice_no = str(base.get('invoice_no') or base.get('ofco_invoice_no') or base.get('invoiceNo') or '').strip()
    line_no = int(base.get('line_no') or base.get('NO') or base.get('lineNo') or 0)
    tariff_id = str(base.get('tariff_id') or base.get('tariffId') or base.get('tar_code') or '').strip()
    description = str(base.get('description') or base.get('subject') or '').strip()
    vat = D(base.get('vat') or base.get('VAT') or 0)
    evidence = str(base.get('evidence') or base.get('prov') or base.get('pdf_ref') or '').strip()

    ratepairs = []
    if isinstance(base.get('ratepairs'), list):
        ratepairs = base['ratepairs']
    else:
        # collect hasEA_i/hasRate_i style
        for i in range(1,5):
            ea_i = base.get(f'ea_{i}') or base.get(f'EA_{i}') or base.get(f'hasEA_{i}')
            rate_i = base.get(f'rate_{i}') or base.get(f'RATE_{i}') or base.get(f'hasRate_{i}')
            if ea_i is not None or rate_i is not None:
                ratepairs.append({'ea': ea_i, 'rate': rate_i})

    stdlines: List[StdLine] = []
    if not ratepairs:
        # fallback EA=1.00, Rate=Amount, Amount=base['amount_excl_tax']
        amount = D(base.get('amount_excl_tax') or base.get('amount') or base.get('line_amount') or 0)
        ea = Decimal('1.00')
        rate = r2(amount)
        u1,u2,u3 = _decompose_units(tariff_id, ea)
        amount_excl = _calc_amount(u1,u2,u3,rate)
        tax, total = _calc_tax(amount_excl, r2(vat))
        stdlines.append(StdLine(invoice_no, line_no, tariff_id, description,
                                u1,u2,u3, rate, amount_excl, r2(vat), tax, total,
                                _bool_calc_check(amount_excl,u1,u2,u3,rate), evidence))
        return stdlines

    # expand each ratepair as its own row (line_no suffix .i)
    idx = 0
    for rp in ratepairs:
        idx += 1
        ea = D(rp.get('ea'))
        rate = r2(D(rp.get('rate')))
        if ea == 0 and rate == 0:
            continue
        u1,u2,u3 = _decompose_units(tariff_id, ea if ea!=0 else Decimal('1'))
        amount_excl = _calc_amount(u1,u2,u3,rate)
        tax, total = _calc_tax(amount_excl, r2(vat))
        stdlines.append(StdLine(invoice_no, int(f"{line_no}{idx:01d}"), tariff_id, description,
                                u1,u2,u3, rate, amount_excl, r2(vat), tax, total,
                                _bool_calc_check(amount_excl,u1,u2,u3,rate), evidence))
    return stdlines

def convert_source_bundle(bundle: Dict[str, Any], source_flag: str) -> List[StdLine]:
    """
    bundle['lines'] : list of raw line dicts from Phase 1 (parser output)
    source_flag in {'ADP_SAFEEN','OFCO'}
    """
    rows: List[StdLine] = []
    for raw in bundle.get('lines', []):
        if source_flag and str(raw.get('source','')).upper() not in {source_flag, '' if source_flag=='OFCO' else ''}:
            # allow missing 'source' for OFCO; otherwise filter exact
            if source_flag != 'OFCO':
                continue
        stds = expand_ratepairs_to_stdlines(raw)
        rows.extend(stds)
    return rows

def run_phase2_merge(phase1_json_path: str, excel_out_path: str) -> None:
    with open(phase1_json_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    # Expected structure (tolerant): {'ADP_SAFEEN': {lines: [...]}, 'OFCO': {lines: [...]}} or flat {'lines':[...]}.
    rows: List[StdLine] = []
    if isinstance(payload, dict) and ('ADP_SAFEEN' in payload or 'OFCO' in payload):
        if 'ADP_SAFEEN' in payload:
            rows += convert_source_bundle(payload['ADP_SAFEEN'], 'ADP_SAFEEN')
        if 'OFCO' in payload:
            rows += convert_source_bundle(payload['OFCO'], 'OFCO')
    else:
        # flat
        rows += convert_source_bundle(payload, 'OFCO')

    # DataFrame in fixed column order
    df = pd.DataFrame([r.to_row() for r in rows], columns=COLS)

    # Post-validations (calc_check, group totals integrity hints)
    # Note: amount_excl_tax + tax_amount == total_incl_tax
    df['calc_check_total'] = (df['amount_excl_tax'].round(2) + df['tax_amount'].round(2) - df['total_incl_tax'].round(2)).abs() <= 0.01
    df['calc_check'] = df['calc_check'] & df['calc_check_total']

    # Excel write
    with pd.ExcelWriter(excel_out_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Standard_Lines', index=False)
        wb  = writer.book
        ws  = writer.sheets['Standard_Lines']
        fmt2 = wb.add_format({'num_format': '0.00'})
        # Apply 2-dec to numeric cols
        for col in ['unit1','unit2','unit3','rate','amount_excl_tax','tax_rate_pct','tax_amount','total_incl_tax']:
            idx = df.columns.get_loc(col)
            ws.set_column(idx, idx, 14, fmt2)
        # Evidence, description wider
        ws.set_column(df.columns.get_loc('description'), df.columns.get_loc('description'), 50)
        ws.set_column(df.columns.get_loc('evidence'), df.columns.get_loc('evidence'), 28)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='Phase 1 JSON payload path')
    ap.add_argument('--out', required=True, help='Excel output path')
    args = ap.parse_args()
    run_phase2_merge(args.input, args.out)

if __name__ == '__main__':
    main()
