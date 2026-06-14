import pandas as pd
from pathlib import Path

print("=" * 80)
print("=== HITACHI Raw Data Header Analysis ===")
print("=" * 80)

hitachi_file = Path("data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx")
print(f"\nFile: {hitachi_file}")
print(f"Exists: {hitachi_file.exists()}")

if hitachi_file.exists():
    xl = pd.ExcelFile(hitachi_file)
    print(f"\nSheets: {xl.sheet_names}")
    
    # Check main sheet with header row 4
    sheet_name = "Case List, RIL"
    print(f"\n--- Sheet: '{sheet_name}' (header=4) ---")
    df = pd.read_excel(hitachi_file, sheet_name=sheet_name, header=4, nrows=5)
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumn list:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:3d}. {col}")
    
    print(f"\nFirst 3 rows data:")
    print(df.head(3).to_string())

print("\n" + "=" * 80)
print("=== SIEMENS Raw Data Header Analysis ===")
print("=" * 80)

siemens_file = Path("data/raw/SIMENSE/Case List_Simense.xlsm")
print(f"\nFile: {siemens_file}")
print(f"Exists: {siemens_file.exists()}")

if siemens_file.exists():
    xl = pd.ExcelFile(siemens_file)
    print(f"\nSheets: {xl.sheet_names}")
    
    # Check main sheet with header row 0
    sheet_name = "Case List, RIL"
    print(f"\n--- Sheet: '{sheet_name}' (header=0) ---")
    df = pd.read_excel(siemens_file, sheet_name=sheet_name, header=0, nrows=5)
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumn list:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:3d}. {col}")
    
    print(f"\nFirst 3 rows data:")
    print(df.head(3).to_string())

print("\n" + "=" * 80)
print("=== Header Comparison ===")
print("=" * 80)

# Load both files
hitachi_df = pd.read_excel(hitachi_file, sheet_name="Case List, RIL", header=4, nrows=0)
siemens_df = pd.read_excel(siemens_file, sheet_name="Case List, RIL", header=0, nrows=0)

hitachi_cols = set(hitachi_df.columns)
siemens_cols = set(siemens_df.columns)

print(f"\nHITACHI unique columns ({len(hitachi_cols - siemens_cols)}):")
for col in sorted(hitachi_cols - siemens_cols):
    print(f"  - {col}")

print(f"\nSIEMENS unique columns ({len(siemens_cols - hitachi_cols)}):")
for col in sorted(siemens_cols - hitachi_cols):
    print(f"  - {col}")

print(f"\nCommon columns ({len(hitachi_cols & siemens_cols)}):")
for col in sorted(hitachi_cols & siemens_cols):
    print(f"  - {col}")

print("\n" + "=" * 80)


