import pandas as pd
import numpy as np
from datetime import datetime
import re

# Target format columns
target_columns = [
    'S No.', 'Operation Month', 'HVDC CODE', 'HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4',
    'Category', '20DC', '20FR', '40DC', '40FR', 'CNTR No.', "CNTR Unstuffing Q'TY", "CNTR Stuffing Q'TY",
    'Start', 'Finish', 'pkg', 'Weight (kg)', 'CBM', 'Handling In freight ton', 'Handling out Freight Ton',
    'Sqm', 'Amount', 'Handling In', 'Handling out', 'Unstuffing', 'Stuffing', 'folk lift', 'crane', 'TOTAL', 'Billing month'
]

def extract_month_from_sheet_name(sheet_name):
    """Extract year-month from sheet name like 'JAN2025', 'MAR2025', 'Feb2025 (HE-SIM)'"""
    month_map = {
        'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUNE': '06',
        'JULY': '07', 'AUG': '08', 'SEP': '09', 'Oct': '10', 'Nov': '11', 'DEC': '12'
    }

    sheet_upper = sheet_name.upper()

    # Check for 4-digit year pattern
    year_match = re.search(r'(20\d{2})', sheet_name)
    year = year_match.group(1) if year_match else None

    # Check for month
    month = None
    for m_name, m_num in month_map.items():
        if m_name in sheet_upper:
            month = m_num
            break

    if year and month:
        return f'{year}-{month}'
    elif month:
        # Default to 2024 if no year specified in older sheets
        return f'2024-{month}'
    return None

def parse_hvdc_code(shipment_no):
    """Parse HVDC CODE parts from Shipment No like 'HVDC-ADOPT-HE-0001'"""
    if pd.isna(shipment_no):
        return [None, None, None, None, None]

    code_str = str(shipment_no).strip()
    parts = code_str.split('-')

    # HVDC CODE = full code
    # HVDC CODE 1-4 = parts
    hvdc_code = code_str
    hvdc_1 = parts[0] if len(parts) > 0 else None
    hvdc_2 = parts[1] if len(parts) > 1 else None
    hvdc_3 = parts[2] if len(parts) > 2 else None
    hvdc_4 = parts[3] if len(parts) > 3 else None

    return [hvdc_code, hvdc_1, hvdc_2, hvdc_3, hvdc_4]

def to_num(val):
    """Convert value to numeric, return 0 if invalid"""
    if pd.isna(val):
        return 0
    try:
        return float(val)
    except:
        return 0

def process_monthly_sheet(xl, sheet_name):
    """Process a monthly invoice sheet and return dataframe in target format"""
    print(f'Processing: {sheet_name}')

    # Read without header
    df = pd.read_excel(xl, sheet_name=sheet_name, header=None)

    if len(df) < 13:
        print(f'  Skipping {sheet_name}: insufficient rows ({len(df)})')
        return None

    # Extract billing month from sheet name
    billing_month = extract_month_from_sheet_name(sheet_name)

    # Find the actual data rows (skip header rows)
    # Data typically starts around row 12-13 (0-indexed: 12+)
    data_start_row = None
    for i in range(10, min(20, len(df))):
        row_val = df.iloc[i, 1]  # Check SR column
        if pd.notna(row_val) and str(row_val).strip().isdigit():
            data_start_row = i
            break

    if data_start_row is None:
        print(f'  Warning: Could not find data start row for {sheet_name}')
        data_start_row = 12  # Default

    # Extract data rows
    data_rows = []
    for i in range(data_start_row, len(df)):
        row = df.iloc[i]

        # Check if this is a data row (has SR number)
        sr_val = row[1] if len(row) > 1 else None
        if pd.isna(sr_val) or str(sr_val).strip() == '':
            # Check if it's a totals/subtotal row
            first_col = row[0] if len(row) > 0 else None
            if pd.notna(first_col) and 'TOTAL' in str(first_col).upper():
                break  # Stop at total row
            continue

        # Parse HVDC codes
        shipment_no = row[2] if len(row) > 2 else None
        hvdc_codes = parse_hvdc_code(shipment_no)

        # Extract container quantities
        cntr_20dv = row[3] if len(row) > 3 else 0
        cntr_20fr = row[4] if len(row) > 4 else 0
        cntr_40dv = row[5] if len(row) > 5 else 0
        cntr_40fr = row[6] if len(row) > 6 else 0

        new_row = {
            'S No.': sr_val,
            'Operation Month': billing_month,
            'HVDC CODE': hvdc_codes[0],
            'HVDC CODE 1': hvdc_codes[1],
            'HVDC CODE 2': hvdc_codes[2],
            'HVDC CODE 3': hvdc_codes[3],
            'HVDC CODE 4': hvdc_codes[4],
            'Category': row[19] if len(row) > 19 else None,
            '20DC': to_num(cntr_20dv),
            '20FR': to_num(cntr_20fr),
            '40DC': to_num(cntr_40dv),
            '40FR': to_num(cntr_40fr),
            'CNTR No.': row[7] if len(row) > 7 else None,
            "CNTR Unstuffing Q'TY": to_num(row[8]) if len(row) > 8 else 0,
            "CNTR Stuffing Q'TY": to_num(row[9]) if len(row) > 9 else 0,
            'Start': row[10] if len(row) > 10 else None,
            'Finish': row[11] if len(row) > 11 else None,
            'pkg': to_num(row[12]) if len(row) > 12 else 0,
            'Weight (kg)': to_num(row[13]) if len(row) > 13 else 0,
            'CBM': to_num(row[14]) if len(row) > 14 else 0,
            'Handling In freight ton': to_num(row[15]) if len(row) > 15 else 0,
            'Handling out Freight Ton': to_num(row[16]) if len(row) > 16 else 0,
            'Sqm': to_num(row[20]) if len(row) > 20 else 0,
            'Amount': to_num(row[21]) if len(row) > 21 else 0,
            'Handling In': to_num(row[23]) if len(row) > 23 else 0,
            'Handling out': to_num(row[25]) if len(row) > 25 else 0,
            'Unstuffing': to_num(row[27]) if len(row) > 27 else 0,
            'Stuffing': to_num(row[29]) if len(row) > 29 else 0,
            'folk lift': to_num(row[31]) if len(row) > 31 else 0,
            'crane': to_num(row[30]) if len(row) > 30 else 0,
            'TOTAL': to_num(row[32]) if len(row) > 32 else 0,
            'Billing month': billing_month,
        }

        data_rows.append(new_row)

    if not data_rows:
        print(f'  No data rows found in {sheet_name}')
        return None

    result_df = pd.DataFrame(data_rows, columns=target_columns)
    print(f'  Extracted {len(result_df)} rows')
    return result_df

def main():
    input_file = 'warehouse.xlsx'
    output_file = 'warehouse_merged.xlsx'

    xl = pd.ExcelFile(input_file)

    # Monthly sheets to process (exclude Shifting Item)
    monthly_sheets = [s for s in xl.sheet_names if s != 'Shifting Item']

    print(f'Found {len(monthly_sheets)} sheets to process')
    print(f'Sheets: {monthly_sheets}')
    print()

    all_data = []
    for sheet in monthly_sheets:
        df = process_monthly_sheet(xl, sheet)
        if df is not None and len(df) > 0:
            all_data.append(df)

    if not all_data:
        print('No data extracted!')
        return

    # Combine all data
    merged_df = pd.concat(all_data, ignore_index=True)

    # Re-number S No. sequentially
    merged_df['S No.'] = range(1, len(merged_df) + 1)

    print(f'\nTotal merged rows: {len(merged_df)}')
    print(f'Output columns: {len(merged_df.columns)}')

    # Write to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        merged_df.to_excel(writer, sheet_name='Merged Data', index=False)

    print(f'\nOutput saved to: {output_file}')

    # Show sample
    print('\n=== Sample Output (first 5 rows) ===')
    print(merged_df.head().to_string())

if __name__ == '__main__':
    main()
