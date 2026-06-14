import pandas as pd
import os

# Check synced file
synced_file = 'data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v2.9.4.xlsx'
print(f"Checking: {synced_file}")
print(f"File exists: {os.path.exists(synced_file)}")

if os.path.exists(synced_file):
    df = pd.read_excel(synced_file)
    print(f"\n=== SYNCED FILE INFO ===")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Check for Case No. column
    case_col = None
    for col in df.columns:
        if 'case' in str(col).lower() and 'no' in str(col).lower():
            case_col = col
            break
    
    if case_col:
        print(f"\nCase column: '{case_col}'")
        print(f"First 10 Case No.:")
        for i, case in enumerate(df[case_col].head(10).tolist(), 1):
            print(f"  {i}. {case}")
        
        print(f"\nLast 10 Case No.:")
        for i, case in enumerate(df[case_col].tail(10).tolist(), 1):
            print(f"  {len(df)-10+i}. {case}")
    
    # Check warehouse columns
    warehouse_cols = [col for col in df.columns if any(w in str(col) for w in ['DHL', 'DSV', 'Hauler', 'JDN', 'AAA', 'MOSB'])]
    print(f"\n=== WAREHOUSE COLUMNS ({len(warehouse_cols)}) ===")
    for col in warehouse_cols:
        non_null = df[col].notna().sum()
        print(f"  - {col}: {non_null} 건")
    
    # Check for specific columns
    print(f"\n=== KEY COLUMNS CHECK ===")
    key_cols = ['No', 'Case No.', 'HVDC CODE', 'ETD/ATD', 'ETA/ATA']
    for col in key_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            print(f"  ✓ {col}: {non_null}/{len(df)}")
        else:
            print(f"  ✗ {col}: NOT FOUND")

# Compare with raw data
raw_file = 'data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx'
print(f"\n\n=== COMPARING WITH RAW DATA ===")
print(f"Checking: {raw_file}")
print(f"File exists: {os.path.exists(raw_file)}")

if os.path.exists(raw_file):
    xl = pd.ExcelFile(raw_file)
    print(f"Number of sheets: {len(xl.sheet_names)}")
    
    total_raw_rows = 0
    for sheet in xl.sheet_names:
        df_sheet = pd.read_excel(xl, sheet_name=sheet)
        print(f"  - Sheet '{sheet}': {len(df_sheet)} rows")
        total_raw_rows += len(df_sheet)
    
    print(f"\nTotal raw rows: {total_raw_rows}")
    if os.path.exists(synced_file):
        synced_df = pd.read_excel(synced_file)
        print(f"Total synced rows: {len(synced_df)}")
        print(f"Difference: {len(synced_df) - total_raw_rows} rows")

