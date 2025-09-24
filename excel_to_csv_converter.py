"""
Excel to CSV Converter for Invoice Audit System

Excel 매크로 파일(.xlsm)을 CSV 형식으로 변환하여 감사 시스템에서 사용할 수 있도록 합니다.
"""

import pandas as pd
import os
import sys
from pathlib import Path

def convert_excel_to_csv(excel_file_path: str, output_dir: str = "io") -> str:
    """
    Excel 파일을 CSV로 변환
    
    Args:
        excel_file_path: Excel 파일 경로
        output_dir: 출력 디렉토리
        
    Returns:
        변환된 CSV 파일 경로
    """
    try:
        # Excel 파일 읽기
        print(f"Excel 파일 읽는 중: {excel_file_path}")
        
        # 모든 시트 읽기
        excel_data = pd.read_excel(excel_file_path, sheet_name=None, engine='openpyxl')
        
        print(f"발견된 시트: {list(excel_data.keys())}")
        
        # 출력 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 각 시트를 CSV로 변환
        csv_files = []
        for sheet_name, df in excel_data.items():
            if df.empty:
                print(f"시트 '{sheet_name}'는 비어있습니다. 건너뜁니다.")
                continue
                
            # 시트명을 파일명으로 사용
            safe_sheet_name = sheet_name.replace(" ", "_").replace("/", "_")
            csv_filename = f"SCNT_{safe_sheet_name}_Invoice_Items.csv"
            csv_path = output_path / csv_filename
            
            # CSV로 저장
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"CSV 저장 완료: {csv_path}")
            csv_files.append(str(csv_path))
            
            # 데이터 미리보기
            print(f"\n시트 '{sheet_name}' 데이터 미리보기:")
            print(f"행 수: {len(df)}")
            print(f"열 수: {len(df.columns)}")
            print(f"컬럼: {list(df.columns)}")
            print(f"첫 5행:")
            print(df.head())
            print("-" * 50)
        
        return csv_files[0] if csv_files else None
        
    except Exception as e:
        print(f"Excel 변환 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    # Excel 파일 경로
    excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
    
    if not os.path.exists(excel_file):
        print(f"Excel 파일을 찾을 수 없습니다: {excel_file}")
        return
    
    # CSV로 변환
    csv_file = convert_excel_to_csv(excel_file)
    
    if csv_file:
        print(f"\n✅ 변환 완료: {csv_file}")
        print("이제 감사 시스템을 실행할 수 있습니다.")
    else:
        print("❌ 변환 실패")

if __name__ == "__main__":
    main()
