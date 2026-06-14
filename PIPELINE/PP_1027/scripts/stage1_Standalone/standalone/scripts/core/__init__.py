# -*- coding: utf-8 -*-
"""
scripts.core package shim for standalone distribution.
Re-exports commonly used symbols and provides detect_header_row utility.
"""
from .header_registry import (
    HeaderRegistry, HeaderCategory, HVDC_HEADER_REGISTRY
)
from .semantic_matcher import (
    SemanticMatcher, find_header_by_meaning
)
from .standard_header_order import (
    STAGE1_BASE_COLS_ORDER, reorder_dataframe_columns
)

# Convenience functions for getting warehouse/site/date columns from central registry
def get_warehouse_columns(use_primary_alias: bool = True):
    """Get warehouse columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_warehouse_columns(use_primary_alias)

def get_site_columns(use_primary_alias: bool = True):
    """Get site columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_site_columns(use_primary_alias)

def get_date_columns(use_primary_alias: bool = True):
    """Get date columns from central registry."""
    return HVDC_HEADER_REGISTRY.get_date_columns(use_primary_alias)

# Lightweight header row detection using heuristic matching against registry aliases.
def detect_header_row(xlsx_path: str, sheet_name: str, max_scan_rows: int = 20):
    import pandas as pd
    from .header_registry import HVDC_HEADER_REGISTRY
    reg = HVDC_HEADER_REGISTRY
    # Read top part without header
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None, nrows=max_scan_rows, engine="openpyxl")
    best_idx, best_score = None, -1.0
    # Build alias bag (lowercased normalized set)
    alias_bag = set()
    for defn in reg.definitions.values():
        for a in defn.aliases:
            alias_bag.add(a.strip().lower())
    # Score each row
    for r in range(len(df)):
        row = df.iloc[r].tolist()
        tokens = [str(c).strip().lower() for c in row if c is not None and str(c).strip() != ""]
        if not tokens:
            continue
        hits = 0.0
        for t in tokens:
            if t in alias_bag:
                hits += 1.0
            elif any(k in t for k in ["no", "site", "case", "qty", "price", "code", "date", "warehouse","handling","status"]):
                hits += 0.5
        score = hits / max(1, len(tokens))
        if score > best_score:
            best_score, best_idx = score, r
    confidence = max(0.0, min(1.0, best_score))
    return best_idx, confidence

# Export all symbols
__all__ = [
    "HeaderRegistry",
    "HeaderCategory",
    "HVDC_HEADER_REGISTRY",
    "SemanticMatcher",
    "find_header_by_meaning",
    "STAGE1_BASE_COLS_ORDER",
    "reorder_dataframe_columns",
    "get_warehouse_columns",
    "get_site_columns",
    "get_date_columns",
    "detect_header_row",
]