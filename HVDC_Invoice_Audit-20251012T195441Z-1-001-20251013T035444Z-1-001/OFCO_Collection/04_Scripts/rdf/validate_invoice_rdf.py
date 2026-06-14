#!/usr/bin/env python3
"""
Invoice RDF 검증 스크립트
생성된 RDF 파일의 구문과 구조를 검증
"""

import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from rdflib import Graph
from pathlib import Path
from typing import Dict, List, Any
import json


def validate_rdf_syntax(ttl_file: str) -> Dict[str, Any]:
    """RDF 구문 검증"""
    print(f"[INFO] Validating RDF syntax: {ttl_file}")

    try:
        g = Graph()
        g.parse(ttl_file, format="turtle")

        return {
            "valid": True,
            "triple_count": len(g),
            "namespaces": list(g.namespaces()),
            "subjects": len(set(g.subjects())),
            "predicates": len(set(g.predicates())),
            "objects": len(set(g.objects())),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def analyze_invoice_entities(g: Graph) -> Dict[str, Any]:
    """Invoice 엔티티 분석"""
    print("[INFO] Analyzing Invoice entities...")

    # Invoice 엔티티 찾기
    hvdc_ns = g.namespace_manager.namespace("hvdc")
    invoice_type = hvdc_ns["Invoice"]

    invoices = list(g.subjects(predicate=None, object=invoice_type))

    analysis = {
        "total_invoices": len(invoices),
        "invoice_details": [],
        "property_stats": {},
        "data_quality": {
            "missing_titles": 0,
            "missing_amounts": 0,
            "missing_currencies": 0,
            "invalid_dates": 0,
        },
    }

    for invoice in invoices:
        # Invoice 속성 수집
        properties = {}
        for p, o in g.predicate_objects(subject=invoice):
            prop_name = str(p).split("#")[-1] if "#" in str(p) else str(p)
            properties[prop_name] = str(o)

        # Invoice 상세 정보
        invoice_detail = {
            "uri": str(invoice),
            "properties": properties,
            "property_count": len(properties),
        }
        analysis["invoice_details"].append(invoice_detail)

        # 속성 통계
        for prop_name in properties.keys():
            analysis["property_stats"][prop_name] = (
                analysis["property_stats"].get(prop_name, 0) + 1
            )

        # 데이터 품질 검사
        if not properties.get("title") or properties.get("title") == "":
            analysis["data_quality"]["missing_titles"] += 1
        if not properties.get("totalAmount") or properties.get("totalAmount") == "0":
            analysis["data_quality"]["missing_amounts"] += 1
        if not properties.get("currency") or properties.get("currency") == "":
            analysis["data_quality"]["missing_currencies"] += 1

    return analysis


def check_data_consistency(g: Graph) -> Dict[str, Any]:
    """데이터 일관성 검사"""
    print("[INFO] Checking data consistency...")

    hvdc_ns = g.namespace_manager.namespace("hvdc")

    consistency_checks = {
        "currency_consistency": True,
        "date_format_consistency": True,
        "amount_format_consistency": True,
        "issues": [],
    }

    # 통화 일관성 검사
    currencies = set()
    for s, p, o in g.triples((None, hvdc_ns["currency"], None)):
        currencies.add(str(o))

    if len(currencies) > 10:  # 너무 많은 다른 통화가 있으면 의심
        consistency_checks["currency_consistency"] = False
        consistency_checks["issues"].append(
            f"Too many different currencies: {len(currencies)}"
        )

    # 날짜 형식 검사
    date_issues = 0
    for s, p, o in g.triples((None, hvdc_ns["invoiceDate"], None)):
        date_str = str(o)
        if date_str == "0" or date_str == "":
            date_issues += 1

    if date_issues > 0:
        consistency_checks["date_format_consistency"] = False
        consistency_checks["issues"].append(f"Invalid dates found: {date_issues}")

    return consistency_checks


def generate_validation_report(ttl_file: str) -> Dict[str, Any]:
    """검증 보고서 생성"""
    print(f"[INFO] Generating validation report for: {ttl_file}")

    # RDF 구문 검증
    syntax_result = validate_rdf_syntax(ttl_file)

    if not syntax_result["valid"]:
        return {"file": ttl_file, "valid": False, "error": syntax_result["error"]}

    # RDF 그래프 로드
    g = Graph()
    g.parse(ttl_file, format="turtle")

    # 엔티티 분석
    entity_analysis = analyze_invoice_entities(g)

    # 일관성 검사
    consistency_checks = check_data_consistency(g)

    # 전체 검증 결과
    validation_result = {
        "file": ttl_file,
        "valid": True,
        "syntax": syntax_result,
        "entities": entity_analysis,
        "consistency": consistency_checks,
        "summary": {
            "total_triples": syntax_result["triple_count"],
            "total_invoices": entity_analysis["total_invoices"],
            "data_quality_score": calculate_quality_score(
                entity_analysis["data_quality"], entity_analysis["total_invoices"]
            ),
            "overall_status": (
                "PASS"
                if consistency_checks["currency_consistency"]
                and consistency_checks["date_format_consistency"]
                else "WARNING"
            ),
        },
    }

    return validation_result


def calculate_quality_score(data_quality: Dict[str, int], total_invoices: int) -> float:
    """데이터 품질 점수 계산 (0-100)"""
    if total_invoices == 0:
        return 0.0

    issues = sum(data_quality.values())
    score = max(0, 100 - (issues / total_invoices) * 100)
    return round(score, 2)


def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("Usage: python validate_invoice_rdf.py <ttl_file>")
        sys.exit(1)

    ttl_file = sys.argv[1]

    if not Path(ttl_file).exists():
        print(f"[ERROR] TTL file not found: {ttl_file}")
        sys.exit(1)

    # 검증 실행
    result = generate_validation_report(ttl_file)

    # 결과 출력
    print(f"\n[VALIDATION RESULT]")
    print(f"  File: {result['file']}")
    print(f"  Valid: {result['valid']}")

    if result["valid"]:
        print(f"  Total triples: {result['summary']['total_triples']}")
        print(f"  Total invoices: {result['summary']['total_invoices']}")
        print(f"  Data quality score: {result['summary']['data_quality_score']}%")
        print(f"  Overall status: {result['summary']['overall_status']}")

        if result["consistency"]["issues"]:
            print(f"\n[ISSUES]")
            for issue in result["consistency"]["issues"]:
                print(f"  - {issue}")

        print(f"\n[PROPERTY STATISTICS]")
        for prop, count in sorted(result["entities"]["property_stats"].items()):
            print(f"  {prop}: {count}")

    # JSON 보고서 저장
    report_file = (
        Path("reports") / f"invoice_validation_report_{Path(ttl_file).stem}.json"
    )
    Path("reports").mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Validation report saved: {report_file}")


if __name__ == "__main__":
    main()
