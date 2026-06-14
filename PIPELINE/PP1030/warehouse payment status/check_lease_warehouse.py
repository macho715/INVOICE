import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_colwidth', 40)

df_pay = pd.read_excel('wh payment.xlsx', sheet_name=1)

lease = df_pay[df_pay['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)]
non_lease = df_pay[~df_pay.index.isin(lease.index)]

# 1. Warehouse Lease - 창고별 구분
print("=" * 100)
print("1. Warehouse Lease 89건 - 창고별 분류")
print("=" * 100)

# CODE 1, CODE 2, CODE 3, CODE 4, Category 조합 확인
print(f"\nLease CODE 1 분포:")
print(lease['HVDC CODE 1'].value_counts())

print(f"\nLease CODE 2 분포:")
print(lease['HVDC CODE 2'].value_counts())

print(f"\nLease CODE 4 분포:")
print(lease['HVDC CODE 4'].value_counts())

print(f"\nLease Category 분포:")
print(lease['Category'].value_counts())

# Category x CODE 4 크로스탭
print(f"\nLease: Category x CODE 4:")
ct = pd.crosstab(lease['Category'], lease['HVDC CODE 4'])
print(ct)

# 창고별 금액 합계
print(f"\nLease 창고별 Amount/TOTAL 합계:")
lease_summary = lease.groupby('Category').agg(
    count=('TOTAL', 'size'),
    Amount_sum=('Amount', 'sum'),
    TOTAL_sum=('TOTAL', 'sum')
).sort_values('TOTAL_sum', ascending=False)
print(lease_summary)
print(f"\n전체 합계: Amount={lease['Amount'].sum():,.0f}  TOTAL={lease['TOTAL'].sum():,.0f}")

# 2. Lease 월별 상세 (창고별)
print()
print("=" * 100)
print("2. Warehouse Lease - 창고별 월별 금액")
print("=" * 100)

# Month 컬럼 확인
month_cols = [c for c in lease.columns if 'month' in c.lower() or 'date' in c.lower() or 'period' in c.lower()]
print(f"날짜 관련 컬럼: {month_cols}")
print(f"전체 컬럼: {lease.columns.tolist()}")

# Lease 샘플 10건
print(f"\nLease 샘플 (처음 15건):")
cols_show = ['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category', 'Month', 'Amount', 'TOTAL']
cols_avail = [c for c in cols_show if c in lease.columns]
if 'Month' not in lease.columns:
    # month 비슷한 컬럼 찾기
    for c in lease.columns:
        if 'mon' in c.lower() or 'date' in c.lower() or '월' in c or 'inv' in c.lower():
            cols_avail.append(c)
print(f"사용 컬럼: {cols_avail}")
print(lease[cols_avail].head(15).to_string())

# 3. Non-Lease에서 Al Markaz 흔적 찾기
print()
print("=" * 100)
print("3. Non-Lease에서 Al Markaz / ALM 관련 항목")
print("=" * 100)

for col in ['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4']:
    alm = non_lease[non_lease[col].astype(str).str.contains('Al.?Mark|ALM|Markaz', case=False, na=False)]
    if len(alm) > 0:
        print(f"\n{col}에 Al Markaz 포함: {len(alm)}건")
        print(alm[['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category', 'Amount']].head(10))

# Indoor 항목 CODE 1 분포 (Al Markaz 포함 여부)
print(f"\nIndoor Category CODE 1 분포:")
indoor = non_lease[non_lease['Category'] == 'Indoor']
print(indoor['HVDC CODE 1'].value_counts())

# 4. Shifting 2건 상세
print()
print("=" * 100)
print("4. Shifting 2건 상세")
print("=" * 100)
shifting = non_lease[non_lease['Category'] == 'Shifting']
print(shifting[['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category', 'Amount', 'TOTAL']].to_string())

# 5. DG 21건 상세
print()
print("=" * 100)
print("5. DG 21건 상세")
print("=" * 100)
dg = non_lease[non_lease['Category'] == 'DG']
print(dg[['HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category', 'Amount', 'TOTAL']].to_string())
print(f"\nDG CODE 1 분포: {dict(dg['HVDC CODE 1'].value_counts())}")
