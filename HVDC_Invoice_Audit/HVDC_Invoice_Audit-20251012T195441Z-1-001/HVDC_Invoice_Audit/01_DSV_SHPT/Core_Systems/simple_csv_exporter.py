#!/usr/bin/env python3
"""
단순 CSV/Excel 출력 모듈
======================

Excel 포맷팅 코드 일체 없음 (에러 방지)
순수 데이터만 출력
"""

import pandas as pd
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def export_simple_csv(df: pd.DataFrame, output_path: str) -> bool:
    """
    포맷팅 없이 순수 CSV 출력
    
    Args:
        df: 데이터프레임
        output_path: 출력 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 순수 CSV 출력 (포맷팅 없음)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")

        logger.info(f"✅ CSV exported: {output_path} ({len(df)} rows)")
        return True

    except Exception as e:
        logger.error(f"❌ CSV export failed: {e}")
        return False


def export_simple_excel(df: pd.DataFrame, output_path: str) -> bool:
    """
    포맷팅 없이 순수 Excel 출력
    
    Warning: Excel styling code is strictly prohibited
    Only basic data export using pandas to_excel()
    
    Args:
        df: 데이터프레임
        output_path: 출력 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 순수 데이터만 출력 (기본 pandas to_excel)
        df.to_excel(output_file, index=False, engine="openpyxl")

        logger.info(f"✅ Excel exported: {output_path} ({len(df)} rows)")
        return True

    except Exception as e:
        logger.error(f"❌ Excel export failed: {e}")
        return False


def export_combined_output(
    df: pd.DataFrame, output_dir: str, base_name: str = "audit_result"
) -> Dict[str, str]:
    """
    CSV + Excel 동시 출력
    
    Args:
        df: 데이터프레임
        output_dir: 출력 디렉토리
        base_name: 파일 기본 이름
        
    Returns:
        Dict[str, str]: 생성된 파일 경로들
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    # CSV 출력
    csv_file = output_path / f"{base_name}_{timestamp}.csv"
    if export_simple_csv(df, str(csv_file)):
        results["csv"] = str(csv_file)

    # Excel 출력
    excel_file = output_path / f"{base_name}_{timestamp}.xlsx"
    if export_simple_excel(df, str(excel_file)):
        results["excel"] = str(excel_file)

    logger.info(f"✅ Combined output: {len(results)} files created")

    return results

