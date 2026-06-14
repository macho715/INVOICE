# -*- coding: utf-8 -*-
"""
SIEMENS Warehouse Data Verification Script

This script verifies that SIEMENS warehouse data is properly loaded and
integrated in the synced file.

Usage:
    python scripts/utils/verify_siemens_warehouse.py [synced_file_path]

If no path is provided, uses the default unified synced file path.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_default_synced_path() -> Path:
    """Get the default unified synced file path"""
    return project_root / "data" / "processed" / "synced" / "HVDC WAREHOUSE_UNIFIED.synced_v3.4.xlsx"


def analyze_warehouse_columns(df: pd.DataFrame, vendor: str) -> Dict[str, any]:
    """
    Analyze warehouse columns for a specific vendor.

    Returns:
        Dict with column names and their null percentages
    """
    # Define warehouse columns to check
    warehouse_cols = [
        "DHL Warehouse", "DSV Indoor", "DSV Al Markaz", "Hauler Indoor",
        "DSV Outdoor", "DSV MZP", "HAULER", "JDN MZD", "MOSB", "AAA Storage"
    ]

    results = {
        "total_rows": len(df),
        "columns": {}
    }

    for col in warehouse_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
            non_null_count = len(df) - null_count
            results["columns"][col] = {
                "null_count": int(null_count),
                "null_pct": round(null_pct, 2),
                "non_null_count": int(non_null_count)
            }
        else:
            results["columns"][col] = {
                "null_count": None,
                "null_pct": 100.0,
                "non_null_count": 0,
                "note": "Column not found"
            }

    return results


def verify_siemens_warehouse_data(synced_file_path: Path) -> Tuple[bool, Dict]:
    """
    Verify SIEMENS warehouse data in synced file.

    Returns:
        Tuple of (success: bool, details: dict)
    """
    print(f"\n{'='*60}")
    print("SIEMENS Warehouse Data Verification")
    print(f"{'='*60}")
    print(f"File: {synced_file_path}")

    if not synced_file_path.exists():
        return False, {"error": f"File not found: {synced_file_path}"}

    try:
        # Load the synced file
        xl = pd.ExcelFile(synced_file_path)
        print(f"Sheets found: {xl.sheet_names}")

        results = {
            "file": str(synced_file_path),
            "sheets": {}
        }

        overall_success = True

        for sheet_name in xl.sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            df = pd.read_excel(synced_file_path, sheet_name=sheet_name)

            if "Source_Vendor" not in df.columns:
                print(f"  [WARNING] Source_Vendor column not found")
                results["sheets"][sheet_name] = {"error": "Source_Vendor column missing"}
                continue

            # Split by vendor
            siemens_df = df[df["Source_Vendor"] == "SIEMENS"]
            hitachi_df = df[df["Source_Vendor"] == "HITACHI"]

            print(f"  Total rows: {len(df)}")
            print(f"  HITACHI rows: {len(hitachi_df)}")
            print(f"  SIEMENS rows: {len(siemens_df)}")

            if len(siemens_df) == 0:
                print(f"  [INFO] No SIEMENS data in this sheet")
                results["sheets"][sheet_name] = {
                    "siemens_rows": 0,
                    "message": "No SIEMENS data"
                }
                continue

            # Analyze warehouse columns
            siemens_analysis = analyze_warehouse_columns(siemens_df, "SIEMENS")
            hitachi_analysis = analyze_warehouse_columns(hitachi_df, "HITACHI")

            print(f"\n  SIEMENS Warehouse Columns:")
            siemens_has_data = False
            for col, stats in siemens_analysis["columns"].items():
                status = "✓" if stats.get("non_null_count", 0) > 0 else "✗"
                print(f"    {status} {col}: {stats.get('non_null_count', 0)} non-null ({stats.get('null_pct', 100)}% null)")
                if stats.get("non_null_count", 0) > 0:
                    siemens_has_data = True

            # Check if SIEMENS has any warehouse data
            if not siemens_has_data:
                print(f"  [WARNING] SIEMENS rows have no warehouse data (all columns null)")
                overall_success = False
            else:
                print(f"  [OK] SIEMENS has warehouse data")

            results["sheets"][sheet_name] = {
                "siemens_rows": len(siemens_df),
                "hitachi_rows": len(hitachi_df),
                "siemens_has_warehouse_data": siemens_has_data,
                "siemens_analysis": siemens_analysis,
                "hitachi_analysis": hitachi_analysis
            }

        return overall_success, results

    except Exception as e:
        return False, {"error": str(e)}


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        synced_file_path = Path(sys.argv[1])
    else:
        synced_file_path = get_default_synced_path()

    success, results = verify_siemens_warehouse_data(synced_file_path)

    print(f"\n{'='*60}")
    if success:
        print("VERIFICATION PASSED: SIEMENS warehouse data is present")
    else:
        print("VERIFICATION FAILED: SIEMENS warehouse data issues found")
    print(f"{'='*60}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
