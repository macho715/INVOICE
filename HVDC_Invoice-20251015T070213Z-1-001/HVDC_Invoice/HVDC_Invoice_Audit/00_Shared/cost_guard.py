#!/usr/bin/env python3
"""
COST-GUARD 밴드 공용 유틸리티
Config 기반 밴드 판정 및 Auto-Fail 로직

Version: 1.0.0
Created: 2025-10-15
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def get_cost_guard_band(delta_pct: Optional[float], bands: Dict) -> str:
    """
    Delta % 기반 COST-GUARD 밴드 결정 (Config 기반)

    Args:
        delta_pct: Delta 백분율 (Draft - Ref) / Ref * 100
        bands: Config의 cost_guard_bands 딕셔너리

    Returns:
        "PASS" | "WARN" | "HIGH" | "CRITICAL" | "N/A"
    """
    if delta_pct is None:
        return "N/A"

    abs_delta = abs(delta_pct)

    # Config에서 임계값 읽기 (Fallback: 하드코딩 값)
    pass_threshold = bands.get("PASS", {}).get("max_delta", 2.0)
    warn_threshold = bands.get("WARN", {}).get("max_delta", 5.0)
    high_threshold = bands.get("HIGH", {}).get("max_delta", 10.0)

    # 밴드 판정 (순서대로)
    if abs_delta <= pass_threshold:
        return "PASS"
    elif abs_delta <= warn_threshold:
        return "WARN"
    elif abs_delta <= high_threshold:
        return "HIGH"
    else:
        return "CRITICAL"


def check_auto_fail(delta_pct: Optional[float], auto_fail_threshold: float = 15.0) -> bool:
    """
    Auto-Fail 조건 확인 (Delta > 15%)

    Args:
        delta_pct: Delta 백분율
        auto_fail_threshold: Auto-Fail 임계값 (기본 15%)

    Returns:
        True if auto-fail 조건 충족
    """
    if delta_pct is None:
        return False

    abs_delta = abs(delta_pct)
    return abs_delta > auto_fail_threshold


def get_band_color(band: str) -> str:
    """
    밴드별 색상 코드 반환 (Excel 조건부 서식용)

    Args:
        band: COST-GUARD 밴드 ("PASS" | "WARN" | "HIGH" | "CRITICAL")

    Returns:
        색상 코드 ("GREEN" | "YELLOW" | "ORANGE" | "RED")
    """
    color_map = {
        "PASS": "GREEN",
        "WARN": "YELLOW",
        "HIGH": "ORANGE",
        "CRITICAL": "RED",
        "N/A": "GRAY",
    }
    return color_map.get(band, "GRAY")


def get_band_severity(band: str) -> str:
    """
    밴드별 심각도 반환

    Args:
        band: COST-GUARD 밴드

    Returns:
        심각도 ("NONE" | "LOW" | "MEDIUM" | "HIGH")
    """
    severity_map = {
        "PASS": "NONE",
        "WARN": "LOW",
        "HIGH": "MEDIUM",
        "CRITICAL": "HIGH",
        "N/A": "UNKNOWN",
    }
    return severity_map.get(band, "UNKNOWN")

