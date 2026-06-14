#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HVDC Excel 파일 처리 스크립트
HVDC_입고로직_종합리포트_20251019_165153_v3.0-corrected.xlsx 파일을 처리하여 RDF 변환
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding="utf-8")

# LogiOntology 모듈 import
sys.path.append("logiontology")
from logiontology.src.ingest.excel import load_excel, convert_excel_to_rdf
from logiontology.src.mapping.registry import MappingRegistry
from logiontology.src.validation.schema_validator import SchemaValidator


def analyze_excel_structure(file_path: str):
    """Excel 파일 구조 분석"""
    print("=" * 60)
    print("HVDC EXCEL FILE STRUCTURE ANALYSIS")
    print("=" * 60)

    xls = pd.ExcelFile(file_path)
    print(f"File: {file_path}")
    print(f"Total Sheets: {len(xls.sheet_names)}")
    print()

    analysis_results = {}

    for i, sheet_name in enumerate(xls.sheet_names, 1):
        print(f"{i:2d}. Sheet {i}")
        print("-" * 30)

        try:
            df = pd.read_excel(xls, sheet_name)

            # 기본 정보
            rows, cols = len(df), len(df.columns)
            missing = df.isnull().sum().sum()
            missing_pct = (missing / (rows * cols) * 100) if rows > 0 else 0

            print(f"Rows: {rows:,}")
            print(f"Columns: {cols}")
            print(f"Missing values: {missing:,} ({missing_pct:.1f}%)")

            # 데이터 타입
            dtypes = df.dtypes.value_counts()
            print(f"Data types: {dict(dtypes)}")

            # HVDC 관련 컬럼 찾기
            hvdc_cols = [col for col in df.columns if "HVDC" in str(col).upper()]
            if hvdc_cols:
                print(f"HVDC columns: {hvdc_cols[:3]}")

            # 샘플 컬럼명
            sample_cols = list(df.columns[:5])
            print(f"Sample columns: {sample_cols}")

            # 분석 결과 저장
            analysis_results[f"sheet_{i}"] = {
                "name": sheet_name,
                "rows": rows,
                "columns": cols,
                "missing_values": int(missing),
                "missing_percentage": float(missing_pct),
                "hvdc_columns": hvdc_cols,
                "sample_columns": sample_cols,
                "data_types": {str(k): int(v) for k, v in dtypes.items()},
            }

        except Exception as e:
            print(f"Error: {str(e)}")
            analysis_results[f"sheet_{i}"] = {"name": sheet_name, "error": str(e)}

        print()

    return analysis_results


def process_hvdc_data(file_path: str):
    """HVDC 데이터 처리 메인 함수"""
    print("=" * 60)
    print("HVDC DATA PROCESSING")
    print("=" * 60)

    # 1. 파일 구조 분석
    analysis = analyze_excel_structure(file_path)

    # 2. 매핑 규칙 로드
    print("\nLoading mapping rules...")
    try:
        registry = MappingRegistry()
        # 기본 매핑 규칙 사용 (설정 파일이 없는 경우)
        print("Using default mapping rules")
    except Exception as e:
        print(f"Warning: Could not load mapping rules: {e}")
        print("Using basic processing...")

    # 3. 출력 디렉토리 생성
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}")

    # 4. 주요 시트 처리 (HVDC 데이터가 있는 시트들)
    xls = pd.ExcelFile(file_path)
    results = {}

    # HVDC 데이터가 있는 시트들 식별
    hvdc_sheets = []
    for i, sheet_name in enumerate(xls.sheet_names):
        if i >= 8:  # Sheet 9, 10, 11, 12 (0-based index 8, 9, 10, 11)
            try:
                df = pd.read_excel(xls, sheet_name)
                hvdc_cols = [col for col in df.columns if "HVDC" in str(col).upper()]
                if hvdc_cols and len(df) > 0:
                    hvdc_sheets.append((i + 1, sheet_name, df))
            except:
                continue

    print(f"\nFound {len(hvdc_sheets)} sheets with HVDC data")

    # 5. 각 HVDC 시트 처리
    for sheet_num, sheet_name, df in hvdc_sheets:
        print(f"\nProcessing Sheet {sheet_num}: {sheet_name}")
        print("-" * 50)

        try:
            print(f"Original data: {len(df)} rows, {len(df.columns)} columns")

            # HVDC 코드 정규화 및 필터링
            hvdc_cols = [col for col in df.columns if "HVDC" in str(col).upper()]
            print(f"HVDC columns found: {hvdc_cols}")

            # HE, SIM 벤더 필터링
            if "HVDC CODE 3" in df.columns:
                # HE, SIM 코드만 필터링
                valid_vendors = ["HE", "SIM"]
                before_filter = len(df)
                df_filtered = df[df["HVDC CODE 3"].isin(valid_vendors)]
                after_filter = len(df_filtered)
                print(f"Vendor filtering: {before_filter} -> {after_filter} rows")
            else:
                df_filtered = df
                print("No HVDC CODE 3 column found, skipping vendor filter")

            # 데이터 정제
            print("Cleaning data...")

            # 결측치 처리
            missing_before = df_filtered.isnull().sum().sum()
            df_clean = df_filtered.copy()

            # 숫자 컬럼의 결측치를 0으로 채우기
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            df_clean[numeric_cols] = df_clean[numeric_cols].fillna(0)

            # 문자열 컬럼의 결측치를 빈 문자열로 채우기
            string_cols = df_clean.select_dtypes(include=["object"]).columns
            df_clean[string_cols] = df_clean[string_cols].fillna("")

            missing_after = df_clean.isnull().sum().sum()
            print(f"Missing values: {missing_before} -> {missing_after}")

            # 6. RDF 변환 시도
            output_file = output_dir / f"sheet_{sheet_num}_hvdc_data.ttl"
            print(f"Converting to RDF: {output_file}")

            try:
                # 간단한 RDF 변환 (기본 구조)
                rdf_content = generate_basic_rdf(df_clean, sheet_name)
                output_file.write_text(rdf_content, encoding="utf-8")

                results[f"sheet_{sheet_num}"] = {
                    "status": "SUCCESS",
                    "original_rows": len(df),
                    "filtered_rows": len(df_filtered),
                    "cleaned_rows": len(df_clean),
                    "output_file": str(output_file),
                    "hvdc_columns": hvdc_cols,
                }
                print(f"[SUCCESS] Generated: {output_file}")

            except Exception as e:
                print(f"[ERROR] RDF conversion error: {str(e)}")
                results[f"sheet_{sheet_num}"] = {
                    "status": "RDF_ERROR",
                    "error": str(e),
                    "original_rows": len(df),
                    "filtered_rows": len(df_filtered),
                }

        except Exception as e:
            print(f"[ERROR] Processing error: {str(e)}")
            results[f"sheet_{sheet_num}"] = {"status": "ERROR", "error": str(e)}

    # 7. 결과 요약
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)

    success_count = 0
    total_count = len(results)

    for sheet_id, result in results.items():
        status = result.get("status", "UNKNOWN")
        if status == "SUCCESS":
            success_count += 1
            print(
                f"[SUCCESS] {sheet_id}: {status} - {result.get('cleaned_rows', 0)} rows -> {result.get('output_file', 'N/A')}"
            )
        else:
            print(
                f"[ERROR] {sheet_id}: {status} - {result.get('error', 'Unknown error')}"
            )

    print(
        f"\nSuccess rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)"
    )

    # 8. 결과 저장
    summary_file = output_dir / "processing_summary.json"
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "input_file": file_path,
        "analysis": analysis,
        "results": results,
        "summary": {
            "total_sheets": len(xls.sheet_names),
            "hvdc_sheets_processed": len(hvdc_sheets),
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
        },
    }

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to: {summary_file}")

    return results


def generate_basic_rdf(df, sheet_name):
    """기본 RDF 생성 (간단한 버전)"""
    rdf_lines = []

    # RDF 헤더
    rdf_lines.append("@prefix ex: <http://samsung.com/project-logistics#> .")
    rdf_lines.append("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    rdf_lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    rdf_lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    rdf_lines.append("")

    # 데이터셋 정보
    rdf_lines.append(f"ex:Dataset_{sheet_name.replace(' ', '_')} a ex:Dataset ;")
    rdf_lines.append(f'    rdfs:label "{sheet_name}" ;')
    rdf_lines.append(f"    ex:totalRecords {len(df)} ;")
    rdf_lines.append(f'    ex:createdAt "{datetime.now().isoformat()}"^^xsd:dateTime .')
    rdf_lines.append("")

    # 샘플 데이터 (처음 10개 레코드만)
    sample_size = min(10, len(df))
    for i in range(sample_size):
        row = df.iloc[i]

        # HVDC 코드가 있는 경우 TransportEvent 생성
        hvdc_codes = []
        for col in df.columns:
            if (
                "HVDC" in str(col).upper()
                and pd.notna(row[col])
                and str(row[col]).strip()
            ):
                hvdc_codes.append(str(row[col]).strip())

        if hvdc_codes:
            event_id = f"event_{i+1}"
            rdf_lines.append(f"ex:{event_id} a ex:TransportEvent ;")
            rdf_lines.append(f'    ex:eventId "{event_id}" ;')

            for j, code in enumerate(hvdc_codes[:3]):  # 최대 3개 코드만
                rdf_lines.append(f'    ex:hvdcCode{j+1} "{code}" ;')

            # 기타 필드들
            if "Shipment Invoice No." in df.columns and pd.notna(
                row["Shipment Invoice No."]
            ):
                rdf_lines.append(
                    f"    ex:shipmentInvoiceNo \"{row['Shipment Invoice No.']}\" ;"
                )

            if "Date" in df.columns and pd.notna(row["Date"]):
                rdf_lines.append(f"    ex:date \"{row['Date']}\"^^xsd:date ;")

            rdf_lines.append("    .")
            rdf_lines.append("")

    return "\n".join(rdf_lines)


def main():
    """메인 실행 함수"""
    file_path = "HVDC_입고로직_종합리포트_20251019_165153_v3.0-corrected.xlsx"

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return

    print("Starting HVDC Excel processing...")
    print(f"Input file: {file_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    try:
        results = process_hvdc_data(file_path)
        print("\nProcessing completed successfully!")

    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
