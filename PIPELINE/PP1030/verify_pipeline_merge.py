#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
파이프라인 단계별 병합 로직 검증 스크립트
각 Stage에서 데이터가 어떻게 병합되고 업데이트되는지 상세 분석
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import sys

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

# 공통 유틸리티 임포트
from scripts.core.verification_utils import print_section

def analyze_stage1_merge():
    """Stage 1 병합 로직 검증"""
    print_section("STAGE 1: 데이터 동기화 및 병합 검증")
    
    # 원본 파일 로드
    print("[1] 원본 파일 분석")
    print("-" * 80)
    
    master_file = Path("data/raw/Case List(HE).xlsx")
    warehouse_file = Path("data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx")
    
    master_sheets_data = {}
    if master_file.exists():
        master_xl = pd.ExcelFile(master_file)
        print(f"Master 파일: {master_file.name}")
        print(f"  - 시트 목록: {master_xl.sheet_names}")
        for sheet in master_xl.sheet_names:
            df = pd.read_excel(master_file, sheet_name=sheet, header=None)
            master_sheets_data[sheet] = len(df)
            print(f"    - '{sheet}': {len(df):,}행 (원본)")
    
    warehouse_sheets_data = {}
    if warehouse_file.exists():
        warehouse_xl = pd.ExcelFile(warehouse_file)
        print(f"\nWarehouse 파일: {warehouse_file.name}")
        print(f"  - 시트 목록: {warehouse_xl.sheet_names}")
        for sheet in warehouse_xl.sheet_names:
            df = pd.read_excel(warehouse_file, sheet_name=sheet, header=None)
            warehouse_sheets_data[sheet] = len(df)
            print(f"    - '{sheet}': {len(df):,}행 (원본)")
    
    # Stage 1 출력 분석
    print("\n[2] Stage 1 출력 분석")
    print("-" * 80)
    
    multi_sheet_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
    merged_file = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
    
    stage1_output = {}
    
    # 멀티 시트 파일 분석
    if multi_sheet_file.exists():
        print(f"멀티 시트 파일: {multi_sheet_file.name}")
        multi_xl = pd.ExcelFile(multi_sheet_file)
        print(f"  - 시트 목록: {multi_xl.sheet_names}")
        
        for sheet in multi_xl.sheet_names:
            df = pd.read_excel(multi_sheet_file, sheet_name=sheet)
            stage1_output[sheet] = {
                'rows': len(df),
                'columns': len(df.columns),
                'has_source_sheet': 'Source_Sheet' in df.columns,
                'has_source_vendor': 'Source_Vendor' in df.columns,
            }
            
            # Source_Sheet 분포
            if 'Source_Sheet' in df.columns:
                sheet_dist = df['Source_Sheet'].value_counts().to_dict()
                stage1_output[sheet]['source_sheet_dist'] = sheet_dist
                print(f"    - '{sheet}': {len(df):,}행, {len(df.columns)}컬럼")
                print(f"      Source_Sheet 분포: {sheet_dist}")
            
            # Source_Vendor 분포
            if 'Source_Vendor' in df.columns:
                vendor_dist = df['Source_Vendor'].value_counts().to_dict()
                stage1_output[sheet]['source_vendor_dist'] = vendor_dist
                print(f"      Source_Vendor 분포: {vendor_dist}")
    
    # 병합 파일 분석
    print(f"\n병합 파일: {merged_file.name}")
    if merged_file.exists():
        merged_df = pd.read_excel(merged_file)
        print(f"  - 총 행수: {len(merged_df):,}행")
        print(f"  - 총 컬럼: {len(merged_df.columns)}개")
        
        if 'Source_Sheet' in merged_df.columns:
            sheet_dist = merged_df['Source_Sheet'].value_counts()
            print(f"\n  Source_Sheet 분포:")
            for sheet, count in sheet_dist.items():
                print(f"    - {sheet}: {count:,}행")
        
        if 'Source_Vendor' in merged_df.columns:
            vendor_dist = merged_df['Source_Vendor'].value_counts()
            print(f"\n  Source_Vendor 분포:")
            for vendor, count in vendor_dist.items():
                print(f"    - {vendor}: {count:,}행")
        
        # Case No 중복 분석
        if 'Case No.' in merged_df.columns:
            case_col = 'Case No.'
            non_empty = merged_df[case_col].notna() & (merged_df[case_col].astype(str).str.strip() != "")
            unique_cases = merged_df[non_empty][case_col].nunique()
            total_non_empty = non_empty.sum()
            dup_count = total_non_empty - unique_cases
            
            print(f"\n  Case No 분석:")
            print(f"    - 총 행수: {len(merged_df):,}")
            print(f"    - 빈 Case No: {(~non_empty).sum():,}행")
            print(f"    - 유효 Case No: {total_non_empty:,}행")
            print(f"    - 고유 Case No: {unique_cases:,}개")
            print(f"    - 중복 Case No: {dup_count:,}행")
            
            if dup_count > 0:
                dup_samples = merged_df[non_empty][merged_df[non_empty][case_col].duplicated(keep=False)][case_col].value_counts().head(5)
                print(f"    - 중복 샘플 (상위 5개):")
                for case, count in dup_samples.items():
                    print(f"      '{case}': {count}회")
    
    # 병합 로직 분석
    print("\n[3] 병합 로직 분석")
    print("-" * 80)
    
    print("Stage 1 병합 프로세스:")
    print("  1. 시트별 매칭:")
    print("     - Master 시트 ↔ Warehouse 시트 semantic matching")
    print("     - 공통 시트: Master 데이터로 Warehouse 업데이트")
    print("     - Warehouse 전용 시트: 그대로 보존")
    print("     - Master 전용 시트: 추가")
    
    print("\n  2. 업데이트 우선순위:")
    print("     - Case No 기준 매칭")
    print("     - 날짜 컬럼: Master 우선 (Master에 값이 있으면 항상 업데이트)")
    print("     - 비날짜 컬럼: Master 우선 (ALWAYS_OVERWRITE_NONDATE=True)")
    print("     - 신규 케이스: Master 데이터로 추가")
    
    print("\n  3. 시트 간 병합:")
    print("     - 순서: Case List, RIL → HE Local → Capacitor")
    print("     - pd.concat()으로 결합")
    print("     - Source_Sheet 컬럼 추가 (시트 출처 기록)")
    
    print("\n  4. 전역 중복 제거:")
    print("     - Case No 기준 중복 제거")
    print("     - 빈 키 행 보존")
    print("     - keep='first' 정책 (첫 번째 발생 유지)")
    
    return {
        'master_sheets': master_sheets_data,
        'warehouse_sheets': warehouse_sheets_data,
        'stage1_output': stage1_output,
        'merged_stats': {
            'rows': len(merged_df) if merged_file.exists() else 0,
            'columns': len(merged_df.columns) if merged_file.exists() else 0,
        }
    }

def analyze_stage2_merge():
    """Stage 2 파생 컬럼 계산 검증"""
    print_section("STAGE 2: 파생 컬럼 계산 검증")
    
    stage1_output = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx")
    stage2_output = Path("data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx")
    
    print("[1] Stage 1 → Stage 2 비교")
    print("-" * 80)
    
    if stage1_output.exists() and stage2_output.exists():
        df_stage1 = pd.read_excel(stage1_output)
        df_stage2 = pd.read_excel(stage2_output)
        
        print(f"Stage 1 출력: {len(df_stage1):,}행, {len(df_stage1.columns)}컬럼")
        print(f"Stage 2 출력: {len(df_stage2):,}행, {len(df_stage2.columns)}컬럼")
        
        # 행수 비교
        if len(df_stage1) == len(df_stage2):
            print(f"\n[OK] 행수 일치: {len(df_stage1):,}행 (변화 없음)")
        else:
            print(f"\n[WARN] 행수 불일치: {len(df_stage1):,} → {len(df_stage2):,} (차이: {len(df_stage2) - len(df_stage1):,})")
        
        # 컬럼 비교
        stage1_cols = set(df_stage1.columns)
        stage2_cols = set(df_stage2.columns)
        
        added_cols = stage2_cols - stage1_cols
        removed_cols = stage1_cols - stage2_cols
        
        print(f"\n컬럼 변화:")
        print(f"  - Stage 1 컬럼: {len(stage1_cols)}개")
        print(f"  - Stage 2 컬럼: {len(stage2_cols)}개")
        print(f"  - 추가된 컬럼: {len(added_cols)}개")
        if added_cols:
            print(f"    {sorted(added_cols)}")
        print(f"  - 제거된 컬럼: {len(removed_cols)}개")
        if removed_cols:
            print(f"    {sorted(removed_cols)}")
        
        # 파생 컬럼 확인
        derived_cols = ['SQM', 'Stack_Status', 'wh handling', 'site handling', 'total handling']
        print(f"\n파생 컬럼 확인:")
        for col in derived_cols:
            if col in df_stage2.columns:
                non_null = df_stage2[col].notna().sum()
                print(f"  - {col}: {non_null:,}개 값 (전체의 {non_null/len(df_stage2)*100:.1f}%)")
            else:
                print(f"  - {col}: 컬럼 없음")
        
        print("\n[2] Stage 2 병합 로직")
        print("-" * 80)
        print("Stage 2는 병합 없음:")
        print("  - 입력: Stage 1 병합 파일 (단일 시트)")
        print("  - 출력: 동일한 행수 유지")
        print("  - 작업: 파생 컬럼 계산 및 추가만 수행")
        print("  - SQM: STACK.MD 기반 계산")
        print("  - Stack_Status: Stack 컬럼 파싱")
        
        return {
            'stage1_rows': len(df_stage1),
            'stage2_rows': len(df_stage2),
            'rows_match': len(df_stage1) == len(df_stage2),
            'added_columns': list(added_cols),
            'removed_columns': list(removed_cols),
        }
    else:
        print("파일을 찾을 수 없습니다.")
        return None

def analyze_stage3_merge():
    """Stage 3 HITACHI+SIEMENS 통합 검증"""
    print_section("STAGE 3: HITACHI + SIEMENS 통합 보고서 검증")
    
    stage2_output = Path("data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx")
    
    # 최신 보고서 파일 찾기
    reports_dir = Path("data/processed/reports")
    report_files = list(reports_dir.glob("HVDC_입고로직_종합리포트_*_v3.0-corrected.xlsx"))
    
    if not report_files:
        print("Stage 3 보고서 파일을 찾을 수 없습니다.")
        return None
    
    latest_report = sorted(report_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    print(f"[1] Stage 3 보고서 파일: {latest_report.name}")
    print("-" * 80)
    
    if stage2_output.exists() and latest_report.exists():
        df_stage2 = pd.read_excel(stage2_output)
        report_xl = pd.ExcelFile(latest_report)
        
        print(f"Stage 2 출력: {len(df_stage2):,}행, {len(df_stage2.columns)}컬럼")
        print(f"Stage 3 보고서 시트: {report_xl.sheet_names}")
        
        # 통합_원본데이터_Fixed 시트 찾기
        combined_sheet = None
        for sheet in report_xl.sheet_names:
            if '통합' in sheet and '원본' in sheet and 'Fixed' in sheet:
                combined_sheet = sheet
                break
        # 폴백: '통합' 또는 'Fixed'만 포함
        if not combined_sheet:
            for sheet in report_xl.sheet_names:
                if '통합' in sheet and 'Fixed' in sheet:
                    combined_sheet = sheet
                    break
        
        if combined_sheet:
            df_stage3 = pd.read_excel(latest_report, sheet_name=combined_sheet)
            print(f"\n통합 데이터 시트: '{combined_sheet}'")
            print(f"  - 행수: {len(df_stage3):,}행")
            print(f"  - 컬럼: {len(df_stage3.columns)}개")
            
            # Source_Vendor 분포
            if 'Source_Vendor' in df_stage3.columns:
                vendor_dist = df_stage3['Source_Vendor'].value_counts()
                print(f"\n  Source_Vendor 분포:")
                for vendor, count in vendor_dist.items():
                    print(f"    - {vendor}: {count:,}행 ({count/len(df_stage3)*100:.1f}%)")
            
            # Stage 2 vs Stage 3 비교
            print(f"\n[2] Stage 2 → Stage 3 비교")
            print("-" * 80)
            print(f"Stage 2 행수: {len(df_stage2):,}행")
            print(f"Stage 3 행수: {len(df_stage3):,}행")
            
            if len(df_stage2) == len(df_stage3):
                print(f"[OK] 행수 일치: {len(df_stage2):,}행 (변화 없음)")
            else:
                diff = len(df_stage3) - len(df_stage2)
                print(f"[WARN] 행수 차이: {diff:,}행 ({abs(diff)/len(df_stage2)*100:.1f}%)")
            
            # 컬럼 비교
            stage2_cols = set(df_stage2.columns)
            stage3_cols = set(df_stage3.columns)
            
            added_cols = stage3_cols - stage2_cols
            removed_cols = stage2_cols - stage3_cols
            
            print(f"\n컬럼 변화:")
            print(f"  - Stage 2 컬럼: {len(stage2_cols)}개")
            print(f"  - Stage 3 컬럼: {len(stage3_cols)}개")
            print(f"  - 추가된 컬럼: {len(added_cols)}개")
            if added_cols:
                print(f"    {sorted(added_cols)[:10]}...")  # 처음 10개만
            print(f"  - 제거된 컬럼: {len(removed_cols)}개")
            if removed_cols:
                print(f"    {sorted(removed_cols)}")
            
            print("\n[3] Stage 3 병합 로직")
            print("-" * 80)
            print("Stage 3 병합 프로세스:")
            print("  1. 데이터 로드:")
            print("     - HITACHI 데이터: Stage 2 출력 파일 로드")
            print("     - SIEMENS 데이터: 옵션 (파일이 있으면 로드)")
            print("     - 각각 독립적으로 로드")
            
            print("\n  2. 데이터 결합:")
            print("     - pd.concat(combined_dfs, ignore_index=True, sort=False)")
            print("     - 행수 합산 (중복 제거 없음)")
            print("     - Source_Vendor 컬럼으로 출처 구분")
            
            print("\n  3. 컬럼 정규화:")
            print("     - normalize_columns(): 컬럼명 공백 정규화")
            print("     - apply_column_synonyms(): 동의어 매핑")
            print("     - 표준 헤더 순서 적용 (63개 컬럼)")
            
            print("\n  4. 신규 컬럼 계산:")
            print("     - Stack_Status: Stack 컬럼 파싱")
            print("     - Total sqm: SQM 기반 계산")
            print("     - Flow Code: 0~5 확장")
            
            print("\n  5. 시트 생성:")
            print("     - 통합_원본데이터_Fixed: HITACHI + SIEMENS 통합")
            print("     - HITACHI_입고로직_종합리포트_Fixed: HITACHI만")
            print("     - SIEMENS_입고로직_종합리포트_Fixed: SIEMENS만")
            
            return {
                'stage2_rows': len(df_stage2),
                'stage3_rows': len(df_stage3),
                'rows_match': len(df_stage2) == len(df_stage3),
                'vendor_dist': vendor_dist.to_dict() if 'Source_Vendor' in df_stage3.columns else {},
                'added_columns': list(added_cols),
                'removed_columns': list(removed_cols),
            }
        else:
            print("통합 데이터 시트를 찾을 수 없습니다.")
            return None
    else:
        print("필요한 파일을 찾을 수 없습니다.")
        return None

def create_summary_report(stage1_result, stage2_result, stage3_result):
    """통합 검증 리포트 생성"""
    print_section("통합 검증 리포트")
    
    print("=" * 80)
    print("파이프라인 데이터 흐름 요약")
    print("=" * 80)
    
    print("\n[원본 → Stage 1]")
    if stage1_result:
        master_total = sum(stage1_result['master_sheets'].values())
        warehouse_total = sum(stage1_result['warehouse_sheets'].values())
        merged_total = stage1_result['merged_stats']['rows']
        
        print(f"  - Master 총 행수: {master_total:,}행")
        print(f"  - Warehouse 총 행수: {warehouse_total:,}행")
        print(f"  - Stage 1 병합 출력: {merged_total:,}행")
        print(f"  - 손실: {master_total + warehouse_total - merged_total:,}행")
        print(f"    (중복 제거 및 헤더 행 제외)")
    
    print("\n[Stage 1 → Stage 2]")
    if stage2_result:
        print(f"  - Stage 1 출력: {stage2_result['stage1_rows']:,}행")
        print(f"  - Stage 2 출력: {stage2_result['stage2_rows']:,}행")
        if stage2_result['rows_match']:
            print(f"  [OK] 행수 불변 (파생 컬럼만 추가)")
        else:
            print(f"  [WARN] 행수 변화 발생")
        print(f"  - 추가된 컬럼: {len(stage2_result['added_columns'])}개")
    
    print("\n[Stage 2 → Stage 3]")
    if stage3_result:
        print(f"  - Stage 2 출력: {stage3_result['stage2_rows']:,}행")
        print(f"  - Stage 3 출력: {stage3_result['stage3_rows']:,}행")
        if stage3_result['rows_match']:
            print(f"  [OK] 행수 불변")
        else:
            print(f"  [WARN] 행수 변화: {stage3_result['stage3_rows'] - stage3_result['stage2_rows']:,}행")
        
        if stage3_result['vendor_dist']:
            print(f"\n  Source_Vendor 분포:")
            for vendor, count in stage3_result['vendor_dist'].items():
                print(f"    - {vendor}: {count:,}행")
    
    print("\n" + "=" * 80)
    print("병합 우선순위 정리")
    print("=" * 80)
    
    print("\n1. Stage 1 (데이터 동기화):")
    print("   - Master 데이터가 항상 우선")
    print("   - 날짜 컬럼: Master에 값이 있으면 무조건 업데이트")
    print("   - 비날짜 컬럼: Master에 값이 있으면 무조건 업데이트")
    print("   - 신규 케이스: Master 데이터로 추가")
    print("   - 중복 제거: Case No 기준, keep='first'")
    
    print("\n2. Stage 2 (파생 컬럼):")
    print("   - 병합 없음")
    print("   - 기존 데이터 유지")
    print("   - 파생 컬럼만 추가")
    
    print("\n3. Stage 3 (통합 보고서):")
    print("   - HITACHI + SIEMENS 단순 결합 (concat)")
    print("   - 중복 제거 없음")
    print("   - Source_Vendor로 구분")
    print("   - 컬럼 정규화 및 표준 순서 적용")

def main():
    """메인 실행 함수"""
    try:
        stage1_result = analyze_stage1_merge()
        stage2_result = analyze_stage2_merge()
        stage3_result = analyze_stage3_merge()
        create_summary_report(stage1_result, stage2_result, stage3_result)
        
        print_section("검증 완료", "=")
        print("모든 단계의 병합 로직 검증이 완료되었습니다.")
        
    except Exception as e:
        import traceback
        print(f"\n오류 발생: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()

