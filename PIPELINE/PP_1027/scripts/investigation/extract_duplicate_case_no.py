#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
중복 CASE_NO 추출 및 분석 스크립트

Stage 3 최종 리포트에서 중복 CASE_NO를 추출하고 상세 분석을 수행합니다.
"""
import pandas as pd
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import find_header_by_meaning

def extract_duplicate_case_no(report_file: Path):
    """중복 CASE_NO 추출 및 분석"""
    
    print("=" * 80)
    print("중복 CASE_NO 추출 및 분석")
    print("=" * 80)
    
    if not report_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {report_file}")
        return
    
    print(f"\n[1] 파일 로드: {report_file.name}")
    try:
        df = pd.read_excel(report_file, sheet_name="통합_원본데이터_Fixed")
    except:
        # 다른 시트 이름 시도
        df = pd.read_excel(report_file, sheet_name=0)
    
    print(f"  - 총 레코드: {len(df)}건")
    
    # Case No 컬럼 찾기
    case_col = find_header_by_meaning(df, "case_number", required=False)
    if not case_col:
        print("❌ Case No 컬럼을 찾을 수 없습니다")
        return
    
    print(f"  - Case No 컬럼: {case_col}")
    
    # 중복 확인
    print(f"\n[2] 중복 CASE_NO 분석")
    case_counts = df[case_col].value_counts()
    duplicates = case_counts[case_counts > 1]
    
    print(f"  - 고유 CASE_NO: {case_counts.size}개")
    print(f"  - 중복된 CASE_NO: {len(duplicates)}개")
    print(f"  - 총 중복 레코드: {duplicates.sum()}건")
    
    if len(duplicates) == 0:
        print("  ✅ 중복이 없습니다!")
        return
    
    # 중복 분포 분석
    print(f"\n[3] 중복 횟수별 분포")
    dup_distribution = Counter(duplicates.values)
    for count, num_cases in sorted(dup_distribution.items()):
        print(f"  - {count}회 중복: {num_cases}개 CASE_NO")
    
    # Source_Vendor별 분석
    source_vendor_col = "Source_Vendor" if "Source_Vendor" in df.columns else None
    if source_vendor_col:
        print(f"\n[4] Source_Vendor별 중복 분포")
        duplicate_cases = duplicates.index.tolist()
        dup_df = df[df[case_col].isin(duplicate_cases)]
        vendor_dist = dup_df[source_vendor_col].value_counts()
        for vendor, count in vendor_dist.items():
            print(f"  - {vendor}: {count}건")
    
    # 중복 데이터 상세 분석
    print(f"\n[5] 중복 데이터 상세 추출 중...")
    duplicate_records = []
    
    for case_no in duplicates.index[:50]:  # 첫 50개만 상세 분석
        case_data = df[df[case_col] == case_no]
        
        # 컬럼 값 차이 분석
        for idx, row in case_data.iterrows():
            record_info = {
                "Case_No": case_no,
                "Row_Index": idx,
                "Duplicate_Count": len(case_data),
            }
            
            # 주요 컬럼 값 추출
            key_cols = ["Source_Vendor", "Source_Sheet", "Site", "Description"]
            for col in key_cols:
                if col in df.columns:
                    record_info[col] = row[col]
            
            duplicate_records.append(record_info)
    
    # 결과 저장
    output_file = PROJECT_ROOT / "data/investigation/duplicate_case_no_analysis.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 중복 요약
        summary_data = {
            'Metric': ['고유 CASE_NO', '중복 CASE_NO', '총 중복 레코드', '최대 중복 횟수'],
            'Value': [
                case_counts.size,
                len(duplicates),
                duplicates.sum(),
                duplicates.max() if len(duplicates) > 0 else 0
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # 중복 CASE_NO 목록
        dup_list = pd.DataFrame({
            'Case_No': duplicates.index,
            'Duplicate_Count': duplicates.values
        }).sort_values('Duplicate_Count', ascending=False)
        dup_list.to_excel(writer, sheet_name='Duplicate_List', index=False)
        
        # 중복 레코드 상세
        if duplicate_records:
            pd.DataFrame(duplicate_records).to_excel(writer, sheet_name='Duplicate_Details', index=False)
        
        # Source_Vendor별 분포
        if source_vendor_col:
            vendor_summary = pd.DataFrame({
                'Source_Vendor': vendor_dist.index,
                'Duplicate_Records': vendor_dist.values
            })
            vendor_summary.to_excel(writer, sheet_name='Vendor_Distribution', index=False)
    
    print(f"\n[6] 결과 저장: {output_file}")
    print("\n" + "=" * 80)
    print("분석 완료")
    print("=" * 80)

if __name__ == "__main__":
    # 최신 리포트 파일 찾기
    report_dir = PROJECT_ROOT / "data/processed/reports"
    
    if len(sys.argv) > 1:
        report_file = Path(sys.argv[1])
    else:
        # 최신 파일 자동 선택
        report_files = list(report_dir.glob("HVDC_입고로직_종합리포트_*.xlsx"))
        if not report_files:
            print(f"❌ 리포트 파일을 찾을 수 없습니다: {report_dir}")
            sys.exit(1)
        report_file = max(report_files, key=lambda p: p.stat().st_mtime)
    
    extract_duplicate_case_no(report_file)

