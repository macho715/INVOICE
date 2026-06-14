import pandas as pd

xl = pd.ExcelFile('HVDC_입고로직_종합리포트_20260415_165850_v3.0-corrected.xlsx')

# Check HITACHI sheet
print('=== HITACHI Sheet Analysis ===')
df_hitachi = pd.read_excel(xl, sheet_name=9)
print(f'Records: {len(df_hitachi)}')
print(f'SQM non-null: {df_hitachi["SQM"].notna().sum()}')
print(f'SQM total: {df_hitachi["SQM"].sum():.2f}')
print()

print('SCT Ref.No (HVDC CODE) top 10:')
print(df_hitachi['SCT Ref.No'].value_counts().head(10))
print()

print('Status_Location_YearMonth top 10:')
print(df_hitachi['Status_Location_YearMonth'].value_counts().sort_index().head(10))
print()

# Check SIEMENS sheet
print('=== SIEMENS Sheet Analysis ===')
df_siemens = pd.read_excel(xl, sheet_name=10)
print(f'Records: {len(df_siemens)}')
print(f'SQM non-null: {df_siemens["SQM"].notna().sum()}')
print(f'SQM total: {df_siemens["SQM"].sum():.2f}')
print()

print('SCT Ref.No (HVDC CODE) top 10:')
print(df_siemens['SCT Ref.No'].value_counts().head(10))
print()

# Check combined sheet (sheet 11)
print('=== 통합 Sheet Analysis ===')
df_all = pd.read_excel(xl, sheet_name=11)
print(f'Records: {len(df_all)}')
print(f'SQM non-null: {df_all["SQM"].notna().sum()}')
print(f'SQM total: {df_all["SQM"].sum():.2f}')
print()

print('Source_Vendor distribution:')
print(df_all['Source_Vendor'].value_counts())
print()

print('SCT Ref.No (HVDC CODE) top 10:')
print(df_all['SCT Ref.No'].value_counts().head(10))
