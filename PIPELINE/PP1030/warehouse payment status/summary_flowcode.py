import pandas as pd
import numpy as np

xl = pd.ExcelFile('HVDC_입고로직.xlsx')
df = pd.read_excel(xl, sheet_name=0)

fc = pd.to_numeric(df['FLOW_CODE'], errors='coerce')
target = df[fc.isin([2, 3, 4, 5])]

print(f"FLOW 2,3,4,5 total: {len(target)}")
print(f"  Flow 2 (Port-WH-Site): {(fc==2).sum()}")
print(f"  Flow 3 (Port-MOSB-Site): {(fc==3).sum()}")
print(f"  Flow 4 (Port-WH-MOSB-Site): {(fc==4).sum()}")
print(f"  Flow 5 (Mixed/Waiting): {(fc==5).sum()}")

wh_cols = ['DSV Indoor', 'DSV Outdoor', 'DSV Al Markaz', 'DSV MZP']
any_dsv = pd.Series(False, index=target.index)
for c in wh_cols:
    any_dsv = any_dsv | target[c].notna()

print(f"\nDSV 4 warehouse 중 하나 이상 거친: {any_dsv.sum()}")
print(f"DSV 안 거침 (FLOW 2,3,4,5 중): {(~any_dsv).sum()}")

# FLOW 3 goes to MOSB, not DSV
no_dsv = target[~any_dsv]
print(f"\nDSV 안 거친 아이템 FLOW 분포:")
print(no_dsv['FLOW_CODE'].value_counts().sort_index())
print(f"MOSB 날짜 있음: {no_dsv['MOSB'].notna().sum()}")

print(f"\n--- DSV 창고별 아이템 수 ---")
for c in wh_cols:
    print(f"  {c}: {target[c].notna().sum()}")

dsv_count = sum(target[c].notna().astype(int) for c in wh_cols)
print(f"\n--- DSV 창고 중복 ---")
print(f"  0개: {(dsv_count==0).sum()}")
print(f"  1개만: {(dsv_count==1).sum()}")
print(f"  2개 이상: {(dsv_count>=2).sum()}")

# Storage cost target: DSV 4 warehouses
# Only items that actually entered a DSV warehouse
dsv_items = target[any_dsv]
print(f"\n=== Storage 비용 배분 대상 ===")
print(f"DSV 창고 거친 아이템: {len(dsv_items)}")
print(f"Source_Vendor: {dict(dsv_items['Source_Vendor'].value_counts())}")

# Handling cost: all FLOW 2,3,4,5
print(f"\n=== Handling 비용 대상 ===")
print(f"FLOW 2,3,4,5 전체: {len(target)}")

# MOSB-only items (FLOW 3 + some FLOW 4/5)
mosb_only = target[(~any_dsv) & target['MOSB'].notna()]
print(f"\nMOSB만 거친 (DSV 없음): {len(mosb_only)}")
