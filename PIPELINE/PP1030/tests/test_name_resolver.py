"""이름 매칭 회귀 테스트 / Regression tests for flexible name resolution."""

from __future__ import annotations

import sys
import types
from importlib import util as importlib_util
from pathlib import Path


def _load_resolver() -> "FlexibleNameResolver":
    """동적 로드 / Dynamically load name_resolver module."""

    module_path = Path(__file__).resolve().parents[1] / "scripts" / "core" / "name_resolver.py"
    scripts_path = str(module_path.parents[1])
    if "scripts" not in sys.modules:
        namespace = types.ModuleType("scripts")
        namespace.__path__ = [scripts_path]
        sys.modules["scripts"] = namespace
    if "scripts.core" not in sys.modules:
        core_pkg = types.ModuleType("scripts.core")
        core_pkg.__path__ = [str(module_path.parent)]
        sys.modules["scripts.core"] = core_pkg
    spec = importlib_util.spec_from_file_location("_name_resolver", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load name_resolver module")
    module = importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    module.__package__ = "scripts.core"
    spec.loader.exec_module(module)
    return module.FlexibleNameResolver


FlexibleNameResolver = _load_resolver()


RESOLVER = FlexibleNameResolver()


def test_header_matching_retains_multilingual_forms() -> None:
    """헤더 유연 매칭 검증 / Ensure multilingual headers remain matchable."""

    candidates = ["Case Number", "케이스번호", "ケース番号"]
    result = RESOLVER.match_best("케이스 번호", candidates, "header")

    assert result is not None
    assert result.value == "케이스번호"
    assert result.score > 0.9


def test_file_name_matching_handles_separator_variations() -> None:
    """파일명 매칭 검증 / Match file names regardless of separators."""

    candidates = [
        "data/raw/HITACHI/Case List_Hitachi.xlsx",
        "data/raw/HITACHI/HVDC WAREHOUSE_HITACHI(HE).xlsx",
    ]
    result = RESOLVER.match_best("Case-List Hitachi.XLSX", candidates, "file")

    assert result is not None
    assert result.value == "data/raw/HITACHI/Case List_Hitachi.xlsx"
    assert result.score > 0.8


def test_sheet_name_matching_preserves_word_boundaries() -> None:
    """시트명 매칭 검증 / Preserve sheet names with flexible whitespace."""

    candidates = ["Case List, RIL", "HE Local", "HE-0214,0252 (Capacitor)"]
    result = RESOLVER.match_best("case   list  ril", candidates, "sheet")

    assert result is not None
    assert result.value == "Case List, RIL"
    assert result.score > 0.9
