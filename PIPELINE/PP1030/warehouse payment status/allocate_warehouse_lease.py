"""
Warehouse Lease Allocation (Method B: 입고로직 재고 기준)

Logic:
  1. Monthly per-item rate = Warehouse Lease / 입고로직 재고
  2. Non-Lease items mapped to warehouse by Category
  3. Indoor items → combined (DSV Indoor + Al Markaz) rate
  4. Output: non-lease rows + allocation columns, lease rows removed
"""
import pandas as pd
import numpy as np
from pathlib import Path

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)

WH_PAYMENT = 'wh payment.xlsx'
LOGIC_FILE = 'HVDC_입고로직.xlsx'
OUTPUT_FILE = 'wh_payment_allocated.xlsx'

# ━━━ 1. Load data ━━━
df_pay = pd.read_excel(WH_PAYMENT, sheet_name=1)
lease_mask = df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)
lease = df_pay[lease_mask].copy()
non_lease = df_pay[~lease_mask].copy()

# ━━━ 2. Lease: per-warehouse per-month amounts ━━━
lease['wh'] = lease['HVDC CODE 1'].str.strip()
lease['month'] = pd.to_datetime(lease['Operation Month']).dt.to_period('M')

lease_pivot = lease.groupby(['month', 'wh'])['TOTAL'].sum().unstack(fill_value=0)
lease_pivot.columns.name = None

# ━━━ 3. 입고로직: monthly stock per warehouse ━━━
df_wh_raw = pd.read_excel(LOGIC_FILE, sheet_name=1, header=None)
wh_names = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor', 'DSV MZP',
            'JDN MZD', 'Hauler Indoor', 'AAA Storage', 'MOSB']

data_rows = df_wh_raw.iloc[1:].copy()
data_rows.columns = range(len(data_rows.columns))
data_rows = data_rows[data_rows[1].astype(str) != 'Total'].copy()

stock = pd.DataFrame()
stock['month'] = data_rows[1].astype(str).values
for idx, wh in enumerate(wh_names):
    col_stock = 2 + idx * 3 + 2  # 3rd col per group = 재고
    stock[wh] = pd.to_numeric(data_rows[col_stock], errors='coerce').fillna(0).astype(int).values

stock['month_period'] = stock['month'].apply(lambda x: pd.Period(x, freq='M'))
stock = stock.set_index('month_period')

# ━━━ 4. Calculate monthly per-item rates ━━━
rate_table = []

lease_months = sorted(lease_pivot.index)
for m in lease_months:
    row = {'month': m}

    # DSV Outdoor
    l_out = lease_pivot.loc[m].get('DSV Outdoor', 0)
    s_out = stock.loc[m, 'DSV Outdoor'] if m in stock.index else 0
    row['Outdoor_lease'] = l_out
    row['Outdoor_stock'] = s_out
    row['Outdoor_rate'] = l_out / s_out if s_out > 0 else 0

    # DSV MZP
    l_mzp = lease_pivot.loc[m].get('DSV MZP', 0)
    s_mzp = stock.loc[m, 'DSV MZP'] if m in stock.index else 0
    row['MZP_lease'] = l_mzp
    row['MZP_stock'] = s_mzp
    row['MZP_rate'] = l_mzp / s_mzp if s_mzp > 0 else 0

    # Indoor + Al Markaz combined
    l_in = lease_pivot.loc[m].get('DSV Indoor', 0)
    l_al = lease_pivot.loc[m].get('DSV Al Markaz', 0)
    s_in = stock.loc[m, 'DSV Indoor'] if m in stock.index else 0
    s_al = stock.loc[m, 'DSV Al Markaz'] if m in stock.index else 0
    s_combined = s_in + max(s_al, 0)  # ignore negative stock
    l_combined = l_in + l_al
    row['Indoor_lease'] = l_in
    row['AlMarkaz_lease'] = l_al
    row['Indoor_stock'] = s_in
    row['AlMarkaz_stock'] = max(s_al, 0)
    row['Combined_stock'] = s_combined
    row['Combined_lease'] = l_combined
    row['Indoor_combined_rate'] = l_combined / s_combined if s_combined > 0 else 0

    rate_table.append(row)

df_rates = pd.DataFrame(rate_table).set_index('month')

print("=" * 120)
print("Monthly Per-Item Rates (Method B)")
print("=" * 120)
print(f"{'Month':<10} | {'Indoor+ALM Lease':>16} {'Stock':>6} {'Rate':>10} | {'Outdoor Lease':>14} {'Stock':>6} {'Rate':>10} | {'MZP Lease':>10} {'Stock':>6} {'Rate':>10}")
print("-" * 120)
for m, r in df_rates.iterrows():
    print(f"{str(m):<10} | {r['Combined_lease']:>16,.0f} {r['Combined_stock']:>6.0f} {r['Indoor_combined_rate']:>10,.2f} | {r['Outdoor_lease']:>14,.0f} {r['Outdoor_stock']:>6.0f} {r['Outdoor_rate']:>10,.2f} | {r['MZP_lease']:>10,.0f} {r['MZP_stock']:>6.0f} {r['MZP_rate']:>10,.2f}")

# ━━━ 5. Map non-lease items to warehouse and assign rates ━━━
non_lease = non_lease.copy()
non_lease['month_period'] = pd.to_datetime(non_lease['Operation Month']).dt.to_period('M')

def map_warehouse(row):
    cat = str(row['Category']).strip()
    code1 = str(row.get('HVDC CODE 1', '')).strip()
    if cat == 'DG':
        return 'EXCLUDED_DG'
    if cat == 'Shifting':
        return 'EXCLUDED_SHIFT'
    if cat == 'Indoor':
        return 'Indoor_Combined'
    if cat == 'Mina Zayed':
        return 'DSV MZP'
    if cat == 'Outdoor':
        if 'MZP' in code1.upper():
            return 'DSV MZP'
        return 'DSV Outdoor'
    return 'UNKNOWN'

non_lease['Mapped_Warehouse'] = non_lease.apply(map_warehouse, axis=1)

def get_rate(row):
    m = row['month_period']
    wh = row['Mapped_Warehouse']
    if wh.startswith('EXCLUDED') or wh == 'UNKNOWN':
        return 0.0
    if m not in df_rates.index:
        return 0.0
    r = df_rates.loc[m]
    if wh == 'Indoor_Combined':
        return r['Indoor_combined_rate']
    elif wh == 'DSV Outdoor':
        return r['Outdoor_rate']
    elif wh == 'DSV MZP':
        return r['MZP_rate']
    return 0.0

non_lease['Allocated_Storage'] = non_lease.apply(get_rate, axis=1)
non_lease['TOTAL_with_Storage'] = non_lease['TOTAL'] + non_lease['Allocated_Storage']

# Clean warehouse name for output
wh_display = {
    'Indoor_Combined': 'DSV Indoor/Al Markaz',
    'DSV Outdoor': 'DSV Outdoor',
    'DSV MZP': 'DSV MZP',
    'EXCLUDED_DG': '-',
    'EXCLUDED_SHIFT': '-',
    'UNKNOWN': '-'
}
non_lease['Storage_Warehouse'] = non_lease['Mapped_Warehouse'].map(wh_display)

# ━━━ 6. Summary ━━━
print()
print("=" * 120)
print("Allocation Summary")
print("=" * 120)

alloc_by_wh = non_lease.groupby('Mapped_Warehouse').agg(
    items=('Allocated_Storage', 'size'),
    allocated_sum=('Allocated_Storage', 'sum'),
    avg_rate=('Allocated_Storage', 'mean')
)
print(alloc_by_wh)

total_allocated = non_lease[~non_lease['Mapped_Warehouse'].str.startswith('EXCLUDED')]['Allocated_Storage'].sum()
total_lease = lease['TOTAL'].sum()
coverage = total_allocated / total_lease * 100

print(f"\nTotal Lease:     {total_lease:>14,.0f} AED")
print(f"Total Allocated: {total_allocated:>14,.0f} AED")
print(f"Coverage:        {coverage:>13.1f}%")
print(f"Unallocated:     {total_lease - total_allocated:>14,.0f} AED ({100 - coverage:.1f}%)")

# Monthly detail
print()
print("Monthly Allocation Detail:")
print(f"{'Month':<10} | {'Lease':>12} {'Allocated':>12} {'Coverage':>8} | {'Indoor':>10} {'Outdoor':>10} {'MZP':>10}")
print("-" * 90)

alloc_items = non_lease[~non_lease['Mapped_Warehouse'].str.startswith('EXCLUDED')].copy()
for m in sorted(alloc_items['month_period'].unique()):
    m_items = alloc_items[alloc_items['month_period'] == m]
    m_alloc = m_items['Allocated_Storage'].sum()
    m_lease = lease[lease['month'] == m]['TOTAL'].sum()
    m_cov = m_alloc / m_lease * 100 if m_lease > 0 else 0

    in_alloc = m_items[m_items['Mapped_Warehouse'] == 'Indoor_Combined']['Allocated_Storage'].sum()
    out_alloc = m_items[m_items['Mapped_Warehouse'] == 'DSV Outdoor']['Allocated_Storage'].sum()
    mzp_alloc = m_items[m_items['Mapped_Warehouse'] == 'DSV MZP']['Allocated_Storage'].sum()

    print(f"{str(m):<10} | {m_lease:>12,.0f} {m_alloc:>12,.0f} {m_cov:>7.1f}% | {in_alloc:>10,.0f} {out_alloc:>10,.0f} {mzp_alloc:>10,.0f}")

# ━━━ 7. Write output Excel ━━━
drop_cols = ['month_period', 'Mapped_Warehouse']
out_df = non_lease.drop(columns=drop_cols)

# Reorder: original columns + new columns at the end
orig_cols = [c for c in df_pay.columns if c in out_df.columns]
new_cols = ['Allocated_Storage', 'Storage_Warehouse', 'TOTAL_with_Storage']
final_cols = orig_cols + new_cols
out_df = out_df[final_cols]

with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    out_df.to_excel(writer, sheet_name='wh_payment_allocated', index=False)

    # Rate reference sheet
    rate_out = df_rates.reset_index()
    rate_out.to_excel(writer, sheet_name='monthly_rates', index=False)

print(f"\nOutput: {OUTPUT_FILE}")
print(f"  Sheet 'wh_payment_allocated': {len(out_df)} rows (lease {len(lease)} rows removed)")
print(f"  Sheet 'monthly_rates': {len(rate_out)} rows")
print(f"\nNew columns: Allocated_Storage, Storage_Warehouse, TOTAL_with_Storage")
