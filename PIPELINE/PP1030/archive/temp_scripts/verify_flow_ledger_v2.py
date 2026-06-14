import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core.flow_ledger_v2 import sanity_report

# Load latest report
latest_report = sorted(Path("data/processed/reports").glob("HVDC_입고로직_종합리포트_*.xlsx"))[-1]
print(f"Checking report: {latest_report.name}\n")

# Load monthly sheet (assuming multi-level headers)
df = pd.read_excel(latest_report, sheet_name="창고_월별_입출고")

# Run sanity check
mismatches = sanity_report(df)

if not mismatches:
    print("✓ Sanity check PASSED: All warehouses balanced (∑IN - ∑OUT = Last Cumulative)")
else:
    print(f"✗ Sanity check FAILED: {len(mismatches)} warehouses")
    for wh, tin, tout, last, exp in mismatches:
        diff = last - exp
        print(f"  {wh}: ∑IN={tin}, ∑OUT={tout}, Last={last}, Expected={exp}, Diff={diff}")

# Check DSV Indoor specifically
dsv_cols = [c for c in df.columns if "누적" in str(c) and "DSV Indoor" in str(c)]
if dsv_cols:
    col = dsv_cols[0]
    # Exclude Total row
    data_rows = df[df.iloc[:, 0] != "Total"]
    last_cum = int(data_rows[col].iloc[-1]) if len(data_rows) > 0 else 0
    print(f"\nDSV Indoor 마지막 누적: {last_cum}")
    target = 789
    tolerance = int(target * 0.05)  # ±5%
    if abs(last_cum - target) <= tolerance:
        print(f"✓ 목표 달성: {target} ±{tolerance} (actual: {last_cum})")
    else:
        print(f"✗ 목표 미달성: expected ~{target}, got {last_cum}")
else:
    print("✗ DSV Indoor column not found")
