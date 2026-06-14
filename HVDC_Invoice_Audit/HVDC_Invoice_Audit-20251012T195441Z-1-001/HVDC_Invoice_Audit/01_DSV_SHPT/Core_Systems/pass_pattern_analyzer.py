#!/usr/bin/env python3
"""
PASS 케이스 패턴 분석기
====================

PASS 항목의 성공 패턴을 식별하여 FAIL 케이스에 적용
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List

def analyze_pass_patterns():
    """PASS 항목의 성공 패턴 분석"""
    
    # 최신 2개 결과 비교 (Before/After PDF Integration)
    json_dir = Path("../Results/Sept_2025/JSON")
    json_files = sorted(json_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    latest_file = json_files[0]
    previous_file = json_files[1] if len(json_files) > 1 else None
    
    print("=" * 80)
    print("PASS 케이스 패턴 분석")
    print("=" * 80)
    print(f"\n최신 결과: {latest_file.name}")
    if previous_file:
        print(f"이전 결과: {previous_file.name}")
    
    # 최신 결과 로드
    with open(latest_file, encoding='utf-8') as f:
        latest_data = json.load(f)
    
    items = latest_data['items']
    
    # PASS vs FAIL 분류
    pass_items = [i for i in items if i.get('status') == 'PASS']
    fail_items = [i for i in items if i.get('status') == 'FAIL']
    review_items = [i for i in items if i.get('status') == 'REVIEW']
    
    print(f"\n📊 현재 통계:")
    print(f"  PASS: {len(pass_items)}개")
    print(f"  FAIL: {len(fail_items)}개")
    print(f"  REVIEW: {len(review_items)}개")
    
    if previous_file:
        with open(previous_file, encoding='utf-8') as f:
            prev_data = json.load(f)
        prev_pass = len([i for i in prev_data['items'] if i.get('status') == 'PASS'])
        prev_fail = len([i for i in prev_data['items'] if i.get('status') == 'FAIL'])
        
        print(f"\n📈 PDF Integration 전후 비교:")
        print(f"  PASS 변화: {prev_pass}개 → {len(pass_items)}개 ({len(pass_items)-prev_pass:+d})")
        print(f"  FAIL 변화: {prev_fail}개 → {len(fail_items)}개 ({len(fail_items)-prev_fail:+d})")
    
    # PASS 패턴 분석
    print(f"\n\n✅ PASS 케이스 분석 ({len(pass_items)}개)")
    print("=" * 80)
    
    # 1. Rate Source 분석
    pass_rate_sources = Counter([i.get('rate_source', 'Unknown') for i in pass_items])
    fail_rate_sources = Counter([i.get('rate_source', 'Unknown') for i in fail_items])
    
    print(f"\n1️⃣ Rate Source 분석:")
    print(f"\n  PASS 항목:")
    for source, count in pass_rate_sources.most_common():
        total_source = len([i for i in items if i.get('rate_source') == source])
        success_rate = (count / total_source * 100) if total_source > 0 else 0
        print(f"    {source}: {count}개 (성공률 {success_rate:.1f}%)")
    
    print(f"\n  FAIL 항목:")
    for source, count in fail_rate_sources.most_common():
        total_source = len([i for i in items if i.get('rate_source') == source])
        fail_rate = (count / total_source * 100) if total_source > 0 else 0
        print(f"    {source}: {count}개 (실패율 {fail_rate:.1f}%)")
    
    # 2. Gate Score 분석
    pass_gate_scores = [i.get('gate_score', 0) for i in pass_items if i.get('gate_score')]
    fail_gate_scores = [i.get('gate_score', 0) for i in fail_items if i.get('gate_score')]
    
    print(f"\n2️⃣ Gate Score 분석:")
    if pass_gate_scores:
        avg_pass_score = sum(pass_gate_scores) / len(pass_gate_scores)
        min_pass_score = min(pass_gate_scores)
        max_pass_score = max(pass_gate_scores)
        print(f"  PASS 평균: {avg_pass_score:.1f} (범위: {min_pass_score:.1f}-{max_pass_score:.1f})")
    
    if fail_gate_scores:
        avg_fail_score = sum(fail_gate_scores) / len(fail_gate_scores)
        min_fail_score = min(fail_gate_scores)
        max_fail_score = max(fail_gate_scores)
        print(f"  FAIL 평균: {avg_fail_score:.1f} (범위: {min_fail_score:.1f}-{max_fail_score:.1f})")
    
    # 3. PDF 검증 분석
    pass_with_pdf = [i for i in pass_items if i.get('pdf_validation', {}).get('enabled')]
    fail_with_pdf = [i for i in fail_items if i.get('pdf_validation', {}).get('enabled')]
    
    print(f"\n3️⃣ PDF 검증 활성화 분석:")
    print(f"  PASS 중 PDF 검증: {len(pass_with_pdf)}개")
    print(f"  FAIL 중 PDF 검증: {len(fail_with_pdf)}개")
    
    if pass_with_pdf:
        pdf_pass_cross_doc = [i for i in pass_with_pdf if i.get('pdf_validation', {}).get('cross_doc_status') == 'PASS']
        print(f"  Cross-document PASS: {len(pdf_pass_cross_doc)}개")
    
    # 4. Description 패턴 분석
    print(f"\n4️⃣ Description 패턴 분석 (PASS 케이스):")
    pass_descriptions = Counter([i.get('description', 'N/A')[:60] for i in pass_items])
    for desc, count in pass_descriptions.most_common(10):
        print(f"  {count}건: {desc}...")
    
    # 5. PASS 케이스의 공통점
    print(f"\n\n🔍 PASS 케이스의 성공 요인:")
    print("=" * 80)
    
    success_factors = []
    
    # Gate 통과 패턴
    pass_with_high_gate = [i for i in pass_items if i.get('gate_score', 0) >= 90]
    if pass_with_high_gate:
        success_factors.append(f"✅ High Gate Score (≥90): {len(pass_with_high_gate)}개")
    
    # Rate Source 성공률
    for source, count in pass_rate_sources.most_common(3):
        success_factors.append(f"✅ {source} Rate: {count}개 항목 성공")
    
    # PDF 검증 성공
    if pass_with_pdf:
        success_factors.append(f"✅ PDF Cross-document 검증 통과: {len(pass_with_pdf)}개")
    
    for factor in success_factors:
        print(f"  {factor}")
    
    # 6. FAIL 케이스 분석
    print(f"\n\n❌ FAIL 케이스 분석 ({len(fail_items)}개)")
    print("=" * 80)
    
    fail_reasons = defaultdict(list)
    
    for item in fail_items:
        # Gate 상세 확인
        gates = item.get('gates', {})
        failed_gates = [k for k, v in gates.items() if v.get('status') == 'FAIL']
        
        if failed_gates:
            for gate in failed_gates:
                fail_reasons[gate].append(item.get('s_no', 'N/A'))
        
        # Rate Source 확인
        rate_source = item.get('rate_source', 'Unknown')
        if rate_source == 'CONTRACT':
            fail_reasons['CONTRACT_RATE_MISMATCH'].append(item.get('s_no', 'N/A'))
    
    print("\n  실패 원인별:")
    for reason, s_nos in sorted(fail_reasons.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"    {reason}: {len(s_nos)}건")
        if len(s_nos) <= 5:
            print(f"      → S/No: {s_nos}")
    
    # 7. 적용 가능한 패턴
    print(f"\n\n🔧 FAIL 케이스에 적용 가능한 패턴:")
    print("=" * 80)
    
    recommendations = []
    
    # Rate Source 기반 개선
    if fail_rate_sources.get('CONTRACT', 0) > 0:
        recommendations.append({
            'issue': 'CONTRACT Rate 매칭 실패',
            'count': fail_rate_sources['CONTRACT'],
            'solution': 'Rate Loader 규칙 추가 또는 Contract Rate 데이터 업데이트',
            'priority': 'HIGH'
        })
    
    # Gate Score 기반 개선
    if fail_gate_scores:
        low_score_fails = [i for i in fail_items if i.get('gate_score', 0) < 70]
        if low_score_fails:
            recommendations.append({
                'issue': 'Low Gate Score',
                'count': len(low_score_fails),
                'solution': '증빙서류 보완 또는 Gate 검증 로직 개선',
                'priority': 'MEDIUM'
            })
    
    # PDF 검증 미실행
    fail_without_pdf = [i for i in fail_items if not i.get('pdf_validation', {}).get('enabled')]
    if fail_without_pdf:
        recommendations.append({
            'issue': 'PDF 검증 미실행',
            'count': len(fail_without_pdf),
            'solution': 'Supporting Documents 폴더 구조 확인 및 PDF 파일 매칭 개선',
            'priority': 'MEDIUM'
        })
    
    for idx, rec in enumerate(recommendations, 1):
        print(f"\n  {idx}. [{rec['priority']}] {rec['issue']} ({rec['count']}건)")
        print(f"     해결책: {rec['solution']}")
    
    # 8. PASS 패턴 문서화
    print(f"\n\n📝 성공 패턴 요약:")
    print("=" * 80)
    
    pattern_summary = {
        'rate_source_success_order': list(pass_rate_sources.keys()),
        'avg_gate_score': avg_pass_score if pass_gate_scores else 0,
        'pdf_validation_correlation': len(pass_with_pdf) / len(pass_items) * 100 if pass_items else 0,
        'common_descriptions': [desc for desc, _ in pass_descriptions.most_common(5)],
        'improvement_recommendations': recommendations
    }
    
    # JSON으로 저장
    output_file = Path("../Results/Sept_2025/Reports/pass_pattern_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pattern_summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n패턴 분석 결과 저장: {output_file}")
    
    return pattern_summary

if __name__ == "__main__":
    analyze_pass_patterns()

