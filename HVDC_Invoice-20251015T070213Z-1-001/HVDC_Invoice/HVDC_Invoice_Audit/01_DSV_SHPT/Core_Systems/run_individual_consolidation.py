#!/usr/bin/env python3
"""
다중 월 인보이스 통합 실행 스크립트

14개월치 인보이스 파일 자동 통합 (2024.08 ~ 2025.09)
- Source_File 컬럼 추가 (A열)
- Month 컬럼 추가 (C열)

Usage:
    python consolidate_all_months.py

Output:
    out/masterdata_all_months_YYYYMMDD_HHMMSS.xlsx
"""

import sys
from pathlib import Path
from datetime import datetime

# 00_Shared 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from engine_multi_month import MultiMonthConsolidator


def main():
    """14개월 인보이스 통합 실행"""
    
    print("=" * 80)
    print("Multi-Month Invoice Consolidation System")
    print("2024.08 ~ 2025.09 (14 months)")
    print("=" * 80)
    print()
    
    # SHPT 폴더
    shpt_folder = Path(__file__).parent.parent / "SHPT"
    
    if not shpt_folder.exists():
        print(f"[ERROR] SHPT folder not found")
        print(f"   Expected: {shpt_folder}")
        return 1
    
    print(f"[INPUT] Folder: {shpt_folder}")
    print()
    
    # 통합 실행
    try:
        consolidator = MultiMonthConsolidator(shpt_folder)
        all_data = consolidator.consolidate_all_months()
        
        # 결과 저장
        output_dir = Path(__file__).parent / "out"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"masterdata_all_months_{timestamp}.xlsx"
        
        print(f"\n[SAVING] Output: {output_file.name}")
        all_data.to_excel(output_file, index=False, engine="openpyxl")
        
        # 요약 출력
        print()
        print("=" * 80)
        print("[SUCCESS] MULTI-MONTH CONSOLIDATION COMPLETE!")
        print("=" * 80)
        print(f"Total rows: {len(all_data)}")
        print(f"Total months: {all_data['Month'].nunique()}")
        print(f"Total columns: {len(all_data.columns)}")
        print()
        print(f"Months covered:")
        for month in sorted(all_data['Month'].unique()):
            count = len(all_data[all_data['Month'] == month])
            source = all_data[all_data['Month'] == month]['Source_File'].iloc[0]
            print(f"  - {month} ({source}): {count} rows")
        
        print()
        print(f"Output: {output_file}")
        print()
        
        # 샘플 데이터 출력
        print("Sample data (first 5 rows):")
        sample_cols = ['Source_File', 'No', 'Month', 'Order Ref. Number', 'DESCRIPTION', 'RATE']
        print(all_data[sample_cols].head().to_string())
        print()
        
        # 통계
        print("\nFile Statistics:")
        file_stats = all_data.groupby('Source_File').size().reset_index(name='Row Count')
        file_stats = file_stats.sort_values('Source_File')
        print(file_stats.to_string(index=False))
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

