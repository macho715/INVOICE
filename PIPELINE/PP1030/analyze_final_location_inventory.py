#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final_Location 기준 창고/현장 최종 재고 분석
DSV Indoor와 Final_Location 관계 분석
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter

# 파일 경로
hitachi_csv = Path("data/processed/reports/HITACHI_원본데이터_FULL_fixed.csv")
samsung_file = Path("data/Samsung Stock On Hand Report_29-DEC-25.xlsx")

print("=" * 80)
print("Final_Location 기준 창고/현장 최종 재고 분석")
print("=" * 80)

# HITACHI CSV 로드
print(f"\n[1] 파일 로드")
print(f"  HITACHI CSV: {hitachi_csv.name}")
hitachi_df = pd.read_csv(hitachi_csv, encoding='utf-8')
print(f"  총 데이터: {len(hitachi_df):,}행, {len(hitachi_df.columns)}컬럼")

# Final_Location 컬럼 확인
if "Final_Location" not in hitachi_df.columns:
    print("\n[ERROR] Final_Location 컬럼을 찾을 수 없습니다.")
    print(f"  사용 가능한 컬럼: {list(hitachi_df.columns)}")
    exit(1)

# Final_Location 값 분포 확인
print(f"\n[2] Final_Location 값 분포")
print("-" * 80)
location_counts = hitachi_df["Final_Location"].value_counts()
print(location_counts)

# 창고와 현장 구분
print(f"\n[3] 창고/현장 구분")
print("-" * 80)

# 창고 목록 (일반적인 창고 이름 패턴)
warehouse_keywords = ["DSV", "DHL", "AAA", "MOSB", "Hauler", "JDN", "MZP", "Al Markaz", "Outdoor", "Indoor"]
site_keywords = ["DAS", "MIR", "SHU", "AGI"]

def classify_location(loc):
    """위치를 창고/현장으로 분류"""
    if pd.isna(loc) or loc == "":
        return "미분류"
    loc_str = str(loc).upper()
    
    # 현장 확인
    for site in site_keywords:
        if site in loc_str:
            return "현장"
    
    # 창고 확인
    for wh in warehouse_keywords:
        if wh.upper() in loc_str:
            return "창고"
    
    return "기타"

hitachi_df["Location_Type"] = hitachi_df["Final_Location"].apply(classify_location)

location_type_counts = hitachi_df["Location_Type"].value_counts()
print(location_type_counts)

# DSV Indoor와 Final_Location 관계 분석
print(f"\n[4] DSV Indoor와 Final_Location 관계 분석")
print("-" * 80)

# DSV Indoor에 값이 있는 케이스
dsv_indoor_cases = hitachi_df[hitachi_df["DSV Indoor"].notna()].copy()
dsv_indoor_cases = dsv_indoor_cases[dsv_indoor_cases["DSV Indoor"] != ""]

print(f"  DSV Indoor 케이스 수: {len(dsv_indoor_cases):,}건")

# DSV Indoor 케이스의 Final_Location 분포
if len(dsv_indoor_cases) > 0:
    dsv_location_counts = dsv_indoor_cases["Final_Location"].value_counts()
    print(f"\n  DSV Indoor 케이스의 Final_Location 분포:")
    print(dsv_location_counts.head(20))
    
    dsv_location_type_counts = dsv_indoor_cases["Location_Type"].value_counts()
    print(f"\n  DSV Indoor 케이스의 Location_Type 분포:")
    print(dsv_location_type_counts)

# 창고별 최종 재고 집계
print(f"\n[5] 창고별 최종 재고 집계")
print("=" * 80)

warehouse_df = hitachi_df[hitachi_df["Location_Type"] == "창고"].copy()
print(f"  창고 위치 총 케이스: {len(warehouse_df):,}건")

warehouse_location_counts = warehouse_df["Final_Location"].value_counts()
print(f"\n  창고별 케이스 수:")
for loc, count in warehouse_location_counts.items():
    print(f"    {loc}: {count:,}건")

# 현장별 최종 재고 집계
print(f"\n[6] 현장별 최종 재고 집계")
print("=" * 80)

site_df = hitachi_df[hitachi_df["Location_Type"] == "현장"].copy()
print(f"  현장 위치 총 케이스: {len(site_df):,}건")

site_location_counts = site_df["Final_Location"].value_counts()
print(f"\n  현장별 케이스 수:")
for loc, count in site_location_counts.items():
    print(f"    {loc}: {count:,}건")

# DSV Indoor 기준 창고/현장 집계
print(f"\n[7] DSV Indoor 기준 창고/현장 집계")
print("=" * 80)

if len(dsv_indoor_cases) > 0:
    dsv_warehouse = dsv_indoor_cases[dsv_indoor_cases["Location_Type"] == "창고"]
    dsv_site = dsv_indoor_cases[dsv_indoor_cases["Location_Type"] == "현장"]
    dsv_other = dsv_indoor_cases[dsv_indoor_cases["Location_Type"].isin(["기타", "미분류"])]
    
    print(f"  DSV Indoor 케이스 중:")
    print(f"    창고 위치: {len(dsv_warehouse):,}건")
    print(f"    현장 위치: {len(dsv_site):,}건")
    print(f"    기타/미분류: {len(dsv_other):,}건")
    
    if len(dsv_warehouse) > 0:
        print(f"\n  DSV Indoor - 창고별 상세:")
        dsv_wh_counts = dsv_warehouse["Final_Location"].value_counts()
        for loc, count in dsv_wh_counts.items():
            print(f"    {loc}: {count:,}건")
    
    if len(dsv_site) > 0:
        print(f"\n  DSV Indoor - 현장별 상세:")
        dsv_site_counts = dsv_site["Final_Location"].value_counts()
        for loc, count in dsv_site_counts.items():
            print(f"    {loc}: {count:,}건")

# 전체 요약
print(f"\n[8] 전체 요약")
print("=" * 80)
print(f"  총 데이터: {len(hitachi_df):,}건")
print(f"  창고 위치: {len(warehouse_df):,}건 ({len(warehouse_df)/len(hitachi_df)*100:.2f}%)")
print(f"  현장 위치: {len(site_df):,}건 ({len(site_df)/len(hitachi_df)*100:.2f}%)")
print(f"  기타/미분류: {len(hitachi_df[hitachi_df['Location_Type'].isin(['기타', '미분류'])]):,}건")

# 결과 저장
output_file = Path("data/analysis/final_location_inventory_report.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("Final_Location 기준 창고/현장 최종 재고 분석 보고서\n")
    f.write("=" * 80 + "\n")
    f.write(f"\n분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"파일: {hitachi_csv.name}\n")
    f.write(f"\n총 데이터: {len(hitachi_df):,}건\n")
    f.write(f"\n창고 위치: {len(warehouse_df):,}건\n")
    f.write(f"현장 위치: {len(site_df):,}건\n")
    f.write(f"\n창고별 상세:\n")
    for loc, count in warehouse_location_counts.items():
        f.write(f"  {loc}: {count:,}건\n")
    f.write(f"\n현장별 상세:\n")
    for loc, count in site_location_counts.items():
        f.write(f"  {loc}: {count:,}건\n")
    if len(dsv_indoor_cases) > 0:
        f.write(f"\nDSV Indoor 케이스 ({len(dsv_indoor_cases):,}건):\n")
        f.write(f"  창고 위치: {len(dsv_warehouse):,}건\n")
        f.write(f"  현장 위치: {len(dsv_site):,}건\n")

print(f"\n[9] 결과 저장")
print(f"  분석 결과: {output_file}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)

