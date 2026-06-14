# isort: skip_file

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # type: ignore[import-untyped]  # noqa: E402

from pipe1.agi_columns import SITE_COLUMNS  # noqa: E402
from pipe1.agi_columns import (
    STATUS_CURRENT_COLUMN,  # noqa: E402
    STATUS_LOCATION_COLUMN,
    STATUS_LOCATION_DATE_COLUMN,
    STATUS_SITE_COLUMN,
    STATUS_STORAGE_COLUMN,
    STATUS_WAREHOUSE_COLUMN,
)
from pipe1.post_agi_column_processor import apply_post_agi_calculations  # noqa: E402


def test_apply_post_agi_calculations_latest_location_and_storage() -> None:
    """최신 위치와 보관 분류를 확인합니다. / Validate latest location and storage."""
    data = {
        "DHL Warehouse": ["2024-01-01", None, None],
        "DSV Indoor": [None, "2024-01-05", None],
        "MIR": [None, None, None],
        "SHU": ["2024-02-01", None, None],
        "AGI": [None, None, None],
        "DAS": [None, None, None],
        "규격": [1, 1, 1],
        "수량": [1, 1, 1],
    }
    df = pd.DataFrame(data)

    result = apply_post_agi_calculations(df)

    assert list(result[STATUS_SITE_COLUMN]) == [1, "", ""]
    assert list(result[STATUS_WAREHOUSE_COLUMN]) == [1, 1, ""]

    assert result.loc[0, STATUS_CURRENT_COLUMN] == "site"
    assert result.loc[0, STATUS_LOCATION_COLUMN] == SITE_COLUMNS[1]
    assert result.loc[0, STATUS_LOCATION_DATE_COLUMN] == pd.Timestamp("2024-02-01")
    assert result.loc[0, STATUS_STORAGE_COLUMN] == "site"

    assert result.loc[1, STATUS_CURRENT_COLUMN] == "warehouse"
    assert result.loc[1, STATUS_LOCATION_COLUMN] == "DSV Indoor"
    assert result.loc[1, STATUS_LOCATION_DATE_COLUMN] == pd.Timestamp("2024-01-05")
    assert result.loc[1, STATUS_STORAGE_COLUMN] == "warehouse"

    assert result.loc[2, STATUS_CURRENT_COLUMN] == "Pre Arrival"
    assert result.loc[2, STATUS_LOCATION_COLUMN] == "Pre Arrival"
    assert pd.isna(result.loc[2, STATUS_LOCATION_DATE_COLUMN])
    assert result.loc[2, STATUS_STORAGE_COLUMN] == "Pre Arrival"

    latest_date_series = result[STATUS_LOCATION_DATE_COLUMN]
    assert pd.api.types.is_datetime64_any_dtype(latest_date_series)


def test_apply_post_agi_calculations_without_movement_columns() -> None:
    """현장·창고 부재 기본값을 확인합니다. / Validate defaults without movement columns."""
    data = {"규격": [2], "수량": [5]}
    df = pd.DataFrame(data)

    result = apply_post_agi_calculations(df)

    assert result.loc[0, STATUS_WAREHOUSE_COLUMN] == ""
    assert result.loc[0, STATUS_SITE_COLUMN] == ""
    assert result.loc[0, STATUS_CURRENT_COLUMN] == "Pre Arrival"
    assert result.loc[0, STATUS_LOCATION_COLUMN] == "Pre Arrival"
    assert pd.isna(result.loc[0, STATUS_LOCATION_DATE_COLUMN])
    assert result.loc[0, STATUS_STORAGE_COLUMN] == "Pre Arrival"
