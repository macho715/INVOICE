"""
OFCO 인보이스 파서

OFCO PDF 인보이스를 파싱하여 표준 형식으로 변환

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import PyPDF2
import re
from pathlib import Path
from typing import List, Dict


class OFCOParser:
    """OFCO 인보이스 파서 클래스"""
    
    def __init__(self):
        """파서 초기화"""
        self.patterns = self._define_patterns()
    
    def _define_patterns(self) -> Dict:
        """정규표현식 패턴 정의"""
        return {
            'invoice_no': r'INVOICE\s*NO\.?\s*[:：]?\s*(OFCO-INV-[\d\-]+)',
            'invoice_date': r'DATE\s*[:：]?\s*(\d{2}[-/]\d{2}[-/]\d{4})',
            'voyage_no': r'(HVDC-[A-Z0-9\-]+)',
            'subject': r'SUBJECT\s*[:：]?\s*(.+?)(?=\n|INVOICE|AMOUNT)',
            'amount': r'(\d+\.?\d*)\s*AED',
        }
    
    def parse(self, pdf_path: Path) -> List[Dict]:
        """
        OFCO PDF 파싱
        
        Parameters:
            pdf_path (Path): PDF 파일 경로
        
        Returns:
            List[Dict]: 파싱된 라인 목록
        """
        lines = []
        
        try:
            # PDF 텍스트 추출
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            # 인보이스 번호 추출
            invoice_match = re.search(self.patterns['invoice_no'], text, re.IGNORECASE)
            invoice_no = invoice_match.group(1) if invoice_match else f"OFCO-INV-{pdf_path.stem}"
            
            # 인보이스 날짜 추출
            date_match = re.search(self.patterns['invoice_date'], text, re.IGNORECASE)
            invoice_date = date_match.group(1) if date_match else "2024-11-01"
            
            # Voyage No 추출 (복수 가능)
            voyage_matches = re.findall(self.patterns['voyage_no'], text, re.IGNORECASE)
            voyage_nos = list(set(voyage_matches)) if voyage_matches else ["UNKNOWN"]
            
            # SUBJECT 추출 (복수 가능)
            subject_matches = re.findall(self.patterns['subject'], text, re.IGNORECASE | re.DOTALL)
            subjects = [s.strip() for s in subject_matches] if subject_matches else ["UNKNOWN"]
            
            # 금액 추출 (복수 가능)
            amount_matches = re.findall(self.patterns['amount'], text)
            amounts = [float(a.replace(',', '')) for a in amount_matches] if amount_matches else [0.0]
            
            # 라인 생성 (SUBJECT와 금액 매칭)
            max_lines = max(len(subjects), len(amounts), len(voyage_nos))
            
            for i in range(max_lines):
                voyage_no = voyage_nos[i % len(voyage_nos)]
                subject = subjects[i % len(subjects)]
                amount = amounts[i % len(amounts)]
                
                line = {
                    'Voyage No': voyage_no,
                    'SUBJECT': subject,
                    'INVOICE NUMBER': invoice_no,
                    'INVOICE DATE': invoice_date,
                    'Total_Amount_AED': amount,
                    'Qty': 1.0,
                    'Provider': 'OFCO',
                    'Service_Type': 'MIXED',
                }
                
                lines.append(line)
            
        except Exception as e:
            print(f"Error parsing OFCO PDF {pdf_path}: {str(e)}")
            # 최소한의 더미 데이터 반환
            lines.append({
                'Voyage No': 'UNKNOWN',
                'SUBJECT': f'OFCO – ERROR PARSING – {pdf_path.name}',
                'INVOICE NUMBER': f'OFCO-INV-{pdf_path.stem}',
                'INVOICE DATE': '2024-11-01',
                'Total_Amount_AED': 0.0,
                'Qty': 1.0,
                'Provider': 'OFCO',
                'Service_Type': 'UNKNOWN',
            })
        
        return lines
