"""
Excel 출력 모듈

OFCO INVOICE 형식으로 Excel 파일 생성

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


class ExcelExporter:
    """Excel 출력 클래스"""
    
    def __init__(self):
        """출력 설정 초기화"""
        self.column_order = self._define_column_order()
    
    def _define_column_order(self):
        """컬럼 순서 정의 (153개 컬럼)"""
        return [
            # 기본 정보 (A~L)
            '전체 순번', '청구 회차', 'NO', 'Voyage No', 'SUBJECT',
            'INVOICE NUMBER', 'INVOICE DATE', 'INVOICE DATE_YEAR_MONTH',
            'COST MAIN', 'COST CENTER A', 'COST CENTER B', 'PRICE CENTER',
            
            # CONTRACT 범위 (M:W) - Price Center QTY/AMOUNT
            'AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY',
            'AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT',
            'AGENCY_FEE_FOR_BERTHING_ARRANGEMENT_QTY',
            'AGENCY_FEE_FOR_BERTHING_ARRANGEMENT_AMOUNT',
            'AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT_QTY',
            'AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT_AMOUNT',
            'AGENCY_FOR_ARRANGEMENT_PTW_QTY',
            'AGENCY_FOR_ARRANGEMENT_PTW_AMOUNT',
            'YARD_QTY',
            'YARD_AMOUNT',
            'OFCO_HANDLING_FEE_QTY',
            'OFCO_HANDLING_FEE_AMOUNT',
            
            # AT COST 범위 (Y:AG)
            'SUPPLY_WATER_5001IG_QTY',
            'SUPPLY_WATER_5001IG_AMOUNT',
            'FORKLIFT_HIRE_CHARGE_QTY',
            'FORKLIFT_HIRE_CHARGE_AMOUNT',
            'FORKLIFT_MOB_DE_MOB_CHARGE_QTY',
            'FORKLIFT_MOB_DE_MOB_CHARGE_AMOUNT',
            'CONSUMABLES_QTY',
            'CONSUMABLES_AMOUNT',
            'DIESEL_VESSEL_QTY',
            'DIESEL_VESSEL_AMOUNT',
            
            # PORT HANDLING 범위 (AI:CU) - 일부만 표시
            'DOCUMENT_PROCESSING_CHARGE_QTY',
            'DOCUMENT_PROCESSING_CHARGE_AMOUNT',
            'BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY_QTY',
            'BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY_AMOUNT',
            'CHANNEL_TRANSIT_CROSSING_REQUEST_QTY',
            'CHANNEL_TRANSIT_CROSSING_REQUEST_AMOUNT',
            'PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT_QTY',
            'PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT_AMOUNT',
            'PILOTAGE_QTY',
            'PILOTAGE_AMOUNT',
            'GATE_PASS_QTY',
            'GATE_PASS_AMOUNT',
            'PORT_DUE_QTY',
            'PORT_DUE_AMOUNT',
            'MANPOWER_RIGGER_QTY',
            'MANPOWER_RIGGER_AMOUNT',
            'MANPOWER_BANKSMAN_QTY',
            'MANPOWER_BANKSMAN_AMOUNT',
            'MANPOWER_SUPERVISOR_QTY',
            'MANPOWER_SUPERVISOR_AMOUNT',
            'EQUIPMENT_75TON_CRANE_QTY',
            'EQUIPMENT_75TON_CRANE_AMOUNT',
            'EQUIPMENT_150TON_CRANE_QTY',
            'EQUIPMENT_150TON_CRANE_AMOUNT',
            'OTHERS_QTY',
            'OTHERS_AMOUNT',
            
            # 통화 집계 (CW:CZ)
            'Total_Amount_AED',
            'Amount_USD',
            'VAT_USD',
            'Total_Amount_USD',
            
            # EA Slots (DA:DH)
            'EA_1_Qty',
            'EA_1_Rate',
            'EA_2_Qty',
            'EA_2_Rate',
            'EA_3_Qty',
            'EA_3_Rate',
            'EA_4_Qty',
            'EA_4_Rate',
            
            # EA Amounts
            'EA_1_Amount',
            'EA_2_Amount',
            'EA_3_Amount',
            'EA_4_Amount',
            'EA_Total_Amount',
            
            # 검증 컬럼
            'calc_check',
            'calc_status',
            'calc_diff',
            'calc_diff_pct',
            'vat_check',
            'vat_diff',
            'expected_vat',
            'pc_check',
            'pc_sum',
            'pc_diff',
            'total_check',
            'total_diff',
            'expected_total',
        ]
    
    def export(self, df: pd.DataFrame, output_path: Path):
        """
        DataFrame을 Excel 파일로 출력
        
        Parameters:
            df (pd.DataFrame): 출력할 DataFrame
            output_path (Path): 출력 파일 경로
        """
        # 출력 디렉토리 생성
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 백업 생성 (기존 파일이 있는 경우)
        if output_path.exists():
            backup_path = output_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
            output_path.rename(backup_path)
            print(f"Backup created: {backup_path}")
        
        # 컬럼 순서 정렬 (존재하는 컬럼만)
        ordered_cols = [col for col in self.column_order if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in ordered_cols]
        final_cols = ordered_cols + remaining_cols
        
        df_export = df[final_cols].copy()
        
        # Excel 출력
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Sheet1', index=False)
            
            # 워크시트 가져오기
            worksheet = writer.sheets['Sheet1']
            
            # 컬럼 너비 자동 조정
            for idx, col in enumerate(df_export.columns, 1):
                max_length = max(
                    df_export[col].astype(str).map(len).max(),
                    len(str(col))
                )
                adjusted_width = min(max_length + 2, 50)  # 최대 50
                worksheet.column_dimensions[self._get_column_letter(idx)].width = adjusted_width
        
        print(f"Excel file exported: {output_path}")
        print(f"Total rows: {len(df_export)}")
        print(f"Total columns: {len(df_export.columns)}")
    
    def _get_column_letter(self, n: int) -> str:
        """컬럼 번호를 Excel 레터로 변환 (1-based)"""
        result = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            result = chr(65 + remainder) + result
        return result
