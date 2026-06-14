# scripts/forecasting/__init__.py
"""
Forecasting Module for HVDC Pipeline

This module provides time series forecasting capabilities for warehouse operations,
including demand prediction, cost forecasting, and capacity planning.
"""

try:
    from scripts.forecasting.forecasting_service_adapter import ForecastService, ForecastResult
    from scripts.forecasting.warehouse_forecast import (
        forecast_warehouse_demand,
        forecast_cost_by_period,
        calculate_forecast_confidence
    )

    __all__ = [
        "ForecastService",
        "ForecastResult",
        "forecast_warehouse_demand",
        "forecast_cost_by_period",
        "calculate_forecast_confidence",
    ]
except ImportError:
    # Fallback for standalone execution
    from forecasting_service_adapter import ForecastService, ForecastResult
    from warehouse_forecast import (
        forecast_warehouse_demand,
        forecast_cost_by_period,
        calculate_forecast_confidence
    )

    __all__ = [
        "ForecastService",
        "ForecastResult",
        "forecast_warehouse_demand",
        "forecast_cost_by_period",
        "calculate_forecast_confidence",
    ]

