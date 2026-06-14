"""
검증 엔진

3중 검증 시스템:
1. calc_check: EA 계산 검증 (Qty × Rate)
2. vat_check: VAT 검증 (5%)
3. pc_check: Price Center 합계 검증

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import pandas as pd
import numpy as np


class ValidationEngine:
    """검증 엔진 클래스"""
    
    def __init__(self):
        """검증 파라미터 초기화"""
        self.calc_tolerance_pct = 0.02  # ±2%
        self.vat_tolerance = 0.01       # ±0.01 USD
        self.pc_tolerance = 1.00        # ±1.00 AED
        self.vat_rate = 0.05            # 5% VAT
        self.exchange_rate = 3.6725     # AED to USD
    
    def validate_calc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        calc_check: EA 계산 검증
        
        Σ(EA_i_Qty × EA_i_Rate) ≈ Total_Amount_AED (±2%)
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: calc_check 컬럼 추가
        """
        # EA 총액 계산
        df['EA_Total_Calculated'] = (
            df['EA_1_Qty'].fillna(0) * df['EA_1_Rate'].fillna(0) +
            df['EA_2_Qty'].fillna(0) * df['EA_2_Rate'].fillna(0) +
            df['EA_3_Qty'].fillna(0) * df['EA_3_Rate'].fillna(0) +
            df['EA_4_Qty'].fillna(0) * df['EA_4_Rate'].fillna(0)
        )
        
        # 차이 계산
        df['calc_diff'] = abs(df['EA_Total_Calculated'] - df['Total_Amount_AED'])
        
        # 차이율 계산
        df['calc_diff_pct'] = np.where(
            df['Total_Amount_AED'] != 0,
            df['calc_diff'] / df['Total_Amount_AED'],
            0
        )
        
        # 검증 플래그 (NaN = PASS, float = FAIL)
        df['calc_check'] = df['calc_diff_pct'].apply(
            lambda x: np.nan if x <= self.calc_tolerance_pct else x
        )
        
        # 상태 (PASS/WARN/FAIL)
        df['calc_status'] = df['calc_diff_pct'].apply(self._get_status)
        
        return df
    
    def validate_vat(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        vat_check: VAT 검증
        
        VAT_USD ≈ Amount_USD × 5% (±0.01 USD)
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: vat_check 컬럼 추가
        """
        # 예상 VAT 계산
        df['expected_vat'] = (df['Amount_USD'] * self.vat_rate).round(2)
        
        # 차이 계산
        df['vat_diff'] = abs(df['VAT_USD'].fillna(0) - df['expected_vat'])
        
        # 검증 플래그 (NaN = PASS, float = FAIL)
        df['vat_check'] = df['vat_diff'].apply(
            lambda x: np.nan if x <= self.vat_tolerance else x
        )
        
        return df
    
    def validate_pc_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        pc_check: Price Center 합계 검증
        
        Σ(Price Center AMOUNT 컬럼) ≈ Total_Amount_AED (±1 AED)
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: pc_check 컬럼 추가
        """
        # Price Center AMOUNT 컬럼 선택
        amount_cols = [col for col in df.columns 
                      if isinstance(col, str) 
                      and '_AMOUNT' in col 
                      and col not in ['Total_Amount_AED', 'Total_Amount_USD', 
                                     'EA_1_Amount', 'EA_2_Amount', 'EA_3_Amount', 'EA_4_Amount',
                                     'EA_Total_Amount', 'EA_Total_Calculated']]
        
        # 합계 계산 (문자열을 숫자로 변환)
        df['pc_sum'] = df[amount_cols].apply(pd.to_numeric, errors='coerce').sum(axis=1, skipna=True)
        
        # 차이 계산
        df['pc_diff'] = abs(df['pc_sum'] - df['Total_Amount_AED'])
        
        # 검증 플래그 (NaN = PASS, float = FAIL)
        df['pc_check'] = df['pc_diff'].apply(
            lambda x: np.nan if x <= self.pc_tolerance else x
        )
        
        return df
    
    def validate_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        total_check: Total Amount 검증
        
        Total_Amount_USD ≈ Amount_USD + VAT_USD
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: total_check 컬럼 추가
        """
        # 예상 총액 계산
        df['expected_total'] = (df['Amount_USD'] + df['VAT_USD']).round(2)
        
        # 차이 계산
        df['total_diff'] = abs(df['Total_Amount_USD'].fillna(0) - df['expected_total'])
        
        # 검증 플래그 (NaN = PASS, float = FAIL)
        df['total_check'] = df['total_diff'].apply(
            lambda x: np.nan if x <= 0.01 else x  # ±0.01 USD
        )
        
        return df
    
    def validate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전체 검증 실행
        
        Parameters:
            df (pd.DataFrame): 입력 DataFrame
        
        Returns:
            pd.DataFrame: 모든 검증 컬럼 추가
        """
        # 통화 변환 (누락 시)
        if 'Amount_USD' not in df.columns or df['Amount_USD'].isna().all():
            df['Amount_USD'] = (df['Total_Amount_AED'] / self.exchange_rate).round(2)
        
        if 'VAT_USD' not in df.columns or df['VAT_USD'].isna().all():
            df['VAT_USD'] = (df['Amount_USD'] * self.vat_rate).round(2)
        
        if 'Total_Amount_USD' not in df.columns or df['Total_Amount_USD'].isna().all():
            df['Total_Amount_USD'] = (df['Amount_USD'] + df['VAT_USD']).round(2)
        
        # 3중 검증 실행
        df = self.validate_calc(df)
        df = self.validate_vat(df)
        df = self.validate_pc_sum(df)
        df = self.validate_total(df)
        
        return df
    
    def _get_status(self, diff_pct: float) -> str:
        """차이율 기반 상태 반환"""
        if diff_pct <= 0.02:
            return 'PASS'
        elif diff_pct <= 0.05:
            return 'WARN'
        else:
            return 'FAIL'
