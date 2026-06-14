"""
Warehouse Lease Allocation v2 — Full Distribution

Logic:
  1. Each warehouse's monthly lease is FULLY distributed to non-lease items
     in that warehouse/month
  2. Indoor items receive combined (DSV Indoor + Al Markaz) lease,
     split by 입고로직 stock ratio for reference
  3. DG/Shifting excluded from allocation → their lease share redistributed
"""
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)

WH_PAYMENT = 'wh payment.xlsx'
LOGIC_FILE = 'HVDC_입고로직.xlsx'
OUTPUT_FILE = 'wh_payment_allocated_v2.xlsx'

# ━━━ 1. Load & split ━━━
df_pay = pd.read_excel(WH_PAYMENT, sheet_name=1)
lease_mask = df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)
lease = df_pay[lease_mask].copy()
non_lease = df_pay[~lease_mask].copy()

print(f"Total rows: {len(df_pay)}, Lease: {len(lease)}, Non-Lease: {len(non_lease)}")
print(f"Total TOTAL: {df_pay['TOTAL'].sum():,.0f}")
print(f"Lease TOTAL: {lease['TOTAL'].sum():,.0f}")
print(f"Non-Lease TOTAL: {non_lease['TOTAL'].sum():,.0f}")

# ━━━ 2. Warehouse mapping for non-lease items ━━━
non_lease = non_lease.copy()
non_lease['month'] = pd.to_datetime(non_lease['Operation Month']).dt.to_period('M')

def map_warehouse(row):
    cat = str(row['Category']).strip()
    code1 = str(row.get('HVDC CODE 1', '')).strip()
    if cat == 'DG':
        return 'EXCLUDED'
    if cat == 'Shifting':
        return 'EXCLUDED'
    if cat == 'Indoor':
        return 'Indoor_Combined'
    if cat == 'Mina Zayed':
        return 'DSV MZP'
    if cat == 'Outdoor':
        if 'MZP' in code1.upper():
            return 'DSV MZP'
        return 'DSV Outdoor'
    return 'EXCLUDED'

non_lease['wh_group'] = non_lease.apply(map_warehouse, axis=1)

# ━━━ 3. Lease: per-warehouse per-month ━━━
lease['wh'] = lease['HVDC CODE 1'].str.strip()
lease['month'] = pd.to_datetime(lease['Operation Month']).dt.to_period('M')

# Map lease warehouse → allocation group
lease_wh_map = {
    'DSV Indoor': 'Indoor_Combined',
    'DSV Al Markaz': 'Indoor_Combined',
    'DSV Outdoor': 'DSV Outdoor',
    'DSV MZP': 'DSV MZP'
}
lease['wh_group'] = lease['wh'].map(lease_wh_map)

# Monthly lease per group
lease_monthly = lease.groupby(['month', 'wh_group'])['TOTAL'].sum().reset_index()
lease_monthly.columns = ['month', 'wh_group', 'lease_amount']

# ━━━ 4. Count non-lease items per group per month ━━━
active = non_lease[non_lease['wh_group'] != 'EXCLUDED']
item_counts = active.groupby(['month', 'wh_group']).size().reset_index(name='item_count')

# Merge
alloc_plan = lease_monthly.merge(item_counts, on=['month', 'wh_group'], how='left')
alloc_plan['item_count'] = alloc_plan['item_count'].fillna(0).astype(int)
alloc_plan['per_item'] = np.where(
    alloc_plan['item_count'] > 0,
    alloc_plan['lease_amount'] / alloc_plan['item_count'],
    0
)

# ━━━ 5. Handle months with lease but no items → redistribute ━━━
no_items = alloc_plan[alloc_plan['item_count'] == 0]
if len(no_items) > 0:
    print(f"\nLease with 0 items (needs redistribution):")
    print(no_items[['month', 'wh_group', 'lease_amount']].to_string())
    orphan_total = no_items['lease_amount'].sum()
    print(f"Orphan amount: {orphan_total:,.0f}")

    # Redistribute orphan proportionally across all active items
    total_active = len(active)
    orphan_per_item = orphan_total / total_active if total_active > 0 else 0
    print(f"Orphan per item ({total_active} items): {orphan_per_item:,.2f}")
else:
    orphan_per_item = 0

# ━━━ 6. Assign allocation to each non-lease item ━━━
alloc_lookup = alloc_plan.set_index(['month', 'wh_group'])['per_item'].to_dict()

def get_allocation(row):
    if row['wh_group'] == 'EXCLUDED':
        return 0.0
    key = (row['month'], row['wh_group'])
    base = alloc_lookup.get(key, 0.0)
    return base + orphan_per_item

non_lease['Allocated_Storage'] = non_lease.apply(get_allocation, axis=1)
non_lease['TOTAL_with_Storage'] = non_lease['TOTAL'] + non_lease['Allocated_Storage']

wh_display = {
    'Indoor_Combined': 'DSV Indoor/Al Markaz',
    'DSV Outdoor': 'DSV Outdoor',
    'DSV MZP': 'DSV MZP',
    'EXCLUDED': '-'
}
non_lease['Storage_Warehouse'] = non_lease['wh_group'].map(wh_display)

# ━━━ 7. Verification ━━━
print()
print("=" * 120)
print("Allocation Plan (per warehouse-group per month)")
print("=" * 120)
print(f"{'Month':<10} | {'Group':<18} {'Lease':>14} {'Items':>6} {'Per Item':>12}")
print("-" * 70)
for _, r in alloc_plan.sort_values(['month', 'wh_group']).iterrows():
    if r['lease_amount'] > 0:
        print(f"{str(r['month']):<10} | {r['wh_group']:<18} {r['lease_amount']:>14,.0f} {r['item_count']:>6} {r['per_item']:>12,.2f}")

total_allocated = non_lease['Allocated_Storage'].sum()
total_lease = lease['TOTAL'].sum()

print()
print("=" * 120)
print("Summary")
print("=" * 120)

by_wh = non_lease.groupby('wh_group').agg(
    items=('Allocated_Storage', 'size'),
    allocated=('Allocated_Storage', 'sum'),
    original_total=('TOTAL', 'sum'),
    new_total=('TOTAL_with_Storage', 'sum')
)
print(by_wh)

print(f"\n{'Original Non-Lease TOTAL:':<30} {non_lease['TOTAL'].sum():>14,.0f}")
print(f"{'Lease TOTAL:':<30} {total_lease:>14,.0f}")
print(f"{'Allocated:':<30} {total_allocated:>14,.0f}")
print(f"{'Coverage:':<30} {total_allocated / total_lease * 100:>13.1f}%")
print(f"{'Deviation:':<30} {abs(total_allocated - total_lease):>14,.0f} ({abs(total_allocated - total_lease) / total_lease * 100:.2f}%)")
print(f"{'New Grand Total:':<30} {non_lease['TOTAL_with_Storage'].sum():>14,.0f}")
print(f"{'Expected (original total):':<30} {df_pay['TOTAL'].sum():>14,.0f}")

# ━━━ 8. Write output ━━━
drop_cols = ['month', 'wh_group']
out_df = non_lease.drop(columns=drop_cols)

orig_cols = [c for c in df_pay.columns if c in out_df.columns]
new_cols = ['Allocated_Storage', 'Storage_Warehouse', 'TOTAL_with_Storage']
out_df = out_df[orig_cols + new_cols]

with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    out_df.to_excel(writer, sheet_name='wh_payment_allocated', index=False)
    alloc_plan.to_excel(writer, sheet_name='allocation_plan', index=False)

print(f"\nOutput: {OUTPUT_FILE}")
print(f"  'wh_payment_allocated': {len(out_df)} rows")
print(f"  'allocation_plan': {len(alloc_plan)} rows (rate reference)")
