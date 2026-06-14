#!/usr/bin/env python3
"""
Invoice Excel 처리 스크립트
SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm 파일을 RDF로 변환
"""

import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import re

# RDF 관련 import
from rdflib import Graph, Namespace, Literal, URIRef, RDF, XSD
from rdflib.namespace import RDF, RDFS, XSD


def load_mapping_rules(config_path: str) -> Dict[str, Any]:
    """매핑 규칙 로드"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_namespaces(rules: Dict[str, Any]) -> Dict[str, Namespace]:
    """네임스페이스 설정"""
    ns_dict = {}
    for prefix, uri in rules["namespaces"].items():
        ns_dict[prefix] = Namespace(uri)
    return ns_dict


def normalize_value(value: Any, field_name: str, rules: Dict[str, Any]) -> Any:
    """값 정규화"""
    if pd.isna(value) or value == "":
        return None

    # 문자열 정리
    if isinstance(value, str):
        value = str(value).strip()

    # 타입 변환
    type_conversion = rules.get("business_rules", {}).get("type_conversion", {})
    target_type = type_conversion.get(field_name)

    if target_type == "decimal":
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    elif target_type == "date":
        try:
            if isinstance(value, str):
                # 숫자만 있는 경우 (예: "0", "150")는 날짜가 아님
                if value.isdigit():
                    return None

                # 다양한 날짜 형식 처리
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return pd.to_datetime(value, format=fmt).strftime("%Y-%m-%d")
                    except:
                        continue
                return None
            elif isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            return None
        except:
            return None

    return value


def apply_business_filters(df: pd.DataFrame, rules: Dict[str, Any]) -> pd.DataFrame:
    """비즈니스 필터 적용"""
    print(f"[INFO] Original rows: {len(df)}")

    # 필수 필드 검증
    required_fields = rules.get("business_rules", {}).get("required_fields", [])
    for field in required_fields:
        if field in df.columns:
            df = df[df[field].notna() & (df[field] != "")]

    # 빈 행 제외
    if rules.get("filters", {}).get("exclude_empty_rows", True):
        df = df.dropna(how="all")

    print(f"[INFO] After filtering: {len(df)} rows")
    return df


def create_invoice_uri(shipment_ref: str, ns_dict: Dict[str, Namespace]) -> URIRef:
    """Invoice URI 생성"""
    # HVDC 코드에서 UUID 생성용 부분 추출
    hvdc_code = shipment_ref.replace("HVDC-ADOPT-", "") if shipment_ref else "UNKNOWN"
    # URI에 사용할 수 없는 문자들을 안전한 문자로 변환
    safe_code = re.sub(r"[^\w\-]", "_", hvdc_code)
    uri_id = f"Invoice/{safe_code}_{datetime.now().strftime('%Y%m%d')}"
    return URIRef(f"{ns_dict['hvdci']}{uri_id}")


def create_shipment_uri(shipment_ref: str, ns_dict: Dict[str, Namespace]) -> URIRef:
    """Shipment URI 생성"""
    hvdc_code = shipment_ref.replace("HVDC-ADOPT-", "") if shipment_ref else "UNKNOWN"
    # URI에 사용할 수 없는 문자들을 안전한 문자로 변환
    safe_code = re.sub(r"[^\w\-]", "_", hvdc_code)
    return URIRef(f"{ns_dict['hvdci']}Shipment/{safe_code}")


def process_invoice_sheet(
    df: pd.DataFrame,
    sheet_name: str,
    rules: Dict[str, Any],
    ns_dict: Dict[str, Namespace],
) -> Graph:
    """Invoice 시트 처리"""
    print(f"[INFO] Processing sheet: {sheet_name}")

    # 컬럼 매핑 적용
    column_mapping = rules.get("column_mapping", {}).get(sheet_name, {})
    if not column_mapping:
        print(f"[WARNING] No column mapping found for sheet: {sheet_name}")
        return Graph()

    # 컬럼명 변경
    df_mapped = df.copy()
    for col_idx, field_name in column_mapping.items():
        if int(col_idx) < len(df.columns):
            df_mapped[field_name] = df.iloc[:, int(col_idx)]

    # 비즈니스 필터 적용
    df_filtered = apply_business_filters(df_mapped, rules)

    if df_filtered.empty:
        print(f"[WARNING] No valid data in sheet: {sheet_name}")
        return Graph()

    # RDF 그래프 생성
    g = Graph()

    # 네임스페이스 바인딩
    for prefix, ns in ns_dict.items():
        g.bind(prefix, ns)

    # 각 행 처리
    for idx, row in df_filtered.iterrows():
        try:
            # Invoice 엔티티 생성
            shipment_ref = row.get("shipment_reference", "")
            if not shipment_ref:
                continue

            invoice_uri = create_invoice_uri(shipment_ref, ns_dict)
            g.add((invoice_uri, RDF.type, ns_dict["hvdc"]["Invoice"]))

            # Invoice 속성 추가
            entity_mapping = rules.get("entity_mapping", {}).get("invoice", {})
            properties = entity_mapping.get("properties", [])

            for prop in properties:
                field_name = prop["field"]
                property_uri = ns_dict["hvdc"][prop["property"].split(":")[1]]
                datatype = prop.get("datatype", "xsd:string")

                value = row.get(field_name)
                if value is not None:
                    normalized_value = normalize_value(value, field_name, rules)
                    if normalized_value is not None:
                        # 날짜 타입의 경우 추가 검증
                        if datatype == "xsd:date":
                            # 날짜 형식이 올바른지 확인 (YYYY-MM-DD)
                            if (
                                isinstance(normalized_value, str)
                                and len(normalized_value) == 10
                                and normalized_value.count("-") == 2
                            ):
                                g.add(
                                    (
                                        invoice_uri,
                                        property_uri,
                                        Literal(normalized_value, datatype=XSD.date),
                                    )
                                )
                        elif datatype == "xsd:decimal":
                            g.add(
                                (
                                    invoice_uri,
                                    property_uri,
                                    Literal(normalized_value, datatype=XSD.decimal),
                                )
                            )
                        else:
                            g.add(
                                (
                                    invoice_uri,
                                    property_uri,
                                    Literal(str(normalized_value)),
                                )
                            )

            # Shipment 연결
            shipment_uri = create_shipment_uri(shipment_ref, ns_dict)
            g.add((invoice_uri, ns_dict["hvdc"]["relatedShipment"], shipment_uri))

        except Exception as e:
            print(f"[ERROR] Error processing row {idx}: {e}")
            continue

    print(f"[INFO] Generated {len(g)} triples for sheet: {sheet_name}")
    return g


def process_invoice_file(
    excel_path: str, config_path: str, output_dir: str = "output"
) -> Dict[str, Any]:
    """Invoice 파일 전체 처리"""
    print(f"[INFO] Starting Invoice processing: {excel_path}")

    # 매핑 규칙 로드
    rules = load_mapping_rules(config_path)
    ns_dict = setup_namespaces(rules)

    # 출력 디렉토리 생성
    Path(output_dir).mkdir(exist_ok=True)

    # Excel 파일 로드
    try:
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = excel_file.sheet_names
        print(f"[INFO] Found {len(sheet_names)} sheets: {sheet_names}")
    except Exception as e:
        print(f"[ERROR] Error loading Excel file: {e}")
        return {"error": str(e)}

    # 결과 저장
    results = {
        "processed_sheets": [],
        "total_triples": 0,
        "output_files": [],
        "errors": [],
    }

    # 각 시트 처리
    for sheet_name in sheet_names:
        try:
            # 시트 읽기
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

            if df.empty:
                print(f"[WARNING] Empty sheet: {sheet_name}")
                continue

            # RDF 변환
            graph = process_invoice_sheet(df, sheet_name, rules, ns_dict)

            if len(graph) > 0:
                # TTL 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = Path(output_dir) / f"invoice_{sheet_name}_{timestamp}.ttl"

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(graph.serialize(format="turtle"))

                results["processed_sheets"].append(sheet_name)
                results["total_triples"] += len(graph)
                results["output_files"].append(str(output_file))

                print(f"[SUCCESS] Saved: {output_file} ({len(graph)} triples)")
            else:
                print(f"[WARNING] No triples generated for sheet: {sheet_name}")

        except Exception as e:
            error_msg = f"Error processing sheet {sheet_name}: {e}"
            print(f"[ERROR] {error_msg}")
            results["errors"].append(error_msg)

    return results


def main():
    """메인 함수"""
    if len(sys.argv) < 3:
        print(
            "Usage: python process_invoice_excel.py <excel_file> <config_file> [output_dir]"
        )
        sys.exit(1)

    excel_path = sys.argv[1]
    config_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "output"

    if not Path(excel_path).exists():
        print(f"[ERROR] Excel file not found: {excel_path}")
        sys.exit(1)

    if not Path(config_path).exists():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    # 처리 실행
    results = process_invoice_file(excel_path, config_path, output_dir)

    # 결과 요약
    print(f"\n[SUMMARY]")
    print(f"  Processed sheets: {len(results['processed_sheets'])}")
    print(f"  Total triples: {results['total_triples']}")
    print(f"  Output files: {len(results['output_files'])}")
    print(f"  Errors: {len(results['errors'])}")

    if results["errors"]:
        print(f"\n[ERRORS]")
        for error in results["errors"]:
            print(f"  - {error}")

    # 보고서 생성
    report_file = (
        Path("reports")
        / f"invoice_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    Path("reports").mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Invoice Processing Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source**: {excel_path}\n")
        f.write(f"**Config**: {config_path}\n\n")

        f.write(f"## Summary\n\n")
        f.write(f"- Processed sheets: {len(results['processed_sheets'])}\n")
        f.write(f"- Total triples: {results['total_triples']}\n")
        f.write(f"- Output files: {len(results['output_files'])}\n")
        f.write(f"- Errors: {len(results['errors'])}\n\n")

        f.write(f"## Processed Sheets\n\n")
        for sheet in results["processed_sheets"]:
            f.write(f"- {sheet}\n")

        f.write(f"\n## Output Files\n\n")
        for file_path in results["output_files"]:
            f.write(f"- {file_path}\n")

        if results["errors"]:
            f.write(f"\n## Errors\n\n")
            for error in results["errors"]:
                f.write(f"- {error}\n")

    print(f"[INFO] Report saved: {report_file}")


if __name__ == "__main__":
    main()
