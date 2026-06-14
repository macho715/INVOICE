# -*- coding: utf-8 -*-
"""파생 컬럼 정의 상수 모듈/Derived column definition constants module."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final, List

# Add project root to path to access core module
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from core import get_warehouse_columns, get_site_columns

# ============================================================================
# HEADER MANAGEMENT: CENTRALIZED IN @core/
# ============================================================================
# All warehouse and site column definitions are sourced from @core/header_registry.py
# This is the Single Source of Truth for all header/column management.
#
# Benefits:
# - Consistency across all stages
# - Automatic handling of header variations (whitespace, case, aliases)
# - Easy maintenance (add new warehouse/site in one place)
#
# DO NOT hardcode warehouse/site lists here. Always use:
#   get_warehouse_columns() - Returns list from core registry (9 warehouses)
#   get_site_columns() - Returns list from core registry (4 sites)
#
# For details: @core/README.md, @core/INTEGRATION_GUIDE.md
# ============================================================================

# Generate from core registry (Single Source of Truth)
WAREHOUSE_COLUMNS: Final[List[str]] = get_warehouse_columns()
SITE_COLUMNS: Final[List[str]] = get_site_columns()

STATUS_WAREHOUSE_COLUMN: Final[str] = "Status_WAREHOUSE"
STATUS_SITE_COLUMN: Final[str] = "Status_SITE"
STATUS_CURRENT_COLUMN: Final[str] = "Status_Current"
STATUS_LOCATION_COLUMN: Final[str] = "Status_Location"
STATUS_LOCATION_DATE_COLUMN: Final[str] = "Status_Location_Date"
STATUS_STORAGE_COLUMN: Final[str] = "Status_Storage"
WH_HANDLING_COLUMN: Final[str] = "wh handling"
SITE_HANDLING_COLUMN: Final[str] = "site  handling"
TOTAL_HANDLING_COLUMN: Final[str] = "total handling"
MINUS_COLUMN: Final[str] = "minus"
FINAL_HANDLING_COLUMN: Final[str] = "final handling"
SQM_COLUMN: Final[str] = "SQM"
STACK_STATUS_COLUMN: Final[str] = "Stack_Status"

DERIVED_COLUMNS: Final[List[str]] = [
    STATUS_WAREHOUSE_COLUMN,
    STATUS_SITE_COLUMN,
    STATUS_CURRENT_COLUMN,
    STATUS_LOCATION_COLUMN,
    STATUS_LOCATION_DATE_COLUMN,
    STATUS_STORAGE_COLUMN,
    WH_HANDLING_COLUMN,
    SITE_HANDLING_COLUMN,
    TOTAL_HANDLING_COLUMN,
    MINUS_COLUMN,
    FINAL_HANDLING_COLUMN,
    SQM_COLUMN,
    STACK_STATUS_COLUMN,
]
