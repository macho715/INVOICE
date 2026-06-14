#!/usr/bin/env python3
"""
Invoice 데이터 시각화 및 요약 스크립트
RDF 파일과 Excel 원본을 비교 분석하여 Mermaid 다이어그램과 보고서를 생성합니다.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict

# Unicode 출력 지원
sys.stdout.reconfigure(encoding="utf-8")

# RDF 처리
from rdflib import Graph, Namespace, RDF, RDFS, XSD, Literal
from rdflib.namespace import NamespaceManager

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_rdf_data(rdf_path: str) -> Tuple[Graph, Dict[str, Any]]:
    """RDF 파일 로드 및 분석"""
    print(f"[INFO] RDF 파일 로드 중: {rdf_path}")

    g = Graph()
    g.parse(rdf_path, format="turtle")

    # 네임스페이스 추출
    namespaces = dict(g.namespaces())
    hvdc_ns = Namespace(namespaces.get("hvdc", "https://hvdc.example.org/ns#"))
    hvdci_ns = Namespace(namespaces.get("hvdci", "https://hvdc.example.org/id/"))

    # Invoice 엔티티 추출
    invoice_type = hvdc_ns["Invoice"]
    invoices = list(g.subjects(predicate=RDF.type, object=invoice_type))

    print(f"[INFO] 발견된 Invoice 수: {len(invoices)}")

    # Invoice 데이터 분석
    invoice_data = []
    for invoice in invoices:
        invoice_info = {"uri": str(invoice), "properties": {}}

        # 모든 속성 추출
        for pred, obj in g.predicate_objects(invoice):
            if isinstance(obj, Literal):
                invoice_info["properties"][str(pred)] = str(obj)
            else:
                invoice_info["properties"][str(pred)] = str(obj)

        invoice_data.append(invoice_info)

    return g, {
        "invoices": invoice_data,
        "total_count": len(invoices),
        "namespaces": namespaces,
        "hvdc_ns": hvdc_ns,
        "hvdci_ns": hvdci_ns,
    }


def load_excel_data(excel_path: str) -> Dict[str, Any]:
    """Excel 파일 로드 및 분석"""
    print(f"[INFO] Excel 파일 로드 중: {excel_path}")

    try:
        df = pd.read_excel(excel_path, sheet_name="SEPT")
        print(f"[INFO] Excel 행 수: {len(df)}")
        print(f"[INFO] Excel 열 수: {len(df.columns)}")

        # 기본 통계
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
        }

        return {"dataframe": df, "stats": stats}
    except Exception as e:
        print(f"[ERROR] Excel 파일 로드 실패: {e}")
        return None


def analyze_invoice_properties(rdf_data: Dict[str, Any]) -> Dict[str, Any]:
    """Invoice 속성 분석"""
    print("[INFO] Invoice 속성 분석 중...")

    invoices = rdf_data["invoices"]

    # 속성별 통계
    property_stats = defaultdict(list)
    currency_dist = Counter()
    vendor_dist = Counter()
    amount_values = []

    for invoice in invoices:
        props = invoice["properties"]

        # 속성 수집
        for prop, value in props.items():
            property_stats[prop].append(value)

        # 통화 분포 (currency 필드가 유효한 통화 코드인지 확인)
        currency_key = None
        for key in props.keys():
            if "currency" in key:
                currency_key = key
                break

        if currency_key:
            currency_val = props[currency_key]
            # 유효한 통화 코드인지 확인 (3글자 알파벳 코드만 허용)
            if (
                currency_val
                and isinstance(currency_val, str)
                and len(currency_val) == 3
                and currency_val.isalpha()
            ):
                currency_dist[currency_val] += 1

        # Vendor 분포 (hasVendor 필드가 날짜가 아닌 경우만)
        vendor_key = None
        for key in props.keys():
            if "hasVendor" in key:
                vendor_key = key
                break

        if vendor_key:
            vendor_val = props[vendor_key]
            # 날짜 형식이 아닌 경우만 Vendor로 인식 (숫자나 특수문자가 적은 경우)
            if (
                vendor_val
                and isinstance(vendor_val, str)
                and not any(c.isdigit() for c in str(vendor_val)[:4])
                and ":" not in str(vendor_val)
                and "-" not in str(vendor_val)
            ):
                vendor_dist[vendor_val] += 1

        # 금액 값
        total_amount_key = None
        for key in props.keys():
            if "totalAmount" in key:
                total_amount_key = key
                break

        if total_amount_key:
            try:
                amount_values.append(float(props[total_amount_key]))
            except (ValueError, TypeError):
                pass

    return {
        "property_stats": dict(property_stats),
        "currency_distribution": dict(currency_dist),
        "vendor_distribution": dict(vendor_dist),
        "amount_values": amount_values,
        "total_amount": sum(amount_values) if amount_values else 0,
        "avg_amount": sum(amount_values) / len(amount_values) if amount_values else 0,
    }


def generate_entity_relationship_diagram(rdf_data: Dict[str, Any]) -> str:
    """Entity Relationship 다이어그램 생성"""
    print("[INFO] Entity Relationship 다이어그램 생성 중...")

    mermaid = """erDiagram
    Invoice {
        string uri
        string shipmentReference
        string invoiceNumber
        string vendor
        string currency
        decimal totalAmount
        date invoiceDate
    }

    Shipment {
        string uri
        string hvdcCode
        string caseNo
        string blNumber
        string containerNumber
    }

    Organization {
        string uri
        string name
        string type
    }

    Invoice ||--o{ Shipment : "relatedTo"
    Invoice }|--|| Organization : "issuedBy"
    Shipment }|--|| Organization : "handledBy"
"""

    return mermaid


def generate_currency_pie_chart(analysis: Dict[str, Any]) -> str:
    """통화 분포 파이 차트 생성"""
    print("[INFO] 통화 분포 파이 차트 생성 중...")

    currency_dist = analysis["currency_distribution"]
    if not currency_dist:
        return 'pie title 통화 분포\n    "데이터 없음" : 100'

    # 상위 5개 통화만 표시
    top_currencies = dict(Counter(currency_dist).most_common(5))
    others = sum(currency_dist.values()) - sum(top_currencies.values())

    mermaid = "pie title 통화 분포\n"
    for currency, count in top_currencies.items():
        mermaid += f'    "{currency}" : {count}\n'

    if others > 0:
        mermaid += f'    "기타" : {others}\n'

    return mermaid


def generate_vendor_bar_chart(analysis: Dict[str, Any]) -> str:
    """Vendor 분포 바 차트 생성"""
    print("[INFO] Vendor 분포 바 차트 생성 중...")

    vendor_dist = analysis["vendor_distribution"]
    if not vendor_dist:
        return 'xychart-beta\n    title Vendor 분포\n    x-axis ["데이터 없음"]\n    y-axis "Invoice 수" 0 --> 10\n    bar [10]'

    # 상위 10개 Vendor만 표시
    top_vendors = dict(Counter(vendor_dist).most_common(10))

    vendors = list(top_vendors.keys())
    counts = list(top_vendors.values())

    mermaid = f"""xychart-beta
    title Vendor 분포
    x-axis {vendors}
    y-axis "Invoice 수" 0 --> {max(counts) + 1}
    bar {counts}"""

    return mermaid


def generate_data_flow_diagram() -> str:
    """데이터 처리 파이프라인 플로우 차트 생성"""
    print("[INFO] 데이터 처리 파이프라인 플로우 차트 생성 중...")

    mermaid = """flowchart TD
    A[Excel 파일<br/>SCNT SHIPMENT DRAFT INVOICE] --> B[데이터 분석<br/>구조 파악]
    B --> C[매핑 규칙 적용<br/>YAML 설정]
    C --> D[데이터 정규화<br/>타입 변환]
    D --> E[RDF 변환<br/>온톨로지 매핑]
    E --> F[TTL 파일 생성<br/>invoice_SEPT_*.ttl]
    F --> G[데이터 검증<br/>RDF 문법 확인]
    G --> H[시각화 보고서<br/>Mermaid 다이어그램]

    style A fill:#e1f5fe
    style F fill:#c8e6c9
    style H fill:#fff3e0
"""

    return mermaid


def generate_ontology_class_diagram(rdf_data: Dict[str, Any]) -> str:
    """RDF 온톨로지 클래스 다이어그램 생성"""
    print("[INFO] RDF 온톨로지 클래스 다이어그램 생성 중...")

    mermaid = """classDiagram
    class Invoice {
        +String hasShipmentReference
        +String hasJobNumber
        +String hasBLNumber
        +String hasContainerNumber
        +String hasVendor
        +Date invoiceDate
        +Date dueDate
        +String paymentTerms
        +String currency
        +Decimal exchangeRate
        +Decimal totalAmount
        +Decimal unitPrice
        +String unit
        +String description
        +String title
        +Decimal amount
        +String currencyCode
        +String invoiceNumber
        +String invoiceType
        +String status
        +String notes
        +String metadata
        +Shipment relatedShipment
    }

    class Shipment {
        +String hvdcCode
        +String caseNo
        +String blNumber
        +String containerNumber
        +Organization vendor
    }

    class Organization {
        +String name
        +String type
    }

    Invoice ||--o{ Shipment : relatedTo
    Invoice }|--|| Organization : issuedBy
    Shipment }|--|| Organization : handledBy
"""

    return mermaid


def compare_rdf_excel(
    rdf_data: Dict[str, Any], excel_data: Dict[str, Any]
) -> Dict[str, Any]:
    """RDF와 Excel 데이터 비교 분석"""
    print("[INFO] RDF와 Excel 데이터 비교 분석 중...")

    if not excel_data:
        return {
            "comparison_available": False,
            "error": "Excel 데이터를 로드할 수 없습니다.",
        }

    rdf_count = rdf_data["total_count"]
    excel_count = excel_data["stats"]["total_rows"]

    # 기본 비교
    comparison = {
        "comparison_available": True,
        "rdf_invoice_count": rdf_count,
        "excel_row_count": excel_count,
        "conversion_rate": (rdf_count / excel_count * 100) if excel_count > 0 else 0,
        "data_quality": {
            "rdf_completeness": 0,
            "excel_completeness": 0,
            "field_mapping_accuracy": 0,
        },
    }

    # 데이터 품질 분석
    if rdf_data["invoices"]:
        # RDF 완성도 (필수 필드 기준)
        required_fields = [
            "hvdc:hasShipmentReference",
            "hvdc:totalAmount",
            "hvdc:currency",
        ]
        complete_invoices = 0

        for invoice in rdf_data["invoices"]:
            props = invoice["properties"]
            if all(field in props and props[field] for field in required_fields):
                complete_invoices += 1

        comparison["data_quality"]["rdf_completeness"] = (
            (complete_invoices / rdf_count * 100) if rdf_count > 0 else 0
        )

    # Excel 완성도
    if excel_data["dataframe"] is not None:
        df = excel_data["dataframe"]
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        comparison["data_quality"]["excel_completeness"] = (
            ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0
        )

    return comparison


def generate_markdown_report(
    rdf_data: Dict[str, Any],
    excel_data: Dict[str, Any],
    analysis: Dict[str, Any],
    comparison: Dict[str, Any],
) -> str:
    """Markdown 보고서 생성"""
    print("[INFO] Markdown 보고서 생성 중...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# Invoice 데이터 시각화 및 요약

**생성 시간**: {timestamp}

## Executive Summary

- **총 Invoice 수**: {rdf_data['total_count']}개
- **총 금액**: {analysis['total_amount']:,.2f}
- **평균 금액**: {analysis['avg_amount']:,.2f}
- **처리 완료율**: {comparison.get('conversion_rate', 0):.1f}%

## Mermaid 다이어그램

### 1. Entity Relationship

```mermaid
{generate_entity_relationship_diagram(rdf_data)}
```

### 2. 통화 분포

```mermaid
{generate_currency_pie_chart(analysis)}
```

### 3. Vendor 분포

```mermaid
{generate_vendor_bar_chart(analysis)}
```

### 4. 데이터 처리 파이프라인

```mermaid
{generate_data_flow_diagram()}
```

### 5. RDF 온톨로지 구조

```mermaid
{generate_ontology_class_diagram(rdf_data)}
```

## 데이터 비교 분석

### RDF vs Excel

- **RDF Invoice 수**: {comparison.get('rdf_invoice_count', 0)}개
- **Excel 행 수**: {comparison.get('excel_row_count', 0)}개
- **변환율**: {comparison.get('conversion_rate', 0):.1f}%

### 데이터 품질 지표

- **RDF 완성도**: {comparison.get('data_quality', {}).get('rdf_completeness', 0):.1f}%
- **Excel 완성도**: {comparison.get('data_quality', {}).get('excel_completeness', 0):.1f}%

## 상세 통계

### 통화 분포
"""

    # 통화 분포 상세
    for currency, count in analysis["currency_distribution"].items():
        percentage = (
            (count / rdf_data["total_count"] * 100)
            if rdf_data["total_count"] > 0
            else 0
        )
        report += f"- **{currency}**: {count}개 ({percentage:.1f}%)\n"

    report += "\n### Vendor 분포\n"

    # Vendor 분포 상세
    for vendor, count in analysis["vendor_distribution"].items():
        percentage = (
            (count / rdf_data["total_count"] * 100)
            if rdf_data["total_count"] > 0
            else 0
        )
        report += f"- **{vendor}**: {count}개 ({percentage:.1f}%)\n"

    report += f"""
## 권장 사항

1. **데이터 품질 개선**: RDF 완성도 {comparison.get('data_quality', {}).get('rdf_completeness', 0):.1f}%를 95% 이상으로 향상
2. **매핑 규칙 최적화**: 변환율 {comparison.get('conversion_rate', 0):.1f}% 개선
3. **검증 강화**: 필수 필드 누락 방지를 위한 사전 검증 로직 추가
4. **모니터링**: 정기적인 데이터 품질 검사 및 보고서 자동 생성

---
*이 보고서는 LogiOntology v3.1 시스템에 의해 자동 생성되었습니다.*
"""

    return report


def save_json_summary(
    rdf_data: Dict[str, Any], analysis: Dict[str, Any], comparison: Dict[str, Any]
) -> str:
    """JSON 통계 데이터 저장"""
    print("[INFO] JSON 통계 데이터 저장 중...")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "rdf_data": {
            "total_invoices": rdf_data["total_count"],
            "namespaces": rdf_data["namespaces"],
        },
        "analysis": {
            "currency_distribution": analysis["currency_distribution"],
            "vendor_distribution": analysis["vendor_distribution"],
            "total_amount": analysis["total_amount"],
            "avg_amount": analysis["avg_amount"],
        },
        "comparison": comparison,
    }

    output_path = project_root / "reports" / "invoice_data_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return str(output_path)


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Invoice 데이터 시각화 및 요약 스크립트")
    print("=" * 60)

    # 파일 경로 설정
    rdf_path = project_root / "output" / "invoice_SEPT_20251020_002513.ttl"
    excel_path = project_root / "data" / "invoice_sept2025.xlsm"

    # RDF 데이터 로드
    print("\n1. RDF 데이터 로드")
    rdf_data = load_rdf_data(str(rdf_path))

    # Excel 데이터 로드
    print("\n2. Excel 데이터 로드")
    excel_data = load_excel_data(str(excel_path))

    # Invoice 속성 분석
    print("\n3. Invoice 속성 분석")
    analysis = analyze_invoice_properties(rdf_data[1])

    # RDF vs Excel 비교
    print("\n4. RDF vs Excel 비교 분석")
    comparison = compare_rdf_excel(rdf_data[1], excel_data)

    # Mermaid 다이어그램 생성
    print("\n5. Mermaid 다이어그램 생성")
    # (다이어그램은 보고서에 포함됨)

    # Markdown 보고서 생성
    print("\n6. Markdown 보고서 생성")
    report = generate_markdown_report(rdf_data[1], excel_data, analysis, comparison)

    # 보고서 저장
    report_path = project_root / "reports" / "INVOICE_VISUALIZATION_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[SUCCESS] 보고서 저장: {report_path}")

    # JSON 통계 저장
    print("\n7. JSON 통계 데이터 저장")
    json_path = save_json_summary(rdf_data[1], analysis, comparison)
    print(f"[SUCCESS] JSON 통계 저장: {json_path}")

    # 요약 출력
    print("\n" + "=" * 60)
    print("처리 완료 요약")
    print("=" * 60)
    print(f"RDF Invoice 수: {rdf_data[1]['total_count']}개")
    print(f"총 금액: {analysis['total_amount']:,.2f}")
    print(f"통화 종류: {len(analysis['currency_distribution'])}개")
    print(f"Vendor 수: {len(analysis['vendor_distribution'])}개")
    print(f"변환율: {comparison.get('conversion_rate', 0):.1f}%")
    print(
        f"RDF 완성도: {comparison.get('data_quality', {}).get('rdf_completeness', 0):.1f}%"
    )
    print("\n생성된 파일:")
    print(f"- 보고서: {report_path}")
    print(f"- 통계: {json_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
