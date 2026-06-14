import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_rows', 100)

# ── 1. Lease: 창고별 월별 금액 ──
df_pay = pd.read_excel('wh payment.xlsx', sheet_name=1)
lease = df_pay[df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)].copy()
non_lease = df_pay[~df_pay.index.isin(lease.index)].copy()

lease['wh'] = lease['HVDC CODE 1'].str.strip()
lease['month'] = pd.to_datetime(lease['Operation Month']).dt.to_period('M')

lease_monthly = lease.groupby(['wh', 'month']).agg(
    lease_count=('TOTAL', 'size'),
    Amount=('Amount', 'sum'),
    TOTAL=('TOTAL', 'sum')
).reset_index()

print("=" * 100)
print("Lease 월별 창고별 금액 (TOTAL)")
print("=" * 100)
pivot_lease = lease_monthly.pivot_table(index='month', columns='wh', values='TOTAL', aggfunc='sum', fill_value=0)
pivot_lease['합계'] = pivot_lease.sum(axis=1)
print(pivot_lease.to_string())
print(f"\n열 합계:")
print(pivot_lease.sum().to_string())

# ── 2. 입고로직: 창고_월별_입출고 (재고 = 해당월 재고 수량) ──
print()
print("=" * 100)
print("입고로직 창고_월별_입출고 - 월별 재고 현황")
print("=" * 100)

df_wh = pd.read_excel('HVDC_입고로직.xlsx', sheet_name=1, header=None)
headers = df_wh.iloc[0].tolist()

# 재고 컬럼 인덱스 (각 창고 3번째 = 재고)
wh_names = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor', 'DSV MZP',
            'JDN MZD', 'Hauler Indoor', 'AAA Storage', 'MOSB']
stock_cols = {}
for i, h in enumerate(headers):
    if isinstance(h, str):
        for wh in wh_names:
            # 재고 = 3rd column per warehouse group
            pass

# Manual: col 2=입고_DHL, 3=출고_DHL, 4=재고_DHL, 5=입고_Indoor, 6=출고_Indoor, 7=재고_Indoor, ...
# Pattern: for each WH: 입고, 출고, 재고 → stride 3, starting col 2
stock_col_map = {}
for idx, wh in enumerate(wh_names):
    base = 2 + idx * 3
    stock_col_map[wh] = base + 2  # 재고 column

data_rows = df_wh.iloc[1:-1].copy()  # skip header and Total row
data_rows.columns = range(len(data_rows.columns))
data_rows[1] = data_rows[1].astype(str)

monthly_stock = pd.DataFrame()
monthly_stock['month'] = data_rows[1].values
for wh, col_idx in stock_col_map.items():
    monthly_stock[wh] = pd.to_numeric(data_rows[col_idx], errors='coerce').fillna(0).astype(int).values

# DSV 4개 창고만 추출
dsv_cols = ['DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor', 'DSV MZP']
print(monthly_stock[['month'] + dsv_cols].to_string(index=False))

# ── 3. 크로스: Lease가 있는 월만 비교 ──
print()
print("=" * 100)
print("Lease 존재 월 vs 입고로직 재고 비교")
print("=" * 100)

lease_months = sorted(lease_monthly['month'].unique())
print(f"Lease 기간: {lease_months[0]} ~ {lease_months[-1]} ({len(lease_months)}개월)")

# Lease 월별 합계
lease_by_wh_month = {}
for wh in ['DSV Indoor', 'DSV Outdoor', 'DSV MZP', 'DSV Al Markaz']:
    sub = lease_monthly[lease_monthly['wh'] == wh]
    lease_by_wh_month[wh] = dict(zip(sub['month'].astype(str), sub['TOTAL']))

# 입고로직 재고에서 같은 월 추출
print(f"\n{'월':<10} | {'Indoor재고':>10} {'AlMark재고':>10} {'Outdoor재고':>10} {'MZP재고':>8} | {'Indoor임대':>12} {'AlMark임대':>12} {'Outdoor임대':>12} {'MZP임대':>12}")
print("-" * 140)

for _, row in monthly_stock.iterrows():
    m = row['month']
    if m == 'Total':
        continue
    in_stock = int(row['DSV Indoor'])
    al_stock = int(row['DSV Al Markaz'])
    out_stock = int(row['DSV Outdoor'])
    mzp_stock = int(row['DSV MZP'])

    in_lease = lease_by_wh_month.get('DSV Indoor', {}).get(m, 0)
    al_lease = lease_by_wh_month.get('DSV Al Markaz', {}).get(m, 0)
    out_lease = lease_by_wh_month.get('DSV Outdoor', {}).get(m, 0)
    mzp_lease = lease_by_wh_month.get('DSV MZP', {}).get(m, 0)

    if in_lease or al_lease or out_lease or mzp_lease:
        print(f"{m:<10} | {in_stock:>10,} {al_stock:>10,} {out_stock:>10,} {mzp_stock:>8,} | {in_lease:>12,.0f} {al_lease:>12,.0f} {out_lease:>12,.0f} {mzp_lease:>12,.0f}")

# ── 4. Non-Lease 월별 분포 ──
print()
print("=" * 100)
print("Non-Lease: Operation Month 분포")
print("=" * 100)
non_lease['month'] = pd.to_datetime(non_lease['Operation Month']).dt.to_period('M')
print(non_lease['month'].value_counts().sort_index())

# Non-Lease: Category x Month
print()
print("Non-Lease: Category별 월 분포:")
ct = pd.crosstab(non_lease['month'], non_lease['Category'])
ct['합계'] = ct.sum(axis=1)
print(ct.to_string())

# ── 5. Indoor 세부: 월별 Indoor 아이템 수 vs 입고로직 Indoor+AlMarkaz 재고 비율 ──
print()
print("=" * 100)
print("Indoor 배분: 월별 DSV Indoor vs Al Markaz 재고 비율")
print("=" * 100)
print(f"{'월':<10} | {'Indoor재고':>10} {'AlMark재고':>10} {'Indoor%':>8} {'AlMark%':>8} | {'Indoor건수':>10}")
print("-" * 80)

indoor_items = non_lease[non_lease['Category'] == 'Indoor']
indoor_by_month = indoor_items.groupby('month').size()

for _, row in monthly_stock.iterrows():
    m = row['month']
    if m == 'Total':
        continue
    in_s = int(row['DSV Indoor'])
    al_s = int(row['DSV Al Markaz'])
    total_s = in_s + al_s
    in_pct = in_s / total_s * 100 if total_s > 0 else 0
    al_pct = al_s / total_s * 100 if total_s > 0 else 0

    m_period = pd.Period(m, freq='M')
    items = indoor_by_month.get(m_period, 0)

    if in_s > 0 or al_s > 0 or items > 0:
        print(f"{m:<10} | {in_s:>10,} {al_s:>10,} {in_pct:>7.1f}% {al_pct:>7.1f}% | {items:>10}")
