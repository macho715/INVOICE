import importlib
import sys
import types
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture()
def semantic_matcher(monkeypatch):
    """단일 테스트용 판다스/넘파이 스텁 삽입 - Stage matcher import with minimal pandas/numpy stubs."""
    monkeypatch.syspath_prepend(str(BASE_DIR))

    pandas_stub = types.ModuleType("pandas")
    pandas_stub.DataFrame = type("DataFrame", (), {})  # type: ignore[attr-defined]
    pandas_stub.Series = type("Series", (), {})  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pandas", pandas_stub)

    numpy_stub = types.ModuleType("numpy")
    monkeypatch.setitem(sys.modules, "numpy", numpy_stub)

    module = importlib.import_module("scripts.core.semantic_matcher")
    return module.MatchReport, module.MatchResult


def test_print_summary_formats_column_name_without_literal_format_spec(semantic_matcher, capfd):
    MatchReport, MatchResult = semantic_matcher

    report = MatchReport(
        total_semantic_keys=1,
        successful_matches=1,
        failed_matches=0,
        average_confidence=0.95,
        results=[
            MatchResult(
                semantic_key="case_number",
                matched=True,
                column_name="Case No.",
                confidence=0.92,
                match_type="exact",
            )
        ],
    )

    report.print_summary()
    captured = capfd.readouterr().out

    assert ":<30s" not in captured

    detail_line = next(
        line for line in captured.splitlines() if "case_number" in line and "Case No." in line
    )

    column_start = detail_line.index("Case No.")
    column_segment = detail_line[column_start : column_start + 30]
    expected_segment = "Case No." + " " * (30 - len("Case No."))

    assert column_segment == expected_segment
