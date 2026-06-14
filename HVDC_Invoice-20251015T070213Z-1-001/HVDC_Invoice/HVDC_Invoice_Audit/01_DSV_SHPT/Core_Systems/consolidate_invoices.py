#!/usr/bin/env python3
"""
인보이스 통합 실행 스크립트

VBA modCompileMaster.CompileAllSheets를 Python으로 자동화

Usage:
    python consolidate_invoices.py

Output:
    out/masterdata_consolidated_YYYYMMDD_HHMMSS.xlsx
"""

import sys
from pathlib import Path
from datetime import datetime

# 00_Shared 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from invoice_consolidator import InvoiceConsolidator


def main():
    """인보이스 통합 실행"""
    
    print("=" * 80)
    print("Invoice Consolidation System (VBA modCompileMaster Python 재구현)")
    print("=" * 80)
    print()
    
    # 입력 파일
    input_file = Path(__file__).parent.parent / "Data" / "DSV 202509" / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
    
    if not input_file.exists():
        print(f"❌ Error: Input file not found")
        print(f"   Expected: {input_file}")
        return 1
    
    print(f"📂 Input: {input_file.name}")
    print()
    
    # 통합 실행
    try:
        consolidator = InvoiceConsolidator(input_file)
        masterdata_df = consolidator.consolidate()
        
        # 결과 저장
        output_dir = Path(__file__).parent / "out"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"masterdata_consolidated_{timestamp}.xlsx"
        
        print(f"\n💾 Saving to: {output_file.name}")
        masterdata_df.to_excel(output_file, index=False, engine="openpyxl")
        
        # 요약 출력
        print()
        print("=" * 80)
        print("✅ Consolidation Complete!")
        print("=" * 80)
        print(f"Total rows: {len(masterdata_df)}")
        print(f"Total sheets: {masterdata_df['Order Ref. Number'].nunique()}")
        print(f"Total columns: {len(masterdata_df.columns)}")
        print(f"\nOutput: {output_file}")
        print()
        
        # 샘플 데이터 출력
        print("Sample data (first 5 rows):")
        print(masterdata_df[['No', 'Order Ref. Number', 'S/No', 'DESCRIPTION', 'RATE']].head().to_string())
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())


