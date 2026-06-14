import pandas as pd

xl = pd.ExcelFile('HVDC_입고로직.xlsx')

# Check all sheets
print('=== HVDC_입고로직.xlsx Summary ===')
print(f'Total sheets: {len(xl.sheet_names)}')
for i, name in enumerate(xl.sheet_names):
    print(f'  {i}: {name}')
print()

# Check 통합 sheet
print('=== Sheet 11 (통합) ===')
df_all = pd.read_excel(xl, sheet_name=11)
print(f'Shape: {df_all.shape}')
print()

# Vendor distribution
print('Source_Vendor distribution:')
print(df_all['Source_Vendor'].value_counts())
print()

# SQM info
sqm_nonnull = df_all['SQM'].notna().sum()
sqm_total = df_all['SQM'].sum()
print(f'SQM non-null: {sqm_nonnull} / {len(df_all)}')
print(f'Total SQM: {sqm_total:.2f}')
print()

# Sample SCT Ref.No
print('Sample SCT Ref.No (HVDC CODE) - Top 10:')
print(df_all['SCT Ref.No'].value_counts().head(10))
print()

# Check sheet 8 (창고_바운스_정산)
print('=== Sheet 8 (창고 바운스 정산) ===')
df_wh = pd.read_excel(xl, sheet_name=8)
print(f'Shape: {df_wh.shape}')
print('Columns:', df_wh.columns.tolist())
print()
print('First 5 rows:')
print(df_wh.head().to_string())
