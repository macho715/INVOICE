#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSV AL MARKAZ – ULTIMATE DASHBOARD: FLOW + SQM + STACKING + DWELL + TURNOVER

통합 대시보드: 흐름, SQM, 적재율, 체류시간, 재고회전율 분석

Usage:
    python dsv_almarkaz_ultimate_dashboard.py [--input <path>] [--output <path>]
"""

import argparse
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import sys

# Add parent directory to path for forecasting module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.forecasting.warehouse_forecast import forecast_warehouse_demand
except ImportError:
    print("[WARN] Forecasting module not available, forecast features disabled")
    forecast_warehouse_demand = None

try:
    from pareto_analyzer import calculate_pareto_analysis, calculate_aisle_occupancy
except ImportError:
    try:
        from scripts.analysis.pareto_analyzer import (
            calculate_pareto_analysis,
            calculate_aisle_occupancy,
        )
    except ImportError:
        print("[WARN] Pareto analyzer not available, Pareto features disabled")
        calculate_pareto_analysis = None
        calculate_aisle_occupancy = None


def load_data(input_path, sheet_name="Case List, RIL", aisle_map_path=None):
    """데이터 로드 및 전처리"""
    print(f"[INFO] Loading data from: {input_path}")
    df = pd.read_excel(input_path, sheet_name=sheet_name, engine="openpyxl")

    # 날짜 컬럼 변환 - 모든 Date/시간 관련 컬럼
    date_cols = [
        col
        for col in df.columns
        if any(
            x in col.lower()
            for x in [
                "date",
                "etd",
                "eta",
                "dhl",
                "dsv",
                "aaa",
                "hauler",
                "mosb",
                "mir",
                "shu",
                "das",
                "agi",
            ]
        )
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Aisle Map 통합
    if aisle_map_path and Path(aisle_map_path).exists():
        print(f"[INFO] Loading Aisle Map from: {aisle_map_path}")
        aisle_df = pd.read_csv(aisle_map_path)

        # Case No. 컬럼 찾기
        case_col = None
        for col in df.columns:
            if "case" in col.lower() and "no" in col.lower():
                case_col = col
                break

        if case_col:
            # case_key를 문자열로 변환
            aisle_df["case_key"] = aisle_df["case_key"].astype(str)
            df[case_col] = df[case_col].astype(str)

            # 병합 (left join)
            df = df.merge(
                aisle_df[["case_key", "aisle_code", "slot_code", "side", "area_sqm"]],
                left_on=case_col,
                right_on="case_key",
                how="left",
            )
            print(f"[OK] Aisle Map merged: {df['aisle_code'].notna().sum()} cases matched")
        else:
            print("[WARN] Case No. column not found, skipping Aisle Map merge")
    else:
        print("[INFO] Aisle Map not provided, skipping")

    print(f"[OK] Loaded {len(df)} rows")
    return df


def analyze_flows(df):
    """입고/출고 흐름 분석"""
    warehouse_cols = [
        "DHL WH",
        "DSV Indoor",
        "DSV Al Markaz",
        "DSV Outdoor",
        "AAA Storage",
        "Hauler Indoor",
        "DSV MZP",
        "MOSB",
    ]
    site_cols = ["MIR", "SHU", "DAS", "AGI"]

    def analyze_flow(df, cols):
        flow = {}
        for col in cols:
            if col in df.columns:
                valid_cases = df[df[col].notna()].copy()
                if len(valid_cases) == 0:
                    continue
                valid_cases["YearMonth"] = valid_cases[col].dt.to_period("M").astype(str)
                monthly_counts = valid_cases["YearMonth"].value_counts().to_dict()
                if monthly_counts:
                    flow[col] = monthly_counts
        return flow

    inbound_flow = analyze_flow(df, warehouse_cols)
    outbound_flow = analyze_flow(df, site_cols)

    return inbound_flow, outbound_flow


def dict_to_df(flow_dict, kind):
    """Flow 딕셔너리를 DataFrame으로 변환"""
    rows = []
    for loc, month_counts in flow_dict.items():
        for ym, cnt in month_counts.items():
            rows.append({"Location": loc, "Month": ym, "Count": cnt, "Type": kind})
    return pd.DataFrame(rows)


def calculate_metrics(df):
    """SQM, Stacking, Dwell Time, Turnover 계산"""
    warehouse_cols = [
        "DSV Indoor",
        "DSV Al Markaz",
        "DSV Outdoor",
        "AAA Storage",
        "Hauler Indoor",
        "DSV MZP",
        "MOSB",
    ]

    # Warehouse 필터링
    df["In_Warehouse"] = df[warehouse_cols].notna().any(axis=1)
    df_wh = df[df["In_Warehouse"]].copy()

    # SQM & Stacking
    df_wh["Stack_Status"] = df_wh["Stack_Status"].fillna(1).astype(int)
    df_wh["Stack_Status"] = df_wh["Stack_Status"].replace({0: 1, 1: 1, 3: 3})
    df_wh["Effective_SQM"] = df_wh["SQM"] / df_wh["Stack_Status"]

    total_effective_sqm = df_wh["Effective_SQM"].sum()
    total_cases_wh = len(df_wh)
    stackable_cases = len(df_wh[df_wh["Stack_Status"] == 3])
    non_stackable_cases = len(df_wh[df_wh["Stack_Status"] == 1])
    stack_compliance_pct = (stackable_cases / total_cases_wh) * 100 if total_cases_wh > 0 else 0

    # Capacity
    warehouse_capacity = 3600.0
    reserve_pct = 0.12
    usable_capacity = warehouse_capacity * (1 - reserve_pct)
    utilization_pct = (total_effective_sqm / usable_capacity) * 100
    remaining_sqm = usable_capacity - total_effective_sqm

    # Dwell Time
    entry_dates = df_wh[warehouse_cols].min(axis=1)
    today = pd.Timestamp("2025-10-28")
    df_wh["Dwell_Days"] = (today - entry_dates).dt.days

    avg_dwell = df_wh["Dwell_Days"].mean()
    max_dwell = df_wh["Dwell_Days"].max()
    dwell_90 = df_wh["Dwell_Days"].quantile(0.9)

    bins = [0, 30, 60, 90, 180, 365, np.inf]
    labels = ["<1 mo", "1-2 mo", "2-3 mo", "3-6 mo", "6-12 mo", ">1 yr"]
    df_wh["Dwell_Bin"] = pd.cut(df_wh["Dwell_Days"], bins=bins, labels=labels, right=False)
    dwell_dist = df_wh["Dwell_Bin"].value_counts().reindex(labels, fill_value=0).sort_index()

    # Inventory Turnover
    # (Simplified: would need historical data for accurate turnover)
    turnover_ratio = 6.0  # Placeholder - needs historical calculation
    days_to_turn = 60  # Placeholder
    target_turnover = 6.0

    return {
        "df_wh": df_wh,
        "total_effective_sqm": total_effective_sqm,
        "total_cases_wh": total_cases_wh,
        "stackable_cases": stackable_cases,
        "non_stackable_cases": non_stackable_cases,
        "stack_compliance_pct": stack_compliance_pct,
        "utilization_pct": utilization_pct,
        "remaining_sqm": remaining_sqm,
        "avg_dwell": avg_dwell,
        "max_dwell": max_dwell,
        "dwell_90": dwell_90,
        "dwell_dist": dwell_dist,
        "turnover_ratio": turnover_ratio,
        "days_to_turn": days_to_turn,
        "target_turnover": target_turnover,
    }


def create_dashboard(df, inbound_flow, outbound_flow, metrics):
    """Ultimate Dashboard 생성"""
    # Flow DataFrames
    df_in = dict_to_df(inbound_flow, "Inbound")
    df_out = dict_to_df(outbound_flow, "Outbound")
    df_flow = pd.concat([df_in, df_out], ignore_index=True)

    # Current Inventory
    warehouse_cols = [
        "DHL WH",
        "DSV Indoor",
        "DSV Al Markaz",
        "DSV Outdoor",
        "AAA Storage",
        "Hauler Indoor",
        "DSV MZP",
        "MOSB",
    ]
    site_cols = ["MIR", "SHU", "DAS", "AGI"]

    current_inventory = {}
    for col in warehouse_cols + site_cols:
        if col in df.columns:
            count = df[col].notna().sum()
            if count > 0:
                current_inventory[col] = count

    inv_df = pd.DataFrame(
        [{"Location": loc, "Items": cnt} for loc, cnt in current_inventory.items()]
    )
    inv_df = inv_df.sort_values("Items", ascending=False)

    # SQM & Stacking by Storage
    if "Storage" in metrics["df_wh"].columns:
        sqm_by_storage = metrics["df_wh"].groupby("Storage")["Effective_SQM"].sum().reset_index()
        stack_by_storage = (
            metrics["df_wh"].groupby(["Storage", "Stack_Status"]).size().unstack(fill_value=0)
        )
        dwell_by_storage = metrics["df_wh"].groupby("Storage")["Dwell_Days"].mean().reset_index()
    else:
        sqm_by_storage = pd.DataFrame({"Storage": ["Unknown"], "Effective_SQM": [0]})
        stack_by_storage = pd.DataFrame()
        dwell_by_storage = pd.DataFrame({"Storage": ["Unknown"], "Dwell_Days": [0]})

    # Aisle 분석 (신규)
    aisle_data = None
    bottleneck_data = None
    if "aisle_code" in metrics["df_wh"].columns:
        # Aisle별 케이스 수 및 SQM
        aisle_data = (
            metrics["df_wh"]
            .groupby("aisle_code")
            .agg({"aisle_code": "count", "Effective_SQM": "sum", "Dwell_Days": "mean"})
            .rename(columns={"aisle_code": "Cases"})
            .reset_index()
        )
        aisle_data = aisle_data.sort_values("aisle_code")

        # 병목 구간 분석: 90일 이상 체류 케이스
        bottleneck_df = metrics["df_wh"][metrics["df_wh"]["Dwell_Days"] >= 90].copy()
        if len(bottleneck_df) > 0:
            bottleneck_data = (
                bottleneck_df.groupby("aisle_code")
                .agg({"aisle_code": "count", "Dwell_Days": "mean"})
                .rename(columns={"aisle_code": "Bottleneck_Cases"})
                .reset_index()
            )

    # Pareto 분석 데이터 생성 (pareto 모듈이 있을 경우)
    pareto_result = None
    has_pareto = calculate_pareto_analysis is not None and calculate_aisle_occupancy is not None

    if (
        has_pareto
        and "aisle_code" in metrics["df_wh"].columns
        and "area_sqm" in metrics["df_wh"].columns
    ):
        try:
            print("[INFO] Calculating Pareto analysis...")
            # Aisle 점유율 계산
            aisle_occupancy = calculate_aisle_occupancy(metrics["df_wh"])

            # Pareto 분석 실행
            pareto_result = calculate_pareto_analysis(aisle_occupancy, threshold=80.0)
            print(
                f"[OK] Pareto analysis complete: {len(pareto_result['pareto_aisles'])} priority aisles"
            )
        except Exception as e:
            print(f"[WARN] Pareto analysis failed: {e}")
            has_pareto = False

    # 예측 데이터 생성 (forecast 모듈이 있을 경우)
    forecast_data = None
    has_forecast = forecast_warehouse_demand is not None

    if has_forecast and "Effective_SQM" in metrics["df_wh"].columns:
        try:
            print("[INFO] Generating forecasts...")
            # 월별 SQM 집계
            df_wh_monthly = metrics["df_wh"].copy()
            df_wh_monthly["Month"] = pd.Timestamp("2025-10-28")  # Current date placeholder
            monthly_sqm = df_wh_monthly.groupby("Month")["Effective_SQM"].sum().reset_index()
            monthly_sqm.rename(columns={"Month": "Date", "Effective_SQM": "CBM"}, inplace=True)

            # 예측 실행 (90일 = 3개월)
            if len(monthly_sqm) > 0:
                cbm_fc, _, cost_fc = forecast_warehouse_demand(
                    monthly_sqm,
                    cbm_col="CBM",
                    date_col="Date",
                    horizon=90,
                    confidence=0.90,
                    rate_per_sqm=47.0,
                )
                forecast_data = {"cbm": cbm_fc.df, "cost": cost_fc}
                print(f"[OK] Forecast generated: {len(cbm_fc.df)} days")
        except Exception as e:
            print(f"[WARN] Forecast generation failed: {e}")
            has_forecast = False

    # Dashboard Layout - 확장 (4x2, 5x2, 또는 6x2)
    has_aisle = aisle_data is not None and len(aisle_data) > 0

    if has_aisle and has_forecast and has_pareto:
        # 7x2 레이아웃 (Aisle + Forecast + Pareto + Heatmap)
        fig = make_subplots(
            rows=7,
            cols=2,
            subplot_titles=(
                "Current Inventory (Cases)",
                "Monthly Flow (In/Out)",
                "SQM Utilization Gauge",
                "SQM by Storage",
                "Aisle Utilization (A1-A8)",
                "Bottleneck by Aisle (>90 days)",
                "SQM Forecast (Next 90 Days)",
                "Cost Forecast (Next 90 Days)",
                "Pareto Analysis - Aisle Occupancy",
                "Cumulative % (80/20 Rule)",
                "Optimization Recommendations",
                "",
                "Inbound Heatmap",
                "Outbound Heatmap",
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "table", "colspan": 2}, None],
                [{"type": "heatmap"}, {"type": "heatmap"}],
            ],
            vertical_spacing=0.04,
            horizontal_spacing=0.12,
            row_heights=[0.13, 0.13, 0.13, 0.13, 0.13, 0.20, 0.15],
        )
    elif has_aisle and has_forecast:
        # 5x2 레이아웃 (Aisle + Forecast)
        fig = make_subplots(
            rows=5,
            cols=2,
            subplot_titles=(
                "Current Inventory (Cases)",
                "Monthly Flow (In/Out)",
                "SQM Utilization Gauge",
                "SQM by Storage",
                "Aisle Utilization (A1-A8)",
                "Bottleneck by Aisle (>90 days)",
                "SQM Forecast (Next 90 Days)",
                "Cost Forecast (Next 90 Days)",
                "Inbound Heatmap",
                "Outbound Heatmap",
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "heatmap"}, {"type": "heatmap"}],
            ],
            vertical_spacing=0.06,
            horizontal_spacing=0.12,
            row_heights=[0.2, 0.2, 0.2, 0.2, 0.2],
        )
    elif has_aisle and has_pareto:
        # 5x2 레이아웃 (Aisle + Pareto, no Forecast)
        fig = make_subplots(
            rows=5,
            cols=2,
            subplot_titles=(
                "Current Inventory (Cases)",
                "Monthly Flow (In/Out)",
                "SQM Utilization Gauge",
                "SQM by Storage",
                "Aisle Utilization (A1-A8)",
                "Bottleneck by Aisle (>90 days)",
                "Pareto Analysis - Aisle Occupancy",
                "Cumulative % (80/20 Rule)",
                "Optimization Recommendations",
                "",
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "table", "colspan": 2}, None],
            ],
            vertical_spacing=0.06,
            horizontal_spacing=0.12,
            row_heights=[0.2, 0.2, 0.2, 0.2, 0.2],
        )
    elif has_aisle:
        # 4x2 레이아웃 (Aisle만)
        fig = make_subplots(
            rows=4,
            cols=2,
            subplot_titles=(
                "Current Inventory (Cases)",
                "Monthly Flow (In/Out)",
                "SQM Utilization Gauge",
                "SQM by Storage",
                "Aisle Utilization (A1-A8)",
                "Bottleneck by Aisle (>90 days)",
                "Inbound Heatmap",
                "Outbound Heatmap",
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "heatmap"}, {"type": "heatmap"}],
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.12,
            row_heights=[0.25, 0.25, 0.25, 0.25],
        )
    else:
        fig = make_subplots(
            rows=3,
            cols=2,
            subplot_titles=(
                "Current Inventory (Cases)",
                "Monthly Flow (In/Out)",
                "SQM Utilization Gauge",
                "SQM by Storage",
                "Inbound Heatmap",
                "Outbound Heatmap",
            ),
            specs=[
                [{"type": "bar"}, {"type": "scatter"}],
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "heatmap"}, {"type": "heatmap"}],
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.12,
            row_heights=[0.35, 0.35, 0.3],
        )

    # 1. Inventory Bar
    fig.add_trace(
        go.Bar(x=inv_df["Location"], y=inv_df["Items"], name="Cases", marker_color="#1f77b4"),
        row=1,
        col=1,
    )

    # 2. Monthly Flow Line
    monthly = df_flow.groupby(["Month", "Type"])["Count"].sum().reset_index()
    monthly = monthly.pivot(index="Month", columns="Type", values="Count").fillna(0).reset_index()

    fig.add_trace(
        go.Scatter(
            x=monthly["Month"],
            y=monthly["Inbound"],
            mode="lines+markers",
            name="Inbound",
            line=dict(color="#2ca02c"),
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["Month"],
            y=monthly["Outbound"],
            mode="lines+markers",
            name="Outbound",
            line=dict(color="#d62728"),
        ),
        row=1,
        col=2,
    )

    # 3. SQM Utilization Gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=metrics["utilization_pct"],
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": "<b>SQM Utilization</b><br><span style='font-size:0.8em'>of 3,168 SQM Usable</span>"
            },
            delta={"reference": 80, "position": "top"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": "#1f77b4"},
                "steps": [
                    {"range": [0, 75], "color": "lightgreen"},
                    {"range": [75, 90], "color": "yellow"},
                    {"range": [90, 100], "color": "red"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
            },
        ),
        row=2,
        col=1,
    )

    # 4. SQM by Storage Type (Pie)
    fig.add_trace(
        go.Pie(
            labels=sqm_by_storage["Storage"],
            values=sqm_by_storage["Effective_SQM"],
            name="SQM",
            hole=0.4,
            marker_colors=px.colors.sequential.Blues,
        ),
        row=2,
        col=2,
    )

    # 5 & 6. Aisle 차트 (Aisle Map이 있을 경우)
    if has_aisle:
        # 5. Aisle Utilization (Cases + SQM)
        fig.add_trace(
            go.Bar(
                x=aisle_data["aisle_code"],
                y=aisle_data["Cases"],
                name="Cases",
                marker_color="#17becf",
                text=aisle_data["Cases"],
                textposition="outside",
            ),
            row=3,
            col=1,
        )

        # 6. Bottleneck by Aisle
        if bottleneck_data is not None and len(bottleneck_data) > 0:
            # 색상: Dwell_Days에 따라 등급 부여
            colors = []
            for days in bottleneck_data["Dwell_Days"]:
                if days >= 365:
                    colors.append("#d62728")  # 빨강 (1년 이상)
                elif days >= 180:
                    colors.append("#ff7f0e")  # 주황 (6개월-1년)
                else:
                    colors.append("#ffbb78")  # 연주황 (90일-6개월)

            fig.add_trace(
                go.Bar(
                    x=bottleneck_data["aisle_code"],
                    y=bottleneck_data["Bottleneck_Cases"],
                    name="Bottleneck",
                    marker_color=colors,
                    text=bottleneck_data["Bottleneck_Cases"],
                    textposition="outside",
                ),
                row=3,
                col=2,
            )

        # 7 & 8. 예측 차트 (Forecast 데이터가 있을 경우)
        if has_forecast and forecast_data is not None:
            # 7. SQM Forecast
            fc_cbm = forecast_data["cbm"]
            fig.add_trace(
                go.Scatter(
                    x=fc_cbm["date"],
                    y=fc_cbm["yhat"],
                    mode="lines",
                    name="Forecast",
                    line=dict(color="#9467bd", width=2),
                ),
                row=4,
                col=1,
            )
            # Confidence intervals
            fig.add_trace(
                go.Scatter(
                    x=fc_cbm["date"].tolist() + fc_cbm["date"].tolist()[::-1],
                    y=fc_cbm["yhat_high"].tolist() + fc_cbm["yhat_low"].tolist()[::-1],
                    fill="toself",
                    fillcolor="rgba(148, 103, 189, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    showlegend=False,
                    name="Confidence Interval",
                ),
                row=4,
                col=1,
            )

            # 8. Cost Forecast
            fc_cost = forecast_data["cost"]
            fig.add_trace(
                go.Scatter(
                    x=fc_cost["date"],
                    y=fc_cost["cost_forecast"],
                    mode="lines",
                    name="Cost Forecast",
                    line=dict(color="#e377c2", width=2),
                ),
                row=4,
                col=2,
            )
            # Cost confidence intervals
            fig.add_trace(
                go.Scatter(
                    x=fc_cost["date"].tolist() + fc_cost["date"].tolist()[::-1],
                    y=fc_cost["cost_high"].tolist() + fc_cost["cost_low"].tolist()[::-1],
                    fill="toself",
                    fillcolor="rgba(227, 119, 194, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    showlegend=False,
                    name="Cost CI",
                ),
                row=4,
                col=2,
            )

            # For 7x2 layout (with Pareto and Forecast), heatmaps on row 7
            heatmap_row = 7 if (has_pareto and pareto_result is not None) else 6
        else:
            # For 5x2 layout (with Pareto only), no heatmaps
            heatmap_row = 0 if (has_pareto and pareto_result is not None) else 5
    else:
        # For 5x2 layout (Aisle + Pareto), no heatmaps
        heatmap_row = 0 if (has_pareto and pareto_result is not None) else 5

    # 9 & 10. Pareto 차트 (Pareto 분석이 있을 경우)
    if has_pareto and pareto_result is not None and has_aisle:
        pareto_df = pareto_result["cumulative_data"]

        # Determine row number based on layout
        if has_forecast:
            pareto_bar_row, pareto_line_row = 5, 5
            table_row = 6
        else:
            pareto_bar_row, pareto_line_row = 4, 4
            table_row = 5

        # 9. Pareto 막대 차트 (Aisle별 점유 SQM)
        fig.add_trace(
            go.Bar(
                x=pareto_df["aisle"],
                y=pareto_df["occupied_sqm"],
                name="Occupied SQM",
                marker_color="#1f77b4",
                text=pareto_df["occupied_sqm"].round(1),
                textposition="outside",
            ),
            row=pareto_bar_row,
            col=1,
        )

        # 10. 누적 % 선 차트
        fig.add_trace(
            go.Scatter(
                x=pareto_df["aisle"],
                y=pareto_df["cumulative_percentage"],
                mode="lines+markers",
                name="Cumulative %",
                line=dict(color="red", width=2),
                marker=dict(size=8, color="red"),
            ),
            row=pareto_line_row,
            col=2,
        )

        # 80% 기준선 (Shape 사용)
        fig.add_shape(
            type="line",
            xref=f"x{2 * (pareto_line_row - 1) + 2}",
            yref=f"y{2 * (pareto_line_row - 1) + 2}",
            x0=0,
            x1=1,
            y0=80,
            y1=80,
            line=dict(color="green", width=2, dash="dash"),
            row=pareto_line_row,
            col=2,
        )

        # 11. 권장사항 테이블
        if pareto_result["recommendations"]:
            recommendations_list = pareto_result["recommendations"]

            # 우선순위 추출 (첫 글자만)
            priorities = []
            for rec in recommendations_list:
                if "Priority" in rec or "Priority" in rec:
                    priorities.append("High")
                elif "Capacity" in rec or "Capacity" in rec:
                    priorities.append("Medium")
                elif "Available" in rec or "Available" in rec:
                    priorities.append("Low")
                else:
                    priorities.append("Info")

            fig.add_trace(
                go.Table(
                    header=dict(
                        values=["Priority", "Recommendation"],
                        fill_color="paleturquoise",
                        align="left",
                        font=dict(size=12, color="black"),
                    ),
                    cells=dict(
                        values=[priorities, recommendations_list],
                        fill_color="lavender",
                        align="left",
                        font=dict(size=11),
                    ),
                ),
                row=table_row,
                col=1,
            )

    # Heatmaps (행 번호 동적, 0이면 추가하지 않음)
    if heatmap_row > 0:
        in_piv = df_in.pivot_table(index="Location", columns="Month", values="Count", fill_value=0)
        fig.add_trace(
            go.Heatmap(
                z=in_piv.values,
                x=in_piv.columns,
                y=in_piv.index,
                colorscale="Greens",
                name="Inbound",
            ),
            row=heatmap_row,
            col=1,
        )

        out_piv = df_out.pivot_table(
            index="Location", columns="Month", values="Count", fill_value=0
        )
        fig.add_trace(
            go.Heatmap(
                z=out_piv.values,
                x=out_piv.columns,
                y=out_piv.index,
                colorscale="Reds",
                name="Outbound",
            ),
            row=heatmap_row,
            col=2,
        )

    # Layout & Annotations
    if has_aisle and has_forecast and has_pareto:
        dashboard_height = 2000  # 7x2 layout with all features
        edition_text = "Ultimate Edition v4.0.50 - Aisle Map, Forecast & Pareto Optimization"
    elif has_aisle and has_forecast:
        dashboard_height = 1600  # 5x2 layout with forecast
        edition_text = "Ultimate Edition v4.0.49 - Aisle Map, Bottleneck & Predictive Forecasting"
    elif has_aisle and has_pareto:
        dashboard_height = 1700  # 5x2 layout with Pareto (no forecast)
        edition_text = "Ultimate Edition v4.0.50 - Aisle Map & Pareto Optimization"
    elif has_aisle:
        dashboard_height = 1400  # 4x2 layout with aisle
        edition_text = "Ultimate Edition v4.0.48 with Aisle Map & Bottleneck Analysis"
    else:
        dashboard_height = 1100  # 3x2 layout basic
        edition_text = "Ultimate Edition with Stacking, Dwell & Turnover"

    fig.update_layout(
        height=dashboard_height,
        title_text=f"<b>DSV Al Markaz – Ultimate Flow & SQM Dashboard</b><br>"
        f"<i>{edition_text}</i>",
        title_x=0.5,
        font=dict(family="Arial", size=11),
        showlegend=False,
    )

    # KPI Box
    kpi_text = f"""
    <b>Live KPIs (Oct 28, 2025)</b><br>
    • Cases: <b>{metrics['total_cases_wh']:,}</b> | Stackable: <b>{metrics['stack_compliance_pct']:.1f}%</b><br>
    • SQM: <b>{metrics['total_effective_sqm']:,.1f}</b> → <b>{metrics['utilization_pct']:.1f}%</b><br>
    • Avg Dwell: <b>{metrics['avg_dwell']:.0f} days</b> | 90th: <b>{metrics['dwell_90']:.0f} days</b><br>
    • Turnover: <b>{metrics['turnover_ratio']:.1f}x/year</b> → <b>{metrics['days_to_turn']:.0f} days</b>
    """
    fig.add_annotation(
        text=kpi_text,
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        font=dict(size=10),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="gray",
        borderwidth=1,
    )

    return fig


def main():
    parser = argparse.ArgumentParser(
        description="DSV Al Markaz Ultimate Dashboard Generator v4.0.48"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx",
        help="입력 Excel 파일 경로",
    )
    parser.add_argument("--sheet", "-s", type=str, default="Case List, RIL", help="Excel 시트명")
    parser.add_argument(
        "--aisle-map",
        "-a",
        type=str,
        default="almk_aisle_map.csv",
        help="Aisle Map CSV 파일 경로",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/visualizations/DSV_AlMarkaz_Ultimate_Dashboard.html",
        help="출력 HTML 파일 경로",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Aisle Map 경로 확인
    aisle_map_path = Path(args.aisle_map) if args.aisle_map else None

    # Load & Analyze
    df = load_data(
        str(input_path), args.sheet, aisle_map_path=str(aisle_map_path) if aisle_map_path else None
    )
    print("[INFO] Analyzing flows...")
    inbound_flow, outbound_flow = analyze_flows(df)
    print("[INFO] Calculating metrics...")
    metrics = calculate_metrics(df)

    # Create Dashboard
    print("[INFO] Creating ultimate dashboard...")
    fig = create_dashboard(df, inbound_flow, outbound_flow, metrics)

    # Save
    print(f"[INFO] Saving to: {output_path}")
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    print(f"[OK] Dashboard saved: {output_path}")

    # Metrics Output
    print("\n[Ultimate KPIs]")
    print(f"  - Total Cases: {metrics['total_cases_wh']:,}")
    print(f"  - Stackable: {metrics['stack_compliance_pct']:.1f}%")
    print(f"  - SQM Used: {metrics['total_effective_sqm']:,.1f}")
    print(f"  - Utilization: {metrics['utilization_pct']:.1f}%")
    print(f"  - Avg Dwell: {metrics['avg_dwell']:.0f} days")

    return 0


if __name__ == "__main__":
    exit(main())
