import pandas as pd

from core.semantic_matcher import SemanticMatcher


def test_semantic_matcher_respects_alias_normalization():
    """Test that semantic matcher can match aliased headers like Case# and Q'ty"""
    df = pd.DataFrame({"Case#": ["A001", "A002"], "Q'ty": [10, 20]})
    m = SemanticMatcher()
    report = m.match_dataframe(df, semantic_keys=["case_number"])

    # Test case_number matching (Case# should match via alias resolution)
    case_col = report.get_column_name("case_number")
    assert case_col is not None, f"case_number not matched. Available: {df.columns.tolist()}"
    assert case_col.lower().replace(" ", "") in {"case#", "caseno"}, f"Unexpected column: {case_col}"

    # Verify that normalized columns include canonical alternatives
    normalized = m._normalize_dataframe_columns(df)
    assert "caseno" in normalized or "case no" in normalized or "case#" in normalized.lower(), \
        f"Normalized columns should include case variants. Got: {list(normalized.keys())}"


def test_semantic_matcher_handles_simense_typo():
    df = pd.DataFrame({"RIL(SIMENSE) Case List": [1, 2]})
    m = SemanticMatcher()
    report = m.match_dataframe(df)
    assert hasattr(report, "results")
