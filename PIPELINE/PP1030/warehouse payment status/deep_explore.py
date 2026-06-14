import pandas as pd
import numpy as np
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 100)

print("=" * 80)
print("A. wh payment - 창고 종류별 비용 구조")
print("=" * 80)

xl_pay = pd.ExcelFile('wh payment.xlsx')
df_pay = pd.read_excel(xl_pay, sheet_name=1)

print(f"\n컬럼 목록: {df_pay.columns.tolist()}")
print()

# HVDC CODE 3 = vendor/warehouse location code
print("--- HVDC CODE 3 (vendor/location) 분포 ---")
print(df_pay['HVDC CODE 3'].value_counts())
print()

# HVDC CODE 4 = item number or "Warehouse lease"
print("--- HVDC CODE 4 분포 (상위 20) ---")
print(df_pay['HVDC CODE 4'].value_counts().head(20))
print()

# Category 분포
if 'Category' in df_pay.columns:
    print("--- Category 분포 ---")
    print(df_pay['Category'].value_counts())
    print()

    print("--- Category별 비용 ---")
    cat_cost = df_pay.groupby('Category').agg({
        'Amount': 'sum', 'TOTAL': 'sum', 'Sqm': 'sum', 'S No.': 'count'
    }).rename(columns={'S No.': 'cnt'})
    print(cat_cost)
    print()

# IN AND OUT 분포
if 'IN AND OUT' in df_pay.columns:
    print("--- IN AND OUT 분포 ---")
    print(df_pay['IN AND OUT'].value_counts())
    print()

# HVDC CODE 2 분포
print("--- HVDC CODE 2 분포 ---")
print(df_pay['HVDC CODE 2'].value_counts())
print()

# HVDC CODE 1 분포
print("--- HVDC CODE 1 분포 ---")
print(df_pay['HVDC CODE 1'].value_counts())
print()

# Warehouse lease vs item-specific records
wh_lease = df_pay[df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease|warehouse', case=False, na=False)]
print(f"--- 'Warehouse lease' 레코드: {len(wh_lease)}건 ---")
if len(wh_lease) > 0:
    print(f"  Amount 합계: {wh_lease['Amount'].sum():,.2f}")
    print(f"  TOTAL 합계: {wh_lease['TOTAL'].sum():,.2f}")
    print(f"  Sqm 합계: {wh_lease['Sqm'].sum():,.2f}")
    print()
    print("  HVDC CODE 3별:")
    print(wh_lease.groupby('HVDC CODE 3').agg({'Amount': 'sum', 'TOTAL': 'sum', 'Sqm': 'sum', 'S No.': 'count'}).rename(columns={'S No.': 'cnt'}))
    print()

non_lease = df_pay[~df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease|warehouse', case=False, na=False)]
print(f"--- 비-lease 레코드 (Handling 등): {len(non_lease)}건 ---")
print(f"  Amount 합계: {non_lease['Amount'].sum():,.2f}")
print(f"  TOTAL 합계: {non_lease['TOTAL'].sum():,.2f}")
print(f"  Sqm 합계: {non_lease['Sqm'].sum():,.2f}")
print()

# Cross tab: HVDC CODE 3 vs Category
print("--- HVDC CODE 3 x Category 교차표 (TOTAL) ---")
ct = pd.crosstab(df_pay['HVDC CODE 3'], df_pay['Category'] if 'Category' in df_pay.columns else 'N/A', values=df_pay['TOTAL'], aggfunc='sum', margins=True)
print(ct.to_string())
print()

print("=" * 80)
print("B. HVDC_입고로직 - 창고 위치 컬럼 분석")
print("=" * 80)

xl_logic = pd.ExcelFile('HVDC_입고로직.xlsx')
df_total = pd.read_excel(xl_logic, sheet_name=0)

# Warehouse location columns (cols 25-38)
wh_cols = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'AAA Storage',
           'DSV Outdoor', 'DSV MZP', 'MOSB', 'Hauler Indoor',
           'JDN MZD', 'Shifting', 'MIR', 'SHU', 'DAS', 'AGI']

print(f"\n창고 위치 컬럼별 non-null 현황:")
for col in wh_cols:
    if col in df_total.columns:
        nn = df_total[col].notna().sum()
        if nn > 0:
            print(f"  {col:<20}: {nn:>5} ({nn/len(df_total)*100:.1f}%)")
print()

# Which items have ANY warehouse date
has_any_wh = pd.Series(False, index=df_total.index)
for col in wh_cols:
    if col in df_total.columns:
        has_any_wh = has_any_wh | df_total[col].notna()
print(f"어떤 창고든 거친 아이템: {has_any_wh.sum()} / {len(df_total)} ({has_any_wh.sum()/len(df_total)*100:.1f}%)")
print(f"창고 안 거친 아이템: {(~has_any_wh).sum()}")
print()

# Items with first in wh / last out wh
has_dates = df_total['first in wh'].notna() & df_total['last out wh'].notna()
print(f"first in wh + last out wh 있는 아이템: {has_dates.sum()}")
print()

# Final_Location 분포
if 'Final_Location' in df_total.columns:
    print("--- Final_Location 분포 ---")
    print(df_total['Final_Location'].value_counts().head(20))
    print()

# Status_Location 분포
if 'Status_Location' in df_total.columns:
    print("--- Status_Location 분포 ---")
    print(df_total['Status_Location'].value_counts().head(20))
    print()

# Status_Current 분포
if 'Status_Current' in df_total.columns:
    print("--- Status_Current 분포 ---")
    print(df_total['Status_Current'].value_counts().head(20))
    print()

# Source_Vendor 분포
print("--- Source_Vendor 분포 ---")
print(df_total['Source_Vendor'].value_counts())
print()

# SCT Ref.No (HVDC CODE) 구조 분석
print("--- SCT Ref.No 구조 분석 ---")
sct = df_total['SCT Ref.No'].dropna().astype(str)
# Parse HVDC CODE 3 from SCT Ref.No
def get_code3(code):
    parts = str(code).split('-')
    return parts[2] if len(parts) > 2 else 'N/A'

df_total['_code3'] = df_total['SCT Ref.No'].apply(get_code3)
print("SCT Ref.No의 CODE 3 분포:")
print(df_total['_code3'].value_counts())
print()

print("=" * 80)
print("C. 창고별 아이템 체류 상세")
print("=" * 80)

# For each warehouse column, check dates and item counts
for col in wh_cols:
    if col in df_total.columns:
        nn = df_total[col].notna().sum()
        if nn > 0:
            dates = pd.to_datetime(df_total[col], errors='coerce')
            valid = dates.notna().sum()
            if valid > 0:
                print(f"\n{col}: {nn}건 (dates valid: {valid})")
                print(f"  범위: {dates.min()} ~ {dates.max()}")
                # Vendor breakdown
                vb = df_total[dates.notna()].groupby('Source_Vendor').size()
                print(f"  Vendor: {dict(vb)}")

print()

print("=" * 80)
print("D. 행 레이블 JSON 대비 분석")
print("=" * 80)

with open('행 레이블 WH 기성 HVDC STATUS 입고로직 전체 입고로직(FLO.json', 'r', encoding='utf-8') as f:
    label_data = json.load(f)

print(f"\n{'label':<20} {'WH기성':>8} {'STATUS':>8} {'입고전체':>8} {'입고FLOW':>10}")
print("-" * 58)
for item in label_data:
    label = item['행 레이블']
    wh = item.get('WH 기성') or 0
    st = item.get('HVDC STATUS') or 0
    logic = item.get('입고로직 전체') or 0
    flow = item.get('입고로직(FLOW CODE 3,4,5)') or 0
    print(f"{label:<20} {wh:>8} {st:>8} {logic:>8} {flow:>10}")

# Now map: which labels in WH기성 have no match in 입고로직?
print("\n--- WH기성에만 있고 입고로직에 없는 label ---")
for item in label_data:
    label = item['행 레이블']
    wh = item.get('WH 기성') or 0
    logic = item.get('입고로직 전체') or 0
    if wh > 0 and logic == 0:
        print(f"  {label}: WH기성 {wh}건")

print("\n--- 입고로직에만 있고 WH기성에 없는 label ---")
for item in label_data:
    label = item['행 레이블']
    wh = item.get('WH 기성') or 0
    logic = item.get('입고로직 전체') or 0
    if logic > 0 and wh == 0:
        print(f"  {label}: 입고로직 {logic}건")

print()

print("=" * 80)
print("E. wh payment HVDC CODE 3 vs 입고로직 CODE 3 매칭")
print("=" * 80)

pay_code3 = set(df_pay['HVDC CODE 3'].dropna().unique())
logic_code3 = set(df_total['_code3'].dropna().unique())

print(f"\nwh payment CODE 3: {sorted(pay_code3)}")
print(f"입고로직 CODE 3: {sorted(logic_code3)}")
print(f"\n교집합: {sorted(pay_code3 & logic_code3)}")
print(f"wh payment에만: {sorted(pay_code3 - logic_code3)}")
print(f"입고로직에만: {sorted(logic_code3 - pay_code3)}")

# wh payment의 CODE 3별 비용
print("\n--- wh payment CODE 3별 비용 ---")
pay_by_code3 = df_pay.groupby('HVDC CODE 3').agg({
    'Amount': 'sum', 'TOTAL': 'sum', 'Sqm': 'sum', 'S No.': 'count'
}).rename(columns={'S No.': 'cnt'}).sort_values('TOTAL', ascending=False)
print(pay_by_code3.to_string())

print()
print("=" * 80)
print("F. wh payment의 Handling vs Storage 구분")
print("=" * 80)

# Sqm > 0 means storage cost, Sqm == 0 means handling only
storage_rows = df_pay[df_pay['Sqm'] > 0]
handling_rows = df_pay[df_pay['Sqm'] == 0]

print(f"\nStorage 레코드 (Sqm > 0): {len(storage_rows)}건")
print(f"  Amount: {storage_rows['Amount'].sum():,.2f}")
print(f"  TOTAL: {storage_rows['TOTAL'].sum():,.2f}")
print(f"  Handling In: {storage_rows['Handling In'].sum():,.2f}" if 'Handling In' in df_pay.columns else "")
print(f"  Handling out: {storage_rows['Handling out'].sum():,.2f}" if 'Handling out' in df_pay.columns else "")

print(f"\nHandling-only 레코드 (Sqm == 0): {len(handling_rows)}건")
print(f"  Amount: {handling_rows['Amount'].sum():,.2f}")
print(f"  TOTAL: {handling_rows['TOTAL'].sum():,.2f}")
print(f"  Handling In: {handling_rows['Handling In'].sum():,.2f}" if 'Handling In' in df_pay.columns else "")
print(f"  Handling out: {handling_rows['Handling out'].sum():,.2f}" if 'Handling out' in df_pay.columns else "")

# Storage by CODE 3
print(f"\n--- Storage (Sqm>0) CODE 3별 ---")
st_by_code3 = storage_rows.groupby('HVDC CODE 3').agg({
    'Amount': 'sum', 'TOTAL': 'sum', 'Sqm': 'sum', 'S No.': 'count'
}).rename(columns={'S No.': 'cnt'}).sort_values('TOTAL', ascending=False)
print(st_by_code3.to_string())

print(f"\n--- Handling-only (Sqm==0) CODE 3별 ---")
h_by_code3 = handling_rows.groupby('HVDC CODE 3').agg({
    'Amount': 'sum', 'TOTAL': 'sum', 'S No.': 'count'
}).rename(columns={'S No.': 'cnt'}).sort_values('TOTAL', ascending=False)
print(h_by_code3.to_string())

# Sample rows to understand structure
print()
print("=" * 80)
print("G. wh payment 샘플 레코드 (다양한 유형)")
print("=" * 80)

cols_show = ['HVDC CODE', 'HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4',
             'Category', 'Operation Month', 'Sqm', 'Amount', 'TOTAL']

# Storage sample
print("\n--- Storage 샘플 (Sqm > 0, 상위 5) ---")
print(storage_rows[cols_show].head(5).to_string())

# Handling sample
print("\n--- Handling 샘플 (Sqm == 0, 상위 5) ---")
print(handling_rows[cols_show].head(5).to_string())

# Warehouse lease sample
if len(wh_lease) > 0:
    print("\n--- Warehouse lease 샘플 ---")
    print(wh_lease[cols_show].head(5).to_string())
