import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_colwidth', 50)

xl = pd.ExcelFile('wh payment.xlsx')
df = pd.read_excel(xl, sheet_name=1)

# Non-lease only
non_lease = df[~df['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)].copy()

print("=" * 100)
print("Non-lease 863건: HVDC CODE 1,2,3,4 + Category 전수 확인")
print("=" * 100)

cols = ['HVDC CODE', 'HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 
        'Category', 'Operation Month', 'TOTAL']

# CODE 3별 상세
for code3 in non_lease['HVDC CODE 3'].value_counts().index:
    sub = non_lease[non_lease['HVDC CODE 3'] == code3]
    print(f"\n--- CODE 3 = {code3} ({len(sub)}건, TOTAL={sub['TOTAL'].sum():,.2f}) ---")
    
    # CODE 1 분포
    c1 = sub['HVDC CODE 1'].value_counts()
    print(f"  CODE 1: {dict(c1)}")
    
    # CODE 2 분포
    c2 = sub['HVDC CODE 2'].value_counts()
    print(f"  CODE 2: {dict(c2)}")
    
    # CODE 4 분포 (상위 10)
    c4 = sub['HVDC CODE 4'].value_counts().head(10)
    print(f"  CODE 4 (top10): {dict(c4)}")
    
    # Category 분포
    cat = sub['Category'].value_counts()
    print(f"  Category: {dict(cat)}")
    
    # 샘플 5건
    print(f"  샘플:")
    for _, row in sub.head(5).iterrows():
        print(f"    {row['HVDC CODE']:<50} C1={str(row['HVDC CODE 1']):<20} C2={str(row['HVDC CODE 2']):<10} C3={str(row['HVDC CODE 3']):<15} C4={str(row['HVDC CODE 4']):<10} Cat={str(row['Category']):<10} TOTAL={row['TOTAL']:>10,.2f}")

print()
print("=" * 100)
print("SCT 상세 (219건)")
print("=" * 100)

sct = non_lease[non_lease['HVDC CODE 3'] == 'SCT']
print(f"\nSCT CODE 1 분포:")
print(sct['HVDC CODE 1'].value_counts().to_string())
print(f"\nSCT CODE 2 분포:")
print(sct['HVDC CODE 2'].value_counts().to_string())
print(f"\nSCT Category 분포:")
print(sct['Category'].value_counts().to_string())

print(f"\nSCT 전체 HVDC CODE (unique):")
for c in sorted(sct['HVDC CODE'].unique()):
    print(f"  {c}")

print()
print("=" * 100)
print("Lease 89건: HVDC CODE 확인 (어떤 창고 이름이 기재되어 있는지)")
print("=" * 100)

lease = df[df['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)]
print(f"\nLease CODE 1 분포:")
print(lease['HVDC CODE 1'].value_counts().to_string())
print(f"\nLease CODE 3 분포:")
print(lease['HVDC CODE 3'].value_counts().to_string())
print(f"\nLease 샘플:")
for _, row in lease.head(10).iterrows():
    print(f"  {row['HVDC CODE']:<60} C1={str(row['HVDC CODE 1']):<20} C3={str(row['HVDC CODE 3']):<15} Month={row['Operation Month']}  TOTAL={row['TOTAL']:>12,.2f}")

print()
print("=" * 100)
print("Non-lease에서 창고 위치 정보가 있는 경우 확인")
print("=" * 100)

# Check if HVDC CODE itself contains warehouse names
wh_names = ['DSV Indoor', 'DSV Outdoor', 'Al Markaz', 'MZP', 'MOSB', 'M44', 'DHL', 'Hauler', 'AAA']
for wh in wh_names:
    for col in ['HVDC CODE', 'HVDC CODE 1', 'HVDC CODE 2', 'HVDC CODE 3', 'HVDC CODE 4', 'Category']:
        matches = non_lease[non_lease[col].astype(str).str.contains(wh, case=False, na=False)]
        if len(matches) > 0:
            print(f"\n  '{wh}' in {col}: {len(matches)}건")
            for _, row in matches.head(3).iterrows():
                print(f"    {row['HVDC CODE']:<50} C3={str(row['HVDC CODE 3']):<15} C4={str(row['HVDC CODE 4']):<15} Cat={str(row['Category']):<10}")

print()
print("=" * 100)
print("Category로 창고 구분 가능성")
print("=" * 100)
print(f"\nNon-lease Category 분포:")
print(non_lease['Category'].value_counts().to_string())

print(f"\nCategory x CODE 3 교차 (TOTAL):")
ct = pd.crosstab(non_lease['HVDC CODE 3'], non_lease['Category'], values=non_lease['TOTAL'], aggfunc='sum', margins=True)
print(ct.to_string())
