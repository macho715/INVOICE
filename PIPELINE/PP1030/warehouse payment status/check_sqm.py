import pandas as pd

# Check warehouse merged SQM column
df_wh = pd.read_excel('warehouse_merged.xlsx')

print('=== Warehouse Merged SQM Analysis ===')
print(f'Records: {len(df_wh)}')
print(f'Sqm non-null: {df_wh["Sqm"].notna().sum()}')
print(f'Sqm > 0: {(df_wh["Sqm"] > 0).sum()}')
sqm_total = df_wh["Sqm"].sum()
print(f'Sqm sum: {sqm_total:.2f}')
print()

# Check where Sqm is > 0
print('Rows with Sqm > 0 (sample):')
df_sqm_positive = df_wh[df_wh['Sqm'] > 0][['HVDC CODE', 'Billing month', 'Sqm', 'Amount', 'Category']].head(20)
print(df_sqm_positive.to_string())
print()

# Monthly SQM totals
print('Monthly Sqm totals:')
monthly_sqm = df_wh.groupby('Billing month')['Sqm'].sum()
for month, sqm in monthly_sqm.items():
    if sqm > 0:
        print(f'  {month}: {sqm:.2f}')

print()
print('=== Comparison with Item-Level Data ===')

# Compare with report data
xl = pd.ExcelFile('HVDC_입고로직_종합리포트_20260415_165850_v3.0-corrected.xlsx')
df_all = pd.read_excel(xl, sheet_name=11)
print(f'Report total SQM: {df_all["SQM"].sum():.2f}')
print(f'Warehouse total Sqm: {sqm_total:.2f}')
