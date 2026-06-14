import sys

sys.path.insert(0, "scripts")
import pandas as pd
from pathlib import Path
from core.flow_ledger_v2 import build_flow_ledger, monthly_inout_table, sanity_report, trace_case

# Load latest report
latest = max(Path("data/processed/reports").glob("HVDC_*.xlsx"), key=lambda p: p.stat().st_mtime)
df = pd.read_excel(latest, sheet_name="창고_월별_입출고")
df = df[[c for c in df.columns if not c.startswith("Unnamed")]]

print("=" * 70)
print("COMPREHENSIVE SANITY CHECK")
print("=" * 70)

for wh in sorted({c.split("_", 1)[1] for c in df.columns if c.startswith("입고_")}):
    tin = df[f"입고_{wh}"].sum()
    tout = df[f"출고_{wh}"].sum()
    cum = df[f"누적_{wh}"].iloc[-2] if len(df) >= 2 else df[f"누적_{wh}"].iloc[-1]
    expected = tin - tout
    match = "OK" if expected == cum else "FAIL"
    ratio = f"{(cum / expected * 100):.1f}%" if expected != 0 else "N/A"

    print(f"{wh:20s} IN={tin:5d} OUT={tout:5d} CUM={cum:5d} EXP={expected:5d} [{match}] {ratio}")

print("\nSanity Report (mismatches only):")
bad = sanity_report(df)
if bad:
    for wh, tin, tout, last, exp in bad:
        print(f"  {wh}: IN={tin}, OUT={tout}, Balance={last}, Expected={exp}")
else:
    print("  All warehouses balanced!")

