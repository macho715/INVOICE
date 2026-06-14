#!/usr/bin/env python3
"""
OFCO 파이프라인 전체 패치 적용 스크립트

이 스크립트는 다음 순서로 패치를 적용합니다:
1. step08: calc_check 경고 수정 (금액 자동 계산)
2. step09: VAT 검증 강화 (허용 범위 적용)
3. 통합 검증 보고서 생성

Usage:
    python apply_all_patches.py --invoice OFCO-INV-0001178 --mode full
    python apply_all_patches.py --invoice OFCO-INV-0001178 --mode calc-only
    python apply_all_patches.py --invoice OFCO-INV-0001178 --mode vat-only

Options:
    --invoice: Invoice 번호 (예: OFCO-INV-0001178)
    --mode: 패치 모드 (full, calc-only, vat-only) (기본값: full)
    --tolerance-calc: calc_check 금액 오차 허용 (기본값: 0.01 AED)
    --tolerance-vat: VAT 오차 허용 비율 (기본값: 0.02 = 2%)
    --recalculate-vat: VAT 자동 재계산 활성화
    --backup: 백업 생성 (기본값: True)
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse


def run_step08(invoice_no: str, tolerance: float = 0.01, backup: bool = True) -> bool:
    """
    Step 08 실행: calc_check 경고 수정
    
    Args:
        invoice_no: Invoice 번호
        tolerance: 금액 오차 허용 범위
        backup: 백업 생성 여부
    
    Returns:
        성공 여부
    """
    print(f"\n{'='*80}")
    print(f"[STEP 08] calc_check 경고 수정")
    print(f"{'='*80}\n")
    
    pipeline_file = f"ofco_pipeline_pdf_{invoice_no}_v3.xlsx"
    
    # EA_Slots 시트 처리
    cmd = [
        sys.executable,
        "step08_ofco_fix_calc_warnings.py",
        "--input", pipeline_file,
        "--sheet", "EA_Slots",
        "--tolerance", str(tolerance)
    ]
    
    if not backup:
        cmd.append("--no-backup")
    
    print(f"[INFO] 실행 명령: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"[ERROR] Step 08 실패 (EA_Slots)")
        return False
    
    # Standard_Lines 시트 처리
    cmd[3] = "Standard_Lines"  # --sheet 변경
    print(f"\n[INFO] 실행 명령: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"[ERROR] Step 08 실패 (Standard_Lines)")
        return False
    
    print(f"\n[SUCCESS] Step 08 완료")
    return True


def run_step09(
    invoice_no: str,
    tolerance: float = 0.02,
    recalculate: bool = False,
    backup: bool = True
) -> bool:
    """
    Step 09 실행: VAT 검증 강화
    
    Args:
        invoice_no: Invoice 번호
        tolerance: VAT 오차 허용 비율
        recalculate: VAT 자동 재계산 여부
        backup: 백업 생성 여부
    
    Returns:
        성공 여부
    """
    print(f"\n{'='*80}")
    print(f"[STEP 09] VAT 검증 강화")
    print(f"{'='*80}\n")
    
    pipeline_file = f"ofco_pipeline_pdf_{invoice_no}_v3.xlsx"
    
    # EA_Slots 시트 처리
    cmd = [
        sys.executable,
        "step09_ofco_vat_validator.py",
        "--input", pipeline_file,
        "--sheet", "EA_Slots",
        "--tolerance", str(tolerance)
    ]
    
    if recalculate:
        cmd.append("--recalculate")
    
    if not backup:
        cmd.append("--no-backup")
    
    print(f"[INFO] 실행 명령: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"[ERROR] Step 09 실패 (EA_Slots)")
        return False
    
    # Standard_Lines 시트 처리
    cmd[3] = "Standard_Lines"  # --sheet 변경
    print(f"\n[INFO] 실행 명령: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"[ERROR] Step 09 실패 (Standard_Lines)")
        return False
    
    print(f"\n[SUCCESS] Step 09 완료")
    return True


def generate_validation_report(invoice_no: str) -> None:
    """
    검증 보고서 생성
    
    Args:
        invoice_no: Invoice 번호
    """
    print(f"\n{'='*80}")
    print(f"[검증 보고서] 생성 중...")
    print(f"{'='*80}\n")
    
    report_path = Path(f"PATCH_VALIDATION_REPORT_{invoice_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# OFCO 파이프라인 패치 검증 보고서\n\n")
        f.write(f"**Invoice**: {invoice_no}\n")
        f.write(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**패치 버전**: v1.0 (Step 08 + Step 09)\n\n")
        
        f.write(f"## 적용된 패치\n\n")
        f.write(f"### Step 08: calc_check 경고 수정\n")
        f.write(f"- 누락된 금액 자동 계산 (단가 × 수량)\n")
        f.write(f"- 금액 오차 수정 (허용 범위: ±0.01 AED)\n")
        f.write(f"- EA_Total_Amount 재계산\n\n")
        
        f.write(f"### Step 09: VAT 검증 강화\n")
        f.write(f"- VAT 오차 허용 범위 도입 (기본 2%)\n")
        f.write(f"- VAT 누락 시 자동 계산 (5% 세율)\n")
        f.write(f"- vat_check 재검증\n\n")
        
        f.write(f"## 후속 작업 권장사항\n\n")
        f.write(f"1. **Step 07 재실행**: 패치된 데이터를 OFCO INVOICE.xlsx에 통합\n")
        f.write(f"   ```bash\n")
        f.write(f"   python step07_ofco_integrate_pipeline_to_excel.py --source ofco_pipeline_pdf_{invoice_no}_v3.xlsx\n")
        f.write(f"   ```\n\n")
        
        f.write(f"2. **검증 실행**: 통합 후 전체 검증 수행\n")
        f.write(f"   ```bash\n")
        f.write(f"   python step07_validate_integration.py --file \"OFCO INVOICE.xlsx\"\n")
        f.write(f"   ```\n\n")
        
        f.write(f"3. **결과 분석**: calc_check 및 vat_check 개선율 확인\n\n")
        
        f.write(f"## 참고 문서\n\n")
        f.write(f"- `PROJECT_WORKLOG.md`: 작업 로그\n")
        f.write(f"- `PIPELINE_STEP_VERIFICATION.md`: 단계별 검증 보고서\n")
        f.write(f"- `OFCO_COMPREHENSIVE_ANALYSIS.md`: 종합 분석 문서\n")
    
    print(f"[OK] 보고서 생성 완료: {report_path}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='OFCO 파이프라인 전체 패치 적용 스크립트 v1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 전체 패치 적용 (calc + VAT)
  python apply_all_patches.py --invoice OFCO-INV-0001178 --mode full
  
  # calc_check만 수정
  python apply_all_patches.py --invoice OFCO-INV-0001178 --mode calc-only
  
  # VAT 검증만 강화 + 자동 재계산
  python apply_all_patches.py --invoice OFCO-INV-0001178 --mode vat-only --recalculate-vat
  
  # 커스텀 허용 범위
  python apply_all_patches.py --invoice OFCO-INV-0001178 --tolerance-calc 0.05 --tolerance-vat 0.05
        """
    )
    
    parser.add_argument('--invoice', type=str, required=True,
                        help='Invoice 번호 (예: OFCO-INV-0001178)')
    parser.add_argument('--mode', type=str, default='full',
                        choices=['full', 'calc-only', 'vat-only'],
                        help='패치 모드 (기본값: full)')
    parser.add_argument('--tolerance-calc', type=float, default=0.01,
                        help='calc_check 금액 오차 허용 (기본값: 0.01 AED)')
    parser.add_argument('--tolerance-vat', type=float, default=0.02,
                        help='VAT 오차 허용 비율 (기본값: 0.02 = 2%%)')
    parser.add_argument('--recalculate-vat', action='store_true', default=False,
                        help='VAT 자동 재계산 활성화')
    parser.add_argument('--backup', action='store_true', default=True,
                        help='백업 생성 (기본값: True)')
    parser.add_argument('--no-backup', action='store_false', dest='backup',
                        help='백업 생성 안 함')
    
    args = parser.parse_args()
    
    print("="*80)
    print("OFCO 파이프라인 전체 패치 적용")
    print("="*80)
    print(f"Invoice: {args.invoice}")
    print(f"패치 모드: {args.mode}")
    print(f"백업 생성: {'예' if args.backup else '아니오'}")
    print()
    
    success = True
    
    # Step 08 실행 (calc-only 또는 full)
    if args.mode in ['full', 'calc-only']:
        if not run_step08(args.invoice, tolerance=args.tolerance_calc, backup=args.backup):
            success = False
    
    # Step 09 실행 (vat-only 또는 full)
    if success and args.mode in ['full', 'vat-only']:
        if not run_step09(
            args.invoice,
            tolerance=args.tolerance_vat,
            recalculate=args.recalculate_vat,
            backup=args.backup
        ):
            success = False
    
    # 검증 보고서 생성
    if success:
        generate_validation_report(args.invoice)
    
    # 최종 결과
    print(f"\n{'='*80}")
    if success:
        print(f"[SUCCESS] 모든 패치 적용 완료!")
        print(f"{'='*80}")
        print(f"\n다음 단계:")
        print(f"1. Step 07 재실행으로 OFCO INVOICE.xlsx 통합")
        print(f"2. 검증 실행으로 개선율 확인")
        print(f"3. 보고서 검토")
        sys.exit(0)
    else:
        print(f"[FAILURE] 패치 적용 중 오류 발생")
        print(f"{'='*80}")
        print(f"\n백업 파일을 확인하고 수동으로 복구하세요.")
        sys.exit(1)


if __name__ == '__main__':
    main()
