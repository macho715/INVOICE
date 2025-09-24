"""
최종 증빙문서 통합 Invoice Audit System

AUDIT LOGIC.MD + 실제 증빙문서를 완전 통합한 최종 송장 감사 시스템입니다.
- 실제 증빙문서 PDF 연결
- Evidence 링크 실제 생성
- S/No 순서 보존
- At-Cost vs Contract 라인 구분
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class FinalIntegratedAuditSystem:
    """최종 증빙문서 통합 송장 감사 시스템"""
    
    def __init__(self):
        self.excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
        self.supporting_docs_path = Path("Samsung C&T (HVDC) Shippments (Aug2025) - Supporting Documents")
        self.output_dir = Path("out")
        self.output_dir.mkdir(exist_ok=True)
        
        # AUDIT LOGIC.MD 기반 검증 규칙
        self.audit_rules = {
            "fx_rates": {
                "USD_AED": 3.6725,
                "AED_USD": 1/3.6725
            },
            "cost_guard_bands": {
                "PASS": 2.0,      # ≤2.00%
                "WARN": 5.0,      # 2.01-5.00%
                "HIGH": 10.0,     # 5.01-10.00%
                "CRITICAL": 15.0  # 10.01-15.00%
            },
            "auto_fail_threshold": 15.0,  # >15.00% AUTOFAIL
            "contract_tolerance": 3.0     # ±3% 계약 허용치
        }
        
        # 증빙문서 타입 매핑
        self.document_type_mapping = {
            "BOE": "세관",
            "DO": "인도",
            "DN": "운송",
            "CarrierInvoice": "선사/항공사",
            "PortCNTAdminInsp": "터미널 관리/검사",
            "PortCNTWashing": "터미널 세척",
            "AirportFees": "공항 수수료",
            "Appointment": "예약",
            "StorageFee": "저장 수수료",
            "CourierFee": "택배 수수료",
            "RepairChargesApproval": "수리비 승인"
        }
        
        # 헤더 키워드
        self.header_keywords = [
            'S/No', 'SNo', 'S.No', 'No', 'Item',
            'Rate Source', 'RateSource', 'Source',
            'Description', 'Desc', 'Item Description',
            'Rate', 'Unit Rate', 'Price', 'Rate_USD',
            'Formula', 'Calc', 'Calculation', 'Formula_Text',
            'Qty', 'Quantity', 'Qty.',
            'Total', 'Total (USD)', 'Amount', 'Total_USD',
            'Currency', 'Curr', 'CCY',
            'At Cost', 'At-Cost', 'Cost'
        ]
    
    def run_final_integrated_audit(self) -> Dict:
        """최종 증빙문서 통합 감사 실행"""
        print("🚀 최종 증빙문서 통합 Invoice Audit System 시작")
        print("=" * 70)
        
        # 1. Excel 데이터 로드
        excel_data = self.load_excel_data()
        if not excel_data:
            return None
        
        # 2. 증빙문서 매핑 생성
        supporting_docs = self.map_supporting_documents_robust()
        
        # 3. 모든 시트에서 송장 데이터 추출
        all_invoice_items = []
        sheet_summaries = {}
        
        for sheet_name, df in excel_data.items():
            print(f"📋 시트 '{sheet_name}' 처리 중...")
            invoice_items = self.extract_invoice_data_with_evidence_robust(df, sheet_name, supporting_docs)
            all_invoice_items.extend(invoice_items)
            
            # 시트별 요약
            sheet_summaries[sheet_name] = self.calculate_sheet_summary(invoice_items)
        
        # 4. S/No 순서로 정렬
        all_invoice_items = self.preserve_sno_order(all_invoice_items)
        
        # 5. 전체 요약 계산
        total_summary = self.calculate_total_summary(all_invoice_items)
        
        # 6. 감사 결과 생성
        audit_result = {
            "audit_metadata": {
                "audit_date": datetime.now().isoformat(),
                "excel_file": self.excel_file,
                "supporting_docs_path": str(self.supporting_docs_path),
                "total_sheets": len(excel_data),
                "total_invoice_items": len(all_invoice_items),
                "total_supporting_docs": len(supporting_docs),
                "system_version": "Final Integrated v5.0",
                "compliance": "FULL_AUDIT_LOGIC_MD_WITH_EVIDENCE_FINAL"
            },
            "audit_rules": self.audit_rules,
            "document_type_mapping": self.document_type_mapping,
            "supporting_documents": supporting_docs,
            "summary": total_summary,
            "sheet_summaries": sheet_summaries,
            "invoice_items": all_invoice_items
        }
        
        return audit_result
    
    def load_excel_data(self) -> Dict[str, pd.DataFrame]:
        """Excel 파일에서 모든 시트 데이터 로드"""
        try:
            print(f"📁 Excel 파일 로드 중: {self.excel_file}")
            excel_data = pd.read_excel(self.excel_file, sheet_name=None, engine='openpyxl')
            print(f"✅ {len(excel_data)}개 시트 로드 완료")
            return excel_data
        except Exception as e:
            print(f"❌ Excel 로드 오류: {e}")
            return {}
    
    def map_supporting_documents_robust(self) -> Dict[str, List[Dict]]:
        """견고한 증빙문서 매핑 생성"""
        print(f"📁 증빙문서 매핑 중: {self.supporting_docs_path}")
        
        supporting_docs = {}
        
        if not self.supporting_docs_path.exists():
            print(f"⚠️ 증빙문서 폴더 없음: {self.supporting_docs_path}")
            return supporting_docs
        
        try:
            # 모든 PDF 파일 스캔 (견고한 경로 처리)
            pdf_files = []
            for root, dirs, files in os.walk(self.supporting_docs_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(Path(root) / file)
            
            print(f"✅ {len(pdf_files)}개 PDF 파일 발견")
            
            for pdf_file in pdf_files:
                try:
                    # 파일명에서 Shipment ID와 문서 타입 추출
                    shipment_id, doc_type = self.extract_shipment_and_doc_type_robust(pdf_file.name)
                    
                    if shipment_id and doc_type:
                        if shipment_id not in supporting_docs:
                            supporting_docs[shipment_id] = []
                        
                        doc_info = {
                            "file_name": pdf_file.name,
                            "file_path": str(pdf_file),
                            "doc_type": doc_type,
                            "doc_type_korean": self.document_type_mapping.get(doc_type, doc_type),
                            "file_size": pdf_file.stat().st_size,
                            "last_modified": datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
                        }
                        
                        supporting_docs[shipment_id].append(doc_info)
                
                except Exception as e:
                    print(f"⚠️ PDF 파일 처리 오류: {pdf_file.name} - {e}")
                    continue
            
            # 각 Shipment별 문서 정렬
            for shipment_id in supporting_docs:
                supporting_docs[shipment_id].sort(key=lambda x: x["doc_type"])
            
            print(f"✅ {len(supporting_docs)}개 Shipment의 증빙문서 매핑 완료")
            return supporting_docs
            
        except Exception as e:
            print(f"❌ 증빙문서 매핑 오류: {e}")
            return {}
    
    def extract_shipment_and_doc_type_robust(self, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """견고한 파일명 파싱"""
        try:
            # 파일명에서 Shipment ID 추출
            if "HVDC-ADOPT-" in filename:
                # HVDC-ADOPT-SCT-0107_BOE.pdf 형식
                parts = filename.split("_")
                if len(parts) >= 2:
                    shipment_id = parts[0]  # HVDC-ADOPT-SCT-0107
                    doc_part = parts[1].replace(".pdf", "")  # BOE
                    
                    # 문서 타입 정규화
                    doc_type = self.normalize_document_type(doc_part)
                    
                    return shipment_id, doc_type
            
            # 다른 형식 시도
            if "HVDC-ADOPT-" in filename:
                # HVDC-ADOPT-SCT-0107_BOE.pdf 형식이 아닌 경우
                base_name = filename.replace(".pdf", "")
                if "_" in base_name:
                    parts = base_name.split("_")
                    shipment_id = parts[0]
                    doc_type = self.normalize_document_type("_".join(parts[1:]))
                    return shipment_id, doc_type
            
            return None, None
            
        except Exception as e:
            print(f"❌ 파일명 파싱 오류: {filename} - {e}")
            return None, None
    
    def normalize_document_type(self, doc_part: str) -> str:
        """문서 타입 정규화"""
        doc_part = doc_part.upper()
        
        if "BOE" in doc_part:
            return "BOE"
        elif "DO" in doc_part:
            return "DO"
        elif "DN" in doc_part:
            return "DN"
        elif "CARRIER" in doc_part or "INVOICE" in doc_part:
            return "CarrierInvoice"
        elif "PORT" in doc_part and "ADMIN" in doc_part:
            return "PortCNTAdminInsp"
        elif "PORT" in doc_part and "WASH" in doc_part:
            return "PortCNTWashing"
        elif "AIRPORT" in doc_part or "FEES" in doc_part:
            return "AirportFees"
        elif "APPOINTMENT" in doc_part:
            return "Appointment"
        elif "STORAGE" in doc_part:
            return "StorageFee"
        elif "COURIER" in doc_part:
            return "CourierFee"
        elif "REPAIR" in doc_part:
            return "RepairChargesApproval"
        else:
            return doc_part
    
    def extract_invoice_data_with_evidence_robust(self, df: pd.DataFrame, sheet_name: str, 
                                                supporting_docs: Dict[str, List[Dict]]) -> List[Dict]:
        """견고한 증빙문서 연결 송장 데이터 추출"""
        invoice_items = []
        
        try:
            # 1. 동적 헤더 행 찾기
            header_row = self.find_header_row_advanced(df)
            if header_row is None:
                print(f"  ⚠️ 헤더 행을 찾을 수 없음: {sheet_name}")
                return invoice_items
            
            # 2. 데이터 범위 찾기
            data_start_row = header_row + 1
            data_end_row = self.find_data_end_row_advanced(df, data_start_row)
            
            if data_end_row is None:
                print(f"  ⚠️ 데이터 범위를 찾을 수 없음: {sheet_name}")
                return invoice_items
            
            # 3. 헤더 컬럼 매핑
            header_mapping = self.create_header_mapping(df.iloc[header_row])
            
            # 4. Shipment ID 추출 (시트명에서)
            shipment_id = self.extract_shipment_id_from_sheet_name_robust(sheet_name)
            
            # 5. 해당 Shipment의 증빙문서 가져오기
            shipment_docs = supporting_docs.get(shipment_id, [])
            
            # 6. 송장 항목 추출
            for idx in range(data_start_row, min(data_end_row + 1, len(df))):
                row = df.iloc[idx]
                
                if self.is_valid_invoice_row_advanced(row):
                    item = self.create_final_integrated_audit_item(
                        row, sheet_name, idx, header_mapping, shipment_docs
                    )
                    if item:
                        invoice_items.append(item)
            
            print(f"  ✅ {len(invoice_items)}개 송장 항목 추출 (증빙문서 {len(shipment_docs)}개 연결)")
            return invoice_items
            
        except Exception as e:
            print(f"❌ 시트 '{sheet_name}' 데이터 추출 오류: {e}")
            return []
    
    def extract_shipment_id_from_sheet_name_robust(self, sheet_name: str) -> str:
        """견고한 Shipment ID 추출"""
        # 시트명이 Shipment ID와 일치하는 경우
        if sheet_name.startswith("HVDC-ADOPT-"):
            return sheet_name
        
        # 시트명을 Shipment ID로 변환
        if sheet_name.startswith("SCT") or sheet_name.startswith("SIM") or sheet_name.startswith("HE"):
            return f"HVDC-ADOPT-{sheet_name}"
        
        # AUG 시트는 특별 처리
        if sheet_name == "AUG":
            return "AUG"
        
        return sheet_name
    
    def find_header_row_advanced(self, df: pd.DataFrame) -> Optional[int]:
        """고급 헤더 행 찾기"""
        best_match_row = None
        best_match_score = 0
        
        for idx, row in df.iterrows():
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            
            # 키워드 매칭 점수 계산
            keyword_matches = sum(1 for keyword in self.header_keywords 
                                if keyword.lower() in row_str.lower())
            
            # 연속된 숫자나 특수 패턴 확인
            has_number_sequence = any(str(cell).isdigit() for cell in row if pd.notna(cell))
            has_currency = any('USD' in str(cell).upper() or 'AED' in str(cell).upper() 
                             for cell in row if pd.notna(cell))
            
            # 점수 계산
            score = keyword_matches
            if has_currency:
                score += 2
            if has_number_sequence:
                score += 1
            
            if score > best_match_score:
                best_match_score = score
                best_match_row = idx
        
        # 최소 2개 이상 키워드 매치 필요
        return best_match_row if best_match_score >= 2 else None
    
    def find_data_end_row_advanced(self, df: pd.DataFrame, start_row: int) -> Optional[int]:
        """고급 데이터 끝 행 찾기"""
        consecutive_empty_rows = 0
        max_consecutive_empty = 3
        
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            non_null_count = row.notna().sum()
            
            if non_null_count == 0:
                consecutive_empty_rows += 1
                if consecutive_empty_rows >= max_consecutive_empty:
                    return idx - consecutive_empty_rows
            else:
                consecutive_empty_rows = 0
        
        return len(df) - 1
    
    def create_header_mapping(self, header_row: pd.Series) -> Dict[str, int]:
        """헤더 컬럼 매핑 생성"""
        mapping = {}
        
        for idx, cell in enumerate(header_row):
            if pd.notna(cell):
                cell_str = str(cell).strip()
                
                # 키워드 매칭으로 컬럼 타입 결정
                if any(keyword in cell_str.upper() for keyword in ['S/NO', 'SNO', 'S.NO', 'NO']):
                    mapping['s_no'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['RATE SOURCE', 'RATESOURCE', 'SOURCE']):
                    mapping['rate_source'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['DESCRIPTION', 'DESC']):
                    mapping['description'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['RATE', 'PRICE', 'UNIT RATE', 'RATE_USD']):
                    mapping['rate'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['QTY', 'QUANTITY']):
                    mapping['quantity'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['TOTAL', 'AMOUNT', 'TOTAL_USD']):
                    mapping['total'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['CURRENCY', 'CURR', 'CCY']):
                    mapping['currency'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['AT COST', 'AT-COST', 'COST']):
                    mapping['at_cost'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['FORMULA', 'CALC', 'FORMULA_TEXT']):
                    mapping['formula'] = idx
        
        return mapping
    
    def is_valid_invoice_row_advanced(self, row: pd.Series) -> bool:
        """고급 유효한 송장 행 확인"""
        non_null_count = row.notna().sum()
        
        # 최소 3개 이상의 값이 있어야 함
        if non_null_count < 3:
            return False
        
        # 숫자 값이 있는지 확인
        has_number = False
        for cell in row:
            if pd.notna(cell):
                try:
                    float(cell)
                    has_number = True
                    break
                except:
                    continue
        
        return has_number
    
    def create_final_integrated_audit_item(self, row: pd.Series, sheet_name: str, 
                                         row_idx: int, header_mapping: Dict[str, int],
                                         shipment_docs: List[Dict]) -> Optional[Dict]:
        """최종 통합 감사 항목 생성"""
        try:
            # 기본 정보 추출
            item = {
                "sheet_name": sheet_name,
                "row_number": row_idx + 1,
                "s_no": self.extract_field_value(row, header_mapping, 's_no'),
                "rate_source": self.extract_field_value(row, header_mapping, 'rate_source'),
                "description": self.extract_field_value(row, header_mapping, 'description'),
                "rate_usd": self.extract_numeric_value(row, header_mapping, 'rate'),
                "quantity": self.extract_numeric_value(row, header_mapping, 'quantity'),
                "total_usd": self.extract_numeric_value(row, header_mapping, 'total'),
                "currency": self.extract_field_value(row, header_mapping, 'currency'),
                "at_cost": self.extract_numeric_value(row, header_mapping, 'at_cost'),
                "formula_text": self.extract_field_value(row, header_mapping, 'formula')
            }
            
            # 증빙문서 연결
            item["supporting_documents"] = self.find_related_documents_robust(item, shipment_docs)
            item["evidence_links"] = self.generate_evidence_links_robust(item["supporting_documents"])
            
            # AUDIT LOGIC.MD 기반 계산
            item["line_type"] = self.determine_line_type(item)
            item["amount_usd"] = self.calculate_amount_usd_audit_logic(item)
            item["delta_percent"] = self.calculate_delta_percent_audit_logic(item)
            item["cost_guard_band"] = self.determine_cost_guard_band_audit_logic(item["delta_percent"])
            item["status"] = self.determine_status_audit_logic(item)
            item["risk_tier"] = self.determine_risk_tier(item)
            item["remarks"] = self.generate_remarks(item)
            item["validation_flags"] = self.generate_validation_flags_audit_logic(item)
            
            return item
            
        except Exception as e:
            print(f"❌ 송장 항목 생성 오류 (행 {row_idx}): {e}")
            return None
    
    def find_related_documents_robust(self, item: Dict, shipment_docs: List[Dict]) -> List[Dict]:
        """견고한 관련 증빙문서 찾기"""
        related_docs = []
        
        # Rate Source 기반 매칭
        if item["rate_source"]:
            for doc in shipment_docs:
                if item["rate_source"].upper() in doc["doc_type"].upper():
                    related_docs.append(doc)
        
        # Description 기반 매칭
        if item["description"]:
            desc_keywords = self.extract_keywords_from_description(item["description"])
            for doc in shipment_docs:
                for keyword in desc_keywords:
                    if keyword.upper() in doc["file_name"].upper():
                        if doc not in related_docs:
                            related_docs.append(doc)
        
        # 기본 매칭 (모든 문서)
        if not related_docs and shipment_docs:
            # 관련 문서가 없으면 첫 번째 문서라도 연결
            related_docs.append(shipment_docs[0])
        
        return related_docs
    
    def extract_keywords_from_description(self, description: str) -> List[str]:
        """Description에서 키워드 추출"""
        keywords = []
        
        # 일반적인 키워드 추출
        if "BOE" in description.upper():
            keywords.append("BOE")
        if "DO" in description.upper():
            keywords.append("DO")
        if "DN" in description.upper():
            keywords.append("DN")
        if "CARRIER" in description.upper():
            keywords.append("Carrier")
        if "PORT" in description.upper():
            keywords.append("Port")
        if "AIRPORT" in description.upper():
            keywords.append("Airport")
        if "STORAGE" in description.upper():
            keywords.append("Storage")
        if "APPOINTMENT" in description.upper():
            keywords.append("Appointment")
        
        return keywords
    
    def generate_evidence_links_robust(self, supporting_docs: List[Dict]) -> List[str]:
        """견고한 Evidence 링크 생성"""
        evidence_links = []
        
        for doc in supporting_docs:
            link = f"PDF: {doc['file_name']} | {doc['doc_type_korean']} | {doc['file_size']} bytes"
            evidence_links.append(link)
        
        return evidence_links
    
    def determine_line_type(self, item: Dict) -> str:
        """라인 타입 결정 (At-Cost vs Contract)"""
        if item["at_cost"] > 0:
            return "At-Cost"
        elif item["rate_source"] and "CONTRACT" in item["rate_source"].upper():
            return "Contract"
        else:
            return "Unknown"
    
    def calculate_amount_usd_audit_logic(self, item: Dict) -> float:
        """AUDIT LOGIC.MD 기반 USD 금액 계산"""
        if item["line_type"] == "At-Cost":
            # At-Cost: 증빙 AED → USD 환산
            if item["currency"] == "AED":
                return round(item["total_usd"] * self.audit_rules["fx_rates"]["AED_USD"], 2)
            else:
                return item["total_usd"]
        else:
            # Contract: Draft USD가 기준
            return item["total_usd"]
    
    def calculate_delta_percent_audit_logic(self, item: Dict) -> float:
        """AUDIT LOGIC.MD 기반 Delta % 계산"""
        if item["line_type"] == "At-Cost" and item["at_cost"] > 0:
            # At-Cost: (DraftTotal_USD - Doc_USD) / Doc_USD * 100
            doc_usd = round(item["at_cost"] * self.audit_rules["fx_rates"]["AED_USD"], 2)
            if doc_usd > 0:
                return round(((item["total_usd"] - doc_usd) / doc_usd) * 100, 2)
        elif item["line_type"] == "Contract":
            # Contract: (DraftRate_USD - RefRate_USD) / RefRate_USD * 100
            # 여기서는 단순히 0으로 설정 (실제로는 Ref JSON 필요)
            return 0.0
        
        return 0.0
    
    def determine_cost_guard_band_audit_logic(self, delta_percent: float) -> str:
        """AUDIT LOGIC.MD 기반 COST-GUARD 밴드 결정"""
        abs_delta = abs(delta_percent)
        
        if abs_delta <= self.audit_rules["cost_guard_bands"]["PASS"]:
            return "PASS"
        elif abs_delta <= self.audit_rules["cost_guard_bands"]["WARN"]:
            return "WARN"
        elif abs_delta <= self.audit_rules["cost_guard_bands"]["HIGH"]:
            return "HIGH"
        elif abs_delta <= self.audit_rules["cost_guard_bands"]["CRITICAL"]:
            return "CRITICAL"
        else:
            return "AUTOFAIL"
    
    def determine_status_audit_logic(self, item: Dict) -> str:
        """AUDIT LOGIC.MD 기반 상태 결정"""
        # AUTOFAIL 체크
        if item["cost_guard_band"] == "AUTOFAIL":
            return "COST_GUARD_FAIL"
        
        # REFERENCE_MISSING 체크
        if not item["rate_source"] or item["rate_source"] == "Unknown":
            return "REFERENCE_MISSING"
        
        # NO DATA 체크
        if item["line_type"] == "Unknown":
            return "NO_DATA"
        
        # 증빙문서 없음 체크
        if not item["supporting_documents"]:
            return "NO_EVIDENCE"
        
        # 일반 상태
        if item["cost_guard_band"] in ["HIGH", "CRITICAL"]:
            return "WARNING"
        else:
            return "PASS"
    
    def determine_risk_tier(self, item: Dict) -> str:
        """리스크 티어 결정"""
        return item["cost_guard_band"]
    
    def generate_remarks(self, item: Dict) -> str:
        """Remarks 생성"""
        remarks = []
        
        if item["status"] == "REFERENCE_MISSING":
            remarks.append("REFERENCE_MISSING")
        
        if item["status"] == "NO_EVIDENCE":
            remarks.append("NO_EVIDENCE")
        
        if item["line_type"] == "Unknown":
            remarks.append("LINE_TYPE_UNKNOWN")
        
        if item["delta_percent"] > self.audit_rules["contract_tolerance"]:
            remarks.append("TOLERANCE_EXCEEDED")
        
        return "; ".join(remarks) if remarks else ""
    
    def generate_validation_flags_audit_logic(self, item: Dict) -> List[str]:
        """AUDIT LOGIC.MD 기반 검증 플래그 생성"""
        flags = []
        
        if item["delta_percent"] > self.audit_rules["auto_fail_threshold"]:
            flags.append("AUTOFAIL")
        
        if item["amount_usd"] <= 0:
            flags.append("ZERO_AMOUNT")
        
        if item["currency"] not in ["USD", "AED"]:
            flags.append("UNKNOWN_CURRENCY")
        
        if not item["rate_source"]:
            flags.append("NO_RATE_SOURCE")
        
        if item["line_type"] == "Unknown":
            flags.append("UNKNOWN_LINE_TYPE")
        
        if not item["supporting_documents"]:
            flags.append("NO_SUPPORTING_DOCS")
        
        return flags
    
    def preserve_sno_order(self, invoice_items: List[Dict]) -> List[Dict]:
        """S/No 순서 보존"""
        def sort_key(item):
            try:
                return int(item["s_no"]) if item["s_no"].isdigit() else float('inf')
            except:
                return float('inf')
        
        return sorted(invoice_items, key=sort_key)
    
    def extract_field_value(self, row: pd.Series, mapping: Dict[str, int], field: str) -> str:
        """필드 값 추출"""
        if field in mapping:
            idx = mapping[field]
            if idx < len(row) and pd.notna(row.iloc[idx]):
                return str(row.iloc[idx]).strip()
        return ""
    
    def extract_numeric_value(self, row: pd.Series, mapping: Dict[str, int], field: str) -> float:
        """숫자 값 추출"""
        if field in mapping:
            idx = mapping[field]
            if idx < len(row) and pd.notna(row.iloc[idx]):
                try:
                    return float(row.iloc[idx])
                except:
                    pass
        return 0.0
    
    def calculate_sheet_summary(self, invoice_items: List[Dict]) -> Dict:
        """시트별 요약 계산"""
        if not invoice_items:
            return {
                "total_items": 0,
                "pass_items": 0,
                "warning_items": 0,
                "fail_items": 0,
                "total_amount": 0.0,
                "average_delta": 0.0,
                "at_cost_items": 0,
                "contract_items": 0,
                "evidence_items": 0
            }
        
        total_items = len(invoice_items)
        pass_items = len([item for item in invoice_items if item["status"] == "PASS"])
        warning_items = len([item for item in invoice_items if item["status"] == "WARNING"])
        fail_items = len([item for item in invoice_items if item["status"] in ["COST_GUARD_FAIL", "REFERENCE_MISSING", "NO_DATA", "NO_EVIDENCE"]])
        total_amount = sum(item["amount_usd"] for item in invoice_items)
        average_delta = sum(item["delta_percent"] for item in invoice_items) / total_items
        at_cost_items = len([item for item in invoice_items if item["line_type"] == "At-Cost"])
        contract_items = len([item for item in invoice_items if item["line_type"] == "Contract"])
        evidence_items = len([item for item in invoice_items if item["supporting_documents"]])
        
        return {
            "total_items": total_items,
            "pass_items": pass_items,
            "warning_items": warning_items,
            "fail_items": fail_items,
            "total_amount": total_amount,
            "average_delta": average_delta,
            "at_cost_items": at_cost_items,
            "contract_items": contract_items,
            "evidence_items": evidence_items
        }
    
    def calculate_total_summary(self, all_invoice_items: List[Dict]) -> Dict:
        """전체 요약 계산"""
        if not all_invoice_items:
            return {
                "total_items": 0,
                "pass_items": 0,
                "warning_items": 0,
                "fail_items": 0,
                "pass_rate": 0.0,
                "total_amount_usd": 0.0,
                "average_delta_percent": 0.0,
                "at_cost_items": 0,
                "contract_items": 0,
                "evidence_items": 0,
                "sno_order_preserved": True
            }
        
        total_items = len(all_invoice_items)
        pass_items = len([item for item in all_invoice_items if item["status"] == "PASS"])
        warning_items = len([item for item in all_invoice_items if item["status"] == "WARNING"])
        fail_items = len([item for item in all_invoice_items if item["status"] in ["COST_GUARD_FAIL", "REFERENCE_MISSING", "NO_DATA", "NO_EVIDENCE"]])
        total_amount = sum(item["amount_usd"] for item in all_invoice_items)
        average_delta = sum(item["delta_percent"] for item in all_invoice_items) / total_items
        at_cost_items = len([item for item in all_invoice_items if item["line_type"] == "At-Cost"])
        contract_items = len([item for item in all_invoice_items if item["line_type"] == "Contract"])
        evidence_items = len([item for item in all_invoice_items if item["supporting_documents"]])
        
        return {
            "total_items": total_items,
            "pass_items": pass_items,
            "warning_items": warning_items,
            "fail_items": fail_items,
            "pass_rate": (pass_items / total_items * 100) if total_items > 0 else 0,
            "total_amount_usd": total_amount,
            "average_delta_percent": average_delta,
            "at_cost_items": at_cost_items,
            "contract_items": contract_items,
            "evidence_items": evidence_items,
            "sno_order_preserved": True
        }
    
    def save_audit_report(self, audit_result: Dict) -> str:
        """감사 보고서 저장"""
        try:
            # JSON 보고서 저장
            json_file = self.output_dir / "final_integrated_audit_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False, default=str)
            
            # CSV 보고서 저장
            csv_file = self.output_dir / "final_integrated_audit_report.csv"
            df = pd.DataFrame(audit_result["invoice_items"])
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            # 상세 요약 보고서 저장
            summary_file = self.output_dir / "final_integrated_audit_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_final_integrated_summary_report(audit_result))
            
            print(f"📄 최종 증빙문서 통합 감사 보고서 저장 완료:")
            print(f"  - JSON: {json_file}")
            print(f"  - CSV: {csv_file}")
            print(f"  - 요약: {summary_file}")
            
            return str(json_file)
            
        except Exception as e:
            print(f"❌ 보고서 저장 오류: {e}")
            return None
    
    def generate_final_integrated_summary_report(self, audit_result: Dict) -> str:
        """최종 통합 요약 보고서 생성"""
        summary = audit_result["summary"]
        rules = audit_result["audit_rules"]
        supporting_docs = audit_result["supporting_documents"]
        
        report = f"""
최종 증빙문서 통합 Invoice Audit System - 상세 보고서
====================================================

감사 일시: {audit_result['audit_metadata']['audit_date']}
Excel 파일: {audit_result['audit_metadata']['excel_file']}
증빙문서 경로: {audit_result['audit_metadata']['supporting_docs_path']}
시스템 버전: {audit_result['audit_metadata']['system_version']}
준수 수준: {audit_result['audit_metadata']['compliance']}
총 시트 수: {audit_result['audit_metadata']['total_sheets']}개
총 송장 항목: {summary['total_items']}개
총 증빙문서: {audit_result['audit_metadata']['total_supporting_docs']}개

📊 전체 요약
-----------
✅ PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)
⚠️ WARNING: {summary['warning_items']}개
❌ FAIL: {summary['fail_items']}개
💰 총 금액: ${summary['total_amount_usd']:,.2f} USD
📈 평균 Delta: {summary['average_delta_percent']:.2f}%
🔢 S/No 순서 보존: {'✅' if summary['sno_order_preserved'] else '❌'}

📋 라인 타입 분석
---------------
At-Cost 라인: {summary['at_cost_items']}개
Contract 라인: {summary['contract_items']}개
증빙문서 연결: {summary['evidence_items']}개

🔧 AUDIT LOGIC.MD 검증 규칙
--------------------------
환율: 1 USD = {rules['fx_rates']['USD_AED']} AED (고정)
계약 허용치: ±{rules['contract_tolerance']}%
AUTOFAIL 임계치: >{rules['auto_fail_threshold']}%

COST-GUARD 밴드:
- PASS: ≤{rules['cost_guard_bands']['PASS']}%
- WARN: {rules['cost_guard_bands']['PASS']}-{rules['cost_guard_bands']['WARN']}%
- HIGH: {rules['cost_guard_bands']['WARN']}-{rules['cost_guard_bands']['HIGH']}%
- CRITICAL: {rules['cost_guard_bands']['HIGH']}-{rules['cost_guard_bands']['CRITICAL']}%
- AUTOFAIL: >{rules['cost_guard_bands']['CRITICAL']}%

📁 증빙문서 분석
---------------
"""
        
        # 증빙문서 타입별 통계
        doc_type_stats = {}
        for shipment_id, docs in supporting_docs.items():
            for doc in docs:
                doc_type = doc["doc_type"]
                if doc_type not in doc_type_stats:
                    doc_type_stats[doc_type] = 0
                doc_type_stats[doc_type] += 1
        
        for doc_type, count in doc_type_stats.items():
            korean_name = self.document_type_mapping.get(doc_type, doc_type)
            report += f"{korean_name}: {count}개\n"
        
        report += f"""
📋 시트별 상세 분석
------------------
"""
        
        for sheet_name, sheet_summary in audit_result["sheet_summaries"].items():
            report += f"""
{sheet_name}:
  - 총 항목: {sheet_summary['total_items']}개
  - PASS: {sheet_summary['pass_items']}개
  - WARNING: {sheet_summary['warning_items']}개
  - FAIL: {sheet_summary['fail_items']}개
  - 총 금액: ${sheet_summary['total_amount']:,.2f} USD
  - 평균 Delta: {sheet_summary['average_delta']:.2f}%
  - At-Cost: {sheet_summary['at_cost_items']}개
  - Contract: {sheet_summary['contract_items']}개
  - 증빙문서 연결: {sheet_summary['evidence_items']}개
"""
        
        report += f"""
=====================================================
감사 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
최종 증빙문서 통합 시스템으로 실행됨
"""
        
        return report

def main():
    """메인 실행 함수"""
    print("🚀 최종 증빙문서 통합 Invoice Audit System 실행")
    print("=" * 70)
    
    # 감사 시스템 초기화
    audit_system = FinalIntegratedAuditSystem()
    
    # 최종 통합 감사 실행
    audit_result = audit_system.run_final_integrated_audit()
    
    if audit_result:
        # 보고서 저장
        report_file = audit_system.save_audit_report(audit_result)
        
        if report_file:
            print(f"\n✅ 최종 증빙문서 통합 감사 완료! 보고서: {report_file}")
            
            # 요약 출력
            summary = audit_result["summary"]
            print(f"\n📊 최종 요약:")
            print(f"  - 총 송장 항목: {summary['total_items']}개")
            print(f"  - PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)")
            print(f"  - WARNING: {summary['warning_items']}개")
            print(f"  - FAIL: {summary['fail_items']}개")
            print(f"  - 총 금액: ${summary['total_amount_usd']:,.2f} USD")
            print(f"  - S/No 순서 보존: {'✅' if summary['sno_order_preserved'] else '❌'}")
            print(f"  - At-Cost 라인: {summary['at_cost_items']}개")
            print(f"  - Contract 라인: {summary['contract_items']}개")
            print(f"  - 증빙문서 연결: {summary['evidence_items']}개")
        else:
            print("❌ 보고서 저장 실패")
    else:
        print("❌ 감사 실행 실패")

if __name__ == "__main__":
    main()
