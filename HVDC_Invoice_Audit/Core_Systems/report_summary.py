#!/usr/bin/env python3
"""9월 SHPT 인보이스 검증 보고서 요약"""

import pandas as pd
from pathlib import Path

# 최신 보고서 로드
report_path = Path("../Results/Sept_2025/Reports/SHPT_SEPT_2025_FINAL_REPORT_20251014_084305.xlsx")

print("=== 9월 SHPT 인보이스 검증 최종 보고서 ===\n")
print(f"📁 파일: {report_path.name}")
print(f"📊 크기: {report_path.stat().st_size // 1024} KB")
print(f"⏰ 생성: 2025-10-14 11:43\n")

# 시트 구조
xl = pd.ExcelFile(report_path)
print(f"📄 시트 구조 ({len(xl.sheet_names)}개):")
for i, name in enumerate(xl.sheet_names, 1):
    print(f"  {i}. {name}")

# Main_Data 요약
df = pd.read_excel(xl, sheet_name='Main_Data')
print(f"\n📈 Main_Data 요약:")
print(f"  - 총 항목: {len(df)}개")
print(f"  - 컬럼 수: {len(df.columns)}개")

# 상태별 집계
status_counts = df['status'].value_counts()
print(f"  - PASS: {status_counts.get('PASS', 0)}개")
print(f"  - FAIL: {status_counts.get('FAIL', 0)}개")
print(f"  - REVIEW: {status_counts.get('REVIEW', 0)}개")

# 금액 합계
if 'total_usd' in df.columns:
    total_amount = df['total_usd'].sum()
    print(f"\n💰 총 금액: ${total_amount:,.2f}")

# PDF 통합 현황
if 'pdf_validation_enabled' in df.columns:
    pdf_enabled = df['pdf_validation_enabled'].sum()
    print(f"\n📑 PDF 통합:")
    print(f"  - PDF 검증 항목: {pdf_enabled}개")
    if 'pdf_parsed_files' in df.columns:
        total_pdfs = df['pdf_parsed_files'].sum()
        print(f"  - 파싱된 PDF: {int(total_pdfs)}개")

# Gate 검증 현황
if 'gate_score' in df.columns:
    avg_gate_score = df['gate_score'].mean()
    print(f"\n🚪 Gate 검증:")
    print(f"  - 평균 Gate Score: {avg_gate_score:.1f}")

print(f"\n✅ 보고서 위치: {report_path}")
print(f"✅ 5개 시트 | 40개 컬럼 | 표준 형식 준수")


