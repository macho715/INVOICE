#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HVDC Flow Code를 지정한 Excel 파일의 특정 시트에만 적용하는 스크립트.

사용 예:
  python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx" "hvdc all status"
  python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx"  # 시트명 기본값: hvdc all status
  python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --header-row 1

필요 컬럼: Status_Location, 창고 컬럼( DHL WH, DSV Indoor, ... MOSB ), 현장 컬럼( MIR, SHU, DAS, AGI ).
레지스트리 alias와 매칭되면 다른 컬럼명(예: DHL Warehouse)도 인식함.
추가 후 컬럼: FLOW_CODE (0~5), FLOW_DESCRIPTION.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 프로젝트 루트 및 scripts (core는 scripts/core에 있음)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core import get_warehouse_columns, get_site_columns
from core.header_registry import HVDC_HEADER_REGISTRY


def apply_flow_code_to_dataframe(
    df: pd.DataFrame,
    warehouse_columns: list,
    site_columns: list,
) -> pd.DataFrame:
    """
    파이프라인과 동일한 v3.5 Flow Code 로직을 DataFrame에 적용.
    FLOW_CODE (0~5), FLOW_DESCRIPTION 컬럼을 추가/덮어씀.
    """
    out = df.copy()
    WH_COLS = [w for w in warehouse_columns if w != "MOSB"]
    MOSB_COLS = [w for w in warehouse_columns if w == "MOSB"]

    # 0/빈문자열 → NaN
    for col in WH_COLS + MOSB_COLS:
        if col in out.columns:
            out[col] = out[col].replace({0: np.nan, "": np.nan})

    status_col = "Status_Location"
    if status_col not in out.columns:
        out["FLOW_CODE"] = 5
        out["FLOW_DESCRIPTION"] = "Flow 5: Mixed / Waiting / Incomplete leg"
        return out

    is_pre_arrival = out[status_col].astype(str).str.contains(
        "Pre Arrival", case=False, na=False
    )
    wh_cnt = (
        out[WH_COLS].notna().sum(axis=1)
        if WH_COLS and all(c in out.columns for c in WH_COLS)
        else pd.Series(0, index=out.index)
    )
    has_mosb = (
        out[MOSB_COLS].notna().any(axis=1)
        if MOSB_COLS and all(c in out.columns for c in MOSB_COLS)
        else pd.Series(False, index=out.index)
    )
    SITE_COLS = [c for c in site_columns if c in out.columns]
    has_site = (
        out[SITE_COLS].notna().any(axis=1)
        if SITE_COLS
        else pd.Series(True, index=out.index)
    )

    flow = pd.Series(0, index=out.index, dtype="int64")
    flow_desc = pd.Series("", index=out.index, dtype="object")

    flow[is_pre_arrival] = 0
    flow_desc[is_pre_arrival] = "Flow 0: Pre Arrival"
    not_pre = ~is_pre_arrival

    flow[not_pre & (wh_cnt == 0) & (~has_mosb)] = 1
    flow_desc[not_pre & (wh_cnt == 0) & (~has_mosb)] = "Flow 1: Port → Site"
    flow[not_pre & (wh_cnt >= 1) & (~has_mosb)] = 2
    flow_desc[not_pre & (wh_cnt >= 1) & (~has_mosb)] = "Flow 2: Port → WH → Site"
    flow[not_pre & (wh_cnt == 0) & has_mosb] = 3
    flow_desc[not_pre & (wh_cnt == 0) & has_mosb] = "Flow 3: Port → MOSB → Site (AGI/DAS)"
    flow[not_pre & (wh_cnt >= 1) & has_mosb] = 4
    flow_desc[not_pre & (wh_cnt >= 1) & has_mosb] = "Flow 4: Port → WH → MOSB → Site (AGI/DAS)"

    final_col = None
    for cand in ["Final_Location", "Final location", "Final_Location_Site", "Site_Final"]:
        if cand in out.columns:
            final_col = cand
            break
    if final_col is not None:
        final_location = out[final_col].astype(str).str.upper()
        is_agi_das = final_location.isin(["AGI", "DAS"])
        need_force = is_agi_das & flow.isin([0, 1, 2])
        flow[need_force] = 3
        flow_desc[need_force] = "Flow 3: Port → MOSB → Site (AGI/DAS forced)"

    cond_mosb_no_site = has_mosb & (~has_site)
    cond_weird_wh = (wh_cnt >= 2) & (~has_mosb) & (~is_pre_arrival)
    need_5 = cond_mosb_no_site | cond_weird_wh
    flow[need_5] = 5
    flow_desc[need_5] = "Flow 5: Mixed / Waiting / Incomplete leg"

    out["FLOW_CODE"] = flow.astype("int64")
    out["FLOW_DESCRIPTION"] = flow_desc
    return out


def _latest_location_and_date(row: pd.Series) -> tuple:
    """한 행의 날짜 시리즈에서 최대 날짜인 컬럼명과 그 날짜 반환. (Stage2 동일)."""
    non_null = row.dropna()
    if non_null.empty:
        return None, pd.NaT
    latest_date = non_null.max()
    latest_columns = non_null[non_null == latest_date].index
    return latest_columns[0], latest_date


def derive_status_location(
    df: pd.DataFrame,
    warehouse_columns: list,
    site_columns: list,
) -> pd.DataFrame:
    """
    Status_Location이 없을 때 Stage2와 동일 규칙으로 파생.
    창고/현장 날짜 컬럼 중 존재하는 것만 사용 → Status_Current → 최근 위치.
    """
    out = df.copy()
    wh_cols = [c for c in warehouse_columns if c in out.columns]
    st_cols = [c for c in site_columns if c in out.columns]
    if not wh_cols and not st_cols:
        out["Status_Location"] = "Pre Arrival"
        return out

    for col in wh_cols + st_cols:
        out[col] = pd.to_datetime(out[col], errors="coerce")

    has_wh = out[wh_cols].notna().any(axis=1) if wh_cols else pd.Series(False, index=out.index)
    has_site = out[st_cols].notna().any(axis=1) if st_cols else pd.Series(False, index=out.index)
    status_current = pd.Series("Pre Arrival", index=out.index)
    status_current.loc[has_site] = "site"
    status_current.loc[has_wh & ~has_site] = "warehouse"

    location_series = pd.Series("Pre Arrival", index=out.index)

    if st_cols:
        site_latest = out[st_cols].apply(_latest_location_and_date, axis=1, result_type="expand")
        site_latest.columns = ["location", "date"]
        site_mask = status_current == "site"
        locs = site_latest.loc[site_mask, "location"].fillna("Pre Arrival")
        location_series.loc[site_mask] = locs

    if wh_cols:
        wh_latest = out[wh_cols].apply(_latest_location_and_date, axis=1, result_type="expand")
        wh_latest.columns = ["location", "date"]
        wh_mask = status_current == "warehouse"
        locs = wh_latest.loc[wh_mask, "location"].fillna("Pre Arrival")
        location_series.loc[wh_mask] = locs

    out["Status_Location"] = location_series.replace({None: "Pre Arrival"})
    return out


def _normalize(s: str) -> str:
    return str(s).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def find_sheet_by_name(wb_sheet_names: list, target: str) -> str | None:
    """대소문자/공백 무시하고 시트명 매칭."""
    target_norm = _normalize(target)
    for name in wb_sheet_names:
        if _normalize(name) == target_norm:
            return name
    return None


def build_excel_to_primary_map(excel_columns: list) -> dict[str, str]:
    """Excel 컬럼명 -> 레지스트리 primary alias 매핑 (alias 매칭)."""
    warehouse_keys = get_warehouse_columns(use_primary_alias=False)
    site_keys = get_site_columns(use_primary_alias=False)
    result = {}
    for key in warehouse_keys + site_keys:
        try:
            definition = HVDC_HEADER_REGISTRY.get_definition(key)
        except KeyError:
            continue
        primary = definition.aliases[0] if definition.aliases else None
        if not primary:
            continue
        primary_norm = _normalize(primary)
        for col in excel_columns:
            if col in result:
                continue
            if _normalize(col) == primary_norm:
                result[col] = primary
                break
            for alias in definition.aliases[1:]:
                if _normalize(alias) == _normalize(col):
                    result[col] = primary
                    break
    return result


def resolve_status_location_column(df: pd.DataFrame) -> str | None:
    """Status_Location 컬럼(또는 alias) 반환. 없으면 None."""
    if "Status_Location" in df.columns:
        return "Status_Location"
    for c in df.columns:
        if _normalize(c) == _normalize("Status_Location"):
            return c
    return None


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Apply HVDC Flow Code to a single sheet in an Excel file."
    )
    parser.add_argument(
        "excel_path",
        type=Path,
        help="Path to Excel file (e.g. docs/HVDC STATUS1.xlsx)",
    )
    parser.add_argument(
        "sheet_name",
        nargs="?",
        default="hvdc all status",
        help="Sheet name (default: hvdc all status)",
    )
    parser.add_argument(
        "--header-row",
        type=int,
        default=0,
        help="Row index for column headers (default: 0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done, do not write file.",
    )
    args = parser.parse_args()

    path = args.excel_path.resolve()
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    with pd.ExcelFile(path, engine="openpyxl") as xl:
        sheet_names_before = xl.sheet_names
    target_sheet = find_sheet_by_name(sheet_names_before, args.sheet_name)
    if target_sheet is None:
        print(f"[ERROR] Sheet not found: {args.sheet_name}")
        print(f"  Available sheets: {sheet_names_before}")
        sys.exit(1)

    print(f"  Reading sheet: '{target_sheet}' from {path.name} (header row={args.header_row})")
    df = pd.read_excel(path, sheet_name=target_sheet, header=args.header_row, engine="openpyxl")
    warehouse_columns = get_warehouse_columns()
    site_columns = get_site_columns()

    # Excel 컬럼명 -> primary alias 매핑 (레지스트리 alias 매칭)
    excel_to_primary = build_excel_to_primary_map(df.columns.tolist())
    status_col = resolve_status_location_column(df)
    if status_col and status_col != "Status_Location":
        excel_to_primary[status_col] = "Status_Location"
    if excel_to_primary:
        df_work = df.rename(columns=excel_to_primary)
    else:
        df_work = df.copy()

    status_location_derived = False
    if "Status_Location" not in df_work.columns:
        df_work = derive_status_location(df_work, warehouse_columns, site_columns)
        status_location_derived = True
        print("  [INFO] Status_Location derived from latest WH/Site dates.")

    missing = [c for c in ["Status_Location"] + warehouse_columns + site_columns if c not in df_work.columns]
    if missing:
        print(f"  [WARN] Missing columns (flow logic may use defaults): {missing[:10]}{'...' if len(missing) > 10 else ''}")

    df_out = apply_flow_code_to_dataframe(df_work, warehouse_columns, site_columns)
    dist = df_out["FLOW_CODE"].value_counts().sort_index()
    print(f"  FLOW_CODE distribution: {dict(dist)}")

    if args.dry_run:
        print("  [DRY-RUN] Skip writing.")
        return

    # 파생한 Status_Location은 Excel에 쓰지 않음
    if status_location_derived and "Status_Location" in df_out.columns:
        df_out = df_out.drop(columns=["Status_Location"])

    # 원본 컬럼명으로 복원 (FLOW_CODE, FLOW_DESCRIPTION는 유지)
    primary_to_excel = {v: k for k, v in excel_to_primary.items()}
    df_final = df_out.rename(columns=primary_to_excel)

    # 다른 시트는 그대로 두고 대상 시트만 덮어쓰기 (mode="a" + if_sheet_exists="replace")
    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_final.to_excel(writer, sheet_name=target_sheet, index=False)
    print(f"  Written: {path} (sheet '{target_sheet}' updated with FLOW_CODE, FLOW_DESCRIPTION).")

    # 저장 후 시트 개수/이름 검증
    with pd.ExcelFile(path, engine="openpyxl") as xl:
        sheet_names_after = xl.sheet_names
    if sheet_names_before != sheet_names_after:
        print(f"  [WARN] Sheet list changed after write: before {len(sheet_names_before)}, after {len(sheet_names_after)}")
        print(f"    Before: {sheet_names_before}")
        print(f"    After:  {sheet_names_after}")
    else:
        print(f"  Verified: {len(sheet_names_after)} sheets unchanged.")


if __name__ == "__main__":
    main()
