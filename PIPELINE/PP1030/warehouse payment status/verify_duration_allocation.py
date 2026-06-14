import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 70)
print("1. wh payment.xlsx - 월별 창고비용 확인")
print("=" * 70)

xl_pay = pd.ExcelFile('wh payment.xlsx')
df_pay = pd.read_excel(xl_pay, sheet_name=1)

print(f"총 레코드: {len(df_pay)}")
print(f"총 Amount (Storage): {df_pay['Amount'].sum():,.2f}")
print(f"총 TOTAL (All costs): {df_pay['TOTAL'].sum():,.2f}")
print()

monthly_cost = df_pay.groupby('Operation Month').agg({
    'Amount': 'sum',
    'TOTAL': 'sum',
    'Sqm': 'sum',
    'S No.': 'count'
}).rename(columns={'S No.': 'record_count'})
monthly_cost = monthly_cost.sort_index()
print("월별 비용 집계:")
print(monthly_cost.to_string())
print()

print("=" * 70)
print("2. HVDC_입고로직.xlsx - 아이템별 체류기간 확인")
print("=" * 70)

xl_logic = pd.ExcelFile('HVDC_입고로직.xlsx')
sheets = xl_logic.sheet_names
print(f"시트 목록: {sheets}")
print()

df_total = pd.read_excel(xl_logic, sheet_name=0)
print(f"total data 시트: {len(df_total)}건, {len(df_total.columns)}컬럼")
print(f"컬럼 목록:")
for i, col in enumerate(df_total.columns):
    print(f"  {i}: {col}")
print()

duration_cols = [c for c in df_total.columns if 'duration' in str(c).lower() or 'first' in str(c).lower() or 'last' in str(c).lower() or 'in wh' in str(c).lower() or 'out wh' in str(c).lower()]
print(f"체류기간 관련 컬럼: {duration_cols}")
print()

for col in duration_cols:
    non_null = df_total[col].notna().sum()
    print(f"  {col}: {non_null}/{len(df_total)} non-null ({non_null/len(df_total)*100:.1f}%)")
print()

if 'total duration' in df_total.columns:
    dur_col = 'total duration'
elif 'Total Duration' in df_total.columns:
    dur_col = 'Total Duration'
else:
    dur_col = [c for c in df_total.columns if 'duration' in str(c).lower()]
    dur_col = dur_col[0] if dur_col else None

if dur_col:
    print(f"체류기간 컬럼 ({dur_col}) 통계:")
    dur_data = pd.to_numeric(df_total[dur_col], errors='coerce')
    print(f"  non-null: {dur_data.notna().sum()}")
    print(f"  평균: {dur_data.mean():.1f}일")
    print(f"  중위수: {dur_data.median():.1f}일")
    print(f"  최소: {dur_data.min()}")
    print(f"  최대: {dur_data.max()}")
    print(f"  합계: {dur_data.sum():,.0f} item-days")
print()

first_in_col = [c for c in df_total.columns if 'first' in str(c).lower() and 'wh' in str(c).lower()]
last_out_col = [c for c in df_total.columns if 'last' in str(c).lower() and 'wh' in str(c).lower()]
print(f"first in wh 컬럼: {first_in_col}")
print(f"last out wh 컬럼: {last_out_col}")

if first_in_col and last_out_col:
    fi_col = first_in_col[0]
    lo_col = last_out_col[0]
    df_total[fi_col] = pd.to_datetime(df_total[fi_col], errors='coerce')
    df_total[lo_col] = pd.to_datetime(df_total[lo_col], errors='coerce')

    has_dates = df_total[fi_col].notna() & df_total[lo_col].notna()
    print(f"\n입출고일 모두 있는 아이템: {has_dates.sum()}건")

    df_with_dates = df_total[has_dates].copy()

    print(f"\n입고일 범위: {df_with_dates[fi_col].min()} ~ {df_with_dates[fi_col].max()}")
    print(f"출고일 범위: {df_with_dates[lo_col].min()} ~ {df_with_dates[lo_col].max()}")

print()
print("=" * 70)
print("3. 아이템-월별 체류 산정 시뮬레이션")
print("=" * 70)

if first_in_col and last_out_col:
    fi_col = first_in_col[0]
    lo_col = last_out_col[0]
    df_sim = df_total[df_total[fi_col].notna() & df_total[lo_col].notna()].copy()

    vendor_col = 'Source_Vendor' if 'Source_Vendor' in df_sim.columns else None

    months = pd.period_range('2024-01', '2026-01', freq='M')
    monthly_item_days = {}

    for month in months:
        m_start = month.start_time
        m_end = month.end_time

        in_wh = (df_sim[fi_col] <= m_end) & (df_sim[lo_col] >= m_start)
        items_in_month = df_sim[in_wh]

        stay_start = items_in_month[fi_col].clip(lower=m_start)
        stay_end = items_in_month[lo_col].clip(upper=m_end)
        days = (stay_end - stay_start).dt.days + 1
        days = days.clip(lower=0)

        total_item_days = days.sum()
        item_count = len(items_in_month)
        monthly_item_days[str(month)] = {
            'item_count': item_count,
            'total_item_days': total_item_days,
            'avg_days': days.mean() if item_count > 0 else 0
        }

    df_monthly_items = pd.DataFrame(monthly_item_days).T
    df_monthly_items.index.name = 'month'
    print("\n월별 창고 체류 아이템 현황:")
    print(df_monthly_items.to_string())
    print()

    print("=" * 70)
    print("4. 비용 배분 시뮬레이션: 전체비용 / 전체 item-days → 일단가")
    print("=" * 70)

    total_cost = df_pay['TOTAL'].sum()
    total_amount = df_pay['Amount'].sum()
    total_item_days_all = df_monthly_items['total_item_days'].sum()

    print(f"\n총 TOTAL 비용: {total_cost:,.2f}")
    print(f"총 Amount 비용: {total_amount:,.2f}")
    print(f"전체 item-days: {total_item_days_all:,.0f}")

    if total_item_days_all > 0:
        cost_per_item_day_total = total_cost / total_item_days_all
        cost_per_item_day_amount = total_amount / total_item_days_all
        print(f"\n일단가 (TOTAL 기준): {cost_per_item_day_total:,.4f} / item-day")
        print(f"일단가 (Amount 기준): {cost_per_item_day_amount:,.4f} / item-day")
    print()

    print("=" * 70)
    print("5. 월별 교차검증: 배분합 vs 실제비용")
    print("=" * 70)

    monthly_cost_reset = monthly_cost.reset_index()
    monthly_cost_reset.columns = ['month', 'Amount', 'TOTAL', 'Sqm', 'record_count']

    print(f"\n{'month':<10} {'actual_TOTAL':>14} {'item_days':>12} {'allocated':>14} {'diff%':>8}")
    print("-" * 62)

    for idx, row in monthly_cost_reset.iterrows():
        m = str(row['month'])
        actual = row['TOTAL']
        m_key = m[:7] if len(m) >= 7 else m

        item_days = 0
        for k, v in monthly_item_days.items():
            if k == m_key:
                item_days = v['total_item_days']
                break

        if total_item_days_all > 0 and item_days > 0:
            allocated = total_cost * (item_days / total_item_days_all)
            diff_pct = (allocated - actual) / actual * 100 if actual != 0 else 0
            print(f"{m_key:<10} {actual:>14,.2f} {item_days:>12,.0f} {allocated:>14,.2f} {diff_pct:>7.1f}%")
        else:
            print(f"{m_key:<10} {actual:>14,.2f} {item_days:>12,.0f} {'N/A':>14} {'N/A':>8}")

    print()
    print("=" * 70)
    print("6. 월별 단가 방식: 해당월 비용 / 해당월 item-days")
    print("=" * 70)
    print(f"\n{'month':<10} {'actual_TOTAL':>14} {'item_days':>12} {'daily_rate':>12} {'items':>8}")
    print("-" * 60)

    for idx, row in monthly_cost_reset.iterrows():
        m = str(row['month'])
        actual = row['TOTAL']
        m_key = m[:7] if len(m) >= 7 else m

        item_days = 0
        item_count = 0
        for k, v in monthly_item_days.items():
            if k == m_key:
                item_days = v['total_item_days']
                item_count = v['item_count']
                break

        if item_days > 0:
            daily_rate = actual / item_days
            print(f"{m_key:<10} {actual:>14,.2f} {item_days:>12,.0f} {daily_rate:>12,.4f} {item_count:>8}")
        else:
            print(f"{m_key:<10} {actual:>14,.2f} {item_days:>12,.0f} {'N/A':>12} {item_count:>8}")
