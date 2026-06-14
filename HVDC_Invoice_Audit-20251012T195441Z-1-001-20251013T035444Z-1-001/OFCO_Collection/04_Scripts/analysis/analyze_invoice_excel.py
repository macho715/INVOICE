#!/usr/bin/env python3
"""
Invoice Excel 파일 구조 분석 스크립트
SCNT SHIPMENT DRAFT INVOICE (SEPT 2025).xlsm 파일을 분석하여 매핑 규칙 설계에 필요한 정보를 수집
"""

import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import openpyxl
from pathlib import Path
import json
from datetime import datetime


def analyze_excel_structure(file_path: str) -> dict:
    """Excel 파일의 구조를 분석"""
    print(f"📊 Analyzing Excel file: {file_path}")

    # Excel 파일 로드
    try:
        # openpyxl로 시트 정보 확인
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet_names = wb.sheetnames
        print(f"📋 Found {len(sheet_names)} sheets: {sheet_names}")

        analysis = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "analysis_date": datetime.now().isoformat(),
            "sheets": {},
            "summary": {
                "total_sheets": len(sheet_names),
                "data_sheets": 0,
                "empty_sheets": 0,
            },
        }

        # 각 시트 분석
        for sheet_name in sheet_names:
            print(f"\n🔍 Analyzing sheet: {sheet_name}")

            try:
                # pandas로 시트 읽기
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

                # 시트 정보
                sheet_info = {
                    "name": sheet_name,
                    "dimensions": f"{df.shape[0]} rows x {df.shape[1]} columns",
                    "total_cells": df.shape[0] * df.shape[1],
                    "non_empty_cells": df.count().sum(),
                    "is_empty": df.empty,
                    "columns": [],
                    "sample_data": [],
                }

                if not df.empty:
                    # 컬럼 정보 수집
                    for i, col in enumerate(df.columns):
                        col_data = df[col].dropna()
                        if not col_data.empty:
                            col_info = {
                                "index": i,
                                "name": str(col),
                                "non_null_count": len(col_data),
                                "data_types": {
                                    str(k): int(v)
                                    for k, v in col_data.apply(type)
                                    .value_counts()
                                    .to_dict()
                                    .items()
                                },
                                "sample_values": col_data.head(5).tolist(),
                                "unique_count": col_data.nunique(),
                            }
                            sheet_info["columns"].append(col_info)

                    # 샘플 데이터 (첫 5행)
                    sheet_info["sample_data"] = df.head(5).to_dict("records")

                    # 헤더 후보 찾기 (첫 번째 비어있지 않은 행)
                    header_candidates = []
                    for idx in range(min(10, len(df))):
                        row = df.iloc[idx]
                        non_null_count = row.count()
                        if non_null_count > 0:
                            header_candidates.append(
                                {
                                    "row_index": idx,
                                    "non_null_count": non_null_count,
                                    "values": row.dropna().tolist()[
                                        :10
                                    ],  # 처음 10개 값만
                                }
                            )

                    sheet_info["header_candidates"] = header_candidates

                    analysis["summary"]["data_sheets"] += 1
                else:
                    analysis["summary"]["empty_sheets"] += 1

                analysis["sheets"][sheet_name] = sheet_info

            except Exception as e:
                print(f"❌ Error analyzing sheet {sheet_name}: {e}")
                analysis["sheets"][sheet_name] = {"name": sheet_name, "error": str(e)}

        return analysis

    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        return {"error": str(e)}


def find_invoice_fields(analysis: dict) -> dict:
    """Invoice 관련 필드 식별"""
    print("\n🔍 Identifying Invoice fields...")

    invoice_keywords = [
        "invoice",
        "inv",
        "bill",
        "amount",
        "total",
        "cost",
        "price",
        "charge",
        "date",
        "number",
        "no",
        "currency",
        "usd",
        "aed",
        "dollar",
        "shipment",
        "ship",
        "bl",
        "bill of lading",
        "container",
        "case",
        "vendor",
        "supplier",
        "company",
        "client",
        "customer",
    ]

    field_mapping = {
        "invoice_number": [],
        "invoice_date": [],
        "amount": [],
        "currency": [],
        "shipment_reference": [],
        "vendor": [],
    }

    for sheet_name, sheet_info in analysis.get("sheets", {}).items():
        if "columns" not in sheet_info:
            continue

        print(f"\n📋 Sheet: {sheet_name}")

        for col in sheet_info["columns"]:
            col_name = col["name"].lower()
            sample_values = [str(v).lower() for v in col["sample_values"]]

            # 키워드 매칭
            for keyword in invoice_keywords:
                if keyword in col_name or any(
                    keyword in str(val) for val in sample_values
                ):
                    if "invoice" in keyword or "inv" in keyword or "bill" in keyword:
                        if "number" in col_name or "no" in col_name:
                            field_mapping["invoice_number"].append(
                                {
                                    "sheet": sheet_name,
                                    "column": col["name"],
                                    "index": col["index"],
                                    "confidence": (
                                        "high" if "invoice" in col_name else "medium"
                                    ),
                                }
                            )
                        elif "date" in col_name:
                            field_mapping["invoice_date"].append(
                                {
                                    "sheet": sheet_name,
                                    "column": col["name"],
                                    "index": col["index"],
                                    "confidence": (
                                        "high" if "invoice" in col_name else "medium"
                                    ),
                                }
                            )
                    elif keyword in ["amount", "total", "cost", "price", "charge"]:
                        field_mapping["amount"].append(
                            {
                                "sheet": sheet_name,
                                "column": col["name"],
                                "index": col["index"],
                                "confidence": (
                                    "high" if keyword in col_name else "medium"
                                ),
                            }
                        )
                    elif keyword in ["currency", "usd", "aed", "dollar"]:
                        field_mapping["currency"].append(
                            {
                                "sheet": sheet_name,
                                "column": col["name"],
                                "index": col["index"],
                                "confidence": (
                                    "high" if keyword in col_name else "medium"
                                ),
                            }
                        )
                    elif keyword in ["shipment", "ship", "bl", "container", "case"]:
                        field_mapping["shipment_reference"].append(
                            {
                                "sheet": sheet_name,
                                "column": col["name"],
                                "index": col["index"],
                                "confidence": (
                                    "high" if keyword in col_name else "medium"
                                ),
                            }
                        )
                    elif keyword in [
                        "vendor",
                        "supplier",
                        "company",
                        "client",
                        "customer",
                    ]:
                        field_mapping["vendor"].append(
                            {
                                "sheet": sheet_name,
                                "column": col["name"],
                                "index": col["index"],
                                "confidence": (
                                    "high" if keyword in col_name else "medium"
                                ),
                            }
                        )

    return field_mapping


def main():
    """메인 함수"""
    if len(sys.argv) != 2:
        print("Usage: python analyze_invoice_excel.py <excel_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    # Excel 구조 분석
    analysis = analyze_excel_structure(file_path)

    if "error" in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        sys.exit(1)

    # Invoice 필드 식별
    field_mapping = find_invoice_fields(analysis)

    # 결과 저장
    output_file = "reports/invoice_analysis_report.json"
    Path("reports").mkdir(exist_ok=True)

    result = {
        "analysis": analysis,
        "field_mapping": field_mapping,
        "recommendations": {
            "primary_sheet": None,
            "mapping_strategy": "manual_review_required",
        },
    }

    # 주요 데이터 시트 찾기
    data_sheets = []
    for sheet_name, sheet_info in analysis["sheets"].items():
        if (
            not sheet_info.get("is_empty", True)
            and sheet_info.get("non_empty_cells", 0) > 10
        ):
            data_sheets.append(
                {
                    "name": sheet_name,
                    "non_empty_cells": sheet_info.get("non_empty_cells", 0),
                    "columns": len(sheet_info.get("columns", [])),
                }
            )

    if data_sheets:
        # 가장 많은 데이터가 있는 시트를 주요 시트로 선택
        primary_sheet = max(data_sheets, key=lambda x: x["non_empty_cells"])
        result["recommendations"]["primary_sheet"] = primary_sheet["name"]
        result["recommendations"]["mapping_strategy"] = "automated_with_review"

    # JSON 파일로 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n✅ Analysis complete! Report saved to: {output_file}")

    # 요약 출력
    print(f"\n📊 SUMMARY:")
    print(f"   Total sheets: {analysis['summary']['total_sheets']}")
    print(f"   Data sheets: {analysis['summary']['data_sheets']}")
    print(f"   Empty sheets: {analysis['summary']['empty_sheets']}")

    if result["recommendations"]["primary_sheet"]:
        print(f"   Primary sheet: {result['recommendations']['primary_sheet']}")

    print(f"\n🔍 IDENTIFIED FIELDS:")
    for field_type, fields in field_mapping.items():
        if fields:
            print(f"   {field_type}: {len(fields)} candidates")
            for field in fields[:3]:  # 처음 3개만 표시
                print(
                    f"     - {field['sheet']}.{field['column']} ({field['confidence']})"
                )


if __name__ == "__main__":
    main()
