"""
OFCO 인보이스 자동 처리 시스템 - 설정 파일
작성자: MACHO-GPT v3.4-mini
작성일: 2025-11-10
"""

# Excel 컬럼 범위 정의
COLUMN_RANGES = {
    'CONTRACT': {
        'start': 12,  # M (AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY)
        'end': 23,    # X (OFCO_HANDLING_FEE_AMOUNT)
        'excel': 'L:W',
        'description': 'CONTRACT 관련 Price Center'
    },
    'AT_COST': {
        'start': 24,  # Y (SUPPLY_WATER_5001IG_QTY)
        'end': 33,    # AH (DIESEL_VESSEL_AMOUNT)
        'excel': 'X:AG',
        'description': 'AT COST 관련 Price Center'
    },
    'PORT_HANDLING': {
        'start': 33,  # AH (DIESEL_VESSEL_AMOUNT)
        'end': 99,    # CV (OTHERS_AMOUNT)
        'excel': 'AH:CU',
        'description': 'PORT HANDLING CHARGE 관련 Price Center'
    },
    'EA_SLOTS': {
        'start': 104,  # DA (EA_1_Qty)
        'end': 111,    # DH (EA_4_Rate)
        'excel': 'CZ:DG',
        'description': 'EA (RatePair) 슬롯'
    }
}

# COST CENTER A → Price Center 매핑
COST_CENTER_MAPPING = {
    'CONTRACT': {
        'cost_center_a': 'CONTRACT',
        'price_centers': [
            'AGENCY FEE FOR CARGO CLEARANCE',
            'AGENCY FEE FOR BERTHING ARRANGEMENT',
            'AGENCY FEE FOR FW SUPPLY ARRANGEMENT',
            'AGENCY FOR ARRANGEMENT PTW',
            'YARD',
            'OFCO HANDLING FEE',
        ],
        'column_range': 'L:W'
    },
    'AT COST': {
        'cost_center_a': 'AT COST',
        'price_centers': [
            'SUPPLY WATER 5000IG',
            'FOLK LIFT HIRE CHARGE',
            'FORKLIFT MOB/DE-MOB CHARGE',
            'CONSUMABLES',
            'DIESEL VESSEL',
        ],
        'column_range': 'X:AG'
    },
    'PORT HANDLING CHARGE': {
        'cost_center_a': 'PORT HANDLING CHARGE',
        'price_centers': [
            'DOCUMENT PROCESSING CHARGE',
            'BULK MATERIAL',
            'PEC CHANGES',
            'ANCHORAGE FEES FOR NON CARGO VESSELS',
            'CHANNEL TRANSIT CHARGES',
            'GENERAL WASTE SERVICE',
            'PORT DUES',
            'BUNKERING',
            'BERTHING SHIFTING',
            'PILOTAGE',
            'PILOT LAUNCH',
            'GENERAL CARGO',
            'GATE PASS',
            'WASTE HANDLING',
            'HEAVY LIFT 20FRT PROJECT',
            'Rigger',
            'Banksman',
            'Foreman',
            'Supervisor',
            '75TON CRANE',
            '100TON CRANE',
            '150TON CRANE',
            'Spread Beam',
            'OTHERS',
        ],
        'column_range': 'AH:CU'
    }
}

# SAFEEN 인보이스 패턴 매핑
SAFEEN_PATTERNS = {
    'subject_keywords': ['SAFEEN', 'Channel Crossing', 'Channel Transit'],
    'cost_main': 'PORT HANDLING',
    'cost_center_a': 'PORT HANDLING CHARGE',
    'cost_center_b': 'CHANNEL TRANSIT CHARGES',
    'default_price_center': 'CHANNEL TRANSIT CHARGES',
    'ea_template': 'CHANNEL_CROSSING_3WAY',  # 3-way EA split
}

# ADP 인보이스 패턴 매핑
ADP_PATTERNS = {
    'subject_keywords': ['ADP', 'ABU DHABI PORTS', 'Port Dues', 'Pilotage'],
    'cost_main': 'PORT HANDLING',
    'cost_center_a': 'PORT HANDLING CHARGE',
    'cost_center_b_variants': {
        'PORT DUES': 'PORT DUES & SERVICES CHARGES',
        'BULK': 'BULK CARGO HANDLING CHARGES',
        'PILOTAGE': 'PORT HANDLING CHARGE',
    },
    'price_center_mapping': {
        'PORT DUES': 'PORT DUES',
        'BULK MATERIAL': 'BULK MATERIAL',
        'PILOTAGE': 'Pilotage',
        'GATE PASS': 'GATE PASS',
    },
    'ea_template': 'PORT_DUES_SIMPLE',  # Simple 1-way EA
}

# OFCO 자체 인보이스 패턴
OFCO_PATTERNS = {
    'subject_keywords': ['OFCO', 'Agency Fee', 'Cargo Clearance', 'Berthing Arrangement'],
    'cost_main': 'CONTRACT',
    'cost_center_a': 'CONTRACT',
    'cost_center_b_variants': {
        'CARGO CLEARANCE': 'AF FOR CC',
        'BERTHING': 'AF FOR BA',
        'FW SUPPLY': 'AF FOR FW SA',
    },
    'price_center_mapping': {
        'CARGO CLEARANCE': 'AGENCY FEE FOR CARGO CLEARANCE',
        'BERTHING': 'AGENCY FEE FOR BERTHING ARRANGEMENT',
        'FW SUPPLY': 'SUPPLY WATER 5000IG',
    },
    'ea_template': 'AGENCY_FEE_1WAY',  # Simple 1-way EA
}

# EA 템플릿 정의
EA_TEMPLATES = {
    'CHANNEL_CROSSING_3WAY': {
        'description': 'SAFEEN Channel Crossing - 3-way split',
        'slots': 3,
        'example': {
            'EA_1': {'Qty': 2.0, 'Rate': 3091.25, 'Description': 'Main Charge'},
            'EA_2': {'Qty': 2.0, 'Rate': 100.00, 'Description': 'Service Fee'},
            'EA_3': {'Qty': 1.0, 'Rate': 239.00, 'Description': 'Additional'},
        }
    },
    'PORT_DUES_SIMPLE': {
        'description': 'ADP Port Dues - Simple',
        'slots': 1,
        'example': {
            'EA_1': {'Qty': 1.0, 'Rate': 'Amount', 'Description': 'Full Amount'},
        }
    },
    'AGENCY_FEE_1WAY': {
        'description': 'OFCO Agency Fee - Simple',
        'slots': 1,
        'example': {
            'EA_1': {'Qty': 1.0, 'Rate': 'Amount', 'Description': 'Full Amount'},
        }
    },
    'MANPOWER_VARIABLE': {
        'description': 'Manpower - Variable hours',
        'slots': 1,
        'example': {
            'EA_1': {'Qty': 'hours', 'Rate': 'hourly_rate', 'Description': 'Manpower Cost'},
        }
    },
    'EQUIPMENT_VARIABLE': {
        'description': 'Equipment Hire - Variable hours',
        'slots': 1,
        'example': {
            'EA_1': {'Qty': 'hours', 'Rate': 'hourly_rate', 'Description': 'Equipment Cost'},
        }
    }
}

# 통화 설정
CURRENCY_CONFIG = {
    'base_currency': 'AED',
    'exchange_rates': {
        'USD': 3.6725,  # 1 USD = 3.6725 AED (고정 환율)
    },
    'vat_rate': 0.05,  # 5% UAE VAT
}

# 검증 규칙
VALIDATION_RULES = {
    'calc_check': {
        'tolerance': 0.02,  # ±2.00% 허용
        'description': 'EA 계산 검증: Σ(EA_i) ≈ Total_Amount_AED'
    },
    'vat_check': {
        'tolerance': 0.01,  # ±0.01 USD 허용
        'description': 'VAT 검증: VAT_USD ≈ Amount_USD × 5%'
    },
    'pc_check': {
        'tolerance': 1.00,  # ±1.00 AED 허용
        'description': 'Price Center 합계 검증'
    }
}

# 파일 경로 설정
FILE_PATHS = {
    'input_dir': r'C:\pipeline_execution_scripts\data',
    'output_dir': r'C:\pipeline_execution_scripts\ofco_monthly_invoice\output',
    'log_dir': r'C:\pipeline_execution_scripts\ofco_monthly_invoice\logs',
    'template': r'C:\pipeline_execution_scripts\OFCO INVOICE.xlsx',
}

# 로깅 설정
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
}

# 처리 옵션
PROCESSING_OPTIONS = {
    'auto_fix_calc_warnings': True,  # calc_check 경고 자동 수정
    'auto_fill_missing_ea': True,    # 누락된 EA 자동 채우기
    'generate_validation_report': True,  # 검증 리포트 생성
    'backup_original': True,  # 원본 백업
}
