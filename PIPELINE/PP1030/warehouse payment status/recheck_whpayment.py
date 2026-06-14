import pandas as pd
import numpy as np
import json

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 220)
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_colwidth', 40)

xl = pd.ExcelFile('wh payment.xlsx')
print(f"시트: {xl.sheet_names}")
print()

# Sheet 0 (표1) - 원본
df0 = pd.read_excel(xl, sheet_name=0)
print(f"=== 표1 (Sheet 0) ===")
print(f"Shape: {df0.shape}")
print(f"컬럼: {df0.columns.tolist()}")
print()

# Sheet 1 (Merged Data) 
df1 = pd.read_excel(xl, sheet_name=1)
print(f"=== Merged Data (Sheet 1) ===")
print(f"Shape: {df1.shape}")
print(f"컬럼: {df1.columns.tolist()}")
print()

print("=" * 80)
print("1. HVDC CODE 전체 구조 분석")
print("=" * 80)

print("\n--- HVDC CODE 샘플 (unique, 상위 30) ---")
codes = df1['HVDC CODE'].dropna().unique()
print(f"총 unique HVDC CODE: {len(codes)}")
for c in sorted(codes)[:30]:
    print(f"  {c}")
print("  ...")
for c in sorted(codes)[-10:]:
    print(f"  {c}")

print()
print("--- HVDC CODE 1 분포 ---")
print(df1['HVDC CODE 1'].value_counts().to_string())

print()
print("--- HVDC CODE 2 분포 ---")
print(df1['HVDC CODE 2'].value_counts().to_string())

print()
print("--- HVDC CODE 3 분포 ---")
c3 = df1['HVDC CODE 3'].value_counts()
print(c3.to_string())

print()
print("--- HVDC CODE 4 분포 ---")
c4 = df1['HVDC CODE 4'].value_counts()
print(c4.to_string())

print()
print("=" * 80)
print("2. CODE 3 (Vendor/Location) x CODE 4 교차 분석")
print("=" * 80)

# CODE 3가 vendor인지 location인지 구분
print("\n--- CODE 3별 CODE 4 패턴 ---")
for code3 in c3.index:
    subset = df1[df1['HVDC CODE 3'] == code3]
    c4_vals = subset['HVDC CODE 4'].value_counts()
    has_lease = 'Warehouse lease' in c4_vals.index if len(c4_vals) > 0 else False
    has_numbers = any(str(v).isdigit() for v in c4_vals.index if pd.notna(v))
    
    print(f"\n  {code3} ({len(subset)}건):")
    print(f"    CODE 4 종류: {len(c4_vals)}")
    print(f"    Warehouse lease: {'YES' if has_lease else 'NO'}")
    print(f"    숫자(아이템번호): {'YES' if has_numbers else 'NO'}")
    print(f"    TOTAL 합계: {subset['TOTAL'].sum():,.2f}")
    print(f"    Amount 합계: {subset['Amount'].sum():,.2f}")
    print(f"    Sqm 합계: {subset['Sqm'].sum():,.2f}")
    if len(c4_vals) <= 5:
        print(f"    CODE 4 값: {dict(c4_vals)}")

print()
print("=" * 80)
print("3. Vendor별 비용 집계 (HE, SCT, SIM 등)")
print("=" * 80)

vendor_codes = ['HE', 'SCT', 'SIM', 'SKM', 'ALS', 'SEI', 'PPL', 'ALM', 'SAS', 'NIE', 'EDG', 'ISO']
location_codes = ['DSV Indoor', 'DSV Outdoor', 'DSV Al Markaz', 'DSV MZP', 'MOSB', 
                  'Hauler Indoor', 'DHL WH', 'AAA Storage', 'Port Handling', 'Port Pass']

print("\n--- Vendor 코드별 (Handling 중심) ---")
for vc in vendor_codes:
    sub = df1[df1['HVDC CODE 3'] == vc]
    if len(sub) > 0:
        print(f"  {vc:>15}: {len(sub):>4}건  TOTAL={sub['TOTAL'].sum():>12,.2f}  Amount={sub['Amount'].sum():>12,.2f}  Sqm={sub['Sqm'].sum():>10,.2f}")

print("\n--- Location 코드별 (Storage 중심) ---")
for lc in location_codes:
    sub = df1[df1['HVDC CODE 3'] == lc]
    if len(sub) > 0:
        print(f"  {lc:>15}: {len(sub):>4}건  TOTAL={sub['TOTAL'].sum():>12,.2f}  Amount={sub['Amount'].sum():>12,.2f}  Sqm={sub['Sqm'].sum():>10,.2f}")

print()
print("=" * 80)
print("4. Vendor별 Handling 비용 상세 (HE/SCT/SIM)")
print("=" * 80)

handling_cols = ['Handling In', 'Handling out', 'Unstuffing', 'Stuffing', 'folk lift', 'crane']
for vc in ['HE', 'SCT', 'SIM']:
    sub = df1[df1['HVDC CODE 3'] == vc]
    if len(sub) == 0:
        continue
    print(f"\n--- {vc} ({len(sub)}건) ---")
    print(f"  TOTAL: {sub['TOTAL'].sum():,.2f}")
    for hc in handling_cols:
        if hc in sub.columns:
            val = sub[hc].sum()
            if val > 0:
                print(f"  {hc}: {val:,.2f}")
    
    # Category 분포
    print(f"  Category: {dict(sub['Category'].value_counts())}")
    print(f"  IN AND OUT: {dict(sub['IN AND OUT'].value_counts())}")

print()
print("=" * 80)
print("5. JSON 행 레이블과 wh payment CODE 3 대조")
print("=" * 80)

with open(u'행 레이블 WH 기성 HVDC STATUS 입고로직 전체 입고로직(FLO.json', 'r', encoding='utf-8') as f:
    label_data = json.load(f)

print(f"\n{'label':<20} {'WH기성':>8} {'CODE3일치':>10} {'STATUS':>8} {'입고전체':>8}")
print("-" * 60)
for item in label_data:
    label = item['행 레이블']
    wh = item.get('WH 기성') or 0
    st = item.get('HVDC STATUS') or 0
    logic = item.get('입고로직 전체') or 0
    
    # Match with CODE 3
    c3_match = len(df1[df1['HVDC CODE 3'] == label])
    # Also check CODE 1
    c1_match = len(df1[df1['HVDC CODE 1'] == label])
    match_str = f"{c3_match}" if c3_match > 0 else f"(C1:{c1_match})" if c1_match > 0 else "0"
    
    print(f"{label:<20} {wh:>8} {match_str:>10} {st:>8} {logic:>8}")

print()
print("=" * 80)
print("6. 전체 비용 구조 요약")
print("=" * 80)

# Warehouse lease vs item handling
lease = df1[df1['HVDC CODE 4'].astype(str).str.contains('Warehouse|lease', case=False, na=False)]
non_lease = df1[~df1.index.isin(lease.index)]

print(f"\n[A] Warehouse Lease (Storage): {len(lease)}건")
print(f"    TOTAL: {lease['TOTAL'].sum():,.2f}")
print(f"    Amount: {lease['Amount'].sum():,.2f}")

print(f"\n[B] Non-Lease (Handling 등): {len(non_lease)}건")
print(f"    TOTAL: {non_lease['TOTAL'].sum():,.2f}")

# Non-lease by CODE 3
print(f"\n    Non-Lease CODE 3 분포:")
nl_by_c3 = non_lease.groupby('HVDC CODE 3')['TOTAL'].agg(['sum','count']).sort_values('sum', ascending=False)
for idx, row in nl_by_c3.iterrows():
    print(f"      {idx:>20}: {row['count']:>4}건  TOTAL={row['sum']:>12,.2f}")

# Grand total
print(f"\n[전체] {len(df1)}건, TOTAL={df1['TOTAL'].sum():,.2f}")
