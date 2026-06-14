#!/usr/bin/env python3
"""
OFCO Pipeline 전체 실행 스크립트

7개 단계를 순차적으로 실행하고, 최종적으로 OFCO INVOICE.xlsx에 통합하는 스크립트입니다.

Usage:
    python run_full_pipeline.py <pdf_file> [options]

Example:
    python run_full_pipeline.py data/OFCO-INV-0001178_Samsung.pdf
    python run_full_pipeline.py data/OFCO-INV-0001178_Samsung.pdf --integrate --target "OFCO INVOICE.xlsx"
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 프로젝트 루트 경로 추가
# pipeline_execution_scripts/00_run_full_pipeline.py 위치 기준
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 메인 파이프라인 import
# pipeline_execution_scripts/00_run_full_pipeline.py 위치 기준
# main 위치: pipeline_docs/main/
main_path = project_root / "pipeline_docs" / "main"
sys.path.insert(0, str(main_path))
from ofco_pdf_to_complete_pipeline import main as run_pipeline

# 통합 스크립트 import (같은 폴더의 step07 파일 사용)
# pipeline_execution_scripts/step07_ofco_integrate_pipeline_to_excel.py
integration_script_path = Path(__file__).parent
sys.path.insert(0, str(integration_script_path))
from step07_ofco_integrate_pipeline_to_excel import integrate_data


def run_full_pipeline(
    pdf_path: str,
    output_path: Optional[str] = None,
    integrate: bool = False,
    target_file: str = "OFCO INVOICE.xlsx",
    source_sheet: str = "Standard_Lines",
    backup: bool = True
) -> bool:
    """
    전체 파이프라인 실행 (Step 1-7) 및 선택적 통합

    Args:
        pdf_path: PDF 파일 경로
        output_path: 출력 Excel 파일 경로 (None이면 자동 생성)
        integrate: OFCO INVOICE.xlsx에 통합할지 여부
        target_file: 통합 대상 파일 경로
        source_sheet: 통합 소스 시트 (Standard_Lines, Complete_Pipeline, EA_Slots)
        backup: 백업 파일 생성 여부

    Returns:
        성공 여부
    """
    # 프로젝트 루트 경로 (함수 내에서도 사용)
    project_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("OFCO Pipeline 전체 실행 (Step 1-7)")
    print("=" * 80)
    print()

    # Step 1-7: PDF → Complete Pipeline Excel
    print("[Phase 1] PDF 파싱 및 Complete Pipeline 실행...")
    print("-" * 80)
    
    try:
        final_df, lines_df, ea_df = run_pipeline(pdf_path, output_path)
        
        if final_df is None or lines_df is None or ea_df is None:
            print("[ERROR] 파이프라인 실행 실패")
            return False
        
        # 출력 파일 경로 확인
        # run_pipeline이 반환한 결과를 기반으로 실제 출력 파일 경로 확인
        if output_path is None:
            # PDF 파일명에서 Invoice 번호 추출
            pdf_name = Path(pdf_path).stem
            invoice_no = None
            if "OFCO-INV" in pdf_name:
                # "OFCO-INV-0001178" 형식 추출
                import re
                match = re.search(r'OFCO-INV-\d+', pdf_name)
                if match:
                    invoice_no = match.group(0)
            
            if invoice_no:
                # 메인 파이프라인은 pipeline_docs/main/에 저장
                # Invoice 번호에서 하이픈을 언더스코어로 변환
                invoice_no_clean = invoice_no.replace('-', '_')
                output_path = f"pipeline_docs/main/ofco_pipeline_pdf_{invoice_no_clean}_v3.xlsx"
            else:
                output_path = f"pipeline_docs/main/ofco_pipeline_pdf_{pdf_name}_v3.xlsx"
        
        pipeline_output = Path(output_path)
        if not pipeline_output.exists():
            # 루트 디렉토리에서도 확인
            alt_path = Path(pipeline_output.name)
            if alt_path.exists():
                pipeline_output = alt_path
                output_path = str(alt_path)
            else:
                print(f"[ERROR] 파이프라인 출력 파일을 찾을 수 없습니다: {output_path}")
                print(f"[INFO] 대체 경로 확인: {alt_path}")
                # 실제 생성된 파일 찾기
                main_dir = Path("pipeline_docs/main")
                if main_dir.exists():
                    xlsx_files = list(main_dir.glob("ofco_pipeline_pdf_*_v3.xlsx"))
                    if xlsx_files:
                        print(f"[INFO] 발견된 파일: {xlsx_files[0]}")
                        pipeline_output = xlsx_files[0]
                        output_path = str(xlsx_files[0])
                    else:
                        return False
                else:
                    return False
        
        print(f"[OK] 파이프라인 완료: {output_path}")
        print(f"  - Standard_Lines: {len(lines_df)}행")
        print(f"  - EA_Slots: {len(ea_df)}행")
        print()
        
    except Exception as e:
        print(f"[ERROR] 파이프라인 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 8 (선택): OFCO INVOICE.xlsx 통합
    if integrate:
        print("\n" + "=" * 80)
        print("[Phase 2] OFCO INVOICE.xlsx 통합 (6단계 프로세스)")
        print("=" * 80)
        print()
        print("통합 프로세스는 다음 6단계로 진행됩니다:")
        print("  Step 1/6: 소스 파일 읽기 (Standard_Lines/Complete_Pipeline/EA_Slots)")
        print("  Step 2/6: 대상 파일 읽기 (OFCO INVOICE.xlsx Sheet1)")
        print("  Step 3/6: 기존 데이터 처리 (Invoice Number 기준 삭제)")
        print("  Step 4/6: 데이터 변환 (기본 정보, Cost/Price Center, EA 슬롯, 금액 정보)")
        print("  Step 5/6: HeaderCore 적용 (컬럼 정렬 및 매핑)")
        print("  Step 6/6: 순번 재계산 및 파일 저장")
        print()
        print("-" * 80)
        
        target_path = Path(target_file)
        if not target_path.exists():
            print(f"[WARNING] 대상 파일이 없습니다: {target_file}")
            print("[INFO] 통합을 건너뜁니다.")
            return True
        
        try:
            success, stats = integrate_data(
                source_file=str(pipeline_output),
                target_file=str(target_path),
                source_sheet=source_sheet,
                backup=backup
            )
            
            if success:
                print("\n" + "=" * 80)
                print("[SUCCESS] 통합 완료")
                print("=" * 80)
                print(f"대상 파일: {target_file}")
                print(f"소스 시트: {source_sheet}")
                print(f"  - 추가된 행 수: {stats.get('added_rows', 0)}")
                print(f"  - 삭제된 행 수: {stats.get('deleted_rows', 0)}")
                print(f"  - 최종 행 수: {stats.get('target_rows_after', 0)}")
                print(f"  - 변경 전 행 수: {stats.get('target_rows_before', 0)}")
                print(f"  - 행 수 변화: {stats.get('target_rows_after', 0) - stats.get('target_rows_before', 0):+d}")
                
                # 분석 보고서 폴더 안내
                analysis_reports_path = project_root / "pipeline_docs" / "pipeline_steps" / "step_07_final_output" / "docs" / "OFCO_INVOICE_ANALYSIS_REPORTS"
                if analysis_reports_path.exists():
                    print(f"\n[INFO] 상세 통합 프로세스 분석 보고서:")
                    print(f"  {analysis_reports_path}")
                    print(f"  - OFCO_INVOICE_INTEGRATION_FLOW.md: 통합 프로세스 흐름도")
                    print(f"  - OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md: 컬럼 매핑 상세")
            else:
                print(f"\n[ERROR] 통합 실패")
                if stats.get('errors'):
                    print(f"오류 {len(stats.get('errors', []))}개:")
                    for error in stats['errors'][:5]:
                        print(f"  - {error}")
                    if len(stats.get('errors', [])) > 5:
                        print(f"  ... 및 {len(stats.get('errors', [])) - 5}개 더")
                return False
                
        except Exception as e:
            print(f"\n[ERROR] 통합 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n" + "=" * 80)
        print("[INFO] 통합 단계는 건너뜁니다. (--integrate 옵션 사용)")
        print("=" * 80)
        print(f"\n수동 통합 명령:")
        print(f"  python {Path(__file__).parent / 'step07_ofco_integrate_pipeline_to_excel.py'} \\")
        print(f"    --source {pipeline_output} \\")
        print(f"    --source-sheet {source_sheet} \\")
        print(f"    --target \"{target_file}\" \\")
        print(f"    --backup")
        print(f"\n통합 프로세스 상세 정보:")
        analysis_reports_path = project_root / "pipeline_docs" / "pipeline_steps" / "step_07_final_output" / "docs" / "OFCO_INVOICE_ANALYSIS_REPORTS"
        if analysis_reports_path.exists():
            print(f"  {analysis_reports_path}")
            print(f"  - OFCO_INVOICE_INTEGRATION_FLOW.md: 6단계 통합 프로세스 흐름도")
            print(f"  - OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md: 컬럼 매핑 상세 규칙")

    print()
    print("=" * 80)
    print("[SUCCESS] 전체 파이프라인 실행 완료")
    print("=" * 80)
    
    # 분석 보고서 폴더 안내
    analysis_reports_path = project_root / "pipeline_docs" / "pipeline_steps" / "step_07_final_output" / "docs" / "OFCO_INVOICE_ANALYSIS_REPORTS"
    if analysis_reports_path.exists():
        print(f"\n[INFO] 통합 프로세스 상세 분석 보고서:")
        print(f"  {analysis_reports_path.absolute()}")
        print(f"  - OFCO_INVOICE_INTEGRATION_FLOW.md: 6단계 통합 프로세스 흐름도")
        print(f"  - OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md: 컬럼 매핑 상세 규칙")
        print(f"  - OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md: 구조 상세 분석")
        print(f"  - M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md: M:CV ↔ DA:DH 상관관계")
    
    return True


def main():
    """메인 실행 함수"""
    # 분석 보고서 경로 확인
    project_root = Path(__file__).parent.parent
    analysis_reports_path = project_root / "pipeline_docs" / "pipeline_steps" / "step_07_final_output" / "docs" / "OFCO_INVOICE_ANALYSIS_REPORTS"
    analysis_info = ""
    if analysis_reports_path.exists():
        analysis_info = f"""
        
통합 프로세스 상세 정보:
  상세 분석 보고서: {analysis_reports_path.absolute()}
  - OFCO_INVOICE_INTEGRATION_FLOW.md: 6단계 통합 프로세스 흐름도
  - OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md: 컬럼 매핑 상세 규칙
  - OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md: 구조 상세 분석
  - M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md: M:CV ↔ DA:DH 상관관계 분석
        """
    
    parser = argparse.ArgumentParser(
        description='OFCO Pipeline 전체 실행 (Step 1-7) 및 선택적 통합',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
예시:
  # 파이프라인만 실행 (통합 없음)
  python run_full_pipeline.py data/OFCO-INV-0001178_Samsung.pdf

  # 파이프라인 실행 + OFCO INVOICE.xlsx 통합
  python run_full_pipeline.py data/OFCO-INV-0001178_Samsung.pdf --integrate

  # 통합 대상 파일 지정
  python run_full_pipeline.py data/OFCO-INV-0001178_Samsung.pdf \\
    --integrate --target "OFCO INVOICE.xlsx" --source-sheet Standard_Lines

통합 프로세스:
  통합은 6단계로 진행됩니다:
  1. 소스 파일 읽기 (Standard_Lines/Complete_Pipeline/EA_Slots)
  2. 대상 파일 읽기 (OFCO INVOICE.xlsx Sheet1)
  3. 기존 데이터 처리 (Invoice Number 기준 삭제)
  4. 데이터 변환 (기본 정보, Cost/Price Center, EA 슬롯, 금액 정보)
  5. HeaderCore 적용 (컬럼 정렬 및 매핑)
  6. 순번 재계산 및 파일 저장{analysis_info}
        """
    )
    
    parser.add_argument('pdf_path', type=str, help='PDF 파일 경로')
    parser.add_argument('--output', type=str, default=None,
                        help='출력 Excel 파일 경로 (기본값: 자동 생성)')
    parser.add_argument('--integrate', action='store_true',
                        help='OFCO INVOICE.xlsx에 통합 (기본값: False)')
    parser.add_argument('--target', type=str, default='OFCO INVOICE.xlsx',
                        help='통합 대상 파일 경로 (기본값: OFCO INVOICE.xlsx)')
    parser.add_argument('--source-sheet', type=str, default='Standard_Lines',
                        choices=['Complete_Pipeline', 'EA_Slots', 'Standard_Lines'],
                        help='통합 소스 시트명 (기본값: Standard_Lines)')
    parser.add_argument('--backup', action='store_true', default=True,
                        help='백업 파일 생성 (기본값: True)')
    parser.add_argument('--no-backup', action='store_false', dest='backup',
                        help='백업 파일 생성 안 함')
    
    args = parser.parse_args()
    
    # PDF 파일 존재 확인
    pdf_file = Path(args.pdf_path)
    if not pdf_file.exists():
        print(f"[ERROR] PDF 파일을 찾을 수 없습니다: {args.pdf_path}")
        sys.exit(1)
    
    # 실행
    success = run_full_pipeline(
        pdf_path=str(pdf_file),
        output_path=args.output,
        integrate=args.integrate,
        target_file=args.target,
        source_sheet=args.source_sheet,
        backup=args.backup
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

