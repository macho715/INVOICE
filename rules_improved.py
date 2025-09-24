"""
Invoice Audit System - Enhanced Business Rules

HVDC Project 송장 감사 시스템의 비즈니스 규칙 엔진 모듈입니다.
Samsung C&T Logistics & ADNOC·DSV Partnership를 위한 FX 환율 및 밴드 규칙을 관리합니다.

Author: MACHO-GPT v3.4-mini
Version: 1.0.0
Created: 2025-01-27
"""

from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class CostGuardBand(Enum):
    """비용 가드 밴드 열거형"""
    GREEN = "GREEN"      # 0-3%: 정상 범위
    YELLOW = "YELLOW"    # 3-7%: 주의 범위
    ORANGE = "ORANGE"    # 7-12%: 경고 범위
    RED = "RED"          # 12-15%: 위험 범위
    CRITICAL = "CRITICAL" # 15%+: 치명적 범위


@dataclass
class FXRate:
    """FX 환율 정보 데이터 클래스"""
    from_currency: str
    to_currency: str
    rate: float
    tolerance: float = 0.03


@dataclass
class ToleranceRule:
    """허용 오차 규칙 데이터 클래스"""
    layer1_tolerance: float = 0.03  # 3% 허용 오차
    autofail_threshold: float = 0.15  # 15% 자동 실패 임계값
    warning_threshold: float = 0.07  # 7% 경고 임계값


# 고정 FX 환율 (USD 기준)
FIXED_FX: Dict[str, float] = {
    "USD_AED": 3.6725,  # USD to AED
    "USD_EUR": 0.85,    # USD to EUR (예시)
    "USD_GBP": 0.73,    # USD to GBP (예시)
}

# 허용 오차 규칙
LAYER1_TOL: float = 0.03  # 3% 허용 오차
AUTOFAIL: float = 0.15    # 15% 자동 실패 임계값
WARNING_THRESHOLD: float = 0.07  # 7% 경고 임계값

# 비용 가드 밴드 임계값
CG_BAND_THRESHOLDS = {
    CostGuardBand.GREEN: 0.03,      # 0-3%
    CostGuardBand.YELLOW: 0.07,     # 3-7%
    CostGuardBand.ORANGE: 0.12,     # 7-12%
    CostGuardBand.RED: 0.15,        # 12-15%
    CostGuardBand.CRITICAL: float('inf')  # 15%+
}


def cg_band(delta_abs: float) -> str:
    """
    비용 가드 밴드 계산
    
    절대 오차율을 기반으로 비용 가드 밴드를 결정합니다.
    
    Args:
        delta_abs: 절대 오차율 (0.0 ~ 1.0)
        
    Returns:
        비용 가드 밴드 문자열
        
    Examples:
        >>> cg_band(0.02)
        "GREEN"
        >>> cg_band(0.05)
        "YELLOW"
        >>> cg_band(0.10)
        "ORANGE"
        >>> cg_band(0.20)
        "CRITICAL"
    """
    if not isinstance(delta_abs, (int, float)):
        return CostGuardBand.CRITICAL.value
    
    if delta_abs < 0:
        delta_abs = abs(delta_abs)
    
    for band, threshold in CG_BAND_THRESHOLDS.items():
        if delta_abs <= threshold:
            return band.value
    
    return CostGuardBand.CRITICAL.value


def calculate_delta_percentage(actual_rate: float, reference_rate: float) -> float:
    """
    오차율 계산
    
    실제 요금과 참조 요금 간의 오차율을 계산합니다.
    
    Args:
        actual_rate: 실제 요금
        reference_rate: 참조 요금
        
    Returns:
        오차율 (0.0 = 0%, 0.1 = 10%)
        
    Raises:
        ValueError: 참조 요금이 0이거나 음수일 때
        
    Examples:
        >>> calculate_delta_percentage(100, 100)
        0.0
        >>> calculate_delta_percentage(110, 100)
        0.1
        >>> calculate_delta_percentage(90, 100)
        -0.1
    """
    if reference_rate <= 0:
        raise ValueError("참조 요금은 0보다 커야 합니다")
    
    return (actual_rate - reference_rate) / reference_rate


def is_within_tolerance(delta_abs: float, tolerance: float = LAYER1_TOL) -> bool:
    """
    허용 오차 범위 내 여부 확인
    
    Args:
        delta_abs: 절대 오차율
        tolerance: 허용 오차율 (기본값: 3%)
        
    Returns:
        허용 오차 범위 내 여부
        
    Examples:
        >>> is_within_tolerance(0.02)
        True
        >>> is_within_tolerance(0.05)
        False
    """
    return delta_abs <= tolerance


def is_autofail(delta_abs: float, threshold: float = AUTOFAIL) -> bool:
    """
    자동 실패 여부 확인
    
    Args:
        delta_abs: 절대 오차율
        threshold: 자동 실패 임계값 (기본값: 15%)
        
    Returns:
        자동 실패 여부
        
    Examples:
        >>> is_autofail(0.10)
        False
        >>> is_autofail(0.20)
        True
    """
    return delta_abs > threshold


def is_warning(delta_abs: float, threshold: float = WARNING_THRESHOLD) -> bool:
    """
    경고 여부 확인
    
    Args:
        delta_abs: 절대 오차율
        threshold: 경고 임계값 (기본값: 7%)
        
    Returns:
        경고 여부
        
    Examples:
        >>> is_warning(0.05)
        False
        >>> is_warning(0.10)
        True
    """
    return delta_abs > threshold


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """
    통화 변환
    
    Args:
        amount: 변환할 금액
        from_currency: 원본 통화
        to_currency: 대상 통화
        
    Returns:
        변환된 금액
        
    Raises:
        ValueError: 지원하지 않는 통화일 때
        
    Examples:
        >>> convert_currency(100, "USD", "AED")
        367.25
        >>> convert_currency(367.25, "AED", "USD")
        100.0
    """
    if from_currency == to_currency:
        return amount
    
    # USD를 기준으로 변환
    if from_currency == "USD":
        if to_currency == "AED":
            return amount * FIXED_FX["USD_AED"]
        else:
            raise ValueError(f"지원하지 않는 통화: {to_currency}")
    
    elif from_currency == "AED":
        if to_currency == "USD":
            return amount / FIXED_FX["USD_AED"]
        else:
            raise ValueError(f"지원하지 않는 통화: {to_currency}")
    
    else:
        raise ValueError(f"지원하지 않는 통화: {from_currency}")


def validate_rate_range(rate: float, min_rate: Optional[float] = None, max_rate: Optional[float] = None) -> bool:
    """
    요금 범위 검증
    
    Args:
        rate: 검증할 요금
        min_rate: 최소 요금 (선택사항)
        max_rate: 최대 요금 (선택사항)
        
    Returns:
        유효한 요금 범위인지 여부
        
    Examples:
        >>> validate_rate_range(100, min_rate=50, max_rate=200)
        True
        >>> validate_rate_range(30, min_rate=50, max_rate=200)
        False
    """
    if min_rate is not None and rate < min_rate:
        return False
    
    if max_rate is not None and rate > max_rate:
        return False
    
    return True


def get_fx_rate(from_currency: str, to_currency: str) -> float:
    """
    FX 환율 조회
    
    Args:
        from_currency: 원본 통화
        to_currency: 대상 통화
        
    Returns:
        FX 환율
        
    Raises:
        ValueError: 지원하지 않는 통화 쌍일 때
    """
    if from_currency == to_currency:
        return 1.0
    
    key = f"{from_currency}_{to_currency}"
    if key in FIXED_FX:
        return FIXED_FX[key]
    
    # 역방향 환율 계산
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in FIXED_FX:
        return 1.0 / FIXED_FX[reverse_key]
    
    raise ValueError(f"지원하지 않는 통화 쌍: {from_currency} -> {to_currency}")


def calculate_audit_status(actual_rate: float, reference_rate: float) -> Tuple[str, str]:
    """
    감사 상태 및 플래그 계산
    
    Args:
        actual_rate: 실제 요금
        reference_rate: 참조 요금
        
    Returns:
        (상태, 플래그) 튜플
        
    Examples:
        >>> calculate_audit_status(100, 100)
        ("Verified", "OK")
        >>> calculate_audit_status(110, 100)
        ("Pending Review", "WARN")
        >>> calculate_audit_status(120, 100)
        ("COST_GUARD_FAIL", "CRITICAL")
    """
    try:
        delta = calculate_delta_percentage(actual_rate, reference_rate)
        delta_abs = abs(delta)
        
        if is_within_tolerance(delta_abs):
            return "Verified", "OK"
        elif is_autofail(delta_abs):
            return "COST_GUARD_FAIL", "CRITICAL"
        elif is_warning(delta_abs):
            return "Pending Review", "WARN"
        else:
            return "Pending Review", "PENDING_REVIEW"
            
    except ValueError:
        return "REFERENCE_MISSING", "PENDING_REVIEW"


def get_tolerance_rule() -> ToleranceRule:
    """
    허용 오차 규칙 반환
    
    Returns:
        허용 오차 규칙 객체
    """
    return ToleranceRule(
        layer1_tolerance=LAYER1_TOL,
        autofail_threshold=AUTOFAIL,
        warning_threshold=WARNING_THRESHOLD
    )


def update_tolerance_rule(layer1_tolerance: Optional[float] = None, 
                         autofail_threshold: Optional[float] = None,
                         warning_threshold: Optional[float] = None) -> None:
    """
    허용 오차 규칙 업데이트
    
    Args:
        layer1_tolerance: 1단계 허용 오차 (선택사항)
        autofail_threshold: 자동 실패 임계값 (선택사항)
        warning_threshold: 경고 임계값 (선택사항)
    """
    global LAYER1_TOL, AUTOFAIL, WARNING_THRESHOLD
    
    if layer1_tolerance is not None:
        LAYER1_TOL = layer1_tolerance
    
    if autofail_threshold is not None:
        AUTOFAIL = autofail_threshold
    
    if warning_threshold is not None:
        WARNING_THRESHOLD = warning_threshold


def get_supported_currencies() -> list:
    """
    지원되는 통화 목록 반환
    
    Returns:
        지원되는 통화 리스트
    """
    currencies = set()
    for fx_key in FIXED_FX.keys():
        from_curr, to_curr = fx_key.split("_")
        currencies.add(from_curr)
        currencies.add(to_curr)
    return sorted(list(currencies))


def add_fx_rate(from_currency: str, to_currency: str, rate: float) -> None:
    """
    FX 환율 추가
    
    Args:
        from_currency: 원본 통화
        to_currency: 대상 통화
        rate: 환율
        
    Raises:
        ValueError: 환율이 0 이하일 때
    """
    if rate <= 0:
        raise ValueError("환율은 0보다 커야 합니다")
    
    key = f"{from_currency}_{to_currency}"
    FIXED_FX[key] = rate


def remove_fx_rate(from_currency: str, to_currency: str) -> None:
    """
    FX 환율 제거
    
    Args:
        from_currency: 원본 통화
        to_currency: 대상 통화
    """
    key = f"{from_currency}_{to_currency}"
    FIXED_FX.pop(key, None)


def get_cost_guard_band_info() -> Dict[str, float]:
    """
    비용 가드 밴드 정보 반환
    
    Returns:
        밴드별 임계값 딕셔너리
    """
    return {
        band.value: threshold 
        for band, threshold in CG_BAND_THRESHOLDS.items()
        if threshold != float('inf')
    }
