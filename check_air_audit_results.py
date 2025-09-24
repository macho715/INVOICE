#!/usr/bin/env python3
"""
항공 운송 감사 결과 확인 스크립트
"""

import json

def main():
    # JSON 보고서 로드
    with open('out/shpt_air_audit_report.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✈️ SHPT 항공 운송 감사 결과")
    print("=" * 50)
    print(f"총 항목: {data['audit_info']['total_items']}개")
    print(f"PASS: {data['statistics']['pass_items']}개")
    print(f"FAIL: {data['statistics']['fail_items']}개")
    print(f"성공률: {data['statistics']['pass_rate']}")
    
    print("\n📋 SIM0092 시트 항목들:")
    sim0092_items = [item for item in data['validation_results'] if item['sheet_name'] == 'SIM0092']
    for item in sim0092_items:
        print(f"- {item['item_code']}: {item['description']}")
        if 'validations' in item and 'amount_consistency' in item['validations']:
            actual = item['validations']['amount_consistency'].get('actual', 0)
            print(f"  금액: ${actual:.2f}")
    
    print(f"\n📊 항공 운송 전용 검증 규칙:")
    for key, value in data['air_specific_validations'].items():
        print(f"- {key}: {value}")

if __name__ == "__main__":
    main()
