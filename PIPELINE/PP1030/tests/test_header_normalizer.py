"""헤더 정규화 회귀 테스트 / Header normalization regression tests."""

from __future__ import annotations

from importlib import util as importlib_util
from pathlib import Path


def _load_header_normalizer() -> "HeaderNormalizer":
    """동적 모듈 로드 / Dynamically load header_normalizer module."""
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "core" / "header_normalizer.py"
    spec = importlib_util.spec_from_file_location("_header_normalizer", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load header_normalizer module")
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.HeaderNormalizer


HeaderNormalizer = _load_header_normalizer()


def test_normalize_retains_korean_characters() -> None:
    """한글 유지 / Preserve Korean characters during normalization."""
    normalizer = HeaderNormalizer()

    assert normalizer.normalize("케이스번호") == "케이스번호"


def test_normalize_retains_japanese_characters() -> None:
    """일본어 유지 / Preserve Japanese characters during normalization."""
    normalizer = HeaderNormalizer()

    assert normalizer.normalize("ケース番号") == "ケース番号"


def test_alternatives_include_non_latin_variants() -> None:
    """비라틴 대안 유지 / Alternatives include non-Latin variants."""
    normalizer = HeaderNormalizer()

    korean_alternatives = normalizer.normalize_with_alternatives("케이스번호")
    japanese_alternatives = normalizer.normalize_with_alternatives("ケース番号")

    assert "케이스번호" in korean_alternatives and "" not in korean_alternatives
    assert "ケース番号" in japanese_alternatives and "" not in japanese_alternatives
