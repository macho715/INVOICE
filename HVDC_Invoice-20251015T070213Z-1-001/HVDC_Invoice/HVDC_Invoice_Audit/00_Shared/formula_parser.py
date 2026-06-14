#!/usr/bin/env python3
"""
Formula Parser - AED/USD 수식 파싱 유틸리티
Portal Fee 및 At-Cost 항목의 수식 기반 검증 지원

Version: 1.0.0
Created: 2025-10-15
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import re
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def parse_aed_from_formula(formula_str: str, fx_rate: float = 3.6725) -> Optional[float]:
    """
    AED 수식에서 USD 값 역산
    
    Args:
        formula_str: 수식 문자열 (예: "=27/3.6725", "=35/3.67")
        fx_rate: USD/AED 환율 (기본 3.6725)
    
    Returns:
        USD 금액 (소수점 2자리), 파싱 실패 시 None
    
    Examples:
        "=27/3.6725" → 7.35 USD (Appointment Fee)
        "=35/3.6725" → 9.53 USD (DPC Fee)
        "=150/3.67" → 40.87 USD
    """
    if not formula_str or not isinstance(formula_str, str):
        return None
    
    formula_str = str(formula_str).strip()
    
    # Pattern 1: "=AED_VALUE/FX_RATE" (가장 일반적)
    # 예: "=27/3.6725", "=35/3.67"
    pattern1 = r"^\s*=\s*([0-9.]+)\s*/\s*([0-9.]+)\s*$"
    match = re.match(pattern1, formula_str)
    
    if match:
        aed_value = float(match.group(1))
        divisor = float(match.group(2))
        
        # 환율인지 확인 (3.6-3.7 range)
        if 3.6 <= divisor <= 3.8:
            usd_value = round(aed_value / divisor, 2)
            logger.info(
                f"[FORMULA] Parsed '{formula_str}' → AED {aed_value:.2f} / {divisor:.4f} = USD ${usd_value:.2f}"
            )
            return usd_value
    
    # Pattern 2: "AED VALUE / FX" (등호 없음)
    # 예: "27 / 3.6725", "AED 35 / 3.67"
    pattern2 = r"(?:AED)?\s*([0-9.]+)\s*/\s*([0-9.]+)"
    match = re.search(pattern2, formula_str, re.IGNORECASE)
    
    if match:
        aed_value = float(match.group(1))
        divisor = float(match.group(2))
        
        if 3.6 <= divisor <= 3.8:
            usd_value = round(aed_value / divisor, 2)
            logger.info(
                f"[FORMULA] Parsed '{formula_str}' → AED {aed_value:.2f} / {divisor:.4f} = USD ${usd_value:.2f}"
            )
            return usd_value
    
    # Pattern 3: 고정 AED 값만 있는 경우 (표준 환율로 변환)
    # 예: "27", "35", "AED 27"
    pattern3 = r"(?:AED)?\s*([0-9.]+)\s*$"
    match = re.match(pattern3, formula_str, re.IGNORECASE)
    
    if match:
        aed_value = float(match.group(1))
        # 일반적인 Portal Fee 범위인지 확인 (10-100 AED)
        if 10.0 <= aed_value <= 100.0:
            usd_value = round(aed_value / fx_rate, 2)
            logger.info(
                f"[FORMULA] Parsed fixed AED '{formula_str}' → AED {aed_value:.2f} / {fx_rate:.4f} = USD ${usd_value:.2f}"
            )
            return usd_value
    
    logger.debug(f"[FORMULA] Could not parse formula: '{formula_str}'")
    return None


def parse_rate_from_formula_or_fixed(
    formula_str: str, 
    description: str,
    known_rates: Optional[Dict[str, float]] = None,
    fx_rate: float = 3.6725
) -> Optional[float]:
    """
    수식 또는 고정 요율에서 USD 값 추출
    
    Args:
        formula_str: Formula 컬럼 값
        description: DESCRIPTION 컬럼 값 (고정 요율 매칭용)
        known_rates: 알려진 고정 요율 딕셔너리 {"APPOINTMENT FEE": 27.0 (AED)}
        fx_rate: USD/AED 환율
    
    Returns:
        USD 금액, 실패 시 None
    """
    # 1. 수식 파싱 시도
    usd_from_formula = parse_aed_from_formula(formula_str, fx_rate)
    if usd_from_formula:
        return usd_from_formula
    
    # 2. 알려진 고정 요율 매칭
    if known_rates and description:
        desc_upper = description.upper().strip()
        
        for key_pattern, aed_value in known_rates.items():
            if key_pattern.upper() in desc_upper:
                usd_value = round(aed_value / fx_rate, 2)
                logger.info(
                    f"[FIXED RATE] Matched '{description}' → AED {aed_value:.2f} = USD ${usd_value:.2f}"
                )
                return usd_value
    
    return None


# 알려진 Portal/At-Cost 고정 요율 (AED)
KNOWN_AED_RATES = {
    "APPOINTMENT FEE": 27.0,
    "TRUCK APPOINTMENT": 27.0,
    "DPC FEE": 35.0,
    "DOCUMENT PROCESSING": 35.0,
    "DOCS PROCESSING": 35.0,
    "PRO CUSTOMS": 35.0,
}

