# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from core.header_registry import HVDC_HEADER_REGISTRY
from core.header_normalizer import HeaderNormalizer

# ------------------------------- Normalization Utils -------------------------------

_WAREHOUSE_KEYS: Tuple[str, ...] = (
    "dhl_wh",
    "dsv_indoor",
    "dsv_al_markaz",
    "dsv_outdoor",
    "dsv_mzp",
    "jdn_mzd",
    "hauler_indoor",
    "aaa_storage",
    "mosb",
)
SITES = {"AGI", "DAS", "MIR", "SHU"}

def _warehouse_labels() -> List[str]:
    reg = HVDC_HEADER_REGISTRY
    return [reg.get_definition(k).description for k in _WAREHOUSE_KEYS]

WAREHOUSES = set(_warehouse_labels())

def _canon_map() -> Dict[str, str]:
    n = HeaderNormalizer()
    m: Dict[str, str] = {}
    for lab in WAREHOUSES | SITES:
        m[n.normalize(lab)] = lab
    return m

def _canon(v: object, amap: Dict[str, str], n=HeaderNormalizer()) -> Optional[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return amap.get(n.normalize(s))

def _stage_of(loc: Optional[str]) -> str:
    if not loc:
        return "shipping"
    if loc in WAREHOUSES:
        return "warehouse"
    if loc in SITES:
        return "site"
    lo = loc.lower()
    if ("pre" in lo and "arrival" in lo) or "eta" in lo or "etd" in lo:
        return "pre_arrival"
    return "shipping"

STAGE_PRIO = {"pre_arrival": 0, "shipping": 1, "warehouse": 2, "site": 3}
WH_PRIO = {
    "DSV Al Markaz": 10,
    "DSV Indoor": 20,
    "DSV Outdoor": 30,
    "AAA Storage": 40,
    "Hauler Indoor": 50,
    "DSV MZP": 60,
    "JDN MZD": 70,
    "MOSB": 80,
    "DHL WH": 90,
}

# ------------------------------- Event Model -------------------------------

@dataclass
class Event:
    case: str
    ym: str
    kind: str  # "IN" | "OUT"
    warehouse: str
    qty: int
    ts: pd.Timestamp
    src: Optional[str] = None
    dst: Optional[str] = None

# ------------------------- Timezone & Month Bucket Helpers ----------------------------

DUBAI_TZ = "Asia/Dubai"

def _to_dubai_aware(ts: pd.Series) -> pd.Series:
    """Convert timestamps to Dubai timezone-aware."""
    s = pd.to_datetime(ts, errors="coerce")
    if getattr(s.dt, "tz", None) is None:
        s = s.dt.tz_localize("Asia/Dubai")
    else:
        s = s.dt.tz_convert("Asia/Dubai")
    return s

def _to_ym_dubai(ts: pd.Series) -> pd.Series:
    """Convert timestamps to Dubai timezone-aware and extract year-month."""
    return _to_dubai_aware(ts).dt.strftime("%Y-%m")

# --------------------------- Main: Ledger Generation --------------------------------

def build_flow_ledger(
    master_df: pd.DataFrame,
    case_cols=("Case No", "Case", "Case_ID", "Case_Number", "case_no", "case"),
    qty_cols=("Pkg", "pkg", "Pkg_Quantity", "pkg_quantity", "quantity", "qty"),
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if master_df is None or master_df.empty:
        cols = ["Year_Month", "Warehouse", "Kind", "Qty"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["case", "ts", "src", "dst", "qty"])

    df = master_df.copy()

    def_pick(cands):
        cc = {c.lower().replace(" ", "_") for c in cands}
        for c in df.columns:
            if c.lower().replace(" ", "_") in cc:
                return c
        return None

    col_case = _pick(case_cols) or "row_id"
    if col_case not in df.columns:
        df[col_case] = df.index

    col_qty = _pick(qty_cols)
    if not col_qty:
        col_qty = "__qty__"
        df[col_qty] = 1

    amap = _canon_map()

    # 1) Melt warehouse/site datetime columns to long format
    loc_cols = [c for c in df.columns if _canon(c, amap) in (WAREHOUSES | SITES)]
    long = (
        df[[col_case, col_qty] + loc_cols]
        .melt(id_vars=[col_case, col_qty], var_name="loc", value_name="ts")
        .dropna(subset=["ts"])
        .copy()
    )

    # 2) 두바이 기준 시간/월버킷
    long["ts"] = _to_dubai_aware(long["ts"])
    long["Year_Month"] = long["ts"].dt.strftime("%Y-%m")

    # 3) 정규화/정렬 키
    long["loc"] = long["loc"].map(lambda s: _canon(s, amap))
    long["stage"] = long["loc"].map(_stage_of)
    long["stage_prio"] = long["stage"].map(STAGE_PRIO)
    long["wh_prio"] = long["loc"].map(lambda s: WH_PRIO.get(s, 999))
    long["qty"] = long[col_qty].astype("float").fillna(0).astype(int)
    long = long[long["qty"] > 0]

    # 4) Same-timestamp handling: sum same warehouse, preserve WH↔Site path transitions
    same_wh = (
        long.groupby([col_case, "ts", "loc", "stage", "stage_prio", "wh_prio"], as_index=False)["qty"]
            .sum()
            .sort_values([col_case, "ts", "stage_prio", "wh_prio"])
    )

    events: List[Event] = []
    edges: List[Tuple[str, pd.Timestamp, Optional[str], Optional[str], int]] = []
    final_rows: List[Tuple[str, pd.Timestamp, str, int]] = []

    # (a) Same-timestamp chain transitions: interpret path as adjacent pairs A→B
    for case, gts in same_wh.groupby(col_case, sort=False):
        for ts, one_ts in gts.groupby("ts", sort=False):
            one_ts = one_ts.sort_values(["stage_prio", "wh_prio"])
            path = [r.loc for r in one_ts.itertuples()]

    if len(path) >= 2:
                # 수정: path가 warehouse로 시작하고 non-warehouse (e.g., site)를 포함하면, 첫 warehouse에 대한 implicit IN from shipping 추가
                if path[0] in WAREHOUSES and any(p not in WAREHOUSES for p in path):
                    qty_first = int(one_ts.loc[one_ts["loc"] == path[0], "qty"].iloc[0])
                    ym = ts.strftime("%Y-%m")
                    events.append(Event(str(case), ym, "IN", path[0], qty_first, ts, src="shipping", dst=path[0]))
                    logger.debug(f"Added implicit IN for case {case} at ts {ts} to {path[0]} from shipping")

    for a, b in zip(path[:-1], path[1:]):
                    if a == b:
                        continue
                    qty_a = int(one_ts.loc[one_ts["loc"] == a, "qty"].iloc[0])
                    ym = ts.strftime("%Y-%m")
                    if a in WAREHOUSES and b in WAREHOUSES:
                        edges.append((str(case), ts, a, b, qty_a))
                        events.append(Event(str(case), ym, "OUT", a, qty_a, ts, src=a, dst=b))
                        events.append(Event(str(case), ym, "IN",  b, qty_a, ts, src=a, dst=b))
                    elif a in WAREHOUSES and b not in WAREHOUSES:
                        events.append(Event(str(case), ym, "OUT", a, qty_a, ts, src=a, dst=b))
                    elif a not in WAREHOUSES and b in WAREHOUSES:
                        events.append(Event(str(case), ym, "IN",  b, qty_a, ts, src=a, dst=b))

    # (b) Store final state only if it is a warehouse (ignore if ends with site, as stock is out)
            if path and path[-1] in WAREHOUSES:
                last_loc = path[-1]
                qty_last = int(one_ts.loc[one_ts["loc"] == last_loc, "qty"].iloc[0])
                final_rows.append((str(case), ts, last_loc, qty_last))

    # (c) Cross-timestamp transitions: use only final states, prevent duplicate transitions
    if final_rows:
        fr = (
            pd.DataFrame(final_rows, columns=[col_case, "ts", "loc", "qty"])
              .sort_values([col_case, "ts"])
        )
        for case, g in fr.groupby(col_case, sort=False):
            prev_loc = None
            for r in g.itertuples(index=False):
                loc, ts, qty = r.loc, r.ts, int(r.qty)
                ym = ts.strftime("%Y-%m")
                if prev_loc is None:
                    if loc in WAREHOUSES:
                        events.append(Event(str(case), ym, "IN", loc, qty, ts, src=None, dst=loc))
                else:
                    if prev_loc != loc:
                        if prev_loc in WAREHOUSES and loc in WAREHOUSES:
                            edges.append((str(case), ts, prev_loc, loc, qty))
                            events.append(Event(str(case), ym, "OUT", prev_loc, qty, ts, src=prev_loc, dst=loc))
                            events.append(Event(str(case), ym, "IN",  loc,      qty, ts, src=prev_loc, dst=loc))
                        elif prev_loc in WAREHOUSES and loc not in WAREHOUSES:
                            events.append(Event(str(case), ym, "OUT", prev_loc, qty, ts, src=prev_loc, dst=loc))
                        elif prev_loc not in WAREHOUSES and loc in WAREHOUSES:
                            events.append(Event(str(case), ym, "IN",  loc,      qty, ts, src=prev_loc, dst=loc))
                prev_loc = loc

    # 5) Monthly warehouse IN/OUT aggregation
    if not events:
        cols = ["Year_Month", "Warehouse", "Kind", "Qty"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["case", "ts", "src", "dst", "qty"])

    ev = pd.DataFrame([e.__dict__ for e in events])
    ledger = (
        ev.groupby(["ym", "warehouse", "kind"], as_index=False)["qty"]
        .sum()
        .rename(
            columns={"ym": "Year_Month", "warehouse": "Warehouse", "kind": "Kind", "qty": "Qty"}
        )
    )
    edges_df = pd.DataFrame(edges, columns=["case", "ts", "src", "dst", "qty"]).sort_values(
        ["case", "ts"]
    )

    return ledger, edges_df

# --------------------------- Monthly Table + Cumulative (cumsum) ---------------------------

def monthly_inout_table(
    ledger: pd.DataFrame, warehouses: Optional[List[str]] = None
) -> pd.DataFrame:
    if ledger is None or ledger.empty:
        return pd.DataFrame(columns=["입고월"])
    warehouses = warehouses or _warehouse_labels()

    piv = ledger.pivot_table(
        index="Year_Month",
        columns=["Warehouse", "Kind"],
        values="Qty",
        aggfunc="sum",
        fill_value=0,
        sort=True,
    ).sort_index()
    out = pd.DataFrame({"입고월": piv.index})
    for w in warehouses:
        ins = piv.get((w, "IN"), pd.Series(0, index=piv.index))
        outs = piv.get((w, "OUT"), pd.Series(0, index=piv.index))
        out[f"입고_{w}"] = ins.astype(int).values
        out[f"출고_{w}"] = outs.astype(int).values
        out[f"누적_{w}"] = (ins - outs).cumsum().astype(int).values
    return out.reset_index(drop=True)

# ------------------------------- Sanity Report --------------------------------

def sanity_report(df_monthly: pd.DataFrame) -> List[Tuple[str, int, int, int, int]]:
    bad = []
    for w in sorted({c.split("_", 1)[1] for c in df_monthly.columns if c.startswith("입고_")}):
        total_in = int(df_monthly[f"입고_{w}"].sum())
        total_out = int(df_monthly[f"출고_{w}"].sum())
        last_bal = int(df_monthly[f"누적_{w}"].iloc[-1]) if len(df_monthly) else 0
        diff = total_in - total_out
        if diff != last_bal:
            bad.append((w, total_in, total_out, last_bal, diff))
            logger.warning(f"Sanity 실패: {w} - 총입고({total_in}) - 총출고({total_out}) = {diff} != 마지막 누적({last_bal})")
        else:
            logger.info(f"Sanity 성공: {w} - 일치")
    return bad다시 확인하라
