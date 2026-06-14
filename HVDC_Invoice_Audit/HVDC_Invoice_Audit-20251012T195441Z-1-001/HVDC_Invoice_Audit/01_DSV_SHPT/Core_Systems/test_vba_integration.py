#!/usr/bin/env python3
"""
VBA 통합 테스트 (TDD)
===================

VBA 실행 결과 읽기 및 Python 통합 테스트
Excel 포맷팅은 절대 사용하지 않음
"""

import pytest
import pandas as pd
from pathlib import Path


class TestVBAResultReader:
    """VBA 결과 읽기 테스트"""

    @pytest.fixture
    def invoice_path(self):
        """INVOICE 파일 경로"""
        return Path("../Data/DSV 202509/SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm")

    def test_should_read_vba_master_data_from_invoice(self, invoice_path):
        """VBA MasterData 시트를 읽어야 함"""
        from vba_result_reader import VBAResultReader

        reader = VBAResultReader()
        df = reader.read_master_data(str(invoice_path))

        # MasterData 시트가 존재해야 함
        assert df is not None
        assert len(df) > 0, "MasterData should have rows"

        print(f"✅ MasterData loaded: {len(df)} rows")

    def test_should_have_vba_calculation_columns(self, invoice_path):
        """REV RATE, REV TOTAL, DIFFERENCE 컬럼이 있어야 함"""
        from vba_result_reader import VBAResultReader

        reader = VBAResultReader()
        df = reader.read_master_data(str(invoice_path))

        # VBA 계산 컬럼 확인
        expected_columns = ["REV RATE", "REV TOTAL", "DIFFERENCE"]
        for col in expected_columns:
            assert col in df.columns, f"Column '{col}' should exist in MasterData"

        print(f"✅ VBA columns found: {expected_columns}")

    def test_should_extract_rev_rate_from_vba_result(self, invoice_path):
        """REV RATE 값을 추출할 수 있어야 함"""
        from vba_result_reader import VBAResultReader

        reader = VBAResultReader()
        df = reader.read_master_data(str(invoice_path))

        # REV RATE 추출
        vba_columns = reader.extract_vba_columns(df)

        assert "REV RATE" in vba_columns.columns
        assert len(vba_columns) == len(df)

        print(f"✅ VBA columns extracted: {list(vba_columns.columns)}")

    def test_should_have_s_no_for_merging(self, invoice_path):
        """S/No 컬럼이 있어야 병합 가능"""
        from vba_result_reader import VBAResultReader

        reader = VBAResultReader()
        df = reader.read_master_data(str(invoice_path))

        assert "S/No" in df.columns, "S/No column required for merging"

        # S/No가 유효한 값인지 확인
        s_no_series = df["S/No"]
        valid_s_nos = s_no_series[pd.notna(s_no_series)]
        assert len(valid_s_nos) > 0, "At least some S/No values should be valid"

        print(f"✅ S/No column found: {len(valid_s_nos)} valid values")


class TestVBAPythonIntegration:
    """VBA-Python 통합 테스트"""

    @pytest.fixture
    def sample_python_df(self):
        """샘플 Python 검증 결과"""
        return pd.DataFrame(
            {
                "s_no": [1, 2, 3],
                "description": ["Item 1", "Item 2", "Item 3"],
                "unit_rate": [100.0, 200.0, 300.0],
                "quantity": [2, 3, 1],
                "total_usd": [200.0, 600.0, 300.0],
                "status": ["PASS", "PASS", "FAIL"],
            }
        )

    @pytest.fixture
    def sample_vba_df(self):
        """샘플 VBA 계산 결과"""
        return pd.DataFrame(
            {
                "S/No": [1, 2, 3],
                "REV RATE": [100.0, 200.0, 305.0],  # 3번 항목 차이
                "REV TOTAL": [200.0, 600.0, 305.0],
                "DIFFERENCE": [0.0, 0.0, 5.0],
            }
        )

    def test_should_merge_vba_results_with_python(self, sample_python_df, sample_vba_df):
        """VBA 결과를 Python 결과와 병합해야 함"""
        from vba_result_reader import integrate_vba_results

        merged = integrate_vba_results(sample_python_df, sample_vba_df)

        # 병합 확인
        assert len(merged) == len(sample_python_df)
        assert "vba_rev_rate" in merged.columns or "REV RATE" in merged.columns

        print(f"✅ Merged data: {merged.shape}")

    def test_should_detect_vba_python_mismatch(self, sample_python_df, sample_vba_df):
        """VBA와 Python 계산 불일치를 감지해야 함"""
        from vba_result_reader import integrate_vba_results, detect_calculation_mismatch

        merged = integrate_vba_results(sample_python_df, sample_vba_df)
        mismatches = detect_calculation_mismatch(merged)

        # S/No 3번이 불일치해야 함 (300.0 vs 305.0)
        assert len(mismatches) > 0, "Should detect mismatch in S/No 3"

        print(f"✅ Detected {len(mismatches)} mismatches")


class TestSimpleExporter:
    """단순 Excel/CSV 출력 테스트 (포맷팅 없음)"""

    @pytest.fixture
    def sample_df(self):
        """샘플 데이터"""
        return pd.DataFrame(
            {
                "s_no": [1, 2, 3],
                "description": ["Item 1", "Item 2", "Item 3"],
                "total_usd": [200.0, 600.0, 300.0],
                "vba_rev_total": [200.0, 600.0, 305.0],
            }
        )

    def test_should_export_to_csv_without_formatting(self, sample_df, tmp_path):
        """포맷팅 없이 CSV로 출력해야 함"""
        from simple_csv_exporter import export_simple_csv

        output_path = tmp_path / "test_output.csv"
        export_simple_csv(sample_df, str(output_path))

        # 파일 생성 확인
        assert output_path.exists()

        # 데이터 확인
        loaded = pd.read_csv(output_path)
        assert len(loaded) == len(sample_df)

        print(f"✅ CSV exported: {output_path}")

    def test_should_export_to_excel_without_formatting(self, sample_df, tmp_path):
        """포맷팅 없이 Excel로 출력해야 함"""
        from simple_csv_exporter import export_simple_excel

        output_path = tmp_path / "test_output.xlsx"
        export_simple_excel(sample_df, str(output_path))

        # 파일 생성 확인
        assert output_path.exists()

        # 데이터 확인
        loaded = pd.read_excel(output_path)
        assert len(loaded) == len(sample_df)

        print(f"✅ Excel exported: {output_path}")

    def test_should_not_contain_formatting_code(self):
        """simple_csv_exporter.py에 포맷팅 코드가 없어야 함"""
        import inspect
        from simple_csv_exporter import export_simple_excel

        source = inspect.getsource(export_simple_excel)

        # 금지된 키워드 검사
        forbidden = [
            "column_dimensions",
            "Font",
            "PatternFill",
            "merge_cells",
            "Alignment",
            "Border",
        ]

        for keyword in forbidden:
            assert (
                keyword not in source
            ), f"Forbidden formatting keyword '{keyword}' found in code"

        print(f"✅ No formatting code detected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

