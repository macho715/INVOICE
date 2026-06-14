import pandas as pd
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from stage3_report.report_generator import HVDCExcelReporterFinal

# Initialize reporter
reporter = HVDCExcelReporterFinal()

# Get stats
stats = reporter.calculate_warehouse_statistics()
master_df = stats.get("processed_data")

print("Master DF shape:", master_df.shape)
print("\nFirst 20 columns:")
for i, col in enumerate(master_df.columns[:20]):
    print(f"  {i+1}. {col}")

print("\nLocation-related columns:")
loc_cols = [
    c
    for c in master_df.columns
    if "location" in c.lower() or "warehouse" in c.lower() or "site" in c.lower()
]
for col in loc_cols:
    print(f"  - {col}")

print("\nDate columns:")
date_cols = [c for c in master_df.columns if master_df[c].dtype == "datetime64[ns]"]
for col in date_cols[:10]:
    print(f"  - {col} (dtype: {master_df[col].dtype})")

print("\nSample row with Status_Location:")
if "Status_Location" in master_df.columns:
    sample = (
        master_df[["Status_Location", "Final_Location"]].iloc[0]
        if "Final_Location" in master_df.columns
        else master_df[["Status_Location"]].iloc[0]
    )
    print(sample)
