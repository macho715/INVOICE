#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
검증 스크립트 공통 유틸리티 함수
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict


def print_section(title: str, char="="):
    """섹션 제목 출력"""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")


def find_case_col(df: pd.DataFrame) -> Optional[str]:
    """데이터프레임에서 Case No 컬럼 찾기"""
    case_patterns = ["caseno", "case no", "case number"]
    
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(p in col_str for p in case_patterns):
            return col
        # "no" 또는 "no."만 있는 경우도 체크
        if col_str in ["no", "no.", "no ."]:
            return col
    return None


def normalize_case_no(case_value: Any) -> str:
    """Case No 값을 정규화 (대문자, 공백 제거)"""
    if pd.isna(case_value):
        return ""
    return str(case_value).strip().upper()


def load_data_file(file_path: Path, sheet_name: Optional[str] = None, header: Optional[int] = None) -> Optional[pd.DataFrame]:
    """데이터 파일 안전하게 로드"""
    try:
        if not file_path.exists():
            return None
        if sheet_name:
            return pd.read_excel(file_path, sheet_name=sheet_name, header=header)
        else:
            return pd.read_excel(file_path, header=header)
    except Exception as e:
        print(f"[ERROR] 파일 로드 실패 {file_path}: {e}")
        return None


def get_common_cases(df1: pd.DataFrame, df2: pd.DataFrame, case_col1: Optional[str] = None, case_col2: Optional[str] = None) -> Dict[str, Any]:
    """두 데이터프레임 간 공통 Case No 찾기"""
    if case_col1 is None:
        case_col1 = find_case_col(df1)
    if case_col2 is None:
        case_col2 = find_case_col(df2)
    
    if case_col1 is None or case_col2 is None:
        return {
            'common_cases': set(),
            'df1_only': set(),
            'df2_only': set(),
            'case_col1': case_col1,
            'case_col2': case_col2
        }
    
    cases1 = set(
        df1[case_col1].dropna().apply(normalize_case_no).values
    )
    cases2 = set(
        df2[case_col2].dropna().apply(normalize_case_no).values
    )
    
    return {
        'common_cases': cases1 & cases2,
        'df1_only': cases1 - cases2,
        'df2_only': cases2 - cases1,
        'case_col1': case_col1,
        'case_col2': case_col2
    }


def format_number(value: Any, precision: int = 0) -> str:
    """숫자를 포맷팅하여 출력"""
    try:
        if pd.isna(value):
            return "N/A"
        num = float(value)
        if precision == 0:
            return f"{int(num):,}"
        return f"{num:,.{precision}f}"
    except:
        return str(value)


def save_results_json(results: Dict[str, Any], file_path: Path):
    """결과를 JSON 파일로 저장"""
    import json
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # JSON 직렬화 불가능한 객체 제거
    json_results = {}
    for key, value in results.items():
        if value is None:
            continue
        if isinstance(value, dict):
            json_results[key] = {
                k: v for k, v in value.items()
                if not isinstance(v, (pd.DataFrame, defaultdict))
            }
            # defaultdict는 dict로 변환
            if isinstance(value, defaultdict):
                json_results[key] = dict(value)
        elif isinstance(value, (list, str, int, float, bool)):
            json_results[key] = value
        elif isinstance(value, set):
            json_results[key] = list(value)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"[OK] 결과 저장: {file_path}")

