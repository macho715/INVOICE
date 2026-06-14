#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsung Stock On Hand Report vs Final_Location 보고서 비교 분석
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import Counter

# 파일 경로
samsung_file = Path("data/Samsung Stock On Hand Report_29-DEC-25.xlsx")
hitachi_csv = Path("data/processed/reports/HITACHI_원본데이터_FULL_fixed.csv")

print("=" * 80)
print("Samsung 파일 vs Final_Location 보고서 비교 분석")
print("=" * 80)

# Samsung 파일 로드
print(f"\n[1] Samsung 파일 분석")
print("-" * 80)
samsung_df = pd.read_excel(samsung_file, sheet_name=0)
print(f"  총 데이터: {len(samsung_df):,}행, {len(samsung_df.columns)}컬럼")
print(f"  컬럼 목록: {list(samsung_df.columns)}")

# Samsung 파일의 위치 관련 컬럼 확인
location_cols = [col for col in samsung_df.columns 
                 if any(x in str(col).lower() for x in ['dsv', 'indoor', 'outdoor', 'site', 'warehouse', 'location'])]
print(f"\n  위치 관련 컬럼: {location_cols}")

# Samsung 파일의 창고/현장별 집계
print(f"\n[2] Samsung 파일 창고/현장별 집계")
print("-" * 80)

# DSV Indoor 케이스
if "DSV Indoor" in samsung_df.columns:
    samsung_dsv_indoor = samsung_df[samsung_df["DSV Indoor"].notna()].copy()
    samsung_dsv_indoor = samsung_dsv_indoor[samsung_dsv_indoor["DSV Indoor"] != ""]
    print(f"  DSV Indoor 케이스: {len(samsung_dsv_indoor):,}건")

# 각 위치 컬럼별 집계
warehouse_cols = ["DSV Indoor", "DSV Outdoor", "DSV Al Markaz", "DSV MZP", 
                  "MOSB", "Hauler Indoor", "DHL WH", "AAA Storage"]
site_cols = ["DAS", "MIR", "SHU", "AGI"]

samsung_warehouse_counts = {}
samsung_site_counts = {}

for col in warehouse_cols:
    if col in samsung_df.columns:
        count = samsung_df[samsung_df[col].notna() & (samsung_df[col] != "")].shape[0]
        if count > 0:
            samsung_warehouse_counts[col] = count

for col in site_cols:
    if col in samsung_df.columns:
        count = samsung_df[samsung_df[col].notna() & (samsung_df[col] != "")].shape[0]
        if count > 0:
            samsung_site_counts[col] = count

print(f"\n  창고별 케이스 수:")
for wh, count in samsung_warehouse_counts.items():
    print(f"    {wh}: {count:,}건")

print(f"\n  현장별 케이스 수:")
for site, count in samsung_site_counts.items():
    print(f"    {site}: {count:,}건")

# HITACHI CSV 로드 및 Final_Location 기준 집계
print(f"\n[3] HITACHI CSV Final_Location 기준 집계")
print("-" * 80)
hitachi_df = pd.read_csv(hitachi_csv, encoding='utf-8')

# Final_Location 분포
final_location_counts = hitachi_df["Final_Location"].value_counts()
print(f"  Final_Location별 케이스 수:")
for loc, count in final_location_counts.items():
    print(f"    {loc}: {count:,}건")

# 창고/현장 구분
warehouse_keywords = ["DSV", "DHL", "AAA", "MOSB", "Hauler", "JDN", "MZP", "Al Markaz", "Outdoor", "Indoor"]
site_keywords = ["DAS", "MIR", "SHU", "AGI"]

def classify_location(loc):
    if pd.isna(loc) or loc == "":
        return "미분류"
    loc_str = str(loc).upper()
    for site in site_keywords:
        if site in loc_str:
            return "현장"
    for wh in warehouse_keywords:
        if wh.upper() in loc_str:
            return "창고"
    return "기타"

hitachi_df["Location_Type"] = hitachi_df["Final_Location"].apply(classify_location)
hitachi_warehouse = hitachi_df[hitachi_df["Location_Type"] == "창고"]
hitachi_site = hitachi_df[hitachi_df["Location_Type"] == "현장"]

print(f"\n  창고 위치 총계: {len(hitachi_warehouse):,}건")
print(f"  현장 위치 총계: {len(hitachi_site):,}건")

# 비교 분석
print(f"\n[4] Samsung vs HITACHI 비교")
print("=" * 80)

# 창고 비교
print(f"\n  창고별 비교:")
warehouse_locations = set(list(samsung_warehouse_counts.keys()) + 
                         [loc for loc in final_location_counts.index 
                          if any(wh in str(loc).upper() for wh in warehouse_keywords)])

for loc in sorted(warehouse_locations):
    samsung_count = samsung_warehouse_counts.get(loc, 0)
    hitachi_count = final_location_counts.get(loc, 0)
    diff = hitachi_count - samsung_count
    print(f"    {loc}:")
    print(f"      Samsung: {samsung_count:,}건")
    print(f"      HITACHI (Final_Location): {hitachi_count:,}건")
    if diff != 0:
        print(f"      차이: {diff:+,}건 ({diff/max(samsung_count, hitachi_count)*100:.2f}%)")

# 현장 비교
print(f"\n  현장별 비교:")
site_locations = set(list(samsung_site_counts.keys()) + 
                    [loc for loc in final_location_counts.index 
                     if any(site in str(loc).upper() for site in site_keywords)])

for loc in sorted(site_locations):
    samsung_count = samsung_site_counts.get(loc, 0)
    hitachi_count = final_location_counts.get(loc, 0)
    diff = hitachi_count - samsung_count
    print(f"    {loc}:")
    print(f"      Samsung: {samsung_count:,}건")
    print(f"      HITACHI (Final_Location): {hitachi_count:,}건")
    if diff != 0:
        print(f"      차이: {diff:+,}건 ({diff/max(samsung_count, hitachi_count)*100:.2f}%)")

# 요약
print(f"\n[5] 요약")
print("=" * 80)
print(f"  Samsung 총 케이스: {len(samsung_df):,}건")
print(f"  HITACHI 총 케이스: {len(hitachi_df):,}건")
print(f"  Samsung 창고 합계: {sum(samsung_warehouse_counts.values()):,}건")
print(f"  HITACHI 창고 합계: {len(hitachi_warehouse):,}건")
print(f"  Samsung 현장 합계: {sum(samsung_site_counts.values()):,}건")
print(f"  HITACHI 현장 합계: {len(hitachi_site):,}건")

# DSV Indoor 특별 분석
print(f"\n[6] DSV Indoor 특별 분석")
print("=" * 80)

samsung_dsv_count = samsung_warehouse_counts.get("DSV Indoor", 0)
hitachi_dsv_final = final_location_counts.get("DSV Indoor", 0)

print(f"  Samsung DSV Indoor (컬럼에 값 있음): {samsung_dsv_count:,}건")
print(f"  HITACHI Final_Location='DSV Indoor': {hitachi_dsv_final:,}건")
print(f"  차이: {hitachi_dsv_final - samsung_dsv_count:+,}건")

# HITACHI에서 DSV Indoor 컬럼에 값이 있지만 Final_Location이 다른 경우
hitachi_dsv_indoor_col = hitachi_df[hitachi_df["DSV Indoor"].notna() & (hitachi_df["DSV Indoor"] != "")]
hitachi_dsv_indoor_but_different_final = hitachi_dsv_indoor_col[hitachi_dsv_indoor_col["Final_Location"] != "DSV Indoor"]

print(f"\n  HITACHI에서 DSV Indoor 컬럼에 값이 있지만 Final_Location이 다른 경우:")
print(f"    총 DSV Indoor 컬럼 값: {len(hitachi_dsv_indoor_col):,}건")
print(f"    Final_Location='DSV Indoor': {hitachi_dsv_final:,}건")
print(f"    Final_Location이 다른 경우: {len(hitachi_dsv_indoor_but_different_final):,}건")
if len(hitachi_dsv_indoor_but_different_final) > 0:
    print(f"\n    Final_Location 분포:")
    diff_final_counts = hitachi_dsv_indoor_but_different_final["Final_Location"].value_counts()
    for loc, count in diff_final_counts.head(10).items():
        print(f"      {loc}: {count:,}건")

# 결과 저장
output_file = Path("data/analysis/samsung_vs_final_location_comparison.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("Samsung 파일 vs Final_Location 보고서 비교 분석\n")
    f.write("=" * 80 + "\n")
    f.write(f"\n분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"\nSamsung 파일:\n")
    f.write(f"  총 케이스: {len(samsung_df):,}건\n")
    f.write(f"  창고 합계: {sum(samsung_warehouse_counts.values()):,}건\n")
    f.write(f"  현장 합계: {sum(samsung_site_counts.values()):,}건\n")
    f.write(f"\nHITACHI Final_Location:\n")
    f.write(f"  총 케이스: {len(hitachi_df):,}건\n")
    f.write(f"  창고 합계: {len(hitachi_warehouse):,}건\n")
    f.write(f"  현장 합계: {len(hitachi_site):,}건\n")
    f.write(f"\n창고별 비교:\n")
    for loc in sorted(warehouse_locations):
        samsung_count = samsung_warehouse_counts.get(loc, 0)
        hitachi_count = final_location_counts.get(loc, 0)
        diff = hitachi_count - samsung_count
        f.write(f"  {loc}: Samsung={samsung_count:,}, HITACHI={hitachi_count:,}, 차이={diff:+,}\n")
    f.write(f"\n현장별 비교:\n")
    for loc in sorted(site_locations):
        samsung_count = samsung_site_counts.get(loc, 0)
        hitachi_count = final_location_counts.get(loc, 0)
        diff = hitachi_count - samsung_count
        f.write(f"  {loc}: Samsung={samsung_count:,}, HITACHI={hitachi_count:,}, 차이={diff:+,}\n")

print(f"\n[7] 결과 저장")
print(f"  분석 결과: {output_file}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)

