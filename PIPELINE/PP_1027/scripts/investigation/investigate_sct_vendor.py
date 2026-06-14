#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor="SCT"인 화물 조사

Master 파일의 Vendor 컬럼에 "SCT" 값이 있는 화물이 Stage 1에서 업데이트되지 않는 문제 조사
"""
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import find_header_by_meaning

def investigate_sct_vendor():
    """Vendor="SCT"인 화물 조사"""
    
    print("=" * 80)
    print("Vendor='SCT' 화물 업데이트 누락 문제 조사")
    print("=" * 80)
    
    # 파일 로드
    master_file = PROJECT_ROOT / "data/raw/HITACHI/Case List_Hitachi.xlsx"
    warehouse_file = PROJECT_ROOT / "data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx"
    synced_file = PROJECT_ROOT / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    
    master_df = pd.read_excel(master_file, sheet_name="Case List, RIL")
    warehouse_df = pd.read_excel(warehouse_file, sheet_name="Case List, RIL")
    
    try:
        synced_df = pd.read_excel(synced_file, sheet_name="Merged Data")
    except:
        synced_df = pd.read_excel(synced_file, sheet_name=0)
    
    # 컬럼 찾기
    master_case_col = find_header_by_meaning(master_df, "case_number", required=False) or "Case No."
    wh_case_col = find_header_by_meaning(warehouse_df, "case_number", required=False) or "Case No."
    synced_case_col = find_header_by_meaning(synced_df, "case_number", required=False) or "Case No."
    
    print(f"\n[1] Master 파일 Vendor='SCT' 화물 분석")
    sct_master = master_df[master_df["Vendor"] == "SCT"].copy()
    print(f"  - Vendor='SCT' 레코드: {len(sct_master)}건")
    print(f"  - Case No 샘플: {sct_master[master_case_col].head(10).tolist()}")
    print(f"  - Description 샘플:")
    if "Description" in sct_master.columns:
        print(f"    {sct_master['Description'].head(5).tolist()}")
    
    # 날짜 컬럼 확인
    date_cols = ["DSV Al Markaz", "DSV Indoor", "DSV Outdoor"]
    for date_col in date_cols:
        if date_col in sct_master.columns:
            has_date = sct_master[date_col].notna().sum()
            print(f"  - {date_col} 있는 레코드: {has_date}건")
    
    # Warehouse에서 매칭 확인
    print(f"\n[2] Warehouse에서 매칭 확인")
    sct_case_nos = set(sct_master[master_case_col].dropna().astype(str))
    wh_case_nos = set(warehouse_df[wh_case_col].dropna().astype(str))
    
    matched = sct_case_nos & wh_case_nos
    not_matched = sct_case_nos - wh_case_nos
    
    print(f"  - SCT Case No 수: {len(sct_case_nos)}")
    print(f"  - Warehouse에 매칭됨: {len(matched)}건")
    print(f"  - Warehouse에 없음: {len(not_matched)}건")
    
    if len(not_matched) > 0:
        print(f"  - ⚠️ 매칭 안 된 Case No (첫 10개): {list(not_matched)[:10]}")
    
    # Synced 파일에서 확인
    print(f"\n[3] Synced 파일에서 Vendor='SCT' 확인")
    synced_case_nos = set(synced_df[synced_case_col].dropna().astype(str))
    
    synced_matched = sct_case_nos & synced_case_nos
    synced_not_matched = sct_case_nos - synced_case_nos
    
    print(f"  - Synced에 매칭됨: {len(synced_matched)}건")
    print(f"  - Synced에 없음: {len(synced_not_matched)}건")
    
    # Source_Vendor 확인
    if "Source_Vendor" in synced_df.columns:
        synced_sct_vendor = synced_df[synced_df["Source_Vendor"] == "SCT"]
        print(f"  - Source_Vendor='SCT': {len(synced_sct_vendor)}건")
    
    if "Vendor" in synced_df.columns:
        synced_vendor_sct = synced_df[synced_df["Vendor"] == "SCT"]
        print(f"  - Vendor='SCT': {len(synced_vendor_sct)}건")
    
    # 날짜 업데이트 확인
    print(f"\n[4] 날짜 업데이트 상태 확인")
    for date_col in date_cols:
        if date_col in master_df.columns and date_col in synced_df.columns:
            # Master에 날짜가 있는 SCT 화물
            master_sct_with_date = sct_master[sct_master[date_col].notna()]
            master_sct_cases = set(master_sct_with_date[master_case_col].dropna().astype(str))
            
            # Synced에서 해당 Case No의 날짜 상태
            synced_sct_rows = synced_df[synced_df[synced_case_col].isin(master_sct_cases)]
            synced_with_date = synced_sct_rows[synced_sct_rows[date_col].notna()]
            
            print(f"  - {date_col}:")
            print(f"    Master SCT에 날짜 있음: {len(master_sct_with_date)}건")
            print(f"    Synced에 날짜 반영됨: {len(synced_with_date)}건")
            
            if len(master_sct_with_date) > len(synced_with_date):
                missing = master_sct_with_date[
                    ~master_sct_with_date[master_case_col].isin(synced_with_date[synced_case_col])
                ]
                print(f"    ⚠️ 업데이트 안 된 Case No (첫 10개): {missing[master_case_col].head(10).tolist()}")
    
    # 결과 저장
    output_file = PROJECT_ROOT / "data/investigation/sct_vendor_analysis.xlsx"
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        sct_master.to_excel(writer, sheet_name='Master_SCT', index=False)
        
        if len(matched) > 0:
            wh_sct = warehouse_df[warehouse_df[wh_case_col].isin(matched)]
            wh_sct.to_excel(writer, sheet_name='Warehouse_SCT', index=False)
        
        if len(synced_matched) > 0:
            synced_sct = synced_df[synced_df[synced_case_col].isin(synced_matched)]
            synced_sct.to_excel(writer, sheet_name='Synced_SCT', index=False)
    
    print(f"\n[5] 결과 저장: {output_file}")
    print("\n" + "=" * 80)
    print("조사 완료")
    print("=" * 80)

if __name__ == "__main__":
    investigate_sct_vendor()

