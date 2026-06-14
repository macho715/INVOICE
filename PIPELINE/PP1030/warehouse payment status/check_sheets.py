import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 200)

# 1. wh payment Category=Outdoor 확인
print("=" * 80)
print("1. wh payment - Outdoor 항목 상세")
print("=" * 80)

xl_pay = pd.ExcelFile('wh payment.xlsx')
df_pay = pd.read_excel(xl_pay, sheet_name=1)

lease = df_pay[df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)]
non_lease = df_pay[~df_pay.index.isin(lease.index)]

outdoor = non_lease[non_lease['Category'] == 'Outdoor']
print(f"Outdoor 항목: {len(outdoor)}건")

print(f"\nOutdoor CODE 3 분포:")
print(outdoor['HVDC CODE 3'].value_counts())

print(f"\nOutdoor CODE 1 분포:")
print(outdoor['HVDC CODE 1'].value_counts())

# DSV MZP in outdoor?
mzp_in_outdoor = outdoor[outdoor['HVDC CODE 3'].astype(str).str.contains('MZP', case=False, na=False)]
print(f"\nOutdoor 중 MZP 포함: {len(mzp_in_outdoor)}건")

# Mina Zayed category separately
mina = non_lease[non_lease['Category'] == 'Mina Zayed']
print(f"\nMina Zayed Category: {len(mina)}건")
print(f"  CODE 3: {dict(mina['HVDC CODE 3'].value_counts())}")

# 결론: Outdoor = DSV Outdoor 확정 (MZP 제외, MZP는 Mina Zayed Category)
print(f"\n=> Outdoor {len(outdoor)}건 = 전부 DSV Outdoor 해당")
print(f"=> Mina Zayed {len(mina)}건 = DSV MZP 해당")

# 2. HVDC_입고로직.xlsx 시트 확인
print()
print("=" * 80)
print("2. HVDC_입고로직.xlsx - 전체 시트 목록")
print("=" * 80)

xl_logic = pd.ExcelFile('HVDC_입고로직.xlsx')
for i, name in enumerate(xl_logic.sheet_names):
    df_temp = pd.read_excel(xl_logic, sheet_name=i)
    print(f"  {i}: {name} ({df_temp.shape[0]}rows x {df_temp.shape[1]}cols)")

# 3. 창고_월별_입출고 시트 (index 1 or search by name)
print()
print("=" * 80)
print("3. 창고_월별_입출고 시트 상세")
print("=" * 80)

# Find the sheet
target_sheet = None
for i, name in enumerate(xl_logic.sheet_names):
    if '입출고' in name or '월별' in name:
        print(f"  Found: {i}: {name}")
        target_sheet = i

if target_sheet is not None:
    df_monthly = pd.read_excel(xl_logic, sheet_name=target_sheet)
    print(f"\nShape: {df_monthly.shape}")
    print(f"컬럼: {df_monthly.columns.tolist()}")
    print()
    print("전체 데이터:")
    print(df_monthly.to_string())
else:
    # Try sheet index 1 and 2
    for idx in [1, 2]:
        df_try = pd.read_excel(xl_logic, sheet_name=idx)
        print(f"\nSheet {idx} ({xl_logic.sheet_names[idx]}):")
        print(f"  Shape: {df_try.shape}")
        print(f"  컬럼: {df_try.columns.tolist()}")
        print()
        print(df_try.to_string())
        print()

# 4. 입고현황_종합 시트도 확인
print()
print("=" * 80)
print("4. 입고현황_종합 시트")
print("=" * 80)

for i, name in enumerate(xl_logic.sheet_names):
    if '입고현황' in name or '종합' in name:
        df_s = pd.read_excel(xl_logic, sheet_name=i)
        print(f"\nSheet {i}: {name}")
        print(f"Shape: {df_s.shape}")
        print(f"컬럼: {df_s.columns.tolist()}")
        print()
        print(df_s.to_string())
        print()

# 5. SQM_창고현황 시트
print()
print("=" * 80)
print("5. SQM_창고현황 시트")
print("=" * 80)

for i, name in enumerate(xl_logic.sheet_names):
    if 'SQM' in name and '창고' in name:
        df_s = pd.read_excel(xl_logic, sheet_name=i)
        print(f"\nSheet {i}: {name}")
        print(f"Shape: {df_s.shape}")
        print(f"컬럼: {df_s.columns.tolist()}")
        print()
        print(df_s.head(30).to_string())
        print("...")
        print(df_s.tail(10).to_string())
        print()
