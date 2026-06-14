#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor 반영 문제 디버깅
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_vendor():
    print("=" * 80)
    print("Vendor 반영 문제 디버깅")
    print("=" * 80)
    
    # 1. Master 파일 확인
    master_file = project_root / "data/raw/HITACHI/Case List_Hitachi.xlsx"
    master = pd.read_excel(master_file, sheet_name="Case List, RIL")
    
    print("\n[1] Master 파일:")
    if "Vendor" in master.columns:
        print(f"  Vendor 컬럼 존재: ✅")
        print(f"  Vendor 값 분포:")
        print(master["Vendor"].value_counts())
        
        # Fallback 매칭 대상 확인
        sct_cases = master[master["Vendor"] == "SCT"]["Case No."].head(10).tolist()
        print(f"\n  SCT Case No 샘플 (10개): {sct_cases}")
    
    # 2. Stage 1 출력 파일 확인 (multi-sheet)
    synced_file = project_root / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
    if synced_file.exists():
        print("\n[2] Stage 1 Multi-sheet 출력:")
        synced = pd.read_excel(synced_file, sheet_name="Case List, RIL")
        
        if "Vendor" in synced.columns:
            print(f"  Vendor 컬럼 존재: ✅")
            vendor_counts = synced["Vendor"].value_counts(dropna=False)
            print(f"  Vendor 값 분포:")
            print(vendor_counts)
            
            # SCT Case No가 있는지 확인
            case_col = "Case No." if "Case No." in synced.columns else None
            if case_col:
                sct_cases_in_synced = synced[synced[case_col].isin(["DCS NETWORK-04", "DCS NETWORK-05", "39-EMERSON"])]
                if len(sct_cases_in_synced) > 0:
                    print(f"\n  SCT Case No 샘플 레코드의 Vendor 값:")
                    print(sct_cases_in_synced[[case_col, "Vendor"]].head(10))
        else:
            print("  Vendor 컬럼 없음: ❌")
    
    # 3. Merged 파일 확인
    merged_file = project_root / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    if merged_file.exists():
        print("\n[3] Stage 1 Merged 출력:")
        merged = pd.read_excel(merged_file, sheet_name="Merged Data")
        
        if "Vendor" in merged.columns:
            print(f"  Vendor 컬럼 존재: ✅")
            vendor_counts = merged["Vendor"].value_counts(dropna=False)
            print(f"  Vendor 값 분포:")
            print(vendor_counts)
            
            # Fallback 매칭된 Case No 확인
            case_col = "Case No." if "Case No." in merged.columns else None
            if case_col:
                # SCT fallback 매칭 대상 Case No 확인
                sct_fallback_cases = ["DCS NETWORK-05", "39-EMERSON", "41-EMERSON", "SCT-0114/02 OF 18"]
                matched = merged[merged[case_col].isin(sct_fallback_cases)]
                if len(matched) > 0:
                    print(f"\n  Fallback 매칭된 SCT Case No의 Vendor 값:")
                    print(matched[[case_col, "Vendor"]])
                else:
                    print(f"\n  ⚠️ Fallback 매칭된 Case No가 merged 파일에 없습니다.")
        else:
            print("  Vendor 컬럼 없음: ❌")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    debug_vendor()




