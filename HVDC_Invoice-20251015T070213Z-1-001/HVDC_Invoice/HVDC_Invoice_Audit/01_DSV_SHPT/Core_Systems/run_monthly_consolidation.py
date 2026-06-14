#!/usr/bin/env python3
"""
월별 요약 시트 통합 실행 스크립트

15개 월별 시트 (2024-08 ~ 2025-09, JUNE Batch1+Batch2 포함)를
하나의 마스터 파일로 통합

Usage:
    python consolidate_month_sheets.py

Output:
    out/month_sheets_master_YYYYMMDD_HHMMSS.xlsx
"""

import sys
from pathlib import Path
from datetime import datetime

# 00_Shared 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from engine_monthly_summary import MonthSheetConsolidator


def main():
    """15개 월별 시트 통합 실행"""
    
    print("=" * 80)
    print("월별 요약 시트 통합 시스템")
    print("2024.08 ~ 2025.09 (14개월, JUNE Batch1+Batch2 = 15개 시트)")
    print("=" * 80)
    print()
    
    # SHPT 폴더
    shpt_folder = Path(__file__).parent.parent / "SHPT"
    
    if not shpt_folder.exists():
        print(f"[ERROR] SHPT 폴더를 찾을 수 없습니다")
        print(f"   Expected: {shpt_folder}")
        return 1
    
    print(f"[INPUT] 폴더: {shpt_folder}")
    print()
    
    # 통합 실행
    try:
        consolidator = MonthSheetConsolidator(shpt_folder)
        all_data = consolidator.consolidate_all_month_sheets()
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent / "out"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"month_sheets_master_{timestamp}.xlsx"
        
        print()
        print(f"[SAVING] 출력 파일: {output_file.name}")
        print()
        
        all_data.to_excel(output_file, index=False)
        
        print("=" * 80)
        print("[SUCCESS] 월별 시트 통합 완료!")
        print("=" * 80)
        print(f"총 행 수: {len(all_data)}")
        print(f"총 컬럼 수: {len(all_data.columns)}")
        print()
        
        # 월별 분포
        print("월별 데이터 분포:")
        month_counts = all_data['Source_Month'].value_counts().sort_index()
        for month, count in month_counts.items():
            print(f"  - {month:<20}: {count:>4} rows")
        
        print()
        print(f"출력: {output_file}")
        print()
        
        # 샘플 데이터
        print("샘플 데이터 (처음 5행):")
        print(all_data[['Source_Month', 'S/No', 'Shipment Reference', 'CW1 Job Number', 'GRAND TOTAL (USD)']].head() 
              if 'GRAND TOTAL (USD)' in all_data.columns 
              else all_data[['Source_Month', 'S/No', 'Shipment Reference']].head())
        
        return 0
        
    except Exception as e:
        print()
        print(f"[ERROR] 통합 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

