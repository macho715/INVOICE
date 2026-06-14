#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 Vendor 분석 스크립트
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def analyze_vendors():
    master_file = project_root / "data/raw/HITACHI/Case List_Hitachi.xlsx"
    
    if not master_file.exists():
        print(f"오류: Master 파일을 찾을 수 없습니다: {master_file}")
        return
    
    print("=" * 80)
    print("Master 파일 Vendor 분석")
    print("=" * 80)
    
    master = pd.read_excel(master_file, sheet_name="Case List, RIL")
    
    vendor_col = "Vendor" if "Vendor" in master.columns else None
    if not vendor_col:
        print("오류: Vendor 컬럼이 없습니다.")
        return
    
    print(f"\n[1] Vendor별 레코드 수:")
    vendor_counts = master[vendor_col].value_counts()
    print(vendor_counts)
    
    print(f"\n[2] Vendor별 Case No 샘플 (각 3개):")
    for vendor in master[vendor_col].dropna().unique():
        vendor_df = master[master[vendor_col] == vendor]
        cases = vendor_df["Case No."].dropna().head(3).tolist()
        print(f"  {vendor}: {cases}")
    
    print(f"\n[3] Vendor별 Case No 형식 분석:")
    for vendor in master[vendor_col].dropna().unique():
        vendor_df = master[master[vendor_col] == vendor]
        cases = vendor_df["Case No."].dropna().head(10).tolist()
        
        # 형식 패턴 분석
        numeric_count = sum(1 for c in cases if str(c).strip().isdigit())
        alpha_numeric = sum(1 for c in cases if any(c.isalpha() for c in str(c)))
        special_format = sum(1 for c in cases if "-" in str(c) or "/" in str(c))
        
        print(f"  {vendor}:")
        print(f"    - 총 샘플: {len(cases)}개")
        print(f"    - 숫자만: {numeric_count}개")
        print(f"    - 영문 포함: {alpha_numeric}개")
        print(f"    - 특수문자(-/): {special_format}개")
    
    print(f"\n[4] Description 키워드 샘플 (Vendor별 상위 5개 키워드):")
    desc_col = "Description" if "Description" in master.columns else None
    if desc_col:
        for vendor in master[vendor_col].dropna().unique():
            vendor_df = master[master[vendor_col] == vendor]
            descs = vendor_df[desc_col].dropna().head(10).tolist()
            print(f"  {vendor}:")
            for i, desc in enumerate(descs[:5], 1):
                print(f"    {i}. {str(desc)[:60]}...")

if __name__ == "__main__":
    analyze_vendors()

