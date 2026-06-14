#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASE_NO 중복 검증 스크립트

각 Stage 출력 파일에서 CASE_NO 중복을 검증하고 리포트를 생성합니다.
"""
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import find_header_by_meaning

def verify_case_no_dedup(file_path: Path, stage_name: str) -> dict:
    """단일 파일에서 CASE_NO 중복 검증"""
    
    if not file_path.exists():
        return {
            "stage": stage_name,
            "file": str(file_path),
            "status": "NOT_FOUND",
            "total_records": 0,
            "unique_cases": 0,
            "duplicates": 0,
            "duplicate_list": []
        }
    
    try:
        # 시트 이름 자동 감지
        excel_file = pd.ExcelFile(file_path)
        sheet_name = None
        for name in ["Merged Data", "통합_원본데이터_Fixed", "Case List, RIL"]:
            if name in excel_file.sheet_names:
                sheet_name = name
                break
        
        if not sheet_name:
            sheet_name = excel_file.sheet_names[0]
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        return {
            "stage": stage_name,
            "file": str(file_path),
            "status": "ERROR",
            "error": str(e),
            "total_records": 0,
            "unique_cases": 0,
            "duplicates": 0
        }
    
    # Case No 컬럼 찾기
    case_col = find_header_by_meaning(df, "case_number", required=False)
    if not case_col:
        return {
            "stage": stage_name,
            "file": str(file_path),
            "status": "NO_CASE_COLUMN",
            "total_records": len(df),
            "unique_cases": 0,
            "duplicates": 0
        }
    
    # 중복 확인
    case_counts = df[case_col].value_counts()
    duplicates = case_counts[case_counts > 1]
    
    duplicate_list = []
    if len(duplicates) > 0:
        # 중복된 Case No 목록 (최대 20개)
        for case_no in duplicates.index[:20]:
            duplicate_list.append({
                "case_no": str(case_no),
                "count": int(duplicates[case_no])
            })
    
    return {
        "stage": stage_name,
        "file": str(file_path),
        "status": "OK",
        "sheet_name": sheet_name,
        "total_records": len(df),
        "unique_cases": case_counts.size,
        "duplicates": len(duplicates),
        "duplicate_records": int(duplicates.sum()) if len(duplicates) > 0 else 0,
        "case_column": case_col,
        "duplicate_list": duplicate_list
    }

def generate_report(results: list):
    """검증 결과 리포트 생성"""
    
    report_content = f"""# CASE_NO 중복 검증 리포트

**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 요약

"""
    
    total_duplicates = 0
    for result in results:
        status_icon = "✅" if result["duplicates"] == 0 else "⚠️"
        report_content += f"### {status_icon} {result['stage']}\n\n"
        report_content += f"- **파일**: `{Path(result['file']).name}`\n"
        report_content += f"- **상태**: {result['status']}\n"
        
        if result["status"] == "OK":
            report_content += f"- **총 레코드**: {result['total_records']}건\n"
            report_content += f"- **고유 CASE_NO**: {result['unique_cases']}개\n"
            report_content += f"- **중복 CASE_NO**: {result['duplicates']}개\n"
            report_content += f"- **중복 레코드**: {result['duplicate_records']}건\n"
            
            if result['duplicates'] > 0:
                total_duplicates += result['duplicates']
                report_content += f"- **Case No 컬럼**: {result['case_column']}\n\n"
                
                if result['duplicate_list']:
                    report_content += "**중복된 CASE_NO (일부)**:\n"
                    for dup in result['duplicate_list'][:10]:
                        report_content += f"- {dup['case_no']}: {dup['count']}회\n"
        else:
            report_content += f"- **에러**: {result.get('error', 'Unknown error')}\n"
        
        report_content += "\n"
    
    report_content += f"""## 최종 결과

- **총 중복 CASE_NO**: {total_duplicates}개
- **검증 상태**: {"✅ 통과" if total_duplicates == 0 else "⚠️ 중복 발견"}

"""
    
    if total_duplicates > 0:
        report_content += """## 권장 사항

1. Stage 1 merged 파일에서 중복 제거 로직 확인
2. Stage 3 데이터 통합 시 중복 제거 확인
3. 중복된 CASE_NO의 데이터 차이 분석 필요

"""
    
    return report_content

def main():
    """메인 함수"""
    
    print("=" * 80)
    print("CASE_NO 중복 검증")
    print("=" * 80)
    
    results = []
    
    # Stage 1 검증
    print("\n[1] Stage 1 검증 중...")
    stage1_file = PROJECT_ROOT / "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx"
    result1 = verify_case_no_dedup(stage1_file, "Stage 1 (Merged)")
    results.append(result1)
    print(f"  - 중복: {result1['duplicates']}개")
    
    # Stage 2 검증
    print("\n[2] Stage 2 검증 중...")
    stage2_file = PROJECT_ROOT / "data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx"
    result2 = verify_case_no_dedup(stage2_file, "Stage 2 (Derived)")
    results.append(result2)
    print(f"  - 중복: {result2['duplicates']}개")
    
    # Stage 3 검증
    print("\n[3] Stage 3 검증 중...")
    report_dir = PROJECT_ROOT / "data/processed/reports"
    report_files = list(report_dir.glob("HVDC_입고로직_종합리포트_*.xlsx"))
    if report_files:
        latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
        result3 = verify_case_no_dedup(latest_report, "Stage 3 (Report)")
        results.append(result3)
        print(f"  - 중복: {result3['duplicates']}개")
    
    # 리포트 생성
    print("\n[4] 리포트 생성 중...")
    report_content = generate_report(results)
    
    output_file = PROJECT_ROOT / "data/investigation/case_no_dedup_verification.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"  - 리포트 저장: {output_file}")
    
    # 콘솔 출력
    print("\n" + "=" * 80)
    print(report_content)
    print("=" * 80)

if __name__ == "__main__":
    main()

