#!/usr/bin/env python3
"""
Standalone JSON to CSV converter for OFCO Parser output
Converts JSON output from ofco_parser.py to Excel-compatible CSV format
"""

import json
import csv
import argparse
import re
from typing import List, Dict, Any


def flatten_json_to_csv_rows(data: Dict[str, Any]) -> List[List[str]]:
    """Convert JSON data to CSV rows with all metadata, items, and audit info"""
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
    meta = data.get("meta", {})
    
    # Data rows - one per line item
    for idx, item in enumerate(data.get("items", []), 1):
        # Extract EA and Rate (use first pair if multiple)
        ea_rate_pairs = item.get("EA_RATE_PAIRS", [])
        ea = ea_rate_pairs[0][0] if ea_rate_pairs else ""
        rate = ea_rate_pairs[0][1] if ea_rate_pairs else ""
        
        # Parse notes for UOM, Tax Rate, Total Incl VAT
        uom = tax_rate = total_incl_vat = ""
        notes = item.get("NOTES", "")
        if notes:
            uom_match = re.search(r"UOM=([^;]+)", notes)
            if uom_match: uom = uom_match.group(1).strip()
            tax_match = re.search(r"VAT=([^;]+)", notes)
            if tax_match: tax_rate = tax_match.group(1).strip()
            total_match = re.search(r"TotalInclVAT=([^;]+)", notes)
            if total_match: total_incl_vat = total_match.group(1).strip()
        
        row = [
            meta.get("invoice_number", ""),
            meta.get("invoice_date", ""),
            meta.get("samsung_ref", ""),
            str(meta.get("vat_percent", "")),
            meta.get("currency", ""),
            str(meta.get("total_amount", "")),
            meta.get("vessel_name", ""),
            meta.get("rotation_no", ""),
            meta.get("voyage_no", ""),
            meta.get("grt", ""),
            meta.get("dwt", ""),
            meta.get("loa", ""),
            meta.get("customer_reg_no", ""),
            str(idx),
            item.get("SUBJECT", ""),
            str(ea) if ea else "",
            str(rate) if rate else "",
            str(item.get("Amount (AED)", "")),
            item.get("COST MAIN", ""),
            item.get("COST CENTER A", ""),
            item.get("COST CENTER B", ""),
            item.get("PRICE CENTER", ""),
            uom,
            tax_rate,
            total_incl_vat,
            notes
        ]
        rows.append(row)
    
    # Add blank row
    rows.append([""] * len(header))
    
    # Audit summary rows
    audit = data.get("audit", {})
    rows.append(["AUDIT SUMMARY:"] + [""] * (len(header) - 1))
    rows.append(["Items Total:", "", "", "", "", str(audit.get("total_amount_from_items", ""))] + [""] * (len(header) - 6))
    rows.append(["Invoice Total:", "", "", "", "", str(meta.get("total_amount", ""))] + [""] * (len(header) - 6))
    
    dev_pct = audit.get("total_deviation_pct")
    rows.append(["Deviation %:", "", "", "", "", str(dev_pct) if dev_pct is not None else "N/A"] + [""] * (len(header) - 6))
    rows.append(["Within Tolerance:", "", "", "", "", "PASS" if audit.get("within_tolerance") else "FAIL"] + [""] * (len(header) - 6))
    
    item_checks = audit.get("item_ea_rate_checks", [])
    passed_checks = sum(1 for chk in item_checks if chk.get('ok', False))
    total_checks = len(item_checks)
    rows.append(["EA×Rate Checks Passed:", "", "", "", "", f"{passed_checks}/{total_checks}"] + [""] * (len(header) - 6))
    
    return rows


def write_csv(rows: List[List[str]], output_path: str):
    """Write rows to CSV file"""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"[OK] Wrote CSV: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert OFCO Parser JSON output to Excel-compatible CSV"
    )
    parser.add_argument("json_file", help="Input JSON file from ofco_parser.py")
    parser.add_argument("--out", "-o", required=True, help="Output CSV file path")
    
    args = parser.parse_args()
    
    # Load JSON
    print(f"Reading JSON from: {args.json_file}")
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to CSV rows
    csv_rows = flatten_json_to_csv_rows(data)
    
    # Write CSV
    write_csv(csv_rows, args.out)
    
    print(f"\n✅ Conversion complete!")
    print(f"   Input:  {args.json_file}")
    print(f"   Output: {args.out}")
    print(f"   Rows:   {len(csv_rows)} (including header and audit summary)")


if __name__ == "__main__":
    main()


