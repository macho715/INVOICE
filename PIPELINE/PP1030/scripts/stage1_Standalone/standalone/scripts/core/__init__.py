# -*- coding: utf-8 -*-
"""
HVDC Pipeline Core Module (Standalone Package)
==============================================

Central header matching and detection system for all pipeline stages.
Standalone package includes only essential modules for Stage 1 synchronization.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from .header_normalizer import HeaderNormalizer, normalize_header
from .semantic_matcher import SemanticMatcher, find_header_by_meaning
from .header_registry import HeaderRegistry, HVDC_HEADER_REGISTRY, HeaderCategory, HeaderDefinition
from .standard_header_order import (
    STANDARD_HEADER_ORDER,
    STAGE2_HEADER_ORDER,
    STAGE1_BASE_COLS_ORDER,
    HeaderOrderManager,
    reorder_dataframe_columns,
)

DEFAULT_HEADER_CONFIDENCE = 0.7


@dataclass
class HeaderDetectionResult:
    """헤더 탐지 결과와 경고를 보관합니다. | Store header detection outcome and warnings."""

    row_index: int
    confidence: float
    threshold: float
    method: str = "heuristic"
    warnings: List[str] = field(default_factory=list)

    @property
    def is_confident(self) -> bool:
        """임계치 충족 여부를 반환합니다. | Return whether confidence meets the threshold."""

        return self.confidence >= self.threshold

    def to_tuple(self) -> Tuple[int, float]:
        """기존 API 호환을 위한 튜플을 제공합니다. | Provide legacy (row, confidence) tuple."""

        return self.row_index, self.confidence

# Minimal detect_header_row implementation (header_detector not included in standalone)
def detect_header_row_with_diagnostics(
    xlsx_path: str,
    sheet_name: str,
    max_scan_rows: int = 20,
    min_confidence: float = DEFAULT_HEADER_CONFIDENCE,
) -> HeaderDetectionResult:
    """간이 휴리스틱으로 헤더를 찾고 진단 정보를 제공합니다. | Detect header with simple diagnostics."""

    warnings: List[str] = []
    try:
        import pandas as pd

        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
        df = pd.read_excel(xl, sheet_name=sheet_name, header=None, nrows=max_scan_rows)

        # Simple heuristic: find first row with mostly text and many non-null values
        best_idx = 0
        best_score = 0.0

        for idx in range(min(max_scan_rows, len(df))):
            row = df.iloc[idx]
            non_null = row.notna().sum()
            if non_null == 0:
                continue
            text_count = sum(1 for v in row if isinstance(v, str) and str(v).strip())
            score = (non_null / len(row)) * 0.5 + (text_count / non_null) * 0.5

            if score > best_score:
                best_score = score
                best_idx = idx
    except Exception:
        # Fallback: assume header is at row 0
        best_idx = 0
        best_score = min_confidence
        warnings.append("FALLBACK: Failed to scan rows; defaulting to row 0")

    confidence = max(0.0, min(1.0, best_score))
    if confidence < min_confidence:
        warnings.append(
            f"LOW_CONFIDENCE: score {confidence:.2f} below threshold {min_confidence:.2f}"
        )

    return HeaderDetectionResult(
        row_index=best_idx,
        confidence=confidence,
        threshold=min_confidence,
        method="heuristic",
        warnings=warnings,
    )


def detect_header_row(
    xlsx_path: str, sheet_name: str, max_scan_rows: int = 20
) -> Tuple[int, float]:
    """기존 튜플 기반 인터페이스를 유지합니다. | Preserve legacy tuple-based interface."""

    result = detect_header_row_with_diagnostics(
        xlsx_path=xlsx_path,
        sheet_name=sheet_name,
        max_scan_rows=max_scan_rows,
    )
    return result.to_tuple()

# Convenience functions for getting warehouse/site/date columns from registry
def get_warehouse_columns(use_primary_alias=True):
    """Get warehouse columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_warehouse_columns(use_primary_alias)

def get_site_columns(use_primary_alias=True):
    """Get site columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_site_columns(use_primary_alias)

def get_date_columns(use_primary_alias=True):
    """Get date columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_date_columns(use_primary_alias)

__version__ = "1.2.0-standalone"
__all__ = [
    "HeaderNormalizer",
    "normalize_header",
    "SemanticMatcher",
    "find_header_by_meaning",
    "HeaderRegistry",
    "HVDC_HEADER_REGISTRY",
    "HeaderCategory",
    "HeaderDefinition",
    "STANDARD_HEADER_ORDER",
    "STAGE2_HEADER_ORDER",
    "STAGE1_BASE_COLS_ORDER",
    "HeaderOrderManager",
    "reorder_dataframe_columns",
    "get_warehouse_columns",
    "get_site_columns",
    "get_date_columns",
    "HeaderDetectionResult",
    "detect_header_row_with_diagnostics",
    "detect_header_row",
]
