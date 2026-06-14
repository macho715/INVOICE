"""Stage-1 창고 헤더 정규화 테스트/Stage-1 warehouse header compatibility."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pandas as pd


def _load_reporter_module() -> ModuleType:
    """Stage-1 모듈에서 리포터 로드/Load reporter from Stage-1 module."""

    module_dir = Path(__file__).parent.parent
    module_path = module_dir / "hvdc_excel_reporter_final_sqm_rev (1).py"
    spec = importlib.util.spec_from_file_location(
        "hvdc_excel_reporter_final_sqm_rev", module_path
    )
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("Unable to load hvdc_excel_reporter module")
    spec.loader.exec_module(module)
    return module


def test_stage1_warehouse_columns_support() -> None:
    """HAULER·JDN MZD 입출고·SQM 반영/Ensure HAULER·JDN MZD appear in IO & SQM."""

    module = _load_reporter_module()
    calculator = module.CorrectedWarehouseIOCalculator()

    df = pd.DataFrame(
        [
            {
                "Pkg": 1,
                "HAULER": pd.Timestamp("2024-05-01"),
                "MIR": pd.Timestamp("2024-05-02"),
            },
            {
                "Pkg": 2,
                "JDN MZD": pd.Timestamp("2024-06-01"),
                "SHU": pd.Timestamp("2024-06-03"),
            },
        ]
    )

    inbound = calculator.calculate_warehouse_inbound_corrected(df)
    outbound = calculator.calculate_warehouse_outbound_corrected(df)
    sqm_inbound = calculator.calculate_monthly_sqm_inbound(df)
    sqm_outbound = calculator.calculate_monthly_sqm_outbound(df)

    assert inbound["by_warehouse"]["HAULER"] == 1
    assert inbound["by_warehouse"]["JDN MZD"] == 2

    assert outbound["by_warehouse"]["HAULER"] == 1
    assert outbound["by_warehouse"]["JDN MZD"] == 2

    assert "HAULER" in sqm_inbound["2024-05"]
    assert "JDN MZD" in sqm_inbound["2024-06"]

    assert "HAULER" in sqm_outbound["2024-05"]
    assert "JDN MZD" in sqm_outbound["2024-06"]

