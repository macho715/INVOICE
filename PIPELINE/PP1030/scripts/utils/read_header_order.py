#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
확정된 헤더 순서 읽기
"""

import pandas as pd
from pathlib import Path

def read_final_header_order():
    """헤더 순서 확정 시트 읽기"""
    file_path = Path("header_order_comparison_report.xlsx")
    
    try:
        # Excel 파일의 모든 시트 확인
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print("=" * 60)
        print("Excel 파일의 시트 목록")
        print("=" * 60)
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"{i}. {sheet_name}")
        
        # "헤더 순서 확정" 시트가 있는지 확인
        if "헤더 순서 확정" in sheet_names:
            df = pd.read_excel(file_path, sheet_name="헤더 순서 확정")
            print("\n" + "=" * 60)
            print("✅ '헤더 순서 확정' 시트 발견")
            print("=" * 60)
            print(f"행 수: {len(df)}")
            print(f"열: {df.columns.tolist()}")
            print("\n첫 20개 헤더:")
            print(df.head(20).to_string(index=False))
            
            # 확정된 헤더 순서 추출
            if '최종 헤더 순서' in df.columns:
                final_headers = df['최종 헤더 순서'].dropna().tolist()
                print(f"\n✅ 확정된 헤더 순서 추출 완료: {len(final_headers)}개")
                return final_headers
            else:
                print("❌ '최종 헤더 순서' 컬럼을 찾을 수 없습니다")
                print(f"사용 가능한 컬럼: {df.columns.tolist()}")
                return None
        else:
            print("\n❌ '헤더 순서 확정' 시트를 찾을 수 없습니다")
            print("사용자가 시트를 추가해야 합니다")
            return None
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

if __name__ == "__main__":
    read_final_header_order()


