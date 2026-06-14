#!/usr/bin/env python3
"""
OFCO Invoice EA Slot Algorithm v1.3
====================================

EA 슬롯 분해·검증 알고리즘 최종판 (OFCO INVOICE 전용)

Features:
- Decimal 기반 정확한 금액 계산
- 우선순위 기반 항목 정렬
- 4개 초과 시 라인 자동 분할
- calc_check, vat_check, total_check 검증
- 플래그 시스템 및 오류 코드

Author: MACHO-GPT v3.4-mini
Date: 2025-01-XX
"""

import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Optional, Any
import re
import json

# ============================================================
# CONSTANTS
# ============================================================

TOL = Decimal("0.01")  # 허용 오차
MAX_EA_SLOTS = 4
Q = lambda x: Decimal(str(x)).quantize(Decimal("0.01"), ROUND_HALF_UP) if x is not None else None

# 우선순위 테이블 (17단계)
PRIORITY_MAP = {
    1: [r'AGENCY_FEE_FOR_CARGO_CLEARANCE'],
    2: [r'AGENCY_FEE_FOR_BERTHING_ARRANGEMENT'],
    3: [r'AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT'],
    4: [r'AGENCY_FOR_ARRANGEMENT_PTW'],
    5: [r'PORT_DUES?', r'PORT_DUE'],
    6: [r'CHANNEL', r'CROSSING', r'TRANSIT'],
    7: [r'PILOTAGE', r'PILOT_LAUNCH'],
    8: [r'WASTE_HANDLING', r'GENERAL_WASTE_SERVICE'],
    9: [r'OFCO_HANDLING_FEE'],
    10: [r'DOCUMENT_PROCESSING_CHARGE'],
    11: [r'BULK_MATERIAL'],
    12: [r'HEAVY_LIFT'],
    13: [r'GENERAL_CARGO'],
    14: [r'MANPOWER'],
    15: [r'EQUIPMENT', r'FORKLIFT'],
    16: [r'CONSUMABLES', r'DIESEL_VESSEL', r'BUNKERING', r'ANCHORAGE', r'PEC_CHANGES'],
    17: [r'OTHERS'],
}

# 기준금액 컬럼 우선순위
REF_AMOUNT_COLS = [
    'Amount_A_AED',
    'amount_excl_tax',
    'line_amount',
    'amount',
    'subtotal',
    'total_excl_tax'
]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def normalize_num(x: Any) -> Optional[Decimal]:
    """
    숫자 값 정제 (천단위 구분자 제거, Decimal 변환)

    Args:
        x: 입력 값

    Returns:
        Decimal 또는 None
    """
    if x is None or pd.isna(x):
        return None

    s = str(x).strip().replace(",", "").replace("—", "").replace("-", "").replace("N/A", "")
    if s == "" or s == "-":
        return None

    try:
        return Decimal(s)
    except:
        return None


def get_priority(name: str) -> int:
    """
    항목 이름으로 우선순위 반환

    Args:
        name: 항목 베이스 이름 (예: "AGENCY_FEE_FOR_CARGO_CLEARANCE")

    Returns:
        우선순위 (1-17, 낮을수록 높음)
    """
    name_upper = name.upper()

    for priority, patterns in PRIORITY_MAP.items():
        for pattern in patterns:
            if re.search(pattern, name_upper, re.IGNORECASE):
                return priority

    return 17  # OTHERS (기본값)


def find_reference_amount(row: pd.Series) -> Optional[Decimal]:
    """
    기준금액 컬럼 탐색 (우선순위 순)

    Args:
        row: DataFrame 행

    Returns:
        기준금액 Decimal 또는 None
    """
    # row.index 처리
    if isinstance(row, pd.Series):
        index = row.index
    elif isinstance(row, dict):
        index = row.keys()
    else:
        index = []

    for col in REF_AMOUNT_COLS:
        if col in index:
            val = normalize_num(row.get(col))
            if val is not None and val > 0:
                return val

    # 대체: *_AMOUNT 컬럼들의 합계
    amt_cols = [str(col) for col in index if str(col).endswith('_AMOUNT')]
    total = Decimal('0.00')
    for col in amt_cols:
        val = normalize_num(row.get(col))
        if val is not None:
            total += val

    return total if total > 0 else None


# ============================================================
# ITEM BUILDING
# ============================================================

def build_items(row: pd.Series, qty_cols: List[str], amt_cols: List[str]) -> List[Dict[str, Any]]:
    """
    QTY/AMOUNT 컬럼에서 아이템 구성

    Args:
        row: DataFrame 행
        qty_cols: QTY 컬럼 목록
        amt_cols: AMOUNT 컬럼 목록

    Returns:
        정렬된 아이템 리스트
    """
    # 베이스 이름 추출
    bases = set()
    for col in qty_cols + amt_cols:
        if col.endswith('_QTY'):
            bases.add(col.replace('_QTY', ''))
        elif col.endswith('_AMOUNT'):
            bases.add(col.replace('_AMOUNT', ''))

    items = []

    for base in bases:
        qty_col = f"{base}_QTY"
        amt_col = f"{base}_AMOUNT"

        q = normalize_num(row.get(qty_col)) if qty_col in row.index else None
        a = normalize_num(row.get(amt_col)) if amt_col in row.index else None

        flags = {}

        # Rule A: qty & amount 둘 다 있고 qty≠0
        if q is not None and a is not None and q != 0:
            r = Q(a / q)
        # Rule B: amount만 있음 → qty=1.00, rate=amount
        elif a is not None:
            q = Decimal("1.00")
            r = Q(a)
            flags["FLAG_QTY_ASSUMED"] = 1
        # Rule D: qty=0 & amount>0 → qty=1.00, rate=amount
        elif q is not None and q == 0 and a is not None:
            q = Decimal("1.00")
            r = Q(a)
            flags["FLAG_ZERO_QTY_FIX"] = 1
        # Rule C & E: qty만 있거나 둘 다 결측 → 스킵
        else:
            continue

        # 금액 계산
        amount = Q(a) if a is not None else Q(q * r)

        items.append({
            "name": base,
            "qty": Q(q),
            "amount": amount,
            "rate": r,
            "priority": get_priority(base),
            "flags": flags
        })

    # 정렬: priority asc, name asc, |amount| desc
    items.sort(key=lambda it: (it["priority"], it["name"], -abs(it["amount"])))

    return items


# ============================================================
# EA PACKING
# ============================================================

def pack_ea(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    아이템을 EA 슬롯에 패킹 (최대 4개)

    Args:
        items: 정렬된 아이템 리스트

    Returns:
        (slots, overflow) - EA 슬롯과 넘치는 항목
    """
    slots = []

    for it in items[:MAX_EA_SLOTS]:
        slots.append({
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": Q(it["qty"] * it["rate"]),
            "name": it["name"],
            "flags": it.get("flags", {})
        })

    overflow = items[MAX_EA_SLOTS:]  # 5개 이상 항목

    return slots, overflow


# ============================================================
# VALIDATION
# ============================================================

def validate_line(
    slots: List[Dict[str, Any]],
    ref_amount: Optional[Decimal],
    tax_rate: Optional[Decimal] = None,
    tax_amount: Optional[Decimal] = None,
    total_incl: Optional[Decimal] = None
) -> Dict[str, Any]:
    """
    라인 레벨 검증

    Args:
        slots: EA 슬롯 리스트
        ref_amount: 기준금액
        tax_rate: 세율 (퍼센트)
        tax_amount: 세금 금액
        total_incl: VAT 포함 총액

    Returns:
        검증 결과 딕셔너리
    """
    # EA 총액 계산
    ea_total = Q(sum(s["amount"] for s in slots if s))

    # calc_check
    calc_check = None
    calc_status = None
    diff_line = None

    if ref_amount is not None:
        diff_line = abs(ea_total - ref_amount)
        if diff_line == 0:
            calc_status = "EXACT"
            calc_check = True
        elif diff_line <= TOL:
            calc_status = "WITHIN_TOL"
            calc_check = True
        else:
            calc_status = "FAIL"
            calc_check = False

    # vat_check
    vat_check = None
    if tax_rate is not None and tax_amount is not None and ref_amount is not None:
        expected_vat = Q(ref_amount * Decimal(str(tax_rate)) / Decimal("100"))
        vat_check = abs(expected_vat - Q(tax_amount)) <= TOL

    # total_check
    total_check = None
    if tax_amount is not None and total_incl is not None and ref_amount is not None:
        expected_total = Q(ref_amount + Q(tax_amount))
        total_check = abs(expected_total - Q(total_incl)) <= TOL

    return {
        "ea_total": float(ea_total) if ea_total else 0.0,
        "calc_check": calc_check,
        "calc_status": calc_status,
        "diff_line": float(diff_line) if diff_line is not None else None,
        "vat_check": vat_check,
        "total_check": total_check
    }


# ============================================================
# LINE SPLITTING
# ============================================================

def split_and_reconcile(
    original_row: pd.Series,
    overflow_items: List[Dict[str, Any]],
    line_no: Any
) -> List[Dict[str, Any]]:
    """
    라인 분할 (5개 이상 항목 시)

    Args:
        original_row: 원본 행 (pd.Series 또는 dict)
        overflow_items: 넘치는 항목들 (5개 이상)
        line_no: 원본 라인 번호

    Returns:
        분할된 행 리스트 (dict 리스트)
    """
    new_rows = []

    # 원본 행을 dict로 변환
    if isinstance(original_row, pd.Series):
        original_dict = original_row.to_dict()
    else:
        original_dict = dict(original_row)

    # overflow를 새 라인으로 분할
    if len(overflow_items) > 0:
        # overflow 항목들을 그룹으로 분할 (최대 4개씩)
        for i in range(0, len(overflow_items), MAX_EA_SLOTS):
            chunk = overflow_items[i:i + MAX_EA_SLOTS]

            # 새 행 생성
            new_row = original_dict.copy()

            # line_no에 suffix 추가
            suffix = chr(ord('A') + i // MAX_EA_SLOTS)
            original_line_no = line_no

            # NaN 처리
            if pd.isna(line_no) or (isinstance(line_no, float) and pd.isna(line_no)):
                line_no_str = str(idx + 1) if 'idx' in locals() else '0'
                new_row['line_no'] = f"{line_no_str}-{suffix}"
            elif isinstance(line_no, (int, float)) and not pd.isna(line_no):
                new_row['line_no'] = f"{int(original_line_no)}-{suffix}"
            elif isinstance(line_no, str):
                new_row['line_no'] = f"{line_no}{suffix}"
            else:
                new_row['line_no'] = f"{line_no}{suffix}"

            if 'NO' in new_row:
                new_row['NO'] = f"{new_row.get('NO', line_no)}{suffix}"

            # overflow 항목들의 합계 계산
            overflow_total = sum(Q(item["amount"]) for item in chunk)

            # 새 행의 기준금액 업데이트 (overflow 합계)
            if 'Amount_A_AED' in new_row:
                new_row['Amount_A_AED'] = float(overflow_total)
            if 'Total_Amount_AED' in new_row:
                # 세금 비율로 재계산 (원본과 동일 비율 가정)
                original_total = normalize_num(original_dict.get('Total_Amount_AED'))
                original_amount = normalize_num(original_dict.get('Amount_A_AED'))
                if original_total and original_amount and original_amount > 0:
                    ratio = overflow_total / original_amount
                    tax_portion = normalize_num(original_dict.get('VAT_USD') or original_dict.get('tax_amount')) or Decimal('0')
                    new_total = overflow_total + (tax_portion * ratio)
                    new_row['Total_Amount_AED'] = float(Q(new_total))
                else:
                    new_row['Total_Amount_AED'] = float(overflow_total)

            # EA 슬롯을 overflow 항목으로 채움
            for idx, item in enumerate(chunk, 1):
                new_row[f'EA_{idx}_Qty'] = float(item["qty"])
                new_row[f'EA_{idx}_Rate'] = float(item["rate"])
                new_row[f'EA_{idx}_Amount'] = float(item["amount"])
                new_row[f'EA_{idx}_Name'] = item.get("name")

            # 나머지 EA 슬롯을 NULL로
            for idx in range(len(chunk) + 1, MAX_EA_SLOTS + 1):
                new_row[f'EA_{idx}_Qty'] = None
                new_row[f'EA_{idx}_Rate'] = None
                new_row[f'EA_{idx}_Amount'] = None
                new_row[f'EA_{idx}_Name'] = None

            # EA 총액 및 검증
            new_row['EA_Total_Amount'] = float(overflow_total)
            new_row['EA_Mapped_Count'] = len(chunk)
            new_row['EA_UNMAPPED'] = False

            # 플래그 설정
            flags = {"FLAG_SPLIT": 1}
            new_row['EA_FLAGS'] = json.dumps(flags)

            # calc_check 계산
            ref_amount = normalize_num(new_row.get('Amount_A_AED'))
            if ref_amount:
                diff = abs(overflow_total - ref_amount)
                new_row['calc_check'] = diff <= TOL
                if diff == 0:
                    new_row['calc_status'] = "EXACT"
                elif diff <= TOL:
                    new_row['calc_status'] = "WITHIN_TOL"
                else:
                    new_row['calc_status'] = "FAIL"

            new_rows.append(new_row)

    return new_rows


# ============================================================
# MAIN PROCESSING FUNCTION
# ============================================================

def process_row_to_ea_slots(row: pd.Series) -> Dict[str, Any]:
    """
    단일 행을 EA 슬롯으로 처리

    Args:
        row: DataFrame 행

    Returns:
        EA 슬롯 결과 딕셔너리
    """
    # QTY/AMOUNT 컬럼 찾기
    # row.index가 컬럼명 리스트 (pd.Series인 경우)
    if isinstance(row, pd.Series):
        index = row.index
    elif isinstance(row, dict):
        index = row.keys()
    else:
        index = []

    qty_cols = [str(col) for col in index if str(col).endswith('_QTY')]
    amt_cols = [str(col) for col in index if str(col).endswith('_AMOUNT')]

    # 아이템 구성
    items = build_items(row, qty_cols, amt_cols)

    # EA 슬롯 패킹
    slots, overflow = pack_ea(items)

    # 기준금액 찾기
    ref_amount = find_reference_amount(row)

    # 세율 및 세금 추출
    tax_rate = normalize_num(row.get('tax_rate_pct'))
    tax_amount = normalize_num(row.get('tax_amount') or row.get('VAT_USD'))
    total_incl = normalize_num(row.get('Total_Amount_AED') or row.get('total_incl_tax'))

    # 검증
    validation = validate_line(slots, ref_amount, tax_rate, tax_amount, total_incl)

    # 결과 딕셔너리 생성
    result = {}

    # EA 슬롯 채우기
    for i in range(MAX_EA_SLOTS):
        if i < len(slots):
            result[f'EA_{i+1}_Qty'] = float(slots[i]["qty"])
            result[f'EA_{i+1}_Rate'] = float(slots[i]["rate"])
            result[f'EA_{i+1}_Amount'] = float(slots[i]["amount"])
            result[f'EA_{i+1}_Name'] = slots[i]["name"]
        else:
            result[f'EA_{i+1}_Qty'] = None
            result[f'EA_{i+1}_Rate'] = None
            result[f'EA_{i+1}_Amount'] = None
            result[f'EA_{i+1}_Name'] = None

    # 총액 및 검증 결과
    result['EA_Total_Amount'] = validation["ea_total"]
    result['EA_Mapped_Count'] = len(slots)
    result['calc_check'] = validation["calc_check"]
    result['calc_status'] = validation["calc_status"]
    result['vat_check'] = validation["vat_check"]
    result['total_check'] = validation["total_check"]

    # 플래그
    all_flags = {}
    for slot in slots:
        all_flags.update(slot.get("flags", {}))
    if len(overflow) > 0:
        all_flags["FLAG_SPLIT"] = 1

    # UNMAPPED 플래그
    result['EA_UNMAPPED'] = len(slots) == 0

    # 음수 금액 체크
    if ref_amount and ref_amount < 0:
        all_flags["FLAG_NEGATIVE"] = 1

    result['EA_FLAGS'] = json.dumps(all_flags) if all_flags else None

    # overflow 정보 저장 (라인 분할 시 사용)
    result['_overflow_items'] = overflow

    return result


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 전체를 EA 슬롯 알고리즘으로 처리

    Args:
        df: 입력 DataFrame

    Returns:
        EA 슬롯이 추가된 DataFrame
    """
    print("=" * 80)
    print("[EA SLOT] EA 슬롯 알고리즘 v1.3 처리 시작...")
    print("=" * 80)
    print(f"총 행 수: {len(df)}")

    results = []
    new_rows_to_add = []

    for idx, row in df.iterrows():
        # EA 슬롯 처리
        ea_result = process_row_to_ea_slots(row)

        # 원본 행을 dict로 변환
        if isinstance(row, pd.Series):
            new_row = row.to_dict()
        else:
            new_row = dict(row)

        # EA 결과 병합
        for key, value in ea_result.items():
            if key != '_overflow_items':
                new_row[key] = value

        results.append(new_row)

        # 라인 분할 필요 시
        overflow = ea_result.get('_overflow_items', [])
        if len(overflow) > 0:
            line_no = new_row.get('line_no') or new_row.get('NO')
            if pd.isna(line_no) if isinstance(line_no, (int, float)) else (line_no is None):
                line_no = idx + 1
            split_rows = split_and_reconcile(new_row, overflow, line_no)
            new_rows_to_add.extend(split_rows)

            # 원본 행에도 플래그 추가
            flags = json.loads(ea_result.get('EA_FLAGS') or '{}')
            flags["FLAG_SPLIT"] = 1
            new_row['EA_FLAGS'] = json.dumps(flags)
            results[-1] = new_row

        if (idx + 1) % 100 == 0:
            print(f"진행: {idx + 1}/{len(df)} 행 처리됨")

    # 분할된 행 추가
    if new_rows_to_add:
        print(f"\n라인 분할: {len(new_rows_to_add)}개 새 행 추가")
        results.extend(new_rows_to_add)

    result_df = pd.DataFrame(results)

    print(f"\n[OK] 완료: {len(result_df)} 행 처리 (원본 {len(df)} + 분할 {len(new_rows_to_add)})")

    return result_df


# ============================================================
# INVOICE-LEVEL VALIDATION
# ============================================================

def validate_invoice(df: pd.DataFrame, invoice_col: str = 'INVOICE NUMBER') -> pd.DataFrame:
    """
    인보이스 레벨 검증

    Args:
        df: DataFrame
        invoice_col: 인보이스 번호 컬럼명

    Returns:
        검증 결과 DataFrame
    """
    if invoice_col not in df.columns:
        print(f"⚠️  {invoice_col} 컬럼이 없습니다.")
        return pd.DataFrame()

    validation_results = []

    invoice_groups = df.groupby(invoice_col)

    for invoice_no, group in invoice_groups:
        # 합계 계산
        sum_amount_excl = group['Amount_A_AED'].apply(
            lambda x: float(normalize_num(x) or 0)
        ).sum()

        sum_tax = group['VAT_USD'].apply(
            lambda x: float(normalize_num(x) or 0)
        ).sum() if 'VAT_USD' in group.columns else 0.0

        sum_total_incl = group['Total_Amount_AED'].apply(
            lambda x: float(normalize_num(x) or 0)
        ).sum()

        # 헤더 총액 찾기 (첫 행의 메타데이터에서)
        first_row = group.iloc[0]
        header_total = normalize_num(first_row.get('Total_Amount_AED'))

        # 검증
        diff_total = abs(sum_total_incl - float(header_total)) if header_total else None

        validation_results.append({
            'Invoice_No': invoice_no,
            'Sum_Amount_Excl': sum_amount_excl,
            'Sum_Tax': sum_tax,
            'Sum_Total_Incl': sum_total_incl,
            'Header_Total': float(header_total) if header_total else None,
            'Diff': diff_total,
            'Pass': diff_total <= float(TOL) if diff_total is not None else None,
            'Row_Count': len(group)
        })

    return pd.DataFrame(validation_results)


if __name__ == "__main__":
    # 테스트 코드
    print("EA 슬롯 알고리즘 v1.3 테스트")
    print("=" * 80)

