# scripts/forecasting/warehouse_forecast.py
"""
Warehouse Demand Forecasting Module

Provides functions for forecasting warehouse demand, capacity, and costs.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict
from datetime import datetime, timedelta

try:
    from scripts.forecasting.forecasting_service_adapter import ForecastService, ForecastResult
except ImportError:
    # Fallback for standalone execution
    from forecasting_service_adapter import ForecastService, ForecastResult


def forecast_warehouse_demand(
    historical_df: pd.DataFrame,
    cbm_col: str = "CBM",
    package_col: str = "Packages",
    date_col: str = "Date",
    horizon: int = 90,
    confidence: float = 0.90,
    rate_per_sqm: float = 47.0,
) -> Tuple[ForecastResult, ForecastResult, pd.DataFrame]:
    """
    예측 창고 수요 (CBM, Package, Cost)

    Args:
        historical_df: 과거 데이터 DataFrame
        cbm_col: CBM 컬럼명
        package_col: Package 컬럼명
        date_col: 날짜 컬럼명
        horizon: 예측 기간 (일)
        confidence: 신뢰구간 (0.0-1.0)
        rate_per_sqm: 제곱미터당 비용 (AED)

    Returns:
        (cbm_forecast, package_forecast, cost_forecast)
    """
    print(f"[INFO] Starting warehouse demand forecast (horizon={horizon} days)")

    # Initialize forecast service
    svc = ForecastService(model="auto", horizon=horizon, conf=confidence)

    # Prepare time series
    historical_df = historical_df.copy()
    historical_df[date_col] = pd.to_datetime(historical_df[date_col])
    historical_df = historical_df.sort_values(date_col).set_index(date_col)

    # CBM 예측
    print(f"[INFO] Forecasting CBM demand...")
    cbm_ts = historical_df[cbm_col].dropna()
    cbm_forecast = svc.fit_forecast(cbm_ts, freq="D")

    # Package 예측
    if package_col in historical_df.columns:
        print(f"[INFO] Forecasting package volume...")
        pkg_ts = historical_df[package_col].dropna()
        package_forecast = svc.fit_forecast(pkg_ts, freq="D")
    else:
        print(f"[WARN] Package column '{package_col}' not found, skipping package forecast")
        # Create dummy forecast
        package_forecast = ForecastResult(
            df=pd.DataFrame(
                {
                    "date": cbm_forecast.df["date"],
                    "yhat": np.nan,
                    "yhat_low": np.nan,
                    "yhat_high": np.nan,
                    "model": "N/A",
                    "mape": np.nan,
                    "rmse": np.nan,
                }
            )
        )

    # 비용 예측 (CBM 기반)
    print(f"[INFO] Calculating cost forecast...")
    cost_forecast = cbm_forecast.df.copy()
    cost_forecast["cost_forecast"] = cost_forecast["yhat"] * rate_per_sqm
    cost_forecast["cost_low"] = cost_forecast["yhat_low"] * rate_per_sqm
    cost_forecast["cost_high"] = cost_forecast["yhat_high"] * rate_per_sqm

    # Add confidence interval
    cost_forecast["confidence"] = confidence

    print(f"[OK] Forecast complete")
    print(f"  - CBM Forecast: {cbm_forecast.df['yhat'].mean():.2f} avg")
    print(f"  - Cost Forecast: {cost_forecast['cost_forecast'].mean():.2f} AED avg")

    return cbm_forecast, package_forecast, cost_forecast


def forecast_cost_by_period(
    historical_df: pd.DataFrame, start_date: str, end_date: str, rate_per_sqm: float = 47.0
) -> Dict[str, float]:
    """
    기간별 비용 예측

    Args:
        historical_df: 과거 데이터
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        rate_per_sqm: 제곱미터당 비용

    Returns:
        예측 통계 딕셔너리
    """
    print(f"[INFO] Forecasting cost for period {start_date} to {end_date}")

    # Calculate forecast horizon
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    horizon = (end - start).days

    # Get forecasts
    cbm_fc, pkg_fc, cost_fc = forecast_warehouse_demand(
        historical_df, horizon=horizon, rate_per_sqm=rate_per_sqm
    )

    # Filter by date range
    cost_filtered = cost_fc[(cost_fc["date"] >= start) & (cost_fc["date"] <= end)]

    # Calculate statistics
    stats = {
        "total_cost": cost_filtered["cost_forecast"].sum(),
        "avg_monthly_cost": cost_filtered["cost_forecast"].mean() * 30,
        "min_cost": cost_filtered["cost_low"].min(),
        "max_cost": cost_filtered["cost_high"].max(),
        "confidence": cost_filtered["confidence"].iloc[0] if len(cost_filtered) > 0 else 0.0,
    }

    print(f"[OK] Cost forecast complete")
    print(f"  - Total Cost: {stats['total_cost']:,.2f} AED")
    print(f"  - Avg Monthly: {stats['avg_monthly_cost']:,.2f} AED")

    return stats


def calculate_forecast_confidence(
    forecast_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    forecast_col: str = "yhat",
    actual_col: str = "actual",
) -> float:
    """
    예측 정확도 계산 (신뢰도)

    Args:
        forecast_df: 예측 결과 DataFrame
        actual_df: 실제 데이터 DataFrame
        forecast_col: 예측 컬럼명
        actual_col: 실제 컬럼명

    Returns:
        신뢰도 (0.0-1.0)
    """
    # Merge forecast and actual data
    merged = pd.merge(
        forecast_df[["date", forecast_col]],
        actual_df[[actual_col]],
        left_index=True,
        right_index=True,
        how="inner",
    )

    if len(merged) == 0:
        print("[WARN] No matching dates for confidence calculation")
        return 0.0

    # Calculate MAPE (Mean Absolute Percentage Error)
    mape = np.abs((merged[forecast_col] - merged[actual_col]) / merged[actual_col]).mean()

    # Convert to confidence (lower MAPE = higher confidence)
    confidence = max(0.0, min(1.0, 1.0 - mape))

    print(f"[INFO] Forecast confidence: {confidence:.2%} (MAPE: {mape:.2%})")

    return confidence


if __name__ == "__main__":
    # Test the module
    print("Testing warehouse forecast module...")

    # Create sample data
    dates = pd.date_range(start="2025-01-01", end="2025-10-01", freq="D")
    sample_df = pd.DataFrame(
        {
            "Date": dates,
            "CBM": np.random.randn(len(dates)).cumsum() + 1000,
            "Packages": np.random.randint(50, 200, len(dates)),
        }
    )

    # Run forecast
    cbm_fc, pkg_fc, cost_fc = forecast_warehouse_demand(sample_df, horizon=30)

    print(f"\nCBM Forecast:\n{cbm_fc.df.head()}")
    print(f"\nCost Forecast:\n{cost_fc.head()}")
    print("\nTest completed successfully!")
