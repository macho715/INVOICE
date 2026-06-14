#!/usr/bin/env python3
"""
Excel 컬럼 구조 검증 스크립트

목적:
- 표준 컬럼이 올바른 순서로 있는지 검증
- 각 월별로 핵심 컬럼의 데이터 존재 여부 확인
- 샘플 데이터 출력
"""

import pandas as pd
from pathlib import Path
import sys

def verify_column_structure(excel_path: Path):
    """
    Excel 파일의 컬럼 구조를 검증합니다.
    """
    print('='*80)
    print('Excel 컬럼 구조 검증')
    print('='*80)
    
    # 1. 파일 읽기
    df = pd.read_excel(excel_path)
    
    print(f'\n파일: {excel_path.name}')
    print(f'총 행 수: {len(df):,} rows')
    print(f'총 컬럼 수: {len(df.columns)} columns')
    print(f'총 개월 수: {df["Month"].nunique()} months')
    
    # 2. 표준 컬럼 순서 확인
    standard_columns = [
        'Source_File',
        'No',
        'Month',
        'CWI Job Number',
        'Order Ref. Number',
        'S/No',
        'DESCRIPTION',
        'RATE SOURCE',
        'RATE',
        'Formula',
        'Q\'TY',
        'TOTAL (USD)',
        'REV RATE',
        'REV TOTAL',
        'DIFFERENCE'
    ]
    
    print('\n' + '='*80)
    print('표준 컬럼 순서 확인')
    print('='*80)
    
    existing_standard = []
    for i, col in enumerate(standard_columns):
        if col in df.columns:
            actual_position = df.columns.tolist().index(col) + 1
            status = '✅' if actual_position == i + 1 else '⚠️'
            print(f'{status} {i+1:2d}. {col:20s} (실제 위치: {actual_position})')
            existing_standard.append(col)
        else:
            print(f'❌ {i+1:2d}. {col:20s} (없음)')
    
    # 3. 실제 컬럼 순서 출력 (처음 20개)
    print('\n' + '='*80)
    print('실제 컬럼 순서 (처음 20개)')
    print('='*80)
    for i, col in enumerate(df.columns[:20], 1):
        marker = '★' if col in standard_columns else ' '
        print(f'{marker} {i:2d}. {col}')
    
    if len(df.columns) > 20:
        print(f'   ... ({len(df.columns) - 20}개 더 있음)')
    
    # 4. 월별 데이터 존재 확인
    print('\n' + '='*80)
    print('월별 핵심 컬럼 데이터 존재 확인')
    print('='*80)
    
    core_columns = ['DESCRIPTION', 'RATE', 'Q\'TY', 'TOTAL (USD)']
    existing_core = [col for col in core_columns if col in df.columns]
    
    for month in sorted(df['Month'].unique()):
        month_df = df[df['Month'] == month]
        print(f'\n{month} ({len(month_df)} rows):')
        
        for col in existing_core:
            non_null_count = month_df[col].notna().sum()
            percentage = (non_null_count / len(month_df)) * 100
            status = '✅' if percentage > 90 else ('⚠️' if percentage > 50 else '❌')
            print(f'  {status} {col:15s}: {non_null_count:3d}/{len(month_df):3d} ({percentage:5.1f}%)')
    
    # 5. 샘플 데이터 출력
    print('\n' + '='*80)
    print('샘플 데이터 (처음 5 rows)')
    print('='*80)
    
    sample_cols = ['Source_File', 'No', 'Month', 'Order Ref. Number', 'S/No', 
                   'DESCRIPTION', 'RATE SOURCE', 'RATE', 'Q\'TY', 'TOTAL (USD)']
    existing_sample = [col for col in sample_cols if col in df.columns]
    
    print(df[existing_sample].head(5).to_string(index=False))
    
    # 6. 컬럼명 정규화 확인
    print('\n' + '='*80)
    print('컬럼명 정규화 확인')
    print('='*80)
    
    # 오타/중복 검사
    issues = []
    if 'RATE SORUCE' in df.columns:
        issues.append('❌ "RATE SORUCE" 발견 (오타)')
    if 'RATE SOURCE' in df.columns:
        print('✅ "RATE SOURCE" 정규화됨')
    else:
        print('⚠️ "RATE SOURCE" 컬럼 없음')
    
    # TOTAL (USD) 변형 검사
    total_usd_variants = [col for col in df.columns if 'TOTAL' in col and 'USD' in col]
    if len(total_usd_variants) > 0:
        print(f'✅ USD Total 컬럼: {total_usd_variants}')
    
    # Q'TY 변형 검사
    qty_variants = [col for col in df.columns if 'Q' in col and ('TY' in col or 'ty' in col or 'Qty' in col)]
    if len(qty_variants) > 0:
        print(f'✅ Quantity 컬럼: {qty_variants}')
    
    if issues:
        print('\n⚠️ 발견된 문제:')
        for issue in issues:
            print(f'  {issue}')
    else:
        print('\n✅ 컬럼명 정규화 확인 완료!')
    
    # 7. 최종 요약
    print('\n' + '='*80)
    print('검증 요약')
    print('='*80)
    print(f'✅ 총 {len(df):,} rows, {len(df.columns)} columns')
    print(f'✅ 표준 컬럼: {len(existing_standard)}/{len(standard_columns)} 개 존재')
    print(f'✅ 추가 컬럼: {len(df.columns) - len(existing_standard)} 개')
    print(f'✅ 개월 수: {df["Month"].nunique()} months')
    print('='*80)


if __name__ == "__main__":
    # 가장 최근 파일 찾기
    out_folder = Path(__file__).parent / "out"
    
    if not out_folder.exists():
        print(f"❌ Out folder not found: {out_folder}")
        sys.exit(1)
    
    # masterdata_all_months_*.xlsx 파일 찾기
    excel_files = list(out_folder.glob("masterdata_all_months_*.xlsx"))
    
    if not excel_files:
        print(f"❌ No masterdata_all_months_*.xlsx files found in {out_folder}")
        sys.exit(1)
    
    # 가장 최근 파일 선택
    latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
    
    verify_column_structure(latest_file)


