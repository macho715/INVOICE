"""
OFCO 월간 인보이스 자동 처리 시스템

기능:
1. SAFEEN/ADP/OFCO PDF 인보이스 자동 파싱
2. COST CENTER 자동 매핑
3. Price Center Pivot 자동 생성
4. EA Slot 자동 분해
5. 3중 검증 (calc_check, vat_check, pc_check)
6. Excel 파일 출력

사용법:
    python monthly_invoice_processor.py --month 2024-11 --input-dir ./invoices --output OFCO_INVOICE_2024_11.xlsx

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Tuple

# 로컬 모듈 임포트
from invoice_parsers import SAFEENParser, ADPParser, OFCOParser
from cost_center_mapping import CostCenterMapper
from ea_slot_decomposer import EASlotDecomposer
from validation_engine import ValidationEngine
from excel_exporter import ExcelExporter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonthlyInvoiceProcessor:
    """월간 인보이스 자동 처리 클래스"""
    
    def __init__(self, month: str, input_dir: str, output_path: str):
        """
        Parameters:
            month (str): 처리 월 (YYYY-MM 형식)
            input_dir (str): 인보이스 PDF 디렉토리
            output_path (str): 출력 Excel 파일 경로
        """
        self.month = month
        self.input_dir = Path(input_dir)
        self.output_path = Path(output_path)
        
        # 모듈 초기화
        self.safeen_parser = SAFEENParser()
        self.adp_parser = ADPParser()
        self.ofco_parser = OFCOParser()
        self.cost_mapper = CostCenterMapper()
        self.ea_decomposer = EASlotDecomposer()
        self.validator = ValidationEngine()
        self.exporter = ExcelExporter()
        
        # 데이터 저장소
        self.df_master = None
        self.invoice_lines = []
        
    def run(self):
        """전체 파이프라인 실행"""
        logger.info(f"Starting monthly invoice processing for {self.month}")
        
        try:
            # Step 1: PDF 파일 스캔
            pdf_files = self._scan_pdf_files()
            logger.info(f"Found {len(pdf_files)} PDF files")
            
            # Step 2: 각 PDF 파싱
            for pdf_file in pdf_files:
                self._process_single_pdf(pdf_file)
            
            # Step 3: DataFrame 생성
            self.df_master = pd.DataFrame(self.invoice_lines)
            logger.info(f"Created DataFrame with {len(self.df_master)} lines")
            
            # Step 4: COST CENTER 매핑
            self.df_master = self.cost_mapper.map_all(self.df_master)
            
            # Step 5: Price Center Pivot 생성
            self.df_master = self._create_price_center_pivot(self.df_master)
            
            # Step 6: EA Slot 분해
            self.df_master = self.ea_decomposer.decompose_all(self.df_master)
            
            # Step 7: 검증
            self.df_master = self.validator.validate_all(self.df_master)
            
            # Step 8: Excel 출력
            self.exporter.export(self.df_master, self.output_path)
            
            # Step 9: 결과 리포트
            self._print_summary()
            
            logger.info(f"Successfully completed. Output: {self.output_path}")
            
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}", exc_info=True)
            raise
    
    def _scan_pdf_files(self) -> List[Path]:
        """입력 디렉토리에서 PDF 파일 스캔"""
        pdf_files = list(self.input_dir.glob('*.pdf'))
        pdf_files.sort()
        return pdf_files
    
    def _process_single_pdf(self, pdf_file: Path):
        """개별 PDF 파일 처리"""
        logger.info(f"Processing: {pdf_file.name}")
        
        # 파일명 기반 파서 선택
        if 'SAFEEN' in pdf_file.name.upper():
            parser = self.safeen_parser
        elif 'ADP' in pdf_file.name.upper() or 'ABU_DHABI_PORTS' in pdf_file.name.upper():
            parser = self.adp_parser
        elif 'OFCO' in pdf_file.name.upper():
            parser = self.ofco_parser
        else:
            logger.warning(f"Unknown PDF type: {pdf_file.name}, trying OFCO parser")
            parser = self.ofco_parser
        
        # 파싱 실행
        try:
            lines = parser.parse(pdf_file)
            self.invoice_lines.extend(lines)
            logger.info(f"  Parsed {len(lines)} lines from {pdf_file.name}")
        except Exception as e:
            logger.error(f"  Failed to parse {pdf_file.name}: {str(e)}")
    
    def _create_price_center_pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price Center Pivot 생성 (44개 Price Center → 88개 컬럼)"""
        logger.info("Creating Price Center Pivot...")
        
        # 44개 Price Center 정의
        price_centers = [
            'AGENCY_FEE_FOR_CARGO_CLEARANCE',
            'AGENCY_FEE_FOR_BERTHING_ARRANGEMENT',
            'AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT',
            'AGENCY_FOR_ARRANGEMENT_PTW',
            'YARD',
            'OFCO_HANDLING_FEE',
            'SUPPLY_WATER_5001IG',
            'FORKLIFT_HIRE_CHARGE',
            'FORKLIFT_MOB_DE_MOB_CHARGE',
            'CONSUMABLES',
            'DIESEL_VESSEL',
            'DOCUMENT_PROCESSING_CHARGE',
            'BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY',
            'BULK_MATERIAL_BAGGED_CARGO_14',
            'BULK_MATERIAL_BAGGED_CARGO_15',
            'BULK_MATERIAL_BAGGED_CARGO_16',
            'BULK_MATERIAL_BAGGED_CARGO_19',
            'PEC_CHANGES',
            'ANCHORAGE_FEES_FOR_NON_CARGO_VESSELS',
            'CHANNEL_TRANSIT_CROSSING_REQUEST',
            'CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT',
            'GENERAL_WASTE_SERVICE',
            'PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT',
            'BUNKERING_LUBE_OIL_SLUDGE_SULPHUR_BILGE_TRANSFER_BUNKERING_PERMIT',
            'PORT_DUE_CARGO',
            'WASTE_HANDLING',
            'BERTHING_SHIFTING',
            'PILOTAGE',
            'PILOT_LAUNCH',
            'GENERAL_CARGO',
            'GATE_PASS',
            'PORT_DUE',
            'WASTE_HANDLING2',
            'BUNKERING',
            'HEAVY_LIFT_20FRT_PROJECT',
            'MANPOWER_RIGGER',
            'MANPOWER_BANKSMAN',
            'MANPOWER_FOREMAN',
            'MANPOWER_SUPERVISOR',
            'EQUIPMENT_75TON_CRANE',
            'EQUIPMENT_100TON_CRAN',
            'EQUIPMENT_150TON_CRANE',
            'EQUIPMENT_SPREAD',
            'OTHERS',
        ]
        
        # 각 Price Center에 대해 QTY/AMOUNT 컬럼 초기화
        for pc in price_centers:
            df[f'{pc}_QTY'] = np.nan
            df[f'{pc}_AMOUNT'] = np.nan
        
        # PRICE CENTER 값에 따라 해당 컬럼에 값 할당
        for idx, row in df.iterrows():
            price_center = row.get('PRICE CENTER', '')
            qty = row.get('Qty', 1.0)
            amount = row.get('Total_Amount_AED', 0.0)
            
            # Price Center 이름 정규화 (공백 제거, 대문자 변환, 언더스코어 변환)
            pc_normalized = price_center.upper().replace(' ', '_')
            
            # 매칭되는 Price Center 컬럼 찾기
            for pc in price_centers:
                if pc in pc_normalized or pc_normalized in pc:
                    df.at[idx, f'{pc}_QTY'] = qty
                    df.at[idx, f'{pc}_AMOUNT'] = amount
                    break
        
        return df
    
    def _print_summary(self):
        """처리 결과 요약 출력"""
        logger.info("\n" + "="*80)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\nTotal Lines: {len(self.df_master)}")
        logger.info(f"Month: {self.month}")
        
        logger.info("\nCOST MAIN Distribution:")
        for cost_main, count in self.df_master['COST MAIN'].value_counts().items():
            logger.info(f"  {cost_main}: {count} lines ({count/len(self.df_master)*100:.1f}%)")
        
        logger.info("\nValidation Results:")
        calc_pass = self.df_master['calc_check'].isna().sum()
        vat_pass = self.df_master['vat_check'].isna().sum()
        pc_pass = self.df_master['pc_check'].isna().sum()
        
        logger.info(f"  calc_check: {calc_pass}/{len(self.df_master)} PASS ({calc_pass/len(self.df_master)*100:.1f}%)")
        logger.info(f"  vat_check: {vat_pass}/{len(self.df_master)} PASS ({vat_pass/len(self.df_master)*100:.1f}%)")
        logger.info(f"  pc_check: {pc_pass}/{len(self.df_master)} PASS ({pc_pass/len(self.df_master)*100:.1f}%)")
        
        total_amount = self.df_master['Total_Amount_AED'].sum()
        logger.info(f"\nTotal Amount: {total_amount:,.2f} AED")
        
        logger.info("="*80 + "\n")


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description='OFCO Monthly Invoice Processor')
    parser.add_argument('--month', required=True, help='Processing month (YYYY-MM)')
    parser.add_argument('--input-dir', required=True, help='Input PDF directory')
    parser.add_argument('--output', required=True, help='Output Excel file path')
    
    args = parser.parse_args()
    
    processor = MonthlyInvoiceProcessor(
        month=args.month,
        input_dir=args.input_dir,
        output_path=args.output
    )
    
    processor.run()


if __name__ == '__main__':
    main()
