#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsung Stock On Hand Report vs 최종 보고서 DSV Indoor 차이점 분석
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 파일 경로
samsung_file = Path("data/Samsung Stock On Hand Report_29-DEC-25.xlsx")
latest_report = sorted(Path("data/processed/reports").glob("HVDC_입고로직_종합리포트_*.xlsx"))[-1]

print("=" * 80)
print("DSV Indoor 차이점 상세 분석")
print("=" * 80)
print(f"\n[1] 파일 로드")
print(f"  Samsung Stock On Hand Report: {samsung_file.name}")
print(f"  최종 보고서: {latest_report.name}")

# Samsung 파일 로드
try:
    # 시트 목록 확인
    samsung_sheets = pd.ExcelFile(samsung_file).sheet_names
    print(f"\n  Samsung 파일 시트: {samsung_sheets}")
    
    # 첫 번째 시트 또는 메인 시트 로드
    samsung_df = pd.read_excel(samsung_file, sheet_name=0)
    print(f"  Samsung 데이터: {len(samsung_df):,}행, {len(samsung_df.columns)}컬럼")
except Exception as e:
    print(f"  [ERROR] Samsung 파일 로드 실패: {e}")
    samsung_df = None

# 최종 보고서 로드
try:
    # 통합_원본데이터_Fixed 시트 사용
    final_df = pd.read_excel(latest_report, sheet_name="통합_원본데이터_Fixed")
    print(f"  최종 보고서 데이터: {len(final_df):,}행, {len(final_df.columns)}컬럼")
except Exception as e:
    print(f"  [ERROR] 최종 보고서 로드 실패: {e}")
    final_df = None

if samsung_df is None or final_df is None:
    print("\n[ERROR] 파일 로드 실패로 분석을 중단합니다.")
    exit(1)

# DSV Indoor 컬럼 찾기
print(f"\n[2] DSV Indoor 컬럼 탐지")
print("-" * 80)

# Samsung 파일에서 DSV Indoor 컬럼 찾기
samsung_dsv_cols = [col for col in samsung_df.columns if "DSV" in str(col) and "Indoor" in str(col)]
if not samsung_dsv_cols:
    # 대소문자 무시 검색
    samsung_dsv_cols = [col for col in samsung_df.columns if "dsv" in str(col).lower() and "indoor" in str(col).lower()]
if not samsung_dsv_cols:
    # 부분 일치 검색
    samsung_dsv_cols = [col for col in samsung_df.columns if "indoor" in str(col).lower()]

print(f"  Samsung 파일 DSV Indoor 컬럼 후보: {samsung_dsv_cols}")
samsung_dsv_col = samsung_dsv_cols[0] if samsung_dsv_cols else None

# 최종 보고서에서 DSV Indoor 컬럼 찾기
final_dsv_cols = [col for col in final_df.columns if "DSV Indoor" in str(col)]
if not final_dsv_cols:
    final_dsv_cols = [col for col in final_df.columns if "dsv" in str(col).lower() and "indoor" in str(col).lower()]

print(f"  최종 보고서 DSV Indoor 컬럼 후보: {final_dsv_cols}")
final_dsv_col = final_dsv_cols[0] if final_dsv_cols else "DSV Indoor"

if not samsung_dsv_col:
    print(f"\n[ERROR] Samsung 파일에서 DSV Indoor 컬럼을 찾을 수 없습니다.")
    print(f"  사용 가능한 컬럼: {list(samsung_df.columns)[:20]}...")
    exit(1)

# Case No 컬럼 찾기
print(f"\n[3] Case No 컬럼 탐지")
print("-" * 80)

case_col_candidates = ["Case No.", "Case No", "CaseNo", "Case", "CASE NO", "CASE_NO"]
samsung_case_col = None
final_case_col = None

for col in case_col_candidates:
    if col in samsung_df.columns:
        samsung_case_col = col
        break
    # 부분 일치
    matching = [c for c in samsung_df.columns if col.lower() in str(c).lower()]
    if matching:
        samsung_case_col = matching[0]
        break

for col in case_col_candidates:
    if col in final_df.columns:
        final_case_col = col
        break
    matching = [c for c in final_df.columns if col.lower() in str(c).lower()]
    if matching:
        final_case_col = matching[0]
        break

print(f"  Samsung Case No 컬럼: {samsung_case_col}")
print(f"  최종 보고서 Case No 컬럼: {final_case_col}")

if not samsung_case_col or not final_case_col:
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

# 최종 보고서: DSV Indoor에 값이 있는 케이스
final_dsv_cases = final_df[final_df[final_dsv_col].notna()].copy()
final_dsv_cases = final_dsv_cases[final_dsv_cases[final_dsv_col] != ""]
final_case_set = set(final_dsv_cases[final_case_col].astype(str).str.strip())

print(f"  최종 보고서 DSV Indoor 케이스 수: {len(final_case_set):,}건")
if len(final_case_set) > 0:
    print(f"    샘플 케이스: {list(final_case_set)[:5]}")

# 차이점 분석
print(f"\n[5] 차이점 상세 분석")
print("=" * 80)

# 1. Samsung에만 있는 케이스
only_samsung = samsung_case_set - final_case_set
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

# 2. 최종 보고서에만 있는 케이스
only_final = final_case_set - samsung_case_set
print(f"\n[5-2] 최종 보고서에만 있는 DSV Indoor 케이스: {len(only_final):,}건")
if only_final:
    print(f"  샘플 (최대 20개): {list(only_final)[:20]}")
    only_final_df = final_dsv_cases[final_dsv_cases[final_case_col].astype(str).str.strip().isin(only_final)]
    if len(only_final_df) > 0:
        print(f"\n  상세 정보 (최대 10건):")
        display_cols = [final_case_col, final_dsv_col]
        if "Description" in only_final_df.columns:
            display_cols.append("Description")
        if "Site" in only_final_df.columns:
            display_cols.append("Site")
        available_cols = [c for c in display_cols if c in only_final_df.columns]
        print(only_final_df[available_cols].head(10).to_string())

# 3. 공통 케이스
common_cases = samsung_case_set & final_case_set
print(f"\n[5-3] 공통 DSV Indoor 케이스: {len(common_cases):,}건")

# 4. 날짜 비교 (공통 케이스)
if common_cases:
    print(f"\n[5-4] 공통 케이스 날짜 비교")
    common_list = list(common_cases)[:100]  # 최대 100개만 비교
    
    samsung_common = samsung_dsv_cases[samsung_dsv_cases[samsung_case_col].astype(str).str.strip().isin(common_list)]
    final_common = final_dsv_cases[final_dsv_cases[final_case_col].astype(str).str.strip().isin(common_list)]
    
    # 날짜 컬럼 찾기
    date_cols_samsung = [col for col in samsung_common.columns if "date" in str(col).lower() or "일자" in str(col)]
    date_cols_final = [col for col in final_common.columns if "date" in str(col).lower() or "일자" in str(col)]
    
    date_diff_count = 0
    date_diff_samples = []
    for case in common_list[:50]:  # 샘플 50개만
        samsung_row = samsung_common[samsung_common[samsung_case_col].astype(str).str.strip() == case]
        final_row = final_common[final_common[final_case_col].astype(str).str.strip() == case]
        
        if len(samsung_row) > 0 and len(final_row) > 0:
            samsung_date = samsung_row[samsung_dsv_col].iloc[0]
            final_date = final_row[final_dsv_col].iloc[0]
            
            if pd.notna(samsung_date) and pd.notna(final_date):
                if str(samsung_date) != str(final_date):
                    date_diff_count += 1
                    if len(date_diff_samples) < 5:
                        date_diff_samples.append({
                            "Case": case,
                            "Samsung": str(samsung_date),
                            "Final": str(final_date)
                        })
    
    print(f"  날짜 차이 케이스 (샘플 50개 중): {date_diff_count}건")
    if date_diff_samples:
        print(f"  날짜 차이 샘플:")
        for sample in date_diff_samples:
            print(f"    Case {sample['Case']}: Samsung={sample['Samsung']}, Final={sample['Final']}")

# 5. 요약 통계
print(f"\n[6] 요약 통계")
print("=" * 80)
print(f"  Samsung DSV Indoor 총 케이스: {len(samsung_case_set):,}건")
print(f"  최종 보고서 DSV Indoor 총 케이스: {len(final_case_set):,}건")
print(f"  공통 케이스: {len(common_cases):,}건")
print(f"  Samsung에만 있음: {len(only_samsung):,}건")
print(f"  최종 보고서에만 있음: {len(only_final):,}건")
if max(len(samsung_case_set), len(final_case_set)) > 0:
    diff_rate = abs(len(samsung_case_set) - len(final_case_set)) / max(len(samsung_case_set), len(final_case_set)) * 100
    print(f"  차이율: {diff_rate:.2f}%")

# 결과를 파일로 저장
output_file = Path("data/analysis/dsv_indoor_comparison_report.txt")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("DSV Indoor 차이점 상세 분석 보고서\n")
    f.write("=" * 80 + "\n")
    f.write(f"\n분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Samsung 파일: {samsung_file.name}\n")
    f.write(f"최종 보고서: {latest_report.name}\n")
    f.write(f"\n요약:\n")
    f.write(f"  Samsung DSV Indoor: {len(samsung_case_set):,}건\n")
    f.write(f"  최종 보고서 DSV Indoor: {len(final_case_set):,}건\n")
    f.write(f"  차이: {abs(len(samsung_case_set) - len(final_case_set)):,}건\n")
    f.write(f"\nSamsung에만 있는 케이스 ({len(only_samsung):,}건):\n")
    for case in list(only_samsung)[:200]:
        f.write(f"  {case}\n")
    f.write(f"\n최종 보고서에만 있는 케이스 ({len(only_final):,}건):\n")
    for case in list(only_final)[:200]:
        f.write(f"  {case}\n")

print(f"\n[7] 결과 저장")
print(f"  분석 결과: {output_file}")

print("\n" + "=" * 80)
print("분석 완료!")
print("=" * 80)

