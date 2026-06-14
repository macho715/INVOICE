import sys

sys.path.insert(0, "scripts")
import pandas as pd
from core.flow_ledger_v2 import sanity_report

# Load the generated report
df = pd.read_excel(
    "data/processed/reports/HVDC_입고로직_종합리포트_20251025_172644_v3.0-corrected.xlsx",
    sheet_name="창고_월별_입출고",
)

# Remove unnamed columns
df = df[[c for c in df.columns if not c.startswith("Unnamed")]]

# Run sanity check
bad = sanity_report(df)
if not bad:
    print("✅ Sanity Check PASSED - All warehouses balanced")
else:
    print(f"❌ Sanity Check FAILED: {len(bad)} mismatches")
    for wh, tin, tout, last, exp in bad[:5]:
        print(f"  {wh}: IN={tin}, OUT={tout}, Balance={last}, Expected={exp}")

print(f"\nTotal months: {len(df)}")
print(f"Total columns: {len(df.columns)}")

# Check DSV Indoor specifically
if "입고_DSV Indoor" in df.columns:
    total_in = df["입고_DSV Indoor"].sum()
    total_out = df["출고_DSV Indoor"].sum()
    final_cum = df["누적_DSV Indoor"].iloc[-1]
    print(f"\nDSV Indoor Summary:")
    print(f"  Total 입고: {total_in}")
    print(f"  Total 출고: {total_out}")
    print(f"  Final 누적: {final_cum}")
    print(
        f"  Balance check: {total_in - total_out} == {final_cum} ? {total_in - total_out == final_cum}"
    )

# Check for "입고=0, 누적만 증가" anomaly
print('\n검증: "입고=0, 누적만 증가" 패턴 확인')
for w in sorted({c.split("_", 1)[1] for c in df.columns if c.startswith("입고_")}):
    zero_in = (df[f"입고_{w}"] == 0) & (df[f"출고_{w}"] == 0)
    prev_cum = df[f"누적_{w}"].shift(1, fill_value=0)
    cum_increased = df[f"누적_{w}"] > prev_cum
    anomaly_rows = zero_in & cum_increased

    if anomaly_rows.sum() > 0:
        print(f'  ❌ {w}: {anomaly_rows.sum()}개 월에서 "입고=0, 출고=0, 누적만 증가" 발견')
        for idx in df[anomaly_rows].index[:3]:
            row = df.loc[idx]
            print(
                f'      월: {row["입고월"]}, 입고={row[f"입고_{w}"]}, 출고={row[f"출고_{w}"]}, 누적={row[f"누적_{w}"]}'
            )
    else:
        print(f'  ✅ {w}: "입고=0, 누적만 증가" 없음')

