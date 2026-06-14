import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 100)

xl = pd.ExcelFile('HVDC_입고로직.xlsx')
df = pd.read_excel(xl, sheet_name=0)

print("=" * 80)
print("A. FLOW_CODE 분포")
print("=" * 80)

print(f"\nFLOW_CODE 컬럼 타입: {df['FLOW_CODE'].dtype}")
print(f"FLOW_CODE non-null: {df['FLOW_CODE'].notna().sum()}")
print()

print("--- FLOW_CODE 값 분포 ---")
print(df['FLOW_CODE'].value_counts().sort_index())
print()

print("--- FLOW_DESCRIPTION 분포 ---")
print(df['FLOW_DESCRIPTION'].value_counts())
print()

# FLOW CODE vs warehouse columns
wh_dsv_cols = ['DSV Indoor', 'DSV Outdoor', 'DSV Al Markaz', 'DSV MZP']

print("=" * 80)
print("B. FLOW_CODE별 DSV 창고 체류 현황")
print("=" * 80)

for fc in sorted(df['FLOW_CODE'].dropna().unique()):
    subset = df[df['FLOW_CODE'] == fc]
    desc = subset['FLOW_DESCRIPTION'].iloc[0] if len(subset) > 0 else ''
    
    wh_counts = {}
    for col in wh_dsv_cols:
        if col in subset.columns:
            wh_counts[col] = subset[col].notna().sum()
    
    has_first_in = subset['first in wh'].notna().sum()
    has_last_out = subset['last out wh'].notna().sum()
    
    print(f"\nFLOW {fc} ({desc}): {len(subset)}건")
    print(f"  first in wh: {has_first_in}, last out wh: {has_last_out}")
    for col, cnt in wh_counts.items():
        if cnt > 0:
            print(f"  {col}: {cnt}")

print()
print("=" * 80)
print("C. FLOW CODE 2,3,4,5만 필터링")
print("=" * 80)

target_flows = [2, 3, 4, 5]
# Handle both numeric and string types
fc_numeric = pd.to_numeric(df['FLOW_CODE'], errors='coerce')
df_target = df[fc_numeric.isin(target_flows)]

print(f"\nFLOW CODE 2,3,4,5 아이템: {len(df_target)}건")
print(f"Source_Vendor 분포:")
print(df_target['Source_Vendor'].value_counts())
print()

# DSV warehouse presence
for col in wh_dsv_cols:
    if col in df_target.columns:
        nn = df_target[col].notna().sum()
        print(f"  {col}: {nn}건 ({nn/len(df_target)*100:.1f}%)")
print()

# first in wh / last out wh
has_dates = df_target['first in wh'].notna() & df_target['last out wh'].notna()
print(f"first in wh + last out wh 있는 아이템: {has_dates.sum()}/{len(df_target)}")
print()

# Check: items with DSV warehouse date but NO first in wh
for col in wh_dsv_cols:
    if col in df_target.columns:
        has_wh = df_target[col].notna()
        no_first = df_target['first in wh'].isna()
        both = (has_wh & no_first).sum()
        if both > 0:
            print(f"  {col} 날짜 있으나 first in wh 없음: {both}건")

print()
print("=" * 80)
print("D. FLOW CODE 2,3,4,5 아이템의 창고별 월별 체류일 시뮬레이션")
print("=" * 80)

months = pd.period_range('2024-01', '2026-01', freq='M')

for wh_col in wh_dsv_cols:
    if wh_col not in df_target.columns:
        continue
    
    # Items that passed through this warehouse
    wh_items = df_target[df_target[wh_col].notna()].copy()
    if len(wh_items) == 0:
        continue
    
    wh_date = pd.to_datetime(wh_items[wh_col], errors='coerce')
    wh_items['_wh_date'] = wh_date
    
    # For duration: need entry and exit date for THIS specific warehouse
    # wh_col date = entry date to this warehouse
    # Need to find when item LEFT this warehouse
    # Check: what other columns might indicate exit?
    
    print(f"\n--- {wh_col} ---")
    print(f"  총 아이템: {len(wh_items)}건")
    print(f"  입고일 범위: {wh_date.min()} ~ {wh_date.max()}")
    
    # Check: do items have dates in subsequent warehouses?
    # The warehouse columns seem to be entry dates for each location
    # Let's check the sequence for a few items
    print(f"\n  샘플 아이템 경로 (상위 5):")
    all_loc_cols = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'AAA Storage',
                    'DSV Outdoor', 'DSV MZP', 'MOSB', 'Hauler Indoor',
                    'JDN MZD', 'Shifting', 'MIR', 'SHU', 'DAS', 'AGI']
    
    for idx in wh_items.head(5).index:
        row = df_target.loc[idx]
        case_no = row.get('Case No.', 'N/A')
        sct = row.get('SCT Ref.No', 'N/A')
        path = []
        for loc in all_loc_cols:
            if loc in row.index and pd.notna(row[loc]):
                dt = pd.to_datetime(row[loc], errors='coerce')
                if pd.notna(dt):
                    path.append(f"{loc}({dt.strftime('%Y-%m-%d')})")
        fi = row.get('first in wh', '')
        lo = row.get('last out wh', '')
        dur = row.get('total duration', '')
        print(f"    Case {case_no} | {sct}")
        print(f"      경로: {' → '.join(path)}")
        print(f"      first in: {fi}, last out: {lo}, duration: {dur}")

print()
print("=" * 80)
print("E. 창고 체류기간 산정 방법 확인")
print("=" * 80)

# For each DSV warehouse, calculate item-days per month
# Entry = warehouse date column, Exit = next location date or last out wh
print("\nDSV 창고별 체류기간 산정:")

for wh_col in wh_dsv_cols:
    if wh_col not in df_target.columns:
        continue
    
    wh_items = df_target[df_target[wh_col].notna()].copy()
    if len(wh_items) == 0:
        continue
    
    wh_items['_entry'] = pd.to_datetime(wh_items[wh_col], errors='coerce')
    
    # Find exit: earliest date AFTER this warehouse's date among subsequent locations
    all_loc_cols_ordered = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'AAA Storage',
                            'DSV Outdoor', 'DSV MZP', 'MOSB', 'Hauler Indoor',
                            'JDN MZD', 'Shifting', 'MIR', 'SHU', 'DAS', 'AGI']
    
    exit_dates = []
    for idx, row in wh_items.iterrows():
        entry = row['_entry']
        if pd.isna(entry):
            exit_dates.append(pd.NaT)
            continue
        
        # Find next location date after entry
        next_date = pd.NaT
        for loc in all_loc_cols_ordered:
            if loc == wh_col:
                continue
            if loc in row.index and pd.notna(row[loc]):
                loc_date = pd.to_datetime(row[loc], errors='coerce')
                if pd.notna(loc_date) and loc_date > entry:
                    if pd.isna(next_date) or loc_date < next_date:
                        next_date = loc_date
        
        # Fallback to last out wh
        if pd.isna(next_date) and pd.notna(row.get('last out wh')):
            lo = pd.to_datetime(row['last out wh'], errors='coerce')
            if pd.notna(lo) and lo >= entry:
                next_date = lo
        
        exit_dates.append(next_date)
    
    wh_items['_exit'] = exit_dates
    
    has_both = wh_items['_entry'].notna() & wh_items['_exit'].notna()
    wh_valid = wh_items[has_both].copy()
    wh_valid['_days'] = (wh_valid['_exit'] - wh_valid['_entry']).dt.days
    
    print(f"\n{wh_col}:")
    print(f"  총 아이템: {len(wh_items)}, entry+exit 있음: {len(wh_valid)}")
    if len(wh_valid) > 0:
        print(f"  체류일 통계: 평균 {wh_valid['_days'].mean():.1f}, 중위수 {wh_valid['_days'].median():.1f}, 최소 {wh_valid['_days'].min()}, 최대 {wh_valid['_days'].max()}")
        print(f"  총 item-days: {wh_valid['_days'].sum():,.0f}")
        
        # Monthly breakdown
        print(f"\n  월별 item-days:")
        for month in months:
            m_start = month.start_time
            m_end = month.end_time
            
            in_wh = (wh_valid['_entry'] <= m_end) & (wh_valid['_exit'] >= m_start)
            items_in_month = wh_valid[in_wh]
            
            if len(items_in_month) > 0:
                stay_start = items_in_month['_entry'].clip(lower=m_start)
                stay_end = items_in_month['_exit'].clip(upper=m_end)
                days = (stay_end - stay_start).dt.days + 1
                days = days.clip(lower=0)
                print(f"    {month}: items={len(items_in_month)}, item-days={days.sum():,.0f}")
    
    no_exit = wh_items['_exit'].isna().sum()
    if no_exit > 0:
        print(f"  [!] exit 날짜 없음 (아직 재고?): {no_exit}건")
