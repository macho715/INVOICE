"""
Unit tests for core.duplicate_handler module
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from scripts.core.duplicate_handler import (
    NormalizationProfile,
    normalize_case_series,
    detect_case_column,
    mark_duplicates,
    compute_global_dup_flags,
    drop_duplicates_by_case,
    drop_duplicates_global,
    validate_duplicate_removal,
)


class TestNormalization:
    """Test Case No normalization functions"""

    def test_normalize_basic(self):
        """Test basic normalization: uppercase, remove spaces"""
        series = pd.Series(["Case-001", "case 002", "CASE_003"])
        result = normalize_case_series(series)
        assert result.iloc[0] == "CASE-001"
        assert result.iloc[1] == "CASE002"
        assert result.iloc[2] == "CASE-003"

    def test_normalize_separator_unification(self):
        """Test separator unification: _, / → -"""
        series = pd.Series(["Case_001", "Case/002", "Case-003"])
        result = normalize_case_series(series)
        assert all("-" in val for val in result)
        assert result.iloc[0] == "CASE-001"
        assert result.iloc[1] == "CASE-002"

    def test_normalize_zero_pad(self):
        """Test zero padding for trailing digits"""
        profile = NormalizationProfile(zero_pad_digits=6)
        series = pd.Series(["HE123", "CASE45"])
        result = normalize_case_series(series, profile=profile)
        assert result.iloc[0] == "HE000123"
        assert result.iloc[1] == "CASE000045"

    def test_normalize_nan_handling(self):
        """Test NaN/None handling"""
        series = pd.Series(["CASE001", None, pd.NA, ""])
        result = normalize_case_series(series)
        assert result.iloc[0] == "CASE001"
        assert result.iloc[1] == ""
        # pd.NA might convert to string "NA" or "", check both
        assert result.iloc[2] in ["", "NA"]
        assert result.iloc[3] == ""


class TestDetectCaseColumn:
    """Test Case column detection"""

    def test_detect_case_column_exists(self):
        """Test detection when Case No column exists"""
        df = pd.DataFrame({"Case No.": [1, 2, 3], "Other": [10, 20, 30]})
        col = detect_case_column(df, required=False)
        assert col == "Case No."

    def test_detect_case_column_fallback(self):
        """Test fallback when Case No not found"""
        df = pd.DataFrame({"Case": [1, 2, 3], "Other": [10, 20, 30]})
        col = detect_case_column(df, required=False)
        assert col == "Case"  # heuristic fallback

    def test_detect_case_column_missing_required(self):
        """Test raises error when required=True and column not found"""
        df = pd.DataFrame({"Other": [10, 20, 30]})
        with pytest.raises(KeyError):
            detect_case_column(df, required=True)


class TestMarkDuplicates:
    """Test duplicate marking within a single DataFrame"""

    def test_mark_duplicates_basic(self):
        """Test basic duplicate marking"""
        df = pd.DataFrame(
            {
                "Case No.": ["CASE001", "CASE002", "CASE001", "CASE003"],
                "Value": [10, 20, 30, 40],
            }
        )
        df_with_flag, dup_mask = mark_duplicates(df, keep="first")
        assert "고유 중복" in df_with_flag.columns or "__dup_label__" in df_with_flag.columns
        assert dup_mask.sum() == 1  # one duplicate
        # First occurrence should not be marked as duplicate
        assert not dup_mask.iloc[0]
        # Second occurrence of CASE001 should be duplicate
        assert dup_mask.iloc[2]

    def test_mark_duplicates_no_duplicates(self):
        """Test when no duplicates exist"""
        df = pd.DataFrame(
            {
                "Case No.": ["CASE001", "CASE002", "CASE003"],
                "Value": [10, 20, 30],
            }
        )
        df_with_flag, dup_mask = mark_duplicates(df, keep="first")
        assert dup_mask.sum() == 0


class TestDropDuplicatesByCase:
    """Test dropping duplicates from a DataFrame"""

    def test_drop_duplicates_basic(self):
        """Test basic duplicate removal"""
        df = pd.DataFrame(
            {
                "Case No.": ["CASE001", "CASE002", "CASE001", "CASE003"],
                "Value": [10, 20, 30, 40],
            }
        )
        result = drop_duplicates_by_case(df, keep="first")
        assert len(result) == 3
        assert "CASE001" in result["Case No."].values
        assert result["Case No."].nunique() == 3

    def test_drop_duplicates_keep_last(self):
        """Test keeping last duplicate"""
        df = pd.DataFrame(
            {
                "Case No.": ["CASE001", "CASE002", "CASE001"],
                "Value": [10, 20, 30],
            }
        )
        result = drop_duplicates_by_case(df, keep="last")
        assert len(result) == 2
        # Last occurrence should have Value=30
        case001_rows = result[result["Case No."] == "CASE001"]
        assert len(case001_rows) == 1
        assert case001_rows.iloc[0]["Value"] == 30


class TestComputeGlobalDupFlags:
    """Test global duplicate flag computation across sheets"""

    def test_compute_global_dup_flags_basic(self):
        """Test basic global flag computation"""
        df1 = pd.DataFrame({"Case No.": ["CASE001", "CASE002"], "Sheet": ["A", "A"]})
        df2 = pd.DataFrame({"Case No.": ["CASE002", "CASE003"], "Sheet": ["B", "B"]})
        sheet_dfs = {"Sheet1": df1, "Sheet2": df2}

        updated, summary = compute_global_dup_flags(sheet_dfs)

        # CASE002 appears in both sheets → should be marked as duplicate in both
        assert len(updated) == 2
        assert len(summary) == 2
        assert "고유" in summary.columns
        assert "중복" in summary.columns

    def test_compute_global_dup_flags_no_duplicates(self):
        """Test when no cross-sheet duplicates exist"""
        df1 = pd.DataFrame({"Case No.": ["CASE001", "CASE002"], "Sheet": ["A", "A"]})
        df2 = pd.DataFrame({"Case No.": ["CASE003", "CASE004"], "Sheet": ["B", "B"]})
        sheet_dfs = {"Sheet1": df1, "Sheet2": df2}

        updated, summary = compute_global_dup_flags(sheet_dfs)
        # All should be unique
        assert summary["중복"].sum() == 0


class TestDropDuplicatesGlobal:
    """Test global duplicate removal across multiple DataFrames"""

    def test_drop_duplicates_global_basic(self):
        """Test basic global duplicate removal"""
        df1 = pd.DataFrame({"Case No.": ["CASE001", "CASE002"], "Value": [10, 20]})
        df2 = pd.DataFrame({"Case No.": ["CASE002", "CASE003"], "Value": [30, 40]})
        dfs = [df1, df2]

        pre_diag, merged = drop_duplicates_global(dfs, keep="first")
        # CASE002 appears in both → should be removed (keep first from df1)
        assert len(merged) == 3  # CASE001, CASE002 (from df1), CASE003
        assert merged["Case No."].nunique() == 3
        assert len(pre_diag) == 2  # diagnostic for 2 sheets


class TestValidateDuplicateRemoval:
    """Test validation and summary functions"""

    def test_validate_duplicate_removal(self):
        """Test validation summary generation"""
        diag_df = pd.DataFrame(
            {
                "part": ["sheet_1", "sheet_2"],
                "rows": [100, 200],
                "unique": [95, 195],
                "dups": [5, 5],
            }
        )
        result = validate_duplicate_removal(diag_df)
        assert result["total_rows"] == 300.0
        assert result["total_dups"] == 10.0
        assert result["dup_rate"] == pytest.approx(10.0 / 300.0, abs=0.001)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

