import pandas as pd
import numpy as np

# Load Master and Synced files
master_file = 'data/raw/Case List.xlsx'
synced_file = 'data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v2.9.4.xlsx'

print("Loading files...")
master_xl = pd.ExcelFile(master_file)
print(f"Master file sheets: {master_xl.sheet_names}")

# Load all sheets from Master
master_dfs = []
for sheet in master_xl.sheet_names:
    df = pd.read_excel(master_xl, sheet_name=sheet)
    print(f"  Master '{sheet}': {len(df)} rows")
    master_dfs.append(df)

master = pd.concat(master_dfs, ignore_index=True)
print(f"Total Master rows: {len(master)}")

synced = pd.read_excel(synced_file)
print(f"Total Synced rows: {len(synced)}")

# Find Case No. column
case_col_master = None
case_col_synced = None

for col in master.columns:
    if 'case' in str(col).lower() and 'no' in str(col).lower():
        case_col_master = col
        break

for col in synced.columns:
    if 'case' in str(col).lower() and 'no' in str(col).lower():
        case_col_synced = col
        break

print(f"\nMaster Case column: '{case_col_master}'")
print(f"Synced Case column: '{case_col_synced}'")

# Compare specific cases
print("\n=== CHECKING UPDATED RECORDS ===")
print("Looking for records that should have been updated...")

# Get date columns (ETD/ATD, ETA/ATA, etc.)
date_cols_master = [col for col in master.columns if any(x in str(col) for x in ['ETD', 'ETA', 'ATD', 'ATA', 'DSV', 'DHL', 'Hauler', 'MIR', 'SHU', 'AGI', 'DAS'])]
date_cols_synced = [col for col in synced.columns if any(x in str(col) for x in ['ETD', 'ETA', 'ATD', 'ATA', 'DSV', 'DHL', 'Hauler', 'MIR', 'SHU', 'AGI', 'DAS'])]

print(f"\nMaster date columns: {len(date_cols_master)}")
print(f"Synced date columns: {len(date_cols_synced)}")

# Sample check: Compare first 10 cases
print("\n=== SAMPLE COMPARISON (First 10 cases) ===")
for i in range(min(10, len(master))):
    master_case = master.iloc[i][case_col_master]
    
    # Find same case in synced
    synced_row = synced[synced[case_col_synced] == master_case]
    
    if len(synced_row) > 0:
        synced_row = synced_row.iloc[0]
        
        # Compare ETD/ATD
        if 'ETD/ATD' in master.columns and 'ETD/ATD' in synced.columns:
            master_val = master.iloc[i]['ETD/ATD']
            synced_val = synced_row['ETD/ATD']
            
            match = "✓" if pd.isna(master_val) and pd.isna(synced_val) else ("✓" if master_val == synced_val else "✗")
            print(f"Case {master_case}: ETD/ATD {match}")
            if match == "✗":
                print(f"  Master: {master_val}")
                print(f"  Synced: {synced_val}")
    else:
        print(f"Case {master_case}: NOT FOUND in synced ✗")

# Check for new records (appends)
print("\n=== NEW RECORDS CHECK ===")
master_cases = set(master[case_col_master].dropna().unique())
synced_cases = set(synced[case_col_synced].dropna().unique())

new_in_synced = synced_cases - master_cases
print(f"New records in synced (not in master): {len(new_in_synced)}")
if len(new_in_synced) > 0:
    print(f"Sample new cases: {list(new_in_synced)[:10]}")

missing_in_synced = master_cases - synced_cases
print(f"Missing records in synced (should be there): {len(missing_in_synced)}")
if len(missing_in_synced) > 0:
    print(f"Sample missing cases: {list(missing_in_synced)[:10]}")

# Check for updates (246 updates reported)
print("\n=== UPDATE VERIFICATION ===")
updates_count = 0
date_updates_count = 0
field_updates_count = 0

# Check common columns
common_cols = [col for col in master.columns if col in synced.columns]
print(f"Common columns to check: {len(common_cols)}")

# Sample detailed check for first 100 records
for i in range(min(100, len(master))):
    master_case = master.iloc[i][case_col_master]
    synced_row = synced[synced[case_col_synced] == master_case]
    
    if len(synced_row) > 0:
        synced_row = synced_row.iloc[0]
        
        for col in common_cols:
            if col == case_col_master or col == case_col_synced:
                continue
                
            master_val = master.iloc[i][col]
            synced_val = synced_row[col]
            
            # Check if different
            if pd.isna(master_val) and pd.isna(synced_val):
                continue
            elif pd.isna(master_val) or pd.isna(synced_val):
                updates_count += 1
                if 'date' in str(col).lower() or any(x in str(col) for x in ['ETD', 'ETA', 'ATD', 'ATA', 'DSV', 'DHL']):
                    date_updates_count += 1
                else:
                    field_updates_count += 1
            elif str(master_val) != str(synced_val):
                updates_count += 1
                if 'date' in str(col).lower() or any(x in str(col) for x in ['ETD', 'ETA', 'ATD', 'ATA', 'DSV', 'DHL']):
                    date_updates_count += 1
                else:
                    field_updates_count += 1

print(f"\nUpdates found in first 100 records:")
print(f"  Total updates: {updates_count}")
print(f"  Date updates: {date_updates_count}")
print(f"  Field updates: {field_updates_count}")

print("\n=== SUMMARY ===")
print(f"✓ Total Master rows: {len(master)}")
print(f"✓ Total Synced rows: {len(synced)}")
print(f"✓ Row count match: {len(master) == len(synced)}")
print(f"✓ All Master cases in Synced: {len(missing_in_synced) == 0}")
print(f"✓ New records in Synced: {len(new_in_synced)}")

