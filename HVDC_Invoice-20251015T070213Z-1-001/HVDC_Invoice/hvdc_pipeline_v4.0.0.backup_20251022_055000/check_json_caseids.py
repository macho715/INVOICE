#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Case IDs in JSON anomaly report"""

import json
import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

with open('data/anomaly/HVDC_anomaly_report.json', encoding='utf-8') as f:
    anomalies = json.load(f)

print(f"총 이상치 건수: {len(anomalies)}")
print()

# 이상치 유형별 집계
from collections import Counter
type_counter = Counter()
for a in anomalies:
    type_counter[a.get('Anomaly_Type', 'Unknown')] += 1

print("이상치 유형별 분포:")
for atype, count in type_counter.most_common():
    print(f"  {atype}: {count}건")
print()

# Case_ID 샘플 확인
print("Case_ID 샘플 (처음 20개):")
for i, a in enumerate(anomalies[:20]):
    case_id = a.get('Case_ID', 'N/A')
    atype = a.get('Anomaly_Type', 'Unknown')
    severity = a.get('Severity', 'Unknown')
    print(f"  {i+1}. Case_ID=[{case_id}], Type={atype}, Severity={severity}")

# Case_ID가 실제 숫자인지 확인
print()
print("Case_ID 타입 분석:")
numeric_ids = sum(1 for a in anomalies if str(a.get('Case_ID', '')).isdigit())
empty_ids = sum(1 for a in anomalies if not a.get('Case_ID') or str(a.get('Case_ID')).strip() == '')
print(f"  숫자 ID: {numeric_ids}개")
print(f"  빈 ID: {empty_ids}개")
print(f"  기타: {len(anomalies) - numeric_ids - empty_ids}개")

