#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 Vendor 반영 상태 검증 스크립트
"""
import pandas as pd
from pathlib import Path
import sys

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.core import find_header_by_meaning

def verify_all_vendors():
    print("=" * 80)
    print("모든 Vendor 반영 상태 검증")
    print("=" * 80)
    
    # Files to check
    master_file = project_root / "data/raw/HITACHI/Case List_Hitachi.xlsx"
    synced_file = project_root / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    
    # Load Master file
    if not master_file.exists():
        print(f"오류: Master 파일을 찾을 수 없습니다: {master_file}")
        return
    
    master = pd.read_excel(master_file, sheet_name="Case List, RIL")
    master_vendor_col = "Vendor" if "Vendor" in master.columns else None
    
    if not master_vendor_col:
        print("오류: Master 파일에 Vendor 컬럼이 없습니다.")
        return
    
    print(f"\n[1] Master 파일 Vendor 분석:")
    master_vendors = master[master_vendor_col].value_counts()
    print(master_vendors)
    
    # Load Synced file
    if not synced_file.exists():
        print(f"\n오류: Synced 파일을 찾을 수 없습니다: {synced_file}")
        print("파이프라인을 먼저 실행해주세요.")
        return
    
    synced = pd.read_excel(synced_file, sheet_name="Merged Data")
    synced_vendor_col = "Vendor" if "Vendor" in synced.columns else None
    
    print(f"\n[2] Synced 파일 Vendor 분석:")
    if synced_vendor_col:
        synced_vendors = synced[synced_vendor_col].value_counts()
        print(synced_vendors)
    else:
        print("  ❌ Vendor 컬럼이 없습니다.")
        return
    
    print(f"\n[3] Vendor별 반영 상태 비교:")
    print(f"{'Vendor':<15} {'Master':<10} {'Synced':<10} {'반영률':<10} {'상태'}")
    print("-" * 60)
    
    for vendor in master_vendors.index:
        master_count = master_vendors[vendor]
        synced_count = synced_vendors.get(vendor, 0)
        rate = (synced_count / master_count * 100) if master_count > 0 else 0
        status = "✅" if synced_count >= master_count * 0.9 else "⚠️" if synced_count > 0 else "❌"
        print(f"{vendor:<15} {master_count:<10} {synced_count:<10} {rate:>6.1f}%   {status}")
    
    print(f"\n[4] 누락된 Vendor 검증:")
    missing_vendors = []
    for vendor in master_vendors.index:
        if vendor not in synced_vendors.index or synced_vendors.get(vendor, 0) < master_vendors[vendor] * 0.9:
            missing_vendors.append(vendor)
    
    if missing_vendors:
        print(f"  ⚠️ 다음 Vendor가 반영되지 않았거나 부족합니다: {', '.join(missing_vendors)}")
        for vendor in missing_vendors:
            master_cases = master[master[master_vendor_col] == vendor]["Case No."].head(5).tolist()
            print(f"    {vendor}: {master_cases}")
    else:
        print("  ✅ 모든 Vendor가 정상적으로 반영되었습니다.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_all_vendors()

