#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsung Stock On Hand Report vs HITACHI CSV - DSV Indoor 비교 분석
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 파일 경로
samsung_file = Path("data/Samsung Stock On Hand Report_29-DEC-25.xlsx")
hitachi_csv = Path("data/processed/reports/HITACHI_원본데이터_FULL_fixed.csv")

print("=" * 80)
print("DSV Indoor 비교 분석 (CSV 기준)")
print("=" * 80)
print(f"\n[1] 파일 로드")
print(f"  Samsung 파일: {samsung_file.name}")
print(f"  HITACHI CSV: {hitachi_csv.name}")

# Samsung 파일 로드
try:
    samsung_df = pd.read_excel(samsung_file, sheet_name=0)
    print(f"  Samsung 데이터: {len(samsung_df):,}행, {len(samsung_df.columns)}컬럼")
except Exception as e:
    print(f"  [ERROR] Samsung 파일 로드 실패: {e}")
    samsung_df = None

# HITACHI CSV 로드
try:
    hitachi_df = pd.read_csv(hitachi_csv, encoding='utf-8')
    print(f"  HITACHI CSV: {len(hitachi_df):,}행, {len(hitachi_df.columns)}컬럼")
except Exception as e:
    print(f"  [ERROR] HITACHI CSV 로드 실패: {e}")
    hitachi_df = None

if samsung_df is None or hitachi_df is None:
    print("\n[ERROR] 파일 로드 실패로 분석을 중단합니다.")
    exit(1)

# DSV Indoor 컬럼 찾기
print(f"\n[2] DSV Indoor 컬럼 탐지")
print("-" * 80)

# Samsung 파일에서 DSV Indoor 컬럼 찾기
samsung_dsv_cols = [col for col in samsung_df.columns if "DSV" in str(col) and "Indoor" in str(col)]
if not samsung_dsv_cols:
    samsung_dsv_cols = [col for col in samsung_df.columns if "dsv" in str(col).lower() and "indoor" in str(col).lower()]
if not samsung_dsv_cols:
    samsung_dsv_cols = [col for col in samsung_df.columns if "indoor" in str(col).lower()]

print(f"  Samsung DSV Indoor 컬럼 후보: {samsung_dsv_cols}")
samsung_dsv_col = samsung_dsv_cols[0] if samsung_dsv_cols else None

# HITACHI CSV에서 DSV Indoor 컬럼 찾기
hitachi_dsv_cols = [col for col in hitachi_df.columns if "DSV Indoor" in str(col)]
if not hitachi_dsv_cols:
    hitachi_dsv_cols = [col for col in hitachi_df.columns if "dsv" in str(col).lower() and "indoor" in str(col).lower()]

print(f"  HITACHI CSV DSV Indoor 컬럼 후보: {hitachi_dsv_cols}")
hitachi_dsv_col = hitachi_dsv_cols[0] if hitachi_dsv_cols else "DSV Indoor"

if not samsung_dsv_col:
    print(f"\n[ERROR] Samsung 파일에서 DSV Indoor 컬럼을 찾을 수 없습니다.")
    print(f"  사용 가능한 컬럼: {list(samsung_df.columns)[:20]}...")
    exit(1)

if not hitachi_dsv_col:
    print(f"\n[ERROR] HITACHI CSV에서 DSV Indoor 컬럼을 찾을 수 없습니다.")
    print(f"  사용 가능한 컬럼: {list(hitachi_df.columns)[:20]}...")
    exit(1)

# Case No 컬럼 찾기
print(f"\n[3] Case No 컬럼 탐지")
print("-" * 80)

case_col_candidates = ["Case No.", "Case No", "CaseNo", "Case", "CASE NO", "CASE_NO"]
samsung_case_col = None
hitachi_case_col = None

for col in case_col_candidates:
    if col in samsung_df.columns:
        samsung_case_col = col
        break
    matching = [c for c in samsung_df.columns if col.lower() in str(c).lower()]
    if matching:
        samsung_case_col = matching[0]
        break

for col in case_col_candidates:
    if col in hitachi_df.columns:
        hitachi_case_col = col
        break
    matching = [c for c in hitachi_df.columns if col.lower() in str(c).lower()]
    if matching:
        hitachi_case_col = matching[0]
        break

print(f"  Samsung Case No 컬럼: {samsung_case_col}")
print(f"  HITACHI Case No 컬럼: {hitachi_case_col}")

if not samsung_case_col or not hitachi_case_col:
    print(f"\n[ERROR] Case No 컬럼을 찾을 수 없습니다.")
    exit(1)

# DSV Indoor 데이터 비교
print(f"\n[4] DSV Indoor 데이터 비교")
print("-" * 80)

# Samsung 파일: DSV Indoor에 값이 있는 케이스
samsung_dsv_cases = samsung_df[samsung_df[samsung_dsv_col].notna()].copy()
samsung_dsv_cases = samsung_dsv_cases[samsung_dsv_cases[samsung_dsv_col] != ""]
samsung_case_set = set(samsung_dsv_cases[samsung_case_col].astype(str).str.strip())

print(f"  Samsung DSV Indoor 케이스 수: {len(samsung_case_set):,}건")
if len(samsung_case_set) > 0:
    print(f"    샘플 케이스: {list(samsung_case_set)[:5]}")

# HITACHI CSV: DSV Indoor에 값이 있는 케이스
hitachi_dsv_cases = hitachi_df[hitachi_df[hitachi_dsv_col].notna()].copy()
hitachi_dsv_cases = hitachi_dsv_cases[hitachi_dsv_cases[hitachi_dsv_col] != ""]
hitachi_case_set = set(hitachi_dsv_cases[hitachi_case_col].astype(str).str.strip())

print(f"  HITACHI CSV DSV Indoor 케이스 수: {len(hitachi_case_set):,}건")
if len(hitachi_case_set) > 0:
    print(f"    샘플 케이스: {list(hitachi_case_set)[:5]}")

# 차이점 분석
print(f"\n[5] 차이점 상세 분석")
print("=" * 80)

# 1. Samsung에만 있는 케이스
only_samsung = samsung_case_set - hitachi_case_set
print(f"\n[5-1] Samsung에만 있는 DSV Indoor 케이스: {len(only_samsung):,}건")
if only_samsung:
    print(f"  샘플 (최대 20개): {list(only_samsung)[:20]}")
    # 상세 정보
    only_samsung_df = samsung_dsv_cases[samsung_dsv_cases[samsung_case_col].astype(str).str.strip().isin(only_samsung)]
    if len(only_samsung_df) > 0:
        print(f"\n  상세 정보 (최대 10건):")
        display_cols = [samsung_case_col, samsung_dsv_col]
        if "Description" in only_samsung_df.columns:
            display_cols.append("Description")
        if "Site" in only_samsung_df.columns:
            display_cols.append("Site")
        available_cols = [c for c in display_cols if c in only_samsung_df.columns]
        print(only_samsung_df[available_cols].head(10).to_string())

# 2. HITACHI에만 있는 케이스
only_hitachi = hitachi_case_set - samsung_case_set
print(f"\n[5-2] HITACHI에만 있는 DSV Indoor 케이스: {len(only_hitachi):,}건")
if only_hitachi:
    print(f"  샘플 (최대 20개): {list(only_hitachi)[:20]}")
    only_hitachi_df = hitachi_dsv_cases[hitachi_dsv_cases[hitachi_case_col].astype(str).str.strip().isin(only_hitachi)]
    if len(only_hitachi_df) > 0:
        print(f"\n  상세 정보 (최대 10건):")
        display_cols = [hitachi_case_col, hitachi_dsv_col]
        if "Description" in only_hitachi_df.columns:
            display_cols.append("Description")
        if "Site" in only_hitachi_df.columns:
            display_cols.append("Site")
        available_cols = [c for c in display_cols if c in only_hitachi_df.columns]
        print(only_hitachi_df[available_cols].head(10).to_string())

# 3. 공통 케이스
common_cases = samsung_case_set & hitachi_case_set
print(f"\n[5-3] 공통 DSV Indoor 케이스: {len(common_cases):,}건")

# 4. 날짜 비교 (공통 케이스)
if common_cases:
    print(f"\n[5-4] 공통 케이스 날짜 비교")
    common_list = list(common_cases)[:100]  # 최대 100개만 비교
    
    samsung_common = samsung_dsv_cases[samsung_dsv_cases[samsung_case_col].astype(str).str.strip().isin(common_list)]
    hitachi_common = hitachi_dsv_cases[hitachi_dsv_cases[hitachi_case_col].astype(str).str.strip().isin(common_list)]
    
    date_diff_count = 0
    date_diff_samples = []
    for case in common_list[:50]:  # 샘플 50개만
        samsung_row = samsung_common[samsung_common[samsung_case_col].astype(str).str.strip() == case]
        hitachi_row = hitachi_common[hitachi_common[hitachi_case_col].astype(str).str.strip() == case]
        
        if len(samsung_row) > 0 and len(hitachi_row) > 0:
            samsung_date = samsung_row[samsung_dsv_col].iloc[0]
            hitachi_date = hitachi_row[hitachi_dsv_col].iloc[0]
            
            if pd.notna(samsung_date) and pd.notna(hitachi_date):
                if str(samsung_date) != str(hitachi_date):
                    date_diff_count += 1
                    if len(date_diff_samples) < 5:
                        date_diff_samples.append({
                            "Case": case,
                            "Samsung": str(samsung_date),
                            "HITACHI": str(hitachi_date)
                        })
    
    print(f"  날짜 차이 케이스 (샘플 50개 중): {date_diff_count}건")
    if date_diff_samples:
        print(f"  날짜 차이 샘플:")
        for sample in date_diff_samples:
            print(f"    Case {sample['Case']}: Samsung={sample['Samsung']}, HITACHI={sample['HITACHI']}")

# 5. 요약 통계
print(f"\n[6] 요약 통계")
print("=" * 80)
print(f"  Samsung DSV Indoor 총 케이스: {len(samsung_case_set):,}건")
print(f"  HITACHI CSV DSV Indoor 총 케이스: {len(hitachi_case_set):,}건")
print(f"  공통 케이스: {len(common_cases):,}건")
print(f"  Samsung에만 있음: {len(only_samsung):,}건")
print(f"  HITACHI에만 있음: {len(only_hitachi):,}건")
if max(len(samsung_case_set), len(hitachi_case_set)) > 0:
    diff_rate = abs(len(samsung_case_set) - len(hitachi_case_set)) / max(len(samsung_case_set), len(hitachi_case_set)) * 100
    print(f"  차이율: {diff_rate:.2f}%")

# 결과를 파일로 저장
output_file = Path("data/analysis/dsv_indoor_csv_comparison_report.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("DSV Indoor 비교 분석 보고서 (HITACHI CSV 기준)\n")
    f.write("=" * 80 + "\n")
    f.write(f"\n분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Samsung 파일: {samsung_file.name}\n")
    f.write(f"HITACHI CSV: {hitachi_csv.name}\n")
    f.write(f"\n요약:\n")
    f.write(f"  Samsung DSV Indoor: {len(samsung_case_set):,}건\n")
    f.write(f"  HITACHI CSV DSV Indoor: {len(hitachi_case_set):,}건\n")
    f.write(f"  차이: {abs(len(samsung_case_set) - len(hitachi_case_set)):,}건\n")
    f.write(f"\nSamsung에만 있는 케이스 ({len(only_samsung):,}건):\n")
    for case in sorted(only_samsung)[:200]:
        f.write(f"  {case}\n")
    f.write(f"\nHITACHI에만 있는 케이스 ({len(only_hitachi):,}건):\n")
    for case in sorted(only_hitachi)[:200]:
        f.write(f"  {case}\n")

print(f"\n[7] 결과 저장")
print(f"  분석 결과: {output_file}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)

