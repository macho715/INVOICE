#!/usr/bin/env python3
"""9월 SHPT 인보이스 검증 결과 분석"""

import json
from pathlib import Path
from collections import Counter

def analyze_results():
    """결과 분석 및 리포트 생성"""
    
    # 최신 JSON 결과 로드
    json_path = Path("../Results/Sept_2025/JSON/shpt_sept_2025_enhanced_result_20251014_051700.json")
    
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("9월 SHPT 인보이스 검증 결과 상세 분석")
    print("=" * 80)
    
    # 1. 전체 통계
    stats = data['statistics']
    print(f"\n📊 전체 통계:")
    print(f"  총 항목: {stats['total_items']}개")
    print(f"  PASS: {stats['pass_items']}개 ({stats['pass_rate']})")
    print(f"  검토 필요: {stats['review_items']}개")
    print(f"  FAIL: {stats['fail_items']}개")
    print(f"  총 금액: ${stats['total_amount_usd']:,.2f} USD")
    
    # 2. Gate 검증
    gate_stats = stats['gate_validation']
    print(f"\n🚪 Gate 검증:")
    print(f"  Gate PASS: {gate_stats['gate_pass_items']}개 ({gate_stats['gate_pass_rate']})")
    print(f"  평균 Gate Score: {gate_stats['avg_gate_score']}")
    
    # 3. Charge Group 분석
    print(f"\n💰 Charge Group 분석:")
    for group, count in stats['charge_group_breakdown'].items():
        print(f"  {group}: {count}개")
    
    # 4. FAIL 항목 상세 분석
    items = data['items']
    fail_items = [i for i in items if i.get('status') == 'FAIL']
    
    print(f"\n❌ FAIL 항목 상세 ({len(fail_items)}건):")
    
    # Rate Source별 FAIL 분석
    fail_by_source = Counter([i.get('rate_source', 'Unknown') for i in fail_items])
    print(f"\n  Rate Source별:")
    for source, count in fail_by_source.most_common():
        print(f"    - {source}: {count}건")
    
    # Gate Score 분포
    gate_scores = [i.get('gate_score', 0) for i in fail_items if i.get('gate_score')]
    if gate_scores:
        avg_fail_gate_score = sum(gate_scores) / len(gate_scores)
        print(f"\n  평균 Gate Score (FAIL 항목): {avg_fail_gate_score:.1f}")
    
    # FAIL 항목 샘플
    print(f"\n  FAIL 항목 샘플 (상위 5건):")
    for i, item in enumerate(fail_items[:5], 1):
        desc = item.get('description', 'N/A')[:60]
        print(f"\n    {i}. S/No {item.get('s_no', 'N/A')}")
        print(f"       Description: {desc}...")
        print(f"       Rate Source: {item.get('rate_source', 'N/A')}")
        print(f"       Gate Score: {item.get('gate_score', 'N/A')}")
        
        # Gate 상세
        gates = item.get('gates', {})
        failed_gates = [k for k, v in gates.items() if v.get('status') == 'FAIL']
        if failed_gates:
            print(f"       Failed Gates: {', '.join(failed_gates)}")
    
    # 5. 검토 필요 항목 분석
    review_items = [i for i in items if i.get('status') == 'REVIEW']
    print(f"\n\n⚠️ 검토 필요 항목 ({len(review_items)}건):")
    
    review_by_source = Counter([i.get('rate_source', 'Unknown') for i in review_items])
    print(f"\n  Rate Source별:")
    for source, count in review_by_source.most_common():
        print(f"    - {source}: {count}건")
    
    # 6. PDF 검증 상태
    print(f"\n\n📄 PDF 검증 상태:")
    pdf_enabled_items = [i for i in items if i.get('pdf_validation', {}).get('enabled')]
    print(f"  PDF 검증 활성화된 항목: {len(pdf_enabled_items)}개")
    
    if pdf_enabled_items:
        pdf_pass = [i for i in pdf_enabled_items if i.get('pdf_validation', {}).get('cross_doc_status') == 'PASS']
        pdf_fail = [i for i in pdf_enabled_items if i.get('pdf_validation', {}).get('cross_doc_status') == 'FAIL']
        print(f"  PDF 검증 PASS: {len(pdf_pass)}개")
        print(f"  PDF 검증 FAIL: {len(pdf_fail)}개")
    
    # 7. 주요 이슈 요약
    print(f"\n\n🔍 주요 이슈 요약:")
    print(f"  1. Gate 통과율 낮음: {gate_stats['gate_pass_rate']} (목표: >80%)")
    print(f"  2. 검토 필요 항목 많음: {stats['review_items']}개 ({stats['review_items']/stats['total_items']*100:.1f}%)")
    print(f"  3. FAIL 항목: {stats['fail_items']}개 - 주로 {fail_by_source.most_common(1)[0][0]} 관련")
    
    # 8. 액션 아이템
    print(f"\n\n✅ 권장 액션 아이템:")
    print(f"  1. FAIL {len(fail_items)}건 → Rate Source 재확인 필요")
    print(f"  2. 검토 필요 {len(review_items)}건 → 수동 검토 및 승인")
    print(f"  3. Gate Score 낮은 항목 → 증빙서류 보완")
    print(f"  4. PDF 검증 실패 항목 → Cross-document 불일치 해결")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_results()

