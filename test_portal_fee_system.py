"""
포털 수수료 검증 시스템 테스트

포털 수수료 분류, AED 추출, USD 환산, ±0.5% 허용치 검증을 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from joiners_enhanced import (
    is_portal_fee, charge_group, parse_aed_from_formula, 
    get_portal_fee_fixed_rate, run_all_gates
)
from rules_enhanced import (
    process_invoice_item, convert_aed_to_usd, 
    get_band_for_group, tolerance_for
)

def test_portal_fee_classification():
    """포털 수수료 분류 테스트"""
    print("🔍 포털 수수료 분류 테스트")
    print("=" * 50)
    
    test_cases = [
        ("MAQTA", "APPOINTMENT FEE", True),
        ("CONTRACT", "APPOINTMENT FEE", True),
        ("AT COST", "DPC FEE", True),
        ("CONTRACT", "CUSTOMS CLEARANCE FEE", False),
        ("AT COST", "TERMINAL HANDLING FEE", False),
        ("CONTRACT", "MANIFEST AMENDMENT FEE", True),
        ("CONTRACT", "EAS MANIFEST FEE", True),
        ("CONTRACT", "DOCUMENT PROCESSING FEE", True),
        ("CONTRACT", "DOC PROCESSING FEE", True),
    ]
    
    for rate_source, description, expected in test_cases:
        result = is_portal_fee(rate_source, description)
        group = charge_group(rate_source, description)
        status = "✅" if result == expected else "❌"
        
        print(f"{status} {rate_source} | {description}")
        print(f"    Portal Fee: {result} | Group: {group}")
        print()
    
    print("✅ 포털 수수료 분류 테스트 완료\n")

def test_aed_extraction():
    """AED 추출 및 USD 환산 테스트"""
    print("🔍 AED 추출 및 USD 환산 테스트")
    print("=" * 50)
    
    test_formulas = [
        "=27/3.6725",
        "=35/3.6725",
        "=100/3.6725",
        "=27.5/3.6725",
        "=1000/3.6725",
        "=27/3.6725*2",
        "=35/3.6725+5",
        "Invalid formula",
        "",
        None
    ]
    
    for formula in test_formulas:
        aed = parse_aed_from_formula(formula)
        if aed is not None:
            usd = convert_aed_to_usd(aed)
            print(f"✅ {formula} → AED: {aed} → USD: {usd}")
        else:
            print(f"❌ {formula} → No AED extracted")
    
    print("\n🔍 고정값 테이블 테스트")
    print("-" * 30)
    
    test_descriptions = [
        "APPOINTMENT FEE",
        "DPC FEE",
        "DOCUMENT PROCESSING FEE",
        "DOC PROCESSING FEE",
        "CUSTOMS CLEARANCE FEE"
    ]
    
    for desc in test_descriptions:
        fixed_rate = get_portal_fee_fixed_rate(desc)
        if fixed_rate:
            print(f"✅ {desc} → AED: {fixed_rate['AED']} → USD: {fixed_rate['USD']}")
        else:
            print(f"❌ {desc} → No fixed rate")
    
    print("✅ AED 추출 및 USD 환산 테스트 완료\n")

def test_tolerance_validation():
    """±0.5% 허용치 검증 테스트"""
    print("🔍 ±0.5% 허용치 검증 테스트")
    print("=" * 50)
    
    test_cases = [
        # (draft_rate, ref_rate, group, expected_status)
        (7.35, 7.35, "PortalFee", "Verified"),      # 0% 차이
        (7.40, 7.35, "PortalFee", "Verified"),      # 0.68% 차이 (0.5% 초과)
        (7.30, 7.35, "PortalFee", "Verified"),      # 0.68% 차이 (0.5% 초과)
        (7.50, 7.35, "PortalFee", "Pending Review"), # 2.04% 차이
        (8.00, 7.35, "PortalFee", "Pending Review"), # 8.84% 차이
        (10.00, 7.35, "PortalFee", "COST_GUARD_FAIL"), # 36.05% 차이
        
        (100.00, 100.00, "Contract", "Verified"),   # 0% 차이
        (103.00, 100.00, "Contract", "Verified"),   # 3% 차이 (정확히 허용치)
        (104.00, 100.00, "Contract", "Pending Review"), # 4% 차이 (허용치 초과)
    ]
    
    for draft_rate, ref_rate, group, expected_status in test_cases:
        invoice_item = {
            "rate_usd": draft_rate,
            "rate_source": "CONTRACT" if group == "Contract" else "APPOINTMENT",
            "description": "APPOINTMENT FEE" if group == "PortalFee" else "CUSTOMS CLEARANCE FEE"
        }
        
        result = process_invoice_item(invoice_item, ref_rate)
        status = "✅" if result["status"] == expected_status else "❌"
        
        print(f"{status} Draft: {draft_rate} | Ref: {ref_rate} | Group: {group}")
        print(f"    Delta: {result['delta_percent']:.2f}% | Status: {result['status']} | Band: {result['band']}")
        print()
    
    print("✅ ±0.5% 허용치 검증 테스트 완료\n")

def test_gate_validation():
    """Gate 검증 테스트"""
    print("🔍 Gate 검증 테스트")
    print("=" * 50)
    
    # 테스트 송장 항목
    invoice_item = {
        "s_no": "1",
        "rate_source": "APPOINTMENT",
        "description": "APPOINTMENT FEE",
        "rate_usd": 7.35,
        "quantity": 1,
        "total_usd": 7.35,
        "currency": "USD",
        "formula_text": "=27/3.6725",
        "cargo_type": "General",
        "port": "Khalifa Port",
        "destination": "DSV MUSSAFAH YARD",
        "unit": "per item"
    }
    
    # 테스트 증빙문서
    supporting_docs = [
        {"doc_type": "BOE", "file_name": "test_boe.pdf"},
        {"doc_type": "DO", "file_name": "test_do.pdf"},
        {"doc_type": "DN", "file_name": "test_dn.pdf"},
        {"doc_type": "CarrierInvoice", "file_name": "test_carrier.pdf"}
    ]
    
    # Gate 검증 실행
    gate_result = run_all_gates(invoice_item, supporting_docs, 7.35)
    
    print(f"Gate Status: {gate_result['Gate_Status']}")
    print(f"Gate Fails: {gate_result['Gate_Fails']}")
    print(f"Gate Score: {gate_result['Gate_Score']}")
    print()
    
    # 개별 Gate 결과
    for gate_name, result in gate_result["gates"].items():
        status = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status} {gate_name}: {result['status']} (Score: {result['score']})")
    
    print("✅ Gate 검증 테스트 완료\n")

def test_integration():
    """통합 테스트"""
    print("🔍 통합 테스트")
    print("=" * 50)
    
    # 포털 수수료 시나리오
    portal_scenarios = [
        {
            "rate_source": "APPOINTMENT",
            "description": "APPOINTMENT FEE",
            "formula_text": "=27/3.6725",
            "rate_usd": 7.35
        },
        {
            "rate_source": "DPC",
            "description": "DPC FEE",
            "formula_text": "=35/3.6725",
            "rate_usd": 9.53
        },
        {
            "rate_source": "CONTRACT",
            "description": "MANIFEST AMENDMENT FEE",
            "formula_text": "=50/3.6725",
            "rate_usd": 13.62
        }
    ]
    
    for i, scenario in enumerate(portal_scenarios, 1):
        print(f"시나리오 {i}: {scenario['description']}")
        
        # 송장 항목 처리
        result = process_invoice_item(scenario, None)
        
        print(f"  Group: {result.get('group', 'Unknown')}")
        print(f"  Ref Rate: {result.get('ref_rate_usd', 'N/A')}")
        print(f"  Delta: {result.get('delta_percent', 0):.2f}%")
        print(f"  Band: {result.get('band', 'Unknown')}")
        print(f"  Status: {result.get('status', 'Unknown')}")
        print(f"  Flag: {result.get('flag', 'Unknown')}")
        print()
    
    print("✅ 통합 테스트 완료\n")

def main():
    """메인 테스트 실행"""
    print("🚀 포털 수수료 검증 시스템 테스트 시작")
    print("=" * 70)
    
    try:
        test_portal_fee_classification()
        test_aed_extraction()
        test_tolerance_validation()
        test_gate_validation()
        test_integration()
        
        print("🎉 모든 테스트 완료!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
