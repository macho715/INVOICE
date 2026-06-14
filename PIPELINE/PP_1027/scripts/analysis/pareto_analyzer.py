# scripts/analysis/pareto_analyzer.py
"""
Pareto Analysis for Warehouse Aisle Optimization

Applies 80/20 law to identify priority aisles for optimization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path


def calculate_pareto_analysis(aisle_data: pd.DataFrame, threshold: float = 80.0) -> Dict:
    """
    Aisle별 Pareto 분석 수행

    Args:
        aisle_data: Aisle별 점유 데이터 (aisle, occupied_sqm, cap_sqm, utilization, over_cap)
        threshold: Pareto 임계값 (기본 80%)

    Returns:
        {
            'pareto_aisles': List[str],  # 상위 80% 기여 Aisle
            'cumulative_data': pd.DataFrame,  # 누적 데이터
            'top_utilization': float,  # 최고 활용률
            'recommendations': List[str]  # 권장사항
        }
    """
    print(f"[INFO] Calculating Pareto analysis (threshold={threshold}%)")

    # Filter for utilized aisles
    df = aisle_data[aisle_data["occupied_sqm"] > 0].copy()

    if len(df) == 0:
        print("[WARN] No utilized aisles found")
        return {
            "pareto_aisles": [],
            "cumulative_data": pd.DataFrame(),
            "top_utilization": 0.0,
            "recommendations": ["No utilized aisles to analyze"],
        }

    # Sort by occupied_sqm descending
    df_sorted = df.sort_values(by="occupied_sqm", ascending=False).reset_index(drop=True)

    # Calculate total occupied
    total_occupied = df_sorted["occupied_sqm"].sum()

    # Cumulative calculations
    df_sorted["cumulative_occupied"] = df_sorted["occupied_sqm"].cumsum()
    df_sorted["cumulative_percentage"] = (df_sorted["cumulative_occupied"] / total_occupied) * 100

    # Identify Pareto point (80% threshold)
    pareto_mask = df_sorted["cumulative_percentage"] <= threshold
    pareto_aisles = df_sorted[pareto_mask]["aisle"].tolist()

    # Get top utilization
    top_utilization = df_sorted["utilization"].max()

    # Generate recommendations
    recommendations = generate_optimization_recommendations(pareto_aisles, df_sorted, df, threshold)

    print(f"[OK] Pareto analysis complete")
    print(f"  - Pareto aisles: {', '.join(pareto_aisles)}")
    print(f"  - Top utilization: {top_utilization:.2f}%")

    return {
        "pareto_aisles": pareto_aisles,
        "cumulative_data": df_sorted,
        "top_utilization": top_utilization,
        "recommendations": recommendations,
    }


def generate_optimization_recommendations(
    pareto_aisles: List[str],
    df_sorted: pd.DataFrame,
    df_full: pd.DataFrame,
    threshold: float,
) -> List[str]:
    """
    Pareto 분석 기반 권장사항 생성

    Args:
        pareto_aisles: 상위 Aisle 리스트
        df_sorted: 정렬된 데이터
        df_full: 전체 데이터
        threshold: Pareto 임계값

    Returns:
        권장사항 리스트
    """
    recommendations = []

    # 1. 우선순위 Aisle 식별
    top_aisles_count = len(pareto_aisles)
    recommendations.append(
        f"🎯 Priority Aisles: {', '.join(pareto_aisles)} "
        f"({top_aisles_count} aisles account for {threshold}% of total occupancy)"
    )

    # 2. 초과 사용 경고
    over_cap_mask = (df_sorted["over_cap"] == True) | (df_sorted["utilization"] > 100)
    over_cap_aisles = df_sorted[over_cap_mask]["aisle"].tolist()

    if over_cap_aisles:
        max_over_cap = df_sorted["utilization"].max()
        recommendations.append(
            f"⚠️ Capacity Exceeded: {', '.join(over_cap_aisles)} "
            f"({max_over_cap:.1f}% utilization - immediate relocation required)"
        )

    # 3. 미사용 Aisle 활용
    unused_aisles = df_full[df_full["occupied_sqm"] == 0]["aisle"].tolist()
    if unused_aisles:
        unused_cap = df_full[df_full["occupied_sqm"] == 0]["cap_sqm"].sum()
        recommendations.append(
            f"💡 Available Capacity: {', '.join(unused_aisles)} "
            f"({unused_cap:.0f} ㎡ unused - consider long/heavy cargo relocation)"
        )

    # 4. 총합 요약
    total_occupied = df_sorted["occupied_sqm"].sum()
    total_capacity = df_full["cap_sqm"].sum()
    overall_utilization = (total_occupied / total_capacity) * 100 if total_capacity > 0 else 0

    recommendations.append(
        f"📊 Overall Status: {total_occupied:.0f} ㎡ used / {total_capacity:.0f} ㎡ capacity "
        f"({overall_utilization:.1f}% utilization)"
    )

    return recommendations


def calculate_aisle_occupancy(df_wh: pd.DataFrame) -> pd.DataFrame:
    """
    실시간 Aisle 점유율 계산

    Args:
        df_wh: 창고 데이터 (aisle_code, area_sqm 포함)

    Returns:
        Aisle별 점유율 DataFrame
    """
    print("[INFO] Calculating aisle occupancy from warehouse data")

    if "aisle_code" not in df_wh.columns or "area_sqm" not in df_wh.columns:
        print("[WARN] Required columns not found (aisle_code, area_sqm)")
        # Return default capacity structure
        return pd.DataFrame(
            {
                "aisle": [f"A{i}" for i in range(1, 9)],
                "occupied_sqm": [0.0] * 8,
                "cap_sqm": [396.0] * 8,
                "utilization": [0.0] * 8,
                "over_cap": [False] * 8,
            }
        )

    # Aggregate by aisle
    aisle_occupancy = (
        df_wh.groupby("aisle_code")
        .agg({"area_sqm": "sum", "aisle_code": "count"})
        .rename(columns={"aisle_code": "case_count"})
    )

    # Add capacity (396 ㎡ per aisle for A1-A8)
    aisle_occupancy["aisle"] = aisle_occupancy.index
    aisle_occupancy["cap_sqm"] = 396.0
    aisle_occupancy["utilization"] = (aisle_occupancy["area_sqm"] / 396.0) * 100
    aisle_occupancy["over_cap"] = aisle_occupancy["utilization"] > 100

    # Add case count
    aisle_occupancy["occupied_sqm"] = aisle_occupancy["area_sqm"]

    # Reset index for clean output
    aisle_occupancy = aisle_occupancy.reset_index(drop=True)[
        ["aisle", "occupied_sqm", "cap_sqm", "utilization", "over_cap", "case_count"]
    ]

    print(f"[OK] Aisle occupancy calculated: {len(aisle_occupancy)} aisles")

    return aisle_occupancy


if __name__ == "__main__":
    # Test the module
    print("Testing Pareto Analyzer module...")

    # Create sample data
    sample_data = pd.DataFrame(
        {
            "aisle": [f"A{i}" for i in range(1, 9)],
            "occupied_sqm": [534.5, 534.93, 526.42, 509.95, 530.98, 520.31, 0.0, 0.0],
            "cap_sqm": [396.0] * 8,
            "utilization": [134.97, 135.08, 132.93, 128.78, 134.09, 131.39, 0.0, 0.0],
            "over_cap": [True, True, True, True, True, True, False, False],
        }
    )

    # Run Pareto analysis
    result = calculate_pareto_analysis(sample_data, threshold=80.0)

    print(f"\nPareto Result:")
    print(f"  - Pareto Aisles: {result['pareto_aisles']}")
    print(f"  - Top Utilization: {result['top_utilization']:.2f}%")
    print(f"\nRecommendations:")
    for i, rec in enumerate(result["recommendations"], 1):
        print(f"  {i}. {rec}")

    print("\nTest completed successfully!")

