"""
간단한 Invoice Audit System 실행 스크립트

Excel 파일을 직접 읽어서 기본적인 감사를 수행합니다.
"""

import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

def run_simple_audit():
    """간단한 감사 실행"""
    print("🚀 간단한 Invoice Audit System 실행")
    print("=" * 50)
    
    # Excel 파일 경로
    excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel 파일을 찾을 수 없습니다: {excel_file}")
        return
    
    try:
        # Excel 파일 읽기
        print(f"📁 Excel 파일 읽는 중: {excel_file}")
        excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
        
        print(f"✅ 발견된 시트: {len(excel_data)}개")
        
        # 각 시트 분석
        audit_results = {}
        total_invoices = 0
        total_amount = 0.0
        
        for sheet_name, df in excel_data.items():
            print(f"\n📋 시트 '{sheet_name}' 분석 중...")
            print(f"  - 행 수: {len(df)}")
            print(f"  - 열 수: {len(df.columns)}")
            
            # 데이터 분석
            non_empty_rows = df.dropna(how='all').shape[0]
            print(f"  - 비어있지 않은 행: {non_empty_rows}")
            
            # 금액 관련 데이터 찾기
            amount_columns = []
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    non_null_count = df[col].notna().sum()
                    if non_null_count > 0:
                        amount_columns.append(col)
                        print(f"  - 숫자 컬럼 '{col}': {non_null_count}개 값")
            
            # 시트별 요약
            sheet_summary = {
                "total_rows": len(df),
                "non_empty_rows": non_empty_rows,
                "amount_columns": amount_columns,
                "data_preview": df.head(3).to_dict('records') if not df.empty else []
            }
            
            audit_results[sheet_name] = sheet_summary
            total_invoices += non_empty_rows
        
        # 전체 요약
        print(f"\n📊 전체 감사 결과:")
        print(f"  - 총 시트 수: {len(excel_data)}")
        print(f"  - 총 송장 항목: {total_invoices}")
        print(f"  - 분석 완료: {len(audit_results)}개 시트")
        
        # 결과 저장
        result_data = {
            "audit_date": datetime.now().isoformat(),
            "excel_file": excel_file,
            "total_sheets": len(excel_data),
            "total_invoices": total_invoices,
            "sheet_results": audit_results
        }
        
        output_file = "simple_audit_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ 감사 결과 저장: {output_file}")
        
        # 주요 시트별 상세 정보
        print(f"\n🔍 주요 시트 상세 정보:")
        for sheet_name, summary in list(audit_results.items())[:5]:  # 처음 5개만
            print(f"  - {sheet_name}: {summary['non_empty_rows']}개 항목")
        
        print(f"\n✅ 감사 완료!")
        
    except Exception as e:
        print(f"❌ 감사 실행 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_audit()
