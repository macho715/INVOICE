# scripts/analysis/warehouse_analysis_functions.py
"""
Warehouse Analysis Functions

Core functions for analyzing warehouse operations, costs, and efficiency.
Extracted from ANALYSE1.ipynb and ANALYSE2.ipynb.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


def calculate_warehouse_transition_plan(
    df: pd.DataFrame, start_month: str, end_month: str, rate_per_sqm: float = 47.0
) -> pd.DataFrame:
    """
    창고 전환 계획 계산 (ANALYSE1 로직)

    Args:
        df: 월별 데이터 DataFrame
        start_month: 시작 월 (YYYY-MM)
        end_month: 종료 월 (YYYY-MM)
        rate_per_sqm: 제곱미터당 비용 (AED)

    Returns:
        월별 전환 계획 DataFrame
    """
    print(f"[INFO] Calculating warehouse transition plan from {start_month} to {end_month}")

    # Create date range
    start = pd.to_datetime(start_month)
    end = pd.to_datetime(end_month)
    months = pd.date_range(start=start, end=end, freq="MS")  # Month Start

    # Initialize plan
    plan = pd.DataFrame(index=months)

    # Define warehouse transitions (based on ANALYSE1 logic)
    # M44-INDOOR: 3000 → 2500 → 2000 → 1500 → 1000
    # MARKAZ-INDOOR: 0 → 0 → 3000 → 2000 → 1500 → 1000
    # MW4-INDOOR: 0 → 0 → 0 → 5000 → 4500 → 4000 → ...

    transition_logic = {
        "M44-INDOOR": lambda m: (
            3000
            if m <= pd.to_datetime("2025-04-30")
            else (
                2500
                if m <= pd.to_datetime("2025-08-31")
                else 2000 if m <= pd.to_datetime("2025-11-30") else 1500
            )
        ),
        "MARKAZ-INDOOR": lambda m: (
            0
            if m <= pd.to_datetime("2025-04-30")
            else (
                3000
                if m <= pd.to_datetime("2025-05-31")
                else 2000 if m <= pd.to_datetime("2025-10-31") else 1500
            )
        ),
        "MW4-INDOOR": lambda m: (
            0
            if m <= pd.to_datetime("2025-05-31")
            else (
                5000
                if m <= pd.to_datetime("2025-06-30")
                else (
                    4500
                    if m <= pd.to_datetime("2025-07-31")
                    else 4000 if m <= pd.to_datetime("2025-08-31") else 3500
                )
            )
        ),
    }

    for wh_name, logic in transition_logic.items():
        plan[wh_name] = [logic(m) for m in months]

    # Calculate totals
    plan["TOTAL_SQM"] = plan["M44-INDOOR"] + plan["MARKAZ-INDOOR"] + plan["MW4-INDOOR"]
    plan["MONTHLY_COST_AED"] = plan["TOTAL_SQM"] * rate_per_sqm

    # Add month labels
    plan["Month"] = plan.index.strftime("%b-%y")

    print(f"[OK] Transition plan calculated: {len(plan)} months")
    print(f"  - Total cost: {plan['MONTHLY_COST_AED'].sum():,.0f} AED")
    print(f"  - Avg monthly cost: {plan['MONTHLY_COST_AED'].mean():,.0f} AED")

    return plan


def analyze_cost_efficiency(
    df: pd.DataFrame,
    sqm_col: str = "TOTAL_SQM",
    cost_col: str = "MONTHLY_COST_AED",
    rate_per_sqm: float = 47.0,
) -> Dict[str, float]:
    """
    비용 효율성 분석

    Args:
        df: 월별 데이터 DataFrame
        sqm_col: 면적 컬럼명
        cost_col: 비용 컬럼명
        rate_per_sqm: 제곱미터당 비용

    Returns:
        비용 효율성 통계
    """
    print(f"[INFO] Analyzing cost efficiency")

    if cost_col not in df.columns and sqm_col in df.columns:
        df[cost_col] = df[sqm_col] * rate_per_sqm

    stats = {
        "avg_monthly_cost": df[cost_col].mean(),
        "total_cost": df[cost_col].sum(),
        "min_monthly_cost": df[cost_col].min(),
        "max_monthly_cost": df[cost_col].max(),
        "cost_per_sqm": (
            df[cost_col].sum() / df[sqm_col].sum() if df[sqm_col].sum() > 0 else rate_per_sqm
        ),
        "efficiency_score": (
            min(
                100.0,
                100.0 * (1.0 - (df[cost_col].mean() - df[cost_col].min()) / df[cost_col].mean()),
            )
            if df[cost_col].mean() > 0
            else 100.0
        ),
    }

    print(f"[OK] Cost efficiency analysis complete")
    print(f"  - Avg monthly cost: {stats['avg_monthly_cost']:,.2f} AED")
    print(f"  - Total cost: {stats['total_cost']:,.2f} AED")
    print(f"  - Efficiency score: {stats['efficiency_score']:.2f}%")

    return stats


def compare_indoor_outdoor(
    df: pd.DataFrame,
    indoor_col: str = "INDOOR CBM",
    outdoor_col: str = "OUTDOOR CBM",
    date_col: str = "Date",
) -> Dict[str, float]:
    """
    Indoor vs Outdoor 창고 비교 (ANALYSE1 로직)

    Args:
        df: 데이터 DataFrame
        indoor_col: Indoor 컬럼명
        outdoor_col: Outdoor 컬럼명
        date_col: 날짜 컬럼명

    Returns:
        비교 통계
    """
    print(f"[INFO] Comparing indoor vs outdoor warehouses")

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # Calculate statistics
    indoor_stats = {
        "avg": df[indoor_col].mean(),
        "max": df[indoor_col].max(),
        "min": df[indoor_col].min(),
        "std": df[indoor_col].std(),
        "trend": "increasing" if df[indoor_col].iloc[-1] > df[indoor_col].iloc[0] else "decreasing",
    }

    outdoor_stats = {
        "avg": df[outdoor_col].mean(),
        "max": df[outdoor_col].max(),
        "min": df[outdoor_col].min(),
        "std": df[outdoor_col].std(),
        "trend": (
            "increasing" if df[outdoor_col].iloc[-1] > df[outdoor_col].iloc[0] else "decreasing"
        ),
    }

    comparison = {
        "indoor_avg": indoor_stats["avg"],
        "outdoor_avg": outdoor_stats["avg"],
        "avg_difference_pct": (
            ((outdoor_stats["avg"] - indoor_stats["avg"]) / indoor_stats["avg"] * 100)
            if indoor_stats["avg"] > 0
            else 0
        ),
        "indoor_trend": indoor_stats["trend"],
        "outdoor_trend": outdoor_stats["trend"],
        "utilization_ratio": (
            outdoor_stats["avg"] / indoor_stats["avg"] if indoor_stats["avg"] > 0 else 0
        ),
    }

    print(f"[OK] Comparison complete")
    print(f"  - Indoor avg: {indoor_stats['avg']:.2f}")
    print(f"  - Outdoor avg: {outdoor_stats['avg']:.2f}")
    print(f"  - Difference: {comparison['avg_difference_pct']:.2f}%")

    return comparison


def calculate_sqm_utilization(
    df: pd.DataFrame, total_cases: int, total_sqm: float, usable_capacity: float
) -> Dict[str, float]:
    """
    SQM 활용률 계산 (대시보드용)

    Args:
        df: 데이터 DataFrame
        total_cases: 총 케이스 수
        total_sqm: 사용 중인 총 SQM
        usable_capacity: 사용 가능한 SQM 용량

    Returns:
        활용률 통계
    """
    utilization_pct = (total_sqm / usable_capacity) * 100 if usable_capacity > 0 else 0
    remaining_sqm = usable_capacity - total_sqm

    stats = {
        "total_sqm": total_sqm,
        "usable_capacity": usable_capacity,
        "utilization_pct": utilization_pct,
        "remaining_sqm": remaining_sqm,
        "cases_per_sqm": total_cases / total_sqm if total_sqm > 0 else 0,
    }

    return stats


if __name__ == "__main__":
    # Test the module
    print("Testing warehouse analysis functions...")

    # Create sample data
    months = pd.date_range(start="2025-01-01", end="2026-01-01", freq="MS")
    sample_df = pd.DataFrame(
        {
            "Month": months,
            "M44-INDOOR": 3000,
            "MARKAZ-INDOOR": 2000,
            "MW4-INDOOR": 5000,
            "TOTAL_SQM": 10000,
            "MONTHLY_COST_AED": 470000,
        }
    )

    # Test transition plan
    plan = calculate_warehouse_transition_plan(sample_df, "2025-01-01", "2026-01-01")
    print(f"\nTransition Plan:\n{plan.head()}")

    # Test cost efficiency
    efficiency = analyze_cost_efficiency(plan)
    print(f"\nCost Efficiency: {efficiency}")

    print("\nTest completed successfully!")
