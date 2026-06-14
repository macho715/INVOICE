#!/usr/bin/env python3
"""
Price Center to Column Auto-Mapping System v2
K~CT 범위(10-97번) 분석 기반 개선된 매핑 로직
PDF 파싱 결과의 Price Center 값을 기준으로 ofco.xlsx 형식의 개별 컬럼에 자동 할당
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher


class PriceCenterMapper:
    """
    Price Center 값을 기준으로 개별 QTY/AMOUNT 컬럼에 자동 매핑하는 클래스
    """

    def __init__(self, mapping_file: str = 'price_center_column_mapping.json', excel_path: str = '../templates/ofco.xlsx'):
        """
        PriceCenterMapper 초기화

        Args:
            mapping_file: Price Center → Column 매핑 사전 파일 경로
            excel_path: Excel 템플릿 파일 경로 (기본값: ../templates/ofco.xlsx)
        """
        self.mapping_file = mapping_file
        self.excel_path = excel_path
        self.mapping_dict = {}
        self.individual_columns = []
        self.logger = self._setup_logger()

        # 특수 케이스 매핑 사전 (K~CT 범위 분석 기반)
        self.special_cases = {
            'SUPPLY WATER 5000IG': 'SUPPLY_WATER_5001IG',  # 이름 변형
            'HANDLING FEE': 'OFCO_HANDLING_FEE_PORT_HANDLING_CHARGE_10',
            'CRANE': 'EQUIPMENT_75TON_CRANE',  # 기본값
            '75TON CRANE': 'EQUIPMENT_75TON_CRANE',
            '100TON CRANE': 'EQUIPMENT_100TON_CRAN',
            '150TON CRANE': 'EQUIPMENT_150TON_CRANE',
            'FORKLIFT': 'FORKLIFT_HIRE_CHARGE',
            'FORKLIFT MOB/DE-MOB': 'FORKLIFT_MOB_DE_MOB_CHARGE',
            'Banksman': 'MANPOWER_BANKSMAN',
            'Foreman': 'MANPOWER_FOREMAN',
            'Rigger': 'MANPOWER_RIGGER',
            'Supervisor': 'MANPOWER_SUPERVISOR',
            'Spread Beam': 'EQUIPMENT_SPREAD',
            'PASS ARRANGEMENT': 'GATE_PASS',
            'DECK MAINTENANCE': 'CONSUMABLES',
            'WATER SUPPLY': 'SUPPLY_WATER_5001IG',
            'WASTE HANDLING': 'WASTE_HANDLING',
            'WASTE HANDLING 2': 'WASTE_HANDLING2',
            'PORT DUES': 'PORT_DUE',
            'PORT DUES CARGO': 'PORT_DUE_CARGO',
            'PORT DUES VESSEL': 'PORT_DUES_FOR_VESSELS_WITH_ABOVE_1_000_UP_TO_3_001GT',
            'BERTHING/SHIFTING': 'BERTHING_SHIFTING',
            'PILOTAGE': 'PILOTAGE',
            'PILOT LAUNCH': 'PILOT_LAUNCH',
            'GENERAL CARGO': 'GENERAL_CARGO',
            'BUNKERING': 'BUNKERING',
            'BUNKERING PERMIT': 'BUNKERING_LUBE_OIL_SLUDGE_SULPHUR_BILGE_TRANSFER_BUNKERING_PERMIT',
            'HEAVY LIFT': 'HEAVY_LIFT_20FRT_PROJECT',
            'ANCHORAGE FEES': 'ANCHORAGE_FEES_FOR_NON_CARGO_VESSELS',
            'CHANNEL TRANSIT': 'CHANNEL_TRANSIT_CROSSING_REQUEST',
            'CHANNEL CROSSING': 'CHANNEL_CROSSING_CHARGES_FOR_VESSELS_WITH_1000_TO_3_001_GT',
            'GENERAL WASTE': 'GENERAL_WASTE_SERVICE',
            'PEC CHANGES': 'PEC_CHANGES',
            'DIESEL VESSEL': 'DIESEL_VESSEL',
            'DOCUMENT PROCESSING': 'DOCUMENT_PROCESSING_CHARGE',
            'BULK MATERIAL': 'BULK_MATERIAL_SOLIDS_A_PARCEL_SIZE_0_10_001_TONS_DIRECT_DELIVERY',
            'BULK MATERIAL BAGGED': 'BULK_MATERIAL_BAGGED_CARGO_14',  # 기본값
            'YARD': 'YARD',
            'OTHERS': 'OTHERS'
        }

        # 매핑 사전 로드
        self._load_mapping_dict()

        # 개별 컬럼 목록 생성
        self._generate_individual_columns()

    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger('PriceCenterMapper')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_mapping_dict(self):
        """매핑 사전 로드 (참고용)"""
        try:
            if Path(self.mapping_file).exists():
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.mapping_dict = json.load(f)
                self.logger.info(f"매핑 사전 로드 완료: {len(self.mapping_dict)}개 패턴")
            else:
                self.logger.warning(f"매핑 사전 파일이 없습니다: {self.mapping_file}")
                self.mapping_dict = {}
        except Exception as e:
            self.logger.error(f"매핑 사전 로드 실패: {e}")
            self.mapping_dict = {}

    def _generate_individual_columns(self):
        """개별 QTY/AMOUNT 컬럼 목록 생성 (K~CT 범위: 10-97번)"""
        # ofco.xlsx에서 실제 컬럼명 추출
        try:
            df = pd.read_excel(self.excel_path, nrows=0)
            all_cols = df.columns.tolist()

            # 10-97번 컬럼 (K~CT 범위)
            self.individual_columns = []
            for i in range(10, 98):
                if i < len(all_cols):
                    col = all_cols[i]
                    if '_QTY' in col or '_AMOUNT' in col:
                        # 기본 이름 추출 (QTY/AMOUNT 제거)
                        base_name = col.replace('_QTY', '').replace('_AMOUNT', '')
                        if base_name not in self.individual_columns:
                            self.individual_columns.append(base_name)

            self.logger.info(f"개별 컬럼 목록 생성: {len(self.individual_columns)}개")

        except Exception as e:
            self.logger.error(f"개별 컬럼 목록 생성 실패: {e}")
            # 기본 목록 사용
            self.individual_columns = [
                'AGENCY_FEE_FOR_CARGO_CLEARANCE',
                'AGENCY_FEE_FOR_BERTHING_ARRANGEMENT',
                'AGENCY_FEE_FOR_FW_SUPPLY_ARRANGEMENT',
                'AGENCY_FOR_ARRANGEMENT_PTW',
                'YARD',
                'OFCO_HANDLING_FEE_PORT_HANDLING_CHARGE_10',
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
                'OTHERS'
            ]

    def direct_name_match(self, price_center: str) -> Optional[str]:
        """이름 기반 직접 매칭 (최우선)"""
        # Price Center 이름을 컬럼명으로 변환
        normalized = price_center.upper().replace(' ', '_')

        # 정확히 일치하는 컬럼 찾기
        for col in self.individual_columns:
            if col == normalized:
                return col

        # 부분 일치 (포함 관계)
        for col in self.individual_columns:
            if normalized in col or col in normalized:
                return col

        return None

    def similarity_match(self, price_center: str, threshold: float = 0.7) -> Optional[str]:
        """유사도 기반 매칭"""
        normalized = price_center.upper().replace(' ', '_')
        best_match = None
        best_score = 0.0

        for col in self.individual_columns:
            score = SequenceMatcher(None, normalized, col).ratio()
            if score > best_score and score > threshold:
                best_score = score
                best_match = col

        return best_match

    def map_price_center_to_column(self, price_center: str) -> str:
        """Price Center를 개별 컬럼으로 매핑 (우선순위 적용)"""
        if not price_center or pd.isna(price_center):
            return 'OTHERS'

        price_center = str(price_center).strip()

        # 1순위: 특수 케이스
        if price_center in self.special_cases:
            mapped = self.special_cases[price_center]
            self.logger.debug(f"특수 케이스 매핑: {price_center} → {mapped}")
            return mapped

        # 2순위: 직접 이름 매칭
        direct = self.direct_name_match(price_center)
        if direct:
            self.logger.debug(f"직접 매칭: {price_center} → {direct}")
            return direct

        # 3순위: 유사도 매칭
        similar = self.similarity_match(price_center)
        if similar:
            self.logger.debug(f"유사도 매칭: {price_center} → {similar}")
            return similar

        # 4순위: 기존 매핑 사전 (빈도 기반)
        if price_center in self.mapping_dict:
            mapped = self.mapping_dict[price_center][0]  # 첫 번째
            self.logger.debug(f"사전 매핑: {price_center} → {mapped}")
            return mapped

        # 최종: OTHERS
        self.logger.debug(f"OTHERS 매핑: {price_center} → OTHERS")
        return 'OTHERS'

    def map_row(self, row_data: Dict) -> Dict[str, float]:
        """
        단일 행 데이터를 매핑하여 개별 컬럼 값 반환 (개선된 로직)

        Args:
            row_data: 행 데이터 딕셔너리 (Price Center, EA, Amount 포함)

        Returns:
            dict: {column_name_qty: qty_value, column_name_amount: amount_value, ...}
        """
        price_center = row_data.get('Price Center', '')
        ea = float(row_data.get('EA', 0) or 0)
        amount = float(row_data.get('Amount', 0) or 0)

        if not price_center or pd.isna(price_center):
            # Price Center가 없으면 OTHERS 컬럼에 할당
            return {
                'OTHERS_QTY': ea,
                'OTHERS_AMOUNT': amount
            }

        # 새로운 우선순위 로직으로 Price Center 매핑
        mapped_column = self.map_price_center_to_column(price_center)

        result = {}
        result[f'{mapped_column}_QTY'] = ea
        result[f'{mapped_column}_AMOUNT'] = amount

        self.logger.debug(f"매핑 완료: {price_center} -> {mapped_column} (EA: {ea}, Amount: {amount})")

        return result

    def apply_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전체 DataFrame에 매핑 적용

        Args:
            df: 입력 DataFrame (Price Center, EA, Amount 컬럼 포함)

        Returns:
            pd.DataFrame: 개별 컬럼이 추가된 DataFrame
        """
        self.logger.info(f"DataFrame 매핑 시작: {len(df)} rows")

        # 결과를 저장할 딕셔너리
        mapping_results = {}

        # 모든 가능한 컬럼명 수집
        all_columns = set()
        for _, row in df.iterrows():
            row_result = self.map_row(row.to_dict())
            all_columns.update(row_result.keys())

        # 모든 컬럼을 0으로 초기화
        for col in all_columns:
            mapping_results[col] = [0.0] * len(df)

        # 각 행에 대해 매핑 적용
        for idx, row in df.iterrows():
            row_result = self.map_row(row.to_dict())
            for col, value in row_result.items():
                mapping_results[col][idx] = value

        # 결과를 DataFrame에 추가
        result_df = df.copy()
        for col, values in mapping_results.items():
            result_df[col] = values

        # 매핑 통계 출력
        self._print_mapping_stats(result_df)

        return result_df

    def _print_mapping_stats(self, df: pd.DataFrame):
        """매핑 통계 출력"""
        # 개별 컬럼 중 값이 있는 컬럼들 찾기
        individual_cols = [col for col in df.columns if isinstance(col, str) and (col.endswith('_QTY') or col.endswith('_AMOUNT'))]

        used_columns = []
        for col in individual_cols:
            if df[col].sum() > 0:
                used_columns.append(col)

        self.logger.info(f"사용된 개별 컬럼: {len(used_columns)}개")
        for col in sorted(used_columns):
            total_value = df[col].sum()
            self.logger.info(f"  {col}: {total_value:,.2f}")

    def get_mapping_summary(self) -> Dict:
        """매핑 사전 요약 정보 반환"""
        return {
            'total_patterns': len(self.mapping_dict),
            'patterns': list(self.mapping_dict.keys()),
            'mapping_file': self.mapping_file
        }


def test_price_center_mapper():
    """PriceCenterMapper 테스트 (개선된 로직)"""
    print("PriceCenterMapper v2 테스트 시작...")

    # 테스트 데이터 생성
    test_data = {
        'Price Center': [
            'AGENCY FEE FOR CARGO CLEARANCE',
            'SUPPLY WATER 5000IG',
            'CHANNEL TRANSIT CHARGES',
            'FORKLIFT',
            'CRANE',
            'BULK MATERIAL',
            'DOCUMENT PROCESSING CHARGE',
            'HANDLING FEE',
            'Banksman',
            'UNKNOWN PRICE CENTER'
        ],
        'EA': [1.0, 1.0, 2.0, 1.0, 1.0, 600.0, 1.0, 1.0, 1.0, 1.0],
        'Amount': [500.0, 454.6, 5401.23, 115.72, 200.0, 3900.0, 35.0, 100.0, 150.0, 100.0]
    }

    test_df = pd.DataFrame(test_data)
    print("테스트 데이터:")
    print(test_df)

    # 매퍼 초기화 및 적용
    mapper = PriceCenterMapper()

    # 개별 매핑 테스트
    print("\n개별 매핑 테스트:")
    for idx, row in test_df.iterrows():
        pc = row['Price Center']
        mapped = mapper.map_price_center_to_column(pc)
        print(f"  {pc:30} → {mapped}")

    # 전체 DataFrame 적용
    result_df = mapper.apply_to_dataframe(test_df)

    print("\n매핑 결과:")
    # 개별 컬럼만 출력
    individual_cols = [col for col in result_df.columns if col.endswith('_QTY') or col.endswith('_AMOUNT')]
    print(result_df[['Price Center', 'EA', 'Amount'] + individual_cols])

    # 매핑 요약
    summary = mapper.get_mapping_summary()
    print(f"\n매핑 사전 요약: {summary['total_patterns']}개 패턴")


if __name__ == '__main__':
    test_price_center_mapper()
