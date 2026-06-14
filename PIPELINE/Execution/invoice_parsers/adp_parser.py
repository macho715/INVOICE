"""
ADP (Abu Dhabi Ports) 인보이스 파서

ADP PDF 인보이스를 파싱하여 표준 형식으로 변환

작성일: 2025-11-11
작성자: MACHO-GPT v3.4-mini
"""

import PyPDF2
import re
from pathlib import Path
from typing import List, Dict


class ADPParser:
    """ADP 인보이스 파서 클래스"""
    
    def __init__(self):
        """파서 초기화"""
        self.patterns = self._define_patterns()
    
    def _define_patterns(self) -> Dict:
        """정규표현식 패턴 정의"""
        return {
            'invoice_no': r'INVOICE\s*NO\.?\s*[:：]?\s*([A-Z0-9\-]+)',
            'invoice_date': r'DATE\s*[:：]?\s*(\d{2}[-/]\d{2}[-/]\d{4})',
            'voyage_no': r'ROT[#\s]*[:：]?\s*([A-Z0-9\-]+)',
            'amount': r'AMOUNT\s*[:：]?\s*AED\s*([\d,]+\.?\d*)',
            'service_type': r'(PORT\s+DUES|BULK\s+MATERIAL|GATE\s+PASS|GENERAL\s+CARGO)',
        }
    
    def parse(self, pdf_path: Path) -> List[Dict]:
        """
        ADP PDF 파싱
        
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
            invoice_no = invoice_match.group(1) if invoice_match else f"ADP-{pdf_path.stem}"
            
            # 인보이스 날짜 추출
            date_match = re.search(self.patterns['invoice_date'], text, re.IGNORECASE)
            invoice_date = date_match.group(1) if date_match else "2024-11-01"
            
            # Voyage No 추출
            voyage_match = re.search(self.patterns['voyage_no'], text, re.IGNORECASE)
            voyage_no = voyage_match.group(1) if voyage_match else "UNKNOWN"
            
            # 서비스 타입 추출
            service_match = re.search(self.patterns['service_type'], text, re.IGNORECASE)
            service_type = service_match.group(1) if service_match else "PORT DUES"
            
            # 금액 추출 (여러 개일 수 있음)
            amount_matches = re.findall(self.patterns['amount'], text, re.IGNORECASE)
            
            if amount_matches:
                for amount_str in amount_matches:
                    amount = float(amount_str.replace(',', ''))
                    
                    # SUBJECT 생성
                    subject = f"ABU DHABI PORTS – {service_type} – Rot# {voyage_no}"
                    
                    # 라인 데이터 생성
                    line = {
                        'Voyage No': voyage_no,
                        'SUBJECT': subject,
                        'INVOICE NUMBER': invoice_no,
                        'INVOICE DATE': invoice_date,
                        'Total_Amount_AED': amount,
                        'Qty': 1.0,
                        'Provider': 'ADP',
                        'Service_Type': service_type,
                    }
                    
                    lines.append(line)
            else:
                # 금액을 찾지 못한 경우 더미 라인 추가
                lines.append({
                    'Voyage No': voyage_no,
                    'SUBJECT': f"ABU DHABI PORTS – {service_type} – Rot# {voyage_no}",
                    'INVOICE NUMBER': invoice_no,
                    'INVOICE DATE': invoice_date,
                    'Total_Amount_AED': 0.0,
                    'Qty': 1.0,
                    'Provider': 'ADP',
                    'Service_Type': service_type,
                })
            
        except Exception as e:
            print(f"Error parsing ADP PDF {pdf_path}: {str(e)}")
            # 최소한의 더미 데이터 반환
            lines.append({
                'Voyage No': 'UNKNOWN',
                'SUBJECT': f'ADP – ERROR PARSING – {pdf_path.name}',
                'INVOICE NUMBER': f'ADP-{pdf_path.stem}',
                'INVOICE DATE': '2024-11-01',
                'Total_Amount_AED': 0.0,
                'Qty': 1.0,
                'Provider': 'ADP',
                'Service_Type': 'UNKNOWN',
            })
        
        return lines
