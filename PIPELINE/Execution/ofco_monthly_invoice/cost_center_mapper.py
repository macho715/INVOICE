"""
OFCO 인보이스 자동 처리 시스템 - Cost Center 매핑 모듈
작성자: MACHO-GPT v3.4-mini
작성일: 2025-11-10
"""

import pandas as pd
import re
from typing import Tuple, Dict, Optional
from config import (
    COST_CENTER_MAPPING,
    SAFEEN_PATTERNS,
    ADP_PATTERNS,
    OFCO_PATTERNS,
    COLUMN_RANGES
)


class CostCenterMapper:
    """COST CENTER A, B, PRICE CENTER 매핑 클래스"""
    
    def __init__(self):
        self.mapping_table = COST_CENTER_MAPPING
        self.safeen_patterns = SAFEEN_PATTERNS
        self.adp_patterns = ADP_PATTERNS
        self.ofco_patterns = OFCO_PATTERNS
    
    def classify_cost_main(self, subject: str) -> str:
        """
        SUBJECT 기반 COST MAIN 분류
        
        Args:
            subject: 인보이스 SUBJECT 텍스트
            
        Returns:
            COST MAIN 카테고리 (PORT HANDLING, CONTRACT, AT COST)
        """
        subject_lower = subject.lower()
        
        # PORT HANDLING 패턴
        port_keywords = ['port dues', 'channel', 'pilotage', 'berthing', 
                        'safeen', 'adp', 'abu dhabi ports', 'waste', 'bunkering']
        if any(kw in subject_lower for kw in port_keywords):
            return 'PORT HANDLING'
        
        # AT COST 패턴
        at_cost_keywords = ['5000 ig', 'equipment', 'forklift', 'consumables', 
                           'diesel vessel', 'at cost']
        if any(kw in subject_lower for kw in at_cost_keywords):
            return 'AT COST'
        
        # CONTRACT 패턴 (기본값)
        contract_keywords = ['agency', 'clearance', 'arrangement', 'ofco']
        if any(kw in subject_lower for kw in contract_keywords):
            return 'CONTRACT'
        
        # 기본값
        return 'CONTRACT'
    
    def three_way_mapping(self, subject: str, amount: float) -> Tuple[str, str, str, str]:
        """
        3-Way 매핑: COST MAIN, COST CENTER A, COST CENTER B, PRICE CENTER
        
        Algorithm:
        1. SUBJECT 패턴 매칭
        2. Priority 기반 매핑 테이블 조회
        3. 3-Way 튜플 반환
        
        Args:
            subject: 인보이스 SUBJECT
            amount: 금액
            
        Returns:
            (cost_main, cost_center_a, cost_center_b, price_center)
        """
        # Step 1: COST MAIN 분류
        cost_main = self.classify_cost_main(subject)
        
        # Step 2: Provider 식별 (SAFEEN, ADP, OFCO)
        provider = self._identify_provider(subject)
        
        # Step 3: Provider별 특화 매핑
        if provider == 'SAFEEN':
            return self._map_safeen(subject, amount)
        elif provider == 'ADP':
            return self._map_adp(subject, amount)
        elif provider == 'OFCO':
            return self._map_ofco(subject, amount)
        else:
            # 기본 매핑
            return self._map_default(subject, amount, cost_main)
    
    def _identify_provider(self, subject: str) -> str:
        """Provider 식별 (SAFEEN, ADP, OFCO)"""
        subject_upper = subject.upper()
        
        if any(kw in subject_upper for kw in self.safeen_patterns['subject_keywords']):
            return 'SAFEEN'
        elif any(kw in subject_upper for kw in self.adp_patterns['subject_keywords']):
            return 'ADP'
        elif any(kw in subject_upper for kw in self.ofco_patterns['subject_keywords']):
            return 'OFCO'
        else:
            return 'UNKNOWN'
    
    def _map_safeen(self, subject: str, amount: float) -> Tuple[str, str, str, str]:
        """
        SAFEEN 인보이스 매핑
        
        패턴:
        - COST MAIN: PORT HANDLING
        - COST CENTER A: PORT HANDLING CHARGE
        - COST CENTER B: CHANNEL TRANSIT CHARGES
        - PRICE CENTER: CHANNEL TRANSIT CHARGES
        """
        cost_main = self.safeen_patterns['cost_main']
        cost_center_a = self.safeen_patterns['cost_center_a']
        cost_center_b = self.safeen_patterns['cost_center_b']
        price_center = self.safeen_patterns['default_price_center']
        
        # Subject에 따른 세부 분류
        if 'BULK' in subject.upper():
            price_center = 'BULK MATERIAL'
            cost_center_b = 'BULK CARGO HANDLING CHARGES'
        elif 'PILOTAGE' in subject.upper():
            price_center = 'Pilotage'
            cost_center_b = 'PORT HANDLING CHARGE'
        
        return (cost_main, cost_center_a, cost_center_b, price_center)
    
    def _map_adp(self, subject: str, amount: float) -> Tuple[str, str, str, str]:
        """
        ADP 인보이스 매핑
        
        패턴:
        - COST MAIN: PORT HANDLING
        - COST CENTER A: PORT HANDLING CHARGE
        - COST CENTER B: 서비스별 상이
        - PRICE CENTER: 서비스별 상이
        """
        cost_main = self.adp_patterns['cost_main']
        cost_center_a = self.adp_patterns['cost_center_a']
        
        subject_upper = subject.upper()
        
        # Port Dues 패턴
        if 'PORT DUES' in subject_upper or 'PORT DUE' in subject_upper:
            cost_center_b = self.adp_patterns['cost_center_b_variants']['PORT DUES']
            price_center = 'PORT DUES'
        
        # Bulk Material 패턴
        elif 'BULK' in subject_upper:
            cost_center_b = self.adp_patterns['cost_center_b_variants']['BULK']
            price_center = 'BULK MATERIAL'
        
        # Pilotage 패턴
        elif 'PILOTAGE' in subject_upper:
            cost_center_b = self.adp_patterns['cost_center_b_variants']['PILOTAGE']
            price_center = 'Pilotage'
        
        # Gate Pass 패턴
        elif 'GATE PASS' in subject_upper:
            cost_center_b = 'PORT DUES & SERVICES CHARGES'
            price_center = 'GATE PASS'
        
        # 기본값
        else:
            cost_center_b = 'PORT DUES & SERVICES CHARGES'
            price_center = 'PORT DUES'
        
        return (cost_main, cost_center_a, cost_center_b, price_center)
    
    def _map_ofco(self, subject: str, amount: float) -> Tuple[str, str, str, str]:
        """
        OFCO 자체 인보이스 매핑
        
        패턴:
        - COST MAIN: CONTRACT
        - COST CENTER A: CONTRACT
        - COST CENTER B: 서비스별 상이
        - PRICE CENTER: 서비스별 상이
        """
        cost_main = self.ofco_patterns['cost_main']
        cost_center_a = self.ofco_patterns['cost_center_a']
        
        subject_upper = subject.upper()
        
        # Cargo Clearance 패턴
        if 'CARGO CLEARANCE' in subject_upper:
            cost_center_b = self.ofco_patterns['cost_center_b_variants']['CARGO CLEARANCE']
            price_center = 'AGENCY FEE FOR CARGO CLEARANCE'
        
        # Berthing Arrangement 패턴
        elif 'BERTHING' in subject_upper:
            cost_center_b = self.ofco_patterns['cost_center_b_variants']['BERTHING']
            price_center = 'AGENCY FEE FOR BERTHING ARRANGEMENT'
        
        # FW Supply 패턴
        elif 'FW SUPPLY' in subject_upper or '5000 IG' in subject_upper:
            # AT COST로 전환
            if '5000 IG FW' in subject_upper:
                cost_main = 'AT COST'
                cost_center_a = 'AT COST'
                cost_center_b = 'AT COST(WATER SUPPLY)'
            else:
                cost_center_b = self.ofco_patterns['cost_center_b_variants']['FW SUPPLY']
            price_center = 'SUPPLY WATER 5000IG'
        
        # Handling Fee 패턴
        elif 'HANDLING FEE' in subject_upper:
            cost_center_b = 'CONTRACT'
            price_center = 'OFCO HANDLING FEE'
        
        # 기본값
        else:
            cost_center_b = 'CONTRACT'
            price_center = 'AGENCY FEE FOR CARGO CLEARANCE'
        
        return (cost_main, cost_center_a, cost_center_b, price_center)
    
    def _map_default(self, subject: str, amount: float, cost_main: str) -> Tuple[str, str, str, str]:
        """기본 매핑 로직"""
        cost_center_a = cost_main
        
        if cost_main == 'CONTRACT':
            cost_center_b = 'CONTRACT'
            price_center = 'AGENCY FEE FOR CARGO CLEARANCE'
        elif cost_main == 'AT COST':
            cost_center_b = 'AT COST'
            price_center = 'SUPPLY WATER 5000IG'
        else:  # PORT HANDLING
            cost_center_b = 'PORT HANDLING CHARGE'
            price_center = 'PORT DUES'
        
        return (cost_main, cost_center_a, cost_center_b, price_center)
    
    def get_column_range_for_cost_center(self, cost_center_a: str) -> Dict[str, int]:
        """
        COST CENTER A에 해당하는 컬럼 범위 반환
        
        Args:
            cost_center_a: COST CENTER A 값
            
        Returns:
            {'start': int, 'end': int, 'excel': str}
        """
        if 'CONTRACT' in cost_center_a:
            return COLUMN_RANGES['CONTRACT']
        elif 'AT COST' in cost_center_a:
            return COLUMN_RANGES['AT_COST']
        elif 'PORT HANDLING' in cost_center_a:
            return COLUMN_RANGES['PORT_HANDLING']
        else:
            # 기본값: CONTRACT 범위
            return COLUMN_RANGES['CONTRACT']
    
    def get_price_center_column_name(self, price_center: str, field_type: str = 'AMOUNT') -> Optional[str]:
        """
        Price Center 이름 → Excel 컬럼명 변환
        
        Args:
            price_center: Price Center 이름
            field_type: 'QTY' 또는 'AMOUNT'
            
        Returns:
            Excel 컬럼명 (예: 'AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT')
        """
        # Price Center 이름을 Excel 컬럼명으로 변환
        # 공백 → 언더스코어, 대문자 변환
        column_name_base = price_center.replace(' ', '_').upper()
        column_name = f"{column_name_base}_{field_type}"
        
        return column_name


# 사용 예시
if __name__ == '__main__':
    mapper = CostCenterMapper()
    
    # 테스트 케이스
    test_cases = [
        "SAFEEN INVOICE NO. 2024/001 - Channel Crossing – Rot# 2503123133",
        "ADP INV-2024-0456 - Port Dues for M/V HVDC Cargo",
        "Agency Fee: Cargo Clearance for Samsung HVDC Project",
        "Arranging FW Supply - 5000 IG FW for vessel",
    ]
    
    print("="*80)
    print("Cost Center 매핑 테스트")
    print("="*80)
    
    for subject in test_cases:
        cost_main, cost_a, cost_b, price_center = mapper.three_way_mapping(subject, 1000.0)
        
        print(f"\nSUBJECT: {subject}")
        print(f"  → COST MAIN: {cost_main}")
        print(f"  → COST CENTER A: {cost_a}")
        print(f"  → COST CENTER B: {cost_b}")
        print(f"  → PRICE CENTER: {price_center}")
        
        # 컬럼 범위 확인
        col_range = mapper.get_column_range_for_cost_center(cost_a)
        print(f"  → Excel 범위: {col_range['excel']} (컬럼 {col_range['start']}~{col_range['end']})")
