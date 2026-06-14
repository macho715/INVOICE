#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test anomaly visualizer directly"""

import sys
import io
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add scripts to path
sys.path.insert(0, str(Path("scripts/stage4_anomaly").resolve()))

from anomaly_visualizer import AnomalyVisualizer

# Load anomalies from JSON
json_path = Path("data/anomaly/HVDC_anomaly_report.json")
with open(json_path, encoding='utf-8') as f:
    anomalies = json.load(f)

print(f"총 이상치: {len(anomalies)}건")
print()

# Create visualizer
visualizer = AnomalyVisualizer(anomalies)

print(f"Visualizer records: {len(visualizer.records)}건")
print(f"Visualizer by_case: {len(visualizer.by_case)}개 케이스")
print()

# Show first 10 cases in by_case
print("by_case 딕셔너리 샘플 (처음 10개):")
for i, (case_id, anoms) in enumerate(list(visualizer.by_case.items())[:10]):
    print(f"  {i+1}. Case ID: [{case_id}] ({len(anoms)} anomalies)")
    for a in anoms:
        print(f"      - Type: {a.get('Anomaly_Type')}, Severity: {a.get('Severity')}")

print()

# Find report file
report_dir = Path("data/processed/reports")
report_files = [f for f in report_dir.glob("HVDC_입고로직_종합리포트_*.xlsx") if "backup" not in f.name.lower()]
file_path = max(report_files, key=lambda p: p.stat().st_mtime)

print(f"대상 파일: {file_path.name}")
print()

# Apply colors
print("색상 적용 실행 중...")
result = visualizer.apply_anomaly_colors(
    excel_file=file_path,
    sheet_name="통합_원본데이터_Fixed",
    case_col="Case No.",
    create_backup=False  # 백업 없이 테스트
)

print()
print("결과:")
print(f"  Success: {result.get('success')}")
print(f"  Message: {result.get('message')}")
print(f"  Applied: {result.get('applied_count', 0)}건")
print(f"  Counts: {result.get('counts', {})}")

