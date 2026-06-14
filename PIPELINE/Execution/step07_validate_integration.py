#!/usr/bin/env python3
"""
OFCO INVOICE.xlsx 통합 검증 스크립트

통합된 OFCO INVOICE.xlsx 파일의 무결성을 검증합니다.

검증 항목:
1. 원본 포맷 유지 (129개 컬럼 순서)
2. SN 개수 확인 (NO 컬럼 1~46)
3. 날짜 형식 확인 (INVOICE DATE_YEAR_MONTH)
4. 삽입 위치 확인 (정렬 기준)
5. 순번 연속성 확인 (전체 순번)
6. 데이터 무결성 확인

Usage:
    python validate_integration.py [--target "OFCO INVOICE.xlsx"] [--invoice OFCO-INV-0001178]
"""

import pandas as pd
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def validate_original_format(df: pd.DataFrame, backup_file: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    원본 포맷 유지 검증 (129개 컬럼 순서)

    Args:
        df: 검증할 DataFrame
        backup_file: 백업 파일 경로 (원본 구조 참조용)

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    # 백업 파일이 있으면 원본 구조 확인
    if backup_file and backup_file.exists():
        try:
            backup_df = pd.read_excel(backup_file, sheet_name='Sheet1', nrows=0)
            original_columns = list(backup_df.columns)
            current_columns = list(df.columns)
            
            # 원본 129개 컬럼 순서 확인
            original_first_129 = original_columns[:129]
            current_first_129 = current_columns[:129]
            
            if original_first_129 != current_first_129:
                diff = [i for i, (a, b) in enumerate(zip(original_first_129, current_first_129)) if a != b]
                errors.append(f"원본 129개 컬럼 순서 불일치: {len(diff)}개 위치에서 차이")
                if diff:
                    errors.append(f"  불일치 위치: {diff[:10]}...")
            else:
                return True, ["✅ 원본 129개 컬럼 순서 일치"]
        except Exception as e:
            errors.append(f"백업 파일 읽기 실패: {e}")
    else:
        # 백업 파일이 없으면 컬럼 수만 확인
        if len(df.columns) < 129:
            errors.append(f"컬럼 수 부족: {len(df.columns)}개 (예상: 129개 이상)")
        else:
            return True, ["✅ 컬럼 수 확인: 129개 이상"]
    
    return len(errors) == 0, errors


def validate_sn_count(df: pd.DataFrame, invoice_no: str, expected_count: int = 46) -> Tuple[bool, List[str]]:
    """
    SN 개수 검증 (NO 컬럼 1~46)

    Args:
        df: 검증할 DataFrame
        invoice_no: Invoice 번호
        expected_count: 예상 SN 개수

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if 'INVOICE NUMBER' not in df.columns:
        return False, ["❌ INVOICE NUMBER 컬럼이 없습니다"]
    
    if 'NO' not in df.columns:
        return False, ["❌ NO 컬럼이 없습니다"]
    
    # Invoice 번호로 필터링
    inv_df = df[df['INVOICE NUMBER'] == invoice_no]
    inv_count = len(inv_df)
    
    if inv_count != expected_count:
        errors.append(f"❌ SN 개수 불일치: {inv_count}개 (예상: {expected_count}개)")
    else:
        # NO 값 범위 확인
        no_values = inv_df['NO'].dropna().unique()
        if len(no_values) > 0:
            no_min = int(no_values.min())
            no_max = int(no_values.max())
            expected_range = set(range(1, expected_count + 1))
            actual_range = set([int(v) for v in no_values])
            
            if expected_range != actual_range:
                missing = expected_range - actual_range
                extra = actual_range - expected_range
                if missing:
                    errors.append(f"❌ 누락된 NO: {sorted(missing)[:10]}")
                if extra:
                    errors.append(f"❌ 추가된 NO: {sorted(extra)[:10]}")
            else:
                return True, [f"✅ SN {expected_count}개 정확히 확인 (NO: {no_min}~{no_max})"]
        else:
            errors.append("❌ NO 값이 없습니다")
    
    return len(errors) == 0, errors


def validate_date_format(df: pd.DataFrame, invoice_no: str) -> Tuple[bool, List[str]]:
    """
    날짜 형식 검증 (INVOICE DATE_YEAR_MONTH)

    Args:
        df: 검증할 DataFrame
        invoice_no: Invoice 번호

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if 'INVOICE DATE_YEAR_MONTH' not in df.columns:
        return False, ["❌ INVOICE DATE_YEAR_MONTH 컬럼이 없습니다"]
    
    inv_df = df[df['INVOICE NUMBER'] == invoice_no]
    
    if len(inv_df) == 0:
        return False, [f"❌ Invoice {invoice_no} 데이터가 없습니다"]
    
    # 날짜 형식 확인 (YYYY-MM-01 형식)
    date_values = inv_df['INVOICE DATE_YEAR_MONTH'].dropna().unique()
    
    if len(date_values) == 0:
        errors.append("❌ INVOICE DATE_YEAR_MONTH 값이 없습니다")
    else:
        # NaT 확인
        nat_count = sum(1 for v in date_values if pd.isna(v))
        if nat_count > 0:
            errors.append(f"❌ NaT 값 발견: {nat_count}개")
        else:
            # 날짜 형식 확인
            date_str = str(date_values[0])
            if date_str.startswith('2025-10-01') or date_str.startswith('2025-10'):
                return True, [f"✅ 날짜 형식 확인: {date_str}"]
            else:
                errors.append(f"⚠️ 날짜 형식 예상과 다름: {date_str}")
    
    return len(errors) == 0, errors


def validate_insertion_position(df: pd.DataFrame, invoice_no: str) -> Tuple[bool, List[str]]:
    """
    삽입 위치 검증 (정렬 기준)

    Args:
        df: 검증할 DataFrame
        invoice_no: Invoice 번호

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if 'INVOICE DATE_YEAR_MONTH' not in df.columns:
        return False, ["❌ INVOICE DATE_YEAR_MONTH 컬럼이 없습니다"]
    
    inv_df = df[df['INVOICE NUMBER'] == invoice_no]
    
    if len(inv_df) == 0:
        return False, [f"❌ Invoice {invoice_no} 데이터가 없습니다"]
    
    # 날짜별 그룹 확인
    date_ym = inv_df['INVOICE DATE_YEAR_MONTH'].iloc[0] if len(inv_df) > 0 else None
    
    if pd.isna(date_ym):
        errors.append("❌ INVOICE DATE_YEAR_MONTH가 NaT입니다")
    else:
        # 같은 날짜의 데이터가 연속적으로 배치되어 있는지 확인
        date_mask = df['INVOICE DATE_YEAR_MONTH'] == date_ym
        date_indices = df[date_mask].index.tolist()
        inv_indices = inv_df.index.tolist()
        
        if set(inv_indices).issubset(set(date_indices)):
            return True, [f"✅ 삽입 위치 확인: {date_ym} 그룹 내 (행 {inv_indices[0]+1}~{inv_indices[-1]+1})"]
        else:
            errors.append(f"⚠️ 삽입 위치가 예상과 다름")
    
    return len(errors) == 0, errors


def validate_sequence_numbers(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    순번 연속성 검증 (전체 순번)

    Args:
        df: 검증할 DataFrame

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if '전체 순번' not in df.columns:
        return False, ["❌ 전체 순번 컬럼이 없습니다"]
    
    seq_values = df['전체 순번'].dropna().unique()
    expected_seq = set(range(1, len(df) + 1))
    actual_seq = set([int(v) for v in seq_values])
    
    if expected_seq != actual_seq:
        missing = expected_seq - actual_seq
        extra = actual_seq - expected_seq
        if missing:
            errors.append(f"❌ 누락된 순번: {sorted(missing)[:10]}...")
        if extra:
            errors.append(f"❌ 추가된 순번: {sorted(extra)[:10]}...")
    elif len(seq_values) != len(df):
        errors.append(f"❌ 순번 개수 불일치: {len(seq_values)}개 (예상: {len(df)}개)")
    else:
        return True, [f"✅ 전체 순번 연속 확인: 1 ~ {len(df)}"]
    
    return len(errors) == 0, errors


def validate_data_integrity(df: pd.DataFrame, invoice_no: str) -> Tuple[bool, List[str]]:
    """
    데이터 무결성 검증

    Args:
        df: 검증할 DataFrame
        invoice_no: Invoice 번호

    Returns:
        (성공 여부, 오류 메시지 리스트)
    """
    errors = []
    
    if 'INVOICE NUMBER' not in df.columns:
        return False, ["❌ INVOICE NUMBER 컬럼이 없습니다"]
    
    inv_df = df[df['INVOICE NUMBER'] == invoice_no]
    
    if len(inv_df) == 0:
        return False, [f"❌ Invoice {invoice_no} 데이터가 없습니다"]
    
    # 필수 컬럼 확인
    required_cols = ['INVOICE NUMBER', 'SUBJECT', 'PRICE CENTER']
    for col in required_cols:
        if col not in inv_df.columns:
            errors.append(f"❌ 필수 컬럼 누락: {col}")
        else:
            missing = inv_df[col].isna().sum()
            if missing > 0:
                errors.append(f"⚠️ {col} 누락: {missing}행")
    
    # Invoice Number 일치 확인
    mismatched = inv_df[inv_df['INVOICE NUMBER'] != invoice_no]
    if len(mismatched) > 0:
        errors.append(f"❌ Invoice Number 불일치: {len(mismatched)}행")
    
    return len(errors) == 0, errors


def validate_all(
    target_file: str,
    invoice_no: str = 'OFCO-INV-0001178',
    expected_sn_count: int = 46,
    backup_file: Optional[str] = None
) -> Dict[str, Tuple[bool, List[str]]]:
    """
    전체 검증 실행

    Args:
        target_file: 검증할 파일 경로
        invoice_no: Invoice 번호
        expected_sn_count: 예상 SN 개수
        backup_file: 백업 파일 경로 (원본 구조 참조용)

    Returns:
        검증 결과 딕셔너리
    """
    print("=" * 80)
    print("OFCO INVOICE.xlsx 통합 검증")
    print("=" * 80)
    print()
    
    target_path = Path(target_file)
    if not target_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {target_file}")
        return {}
    
    print(f"[INFO] 검증 대상: {target_file}")
    print(f"[INFO] Invoice: {invoice_no}")
    print(f"[INFO] 예상 SN 개수: {expected_sn_count}")
    print()
    
    # 파일 읽기
    try:
        df = pd.read_excel(target_path, sheet_name='Sheet1')
        print(f"[OK] 파일 로드 완료: {len(df)}행, {len(df.columns)}컬럼")
    except Exception as e:
        print(f"[ERROR] 파일 읽기 실패: {e}")
        return {}
    
    print()
    
    # 검증 실행
    results = {}
    
    backup_path = Path(backup_file) if backup_file else target_path.with_suffix('.xlsx.backup')
    
    print("[1/6] 원본 포맷 검증...")
    results['original_format'] = validate_original_format(df, backup_path if backup_path.exists() else None)
    print_results(results['original_format'])
    
    print("\n[2/6] SN 개수 검증...")
    results['sn_count'] = validate_sn_count(df, invoice_no, expected_sn_count)
    print_results(results['sn_count'])
    
    print("\n[3/6] 날짜 형식 검증...")
    results['date_format'] = validate_date_format(df, invoice_no)
    print_results(results['date_format'])
    
    print("\n[4/6] 삽입 위치 검증...")
    results['insertion_position'] = validate_insertion_position(df, invoice_no)
    print_results(results['insertion_position'])
    
    print("\n[5/6] 순번 연속성 검증...")
    results['sequence_numbers'] = validate_sequence_numbers(df)
    print_results(results['sequence_numbers'])
    
    print("\n[6/6] 데이터 무결성 검증...")
    results['data_integrity'] = validate_data_integrity(df, invoice_no)
    print_results(results['data_integrity'])
    
    # 최종 결과
    print()
    print("=" * 80)
    all_passed = all(success for success, _ in results.values())
    if all_passed:
        print("[SUCCESS] 모든 검증 통과")
    else:
        failed_count = sum(1 for success, _ in results.values() if not success)
        print(f"[WARNING] {failed_count}/{len(results)} 검증 실패")
    print("=" * 80)
    
    return results


def print_results(result: Tuple[bool, List[str]]):
    """검증 결과 출력"""
    success, messages = result
    for msg in messages:
        print(f"  {msg}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='OFCO INVOICE.xlsx 통합 검증',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--target', type=str, default='OFCO INVOICE.xlsx',
                        help='검증 대상 파일 경로 (기본값: OFCO INVOICE.xlsx)')
    parser.add_argument('--invoice', type=str, default='OFCO-INV-0001178',
                        help='Invoice 번호 (기본값: OFCO-INV-0001178)')
    parser.add_argument('--sn-count', type=int, default=46,
                        help='예상 SN 개수 (기본값: 46)')
    parser.add_argument('--backup', type=str, default=None,
                        help='백업 파일 경로 (원본 구조 참조용)')
    
    args = parser.parse_args()
    
    results = validate_all(
        target_file=args.target,
        invoice_no=args.invoice,
        expected_sn_count=args.sn_count,
        backup_file=args.backup
    )
    
    # 종료 코드
    all_passed = all(success for success, _ in results.values()) if results else False
    exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()

