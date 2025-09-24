"""
Invoice Audit System 실행 스크립트

SCNT SHIPMENT DRAFT INVOICE (AUG 2025) FINAL.xlsm 파일을 처리하여
송장 감사를 수행합니다.
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 개선된 모듈들 import
sys.path.append('.')
from audit_runner_improved import AuditRunner, AuditResult, InvoiceData
from joiners_improved import DataJoiner, CurrencyNormalizer
from rules_improved import RulesEngine, ExchangeRateManager

class InvoiceAuditSystem:
    """송장 감사 시스템 메인 클래스"""
    
    def __init__(self):
        self.audit_runner = AuditRunner()
        self.data_joiner = DataJoiner()
        self.rules_engine = RulesEngine()
        self.currency_normalizer = CurrencyNormalizer()
        self.exchange_rate_manager = ExchangeRateManager()
        
    def load_invoice_data(self, csv_file_path: str) -> List[InvoiceData]:
        """CSV 파일에서 송장 데이터 로드"""
        try:
            print(f"송장 데이터 로드 중: {csv_file_path}")
            
            # CSV 파일 읽기
            df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
            
            # 실제 데이터 행 찾기 (헤더 제외)
            data_start_row = self._find_data_start_row(df)
            if data_start_row is None:
                print("❌ 유효한 데이터를 찾을 수 없습니다.")
                return []
            
            # 데이터 추출
            invoice_data = []
            for idx, row in df.iloc[data_start_row:].iterrows():
                if self._is_valid_invoice_row(row):
                    invoice = self._create_invoice_from_row(row, idx)
                    if invoice:
                        invoice_data.append(invoice)
            
            print(f"✅ {len(invoice_data)}개의 송장 항목을 로드했습니다.")
            return invoice_data
            
        except Exception as e:
            print(f"❌ 송장 데이터 로드 오류: {e}")
            return []
    
    def _find_data_start_row(self, df: pd.DataFrame) -> int:
        """실제 데이터가 시작하는 행 찾기"""
        for idx, row in df.iterrows():
            # 'Bill to:' 또는 'Draft Invoice Date:' 같은 키워드 찾기
            row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
            if 'Bill to:' in row_str or 'Draft Invoice Date:' in row_str:
                return idx + 1  # 다음 행부터 데이터
        return None
    
    def _is_valid_invoice_row(self, row: pd.Series) -> bool:
        """유효한 송장 행인지 확인"""
        # 빈 행이 아닌지 확인
        non_null_count = row.notna().sum()
        return non_null_count > 3  # 최소 3개 이상의 값이 있어야 함
    
    def _create_invoice_from_row(self, row: pd.Series, row_idx: int) -> InvoiceData:
        """행 데이터에서 InvoiceData 객체 생성"""
        try:
            # 기본 데이터 추출 (실제 구조에 맞게 수정 필요)
            invoice_id = f"INV_{row_idx:04d}"
            amount = self._extract_amount(row)
            currency = self._extract_currency(row)
            description = self._extract_description(row)
            
            return InvoiceData(
                invoice_id=invoice_id,
                amount=amount,
                currency=currency,
                description=description,
                date=datetime.now(),
                status="pending"
            )
        except Exception as e:
            print(f"송장 데이터 생성 오류 (행 {row_idx}): {e}")
            return None
    
    def _extract_amount(self, row: pd.Series) -> float:
        """행에서 금액 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell)
                # 숫자 패턴 찾기
                import re
                numbers = re.findall(r'[\d,]+\.?\d*', cell_str)
                if numbers:
                    try:
                        return float(numbers[0].replace(',', ''))
                    except:
                        continue
        return 0.0
    
    def _extract_currency(self, row: pd.Series) -> str:
        """행에서 통화 추출"""
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell)
                # 통화 코드 패턴 찾기
                import re
                currency_match = re.search(r'[A-Z]{3}', cell_str)
                if currency_match:
                    return currency_match.group()
        return "USD"  # 기본값
    
    def _extract_description(self, row: pd.Series) -> str:
        """행에서 설명 추출"""
        descriptions = []
        for cell in row:
            if pd.notna(cell):
                cell_str = str(cell)
                if len(cell_str) > 5 and not cell_str.isdigit():
                    descriptions.append(cell_str)
        return " | ".join(descriptions[:3])  # 최대 3개 설명
    
    def run_audit(self, invoice_data: List[InvoiceData]) -> AuditResult:
        """송장 감사 실행"""
        try:
            print(f"\n🔍 송장 감사 시작: {len(invoice_data)}개 항목")
            
            # 1. 통화 정규화
            print("1️⃣ 통화 코드 정규화 중...")
            normalized_data = []
            for invoice in invoice_data:
                normalized_currency = self.currency_normalizer.normalize(invoice.currency)
                invoice.currency = normalized_currency
                normalized_data.append(invoice)
            
            # 2. 환율 적용
            print("2️⃣ 환율 적용 중...")
            for invoice in normalized_data:
                if invoice.currency != "USD":
                    try:
                        rate = self.exchange_rate_manager.get_exchange_rate(invoice.currency, "USD")
                        invoice.amount_usd = invoice.amount * rate
                    except:
                        invoice.amount_usd = invoice.amount
                else:
                    invoice.amount_usd = invoice.amount
            
            # 3. 비즈니스 규칙 검증
            print("3️⃣ 비즈니스 규칙 검증 중...")
            validation_results = []
            for invoice in normalized_data:
                result = self.rules_engine.validate_invoice(invoice)
                validation_results.append(result)
            
            # 4. 감사 결과 생성
            print("4️⃣ 감사 결과 생성 중...")
            audit_result = self.audit_runner.generate_audit_report(normalized_data, validation_results)
            
            print("✅ 감사 완료!")
            return audit_result
            
        except Exception as e:
            print(f"❌ 감사 실행 오류: {e}")
            return None
    
    def save_results(self, audit_result: AuditResult, output_file: str = "audit_results.json"):
        """감사 결과 저장"""
        try:
            # 결과를 JSON으로 변환
            result_data = {
                "audit_date": datetime.now().isoformat(),
                "total_invoices": audit_result.total_invoices,
                "total_amount": audit_result.total_amount,
                "total_amount_usd": audit_result.total_amount_usd,
                "validation_results": [
                    {
                        "invoice_id": vr.invoice_id,
                        "is_valid": vr.is_valid,
                        "errors": vr.errors,
                        "warnings": vr.warnings
                    } for vr in audit_result.validation_results
                ],
                "summary": {
                    "valid_invoices": audit_result.valid_invoices,
                    "invalid_invoices": audit_result.invalid_invoices,
                    "total_errors": audit_result.total_errors,
                    "total_warnings": audit_result.total_warnings
                }
            }
            
            # JSON 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"📄 감사 결과 저장: {output_file}")
            
        except Exception as e:
            print(f"❌ 결과 저장 오류: {e}")

def main():
    """메인 실행 함수"""
    print("🚀 Invoice Audit System 실행")
    print("=" * 50)
    
    # 감사 시스템 초기화
    audit_system = InvoiceAuditSystem()
    
    # CSV 파일 목록 가져오기
    io_dir = Path("io")
    if not io_dir.exists():
        print("❌ io 디렉토리를 찾을 수 없습니다.")
        return
    
    csv_files = list(io_dir.glob("*.csv"))
    if not csv_files:
        print("❌ CSV 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 CSV 파일: {len(csv_files)}개")
    
    # 첫 번째 CSV 파일로 테스트 실행
    test_file = csv_files[0]
    print(f"🧪 테스트 파일: {test_file.name}")
    
    # 송장 데이터 로드
    invoice_data = audit_system.load_invoice_data(str(test_file))
    
    if not invoice_data:
        print("❌ 송장 데이터를 로드할 수 없습니다.")
        return
    
    # 감사 실행
    audit_result = audit_system.run_audit(invoice_data)
    
    if audit_result:
        # 결과 저장
        audit_system.save_results(audit_result)
        
        # 결과 요약 출력
        print(f"\n📊 감사 결과 요약:")
        print(f"  - 총 송장 수: {audit_result.total_invoices}")
        print(f"  - 총 금액: ${audit_result.total_amount_usd:,.2f} USD")
        print(f"  - 유효한 송장: {audit_result.valid_invoices}")
        print(f"  - 무효한 송장: {audit_result.invalid_invoices}")
        print(f"  - 총 오류: {audit_result.total_errors}")
        print(f"  - 총 경고: {audit_result.total_warnings}")
    else:
        print("❌ 감사 실행 실패")

if __name__ == "__main__":
    main()
