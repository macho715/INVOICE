"""
개선된 Invoice Audit System

상세 매뉴얼 기반으로 업그레이드된 송장 감사 시스템입니다.
- 동적 헤더 인식
- 시트별 구조 자동 감지
- 정확한 검증 규칙 적용
- 상세 보고서 생성
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

class UpgradedAuditSystem:
    """개선된 송장 감사 시스템"""
    
    def __init__(self):
        self.excel_file = "SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm"
        self.output_dir = Path("out")
        self.output_dir.mkdir(exist_ok=True)
        
        # 검증 규칙 설정 (상세 매뉴얼 기반)
        self.validation_rules = {
            "fx_rates": {
                "USD_AED": 3.6725,
                "AED_USD": 1/3.6725
            },
            "tolerance_limits": {
                "contract_tolerance": 3.0,  # ±3%
                "cost_guard_fail": 15.0    # >15% 자동 FAIL
            },
            "cost_guard_bands": {
                "PASS": 2.0,      # ≤2%
                "WARN": 5.0,      # 2.01-5%
                "HIGH": 10.0,     # 5.01-10%
                "CRITICAL": 15.0  # 10.01-15%
            }
        }
        
        # 헤더 키워드 확장 (다양한 시트 구조 지원)
        self.header_keywords = [
            'S/No', 'SNo', 'S.No', 'No', 'Item',
            'Rate Source', 'RateSource', 'Source',
            'Description', 'Desc', 'Item Description',
            'Rate', 'Unit Rate', 'Price',
            'Formula', 'Calc', 'Calculation',
            'Qty', 'Quantity', 'Qty.',
            'Total', 'Total (USD)', 'Amount', 'Total Amount',
            'Currency', 'Curr', 'CCY',
            'At Cost', 'At-Cost', 'Cost',
            'Bill to', 'Bill To', 'Customer',
            'Draft Invoice Date', 'Invoice Date', 'Date',
            'Shipment', 'Shipment ID', 'Shipment No'
        ]
    
    def run_complete_audit(self) -> Dict:
        """완전한 감사 실행 (상세 매뉴얼 기반)"""
        print("🚀 개선된 Invoice Audit System 시작")
        print("=" * 60)
        
        # 1. Excel 데이터 로드
        excel_data = self.load_excel_data()
        if not excel_data:
            return None
        
        # 2. 모든 시트에서 송장 데이터 추출
        all_invoice_items = []
        sheet_summaries = {}
        
        for sheet_name, df in excel_data.items():
            print(f"📋 시트 '{sheet_name}' 처리 중...")
            invoice_items = self.extract_invoice_data_advanced(df, sheet_name)
            all_invoice_items.extend(invoice_items)
            
            # 시트별 요약
            sheet_summaries[sheet_name] = self.calculate_sheet_summary(invoice_items)
        
        # 3. 전체 요약 계산
        total_summary = self.calculate_total_summary(all_invoice_items)
        
        # 4. 감사 결과 생성
        audit_result = {
            "audit_metadata": {
                "audit_date": datetime.now().isoformat(),
                "excel_file": self.excel_file,
                "total_sheets": len(excel_data),
                "total_invoice_items": len(all_invoice_items),
                "system_version": "Upgraded v2.0"
            },
            "validation_rules": self.validation_rules,
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
    
    def extract_invoice_data_advanced(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """고급 송장 데이터 추출 (동적 헤더 인식)"""
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
            
            # 4. 송장 항목 추출
            for idx in range(data_start_row, min(data_end_row + 1, len(df))):
                row = df.iloc[idx]
                
                if self.is_valid_invoice_row_advanced(row):
                    item = self.create_invoice_item_advanced(
                        row, sheet_name, idx, header_mapping
                    )
                    if item:
                        invoice_items.append(item)
            
            print(f"  ✅ {len(invoice_items)}개 송장 항목 추출")
            return invoice_items
            
        except Exception as e:
            print(f"❌ 시트 '{sheet_name}' 데이터 추출 오류: {e}")
            return []
    
    def find_header_row_advanced(self, df: pd.DataFrame) -> Optional[int]:
        """고급 헤더 행 찾기 (다양한 구조 지원)"""
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
                elif any(keyword in cell_str.upper() for keyword in ['RATE', 'PRICE', 'UNIT RATE']):
                    mapping['rate'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['QTY', 'QUANTITY']):
                    mapping['quantity'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['TOTAL', 'AMOUNT']):
                    mapping['total'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['CURRENCY', 'CURR', 'CCY']):
                    mapping['currency'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['AT COST', 'AT-COST', 'COST']):
                    mapping['at_cost'] = idx
                elif any(keyword in cell_str.upper() for keyword in ['FORMULA', 'CALC']):
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
    
    def create_invoice_item_advanced(self, row: pd.Series, sheet_name: str, 
                                   row_idx: int, header_mapping: Dict[str, int]) -> Optional[Dict]:
        """고급 송장 항목 생성"""
        try:
            # 기본 정보 추출
            item = {
                "sheet_name": sheet_name,
                "row_number": row_idx + 1,
                "s_no": self.extract_field_value(row, header_mapping, 's_no'),
                "rate_source": self.extract_field_value(row, header_mapping, 'rate_source'),
                "description": self.extract_field_value(row, header_mapping, 'description'),
                "rate": self.extract_numeric_value(row, header_mapping, 'rate'),
                "quantity": self.extract_numeric_value(row, header_mapping, 'quantity'),
                "total_usd": self.extract_numeric_value(row, header_mapping, 'total'),
                "currency": self.extract_field_value(row, header_mapping, 'currency'),
                "at_cost": self.extract_numeric_value(row, header_mapping, 'at_cost'),
                "formula": self.extract_field_value(row, header_mapping, 'formula')
            }
            
            # 계산된 필드
            item["amount_usd"] = self.calculate_amount_usd(item)
            item["delta_percent"] = self.calculate_delta_percent(item)
            item["cost_guard_band"] = self.determine_cost_guard_band(item["delta_percent"])
            item["status"] = self.determine_status_advanced(item)
            item["validation_flags"] = self.generate_validation_flags(item)
            
            return item
            
        except Exception as e:
            print(f"❌ 송장 항목 생성 오류 (행 {row_idx}): {e}")
            return None
    
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
    
    def calculate_amount_usd(self, item: Dict) -> float:
        """USD 금액 계산"""
        if item["currency"] == "USD":
            return item["total_usd"]
        elif item["currency"] == "AED":
            return item["total_usd"] * self.validation_rules["fx_rates"]["AED_USD"]
        else:
            return item["total_usd"]
    
    def calculate_delta_percent(self, item: Dict) -> float:
        """Delta % 계산"""
        if item["at_cost"] > 0 and item["amount_usd"] > 0:
            return ((item["amount_usd"] - item["at_cost"]) / item["at_cost"]) * 100
        return 0.0
    
    def determine_cost_guard_band(self, delta_percent: float) -> str:
        """COST-GUARD 밴드 결정"""
        abs_delta = abs(delta_percent)
        
        if abs_delta <= self.validation_rules["cost_guard_bands"]["PASS"]:
            return "PASS"
        elif abs_delta <= self.validation_rules["cost_guard_bands"]["WARN"]:
            return "WARN"
        elif abs_delta <= self.validation_rules["cost_guard_bands"]["HIGH"]:
            return "HIGH"
        elif abs_delta <= self.validation_rules["cost_guard_bands"]["CRITICAL"]:
            return "CRITICAL"
        else:
            return "COST_GUARD_FAIL"
    
    def determine_status_advanced(self, item: Dict) -> str:
        """고급 상태 결정"""
        # COST-GUARD_FAIL 체크
        if item["cost_guard_band"] == "COST_GUARD_FAIL":
            return "COST_GUARD_FAIL"
        
        # REFERENCE_MISSING 체크 (참조 요율 없음)
        if item["rate_source"] == "" or item["rate_source"] == "Unknown":
            return "REFERENCE_MISSING"
        
        # 일반 상태
        if item["cost_guard_band"] in ["HIGH", "CRITICAL"]:
            return "WARNING"
        else:
            return "PASS"
    
    def generate_validation_flags(self, item: Dict) -> List[str]:
        """검증 플래그 생성"""
        flags = []
        
        if item["delta_percent"] > self.validation_rules["tolerance_limits"]["contract_tolerance"]:
            flags.append("TOLERANCE_EXCEEDED")
        
        if item["amount_usd"] <= 0:
            flags.append("ZERO_AMOUNT")
        
        if item["currency"] not in ["USD", "AED"]:
            flags.append("UNKNOWN_CURRENCY")
        
        if item["rate_source"] == "":
            flags.append("NO_RATE_SOURCE")
        
        return flags
    
    def calculate_sheet_summary(self, invoice_items: List[Dict]) -> Dict:
        """시트별 요약 계산"""
        if not invoice_items:
            return {
                "total_items": 0,
                "pass_items": 0,
                "warning_items": 0,
                "fail_items": 0,
                "total_amount": 0.0,
                "average_delta": 0.0
            }
        
        total_items = len(invoice_items)
        pass_items = len([item for item in invoice_items if item["status"] == "PASS"])
        warning_items = len([item for item in invoice_items if item["status"] == "WARNING"])
        fail_items = len([item for item in invoice_items if item["status"] in ["COST_GUARD_FAIL", "REFERENCE_MISSING"]])
        total_amount = sum(item["amount_usd"] for item in invoice_items)
        average_delta = sum(item["delta_percent"] for item in invoice_items) / total_items
        
        return {
            "total_items": total_items,
            "pass_items": pass_items,
            "warning_items": warning_items,
            "fail_items": fail_items,
            "total_amount": total_amount,
            "average_delta": average_delta
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
                "average_delta_percent": 0.0
            }
        
        total_items = len(all_invoice_items)
        pass_items = len([item for item in all_invoice_items if item["status"] == "PASS"])
        warning_items = len([item for item in all_invoice_items if item["status"] == "WARNING"])
        fail_items = len([item for item in all_invoice_items if item["status"] in ["COST_GUARD_FAIL", "REFERENCE_MISSING"]])
        total_amount = sum(item["amount_usd"] for item in all_invoice_items)
        average_delta = sum(item["delta_percent"] for item in all_invoice_items) / total_items
        
        return {
            "total_items": total_items,
            "pass_items": pass_items,
            "warning_items": warning_items,
            "fail_items": fail_items,
            "pass_rate": (pass_items / total_items * 100) if total_items > 0 else 0,
            "total_amount_usd": total_amount,
            "average_delta_percent": average_delta
        }
    
    def save_audit_report(self, audit_result: Dict) -> str:
        """감사 보고서 저장"""
        try:
            # JSON 보고서 저장
            json_file = self.output_dir / "upgraded_audit_report.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(audit_result, f, indent=2, ensure_ascii=False, default=str)
            
            # CSV 보고서 저장
            csv_file = self.output_dir / "upgraded_audit_report.csv"
            df = pd.DataFrame(audit_result["invoice_items"])
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            # 상세 요약 보고서 저장
            summary_file = self.output_dir / "upgraded_audit_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_detailed_summary_report(audit_result))
            
            print(f"📄 개선된 감사 보고서 저장 완료:")
            print(f"  - JSON: {json_file}")
            print(f"  - CSV: {csv_file}")
            print(f"  - 요약: {summary_file}")
            
            return str(json_file)
            
        except Exception as e:
            print(f"❌ 보고서 저장 오류: {e}")
            return None
    
    def generate_detailed_summary_report(self, audit_result: Dict) -> str:
        """상세 요약 보고서 생성"""
        summary = audit_result["summary"]
        rules = audit_result["validation_rules"]
        
        report = f"""
개선된 Invoice Audit System - 상세 보고서
==========================================

감사 일시: {audit_result['audit_metadata']['audit_date']}
Excel 파일: {audit_result['audit_metadata']['excel_file']}
시스템 버전: {audit_result['audit_metadata']['system_version']}
총 시트 수: {audit_result['audit_metadata']['total_sheets']}개
총 송장 항목: {summary['total_items']}개

📊 전체 요약
-----------
✅ PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)
⚠️ WARNING: {summary['warning_items']}개
❌ FAIL: {summary['fail_items']}개
💰 총 금액: ${summary['total_amount_usd']:,.2f} USD
📈 평균 Delta: {summary['average_delta_percent']:.2f}%

🔧 검증 규칙
-----------
환율: 1 USD = {rules['fx_rates']['USD_AED']} AED
계약 허용치: ±{rules['tolerance_limits']['contract_tolerance']}%
COST-GUARD FAIL: >{rules['tolerance_limits']['cost_guard_fail']}%

밴드 기준:
- PASS: ≤{rules['cost_guard_bands']['PASS']}%
- WARN: {rules['cost_guard_bands']['PASS']}-{rules['cost_guard_bands']['WARN']}%
- HIGH: {rules['cost_guard_bands']['WARN']}-{rules['cost_guard_bands']['HIGH']}%
- CRITICAL: {rules['cost_guard_bands']['HIGH']}-{rules['cost_guard_bands']['CRITICAL']}%
- FAIL: >{rules['cost_guard_bands']['CRITICAL']}%

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
"""
        
        report += f"""
==========================================
감사 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

def main():
    """메인 실행 함수"""
    print("🚀 개선된 Invoice Audit System 실행")
    print("=" * 60)
    
    # 감사 시스템 초기화
    audit_system = UpgradedAuditSystem()
    
    # 완전한 감사 실행
    audit_result = audit_system.run_complete_audit()
    
    if audit_result:
        # 보고서 저장
        report_file = audit_system.save_audit_report(audit_result)
        
        if report_file:
            print(f"\n✅ 개선된 감사 완료! 보고서: {report_file}")
            
            # 요약 출력
            summary = audit_result["summary"]
            print(f"\n📊 최종 요약:")
            print(f"  - 총 송장 항목: {summary['total_items']}개")
            print(f"  - PASS: {summary['pass_items']}개 ({summary['pass_rate']:.1f}%)")
            print(f"  - WARNING: {summary['warning_items']}개")
            print(f"  - FAIL: {summary['fail_items']}개")
            print(f"  - 총 금액: ${summary['total_amount_usd']:,.2f} USD")
        else:
            print("❌ 보고서 저장 실패")
    else:
        print("❌ 감사 실행 실패")

if __name__ == "__main__":
    main()
