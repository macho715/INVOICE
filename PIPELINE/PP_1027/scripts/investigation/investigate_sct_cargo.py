#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCT 화물 업데이트 누락 문제 조사 스크립트

Stage 1에서 SCT Ref.No가 있는 화물이 업데이트되지 않는 문제를 조사합니다.
"""
import pandas as pd
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import find_header_by_meaning

def investigate_sct_cargo():
    """SCT Ref.No 데이터 조사"""
    
    print("=" * 80)
    print("SCT 화물 업데이트 누락 문제 조사")
    print("=" * 80)
    
    # 1. Master 파일 확인
    master_file = PROJECT_ROOT / "data/raw/HITACHI/Case List_Hitachi.xlsx"
    warehouse_file = PROJECT_ROOT / "data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx"
    synced_file = PROJECT_ROOT / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    stage3_report = PROJECT_ROOT / "data/processed/reports/HVDC_입고로직_종합리포트_20251031_080151_v3.0-corrected.xlsx"
    
    results = {}
    
    # 2. Master 파일 분석
    if master_file.exists():
        print(f"\n[1] Master 파일 분석: {master_file.name}")
        master_df = pd.read_excel(master_file, sheet_name="Case List, RIL")
        
        # SCT Ref.No 컬럼 찾기
        # 직접 컬럼명 확인 (semantic matching이 실패할 수 있음)
        sct_cols = [col for col in master_df.columns if "sct" in str(col).lower() and "ref" in str(col).lower()]
        if not sct_cols:
            # 더 넓게 검색
            sct_cols = [col for col in master_df.columns if "sct" in str(col).lower()]
        sct_col = sct_cols[0] if sct_cols else None
        
        if sct_col:
            sct_data = master_df[sct_col].notna()
            sct_count = sct_data.sum()
            total_count = len(master_df)
            
            results['master'] = {
                'total': total_count,
                'sct_count': sct_count,
                'sct_percentage': (sct_count / total_count * 100) if total_count > 0 else 0,
                'sct_column': sct_col
            }
            
            print(f"  - 총 레코드: {total_count}건")
            print(f"  - SCT Ref.No 있음: {sct_count}건 ({results['master']['sct_percentage']:.1f}%)")
            print(f"  - SCT Ref.No 컬럼: {sct_col}")
            
            # SCT Ref.No가 있지만 Case No가 없는 레코드 확인
            case_col = find_header_by_meaning(master_df, "case_number", required=False)
            if case_col:
                sct_no_case = master_df[sct_data & master_df[case_col].isna()]
                if len(sct_no_case) > 0:
                    print(f"  - ⚠️ SCT Ref.No 있지만 Case No 없는 레코드: {len(sct_no_case)}건")
                    print(f"    첫 5개 SCT Ref.No: {sct_no_case[sct_col].head().tolist()}")
        else:
            print(f"  - ❌ SCT Ref.No 컬럼을 찾을 수 없습니다")
            results['master'] = {'error': 'SCT Ref.No column not found'}
    
    # 3. Warehouse 파일 분석
    if warehouse_file.exists():
        print(f"\n[2] Warehouse 파일 분석: {warehouse_file.name}")
        warehouse_df = pd.read_excel(warehouse_file, sheet_name="Case List, RIL")
        
        sct_col = find_header_by_meaning(warehouse_df, "sct_ref_no", required=False)
        if not sct_col:
            sct_cols = [col for col in warehouse_df.columns if "sct" in str(col).lower() and "ref" in str(col).lower()]
            sct_col = sct_cols[0] if sct_cols else None
        
        if sct_col:
            sct_data = warehouse_df[sct_col].notna()
            sct_count = sct_data.sum()
            total_count = len(warehouse_df)
            
            results['warehouse'] = {
                'total': total_count,
                'sct_count': sct_count,
                'sct_percentage': (sct_count / total_count * 100) if total_count > 0 else 0,
                'sct_column': sct_col
            }
            
            print(f"  - 총 레코드: {total_count}건")
            print(f"  - SCT Ref.No 있음: {sct_count}건 ({results['warehouse']['sct_percentage']:.1f}%)")
    else:
        print(f"  - ❌ Warehouse 파일을 찾을 수 없습니다: {warehouse_file}")
    
    # 4. Synced 파일 분석
    if synced_file.exists():
        print(f"\n[3] Stage 1 Synced 파일 분석: {synced_file.name}")
        try:
            synced_df = pd.read_excel(synced_file, sheet_name="Merged Data")
        except:
            # Merged Data 시트가 없으면 첫 번째 시트 사용
            synced_df = pd.read_excel(synced_file, sheet_name=0)
        
        sct_col = find_header_by_meaning(synced_df, "sct_ref_no", required=False)
        if not sct_col:
            sct_cols = [col for col in synced_df.columns if "sct" in str(col).lower() and "ref" in str(col).lower()]
            sct_col = sct_cols[0] if sct_cols else None
        
        case_col = find_header_by_meaning(synced_df, "case_number", required=False)
        
        if sct_col and case_col:
            sct_data = synced_df[sct_col].notna()
            sct_count = sct_data.sum()
            total_count = len(synced_df)
            
            # SCT Ref.No는 있지만 Case No가 없는 레코드
            sct_no_case = synced_df[sct_data & synced_df[case_col].isna()]
            
            results['synced'] = {
                'total': total_count,
                'sct_count': sct_count,
                'sct_no_case_count': len(sct_no_case),
                'sct_column': sct_col,
                'case_column': case_col
            }
            
            print(f"  - 총 레코드: {total_count}건")
            print(f"  - SCT Ref.No 있음: {sct_count}건")
            if len(sct_no_case) > 0:
                print(f"  - ⚠️ SCT Ref.No 있지만 Case No 없는 레코드: {len(sct_no_case)}건")
                print(f"    첫 5개 SCT Ref.No: {sct_no_case[sct_col].head().tolist()}")
    else:
        print(f"\n[3] ❌ Synced 파일을 찾을 수 없습니다: {synced_file}")
    
    # 5. Master와 Warehouse 간 SCT Ref.No 매칭 확인
    if 'master' in results and 'warehouse' in results and results['master'].get('sct_column') and results['warehouse'].get('sct_column'):
        print(f"\n[4] Master-Warehouse SCT Ref.No 매칭 분석")
        
        master_sct = master_df[results['master']['sct_column']].dropna().unique()
        warehouse_sct = warehouse_df[results['warehouse']['sct_column']].dropna().unique()
        
        master_only = set(master_sct) - set(warehouse_sct)
        warehouse_only = set(warehouse_sct) - set(master_sct)
        common = set(master_sct) & set(warehouse_sct)
        
        print(f"  - Master만 있는 SCT Ref.No: {len(master_only)}개")
        print(f"  - Warehouse만 있는 SCT Ref.No: {len(warehouse_only)}개")
        print(f"  - 공통 SCT Ref.No: {len(common)}개")
        
        if len(master_only) > 0:
            print(f"  - ⚠️ Master에만 있는 SCT Ref.No (업데이트 필요):")
            print(f"    첫 10개: {list(master_only)[:10]}")
    
    # 6. 결과 저장
    output_file = PROJECT_ROOT / "data/investigation/sct_cargo_analysis.xlsx"
    
    # 최소 하나의 시트는 있어야 함
    has_sheets = False
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        if 'master' in results and results['master'].get('sct_column') and 'master_df' in locals():
            master_sct_only = master_df[master_df[results['master']['sct_column']].notna()]
            if len(master_sct_only) > 0:
                master_sct_only.to_excel(writer, sheet_name='Master_SCT', index=False)
                has_sheets = True
        
        if 'warehouse' in results and results['warehouse'].get('sct_column') and 'warehouse_df' in locals():
            warehouse_sct_only = warehouse_df[warehouse_df[results['warehouse']['sct_column']].notna()]
            if len(warehouse_sct_only) > 0:
                warehouse_sct_only.to_excel(writer, sheet_name='Warehouse_SCT', index=False)
                has_sheets = True
        
        # 시트가 없으면 빈 DataFrame이라도 추가
        if not has_sheets:
            pd.DataFrame({'Note': ['No SCT data found']}).to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\n[5] 결과 저장: {output_file}")
    print("\n" + "=" * 80)
    print("조사 완료")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    investigate_sct_cargo()

