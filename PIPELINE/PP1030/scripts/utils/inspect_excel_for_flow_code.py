#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 파일의 시트/컬럼을 확인하여 Flow Code 적용 가능 여부를 점검하는 읽기 전용 스크립트.

사용 예:
  python scripts/utils/inspect_excel_for_flow_code.py "docs/HVDC STATUS1.xlsx"
  python scripts/utils/inspect_excel_for_flow_code.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --header-row 0
"""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import get_warehouse_columns, get_site_columns
from core.header_registry import HVDC_HEADER_REGISTRY
from scripts.utils.apply_flow_code_to_sheet import (
    apply_flow_code_to_dataframe,
    derive_status_location,
)


def _normalize(s: str) -> str:
    return str(s).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def find_primary_alias_for_columns(
    excel_columns: list,
    semantic_keys: list,
) -> dict[str, str]:
    """Excel 컬럼명 -> 레지스트리 primary alias 매핑 (alias 매칭)."""
    result = {}
    for key in semantic_keys:
        try:
            definition = HVDC_HEADER_REGISTRY.get_definition(key)
        except KeyError:
            continue
        primary = definition.aliases[0] if definition.aliases else None
        if not primary:
            continue
        primary_norm = _normalize(primary)
        for col in excel_columns:
            if col in result:
                continue
            if _normalize(col) == primary_norm:
                result[col] = primary
                break
            for alias in definition.aliases[1:]:
                if _normalize(alias) == _normalize(col):
                    result[col] = primary
                    break
    return result


def find_sheet_by_name(wb_sheet_names: list, target: str) -> str | None:
    """대소문자/공백 무시하고 시트명 매칭."""
    target_norm = _normalize(target)
    for name in wb_sheet_names:
        if _normalize(name) == target_norm:
            return name
    return None


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Inspect Excel file for Flow Code: list sheets and columns, check required columns."
    )
    parser.add_argument("excel_path", type=Path, help="Path to Excel file")
    parser.add_argument(
        "sheet_name",
        nargs="?",
        default="hvdc all status",
        help="Sheet name to inspect (default: hvdc all status)",
    )
    parser.add_argument(
        "--header-row",
        type=int,
        default=0,
        help="Row index for column headers (default: 0)",
    )
    args = parser.parse_args()

    path = args.excel_path.resolve()
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    with pd.ExcelFile(path, engine="openpyxl") as xl:
        sheet_names = xl.sheet_names

    print(f"File: {path.name}")
    print(f"Sheets ({len(sheet_names)}): {sheet_names}")

    target_sheet = find_sheet_by_name(sheet_names, args.sheet_name)
    if target_sheet is None:
        print(f"\n[ERROR] Sheet not found: '{args.sheet_name}'")
        print("  Available:", sheet_names)
        sys.exit(1)

    df = pd.read_excel(path, sheet_name=target_sheet, header=args.header_row, engine="openpyxl")
    excel_cols = df.columns.tolist()
    print(f"\nSheet: '{target_sheet}' (header row={args.header_row})")
    print(f"Columns ({len(excel_cols)}): {excel_cols}")

    warehouse_columns = get_warehouse_columns()
    site_columns = get_site_columns()
    warehouse_keys = get_warehouse_columns(use_primary_alias=False)
    site_keys = get_site_columns(use_primary_alias=False)

    excel_to_primary = find_primary_alias_for_columns(excel_cols, warehouse_keys + site_keys)

    status_ok = "Status_Location" in df.columns or any(
        _normalize(c) == _normalize("Status_Location") for c in df.columns
    )
    status_col = "Status_Location" if "Status_Location" in df.columns else None
    if not status_col:
        for c in df.columns:
            if _normalize(c) == _normalize("Status_Location"):
                status_col = c
                break

    print("\n--- Required for Flow Code ---")
    print(f"  Status_Location: {'OK' if status_ok else 'MISSING'}" + (f" (column: {status_col!r})" if status_col else ""))

    print("  Warehouse columns (primary alias):")
    for wh in warehouse_columns:
        from_excel = [c for c, p in excel_to_primary.items() if p == wh]
        if from_excel:
            print(f"    {wh}: OK (Excel: {from_excel[0]!r})")
        else:
            print(f"    {wh}: {'OK' if wh in df.columns else 'MISSING'}")

    print("  Site columns (primary alias):")
    for site in site_columns:
        from_excel = [c for c, p in excel_to_primary.items() if p == site]
        if from_excel:
            print(f"    {site}: OK (Excel: {from_excel[0]!r})")
        else:
            print(f"    {site}: {'OK' if site in df.columns else 'MISSING'}")

    missing_primary = [c for c in warehouse_columns + site_columns if c not in df.columns and c not in excel_to_primary.values()]
    if excel_to_primary:
        print(f"\n  Alias mapping: {len(excel_to_primary)} Excel column(s) matched to primary alias.")
    if missing_primary:
        print(f"  Missing (no alias match): {missing_primary}")

    # --- Flow Code (this run): df_work, Status_Location 파생, FLOW_CODE 분포 ---
    print("\n--- Flow Code (this run) ---")
    df_work = df.rename(columns=excel_to_primary) if excel_to_primary else df.copy()
    status_derived = False
    if "Status_Location" not in df_work.columns:
        df_work = derive_status_location(df_work, warehouse_columns, site_columns)
        status_derived = True
        print("  Status_Location: MISSING (derived in this run from WH/Site dates)")
    else:
        print("  Status_Location: OK (used as-is)")

    df_with_flow = apply_flow_code_to_dataframe(df_work, warehouse_columns, site_columns)
    dist = df_with_flow["FLOW_CODE"].value_counts().sort_index()
    print(f"  FLOW_CODE distribution: {dict(dist)}")


if __name__ == "__main__":
    main()
