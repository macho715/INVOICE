#!/usr/bin/env python3
"""
Multi-Month Invoice Consolidator

여러 개월 인보이스 파일을 자동으로 통합
- 14개월치 파일 처리 (2024.08 ~ 2025.09)
- Source_File 컬럼 추가 (A열)
- Month 컬럼 추가 (C열)

Version: 1.0.0
Created: 2024-10-16
"""

import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

import pandas as pd

from engine_individual_sheets import InvoiceConsolidator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 월 이름 → 번호 매핑
MONTH_MAP = {
    'JANUARY': '01', 'FEBRUARY': '02', 'MARCH': '03', 'APRIL': '04',
    'MAY': '05', 'JUNE': '06', 'JULY': '07', 
    'AUG': '08', 'AUGUST': '08',
    'SEP': '09', 'SEPT': '09', 'SEPTEMBER': '09',
    'OCT': '10', 'OCTOBER': '10', 
    'NOV': '11', 'NOVEMBER': '11',
    'DEC': '12', 'DECEMBER': '12'
}


class MultiMonthConsolidator:
    """여러 개월 인보이스 파일을 통합"""
    
    def __init__(self, shpt_folder: Path):
        self.shpt_folder = Path(shpt_folder)
        
        # 파일명 패턴: "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm"
        self.invoice_pattern = re.compile(
            r'SCNT SHIPMENT DRAFT INVOICE \(([A-Z]+)\s+(\d{4})\)',
            re.IGNORECASE
        )
    
    def consolidate_all_months(self) -> pd.DataFrame:
        """
        SHPT 폴더의 모든 인보이스 파일 통합
        
        Returns:
            pd.DataFrame with Source_File as first column (A열)
        """
        logger.info(f"Scanning folder: {self.shpt_folder}")
        
        # 1. Excel 파일 목록
        invoice_files = self._get_invoice_files()
        logger.info(f"Found {len(invoice_files)} invoice files")
        
        # 2. 각 파일 처리
        all_month_data = []
        
        for file_path, month, source_label in invoice_files:
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing: {file_path.name}")
            logger.info(f"Month: {month}, Label: {source_label}")
            logger.info(f"{'='*80}")
            
            try:
                df = self._process_single_file(file_path, month, source_label)
                if df is not None and len(df) > 0:
                    all_month_data.append(df)
                    logger.info(f"✅ Extracted {len(df)} rows from {source_label}")
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                continue
        
        # 3. 모든 월 데이터 병합
        if not all_month_data:
            raise ValueError("No data extracted from any file")
        
        merged_df = pd.concat(all_month_data, ignore_index=True)
        
        # 4. 표준화 적용 (컬럼명 정규화 + 순서 재정렬)
        merged_df = self._standardize_output(merged_df)
        
        # 5. No 컬럼 재정렬 (전체 일련번호)
        if 'No' in merged_df.columns:
            merged_df['No'] = range(1, len(merged_df) + 1)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ CONSOLIDATION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Total rows: {len(merged_df)}")
        logger.info(f"Total files: {len(all_month_data)}")
        logger.info(f"Total columns: {len(merged_df.columns)}")
        logger.info(f"Months covered: {sorted(merged_df['Month'].unique())}")
        
        return merged_df
    
    def _get_invoice_files(self) -> List[Tuple[Path, str, str]]:
        """
        인보이스 파일 목록 반환 (시간 순 정렬)
        
        Returns:
            [(파일경로, "2024-08", "AUG 2024"), ...]
        """
        invoice_files = []
        
        # *.xlsx, *.xlsm 파일 찾기
        for pattern in ['*.xlsx', '*.xlsm']:
            for file_path in self.shpt_folder.glob(pattern):
                # 파일명에서 월 정보 추출
                month = self._extract_month_from_filename(file_path.name)
                source_label = self._extract_source_label(file_path.name)
                
                if month != "UNKNOWN":
                    invoice_files.append((file_path, month, source_label))
        
        # 월 순으로 정렬 (2024-08, 2024-09, ..., 2025-09)
        invoice_files.sort(key=lambda x: x[1])
        
        return invoice_files
    
    def _extract_month_from_filename(self, filename: str) -> str:
        """
        파일명에서 월 정보 추출
        
        Examples:
            "SCNT ... (AUG 2024).xlsx" → "2024-08"
            "SCNT ... (SEPT 2025).xlsm" → "2025-09"
            "SCNT ... (JANUARY 2025).xlsx" → "2025-01"
        
        Returns:
            "YYYY-MM" 형식 또는 "UNKNOWN"
        """
        match = self.invoice_pattern.search(filename)
        if match:
            month_name = match.group(1).strip().upper()
            year = match.group(2)
            
            month_num = MONTH_MAP.get(month_name)
            if month_num:
                return f"{year}-{month_num}"
        
        logger.warning(f"Could not extract month from: {filename}")
        return "UNKNOWN"
    
    def _extract_source_label(self, filename: str) -> str:
        """
        파일명에서 Source_File 레이블 추출
        
        Examples:
            "SCNT ... (SEPT 2025).xlsm" → "SEPT 2025"
            "SCNT ... (AUG 2024).xlsx" → "AUG 2024"
        
        Returns:
            "MONTH YEAR" 형식
        """
        match = self.invoice_pattern.search(filename)
        if match:
            month_name = match.group(1).strip().upper()
            year = match.group(2)
            return f"{month_name} {year}"
        
        return filename
    
    def _process_single_file(self, file_path: Path, month: str, source_label: str) -> Optional[pd.DataFrame]:
        """
        단일 파일 처리
        
        1. InvoiceConsolidator로 시트 통합
        2. Source_File 컬럼 추가 (A열)
        3. Month 컬럼 추가
        4. DataFrame 반환
        """
        # InvoiceConsolidator로 시트 통합
        consolidator = InvoiceConsolidator(file_path)
        df = consolidator.consolidate()
        
        if df is None or len(df) == 0:
            logger.warning(f"No data extracted from {file_path.name}")
            return None
        
        # Source_File 컬럼 추가 (맨 앞에 삽입)
        df.insert(0, 'Source_File', source_label)
        
        # Month 컬럼 추가 (Source_File 다음)
        df.insert(1, 'Month', month)
        
        return df
    
    def _standardize_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        최종 출력 표준화
        
        1. 컬럼명 정규화 (오타 수정, 통일)
        2. 표준 컬럼 순서 적용
        3. 중복 컬럼 제거
        """
        logger.info("출력 표준화 시작...")
        
        # 1. 컬럼명 정규화
        column_mapping = {
            'RATE SORUCE': 'RATE SOURCE',
            'TOTAL(USD)': 'TOTAL (USD)',
            'TOTAL(AED)': 'TOTAL (AED)',
            'Line\u202fTotal (USD)': 'Line Total (USD)',
            'Qty': 'Q\'TY',
            'QTY': 'Q\'TY',
        }
        df = df.rename(columns=column_mapping)
        
        # 2. 중복 컬럼 제거 (같은 이름의 컬럼이 여러 개 있을 경우 첫 번째만 유지)
        df = df.loc[:, ~df.columns.duplicated()]
        
        # 3. 표준 컬럼 순서 정의
        standard_columns = [
            'Source_File',
            'No',
            'Month',
            'CWI Job Number',
            'Order Ref. Number',
            'S/No',
            'DESCRIPTION',
            'RATE SOURCE',
            'RATE',
            'Formula',
            'Q\'TY',
            'TOTAL (USD)',
            'REV RATE',
            'REV TOTAL',
            'DIFFERENCE'
        ]
        
        # 4. 실제 존재하는 표준 컬럼만 필터링
        existing_standard = [col for col in standard_columns if col in df.columns]
        
        # 5. 나머지 컬럼들 (표준 컬럼 제외, 알파벳 순)
        # 타입 불일치 방지: 모두 문자열로 변환 후 정렬
        remaining_columns = sorted([str(col) for col in df.columns if col not in standard_columns])
        
        # 6. 최종 컬럼 순서
        final_column_order = existing_standard + remaining_columns
        
        # 7. 컬럼 순서 재정렬
        df = df[final_column_order]
        
        logger.info(f"✅ 표준화 완료: {len(existing_standard)} 표준 컬럼 + {len(remaining_columns)} 추가 컬럼")
        logger.info(f"   표준 컬럼: {', '.join(existing_standard[:7])}...")
        
        return df


def main():
    """테스트 실행"""
    shpt_folder = Path(__file__).parent.parent / "01_DSV_SHPT" / "SHPT"
    
    if not shpt_folder.exists():
        logger.error(f"SHPT folder not found: {shpt_folder}")
        return
    
    consolidator = MultiMonthConsolidator(shpt_folder)
    df = consolidator.consolidate_all_months()
    
    print(f"\n✅ Test complete!")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns[:10])}...")
    print(f"\nSample (first 3 rows):")
    print(df[['Source_File', 'No', 'Month', 'Order Ref. Number', 'DESCRIPTION']].head(3))


if __name__ == "__main__":
    main()

