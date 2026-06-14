from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# =========================
# 설정
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_XLSX = PROJECT_ROOT / "docs" / "HVDC STATUS1.xlsx"
DEFAULT_SHEET_NAME = "hvdc all status"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "map_json"

SITE_DOC_COLS = {
    "SHU": "DOC_SHU",
    "DAS": "DOC_DAS",
    "MIR": "DOC_MIR",
    "AGI": "DOC_AGI",
}

SITE_ACTUAL_COLS = {
    "SHU": "SHU",
    "MIR": "MIR",
    "DAS": "DAS",
    "AGI": "AGI",
}

WAREHOUSE_COLS = {
    "DSV Indoor": "wh:dsv_indoor",
    "DSV Outdoor": "wh:dsv_outdoor",
    "DSV MZD": "wh:dsv_mzd",
    "DSV Kizad": "wh:dsv_kizad",
    "JDN MZD": "wh:jdn_mzd",
    "JDN Waterfront": "wh:jdn_waterfront",
    "AAA Storage": "wh:aaa_storage",
    "ZENER (WH)": "wh:zener_wh",
    "Hauler DG Storage": "wh:hauler_dg_storage",
    "Vijay Tanks": "wh:vijay_tanks",
}

MOSB_COL = "MOSB"

NUMERIC_COLS = [
    "CIF VALUE (A+B+C)",
    "GWT (KG)",
    "CBM",
    "QTY OF CNTR",
]

DATE_COLS = [
    "ETD",
    "ATD",
    "ETA",
    "ATA",
    "Attestation Date",
    "DO Collection",
    "Customs Start",
    "Customs Close",
    "SHU",
    "MIR",
    "DAS",
    "AGI",
    "DSV Indoor",
    "DSV Outdoor",
    "DSV MZD",
    "DSV Kizad",
    "JDN MZD",
    "JDN Waterfront",
    "MOSB",
    "AAA Storage",
    "ZENER (WH)",
    "Hauler DG Storage",
    "Vijay Tanks",
    "FINAL DELIVERY",
]

REQUIRED_INPUT_COLS = sorted(
    {
        "SCT SHIP NO.",
        "MR#",
        "VENDOR",
        "CATEGORY",
        "COE",
        "POL",
        "POD",
        "SHIP MODE",
        "ETD",
        "ATD",
        "ETA",
        "ATA",
        "Customs Start",
        "Customs Close",
        "Custom Code",
        "FINAL DELIVERY",
        "CIF VALUE (A+B+C)",
        "GWT (KG)",
        "CBM",
        "QTY OF CNTR",
    }
)

POD_NODE_MAP = {
    "khalifa": "port:khalifa",
    "mina zayed": "port:mina_zayed",
    "jebel ali": "port:jebel_ali",
    "abu dhabi airport": "airport:auh",
    "auh": "airport:auh",
}

CUSTOMS_NODE_MAP = {
    "khalifa": "customs:khalifa",
    "mina zayed": "customs:mina_zayed",
    "jebel ali": "customs:jebel_ali",
    "abu dhabi airport": "customs:auh",
    "auh": "customs:auh",
}

POD_ALIAS_FOR_DISPLAY = {
    "port:khalifa": "Khalifa Port",
    "port:mina_zayed": "Mina Zayed",
    "port:jebel_ali": "Jebel Ali",
    "airport:auh": "Abu Dhabi Airport",
}

CUSTOMS_ALIAS_FOR_DISPLAY = {
    "customs:khalifa": "Khalifa Customs",
    "customs:mina_zayed": "Mina Zayed Customs",
    "customs:jebel_ali": "Jebel Ali Customs",
    "customs:auh": "AUH Customs",
}

SITE_NODE_LABEL = {
    "site:SHU": "SHU",
    "site:MIR": "MIR",
    "site:DAS": "DAS",
    "site:AGI": "AGI",
}

UAE_STATIC_NODE_REGISTRY = {
    "port:khalifa": {"id": "port:khalifa", "type": "port", "name": "Khalifa Port"},
    "port:mina_zayed": {"id": "port:mina_zayed", "type": "port", "name": "Mina Zayed"},
    "port:jebel_ali": {"id": "port:jebel_ali", "type": "port", "name": "Jebel Ali"},
    "airport:auh": {"id": "airport:auh", "type": "airport", "name": "Abu Dhabi Airport"},
    "customs:khalifa": {"id": "customs:khalifa", "type": "customs", "name": "Khalifa Customs"},
    "customs:mina_zayed": {"id": "customs:mina_zayed", "type": "customs", "name": "Mina Zayed Customs"},
    "customs:jebel_ali": {"id": "customs:jebel_ali", "type": "customs", "name": "Jebel Ali Customs"},
    "customs:auh": {"id": "customs:auh", "type": "customs", "name": "AUH Customs"},
    "mosb:mosb": {"id": "mosb:mosb", "type": "mosb", "name": "MOSB"},
    "site:SHU": {"id": "site:SHU", "type": "site", "name": "SHU"},
    "site:MIR": {"id": "site:MIR", "type": "site", "name": "MIR"},
    "site:DAS": {"id": "site:DAS", "type": "site", "name": "DAS"},
    "site:AGI": {"id": "site:AGI", "type": "site", "name": "AGI"},
    **{
        node_id: {"id": node_id, "type": "warehouse", "name": col_name}
        for col_name, node_id in WAREHOUSE_COLS.items()
    },
}


# =========================
# 유틸
# =========================

def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def slugify(value: str) -> str:
    value = normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def has_marker(value: Any) -> bool:
    """
    DOC_* 컬럼용.
    'O', 'o', 'x', 숫자, 날짜, 기타 문자열 모두 non-empty면 True 처리.
    """
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if isinstance(value, pd.Timestamp):
        return True
    text = str(value).strip()
    return text != ""


def valid_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        ts = pd.to_datetime(value, errors="coerce")
    except Exception:
        return None
    if pd.isna(ts):
        return None
    # 가정: 2000년 이전 날짜는 placeholder/오류 가능성이 커서 버림
    if ts.year < 2000:
        return None
    return ts.strftime("%Y-%m-%d")


def safe_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float) and math.isnan(value):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def map_pod_to_entry_node(pod: str) -> str:
    pod_l = normalize_text(pod).lower()
    for key, node_id in POD_NODE_MAP.items():
        if key in pod_l:
            return node_id
    return f"port:{slugify(pod_l)}"


def map_pod_to_customs_node(pod: str) -> str:
    pod_l = normalize_text(pod).lower()
    for key, node_id in CUSTOMS_NODE_MAP.items():
        if key in pod_l:
            return node_id
    return f"customs:{slugify(pod_l)}"


def region_from_coe(coe: str) -> str:
    coe_u = normalize_text(coe).upper()
    europe = {
        "FRANCE", "GERMANY", "ITALY", "BELGIUM", "NETHERLANDS", "SPAIN",
        "SWEDEN", "DENMARK", "NORWAY", "UK", "UNITED KINGDOM", "POLAND",
        "FINLAND", "AUSTRIA", "CZECH", "SLOVAKIA",
    }
    east_asia = {
        "KOREA", "CHINA", "JAPAN", "TAIWAN", "THAILAND", "VIETNAM",
        "INDONESIA", "MALAYSIA", "SINGAPORE", "PHILIPPINES",
    }
    middle_east = {"UAE", "QATAR", "SAUDI ARABIA", "OMAN", "BAHRAIN", "KUWAIT"}
    americas = {"USA", "UNITED STATES", "CANADA", "MEXICO", "BRAZIL", "CHILE"}

    if coe_u in europe:
        return "Europe"
    if coe_u in east_asia:
        return "East / SE Asia"
    if coe_u in middle_east:
        return "Middle East"
    if coe_u in americas:
        return "Americas"
    return "Other"


def make_origin_region_node(coe: str) -> str:
    region = region_from_coe(coe)
    return f"origin_region:{slugify(region)}"


def make_origin_pol_node(pol: str, coe: str) -> str:
    return f"origin_pol:{slugify(coe)}:{slugify(pol)}"


def make_site_node(site_code: str) -> str:
    return f"site:{site_code}"


def choose_effective_sites(planned_sites: List[str], actual_sites: List[str]) -> List[str]:
    """
    actual이 있으면 actual 우선.
    actual이 없으면 planned 사용.
    """
    return actual_sites if actual_sites else planned_sites


def flow_code_from_sites_and_staging(
    final_site: Optional[str],
    wh_any: bool,
    mosb_any: bool,
) -> Optional[int]:
    if not final_site:
        return None

    if final_site in {"SHU", "MIR"}:
        return 2 if wh_any else 1

    if final_site in {"DAS", "AGI"}:
        # 규정상 AGI/DAS는 MOSB leg 필수
        return 4 if wh_any else 3

    return None


def status_from_row(
    ata: Optional[str],
    customs_start: Optional[str],
    customs_close: Optional[str],
    wh_visits: List[Dict[str, Any]],
    mosb_visit: Optional[str],
    actual_sites: List[str],
    final_delivery: Optional[str],
) -> str:
    if final_delivery:
        return "delivered"
    if actual_sites:
        return "at_site_pending_close"
    if mosb_visit:
        return "mosb_pending"
    if wh_visits:
        return "warehouse_staging"
    if customs_close:
        return "customs_cleared_pending_dispatch"
    if customs_start:
        return "customs_in_progress"
    if ata:
        return "arrived_pending_customs"
    return "in_transit"


def sort_visits_by_date(visits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key_fn(x: Dict[str, Any]) -> Tuple[int, str]:
        dt = x.get("date")
        return (0, dt) if dt else (1, "9999-12-31")
    return sorted(visits, key=key_fn)


def add_edge(
    edge_acc: Dict[Tuple[str, str, str], Dict[str, Any]],
    source: str,
    target: str,
    route_type: str,
    shipment_id: str,
    weight: float,
    cif_value: float,
    gross_weight_kg: float,
    flow_code: Optional[int],
):
    key = (source, target, route_type)
    if key not in edge_acc:
        edge_acc[key] = {
            "id": f"{source}__{target}",
            "source": source,
            "target": target,
            "route_type": route_type,
            "shipment_count": 0.0,
            "shipment_ids": [],
            "allocation_weight_sum": 0.0,
            "cif_value_sum": 0.0,
            "gross_weight_kg_sum": 0.0,
            "flow_codes": set(),
        }

    edge_acc[key]["shipment_count"] += weight
    edge_acc[key]["allocation_weight_sum"] += weight
    edge_acc[key]["cif_value_sum"] += cif_value * weight
    edge_acc[key]["gross_weight_kg_sum"] += gross_weight_kg * weight
    edge_acc[key]["shipment_ids"].append(shipment_id)
    if flow_code is not None:
        edge_acc[key]["flow_codes"].add(flow_code)


def add_node(
    node_acc: Dict[str, Dict[str, Any]],
    node_id: str,
    node_type: str,
    name: str,
):
    if node_id not in node_acc:
        node_acc[node_id] = {
            "id": node_id,
            "type": node_type,
            "name": name,
        }


def normalize_lookup_key(value: Any) -> str:
    return re.sub(r"[\s_-]+", "", normalize_text(value).lower())


def resolve_sheet_name(sheet_names: List[str], target_sheet: str) -> Optional[str]:
    target_norm = normalize_lookup_key(target_sheet)
    for sheet_name in sheet_names:
        if normalize_lookup_key(sheet_name) == target_norm:
            return sheet_name
    return None


def load_input_dataframe(
    excel_path: Path,
    sheet_name: str,
    header_row: int,
) -> Tuple[pd.DataFrame, Path, str]:
    resolved_path = excel_path.resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Excel file not found: {resolved_path}")

    with pd.ExcelFile(resolved_path, engine="openpyxl") as xl:
        actual_sheet_name = resolve_sheet_name(xl.sheet_names, sheet_name)
        if actual_sheet_name is None:
            raise ValueError(
                f"Sheet '{sheet_name}' not found in {resolved_path.name}. "
                f"Available sheets: {xl.sheet_names}"
            )

    df = pd.read_excel(
        resolved_path,
        sheet_name=actual_sheet_name,
        header=header_row,
        engine="openpyxl",
    )
    return df, resolved_path, actual_sheet_name


def validate_required_columns(df: pd.DataFrame) -> None:
    missing_cols = [col for col in REQUIRED_INPUT_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in DATE_COLS:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")

    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def build_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build shipment path and graph JSON from HVDC status Excel."
    )
    parser.add_argument(
        "excel_path",
        nargs="?",
        type=Path,
        default=DEFAULT_INPUT_XLSX,
        help=f"Input Excel path (default: {DEFAULT_INPUT_XLSX})",
    )
    parser.add_argument(
        "sheet_name",
        nargs="?",
        default=DEFAULT_SHEET_NAME,
        help=f"Sheet name to read (default: {DEFAULT_SHEET_NAME})",
    )
    parser.add_argument(
        "--header-row",
        type=int,
        default=0,
        help="Header row index for the selected sheet (default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for generated JSON files (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args()


def write_outputs(
    output_dir: Path,
    meta: Dict[str, Any],
    shipment_paths: List[Dict[str, Any]],
    graphs: Dict[str, Any],
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    shipment_file = output_dir / "shipment_paths.json"
    global_file = output_dir / "global_graph.json"
    uae_file = output_dir / "uae_ops_graph.json"

    shipment_payload = {
        "meta": meta,
        "shipments": shipment_paths,
    }

    shipment_file.write_text(
        json.dumps(shipment_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    global_file.write_text(
        json.dumps({"meta": meta, **graphs["global_graph"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    uae_file.write_text(
        json.dumps({"meta": meta, **graphs["uae_ops_graph"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "shipment_file": shipment_file,
        "global_file": global_file,
        "uae_file": uae_file,
    }


# =========================
# 핵심 변환
# =========================

def build_paths_for_row(row: pd.Series) -> Dict[str, Any]:
    shipment_id = normalize_text(row["SCT SHIP NO."])
    coe = normalize_text(row["COE"])
    pol = normalize_text(row["POL"])
    pod = normalize_text(row["POD"])
    ship_mode = normalize_text(row["SHIP MODE"])

    ata = valid_date(row["ATA"])
    customs_start = valid_date(row["Customs Start"])
    customs_close = valid_date(row["Customs Close"])
    final_delivery = valid_date(row["FINAL DELIVERY"])

    planned_sites = [
        site
        for site, col in SITE_DOC_COLS.items()
        if has_marker(row.get(col))
    ]

    actual_site_visits = {
        site: valid_date(row.get(col))
        for site, col in SITE_ACTUAL_COLS.items()
    }
    actual_sites = [site for site, dt in actual_site_visits.items() if dt]

    wh_visits = []
    for col_name, node_ref in WAREHOUSE_COLS.items():
        dt = valid_date(row.get(col_name))
        if dt:
            wh_visits.append(
                {
                    "column": col_name,
                    "node_ref": node_ref,
                    "date": dt,
                }
            )
    wh_visits = sort_visits_by_date(wh_visits)

    mosb_visit = valid_date(row.get(MOSB_COL))

    effective_sites = choose_effective_sites(planned_sites, actual_sites)
    wh_any = len(wh_visits) > 0
    mosb_any = mosb_visit is not None or any(s in {"DAS", "AGI"} for s in effective_sites)

    flow_code_planned = None
    if planned_sites:
        # multi-site일 경우 site별 별도 graph path를 만들고 row 대표값은 None 또는 list로 둠
        if len(planned_sites) == 1:
            flow_code_planned = flow_code_from_sites_and_staging(planned_sites[0], wh_any, mosb_any)

    flow_code_actual = None
    if actual_sites:
        if len(actual_sites) == 1:
            flow_code_actual = flow_code_from_sites_and_staging(actual_sites[0], wh_any, mosb_any)

    entry_node_ref = map_pod_to_entry_node(pod)
    customs_node_ref = map_pod_to_customs_node(pod)

    # ---------- Global paths ----------
    global_paths = []
    origin_region_ref = make_origin_region_node(coe)
    origin_pol_ref = make_origin_pol_node(pol, coe)

    for site in effective_sites or [None]:
        path = [origin_region_ref, origin_pol_ref, entry_node_ref]
        if site:
            path.append(make_site_node(site))
        global_paths.append(path)

    # ---------- UAE Ops paths ----------
    uae_ops_paths = []

    if effective_sites:
        for site in effective_sites:
            path = [entry_node_ref]

            # customs는 UAE Ops에서 항상 논리 노드로 유지
            path.append(customs_node_ref)

            if wh_visits:
                for wh in wh_visits:
                    path.append(wh["node_ref"])

            requires_mosb = site in {"DAS", "AGI"}
            if mosb_visit or requires_mosb:
                path.append("mosb:mosb")

            # actual 도착이 없고 아직 중간단계면 site 종착을 넣되 상태에서 pending 처리
            path.append(make_site_node(site))
            uae_ops_paths.append(path)
    else:
        # planned/actual site 둘 다 없을 경우 현재 단계까지만 표시
        path = [entry_node_ref]
        if customs_start or customs_close:
            path.append(customs_node_ref)
        if wh_visits:
            for wh in wh_visits:
                path.append(wh["node_ref"])
        if mosb_visit:
            path.append("mosb:mosb")
        uae_ops_paths.append(path)

    status = status_from_row(
        ata=ata,
        customs_start=customs_start,
        customs_close=customs_close,
        wh_visits=wh_visits,
        mosb_visit=mosb_visit,
        actual_sites=actual_sites,
        final_delivery=final_delivery,
    )

    return {
        "shipment_id": shipment_id,
        "mr_no": normalize_text(row["MR#"]),
        "vendor": normalize_text(row["VENDOR"]),
        "category": normalize_text(row["CATEGORY"]),
        "coe": coe,
        "origin_region": region_from_coe(coe),
        "pol": pol,
        "pod": pod,
        "ship_mode": ship_mode,
        "etd": valid_date(row["ETD"]),
        "atd": valid_date(row["ATD"]),
        "eta": valid_date(row["ETA"]),
        "ata": ata,
        "customs_start": customs_start,
        "customs_close": customs_close,
        "custom_code": normalize_text(row["Custom Code"]),
        "planned_sites": planned_sites,
        "actual_sites": actual_sites,
        "actual_site_dates": actual_site_visits,
        "warehouse_visits": wh_visits,
        "mosb_visit": mosb_visit,
        "final_delivery": final_delivery,
        "entry_node_ref": entry_node_ref,
        "customs_node_ref": customs_node_ref,
        "global_paths": global_paths,
        "uae_ops_paths": uae_ops_paths,
        "flow_code_planned": flow_code_planned,
        "flow_code_actual": flow_code_actual,
        "status": status,
        "metrics": {
            "cif_value": safe_number(row["CIF VALUE (A+B+C)"]),
            "gross_weight_kg": safe_number(row["GWT (KG)"]),
            "cbm": safe_number(row["CBM"]),
            "qty_of_container": safe_number(row["QTY OF CNTR"]),
        },
        "flags": {
            "wh_any": wh_any,
            "mosb_required": any(s in {"DAS", "AGI"} for s in effective_sites),
            "mosb_any": mosb_any,
            "multi_planned_site": len(planned_sites) > 1,
            "multi_actual_site": len(actual_sites) > 1,
        },
    }


# =========================
# Graph aggregate
# =========================

def build_graphs(shipment_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
    global_nodes: Dict[str, Dict[str, Any]] = {}
    global_edges: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    uae_nodes: Dict[str, Dict[str, Any]] = {**UAE_STATIC_NODE_REGISTRY}
    uae_edges: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    # Origin node registry는 동적으로 추가
    for shipment in shipment_paths:
        shipment_id = shipment["shipment_id"]
        cif_value = shipment["metrics"]["cif_value"]
        gross_weight_kg = shipment["metrics"]["gross_weight_kg"]

        # -------- Global --------
        global_path_list = shipment["global_paths"]
        global_path_weight = 1.0 / max(len(global_path_list), 1)

        for path in global_path_list:
            # 노드 추가
            for node_ref in path:
                if node_ref.startswith("origin_region:"):
                    add_node(global_nodes, node_ref, "origin_region", node_ref.split(":", 1)[1].replace("_", " ").title())
                elif node_ref.startswith("origin_pol:"):
                    add_node(global_nodes, node_ref, "origin_pol", node_ref.split(":", 2)[-1].replace("_", " ").title())
                elif node_ref in SITE_NODE_LABEL:
                    add_node(global_nodes, node_ref, "site", SITE_NODE_LABEL[node_ref])
                elif node_ref in UAE_STATIC_NODE_REGISTRY:
                    node_meta = UAE_STATIC_NODE_REGISTRY[node_ref]
                    add_node(global_nodes, node_ref, node_meta["type"], node_meta["name"])
                else:
                    add_node(global_nodes, node_ref, "unknown", node_ref)

            # edge 추가
            for src, tgt in zip(path[:-1], path[1:]):
                if src.startswith("origin_region:") and tgt.startswith("origin_pol:"):
                    route_type = "origin_region_to_pol"
                elif src.startswith("origin_pol:") and (tgt.startswith("port:") or tgt.startswith("airport:")):
                    route_type = "pol_to_pod"
                elif (src.startswith("port:") or src.startswith("airport:")) and tgt.startswith("site:"):
                    route_type = "pod_to_site"
                else:
                    route_type = "global_path"

                add_edge(
                    global_edges,
                    src,
                    tgt,
                    route_type,
                    shipment_id,
                    global_path_weight,
                    cif_value,
                    gross_weight_kg,
                    shipment["flow_code_planned"] or shipment["flow_code_actual"],
                )

        # -------- UAE Ops --------
        uae_path_list = shipment["uae_ops_paths"]
        uae_path_weight = 1.0 / max(len(uae_path_list), 1)

        for path in uae_path_list:
            for node_ref in path:
                if node_ref not in uae_nodes:
                    if node_ref.startswith("site:"):
                        add_node(uae_nodes, node_ref, "site", node_ref.split(":")[-1])
                    else:
                        add_node(uae_nodes, node_ref, "derived", node_ref)

            for src, tgt in zip(path[:-1], path[1:]):
                if src.startswith("port:") or src.startswith("airport:"):
                    if tgt.startswith("customs:"):
                        route_type = "port_to_customs"
                    else:
                        route_type = "port_outbound"
                elif src.startswith("customs:") and tgt.startswith("wh:"):
                    route_type = "customs_to_wh"
                elif src.startswith("customs:") and tgt.startswith("site:"):
                    route_type = "customs_to_site"
                elif src.startswith("wh:") and tgt == "mosb:mosb":
                    route_type = "wh_to_mosb"
                elif src.startswith("wh:") and tgt.startswith("site:"):
                    route_type = "wh_to_site"
                elif src == "mosb:mosb" and tgt.startswith("site:"):
                    route_type = "mosb_to_site"
                else:
                    route_type = "uae_ops_path"

                add_edge(
                    uae_edges,
                    src,
                    tgt,
                    route_type,
                    shipment_id,
                    uae_path_weight,
                    cif_value,
                    gross_weight_kg,
                    shipment["flow_code_actual"] or shipment["flow_code_planned"],
                )

    # set → sorted list
    for edge_dict in (global_edges, uae_edges):
        for item in edge_dict.values():
            item["flow_codes"] = sorted(item["flow_codes"])
            item["shipment_ids"] = sorted(set(item["shipment_ids"]))

    return {
        "global_graph": {
            "nodes": sorted(global_nodes.values(), key=lambda x: (x["type"], x["name"])),
            "edges": sorted(global_edges.values(), key=lambda x: (x["source"], x["target"])),
        },
        "uae_ops_graph": {
            "nodes": sorted(uae_nodes.values(), key=lambda x: (x["type"], x["name"])),
            "edges": sorted(uae_edges.values(), key=lambda x: (x["source"], x["target"])),
        },
    }


# =========================
# 실행
# =========================

def main() -> None:
    args = build_cli_args()
    df, input_path, actual_sheet_name = load_input_dataframe(
        args.excel_path,
        args.sheet_name,
        args.header_row,
    )
    validate_required_columns(df)
    df = preprocess_dataframe(df)

    # 날짜 컬럼 전처리

    # 숫자 컬럼 전처리

    shipment_paths: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        shipment_id = normalize_text(row.get("SCT SHIP NO."))
        if not shipment_id:
            continue
        shipment_paths.append(build_paths_for_row(row))

    graphs = build_graphs(shipment_paths)

    meta = {
        "source_file": str(input_path),
        "sheet_name": actual_sheet_name,
        "row_count": len(shipment_paths),
        "grain": "1 row = 1 shipment / 1 voyage case",
        "rules": {
            "global": "COE/POL/POD/DOC_* 중심",
            "uae_ops": "POD/Customs/WH/MOSB/SHU~AGI 중심",
            "planned_vs_actual": "DOC_* = 계획, SHU~AGI = 실제",
            "wh_role": "선택 staging",
            "mosb_role": "AGI/DAS 필수 경유 hub",
        },
        "assumptions": [
            "DOC_* 컬럼은 non-empty marker면 계획 site로 간주",
            "actual site는 SHU/MIR/DAS/AGI 날짜 존재 기준",
            "multi-site row는 graph aggregate 시 path를 복수 생성하고 allocation_weight를 1/n 분배",
            "2000년 이전 날짜는 placeholder/오류 가능성으로 무시",
            "POD→Customs 매핑은 문자열 alias 기반",
        ],
    }

    output_files = write_outputs(args.output_dir, meta, shipment_paths, graphs)

    # 파일 저장

    print(f"[OK] shipment paths -> {output_files['shipment_file']}")
    print(f"[OK] global graph   -> {output_files['global_file']}")
    print(f"[OK] uae ops graph  -> {output_files['uae_file']}")


if __name__ == "__main__":
    main()
