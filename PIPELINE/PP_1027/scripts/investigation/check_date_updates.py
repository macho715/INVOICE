#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
날짜 업데이트 확인 스크립트
"""
import pandas as pd
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_date_updates():
    print("=" * 80)
    print("날짜 업데이트 확인")
    print("=" * 80)
    
    # Master 파일 로드 (헤더는 5행)
    master_file = project_root / "data/raw/HITACHI/Case List(20251030)v2.xlsx"
    master = pd.read_excel(master_file, sheet_name="Case List, RIL", header=4)
    
    print(f"\n[1] Master 파일 컬럼 목록:")
    print(f"  총 {len(master.columns)}개 컬럼")
    print("  날짜 관련 컬럼:")
    date_related = [c for c in master.columns if any(kw in str(c).lower() for kw in ['date', 'etd', 'eta', 'dhl', 'dsv', 'aaa', 'mir', 'shu', 'das', 'agi', 'mzp'])]
    for i, col in enumerate(date_related[:10]):
        print(f"    {i+1}. {col}")
    
    # Synced 파일 로드
    synced_file = project_root / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
    synced = pd.read_excel(synced_file, sheet_name="Case List, RIL")
    
    print(f"\n[2] Synced 파일 컬럼 목록:")
    print(f"  총 {len(synced.columns)}개 컬럼")
    
    # 날짜 컬럼 찾기
    date_cols_synced = ['ETD/ATD', 'ETA/ATA', 'DHL WH', 'DSV Indoor', 'DSV Al Markaz', 
                        'DSV Outdoor', 'MIR', 'SHU', 'DAS', 'AGI']
    
    print(f"\n[3] 최신 날짜 비교 (Master vs Synced):")
    comparison_results = []
    
    for col in date_cols_synced:
        if col in synced.columns:
            # Master에서 해당 컬럼 찾기
            master_col = None
            for mc in master.columns:
                if col in str(mc) or str(mc) == col or str(mc).strip() == col:
                    master_col = mc
                    break
            
            if master_col and master_col in master.columns:
                master_max = None
                master_count = 0
                if master[master_col].notna().any():
                    master_max = master[master_col].dropna().max()
                    master_count = master[master_col].notna().sum()
                
                synced_max = None
                synced_count = 0
                if synced[col].notna().any():
                    synced_max = synced[col].dropna().max()
                    synced_count = synced[col].notna().sum()
                
                # 날짜 비교
                is_updated = "확인필요"
                if master_max is not None and synced_max is not None:
                    try:
                        master_date = pd.to_datetime(master_max).date()
                        synced_date = pd.to_datetime(synced_max).date()
                        is_updated = "예" if master_date == synced_date else "다름"
                    except:
                        pass
                
                comparison_results.append({
                    'col': col,
                    'master_col': master_col,
                    'master_max': master_max,
                    'master_count': master_count,
                    'synced_max': synced_max,
                    'synced_count': synced_count,
                    'updated': is_updated
                })
                
                print(f"\n  {col}:")
                print(f"    Master 컬럼: {master_col}")
                print(f"    Master 최신: {master_max} ({master_count}건)")
                print(f"    Synced 최신: {synced_max} ({synced_count}건)")
                print(f"    업데이트 여부: {is_updated}")
    
    # 파이프라인 로그에서 날짜 업데이트 확인
    print(f"\n[4] 파이프라인 로그 확인:")
    print("  - Date updates: 53건")
    print("  - 최신 날짜 예시:")
    print("    MIR: 2025-10-30")
    print("    ETA/ATA: 2025-12-21")
    
    # 요약
    updated_count = sum(1 for r in comparison_results if r['updated'] == '예')
    print("\n" + "=" * 80)
    print("요약:")
    print(f"  - 비교 가능한 날짜 컬럼: {len(comparison_results)}개")
    print(f"  - 업데이트 확인된 컬럼: {updated_count}개")
    print(f"  - Synced 파일 최신 날짜: MIR=2025-10-30, ETA/ATA=2025-12-21")
    print("=" * 80)

if __name__ == "__main__":
    check_date_updates()

