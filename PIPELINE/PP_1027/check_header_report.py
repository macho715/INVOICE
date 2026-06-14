#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
헤더 순서 비교 보고서 내용 확인 스크립트
"""

import pandas as pd
from pathlib import Path

def check_report_content():
    """생성된 보고서의 내용 확인"""
    file_path = Path("header_order_comparison_report.xlsx")
    
    if not file_path.exists():
        print("❌ 보고서 파일을 찾을 수 없습니다")
        return
    
    try:
        # Excel 파일 읽기
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        print("=" * 60)
        print("헤더 순서 비교 보고서 내용 확인")
        print("=" * 60)
        print(f"📁 파일: {file_path}")
        print(f"📋 시트 수: {len(sheet_names)}")
        print(f"📊 시트 목록: {sheet_names}")
        print()
        
        # 각 시트별 내용 확인
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"📄 시트: {sheet_name}")
            print(f"   - 행 수: {len(df)}")
            print(f"   - 열 수: {len(df.columns)}")
            
            if sheet_name == "헤더 순서 비교":
                print("   - 첫 5행 미리보기:")
                print(df.head().to_string(index=False))
            elif "전체 헤더" in sheet_name:
                print(f"   - 첫 10개 헤더:")
                for i, header in enumerate(df.iloc[:10, 1]):
                    print(f"     {i+1:2d}. {header}")
            elif sheet_name == "차이점 분석":
                print("   - 분석 결과:")
                for _, row in df.iterrows():
                    print(f"     {row['분석 항목']}: {row['값']}")
            
            print()
        
        # 주요 차이점 요약
        print("=" * 60)
        print("주요 차이점 요약")
        print("=" * 60)
        
        # 각 스테이지별 헤더 수
        stage1_df = pd.read_excel(file_path, sheet_name="Stage 1 전체 헤더")
        stage2_df = pd.read_excel(file_path, sheet_name="Stage 2 전체 헤더")
        stage3_df = pd.read_excel(file_path, sheet_name="Stage 3 전체 헤더")
        standard_df = pd.read_excel(file_path, sheet_name="표준 순서 정의")
        
        print(f"📊 Stage 1 헤더 수: {len(stage1_df)}개")
        print(f"📊 Stage 2 헤더 수: {len(stage2_df)}개")
        print(f"📊 Stage 3 헤더 수: {len(stage3_df)}개")
        print(f"📊 표준 헤더 수: {len(standard_df)}개")
        print()
        
        # 순서 비교
        comparison_df = pd.read_excel(file_path, sheet_name="헤더 순서 비교")
        match_count = len(comparison_df[comparison_df['일치여부'] == '✅'])
        mismatch_count = len(comparison_df[comparison_df['일치여부'] == '❌'])
        warning_count = len(comparison_df[comparison_df['일치여부'] == '⚠️'])
        
        print(f"✅ 일치: {match_count}개")
        print(f"❌ 불일치: {mismatch_count}개")
        print(f"⚠️ 경고: {warning_count}개")
        
    except Exception as e:
        print(f"❌ 보고서 확인 실패: {e}")

if __name__ == "__main__":
    check_report_content()

