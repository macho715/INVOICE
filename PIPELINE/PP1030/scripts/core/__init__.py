# -*- coding: utf-8 -*-
"""
HVDC Pipeline Core Module
=========================

Central header matching and detection system for all pipeline stages.
This module provides robust, flexible header matching with zero hardcoding.

Main Components:
- header_detector: Automatically finds where headers start in Excel files
- header_normalizer: Normalizes header names handling all edge cases
- semantic_matcher: Matches headers based on meaning, not exact strings
- header_registry: Configuration for semantic mappings across all stages
- data_parser: Core data parsing utilities (Stack_Status, SQM, unit conversions)
"""

from .data_parser import (
    calculate_sqm,
    convert_mm_to_cm,
    map_stack_status,
    parse_stack_status,
)
from .file_registry import (
    FileRegistry,
    get_master_file,
    get_source_file_name,
    get_synced_file,
    get_warehouse_file,
    normalize_vendor_name,
)
from .header_detector import (
    HeaderDetectionResult,
    HeaderDetector,
    detect_header_row,
    detect_header_row_with_diagnostics,
)
from .header_normalizer import HeaderNormalizer, normalize_header
from .header_registry import (
    HVDC_HEADER_REGISTRY,
    HeaderCategory,
    HeaderDefinition,
    HeaderRegistry,
)
from .name_resolver import FlexibleNameResolver, MatchResult
from .semantic_matcher import SemanticMatcher, find_header_by_meaning
from .standard_header_order import (
    STAGE1_BASE_COLS_ORDER,
    STAGE2_HEADER_ORDER,
    STANDARD_HEADER_ORDER,
    HeaderOrderManager,
)
from .duplicate_handler import (
    NormalizationProfile,
    normalize_case_series,
    detect_case_column,
    mark_duplicates,
    compute_global_dup_flags,
    drop_duplicates_by_case,
    drop_duplicates_global,
    inject_excel_dup_column,
    validate_duplicate_removal,
)
from .file_finder import (
    RawFileHit,
    find_vendor_files,
    scan_raw_folder,
)


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


__version__ = "1.2.0"
__all__ = [
    "HeaderDetector",
    "HeaderDetectionResult",
    "detect_header_row",
    "detect_header_row_with_diagnostics",
    "HeaderNormalizer",
    "normalize_header",
    "SemanticMatcher",
    "find_header_by_meaning",
    "HeaderRegistry",
    "HVDC_HEADER_REGISTRY",
    "HeaderCategory",
    "HeaderDefinition",
    "FlexibleNameResolver",
    "MatchResult",
    "parse_stack_status",
    "calculate_sqm",
    "convert_mm_to_cm",
    "map_stack_status",
    "STANDARD_HEADER_ORDER",
    "STAGE2_HEADER_ORDER",
    "STAGE1_BASE_COLS_ORDER",
    "HeaderOrderManager",
    "get_warehouse_columns",
    "get_site_columns",
    "get_date_columns",
    "FileRegistry",
    "get_master_file",
    "get_warehouse_file",
    "get_synced_file",
    "normalize_vendor_name",
    "get_source_file_name",
    "NormalizationProfile",
    "normalize_case_series",
    "detect_case_column",
    "mark_duplicates",
    "compute_global_dup_flags",
    "drop_duplicates_by_case",
    "drop_duplicates_global",
    "inject_excel_dup_column",
    "validate_duplicate_removal",
    "RawFileHit",
    "find_vendor_files",
    "scan_raw_folder",
]
