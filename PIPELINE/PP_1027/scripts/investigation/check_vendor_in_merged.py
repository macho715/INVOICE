#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 1 Merged 파일에서 Vendor 컬럼 상태 확인
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_vendor():
    merged_file = project_root / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    
    if not merged_file.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {merged_file}")
        return
    
    synced = pd.read_excel(merged_file, sheet_name="Merged Data")
    
    print("=" * 80)
    print("Stage 1 Merged 파일 Vendor 분석")
    print("=" * 80)
    print(f"\n총 레코드: {len(synced)}건")
    
    vendor_col = "Vendor" if "Vendor" in synced.columns else None
    
    if not vendor_col:
        print("\n❌ Vendor 컬럼이 없습니다!")
        print("사용 가능한 컬럼:")
        print(synced.columns.tolist()[:20])
        return
    
    print(f"\n[1] Vendor 컬럼 존재: ✅")
    print(f"\n[2] Vendor 값 분포:")
    vendor_counts = synced[vendor_col].value_counts(dropna=False)
    print(vendor_counts)
    
    print(f"\n[3] Vendor 값 없는 레코드: {synced[vendor_col].isna().sum()}건")
    
    print(f"\n[4] Source_Vendor와 Vendor 비교:")
    if "Source_Vendor" in synced.columns:
        print("Source_Vendor 분포:")
        print(synced["Source_Vendor"].value_counts(dropna=False).head(10))
        
        # Vendor='SCT'인 레코드 확인
        if "SCT" in vendor_counts.index:
            sct_df = synced[synced[vendor_col] == "SCT"]
            print(f"\n[5] Vendor='SCT' 레코드 샘플 (5개):")
            case_col = "Case No." if "Case No." in synced.columns else None
            if case_col:
                print(sct_df[[case_col, vendor_col, "Source_Vendor"]].head(5))
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_vendor()




