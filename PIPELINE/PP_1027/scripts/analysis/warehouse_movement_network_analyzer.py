#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Warehouse Movement Network Analyzer

창고 간 물류 이동 경로를 네트워크 그래프로 시각화하여 주요 이동 패턴을 분석합니다.

Usage:
    python warehouse_movement_network_analyzer.py --input <path> --output <path> --top-n 20
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns


def identify_movements(row, location_columns):
    """
    각 케이스의 이동 경로를 날짜 순으로 추적하여 연속된 위치 쌍을 생성합니다.

    Args:
        row: DataFrame row
        location_columns: 위치 컬럼 리스트

    Returns:
        list: (from_location, to_location) 튜플 리스트
    """
    # Filter only the location columns that have dates
    valid_locations = {col: row[col] for col in location_columns if pd.notna(row[col])}

    # Sort locations by date
    sorted_locations = sorted(valid_locations.items(), key=lambda x: x[1])

    # Create pairs of consecutive locations (from -> to)
    movements = []
    for i in range(len(sorted_locations) - 1):
        from_loc = sorted_locations[i][0]
        to_loc = sorted_locations[i + 1][0]
        movements.append((from_loc, to_loc))

    return movements


def analyze_movements(df, location_columns):
    """
    모든 케이스의 이동 경로를 분석하여 빈도를 계산합니다.

    Args:
        df: DataFrame
        location_columns: 위치 컬럼 리스트

    Returns:
        DataFrame: From_Location, To_Location, Count 컬럼을 가진 DataFrame
    """
    # Apply the function to each row and collect all movements
    all_movements = []
    for _, row in df.iterrows():
        movements = identify_movements(row, location_columns)
        all_movements.extend(movements)

    # Count the frequency of each movement
    movement_counts = {}
    for movement in all_movements:
        if movement in movement_counts:
            movement_counts[movement] += 1
        else:
            movement_counts[movement] = 1

    # Convert to DataFrame for easier analysis
    movement_df = pd.DataFrame(
        [(from_loc, to_loc, count) for (from_loc, to_loc), count in movement_counts.items()],
        columns=["From_Location", "To_Location", "Count"],
    )

    # Sort by count in descending order
    movement_df = movement_df.sort_values("Count", ascending=False)

    return movement_df


def create_network_graph(movement_df, top_n=20, output_path="warehouse_movement_network.png"):
    """
    이동 경로 데이터로부터 네트워크 그래프를 생성하고 저장합니다.

    Args:
        movement_df: 이동 경로 DataFrame
        top_n: 상위 N개 이동 경로만 시각화
        output_path: 출력 이미지 경로
    """
    # Create a network graph of the top movements
    top_movements = movement_df.head(top_n)

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes and edges with weights
    for _, row in top_movements.iterrows():
        from_loc = row["From_Location"]
        to_loc = row["To_Location"]
        count = row["Count"]

        # Add nodes if they don't exist
        if from_loc not in G.nodes():
            G.add_node(from_loc)
        if to_loc not in G.nodes():
            G.add_node(to_loc)

        # Add edge with weight
        G.add_edge(from_loc, to_loc, weight=count)

    # Set up the figure with a specific size
    plt.figure(figsize=(14, 10))

    # Create a layout for the nodes
    pos = nx.spring_layout(G, k=0.3, seed=42)

    # Get edge weights for line thickness and color
    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_weight = max(edge_weights)
    min_weight = min(edge_weights)

    # Normalize edge weights for thickness
    normalized_weights = [
        2 + 8 * (weight - min_weight) / (max_weight - min_weight) for weight in edge_weights
    ]

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue", alpha=0.8)

    # Draw the edges with varying thickness based on weight
    edge_colors = edge_weights
    edges = nx.draw_networkx_edges(
        G,
        pos,
        width=normalized_weights,
        edge_color=edge_colors,
        edge_cmap=plt.cm.Blues,
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
    )

    # Draw the labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Add edge labels (counts)
    edge_labels = {(u, v): G[u][v]["weight"] for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    # Add a title and adjust layout
    plt.title(f"Network of Top {top_n} Warehouse Movements", fontsize=16)
    plt.axis("off")

    # Fix the colorbar issue by creating a separate axes for it
    plt.tight_layout()

    # Create a separate axes for the colorbar
    cbar_ax = plt.axes([0.92, 0.1, 0.02, 0.8])  # [left, bottom, width, height]
    sm = plt.cm.ScalarMappable(
        cmap=plt.cm.Blues, norm=plt.Normalize(vmin=min(edge_colors), vmax=max(edge_colors))
    )
    sm.set_array([])
    plt.colorbar(sm, cax=cbar_ax, label="Number of Movements")

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Network graph saved to: {output_path}")
    plt.close()


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="Warehouse Movement Network Analyzer - 창고 간 물류 이동 경로 네트워크 분석"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx",
        help="입력 Excel 파일 경로 (기본값: data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx)",
    )
    parser.add_argument(
        "--sheet",
        "-s",
        type=str,
        default="Case List",
        help="Excel 시트명 (기본값: Case List)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/visualizations/warehouse_movement_network.png",
        help="출력 이미지 경로 (기본값: data/processed/visualizations/warehouse_movement_network.png)",
    )
    parser.add_argument(
        "--top-n",
        "-n",
        type=int,
        default=20,
        help="상위 N개 이동 경로 시각화 (기본값: 20)",
    )
    parser.add_argument(
        "--engine",
        "-e",
        type=str,
        default="openpyxl",
        choices=["openpyxl", "calamine"],
        help="Excel 엔진 (기본값: openpyxl)",
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

    print(f"[INFO] Loading data from: {input_path}")

    # Load the movement data
    try:
        df = pd.read_excel(input_path, sheet_name=args.sheet, engine=args.engine)
        print(f"[OK] Loaded {len(df)} rows")
    except Exception as e:
        print(f"[ERROR] Failed to load data: {e}")
        return 1

    # Create a list of all location columns
    location_columns = [
        "DHL Warehouse",
        "DSV Indoor",
        "DSV Al Markaz",
        "DSV Outdoor",
        "AAA  Storage",
        "Hauler Indoor",
        "DSV MZP",
        "MOSB",
        "Shifting",
        "MIR",
        "SHU",
        "DAS",
        "AGI",
    ]

    # Convert date columns to datetime format
    print(f"[INFO] Converting date columns to datetime format...")
    for col in location_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Analyze movements
    print(f"[INFO] Analyzing movements...")
    movement_df = analyze_movements(df, location_columns)
    print(f"[OK] Found {len(movement_df)} unique movement patterns")
    print(f"[INFO] Top 5 movements:")
    print(movement_df.head(5).to_string(index=False))

    # Create network graph
    print(f"[INFO] Creating network graph (top {args.top_n} movements)...")
    create_network_graph(movement_df, top_n=args.top_n, output_path=str(output_path))

    # Save movement summary to CSV
    csv_path = output_path.with_suffix(".csv")
    movement_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Movement summary saved to: {csv_path}")

    return 0


if __name__ == "__main__":
    exit(main())

