#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 Excel 파일 검증 스크립트 v2 (유사도 기반)
"""

import pandas as pd
import glob


def verify_final_excel_v2():
    """유사도 기반 PDF 검증 결과 확인"""

    # 최신 파일 찾기
    files = glob.glob(
        "Results/Sept_2025/domestic_sept_2025_FINAL_WITH_PDF_VALIDATION_*.xlsx"
    )
    if not files:
        print("❌ 파일을 찾을 수 없습니다")
        return

    excel_file = max(files)  # 최신 파일

    print("=" * 80)
    print("최종 Excel 파일 검증 (유사도 기반)")
    print("=" * 80)
    print(f"\n📂 파일: {excel_file.split('/')[-1]}")

    # items 시트 로드
    items_df = pd.read_excel(excel_file, sheet_name="items")

    print(f"\n📊 items 시트: {len(items_df)} rows × {len(items_df.columns)} columns")

    # PDF 검증 컬럼
    pdf_cols = [col for col in items_df.columns if col.startswith("dn_")]
    print(f"\n✅ PDF 검증 컬럼 ({len(pdf_cols)}개):")
    for col in pdf_cols:
        print(f"  - {col}")

    # 유사도 기반 통계
    print(f"\n📈 유사도 기반 검증 통계:")

    if "dn_matched" in items_df.columns:
        matched = (items_df["dn_matched"] == "Yes").sum()
        print(f"  DN 매칭: {matched}/44 ({matched/44*100:.1f}%)")

    if "dn_validation_status" in items_df.columns:
        pass_count = (items_df["dn_validation_status"] == "PASS").sum()
        warn_count = (items_df["dn_validation_status"] == "WARN").sum()
        fail_count = (items_df["dn_validation_status"] == "FAIL").sum()
        na_count = (items_df["dn_validation_status"] == "N/A").sum()

        print(f"\n  검증 상태:")
        print(f"    ✅ PASS: {pass_count}/44 ({pass_count/44*100:.1f}%)")
        print(f"    ⚠️  WARN: {warn_count}/44 ({warn_count/44*100:.1f}%)")
        print(f"    ❌ FAIL: {fail_count}/44 ({fail_count/44*100:.1f}%)")
        print(f"    N/A: {na_count}/44 ({na_count/44*100:.1f}%)")

    # 유사도 평균
    if "dn_origin_similarity" in items_df.columns:
        avg_origin_sim = items_df[items_df["dn_origin_similarity"] > 0][
            "dn_origin_similarity"
        ].mean()
        avg_dest_sim = items_df[items_df["dn_dest_similarity"] > 0][
            "dn_dest_similarity"
        ].mean()
        avg_vehicle_sim = items_df[items_df["dn_vehicle_similarity"] > 0][
            "dn_vehicle_similarity"
        ].mean()

        print(f"\n  평균 유사도:")
        print(f"    Origin: {avg_origin_sim:.3f} (70% 임계값)")
        print(f"    Destination: {avg_dest_sim:.3f} (70% 임계값)")
        print(f"    Vehicle: {avg_vehicle_sim:.3f} (60% 임계값)")

    # 샘플 데이터 (PASS 케이스)
    print(f"\n📋 샘플 데이터 (PASS 케이스 상위 3개):")
    if "dn_validation_status" in items_df.columns:
        pass_samples = items_df[items_df["dn_validation_status"] == "PASS"]
        if len(pass_samples) > 0:
            sample_cols = [
                "origin",
                "destination",
                "dn_origin_extracted",
                "dn_dest_extracted",
                "dn_origin_similarity",
                "dn_dest_similarity",
                "dn_validation_status",
            ]
            available_cols = [col for col in sample_cols if col in items_df.columns]
            print(pass_samples[available_cols].head(3).to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ 검증 완료!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        verify_final_excel_v2()
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback

        traceback.print_exc()
