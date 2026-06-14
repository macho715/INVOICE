import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_colwidth', 20)

xl = pd.ExcelFile('HVDC_입고로직.xlsx')

# Sheet 1: 창고_월별_입출고 - raw (no header)
print("=" * 120)
print("Sheet 1: 창고_월별_입출고 (header=None)")
print("=" * 120)
df1 = pd.read_excel(xl, sheet_name=1, header=None)
print(f"Shape: {df1.shape}")
print()
for r in range(min(5, len(df1))):
    print(f"Row {r}: {df1.iloc[r].tolist()}")
print("...")
for r in range(5, len(df1)):
    vals = df1.iloc[r].tolist()
    vals_str = [str(v)[:15] for v in vals]
    print(f"Row {r}: {vals_str}")

# Also check what the Outdoor mapping looks like
print()
print("=" * 120)
print("wh payment Outdoor - DSV MZP 식별")
print("=" * 120)

df_pay = pd.read_excel('wh payment.xlsx', sheet_name=1)
lease = df_pay[df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)]
non_lease = df_pay[~df_pay.index.isin(lease.index)]

outdoor = non_lease[non_lease['Category'] == 'Outdoor']

# CODE 1 = "DSV MZP" 인 항목
mzp_code1 = outdoor[outdoor['HVDC CODE 1'].astype(str).str.contains('MZP', case=False, na=False)]
print(f"Outdoor 중 CODE 1에 MZP: {len(mzp_code1)}건")
if len(mzp_code1) > 0:
    print(mzp_code1[['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category', 'Amount', 'TOTAL']].head(10))

# CODE 2에 MZP?
mzp_code2 = outdoor[outdoor['HVDC CODE 2'].astype(str).str.contains('MZP', case=False, na=False)]
print(f"\nOutdoor 중 CODE 2에 MZP: {len(mzp_code2)}건")

# CODE 3에 MZP?
mzp_code3 = outdoor[outdoor['HVDC CODE 3'].astype(str).str.contains('MZP', case=False, na=False)]
print(f"Outdoor 중 CODE 3에 MZP: {len(mzp_code3)}건")

# CODE 4에 MZP?
mzp_code4 = outdoor[outdoor['HVDC CODE 4'].astype(str).str.contains('MZP', case=False, na=False)]
print(f"Outdoor 중 CODE 4에 MZP: {len(mzp_code4)}건")

outdoor_no_mzp = outdoor[~outdoor.index.isin(mzp_code1.index)]
print(f"\nOutdoor - MZP 제외: {len(outdoor_no_mzp)}건 = DSV Outdoor 확정")

# 전체 Non-Lease Category 분포
print()
print("Non-Lease Category 전체 분포:")
print(non_lease['Category'].value_counts())
print(f"Total: {len(non_lease)}")
