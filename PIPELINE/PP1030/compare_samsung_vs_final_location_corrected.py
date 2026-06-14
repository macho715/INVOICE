#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsung 파일 vs Final_Location 기준 최종 재고 비교 분석 (수정)
Final_Location = 창고/현장에 있는 최종 재고 개수
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 파일 경로
samsung_file = Path("data/Samsung Stock On Hand Report_29-DEC-25.xlsx")
hitachi_csv = Path("data/processed/reports/HITACHI_원본데이터_FULL_fixed.csv")

print("=" * 80)
print("Samsung 파일 vs Final_Location 기준 최종 재고 비교 (수정)")
print("=" * 80)

# 1. HITACHI CSV 로드 및 Final_Location 기준 집계
print(f"\n[1] HITACHI CSV Final_Location 기준 최종 재고 집계")
print("-" * 80)
hitachi_df = pd.read_csv(hitachi_csv, encoding='utf-8')

# Final_Location별 케이스 수 (최종 재고 개수)
final_location_counts = hitachi_df["Final_Location"].value_counts()
print(f"  Final_Location별 최종 재고 개수:")
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

warehouse_total = len(hitachi_df[hitachi_df["Location_Type"] == "창고"])
site_total = len(hitachi_df[hitachi_df["Location_Type"] == "현장"])

print(f"\n  창고 위치 총계: {warehouse_total:,}건")
print(f"  현장 위치 총계: {site_total:,}건")

# 2. Samsung 파일 분석
print(f"\n[2] Samsung 파일 분석")
print("-" * 80)
samsung_df = pd.read_excel(samsung_file, sheet_name=0)
print(f"  총 데이터: {len(samsung_df):,}행")

# Samsung 파일은 DSV Indoor 컬럼만 있음
if "DSV Indoor" in samsung_df.columns:
    samsung_dsv_count = samsung_df[samsung_df["DSV Indoor"].notna() & (samsung_df["DSV Indoor"] != "")].shape[0]
    print(f"  DSV Indoor 컬럼에 값이 있는 케이스: {samsung_dsv_count:,}건")

# 3. 비교 분석
print(f"\n[3] 비교 분석")
print("=" * 80)

# Samsung의 DSV Indoor 케이스들의 Final_Location 분포 확인
print(f"\n[3-1] Samsung DSV Indoor 케이스의 Final_Location 분포")
print("-" * 80)

# Case No.로 매칭
samsung_cases = set(samsung_df[samsung_df["DSV Indoor"].notna() & (samsung_df["DSV Indoor"] != "")]["Case No."].astype(str).str.strip())
hitachi_cases = hitachi_df["Case No."].astype(str).str.strip()

# 매칭된 케이스 찾기
matched_cases = samsung_cases & set(hitachi_cases)
print(f"  Samsung DSV Indoor 케이스: {len(samsung_cases):,}건")
print(f"  HITACHI에서 매칭된 케이스: {len(matched_cases):,}건")

if len(matched_cases) > 0:
    matched_df = hitachi_df[hitachi_df["Case No."].astype(str).str.strip().isin(matched_cases)]
    matched_final_location = matched_df["Final_Location"].value_counts()
    
    print(f"\n  매칭된 케이스의 Final_Location 분포:")
    for loc, count in matched_final_location.items():
        print(f"    {loc}: {count:,}건")

# 4. Final_Location='DSV Indoor'와 비교
print(f"\n[3-2] Final_Location='DSV Indoor' 최종 재고")
print("-" * 80)
hitachi_dsv_final = final_location_counts.get("DSV Indoor", 0)
print(f"  HITACHI Final_Location='DSV Indoor': {hitachi_dsv_final:,}건")
print(f"  Samsung DSV Indoor 컬럼 값: {samsung_dsv_count:,}건")
print(f"  차이: {samsung_dsv_count - hitachi_dsv_final:+,}건")

# 5. 전체 창고/현장별 최종 재고 비교
print(f"\n[4] 창고/현장별 최종 재고 비교")
print("=" * 80)

print(f"\n  창고별 최종 재고 (Final_Location 기준):")
warehouse_locations = [loc for loc in final_location_counts.index if classify_location(loc) == "창고"]
for loc in sorted(warehouse_locations):
    count = final_location_counts[loc]
    print(f"    {loc}: {count:,}건")

print(f"\n  현장별 최종 재고 (Final_Location 기준):")
site_locations = [loc for loc in final_location_counts.index if classify_location(loc) == "현장"]
for loc in sorted(site_locations):
    count = final_location_counts[loc]
    print(f"    {loc}: {count:,}건")

# 결과 저장
output_file = Path("data/analysis/samsung_vs_final_location_corrected.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("Samsung 파일 vs Final_Location 기준 최종 재고 비교 (수정)\n")
    f.write("=" * 80 + "\n")
    f.write(f"\n분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"\nHITACHI Final_Location 기준 최종 재고:\n")
    f.write(f"  창고 위치: {warehouse_total:,}건\n")
    f.write(f"  현장 위치: {site_total:,}건\n")
    f.write(f"\n창고별 상세:\n")
    for loc in sorted(warehouse_locations):
        f.write(f"  {loc}: {final_location_counts[loc]:,}건\n")
    f.write(f"\n현장별 상세:\n")
    for loc in sorted(site_locations):
        f.write(f"  {loc}: {final_location_counts[loc]:,}건\n")

print(f"\n[5] 결과 저장")
print(f"  분석 결과: {output_file}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)

