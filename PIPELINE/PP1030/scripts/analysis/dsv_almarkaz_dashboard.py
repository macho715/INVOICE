#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSV Al Markaz - Full Flow + SQM Utilization Dashboard

창고 이동 흐름 분석 및 SQM 사용률 모니터링 대시보드를 생성합니다.

Usage:
    python dsv_almarkaz_dashboard.py [--input <path>] [--output <path>]
"""

import argparse
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime


def load_data(input_path, sheet_name="Case List"):
    """
    Excel 파일에서 데이터를 로드하고 기본 전처리를 수행합니다.

    Args:
        input_path: Excel 파일 경로
        sheet_name: 시트명

    Returns:
        DataFrame: 전처리된 데이터
    """
    print(f"[INFO] Loading data from: {input_path}")
    df = pd.read_excel(input_path, sheet_name=sheet_name, engine="openpyxl")

    # 날짜 컬럼을 datetime으로 변환
    date_cols = [col for col in df.columns
                 if any(x in col for x in ['DHL', 'DSV', 'AAA', 'Hauler', 'MOSB', 'MIR', 'SHU', 'DAS', 'AGI'])
                 or col.endswith('Date')]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    print(f"[OK] Loaded {len(df)} rows")
    return df


def analyze_inbound_flow(df):
    """
    입고(Inbound) 흐름을 월별로 분석합니다.

    Args:
        df: DataFrame

    Returns:
        dict: {location: {year_month: count}}
    """
    warehouse_cols = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor',
                     'AAA Storage', 'Hauler Indoor', 'DSV MZP', 'MOSB']

    inbound_flow = {}

    for col in warehouse_cols:
        if col in df.columns:
            # 해당 컬럼이 있는 케이스만 필터링
            valid_cases = df[df[col].notna()].copy()
            if len(valid_cases) == 0:
                continue

            # 년월 추출
            valid_cases['YearMonth'] = valid_cases[col].dt.to_period('M').astype(str)

            # 월별 카운트
            monthly_counts = valid_cases['YearMonth'].value_counts().to_dict()
            inbound_flow[col] = monthly_counts

    return inbound_flow


def analyze_outbound_flow(df):
    """
    출고(Outbound) 흐름을 월별로 분석합니다.

    Args:
        df: DataFrame

    Returns:
        dict: {location: {year_month: count}}
    """
    site_cols = ['MIR', 'SHU', 'DAS', 'AGI']

    outbound_flow = {}

    for col in site_cols:
        if col in df.columns:
            # 해당 컬럼이 있는 케이스만 필터링
            valid_cases = df[df[col].notna()].copy()
            if len(valid_cases) == 0:
                continue

            # 년월 추출
            valid_cases['YearMonth'] = valid_cases[col].dt.to_period('M').astype(str)

            # 월별 카운트
            monthly_counts = valid_cases['YearMonth'].value_counts().to_dict()
            outbound_flow[col] = monthly_counts

    return outbound_flow


def calculate_current_inventory(df):
    """
    현재 재고를 위치별로 계산합니다.

    Args:
        df: DataFrame

    Returns:
        dict: {location: count}
    """
    warehouse_cols = ['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor',
                     'AAA Storage', 'Hauler Indoor', 'DSV MZP', 'MOSB']
    site_cols = ['MIR', 'SHU', 'DAS', 'AGI']

    inventory = {}

    # Warehouse 재고
    for col in warehouse_cols:
        if col in df.columns:
            count = df[col].notna().sum()
            if count > 0:
                inventory[col] = count

    # Site 재고
    for col in site_cols:
        if col in df.columns:
            count = df[col].notna().sum()
            if count > 0:
                inventory[col] = count

    return inventory


def calculate_sqm_metrics(df):
    """
    SQM 사용률 메트릭을 계산합니다.

    Args:
        df: DataFrame

    Returns:
        dict: SQM 메트릭 딕셔너리
    """
    warehouse_cols = ['DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor', 'AAA Storage',
                      'Hauler Indoor', 'DSV MZP', 'MOSB']

    # Warehouse에 있는 케이스 필터링
    df['In_Warehouse'] = df[warehouse_cols].notna().any(axis=1)
    df_wh = df[df['In_Warehouse']].copy()

    # SQM 및 Stack_Status 컬럼이 있는지 확인
    if 'SQM' not in df_wh.columns:
        print("[WARN] 'SQM' column not found. Using default values.")
        df_wh['SQM'] = 0
    if 'Stack_Status' not in df_wh.columns:
        print("[WARN] 'Stack_Status' column not found. Using default value of 1.")
        df_wh['Stack_Status'] = 1

    # Effective SQM 계산 (Stack_Status가 0이면 1로 대체)
    df_wh['Stack_Status'] = df_wh['Stack_Status'].replace({0: 1, 1: 1, 3: 3})
    df_wh['Effective_SQM'] = df_wh['SQM'] / df_wh['Stack_Status']

    # 메트릭 계산
    total_effective_sqm = df_wh['Effective_SQM'].sum()
    total_raw_sqm = df_wh['SQM'].sum()
    total_cases_wh = len(df_wh)
    warehouse_capacity = 3600.0
    reserve_sqm = warehouse_capacity * 0.12
    usable_capacity = warehouse_capacity - reserve_sqm
    utilization_pct = (total_effective_sqm / usable_capacity) * 100 if usable_capacity > 0 else 0
    remaining_sqm = usable_capacity - total_effective_sqm

    return {
        'total_effective_sqm': total_effective_sqm,
        'total_raw_sqm': total_raw_sqm,
        'total_cases_wh': total_cases_wh,
        'warehouse_capacity': warehouse_capacity,
        'reserve_sqm': reserve_sqm,
        'usable_capacity': usable_capacity,
        'utilization_pct': utilization_pct,
        'remaining_sqm': remaining_sqm,
        'df_wh': df_wh
    }


def dict_to_df(flow_dict, kind):
    """Flow 딕셔너리를 DataFrame으로 변환합니다."""
    rows = []
    for loc, month_counts in flow_dict.items():
        for ym, cnt in month_counts.items():
            rows.append({"Location": loc, "Month": ym, "Count": cnt, "Type": kind})
    return pd.DataFrame(rows)


def create_dashboard(inbound_flow, outbound_flow, current_inventory, sqm_metrics):
    """
    Plotly 대시보드를 생성합니다.

    Args:
        inbound_flow: 입고 흐름 딕셔너리
        outbound_flow: 출고 흐름 딕셔너리
        current_inventory: 현재 재고 딕셔너리
        sqm_metrics: SQM 메트릭 딕셔너리
    """
    # Flow DataFrames
    df_in = dict_to_df(inbound_flow, "Inbound")
    df_out = dict_to_df(outbound_flow, "Outbound")
    df_flow = pd.concat([df_in, df_out], ignore_index=True)

    # Current Inventory
    inv_df = pd.DataFrame([
        {"Location": loc, "Items": cnt}
        for loc, cnt in current_inventory.items()
    ])
    inv_df = inv_df.sort_values("Items", ascending=False)

    # SQM by Storage Type
    if 'Storage' in sqm_metrics['df_wh'].columns:
        sqm_by_storage = sqm_metrics['df_wh'].groupby('Storage')['Effective_SQM'].sum().reset_index()
        sqm_by_storage = sqm_by_storage.sort_values('Effective_SQM', ascending=False)
    else:
        sqm_by_storage = pd.DataFrame({'Storage': ['Unknown'], 'Effective_SQM': [0]})

    # Create dashboard
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Current Inventory (Cases)",
            "Monthly Flow (In/Out)",
            "SQM Utilization Gauge",
            "SQM by Storage Type",
            "Inbound Heatmap",
            "Outbound Heatmap"
        ),
        specs=[
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "indicator"}, {"type": "pie"}],
            [{"type": "heatmap"}, {"type": "heatmap"}]
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.12,
        row_heights=[0.3, 0.35, 0.35]
    )

    # 1. Inventory Bar
    fig.add_trace(
        go.Bar(x=inv_df["Location"], y=inv_df["Items"],
               name="Cases", marker_color="#1f77b4"),
        row=1, col=1
    )

    # 2. Monthly Flow Line
    monthly = df_flow.groupby(["Month", "Type"])["Count"].sum().reset_index()
    monthly = monthly.pivot(index="Month", columns="Type", values="Count").fillna(0).reset_index()

    fig.add_trace(
        go.Scatter(x=monthly["Month"], y=monthly["Inbound"],
                   mode="lines+markers", name="Inbound", line=dict(color="#2ca02c")),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=monthly["Month"], y=monthly["Outbound"],
                   mode="lines+markers", name="Outbound", line=dict(color="#d62728")),
        row=1, col=2
    )

    # 3. SQM Utilization Gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=sqm_metrics['utilization_pct'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "<b>SQM Utilization</b><br><span style='font-size:0.8em'>of 3,168 SQM Usable</span>"},
            delta={'reference': 80, 'position': "top"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 75], 'color': "lightgreen"},
                    {'range': [75, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=1
    )

    # 4. SQM by Storage Type (Pie)
    fig.add_trace(
        go.Pie(labels=sqm_by_storage['Storage'], values=sqm_by_storage['Effective_SQM'],
               name="SQM", hole=0.4, marker_colors=px.colors.sequential.Blues),
        row=2, col=2
    )

    # 5. Inbound Heatmap
    in_piv = df_in.pivot_table(index="Location", columns="Month", values="Count", fill_value=0)
    fig.add_trace(
        go.Heatmap(z=in_piv.values, x=in_piv.columns, y=in_piv.index,
                   colorscale="Greens", name="Inbound"),
        row=3, col=1
    )

    # 6. Outbound Heatmap
    out_piv = df_out.pivot_table(index="Location", columns="Month", values="Count", fill_value=0)
    fig.add_trace(
        go.Heatmap(z=out_piv.values, x=out_piv.columns, y=out_piv.index,
                   colorscale="Reds", name="Outbound"),
        row=3, col=2
    )

    # Layout & Annotations
    fig.update_layout(
        height=1100,
        title_text="<b>DSV Al Markaz – Flow & SQM Utilization Dashboard</b>",
        title_x=0.5,
        font=dict(family="Arial", size=11),
        showlegend=False
    )

    # Add annotation box with key metrics
    annotation_text = f"""
    <b>Live SQM Metrics</b><br>
    • Occupied: <b>{sqm_metrics['total_effective_sqm']:,.1f} SQM</b><br>
    • Capacity (usable): <b>3,168 SQM</b><br>
    • Remaining: <b>{sqm_metrics['remaining_sqm']:,.1f} SQM</b><br>
    • Cases in WH: <b>{sqm_metrics['total_cases_wh']:,}</b>
    """
    fig.add_annotation(
        text=annotation_text,
        xref="paper", yref="paper",
        x=0.98, y=0.98, xanchor="right", yanchor="top",
        showarrow=False,
        font=dict(size=10),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="gray", borderwidth=1,
        align="left"
    )

    return fig


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="DSV Al Markaz Flow & SQM Dashboard Generator"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx",
        help="입력 Excel 파일 경로"
    )
    parser.add_argument(
        "--sheet",
        "-s",
        type=str,
        default="Case List, RIL",
        help="Excel 시트명"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/visualizations/DSV_AlMarkaz_Full_Dashboard.html",
        help="출력 HTML 파일 경로"
    )

    args = parser.parse_args()

    # 파일 경로 검증
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    # 출력 디렉토리 생성
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 데이터 로드
    df = load_data(str(input_path), args.sheet)

    # 분석 수행
    print("[INFO] Analyzing inbound flow...")
    inbound_flow = analyze_inbound_flow(df)

    print("[INFO] Analyzing outbound flow...")
    outbound_flow = analyze_outbound_flow(df)

    print("[INFO] Calculating current inventory...")
    current_inventory = calculate_current_inventory(df)

    print("[INFO] Calculating SQM metrics...")
    sqm_metrics = calculate_sqm_metrics(df)

    # 대시보드 생성
    print("[INFO] Creating dashboard...")
    fig = create_dashboard(inbound_flow, outbound_flow, current_inventory, sqm_metrics)

    # 저장
    print(f"[INFO] Saving dashboard to: {output_path}")
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    print(f"[OK] Dashboard saved: {output_path}")

    # 메트릭 출력
    print("\n[SQM Metrics]")
    print(f"  - Total Effective SQM: {sqm_metrics['total_effective_sqm']:,.1f}")
    print(f"  - Utilization: {sqm_metrics['utilization_pct']:.1f}%")
    print(f"  - Remaining: {sqm_metrics['remaining_sqm']:,.1f} SQM")
    print(f"  - Cases in Warehouse: {sqm_metrics['total_cases_wh']:,}")

    return 0


if __name__ == "__main__":
    exit(main())

