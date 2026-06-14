#!/usr/bin/env python3
"""
OFCO PDF → Complete Pipeline 통합 실행 스크립트

PDF 파일을 파싱하고 Complete Pipeline을 실행하는 전체 워크플로우

Usage:
    python ofco_pdf_to_complete_pipeline.py <pdf_file>

Example:
    python ofco_pdf_to_complete_pipeline.py ofco_pipeline/data/OFCO-INV-0001178_Samsung\ \(1\).pdf
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Optional

# PDF 파서 import (pipeline_docs 구조)
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline_steps" / "step_01_pdf_parsing" / "scripts"))
from ofco_parse_pdf_patched import parse_ofco_invoice, OFCOPayload, LineItem

# Complete Pipeline import (같은 폴더)
from ofco_complete_pipeline_v2 import (
    Phase1Transformer,
    Phase2Allocator,
    EASlotPacker,
    StandardLine,
)

import os


def payload_to_dataframe(payload: OFCOPayload) -> pd.DataFrame:
    """
    OFCOPayload를 DataFrame으로 변환 (Complete Pipeline 입력 형식)

    Args:
        payload: PDF 파서 출력

    Returns:
        DataFrame: Complete Pipeline 입력 형식
    """
    rows = []

    for idx, item in enumerate(payload.items, 1):
        row = {
            # 기본 정보
            "invoice_no": payload.meta.invoice_number or "",
            "invoice_date": payload.meta.invoice_date or "",
            "voyage_no": payload.meta.voyage_no or "",
            "supplier": payload.meta.supplier_name or "",
            "currency": payload.meta.currency or "AED",

            # 라인 정보
            "line_no": idx,
            "sn": "",  # LineItem에는 sn이 없음, notes에서 추출 가능하지만 일단 빈 값
            "tariff_code": "",  # LineItem에는 tariff_code가 없음
            "description": item.subject or "",
            "section": "",  # LineItem에는 section이 없음
            "notes": item.notes or "",

            # 금액 정보
            "amount_excl_vat": item.amount or 0.0,
            "tax_rate": payload.meta.vat_percent or 0.0,
            "tax_amount": 0.0,  # LineItem에는 tax_amount가 없음, 계산 필요
            "amount_incl_vat": item.amount or 0.0,  # LineItem에는 amount_incl_vat가 없음
        }

        # EA/Rate 페어 처리 (최대 4개)
        for i, (qty, rate) in enumerate(item.ea_rates[:4], 1):
            row[f"EA_{i}_Qty"] = qty
            row[f"EA_{i}_Rate"] = rate
            row[f"EA_{i}_Amount"] = qty * rate if qty and rate else 0.0

        # Price Center별 QTY/AMOUNT 컬럼 (예시 - 실제 컬럼명은 Excel 파일 구조에 따라 다름)
        # 여기서는 기본적인 패턴만 제공
        if item.price_center:
            # Price Center 이름에 따라 동적으로 컬럼 생성
            pc_name = item.price_center.replace(" ", "_").upper()
            if item.ea_rates:
                qty, rate = item.ea_rates[0]
                row[f"{pc_name}_QTY"] = qty
                row[f"{pc_name}_AMOUNT"] = qty * rate if qty and rate else 0.0

        rows.append(row)

    df = pd.DataFrame(rows)

    # 누락된 컬럼 추가 (기본값으로)
    required_cols = [
        "AGENCY_FEE_FOR_CARGO_CLEARANCE_QTY",
        "AGENCY_FEE_FOR_CARGO_CLEARANCE_AMOUNT",
        "PORT_DUE_QTY",
        "PORT_DUE_AMOUNT",
        "CHANNEL_DUE_QTY",
        "CHANNEL_DUE_AMOUNT",
        "PILOTAGE_QTY",
        "PILOTAGE_AMOUNT",
        "WASTE_HANDLING_QTY",
        "WASTE_HANDLING_AMOUNT",
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0

    # Step 6: 원본 DataFrame 헤더 정렬 (HeaderCore 사용)
    from ofco_header_core import get_header_core
    header_core = get_header_core()
    
    # OFCO INVOICE.xlsx 기준 헤더 순서에 맞게 정렬
    # 없는 컬럼은 None으로 채워서 추가하여 기준 순서 유지
    df = header_core.reorder_dataframe(df, phase=None, fill_missing=True)
    
    return df


def main(pdf_path: str, output_path: Optional[str] = None):
    """
    PDF 파일부터 Complete Pipeline까지 전체 실행

    Args:
        pdf_path: PDF 파일 경로
        output_path: 출력 Excel 파일 경로 (None이면 자동 생성)
    """
    print("=" * 80)
    print("[PIPELINE] OFCO PDF → Complete Pipeline v3.0")
    print("=" * 80)

    # Step 1: PDF 파싱
    print("\n[Step 1/7] PDF 파싱...")
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"[ERROR] PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return None, None, None

    try:
        payload = parse_ofco_invoice(str(pdf_file))
        print(f"[OK] PDF 파싱 완료: {len(payload.items)}개 항목 추출")
        print(f"  - Invoice: {payload.meta.invoice_number}")
        print(f"  - Date: {payload.meta.invoice_date}")
        print(f"  - Supplier: {payload.meta.supplier_name}")
    except Exception as e:
        print(f"[ERROR] PDF 파싱 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # Step 2: DataFrame 변환
    print("\n[Step 2/7] DataFrame 변환...")
    try:
        df = payload_to_dataframe(payload)
        print(f"[OK] DataFrame 생성: {len(df)} 행, {len(df.columns)} 컬럼")
    except Exception as e:
        print(f"[ERROR] DataFrame 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # Step 3: Phase 1 - Standard Lines
    print("\n[Step 3/7] Phase 1: Standard Lines 변환...")
    try:
        phase1 = Phase1Transformer(df)
        standard_lines = phase1.transform_all()
        print(f"[OK] Phase 1 완료: {len(standard_lines)} 표준 Lines 생성")

        # calc_check 통계
        calc_pass = sum(1 for line in standard_lines if hasattr(line, 'calc_check') and line.calc_check)
        if len(standard_lines) > 0:
            print(f"  calc_check 통과: {calc_pass}/{len(standard_lines)} ({calc_pass/len(standard_lines)*100:.2f}%)")
    except Exception as e:
        print(f"[ERROR] Phase 1 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # Step 4: Phase 2 - Cost Center + Price Center
    print("\n[Step 4/7] Phase 2: Cost Center + Price Center 매핑...")
    try:
        # JSON 규칙 경로 자동 탐색 (pipeline_docs 구조 우선)
        json_rules_path = Path(__file__).parent.parent / "pipeline_steps" / "step_04_phase2_mapping" / "config" / "subject_cost_center_mapping.json"
        if not json_rules_path.exists():
            json_rules_path = Path(__file__).parent / "ofco_pipeline" / "config" / "subject_cost_center_mapping.json"
        if not json_rules_path.exists():
            json_rules_path = Path(__file__).parent / "MAPPING" / "subject_cost_center_mapping.json"
        if not json_rules_path.exists():
            json_rules_path = Path("ofco_pipeline/config/subject_cost_center_mapping.json")

        phase2 = Phase2Allocator(
            standard_lines,
            str(json_rules_path) if json_rules_path.exists() else None
        )
        processed_lines = phase2.process_all()
        print(f"[OK] Phase 2 완료: {len(processed_lines)} 라인 처리")

        # Cost Center 매핑 통계
        # StandardLine의 필드명 확인 필요 - 일단 통계 출력 생략
        # mapped = sum(1 for line in processed_lines if hasattr(line, 'cost_center_b') and line.cost_center_b and line.cost_center_b != "[EXT] Others")
        # if len(processed_lines) > 0:
        #     print(f"  Cost Center 매핑: {mapped}/{len(processed_lines)} ({mapped/len(processed_lines)*100:.2f}%)")
    except Exception as e:
        print(f"[ERROR] Phase 2 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # Step 5: Lines DataFrame 생성
    print("\n[Step 5/7] Lines DataFrame 생성...")
    try:
        lines_df = pd.DataFrame([line.to_dict() for line in processed_lines])
        print(f"[OK] Lines DataFrame: {len(lines_df)} 행")
    except Exception as e:
        print(f"[ERROR] Lines DataFrame 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # Step 6: Phase 3 - EA Slots
    print("\n[Step 6/7] Phase 3: EA Slots 패킹...")

    # 환경 변수 확인: USE_NEW_EA (기본값: True)
    USE_NEW_EA = os.getenv("USE_NEW_EA", "True").lower() == "true"

    if USE_NEW_EA:
        print("  [NEW] 우선순위 기반 EA 할당 사용 (ofco_ea_allocator_v1p3)")

        try:
            # EA Integration Scaffold import (pipeline_docs 구조)
            sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline_steps" / "step_06_phase3_ea_slots" / "scripts"))
            from ofco_pipeline_integration_scaffold import (
                allocate_ea,
                check_pc_sums,
                validate_invoice_totals,
            )

            # 원본 DataFrame과 Lines DataFrame 병합
            merged_df = df.reset_index(drop=True).join(
                lines_df.reset_index(drop=True), rsuffix="_lines"
            )

            # Price Center A/B/C 합계 검증
            merged_df = check_pc_sums(
                merged_df,
                col_a="price_center_a",
                col_b="price_center_b",
                col_c="price_center_c",
                ref_col="amount_excl_tax",
            )

            # EA 슬롯 할당
            ea_df_new = allocate_ea(merged_df)
            ea_df = ea_df_new
            print(f"  [OK] EA 할당 완료: {len(ea_df)} 행")

        except Exception as e:
            print(f"  [ERROR] 새로운 EA 할당 로직 실패: {e}")
            import traceback
            print(f"  [ERROR] 상세: {traceback.format_exc()}")
            print("  [FALLBACK] 기존 로직으로 전환...")
            USE_NEW_EA = False

    if not USE_NEW_EA:
        # 기존 로직 (롤백용)
        packer = EASlotPacker(df, processed_lines)
        ea_df = packer.pack_all()
        print(f"  [OK] EA 패킹 완료: {len(ea_df)} 행")

    # Step 7: 최종 결과 저장
    print("\n[Step 7/7] 최종 결과 저장...")

    # 최종 DataFrame 결합 전 헤더 정렬
    print("  [HeaderCore] 최종 결합 전 헤더 정렬 중...")
    from ofco_header_core import get_header_core
    header_core = get_header_core()
    
    # 각 DataFrame을 HeaderCore로 정렬
    df_reordered = header_core.reorder_dataframe(df, phase=None, fill_missing=False)
    lines_df_reordered = header_core.reorder_dataframe(lines_df, phase=1, fill_missing=False)
    ea_df_reordered = header_core.reorder_dataframe(ea_df, phase=3, fill_missing=False)
    
    # 최종 DataFrame 결합
    final_df = df_reordered.reset_index(drop=True).join(
        lines_df_reordered.reset_index(drop=True), rsuffix="_lines"
    ).join(
        ea_df_reordered.reset_index(drop=True), rsuffix="_ea"
    )
    
    # 최종 결합 후 전체 정렬 (OFCO INVOICE.xlsx 순서)
    final_df = header_core.reorder_dataframe(final_df, phase=None, fill_missing=True)

    # 출력 파일 경로 결정
    if output_path is None:
        invoice_no = payload.meta.invoice_number or "UNKNOWN"
        output_dir = Path(__file__).parent
        output_path = output_dir / f"ofco_pipeline_pdf_{invoice_no.replace('-', '_')}_v3.xlsx"

    output_file = Path(output_path)

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            final_df.to_excel(writer, sheet_name="Complete_Pipeline", index=False)
            lines_df.to_excel(writer, sheet_name="Standard_Lines", index=False)
            ea_df.to_excel(writer, sheet_name="EA_Slots", index=False)

        print(f"[OK] 저장 완료: {output_file}")
    except Exception as e:
        print(f"[ERROR] 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

    # 최종 통계 출력
    print("\n" + "=" * 80)
    print("[STATS] 최종 통계")
    print("=" * 80)
    print(f"총 처리 행: {len(final_df)}")
    print(f"Standard Lines: {len(lines_df)}")
    print(f"EA Slots: {len(ea_df)}")

    if USE_NEW_EA and "calc_status" in ea_df.columns:
        status_counts = ea_df["calc_status"].value_counts()
        print(f"\ncalc_status 분포:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")

    if USE_NEW_EA and "calc_check" in ea_df.columns:
        calc_pass = ea_df["calc_check"].sum() if ea_df["calc_check"].dtype == bool else (ea_df["calc_check"] == True).sum()
        print(f"\nEA calc_check: {calc_pass}/{len(ea_df)} ({calc_pass/len(ea_df)*100:.2f}%)")

    print("\n[OK] 파이프라인 완료!")
    print("=" * 80)

    return final_df, lines_df, ea_df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ofco_pdf_to_complete_pipeline.py <pdf_file> [output_file]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    main(pdf_path, output_path)

