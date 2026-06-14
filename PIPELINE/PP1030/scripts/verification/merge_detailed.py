#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파이프라인 병합 로직 상세 검증
실제 데이터를 추적하여 업데이트 과정 분석
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def analyze_stage1_update_logic():
    """Stage 1 업데이트 로직 상세 분석"""
    print("=" * 80)
    print("STAGE 1: 업데이트 로직 상세 분석")
    print("=" * 80)
    
    # 원본 Master 파일 (Case List)
    master_file = Path("data/raw/Case List(HE).xlsx")
    master_df = pd.read_excel(master_file, sheet_name="Case List", header=4)
    
    # Stage 1 멀티 시트 파일의 Case List, RIL 시트
    multi_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    warehouse_synced = pd.read_excel(multi_file, sheet_name="Case List, RIL")
    
    print("\n[1] Master vs Warehouse 매칭 분석")
    print("-" * 80)
    print(f"Master 파일 (Case List): {len(master_df):,}행")
    print(f"Warehouse 시트 (Case List, RIL): {len(warehouse_synced):,}행")
    
    # Case No 기준 매칭
    if 'Case No.' in master_df.columns and 'Case No.' in warehouse_synced.columns:
        master_cases = set(master_df['Case No.'].dropna().astype(str).str.strip().str.upper())
        warehouse_cases = set(warehouse_synced['Case No.'].dropna().astype(str).str.strip().str.upper())
        
        common_cases = master_cases & warehouse_cases
        master_only = master_cases - warehouse_cases
        warehouse_only = warehouse_cases - master_cases
        
        print(f"\nCase No 매칭 결과:")
        print(f"  - 공통 케이스: {len(common_cases):,}개")
        print(f"  - Master 전용: {len(master_only):,}개")
        print(f"  - Warehouse 전용: {len(warehouse_only):,}개")
        
        # 샘플 케이스 확인
        if len(common_cases) > 0:
            sample_case = list(common_cases)[0]
            master_row = master_df[master_df['Case No.'].astype(str).str.strip().str.upper() == sample_case]
            warehouse_row = warehouse_synced[warehouse_synced['Case No.'].astype(str).str.strip().str.upper() == sample_case]
            
            if len(master_row) > 0 and len(warehouse_row) > 0:
                print(f"\n  샘플 케이스 '{sample_case}' 비교:")
                # 날짜 컬럼 비교
                date_cols = ['ETD/ATD', 'ETA/ATA', 'DHL WH', 'DSV Indoor', 'DSV Al Markaz']
                for col in date_cols:
                    if col in master_row.columns and col in warehouse_row.columns:
                        m_val = master_row[col].iloc[0] if len(master_row) > 0 else None
                        w_val = warehouse_row[col].iloc[0] if len(warehouse_row) > 0 else None
                        if pd.notna(m_val) and pd.notna(w_val):
                            status = "일치" if str(m_val) == str(w_val) else "다름 (Master 우선)"
                            print(f"    - {col}: Master={m_val}, Warehouse={w_val} [{status}]")
                        elif pd.notna(m_val):
                            print(f"    - {col}: Master={m_val}, Warehouse=비어있음 [업데이트됨]")
    
    # Source_Vendor 분포 확인
    print(f"\n[2] Source_Vendor 분포 (업데이트 후)")
    print("-" * 80)
    if 'Source_Vendor' in warehouse_synced.columns:
        vendor_dist = warehouse_synced['Source_Vendor'].value_counts()
        for vendor, count in vendor_dist.items():
            print(f"  - {vendor}: {count:,}행 ({count/len(warehouse_synced)*100:.1f}%)")
    
    # Source_Sheet 분포 확인
    print(f"\n[3] Source_Sheet 분포")
    print("-" * 80)
    if 'Source_Sheet' in warehouse_synced.columns:
        sheet_dist = warehouse_synced['Source_Sheet'].value_counts()
        for sheet, count in sheet_dist.items():
            print(f"  - {sheet}: {count:,}행")

def analyze_stage1_sheet_merge():
    """Stage 1 시트 간 병합 상세 분석"""
    print("\n" + "=" * 80)
    print("STAGE 1: 시트 간 병합 상세 분석")
    print("=" * 80)
    
    multi_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    merged_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
    
    if not multi_file.exists() or not merged_file.exists():
        print("필요한 파일을 찾을 수 없습니다.")
        return
    
    print("\n[1] 멀티 시트 파일 (시트별)")
    print("-" * 80)
    multi_xl = pd.ExcelFile(multi_file)
    sheet_stats = {}
    
    for sheet in multi_xl.sheet_names:
        df = pd.read_excel(multi_file, sheet_name=sheet)
        sheet_stats[sheet] = {
            'rows': len(df),
            'columns': len(df.columns),
        }
        if 'Source_Sheet' in df.columns:
            sheet_stats[sheet]['source_sheet'] = df['Source_Sheet'].iloc[0] if len(df) > 0 else None
        if 'Source_Vendor' in df.columns:
            vendor_dist = df['Source_Vendor'].value_counts().to_dict()
            sheet_stats[sheet]['vendor_dist'] = vendor_dist
        
        print(f"  - '{sheet}': {len(df):,}행, {len(df.columns)}컬럼")
        if 'vendor_dist' in sheet_stats[sheet]:
            print(f"    Source_Vendor: {sheet_stats[sheet]['vendor_dist']}")
    
    print(f"\n[2] 병합 파일 (단일 시트)")
    print("-" * 80)
    merged_df = pd.read_excel(merged_file)
    print(f"  - 총 행수: {len(merged_df):,}행")
    print(f"  - 총 컬럼: {len(merged_df.columns)}개")
    
    # 시트별 행수 합계와 비교
    total_from_sheets = sum(s['rows'] for s in sheet_stats.values())
    print(f"\n[3] 병합 전후 비교")
    print("-" * 80)
    print(f"  - 시트별 합계: {total_from_sheets:,}행")
    print(f"  - 병합 후: {len(merged_df):,}행")
    print(f"  - 차이: {total_from_sheets - len(merged_df):,}행")
    
    if 'Source_Sheet' in merged_df.columns:
        print(f"\n  병합 후 Source_Sheet 분포:")
        sheet_dist = merged_df['Source_Sheet'].value_counts()
        for sheet, count in sheet_dist.items():
            print(f"    - {sheet}: {count:,}행")
            # 시트별 원본 행수와 비교
            for orig_sheet, stats in sheet_stats.items():
                if stats.get('source_sheet') == sheet:
                    orig_rows = stats['rows']
                    diff = count - orig_rows
                    if diff != 0:
                        print(f"      (원본 '{orig_sheet}': {orig_rows:,}행, 차이: {diff:,}행)")
    
    # 중복 제거 분석
    if 'Case No.' in merged_df.columns:
        print(f"\n[4] 중복 제거 분석")
        print("-" * 80)
        case_col = 'Case No.'
        non_empty = merged_df[case_col].notna() & (merged_df[case_col].astype(str).str.strip() != "")
        unique_cases = merged_df[non_empty][case_col].nunique()
        
        print(f"  - 병합 전 총 행수: {total_from_sheets:,}행")
        print(f"  - 병합 후 총 행수: {len(merged_df):,}행")
        print(f"  - 중복 제거로 감소: {total_from_sheets - len(merged_df):,}행")
        print(f"  - 고유 Case No: {unique_cases:,}개")

def analyze_stage3_merge():
    """Stage 3 병합 로직 상세 분석"""
    print("\n" + "=" * 80)
    print("STAGE 3: HITACHI + SIEMENS 통합 상세 분석")
    print("=" * 80)
    
    stage2_file = Path("data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx")
    reports_dir = Path("data/processed/reports")
    report_files = list(reports_dir.glob("HVDC_입고로직_종합리포트_*_v3.0-corrected.xlsx"))
    
    if not report_files:
        print("Stage 3 보고서 파일을 찾을 수 없습니다.")
        return
    
    latest_report = sorted(report_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    if not stage2_file.exists():
        print("Stage 2 출력 파일을 찾을 수 없습니다.")
        return
    
    df_stage2 = pd.read_excel(stage2_file)
    report_xl = pd.ExcelFile(latest_report)
    
    print(f"\n[1] Stage 2 출력 분석")
    print("-" * 80)
    print(f"  - 행수: {len(df_stage2):,}행")
    if 'Source_Vendor' in df_stage2.columns:
        vendor_dist_stage2 = df_stage2['Source_Vendor'].value_counts()
        print(f"  - Source_Vendor 분포:")
        for vendor, count in vendor_dist_stage2.items():
            print(f"    - {vendor}: {count:,}행 ({count/len(df_stage2)*100:.1f}%)")
    
    # 통합 시트 찾기
    combined_sheet = None
    for sheet in report_xl.sheet_names:
        if '통합' in sheet and '원본' in sheet and 'Fixed' in sheet:
            combined_sheet = sheet
            break
    
    if combined_sheet:
        df_stage3 = pd.read_excel(latest_report, sheet_name=combined_sheet)
        
        print(f"\n[2] Stage 3 통합 데이터 분석")
        print("-" * 80)
        print(f"  - 시트: '{combined_sheet}'")
        print(f"  - 행수: {len(df_stage3):,}행")
        
        if 'Source_Vendor' in df_stage3.columns:
            vendor_dist_stage3 = df_stage3['Source_Vendor'].value_counts()
            print(f"  - Source_Vendor 분포:")
            for vendor, count in vendor_dist_stage3.items():
                print(f"    - {vendor}: {count:,}행 ({count/len(df_stage3)*100:.1f}%)")
        
        # Stage 2 vs Stage 3 비교
        print(f"\n[3] Stage 2 → Stage 3 비교")
        print("-" * 80)
        print(f"  Stage 2 행수: {len(df_stage2):,}행")
        print(f"  Stage 3 행수: {len(df_stage3):,}행")
        
        if len(df_stage2) == len(df_stage3):
            print(f"  [OK] 행수 일치 (중복 제거 없음)")
            
            # Source_Vendor 분포 비교
            if 'Source_Vendor' in df_stage2.columns and 'Source_Vendor' in df_stage3.columns:
                print(f"\n  Source_Vendor 분포 비교:")
                for vendor in set(vendor_dist_stage2.index) | set(vendor_dist_stage3.index):
                    stage2_count = vendor_dist_stage2.get(vendor, 0)
                    stage3_count = vendor_dist_stage3.get(vendor, 0)
                    if stage2_count == stage3_count:
                        print(f"    - {vendor}: {stage2_count:,}행 [일치]")
                    else:
                        print(f"    - {vendor}: Stage2={stage2_count:,}, Stage3={stage3_count:,} [차이: {stage3_count - stage2_count:,}]")
        else:
            print(f"  [WARN] 행수 차이: {len(df_stage3) - len(df_stage2):,}행")
        
        # HITACHI/SIEMENS 분리 시트 확인
        print(f"\n[4] HITACHI/SIEMENS 분리 시트 확인")
        print("-" * 80)
        hitachi_sheet = None
        siemens_sheet = None
        
        for sheet in report_xl.sheet_names:
            if 'HITACHI' in sheet and 'Fixed' in sheet:
                hitachi_sheet = sheet
            elif 'SIEMENS' in sheet and 'Fixed' in sheet:
                siemens_sheet = sheet
        
        if hitachi_sheet:
            df_hitachi = pd.read_excel(latest_report, sheet_name=hitachi_sheet)
            print(f"  - {hitachi_sheet}: {len(df_hitachi):,}행")
            if 'Source_Vendor' in df_hitachi.columns:
                print(f"    Source_Vendor: {df_hitachi['Source_Vendor'].value_counts().to_dict()}")
        
        if siemens_sheet:
            df_siemens = pd.read_excel(latest_report, sheet_name=siemens_sheet)
            print(f"  - {siemens_sheet}: {len(df_siemens):,}행")
            if 'Source_Vendor' in df_siemens.columns:
                print(f"    Source_Vendor: {df_siemens['Source_Vendor'].value_counts().to_dict()}")

def main():
    """메인 실행 함수"""
    try:
        analyze_stage1_update_logic()
        analyze_stage1_sheet_merge()
        analyze_stage3_merge()
        
        print("\n" + "=" * 80)
        print("상세 검증 완료")
        print("=" * 80)
        
    except Exception as e:
        import traceback
        print(f"\n오류 발생: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

