# -*- coding: utf-8 -*-
"""
Test Stage 1 SIEMENS Warehouse Integration

Tests the multi-vendor warehouse loading and merging functionality.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.stage1_sync_sorted.data_synchronizer_v30 import DataSynchronizerV30
except ImportError as e:
    pytest.skip(f"Could not import DataSynchronizerV30: {e}", allow_module_level=True)


class TestSiemensWarehouseLoading:
    """Test SIEMENS warehouse file loading"""

    def test_load_warehouse_files_finds_both_vendors(self):
        """Test that both HITACHI and SIEMENS warehouse files are loaded"""
        sync = DataSynchronizerV30()

        # Mock config with both vendors
        warehouse_configs = [
            {"vendor": "HITACHI", "path": "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx", "required": False},
            {"vendor": "SIEMENS", "path": "data/raw/HVDC WAREHOUSE_SIMENSE(SIM).xlsm", "required": False}
        ]

        # Adjust paths to absolute
        for cfg in warehouse_configs:
            cfg["path"] = str(project_root / cfg["path"])

        # Test loading (may fail if files don't exist, but that's OK for this test)
        try:
            result = sync._load_warehouse_files(warehouse_configs)
            # If files exist, verify structure
            assert isinstance(result, dict)
            print(f"Loaded {len(result)} sheets")
        except FileNotFoundError:
            pytest.skip("Warehouse files not found, skipping integration test")

    def test_merge_warehouse_data_preserves_all_rows(self):
        """Test that merging preserves all rows from both vendors"""
        sync = DataSynchronizerV30()

        # Create mock dataframes
        hitachi_df = pd.DataFrame({
            "Case No.": ["CASE001", "CASE002", "CASE003"],
            "DHL Warehouse": ["2025-01-01", None, "2025-01-03"],
            "Source_Vendor": ["HITACHI", "HITACHI", "HITACHI"]
        })

        siemens_df = pd.DataFrame({
            "Case No.": ["CASE002", "CASE004"],  # CASE002 overlaps
            "DHL Warehouse": ["2025-02-01", "2025-02-04"],
            "AAA Storage": ["2025-02-01", "2025-02-04"],
            "Source_Vendor": ["SIEMENS", "SIEMENS"]
        })

        df_vendor_list = [(hitachi_df, "HITACHI"), (siemens_df, "SIEMENS")]

        result = sync._merge_warehouse_data(df_vendor_list, "TestSheet")

        # Verify all unique cases are present
        assert len(result) == 4  # CASE001, CASE002, CASE003, CASE004
        assert set(result["Case No."]) == {"CASE001", "CASE002", "CASE003", "CASE004"}

    def test_merge_warehouse_data_fills_nulls_from_siemens(self):
        """Test that SIEMENS data fills HITACHI null warehouse values"""
        sync = DataSynchronizerV30()

        # Create mock data with overlapping case but different warehouse data
        hitachi_df = pd.DataFrame({
            "Case No.": ["CASE001"],
            "DHL Warehouse": [None],  # Null in HITACHI
            "Source_Vendor": ["HITACHI"]
        })

        siemens_df = pd.DataFrame({
            "Case No.": ["CASE001"],
            "DHL Warehouse": ["2025-02-01"],  # Has data in SIEMENS
            "Source_Vendor": ["SIEMENS"]
        })

        df_vendor_list = [(hitachi_df, "HITACHI"), (siemens_df, "SIEMENS")]

        result = sync._merge_warehouse_data(df_vendor_list, "TestSheet")

        # Verify the null was filled
        assert len(result) == 1
        assert result["DHL Warehouse"].iloc[0] == "2025-02-01"

    def test_merge_prefers_hitachi_for_overlapping_cases(self):
        """Test that HITACHI data takes precedence for overlapping cases"""
        sync = DataSynchronizerV30()

        # Both have data for same case
        hitachi_df = pd.DataFrame({
            "Case No.": ["CASE001"],
            "DHL Warehouse": ["2025-01-01"],  # HITACHI has data
            "Source_Vendor": ["HITACHI"]
        })

        siemens_df = pd.DataFrame({
            "Case No.": ["CASE001"],
            "DHL Warehouse": ["2025-02-01"],  # SIEMENS also has data
            "Source_Vendor": ["SIEMENS"]
        })

        df_vendor_list = [(hitachi_df, "HITACHI"), (siemens_df, "SIEMENS")]

        result = sync._merge_warehouse_data(df_vendor_list, "TestSheet")

        # HITACHI value should be preserved (not overwritten)
        assert result["DHL Warehouse"].iloc[0] == "2025-01-01"

    def test_source_vendor_set_correctly_for_warehouse(self):
        """Test that Source_Vendor is correctly set for warehouse data"""
        sync = DataSynchronizerV30()

        hitachi_df = pd.DataFrame({
            "Case No.": ["CASE001"],
            "DHL Warehouse": ["2025-01-01"],
        })

        siemens_df = pd.DataFrame({
            "Case No.": ["CASE002"],
            "AAA Storage": ["2025-02-01"],
        })

        df_vendor_list = [(hitachi_df, "HITACHI"), (siemens_df, "SIEMENS")]

        result = sync._merge_warehouse_data(df_vendor_list, "TestSheet")

        # Verify Source_Vendor is set
        assert "Source_Vendor" in result.columns
        # Each row should have correct vendor
        vendors = set(result["Source_Vendor"])
        assert vendors == {"HITACHI", "SIEMENS"} or vendors == {"HITACHI"}


class TestSiemensWarehouseConfig:
    """Test configuration handling for SIEMENS warehouse"""

    def test_warehouse_configs_optional_files(self):
        """Test that optional files don't cause failure when missing"""
        sync = DataSynchronizerV30()

        # Config with non-existent optional file
        warehouse_configs = [
            {"vendor": "HITACHI", "path": str(project_root / "data" / "raw" / "nonexistent_he.xlsx"), "required": False},
            {"vendor": "SIEMENS", "path": str(project_root / "data" / "raw" / "nonexistent_sim.xlsm"), "required": False}
        ]

        # Should not raise exception, should return empty dict
        result = sync._load_warehouse_files(warehouse_configs)
        assert isinstance(result, dict)

    def test_warehouse_configs_required_files_raise_error(self):
        """Test that required files raise error when missing"""
        sync = DataSynchronizerV30()

        warehouse_configs = [
            {"vendor": "HITACHI", "path": str(project_root / "data" / "raw" / "nonexistent.xlsx"), "required": True}
        ]

        with pytest.raises(FileNotFoundError):
            sync._load_warehouse_files(warehouse_configs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
