#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCT Ref.No가 있는 화물의 업데이트 상태 확인

Master와 Warehouse를 비교하여 SCT Ref.No가 있는 화물이 제대로 업데이트되었는지 확인합니다.
"""
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import find_header_by_meaning

def verify_sct_updates():
    """SCT Ref.No 화물의 업데이트 상태 확인"""
    
    print("=" * 80)
    print("SCT Ref.No 화물 업데이트 상태 확인")
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
    
    wh_sct_col = "SCT Ref.No" if "SCT Ref.No" in warehouse_df.columns else None
    synced_sct_col = "SCT Ref.No" if "SCT Ref.No" in synced_df.columns else None
    
    if not wh_sct_col:
        print("❌ Warehouse에 SCT Ref.No 컬럼이 없습니다")
        return
    
    print(f"\n[1] Warehouse SCT Ref.No 분석")
    wh_sct_data = warehouse_df[warehouse_df[wh_sct_col].notna()]
    print(f"  - SCT Ref.No 있는 레코드: {len(wh_sct_data)}건")
    print(f"  - 첫 5개 Case No: {wh_sct_data[wh_case_col].head().tolist()}")
    print(f"  - 첫 5개 SCT Ref.No: {wh_sct_data[wh_sct_col].head().tolist()}")
    
    # Master에 있는 Case No와 매칭 확인
    master_case_set = set(master_df[master_case_col].dropna().astype(str))
    wh_case_set = set(wh_sct_data[wh_case_col].dropna().astype(str))
    
    common_cases = master_case_set & wh_case_set
    master_only = master_case_set - wh_case_set
    wh_only = wh_case_set - master_case_set
    
    print(f"\n[2] Case No 매칭 분석")
    print(f"  - Master Case No 수: {len(master_case_set)}")
    print(f"  - Warehouse SCT 있는 Case No 수: {len(wh_case_set)}")
    print(f"  - 공통 Case No: {len(common_cases)}")
    print(f"  - Master에만 있음: {len(master_only)}")
    print(f"  - Warehouse에만 있음 (SCT 있음): {len(wh_only)}")
    
    # Synced 파일에서 SCT Ref.No가 있는 화물 확인
    if synced_sct_col:
        print(f"\n[3] Synced 파일 SCT Ref.No 분석")
        synced_sct_data = synced_df[synced_df[synced_sct_col].notna()]
        synced_case_set = set(synced_sct_data[synced_case_col].dropna().astype(str))
        
        print(f"  - SCT Ref.No 있는 레코드: {len(synced_sct_data)}건")
        print(f"  - Warehouse에서 추가된 SCT Case: {len(synced_case_set - master_case_set)}건")
        
        # Master에 없는 Case No가 Synced에 있는지 확인
        synced_only = synced_case_set - master_case_set
        if len(synced_only) > 0:
            print(f"\n  ⚠️ Master에 없지만 Synced에 있는 Case No (SCT 있음): {len(synced_only)}건")
            print(f"    첫 10개: {list(synced_only)[:10]}")
    
    # 날짜 업데이트 확인 (예: DSV Indoor 날짜)
    date_cols = ["DSV Indoor", "DSV Al Markaz", "DSV Outdoor"]
    print(f"\n[4] 날짜 컬럼 업데이트 확인")
    
    for date_col in date_cols:
        if date_col in master_df.columns and date_col in warehouse_df.columns:
            # Master에 날짜가 있지만 Warehouse에 없는 케이스
            master_has_date = master_df[master_df[date_col].notna()]
            master_case_with_date = set(master_has_date[master_case_col].dropna().astype(str))
            
            # 이 Case No 중 SCT가 있는 것
            wh_sct_case_set = set(wh_sct_data[wh_case_col].dropna().astype(str))
            sct_with_master_date = master_case_with_date & wh_sct_case_set
            
            if len(sct_with_master_date) > 0:
                print(f"  - {date_col}: Master에 날짜 있고 Warehouse SCT 있는 Case: {len(sct_with_master_date)}건")
    
    print("\n" + "=" * 80)
    print("확인 완료")
    print("=" * 80)

if __name__ == "__main__":
    verify_sct_updates()

