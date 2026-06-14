"""
COST CENTER 자동 매핑 모듈

SUBJECT 기반 COST MAIN, COST CENTER A, B, PRICE CENTER 자동 매핑

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import pandas as pd
import re
from typing import Tuple


class CostCenterMapper:
    """COST CENTER 자동 매핑 클래스"""
    
    def __init__(self):
        """매핑 규칙 초기화"""
        self.mapping_rules = self._load_mapping_rules()
    
    def _load_mapping_rules(self):
        """매핑 규칙 정의"""
        return [
            # Priority 1: SAFEEN (CHANNEL CROSSING)
            {
                'pattern': r'SAFEEN.*CHANNEL.*CROSS',
                'cost_main': 'PORT HANDLING',
                'cost_center_a': 'PORT HANDLING CHARGE',
                'cost_center_b': 'CHANNEL TRANSIT CHARGES',
                'price_center': 'CHANNEL TRANSIT CHARGES',
                'column_range': 'AH:CU',
                'priority': 1
            },
            
            # Priority 2: SAFEEN (PILOTAGE)
            {
                'pattern': r'SAFEEN.*PILOT',
                'cost_main': 'PORT HANDLING',
                'cost_center_a': 'PORT HANDLING CHARGE',
                'cost_center_b': 'PILOTAGE',
                'price_center': 'Pilotage',
                'column_range': 'AH:CU',
                'priority': 2
            },
            
            # Priority 3: ADP + PORT DUES
            {
                'pattern': r'(ADP|ABU DHABI PORT).*PORT.*DUES',
                'cost_main': 'PORT HANDLING',
                'cost_center_a': 'PORT HANDLING CHARGE',
                'cost_center_b': 'PORT DUES & SERVICES CHARGES',
                'price_center': 'PORT DUES',
                'column_range': 'AH:CU',
                'priority': 3
            },
            
            # Priority 4: ADP + BULK MATERIAL
            {
                'pattern': r'(ADP|ABU DHABI PORT).*BULK',
                'cost_main': 'PORT HANDLING',
                'cost_center_a': 'PORT HANDLING CHARGE',
                'cost_center_b': 'BULK CARGO HANDLING CHARGES',
                'price_center': 'BULK MATERIAL',
                'column_range': 'AH:CU',
                'priority': 4
            },
            
            # Priority 5: CARGO CLEARANCE
            {
                'pattern': r'CARGO.*CLEARANCE',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT',
                'cost_center_b': 'AF FOR CC',
                'price_center': 'AGENCY FEE FOR CARGO CLEARANCE',
                'column_range': 'L:W',
                'priority': 5
            },
            
            # Priority 6: BERTHING ARRANGEMENT
            {
                'pattern': r'BERTHING.*ARRANGEMENT',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT(AF FOR BA)',
                'cost_center_b': 'CONTRACT',
                'price_center': 'AGENCY FEE FOR BERTHING ARRANGEMENT',
                'column_range': 'L:W',
                'priority': 6
            },
            
            # Priority 7: FW SUPPLY (CONTRACT)
            {
                'pattern': r'(ARRANGING.*FW|FW.*SUPPLY|FRESH.*WATER.*SUPPLY)',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT',
                'cost_center_b': 'AF FOR FW SA',
                'price_center': 'SUPPLY WATER 5000IG',
                'column_range': 'L:W',
                'priority': 7
            },
            
            # Priority 8: 5000 IG FW (AT COST)
            {
                'pattern': r'5000.*IG.*FW',
                'cost_main': 'AT COST',
                'cost_center_a': 'AT COST',
                'cost_center_b': 'AT COST(WATER SUPPLY)',
                'price_center': 'SUPPLY WATER 5000IG',
                'column_range': 'X:AG',
                'priority': 8
            },
            
            # Priority 9: EQUIPMENT HIRE (FORKLIFT)
            {
                'pattern': r'FORKLIFT',
                'cost_main': 'AT COST',
                'cost_center_a': 'AT COST',
                'cost_center_b': 'AT COST(EQUIPMENT HIRE)',
                'price_center': 'FORKLIFT HIRE CHARGE',
                'column_range': 'X:AG',
                'priority': 9
            },
            
            # Priority 10: EQUIPMENT HIRE (CRANE)
            {
                'pattern': r'CRANE',
                'cost_main': 'AT COST',
                'cost_center_a': 'AT COST',
                'cost_center_b': 'AT COST(EQUIPMENT HIRE)',
                'price_center': 'EQUIPMENT HIRE',
                'column_range': 'AH:CU',
                'priority': 10
            },
            
            # Priority 11: MANPOWER (RIGGER)
            {
                'pattern': r'RIGGER',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT',
                'cost_center_b': 'CONTRACT',
                'price_center': 'Rigger',
                'column_range': 'AH:CU',
                'priority': 11
            },
            
            # Priority 12: MANPOWER (BANKSMAN)
            {
                'pattern': r'BANKSMAN',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT',
                'cost_center_b': 'CONTRACT',
                'price_center': 'Banksman',
                'column_range': 'AH:CU',
                'priority': 12
            },
            
            # Priority 13: MANPOWER (SUPERVISOR)
            {
                'pattern': r'SUPERVISOR',
                'cost_main': 'CONTRACT',
                'cost_center_a': 'CONTRACT',
                'cost_center_b': 'CONTRACT',
                'price_center': 'Supervisor',
                'column_range': 'AH:CU',
                'priority': 13
            },
            
            # Priority 14: GATE PASS
            {
                'pattern': r'GATE.*PASS',
                'cost_main': 'PORT HANDLING',
                'cost_center_a': 'PORT HANDLING CHARGE',
                'cost_center_b': 'PORT DUES & SERVICES CHARGES',
                'price_center': 'GATE PASS',
                'column_range': 'AH:CU',
                'priority': 14
            },
        ]
    
    def map_single(self, subject: str, amount: float) -> Tuple[str, str, str, str, str]:
        """
        단일 라인에 대해 COST CENTER 매핑
        
        Parameters:
            subject (str): SUBJECT 텍스트
            amount (float): 금액
        
        Returns:
            tuple: (COST_MAIN, COST_CENTER_A, COST_CENTER_B, PRICE_CENTER, COLUMN_RANGE)
        """
        if not subject or not isinstance(subject, str):
            return ('UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN')
        
        subject_upper = subject.upper()
        
        # 매핑 규칙 순회 (Priority 순서대로)
        for rule in sorted(self.mapping_rules, key=lambda x: x['priority']):
            if re.search(rule['pattern'], subject_upper, re.IGNORECASE):
                return (
                    rule['cost_main'],
                    rule['cost_center_a'],
                    rule['cost_center_b'],
                    rule['price_center'],
                    rule['column_range']
                )
        
        # 매칭 실패 시 기본값
        return ('UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN')
    
    def map_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전체 DataFrame에 대해 COST CENTER 매핑
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: COST CENTER 매핑 추가된 DataFrame
        """
        df['COST MAIN'] = None
        df['COST CENTER A'] = None
        df['COST CENTER B'] = None
        df['PRICE CENTER'] = None
        df['COLUMN_RANGE'] = None
        
        for idx, row in df.iterrows():
            cost_main, cost_a, cost_b, price_center, col_range = self.map_single(
                row.get('SUBJECT', ''),
                row.get('Total_Amount_AED', 0.0)
            )
            
            df.at[idx, 'COST MAIN'] = cost_main
            df.at[idx, 'COST CENTER A'] = cost_a
            df.at[idx, 'COST CENTER B'] = cost_b
            df.at[idx, 'PRICE CENTER'] = price_center
            df.at[idx, 'COLUMN_RANGE'] = col_range
        
        return df
