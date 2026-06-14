"""
OFCO 인보이스 자동 처리 시스템 - 월간 실행 스크립트
작성자: MACHO-GPT v3.4-mini
작성일: 2025-11-10

사용법:
    python monthly_runner.py --month 2024-11
    python monthly_runner.py --month 2024-11 --auto-fix
    python monthly_runner.py --all-months
"""

import argparse
from datetime import datetime
from pathlib import Path
import sys

from invoice_processor import InvoiceProcessor
from config import FILE_PATHS


def parse_arguments():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='OFCO 월간 인보이스 자동 처리'
    )
    
    parser.add_argument(
        '--month',
        type=str,
        help='처리할 월 (예: 2024-11)'
    )
    
    parser.add_argument(
        '--all-months',
        action='store_true',
        help='모든 월 처리'
    )
    
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='calc_check 경고 자동 수정'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='로그 레벨'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='출력 디렉토리 (기본: config.py의 output_dir)'
    )
    
    return parser.parse_args()


def run_monthly_processing(month: str, processor: InvoiceProcessor, auto_fix: bool = False):
    """월간 처리 실행"""
    print(f"\n{'='*80}")
    print(f"Processing {month}")
    print(f"{'='*80}\n")
    
    try:
        # 1. 처리
        df_result = processor.process_monthly_invoice(month)
        
        # 2. 자동 수정 (옵션)
        if auto_fix:
            print("\n자동 수정 적용 중...")
            df_result = apply_auto_fixes(df_result)
        
        # 3. 저장
        output_filename = f"OFCO_INVOICE_{month}_Processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = processor.save_processed_invoice(df_result, output_filename)
        
        print(f"\n✅ SUCCESS: {month} 처리 완료")
        print(f"   출력 파일: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {month} 처리 실패")
        print(f"   오류: {e}")
        return False


def apply_auto_fixes(df):
    """자동 수정 적용"""
    # calc_check 경고 수정: 누락된 금액을 Qty × Rate로 채우기
    mask = df['calc_check'].notna()
    
    for idx in df[mask].index:
        # EA_1 Amount 재계산
        if pd.notna(df.loc[idx, 'EA_1_Qty']) and pd.notna(df.loc[idx, 'EA_1_Rate']):
            df.loc[idx, 'EA_1_Amount'] = df.loc[idx, 'EA_1_Qty'] * df.loc[idx, 'EA_1_Rate']
        
        # EA_2 Amount 재계산
        if pd.notna(df.loc[idx, 'EA_2_Qty']) and pd.notna(df.loc[idx, 'EA_2_Rate']):
            df.loc[idx, 'EA_2_Amount'] = df.loc[idx, 'EA_2_Qty'] * df.loc[idx, 'EA_2_Rate']
        
        # EA_3 Amount 재계산
        if pd.notna(df.loc[idx, 'EA_3_Qty']) and pd.notna(df.loc[idx, 'EA_3_Rate']):
            df.loc[idx, 'EA_3_Amount'] = df.loc[idx, 'EA_3_Qty'] * df.loc[idx, 'EA_3_Rate']
        
        # EA_4 Amount 재계산
        if pd.notna(df.loc[idx, 'EA_4_Qty']) and pd.notna(df.loc[idx, 'EA_4_Rate']):
            df.loc[idx, 'EA_4_Amount'] = df.loc[idx, 'EA_4_Qty'] * df.loc[idx, 'EA_4_Rate']
        
        # EA Total 재계산
        ea_total = sum([
            df.loc[idx, 'EA_1_Amount'] if pd.notna(df.loc[idx, 'EA_1_Amount']) else 0,
            df.loc[idx, 'EA_2_Amount'] if pd.notna(df.loc[idx, 'EA_2_Amount']) else 0,
            df.loc[idx, 'EA_3_Amount'] if pd.notna(df.loc[idx, 'EA_3_Amount']) else 0,
            df.loc[idx, 'EA_4_Amount'] if pd.notna(df.loc[idx, 'EA_4_Amount']) else 0,
        ])
        df.loc[idx, 'EA_Total_Amount'] = ea_total
    
    print(f"   자동 수정 완료: {mask.sum()}건")
    return df


def main():
    """메인 함수"""
    args = parse_arguments()
    
    # 출력 디렉토리 설정
    if args.output_dir:
        FILE_PATHS['output_dir'] = args.output_dir
    
    # 프로세서 초기화
    processor = InvoiceProcessor(log_level=args.log_level)
    
    # 처리 실행
    if args.all_months:
        # 모든 월 처리 (2024년 1월~12월)
        months = [f"2024-{str(m).zfill(2)}" for m in range(1, 13)]
        
        results = []
        for month in months:
            success = run_monthly_processing(month, processor, args.auto_fix)
            results.append((month, success))
        
        # 최종 결과
        print(f"\n{'='*80}")
        print("전체 처리 결과")
        print(f"{'='*80}")
        for month, success in results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{month}: {status}")
        
        success_count = sum(1 for _, s in results if s)
        print(f"\n총 {len(results)}개월 중 {success_count}개월 성공")
        
    elif args.month:
        # 단일 월 처리
        run_monthly_processing(args.month, processor, args.auto_fix)
        
    else:
        print("오류: --month 또는 --all-months 옵션을 지정해야 합니다.")
        sys.exit(1)


if __name__ == '__main__':
    main()
