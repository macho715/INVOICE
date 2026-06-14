"""
EA Slot 분해 엔진

라인 총액을 최대 4개 EA Slots (RatePair)로 분해

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class EASlotDecomposer:
    """EA Slot 자동 분해 클래스"""
    
    def __init__(self):
        """EA 템플릿 초기화"""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """EA 분해 템플릿 정의"""
        return {
            # Template 1: Channel Crossing (3-way split)
            'CHANNEL_CROSSING': {
                'slots': 3,
                'breakdown': [
                    {'qty_pct': 2.0, 'rate_base': 'major'},  # EA_1: 주 요금
                    {'qty_pct': 2.0, 'rate_base': 'minor'},  # EA_2: 부가 서비스
                    {'qty_pct': 1.0, 'rate_base': 'misc'},   # EA_3: 기타
                ]
            },
            
            # Template 2: Agency Fee (1-way, 전액)
            'AGENCY_FEE': {
                'slots': 1,
                'breakdown': [
                    {'qty_pct': 1.0, 'rate_base': 'full'},   # EA_1: 전액
                ]
            },
            
            # Template 3: Manpower (variable, 시간당)
            'MANPOWER': {
                'slots': 1,
                'breakdown': [
                    {'qty_pct': 'hours', 'rate_base': 'hourly'},  # EA_1: 시간 × 시급
                ]
            },
            
            # Template 4: Equipment (1-way or 2-way)
            'EQUIPMENT': {
                'slots': 2,
                'breakdown': [
                    {'qty_pct': 'hours', 'rate_base': 'hourly'},      # EA_1: 시간 × 시급
                    {'qty_pct': 1.0, 'rate_base': 'mobilization'},    # EA_2: 동원 비용
                ]
            },
        }
    
    def decompose_single(self, row: pd.Series) -> Dict:
        """
        단일 라인에 대해 EA Slot 분해
        
        Parameters:
            row (pd.Series): DataFrame 행
        
        Returns:
            dict: EA_1~4 Qty, Rate, Amount
        """
        subject = row.get('SUBJECT', '')
        amount = row.get('Total_Amount_AED', 0.0)
        price_center = row.get('PRICE CENTER', '')
        
        # 템플릿 선택
        template_key = self._select_template(subject, price_center)
        template = self.templates.get(template_key, self.templates['AGENCY_FEE'])  # Default: 1-way
        
        # EA Slot 초기화
        ea_slots = {}
        for i in range(1, 5):
            ea_slots[f'EA_{i}_Qty'] = np.nan
            ea_slots[f'EA_{i}_Rate'] = np.nan
            ea_slots[f'EA_{i}_Amount'] = np.nan
        
        # 템플릿에 따라 분해
        if template_key == 'CHANNEL_CROSSING':
            # 3-way split (SAFEEN 패턴)
            ea_slots['EA_1_Qty'] = 2.0
            ea_slots['EA_1_Rate'] = amount * 0.93 / 2.0  # 93%
            ea_slots['EA_1_Amount'] = amount * 0.93
            
            ea_slots['EA_2_Qty'] = 2.0
            ea_slots['EA_2_Rate'] = amount * 0.03 / 2.0  # 3%
            ea_slots['EA_2_Amount'] = amount * 0.03
            
            ea_slots['EA_3_Qty'] = 1.0
            ea_slots['EA_3_Rate'] = amount * 0.04  # 4%
            ea_slots['EA_3_Amount'] = amount * 0.04
            
        elif template_key == 'MANPOWER':
            # 시간 기반 분해 (예: 8시간 × 시급)
            # 기본값: 8시간으로 가정
            hours = row.get('Qty', 8.0)
            hourly_rate = amount / hours if hours > 0 else amount
            
            ea_slots['EA_1_Qty'] = hours
            ea_slots['EA_1_Rate'] = hourly_rate
            ea_slots['EA_1_Amount'] = amount
            
        elif template_key == 'EQUIPMENT':
            # 2-way split (장비 임대 + 동원 비용)
            hours = row.get('Qty', 1.0)
            
            if hours > 1:  # 시간 기반
                ea_slots['EA_1_Qty'] = hours
                ea_slots['EA_1_Rate'] = amount * 0.9 / hours  # 90%
                ea_slots['EA_1_Amount'] = amount * 0.9
                
                ea_slots['EA_2_Qty'] = 1.0
                ea_slots['EA_2_Rate'] = amount * 0.1  # 10% 동원 비용
                ea_slots['EA_2_Amount'] = amount * 0.1
            else:  # 1-way
                ea_slots['EA_1_Qty'] = 1.0
                ea_slots['EA_1_Rate'] = amount
                ea_slots['EA_1_Amount'] = amount
        
        else:
            # Default: 1-way (전액)
            ea_slots['EA_1_Qty'] = 1.0
            ea_slots['EA_1_Rate'] = amount
            ea_slots['EA_1_Amount'] = amount
        
        # EA Total Amount 계산
        ea_slots['EA_Total_Amount'] = sum([
            ea_slots.get(f'EA_{i}_Amount', 0.0) or 0.0 
            for i in range(1, 5)
        ])
        
        return ea_slots
    
    def _select_template(self, subject: str, price_center: str) -> str:
        """SUBJECT/PRICE_CENTER 기반 템플릿 선택"""
        subject_upper = subject.upper()
        price_upper = price_center.upper()
        
        if 'SAFEEN' in subject_upper and 'CHANNEL' in subject_upper:
            return 'CHANNEL_CROSSING'
        elif 'RIGGER' in price_upper or 'BANKSMAN' in price_upper or 'SUPERVISOR' in price_upper:
            return 'MANPOWER'
        elif 'EQUIPMENT' in price_upper or 'CRANE' in price_upper or 'FORKLIFT' in price_upper:
            return 'EQUIPMENT'
        elif 'AGENCY' in price_upper:
            return 'AGENCY_FEE'
        else:
            return 'AGENCY_FEE'  # Default
    
    def decompose_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전체 DataFrame에 대해 EA Slot 분해
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: EA Slots 추가된 DataFrame
        """
        # EA 컬럼 초기화
        for i in range(1, 5):
            df[f'EA_{i}_Qty'] = np.nan
            df[f'EA_{i}_Rate'] = np.nan
            df[f'EA_{i}_Amount'] = np.nan
        df['EA_Total_Amount'] = np.nan
        
        # 각 행에 대해 EA 분해
        for idx, row in df.iterrows():
            ea_slots = self.decompose_single(row)
            
            for key, value in ea_slots.items():
                df.at[idx, key] = value
        
        return df
