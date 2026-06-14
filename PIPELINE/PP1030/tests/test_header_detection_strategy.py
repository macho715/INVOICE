"""헤더 탐지 보강 시나리오 테스트. | Tests for improved header detection strategies."""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import pytest

from scripts.core import HeaderDetectionResult
from scripts.stage1_sync_sorted.data_synchronizer_v30 import DataSynchronizerV30


@pytest.fixture
def base_override() -> Dict[Tuple[str, str], int]:
    """기본 오버라이드 딕셔너리. | Provide base override dictionary for tests."""

    return {("warehouse", "sheet1"): 2}


def test_manual_header_override_precedence(tmp_path: Path, base_override):
    """수동 지정이 우선 적용되는지 확인. | Manual override should take precedence."""

    raw = pd.DataFrame(
        [
            [None, None, None],
            [None, None, None],
            ["Case No.", "Description", "ETA"],
            ["A1", "Transformer", "2024-01-01"],
        ]
    )
    excel_path = tmp_path / "warehouse.xlsx"
    raw.to_excel(excel_path, index=False, header=False)

    sync = DataSynchronizerV30(header_overrides=base_override)
    sync.debug_dhl_wh = False

    sheet_data = sync._load_file_by_sheets(str(excel_path), "Warehouse")
    df, header_row = sheet_data["Sheet1"]

    assert header_row == 2
    assert list(df.columns) == ["Case No.", "Description", "ETA"]


def test_vendor_fallback_when_heuristic_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """벤더 기본값이 휴리스틱 실패 시 활용되는지 검증. | Vendor fallback kicks in on heuristic failure."""

    df = pd.DataFrame(
        {
            "Case No.": ["A1", "A2", "A3", "A4", "A5"],
            "Description": ["Item"] * 5,
            "ETA": ["2024-01-01"] * 5,
        }
    )
    excel_path = tmp_path / "simense_report.xlsx"
    df.to_excel(excel_path, index=False)

    sync = DataSynchronizerV30()
    sync.debug_dhl_wh = False

    fake_result = HeaderDetectionResult(
        row_index=4,
        confidence=0.2,
        threshold=sync.header_confidence_threshold,
        method="heuristic",
        warnings=["LOW_CONFIDENCE: forced for test"],
    )

    monkeypatch.setattr(
        sync.header_detector,
        "detect_with_diagnostics",
        lambda file_path, sheet_name: fake_result,
    )

    sheet_data = sync._load_file_by_sheets(str(excel_path), "Warehouse")
    df_loaded, header_row = sheet_data["Sheet1"]

    assert header_row == 0
    assert "Case No." in df_loaded.columns
