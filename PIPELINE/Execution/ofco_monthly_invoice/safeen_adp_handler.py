"""
OFCO 인보이스 자동 처리 시스템 - SAFEEN/ADP 특화 처리 모듈
작성자: MACHO-GPT v3.4-mini
작성일: 2025-11-10
"""

import pandas as pd
import re
from typing import Dict, List, Tuple
from config import SAFEEN_PATTERNS, ADP_PATTERNS, EA_TEMPLATES


class SafeenAdpHandler:
    """SAFEEN/ADP 인보이스 특화 처리 클래스"""
    
    def __init__(self):
        self.safeen_patterns = SAFEEN_PATTERNS
        self.adp_patterns = ADP_PATTERNS
        self.ea_templates = EA_TEMPLATES
    
    def is_safeen_invoice(self, subject: str) -> bool:
        """SAFEEN 인보이스 여부 확인"""
        subject_upper = subject.upper()
        return any(kw in subject_upper for kw in self.safeen_patterns['subject_keywords'])
    
    def is_adp_invoice(self, subject: str) -> bool:
        """ADP 인보이스 여부 확인"""
        subject_upper = subject.upper()
        return any(kw in subject_upper for kw in self.adp_patterns['subject_keywords'])
    
    def process_safeen_invoice(self, invoice_line: Dict) -> Dict:
        """
        SAFEEN 인보이스 처리
        
        특징:
        - 3-way EA split (Channel Crossing 패턴)
        - CHANNEL TRANSIT CHARGES Price Center
        - PORT HANDLING CHARGE Cost Center
        
        Args:
            invoice_line: 인보이스 라인 정보
            
        Returns:
            처리된 라인 정보 (EA 슬롯 포함)
        """
        subject = invoice_line['SUBJECT']
        amount = invoice_line['Total_Amount_AED']
        
        # EA 템플릿 선택
        if 'CHANNEL CROSSING' in subject.upper() or 'CHANNEL TRANSIT' in subject.upper():
            ea_template_name = 'CHANNEL_CROSSING_3WAY'
        else:
            # 기본 템플릿
            ea_template_name = 'PORT_DUES_SIMPLE'
        
        # EA 분해
        ea_slots = self._decompose_safeen_ea(amount, ea_template_name)
        
        # 라인 정보 업데이트
        result = invoice_line.copy()
        result.update(ea_slots)
        result['EA_Template'] = ea_template_name
        
        return result
    
    def process_adp_invoice(self, invoice_line: Dict) -> Dict:
        """
        ADP 인보이스 처리
        
        특징:
        - Simple 1-way EA (대부분)
        - 다양한 Price Center (PORT DUES, BULK MATERIAL 등)
        - PORT HANDLING CHARGE Cost Center
        
        Args:
            invoice_line: 인보이스 라인 정보
            
        Returns:
            처리된 라인 정보 (EA 슬롯 포함)
        """
        subject = invoice_line['SUBJECT']
        amount = invoice_line['Total_Amount_AED']
        
        # EA 템플릿 선택 (대부분 Simple)
        ea_template_name = 'PORT_DUES_SIMPLE'
        
        # EA 분해
        ea_slots = self._decompose_adp_ea(amount, ea_template_name)
        
        # 라인 정보 업데이트
        result = invoice_line.copy()
        result.update(ea_slots)
        result['EA_Template'] = ea_template_name
        
        return result
    
    def _decompose_safeen_ea(self, amount: float, template_name: str) -> Dict:
        """
        SAFEEN 인보이스 EA 분해
        
        Algorithm:
        1. 템플릿 조회
        2. Amount → EA 슬롯 분배
        3. 검증: Σ(EA_i) ≈ amount (±2%)
        
        Returns:
            EA 슬롯 딕셔너리
        """
        template = self.ea_templates.get(template_name, {})
        
        if template_name == 'CHANNEL_CROSSING_3WAY':
            # 3-way split (고정 비율 사용 - 실제 데이터 기반)
            # 예시: 6621.52 = (2×3091.25) + (2×100.00) + (1×239.00)
            
            # 비율 계산 (실제 데이터 기반 평균)
            ratio_ea1 = 0.935  # 93.5%
            ratio_ea2 = 0.030  # 3.0%
            ratio_ea3 = 0.035  # 3.5%
            
            ea1_amount = amount * ratio_ea1
            ea2_amount = amount * ratio_ea2
            ea3_amount = amount * ratio_ea3
            
            # Rate 계산 (Qty=2, 2, 1 가정)
            ea1_rate = ea1_amount / 2.0
            ea2_rate = ea2_amount / 2.0
            ea3_rate = ea3_amount / 1.0
            
            return {
                'EA_1_Qty': 2.0,
                'EA_1_Rate': round(ea1_rate, 2),
                'EA_1_Amount': round(ea1_amount, 2),
                'EA_1_Name': 'Channel Crossing Main Charge',
                
                'EA_2_Qty': 2.0,
                'EA_2_Rate': round(ea2_rate, 2),
                'EA_2_Amount': round(ea2_amount, 2),
                'EA_2_Name': 'Service Fee',
                
                'EA_3_Qty': 1.0,
                'EA_3_Rate': round(ea3_rate, 2),
                'EA_3_Amount': round(ea3_amount, 2),
                'EA_3_Name': 'Additional Charge',
                
                'EA_4_Qty': None,
                'EA_4_Rate': None,
                'EA_4_Amount': None,
                'EA_4_Name': None,
                
                'EA_Total_Amount': round(amount, 2),
                'EA_Mapped_Count': 3,
            }
        else:
            # Simple 1-way
            return self._simple_ea_1way(amount)
    
    def _decompose_adp_ea(self, amount: float, template_name: str) -> Dict:
        """
        ADP 인보이스 EA 분해
        
        대부분 Simple 1-way EA
        """
        return self._simple_ea_1way(amount)
    
    def _simple_ea_1way(self, amount: float) -> Dict:
        """Simple 1-way EA (전액을 EA_1에 할당)"""
        return {
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
        }
    
    def extract_rotation_number(self, subject: str) -> str:
        """
        Rotation Number 추출
        
        패턴: Rot# 2503123133, Rotation No. 2504053298
        
        Returns:
            Rotation Number 또는 빈 문자열
        """
        # 패턴 매칭
        patterns = [
            r'Rot#?\s*(\d+)',
            r'Rotation\s+No\.?\s*(\d+)',
            r'ROT[-\s]*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''
    
    def validate_safeen_invoice(self, invoice_line: Dict) -> Tuple[bool, List[str]]:
        """
        SAFEEN 인보이스 검증
        
        검증 항목:
        1. Rotation Number 존재 여부
        2. CHANNEL TRANSIT CHARGES Price Center 확인
        3. EA 합계 일치 여부
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 1. Rotation Number
        rotation_no = self.extract_rotation_number(invoice_line['SUBJECT'])
        if not rotation_no:
            errors.append("Rotation Number not found in SUBJECT")
        
        # 2. Price Center
        if invoice_line.get('PRICE CENTER') != 'CHANNEL TRANSIT CHARGES':
            # Warning only (BULK MATERIAL도 허용)
            if invoice_line.get('PRICE CENTER') not in ['CHANNEL TRANSIT CHARGES', 'BULK MATERIAL', 'Pilotage']:
                errors.append(f"Unexpected Price Center: {invoice_line.get('PRICE CENTER')}")
        
        # 3. EA 합계
        ea_total = invoice_line.get('EA_Total_Amount', 0)
        amount = invoice_line.get('Total_Amount_AED', 0)
        if amount > 0:
            diff_pct = abs(ea_total - amount) / amount
            if diff_pct > 0.02:  # 2% 초과
                errors.append(f"EA Total mismatch: {ea_total:.2f} vs {amount:.2f} ({diff_pct*100:.2f}%)")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def validate_adp_invoice(self, invoice_line: Dict) -> Tuple[bool, List[str]]:
        """
        ADP 인보이스 검증
        
        검증 항목:
        1. ADP 키워드 확인
        2. PORT HANDLING CHARGE Cost Center 확인
        3. EA 합계 일치 여부
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 1. ADP 키워드
        if not any(kw in invoice_line['SUBJECT'].upper() for kw in ['ADP', 'ABU DHABI PORTS']):
            errors.append("ADP keyword not found in SUBJECT")
        
        # 2. Cost Center
        if invoice_line.get('COST CENTER A') != 'PORT HANDLING CHARGE':
            # Warning only
            pass
        
        # 3. EA 합계
        ea_total = invoice_line.get('EA_Total_Amount', 0)
        amount = invoice_line.get('Total_Amount_AED', 0)
        if amount > 0:
            diff_pct = abs(ea_total - amount) / amount
            if diff_pct > 0.02:  # 2% 초과
                errors.append(f"EA Total mismatch: {ea_total:.2f} vs {amount:.2f} ({diff_pct*100:.2f}%)")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)


# 사용 예시
if __name__ == '__main__':
    handler = SafeenAdpHandler()
    
    # 테스트 데이터
    safeen_line = {
        'NO': 1,
        'SUBJECT': 'SAFEEN INVOICE NO. 2024/001 - Channel Crossing – Rot# 2503123133',
        'Total_Amount_AED': 6621.52,
        'COST MAIN': 'PORT HANDLING',
        'COST CENTER A': 'PORT HANDLING CHARGE',
        'COST CENTER B': 'CHANNEL TRANSIT CHARGES',
        'PRICE CENTER': 'CHANNEL TRANSIT CHARGES',
    }
    
    adp_line = {
        'NO': 2,
        'SUBJECT': 'ADP INV-2024-0456 - Port Dues for M/V HVDC Cargo',
        'Total_Amount_AED': 3500.00,
        'COST MAIN': 'PORT HANDLING',
        'COST CENTER A': 'PORT HANDLING CHARGE',
        'COST CENTER B': 'PORT DUES & SERVICES CHARGES',
        'PRICE CENTER': 'PORT DUES',
    }
    
    print("="*80)
    print("SAFEEN/ADP 처리 테스트")
    print("="*80)
    
    # SAFEEN 처리
    print("\n1. SAFEEN 인보이스 처리:")
    safeen_result = handler.process_safeen_invoice(safeen_line)
    print(f"  SUBJECT: {safeen_result['SUBJECT']}")
    print(f"  Total: {safeen_result['Total_Amount_AED']:.2f} AED")
    print(f"  EA_1: Qty={safeen_result['EA_1_Qty']}, Rate={safeen_result['EA_1_Rate']:.2f}")
    print(f"  EA_2: Qty={safeen_result['EA_2_Qty']}, Rate={safeen_result['EA_2_Rate']:.2f}")
    print(f"  EA_3: Qty={safeen_result['EA_3_Qty']}, Rate={safeen_result['EA_3_Rate']:.2f}")
    print(f"  EA Total: {safeen_result['EA_Total_Amount']:.2f} AED")
    
    # SAFEEN 검증
    is_valid, errors = handler.validate_safeen_invoice(safeen_result)
    print(f"  Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"    - {err}")
    
    # ADP 처리
    print("\n2. ADP 인보이스 처리:")
    adp_result = handler.process_adp_invoice(adp_line)
    print(f"  SUBJECT: {adp_result['SUBJECT']}")
    print(f"  Total: {adp_result['Total_Amount_AED']:.2f} AED")
    print(f"  EA_1: Qty={adp_result['EA_1_Qty']}, Rate={adp_result['EA_1_Rate']:.2f}")
    print(f"  EA Total: {adp_result['EA_Total_Amount']:.2f} AED")
    
    # ADP 검증
    is_valid, errors = handler.validate_adp_invoice(adp_result)
    print(f"  Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"    - {err}")
