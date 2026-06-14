"""
OFCO 인보이스 자동 처리 시스템 - 메인 프로세서
작성자: MACHO-GPT v3.4-mini
작성일: 2025-11-10
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import logging

from config import (
    COLUMN_RANGES,
    CURRENCY_CONFIG,
    VALIDATION_RULES,
    FILE_PATHS,
    PROCESSING_OPTIONS
)
from cost_center_mapper import CostCenterMapper
from safeen_adp_handler import SafeenAdpHandler


class InvoiceProcessor:
    """OFCO 인보이스 메인 처리 클래스"""
    
    def __init__(self, log_level='INFO'):
        # 로거 설정
        self.logger = self._setup_logger(log_level)
        
        # 모듈 초기화
        self.cost_center_mapper = CostCenterMapper()
        self.safeen_adp_handler = SafeenAdpHandler()
        
        # 통계
        self.stats = {
            'total_lines': 0,
            'safeen_lines': 0,
            'adp_lines': 0,
            'ofco_lines': 0,
            'calc_warnings': 0,
            'vat_warnings': 0,
            'pc_warnings': 0,
        }
    
    def _setup_logger(self, level='INFO'):
        """로거 설정"""
        logger = logging.getLogger('InvoiceProcessor')
        logger.setLevel(getattr(logging, level))
        
        # 콘솔 핸들러
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, level))
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
        return logger
    
    def process_monthly_invoice(self, invoice_month: str) -> pd.DataFrame:
        """
        월간 인보이스 처리
        
        Args:
            invoice_month: 처리할 월 (예: '2024-11')
            
        Returns:
            처리된 DataFrame
        """
        self.logger.info(f"Processing invoice for {invoice_month}")
        
        # 1. 템플릿 로드
        template_path = FILE_PATHS['template']
        df = pd.read_excel(template_path, sheet_name='Sheet1')
        
        self.logger.info(f"Loaded template: {len(df)} rows")
        
        # 2. 월 필터링
        df_month = self._filter_by_month(df, invoice_month)
        self.logger.info(f"Filtered to {invoice_month}: {len(df_month)} rows")
        
        # 3. 라인별 처리
        df_processed = self._process_lines(df_month)
        
        # 4. 검증
        df_validated = self._validate_invoice(df_processed)
        
        # 5. 통계 출력
        self._print_statistics()
        
        return df_validated
    
    def _filter_by_month(self, df: pd.DataFrame, invoice_month: str) -> pd.DataFrame:
        """월별 필터링"""
        # INVOICE DATE_YEAR_MONTH 컬럼으로 필터링
        if 'INVOICE DATE_YEAR_MONTH' in df.columns:
            df_filtered = df[
                df['INVOICE DATE_YEAR_MONTH'].dt.strftime('%Y-%m') == invoice_month
            ].copy()
        else:
            # 전체 반환
            df_filtered = df.copy()
        
        return df_filtered
    
    def _process_lines(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        라인별 처리
        
        Algorithm:
        1. SUBJECT 파싱
        2. Cost Center 3-Way 매핑
        3. Price Center 할당
        4. EA 슬롯 분해
        5. 통화 변환
        """
        self.logger.info("Processing lines...")
        
        processed_lines = []
        
        for idx, row in df.iterrows():
            try:
                processed_line = self._process_single_line(row)
                processed_lines.append(processed_line)
                
                # 진행률 표시
                if (idx + 1) % 100 == 0:
                    self.logger.info(f"Processed {idx + 1}/{len(df)} lines")
                    
            except Exception as e:
                self.logger.error(f"Error processing line {row['NO']}: {e}")
                processed_lines.append(row.to_dict())
        
        df_processed = pd.DataFrame(processed_lines)
        self.stats['total_lines'] = len(df_processed)
        
        return df_processed
    
    def _process_single_line(self, row: pd.Series) -> Dict:
        """단일 라인 처리"""
        line_dict = row.to_dict()
        subject = row['SUBJECT']
        amount = row['Total_Amount_AED']
        
        # 1. Cost Center 매핑
        cost_main, cost_a, cost_b, price_center = \
            self.cost_center_mapper.three_way_mapping(subject, amount)
        
        line_dict['COST MAIN'] = cost_main
        line_dict['COST CENTER A'] = cost_a
        line_dict['COST CENTER B'] = cost_b
        line_dict['PRICE CENTER'] = price_center
        
        # 2. SAFEEN/ADP 특화 처리
        if self.safeen_adp_handler.is_safeen_invoice(subject):
            line_dict = self.safeen_adp_handler.process_safeen_invoice(line_dict)
            self.stats['safeen_lines'] += 1
            
        elif self.safeen_adp_handler.is_adp_invoice(subject):
            line_dict = self.safeen_adp_handler.process_adp_invoice(line_dict)
            self.stats['adp_lines'] += 1
            
        else:
            # OFCO 자체 인보이스
            line_dict = self._process_ofco_line(line_dict)
            self.stats['ofco_lines'] += 1
        
        # 3. 통화 변환
        line_dict = self._convert_currency(line_dict)
        
        # 4. Price Center 컬럼 채우기
        line_dict = self._fill_price_center_columns(line_dict)
        
        return line_dict
    
    def _process_ofco_line(self, line_dict: Dict) -> Dict:
        """OFCO 자체 인보이스 처리 (Simple 1-way EA)"""
        amount = line_dict['Total_Amount_AED']
        
        line_dict.update({
            'EA_1_Qty': 1.0,
            'EA_1_Rate': round(amount, 2),
            'EA_1_Amount': round(amount, 2),
            'EA_1_Name': 'Full Amount',
            
            'EA_2_Qty': None,
            'EA_2_Rate': None,
            'EA_2_Amount': None,
            'EA_2_Name': None,
            
            'EA_3_Qty': None,
            'EA_3_Rate': None,
            'EA_3_Amount': None,
            'EA_3_Name': None,
            
            'EA_4_Qty': None,
            'EA_4_Rate': None,
            'EA_4_Amount': None,
            'EA_4_Name': None,
            
            'EA_Total_Amount': round(amount, 2),
            'EA_Mapped_Count': 1,
            'EA_Template': 'AGENCY_FEE_1WAY',
        })
        
        return line_dict
    
    def _convert_currency(self, line_dict: Dict) -> Dict:
        """
        통화 변환 (AED → USD)
        
        Algorithm:
        1. Amount_USD = Total_Amount_AED / exchange_rate
        2. VAT_USD = Amount_USD × 5%
        3. Total_Amount_USD = Amount_USD + VAT_USD
        """
        amount_aed = line_dict['Total_Amount_AED']
        exchange_rate = CURRENCY_CONFIG['exchange_rates']['USD']
        vat_rate = CURRENCY_CONFIG['vat_rate']
        
        # USD 변환
        amount_usd = amount_aed / exchange_rate
        vat_usd = amount_usd * vat_rate
        total_usd = amount_usd + vat_usd
        
        line_dict['Amount_USD'] = round(amount_usd, 2)
        line_dict['VAT_USD'] = round(vat_usd, 2)
        line_dict['Total_Amount_USD'] = round(total_usd, 2)
        
        return line_dict
    
    def _fill_price_center_columns(self, line_dict: Dict) -> Dict:
        """
        Price Center별 QTY/AMOUNT 컬럼 채우기
        
        Algorithm:
        1. Price Center 이름 → 컬럼명 변환
        2. 해당 컬럼에 QTY/AMOUNT 값 할당
        3. 나머지 컬럼은 NaN 또는 0.0
        """
        price_center = line_dict.get('PRICE CENTER', '')
        
        if not price_center:
            return line_dict
        
        # 컬럼명 생성
        qty_col = self.cost_center_mapper.get_price_center_column_name(
            price_center, 'QTY'
        )
        amount_col = self.cost_center_mapper.get_price_center_column_name(
            price_center, 'AMOUNT'
        )
        
        # EA_1 값 사용
        qty = line_dict.get('EA_1_Qty', 1.0)
        amount = line_dict.get('Total_Amount_AED', 0.0)
        
        # 컬럼 채우기
        if qty_col:
            line_dict[qty_col] = qty
        if amount_col:
            line_dict[amount_col] = amount
        
        return line_dict
    
    def _validate_invoice(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        인보이스 검증
        
        검증 항목:
        1. calc_check: EA 계산 검증
        2. vat_check: VAT 검증
        3. pc_check: Price Center 합계 검증
        """
        self.logger.info("Validating invoice...")
        
        # 1. calc_check
        df = self._validate_ea_calculation(df)
        
        # 2. vat_check
        df = self._validate_vat(df)
        
        # 3. pc_check
        df = self._validate_price_center_sum(df)
        
        return df
    
    def _validate_ea_calculation(self, df: pd.DataFrame) -> pd.DataFrame:
        """EA 계산 검증"""
        tolerance = VALIDATION_RULES['calc_check']['tolerance']
        
        # EA 총액 계산
        df['EA_Total_Amount_Calc'] = (
            df['EA_1_Qty'].fillna(0) * df['EA_1_Rate'].fillna(0) +
            df['EA_2_Qty'].fillna(0) * df['EA_2_Rate'].fillna(0) +
            df['EA_3_Qty'].fillna(0) * df['EA_3_Rate'].fillna(0) +
            df['EA_4_Qty'].fillna(0) * df['EA_4_Rate'].fillna(0)
        )
        
        # 차이 계산
        df['calc_diff'] = abs(df['EA_Total_Amount_Calc'] - df['Total_Amount_AED'])
        df['calc_diff_pct'] = df['calc_diff'] / df['Total_Amount_AED']
        
        # 검증 플래그
        df['calc_check'] = df['calc_diff_pct'].apply(
            lambda x: np.nan if x <= tolerance else x
        )
        
        # 통계
        warnings = df['calc_check'].notna().sum()
        self.stats['calc_warnings'] = warnings
        self.logger.info(f"calc_check warnings: {warnings}")
        
        return df
    
    def _validate_vat(self, df: pd.DataFrame) -> pd.DataFrame:
        """VAT 검증"""
        tolerance = VALIDATION_RULES['vat_check']['tolerance']
        vat_rate = CURRENCY_CONFIG['vat_rate']
        
        # 예상 VAT 계산
        df['expected_vat'] = (df['Amount_USD'] * vat_rate).round(2)
        
        # 차이 계산
        df['vat_diff'] = abs(df['VAT_USD'] - df['expected_vat'])
        
        # 검증 플래그
        df['vat_check'] = df['vat_diff'].apply(
            lambda x: np.nan if x <= tolerance else x
        )
        
        # 통계
        warnings = df['vat_check'].notna().sum()
        self.stats['vat_warnings'] = warnings
        self.logger.info(f"vat_check warnings: {warnings}")
        
        return df
    
    def _validate_price_center_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price Center 합계 검증"""
        tolerance = VALIDATION_RULES['pc_check']['tolerance']
        
        # Price Center AMOUNT 컬럼 선택
        pc_amount_cols = [col for col in df.columns 
                         if isinstance(col, str) and col.endswith('_AMOUNT') 
                         and col not in ['Total_Amount_AED', 'EA_Total_Amount',
                                        'EA_1_Amount', 'EA_2_Amount', 
                                        'EA_3_Amount', 'EA_4_Amount']]
        
        # 합계 계산
        df['pc_sum'] = df[pc_amount_cols].sum(axis=1, skipna=True)
        
        # 차이 계산
        df['pc_diff'] = abs(df['pc_sum'] - df['Total_Amount_AED'])
        
        # 검증 플래그
        df['pc_check'] = df['pc_diff'].apply(
            lambda x: np.nan if x <= tolerance else x
        )
        
        # 통계
        warnings = df['pc_check'].notna().sum()
        self.stats['pc_warnings'] = warnings
        self.logger.info(f"pc_check warnings: {warnings}")
        
        return df
    
    def _print_statistics(self):
        """통계 출력"""
        self.logger.info("\n" + "="*80)
        self.logger.info("처리 통계")
        self.logger.info("="*80)
        self.logger.info(f"총 라인 수: {self.stats['total_lines']}")
        self.logger.info(f"  - SAFEEN: {self.stats['safeen_lines']}")
        self.logger.info(f"  - ADP: {self.stats['adp_lines']}")
        self.logger.info(f"  - OFCO: {self.stats['ofco_lines']}")
        self.logger.info(f"\n검증 결과:")
        self.logger.info(f"  - calc_check 경고: {self.stats['calc_warnings']}")
        self.logger.info(f"  - vat_check 경고: {self.stats['vat_warnings']}")
        self.logger.info(f"  - pc_check 경고: {self.stats['pc_warnings']}")
        self.logger.info("="*80)
    
    def save_processed_invoice(self, df: pd.DataFrame, output_filename: str):
        """처리된 인보이스 저장"""
        output_dir = Path(FILE_PATHS['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / output_filename
        
        # 백업
        if PROCESSING_OPTIONS['backup_original'] and output_path.exists():
            backup_path = output_path.with_suffix('.xlsx.backup')
            output_path.rename(backup_path)
            self.logger.info(f"Backup created: {backup_path}")
        
        # 저장
        df.to_excel(output_path, index=False, sheet_name='Sheet1')
        self.logger.info(f"Saved to: {output_path}")
        
        return output_path


# 사용 예시
if __name__ == '__main__':
    processor = InvoiceProcessor(log_level='INFO')
    
    # 2024년 11월 인보이스 처리
    df_result = processor.process_monthly_invoice('2024-11')
    
    # 저장
    output_file = f"OFCO_INVOICE_2024-11_Processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    processor.save_processed_invoice(df_result, output_file)
