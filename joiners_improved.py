"""
Invoice Audit System - Enhanced Data Joiners

HVDC Project 송장 감사 시스템의 데이터 정규화 및 조인 로직 모듈입니다.
Samsung C&T Logistics & ADNOC·DSV Partnership를 위한 데이터 표준화를 수행합니다.

Author: MACHO-GPT v3.4-mini
Version: 1.0.0
Created: 2025-01-27
"""

import re
from typing import Dict, Optional, Tuple


# 목적지 정규화 매핑 테이블
CANON_DEST: Dict[str, str] = {
    # MIRFA SITE 관련 정규화
    "MIRFA SITE": "MIRFA SITE",
    "MIRFA": "MIRFA SITE",
    "MIRFA SITE, UAE": "MIRFA SITE",
    "MIRFA SITE, UAE.": "MIRFA SITE",
    
    # SHUWEIHAT Site 관련 정규화
    "SHUWEIHAT Site": "SHUWEIHAT Site",
    "SHUWEIHAT": "SHUWEIHAT Site",
    "SHUWEIHAT SITE": "SHUWEIHAT Site",
    "SHUWEIHAT Site, UAE": "SHUWEIHAT Site",
    
    # Storage Yard 관련 정규화
    "Storage Yard": "Storage Yard",
    "STORAGE YARD": "Storage Yard",
    "Storage": "Storage Yard",
    
    # Hamariya free zone 관련 정규화
    "Hamariya free zone, Sharjah": "Hamariya free zone, Sharjah",
    "Hamariya free zone": "Hamariya free zone, Sharjah",
    "Hamariya": "Hamariya free zone, Sharjah",
    "Sharjah": "Hamariya free zone, Sharjah",
    
    # 기타 정규화
    "Dubai": "Dubai",
    "Abu Dhabi": "Abu Dhabi",
    "UAE": "UAE",
}


def canon_dest(destination: str) -> str:
    """
    목적지 문자열 정규화
    
    입력된 목적지 문자열을 표준화된 형태로 변환합니다.
    공백 정규화 및 매핑 테이블을 통한 표준화를 수행합니다.
    
    Args:
        destination: 정규화할 목적지 문자열
        
    Returns:
        정규화된 목적지 문자열
        
    Examples:
        >>> canon_dest("MIRFA SITE")
        "MIRFA SITE"
        >>> canon_dest("  mirfa  ")
        "mirfa"
        >>> canon_dest("")
        ""
        >>> canon_dest(None)
        ""
    """
    if not destination:
        return ""
    
    # 공백 정규화: 여러 공백을 하나로 변환하고 앞뒤 공백 제거
    normalized = re.sub(r"\s+", " ", destination).strip()
    
    # 매핑 테이블에서 정규화된 형태 찾기
    return CANON_DEST.get(normalized, normalized)


def unit_key(unit: str) -> str:
    """
    단위 문자열 정규화
    
    입력된 단위 문자열을 표준화된 형태로 변환합니다.
    대소문자 정규화 및 표준 단위 매핑을 수행합니다.
    
    Args:
        unit: 정규화할 단위 문자열
        
    Returns:
        정규화된 단위 문자열
        
    Examples:
        >>> unit_key("per RT")
        "per RT"
        >>> unit_key("PER rt")
        "per RT"
        >>> unit_key("per truck")
        "per truck"
        >>> unit_key("")
        ""
        >>> unit_key(None)
        ""
    """
    if not unit:
        return ""
    
    # 소문자로 변환하고 앞뒤 공백 제거
    normalized = (unit or "").strip().lower()
    
    # 표준 단위 매핑
    unit_mapping = {
        "per rt": "per RT",
        "per truck": "per truck",
        "per kg": "per KG",
        "per b/l": "per B/L",
        "per container": "per container",
        "per hour": "per hour",
        "per axle": "per axle",
    }
    
    return unit_mapping.get(normalized, normalized)


def port_hint(port: str, destination: str, unit: str) -> Optional[str]:
    """
    포트 힌트 생성
    
    목적지와 단위 정보를 기반으로 포트 힌트를 생성합니다.
    특정 목적지에 대한 포트 매핑을 제공합니다.
    
    Args:
        port: 원본 포트 문자열
        destination: 정규화된 목적지
        unit: 정규화된 단위
        
    Returns:
        포트 힌트 문자열 또는 None
        
    Examples:
        >>> port_hint("Dubai Airport", "MIRFA SITE", "per truck")
        "Dubai Airport"
        >>> port_hint("", "MIRFA SITE", "per truck")
        "Dubai Airport"
        >>> port_hint("Jebel Ali Port", "SHUWEIHAT Site", "per RT")
        "Jebel Ali Port"
    """
    if not port and not destination:
        return None
    
    # 포트가 이미 있으면 그대로 반환
    if port and port.strip():
        return port.strip()
    
    # 목적지 기반 포트 힌트 생성
    destination_port_mapping = {
        "MIRFA SITE": "Dubai Airport",
        "SHUWEIHAT Site": "Jebel Ali Port", 
        "Storage Yard": "Jebel Ali Port",
        "Hamariya free zone, Sharjah": "Jebel Ali Port",
    }
    
    return destination_port_mapping.get(destination)


def validate_cargo_type(cargo_type: str) -> bool:
    """
    화물 유형 검증
    
    입력된 화물 유형이 유효한지 검증합니다.
    
    Args:
        cargo_type: 검증할 화물 유형
        
    Returns:
        유효한 화물 유형인지 여부
        
    Examples:
        >>> validate_cargo_type("Air")
        True
        >>> validate_cargo_type("Bulk")
        True
        >>> validate_cargo_type("Container")
        True
        >>> validate_cargo_type("Invalid")
        False
    """
    if not cargo_type:
        return False
    
    valid_cargo_types = {"Air", "Bulk", "Container", "LCL", "FCL"}
    return cargo_type.strip() in valid_cargo_types


def validate_port(port: str) -> bool:
    """
    포트 검증
    
    입력된 포트가 유효한지 검증합니다.
    
    Args:
        port: 검증할 포트
        
    Returns:
        유효한 포트인지 여부
        
    Examples:
        >>> validate_port("Dubai Airport")
        True
        >>> validate_port("Jebel Ali Port")
        True
        >>> validate_port("Invalid Port")
        False
    """
    if not port:
        return False
    
    valid_ports = {
        "Dubai Airport",
        "Abu Dhabi Airport", 
        "Jebel Ali Port",
        "Mina Zayed Port",
        "Musaffah Port",
        "Khalifa Port"
    }
    
    return port.strip() in valid_ports


def create_join_key(cargo_type: str, port: str, destination: str, unit: str) -> Tuple[str, str, str, str]:
    """
    조인 키 생성
    
    화물 유형, 포트, 목적지, 단위를 조합하여 조인 키를 생성합니다.
    
    Args:
        cargo_type: 화물 유형
        port: 포트
        destination: 목적지
        unit: 단위
        
    Returns:
        정규화된 조인 키 튜플 (cargo_type, port, destination, unit)
        
    Examples:
        >>> create_join_key("Air", "Dubai Airport", "MIRFA SITE", "per truck")
        ("Air", "Dubai Airport", "MIRFA SITE", "per truck")
    """
    normalized_cargo_type = (cargo_type or "").strip()
    normalized_port = (port or "").strip()
    normalized_destination = canon_dest(destination)
    normalized_unit = unit_key(unit)
    
    return (normalized_cargo_type, normalized_port, normalized_destination, normalized_unit)


def normalize_invoice_data(invoice_data: Dict[str, str]) -> Dict[str, str]:
    """
    송장 데이터 정규화
    
    송장 데이터의 모든 필드를 정규화합니다.
    
    Args:
        invoice_data: 정규화할 송장 데이터 딕셔너리
        
    Returns:
        정규화된 송장 데이터 딕셔너리
    """
    normalized = {}
    
    # 기본 필드 정규화
    normalized["CargoType"] = (invoice_data.get("CargoType") or "").strip()
    normalized["Port"] = (invoice_data.get("Port") or "").strip()
    normalized["Destination"] = canon_dest(invoice_data.get("Destination") or "")
    normalized["Unit"] = unit_key(invoice_data.get("Unit") or "")
    
    # 기타 필드 정규화
    for key, value in invoice_data.items():
        if key not in normalized:
            normalized[key] = (value or "").strip()
    
    return normalized


def validate_join_key(join_key: Tuple[str, str, str, str]) -> bool:
    """
    조인 키 검증
    
    생성된 조인 키가 유효한지 검증합니다.
    
    Args:
        join_key: 검증할 조인 키 튜플
        
    Returns:
        유효한 조인 키인지 여부
    """
    if len(join_key) != 4:
        return False
    
    cargo_type, port, destination, unit = join_key
    
    return (
        validate_cargo_type(cargo_type) and
        validate_port(port) and
        bool(destination) and
        bool(unit)
    )


# 모듈 레벨 상수
SUPPORTED_CARGO_TYPES = {"Air", "Bulk", "Container", "LCL", "FCL"}
SUPPORTED_PORTS = {
    "Dubai Airport",
    "Abu Dhabi Airport",
    "Jebel Ali Port", 
    "Mina Zayed Port",
    "Musaffah Port",
    "Khalifa Port"
}
SUPPORTED_UNITS = {
    "per RT", "per truck", "per KG", "per B/L", 
    "per container", "per hour", "per axle"
}


def get_supported_cargo_types() -> set:
    """
    지원되는 화물 유형 목록 반환
    
    Returns:
        지원되는 화물 유형 집합
    """
    return SUPPORTED_CARGO_TYPES.copy()


def get_supported_ports() -> set:
    """
    지원되는 포트 목록 반환
    
    Returns:
        지원되는 포트 집합
    """
    return SUPPORTED_PORTS.copy()


def get_supported_units() -> set:
    """
    지원되는 단위 목록 반환
    
    Returns:
        지원되는 단위 집합
    """
    return SUPPORTED_UNITS.copy()


def get_canonical_destinations() -> Dict[str, str]:
    """
    정규화된 목적지 매핑 반환
    
    Returns:
        목적지 정규화 매핑 딕셔너리
    """
    return CANON_DEST.copy()
