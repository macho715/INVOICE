#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 1 실행 결과 확인"""

import pandas as pd
from pathlib import Path

print("=" * 60)
print("Stage 1 실행 결과 확인")
print("=" * 60)

# 병합 파일 확인
merged_path = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
if merged_path.exists():
    df = pd.read_excel(merged_path)
    print(f"\n병합 파일: {merged_path.name}")
    print(f"  - 총 행수: {len(df):,}행")
    print(f"  - 총 컬럼: {len(df.columns)}개")
    
    if "Source_Sheet" in df.columns:
        print(f"\nSource_Sheet 분포:")
        sheet_dist = df["Source_Sheet"].value_counts()
        for sheet, count in sheet_dist.items():
            print(f"  - {sheet}: {count:,}행")
    
    if "Source_Vendor" in df.columns:
        print(f"\nSource_Vendor 분포:")
        vendor_dist = df["Source_Vendor"].value_counts()
        for vendor, count in vendor_dist.items():
            print(f"  - {vendor}: {count:,}행")
else:
    print("\n병합 파일이 없습니다.")

# 멀티 시트 파일 확인
multi_path = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
if multi_path.exists():
    print(f"\n\n멀티 시트 파일: {multi_path.name}")
    xl = pd.ExcelFile(multi_path)
    print(f"  - 시트 목록: {xl.sheet_names}")
    
    for sheet_name in xl.sheet_names:
        df_sheet = pd.read_excel(multi_path, sheet_name=sheet_name)
        print(f"  - {sheet_name}: {len(df_sheet):,}행, {len(df_sheet.columns)}컬럼")

# 원본 파일과 비교
print("\n" + "=" * 60)
print("원본 파일 비교")
print("=" * 60)

original_data = [
    ("Case List(HE).xlsx", "Case List", 1776),
    ("HVDC WAREHOUSE_HITACHI(HE).xlsx", "Case List, RIL", 7006),
    ("HVDC WAREHOUSE_HITACHI(HE).xlsx", "HE Local", 84),
    ("HVDC WAREHOUSE_HITACHI(HE).xlsx", "HE-0214,0252 (Capacitor)", 107),
]

print("\n원본 예상 데이터:")
total_original = 0
for fname, sheet, rows in original_data:
    print(f"  {fname} | {sheet}: {rows:,}행")
    total_original += rows
print(f"  총합: {total_original:,}행")

if merged_path.exists():
    print(f"\n실제 처리된 데이터: {len(df):,}행")
    print(f"차이: {total_original - len(df):,}행 ({(total_original - len(df))/total_original*100:.1f}%)")

