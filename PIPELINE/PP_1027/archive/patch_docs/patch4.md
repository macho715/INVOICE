좋아, “전이 우선순위 + 동일시각 병합”까지 들어간 **완전판 레저(ledger) 모듈**로 정리해 줄게.
핵심은 케이스별 **상태 타임라인 → 전이(transition)**를 정확히 재구성해서, 월별 입·출고·누적이 **자연스럽게 맞게** 만드는 것.

아래 그대로 추가하면 된다.

---

# 1) 새 모듈: `core/flow_ledger.py`

```python
# -*- coding: utf-8 -*-
"""
Warehouse Flow Ledger (canonical)
- 상태 타임라인 → 전이(transition) → 이벤트 레저(입고/출고/이동)
- 전이 우선순위 + 동일시각 병합 규칙 포함
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .header_registry import HVDC_HEADER_REGISTRY
from .header_normalizer import HeaderNormalizer

# ---- 창고 라벨/정규화 ---------------------------------------------------------

_WAREHOUSE_KEYS: Tuple[str, ...] = (
    "dhl_wh",
    "dsv_indoor",
    "dsv_al_markaz",
    "hauler_indoor",
    "dsv_outdoor",
    "dsv_mzp",
    "jdn_mzd",
    "aaa_storage",
    "mosb",
)

def _warehouse_labels() -> List[str]:
    reg = HVDC_HEADER_REGISTRY
    return [reg.get_definition(k).description for k in _WAREHOUSE_KEYS]

def _canon_map() -> Dict[str, str]:
    norm = HeaderNormalizer()
    amap = {}
    for label in _warehouse_labels():
        amap[norm.normalize(label)] = label
    # 사이트(현장) 라벨은 원본 그대로 사용(정규화만)
    for site in ("AGI","DAS","MIR","SHU"):
        amap[norm.normalize(site)] = site
    return amap

def _canon(value: object, amap: Dict[str, str], norm=HeaderNormalizer()) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return amap.get(norm.normalize(s))

# ---- 전이 우선순위(동일시각 정렬용) ------------------------------------------

# 위치 카테고리 → 타임라인 정렬 우선순위
# 낮을수록 먼저 처리(=이전 상태 취급)
STAGE_PRIO = {
    "pre_arrival": 0,
    "warehouse":   1,
    "site":        2,
    "shipping":    3,
}

# 창고 내부의 상대 우선순위(동일시각 WH↔WH 체인 정렬용)
WH_PRIO = {
    "DSV Al Markaz": 10,
    "DSV Indoor":    20,
    "DSV Outdoor":   30,
    "AAA Storage":   40,
    "Hauler Indoor": 50,
    "DSV MZP":       60,
    "JDN MZD":       70,
    "MOSB":          80,
    "DHL WH":        90,
}

WAREHOUSES = set(_warehouse_labels())
SITES = {"AGI","DAS","MIR","SHU"}

def _stage_of(loc: str) -> str:
    if not loc: return "shipping"
    if loc in WAREHOUSES: return "warehouse"
    if loc in SITES:      return "site"
    # 흔한 프리어라이벌 키워드(헤더/상태 텍스트 기반)
    lo = loc.lower()
    if "pre" in lo and "arrival" in lo: return "pre_arrival"
    if "eta" in lo or "etd" in lo:      return "pre_arrival"
    return "shipping"

# ---- 동등시각 병합 규칙 -------------------------------------------------------
# 규칙 요약
# 1) 같은 케이스, 같은 시각에 여러 상태가 있으면 (stage, warehouse 우선순위)로 정렬
# 2) 동일 시각의 WH들만 남겨 “연쇄 전이(WH→WH→WH…)”로 압축
# 3) 같은 WH가 연속으로 반복되면 1개로 축약(중복 제거)
# 4) WH→SITE/SHIPPING 전이는 “출고” 이벤트로 기록

@dataclass
class Event:
    case: str
    year_month: str
    kind: str          # "IN" | "OUT" | "MOVE"
    warehouse: str     # 대상 창고(입고/출고 기준)
    qty: int
    ts: pd.Timestamp
    src: Optional[str] = None
    dst: Optional[str] = None

def build_flow_ledger(master_df: pd.DataFrame,
                      case_col_candidates=("Case No","Case","Case_ID","Case_Number"),
                      qty_col_candidates=("Pkg","pkg","quantity","qty")) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    상태 타임라인 → 전이 레저 생성(전이 우선순위/동일시각 병합 포함)

    Returns:
      (ledger_df, edges_df)
      - ledger_df: Year_Month, Warehouse, Kind, Qty (월×창고×입/출 합계)
      - edges_df : 전이 상세(케이스별 from→to, ts, qty)
    """
    if master_df is None or master_df.empty:
        cols = ["Year_Month","Warehouse","Kind","Qty"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["case","ts","src","dst","qty"])

    df = master_df.copy()
    # 느슨한 컬럼 매핑
    def _pick(cands):
        for c in df.columns:
            key = c.lower().replace(" ","_")
            if key in {x.lower().replace(" ","_") for x in cands}:
                return c
        return None

    col_case = _pick(case_col_candidates) or "row_id"
    if col_case not in df.columns:
        df[col_case] = df.index

    col_qty  = _pick(qty_col_candidates)
    if not col_qty:
        df[col_qty := "__qty__"] = 1

    # 날짜/위치 후보: 창고+사이트 열만 사용
    amap = _canon_map()
    loc_cols = [c for c in df.columns if _canon(c, amap) in WAREHOUSES|SITES]
    # melt로 (case, loc, ts) 구성
    long = df[[col_case, col_qty] + loc_cols].melt(id_vars=[col_case, col_qty],
                                                   var_name="loc",
                                                   value_name="ts")
    long = long.dropna(subset=["ts"]).copy()
    long["ts"] = pd.to_datetime(long["ts"], errors="coerce")
    long = long.dropna(subset=["ts"])
    long["loc"] = long["loc"].map(lambda s: _canon(s, amap))
    long["stage"] = long["loc"].map(_stage_of)
    long["stage_prio"] = long["stage"].map(STAGE_PRIO)
    long["wh_prio"] = long["loc"].map(lambda s: WH_PRIO.get(s, 999))
    long["qty"] = long[col_qty].fillna(1).clip(lower=1).astype(int)

    # 케이스별 정렬(동일시각: stage→warehouse 우선순위)
    long = long.sort_values([col_case, "ts", "stage_prio", "wh_prio"]).reset_index(drop=True)

    # 동일시각 병합: 같은 케이스·같은 ts 묶어서 WH들만 남겨 체인 구성
    def collapse_same_timestamp(group: pd.DataFrame) -> List[Tuple[pd.Timestamp, List[str], int]]:
        out = []
        for ts, g in group.groupby("ts"):
            # 순서는 이미 stage→wh_prio로 정렬됨
            whs = [r.loc for r in g.itertuples() if r.loc in WAREHOUSES]
            qty = int(g["qty"].max())  # 보수적으로 최댓값(=PKG) 사용
            out.append((ts, whs, qty))
        return out

    events: List[Event] = []
    edges: List[Tuple[str, pd.Timestamp, Optional[str], Optional[str], int]] = []

    for case, g in long.groupby(col_case, sort=False):
        # ① 연속 중복 WH 제거용 버퍼
        timeline: List[Tuple[pd.Timestamp, str, int]] = []

        # 같은 케이스의 (ts → wh 리스트) 뽑기
        for ts, wh_list, qty in collapse_same_timestamp(g):
            if not wh_list:
                # WH가 없고 SITE/SHIPPING만 있는 경우: 이전 WH가 있었다면 OUT 처리 대상
                stage_row = g[g["ts"] == ts].iloc[0]
                timeline.append((ts, stage_row.loc, qty))  # 그대로 기록(비WH일 수도)
                continue

            # 동일시각 WH 체인 압축: wh_list 순서대로 연결 전이
            # 예: [AAA, DSV Indoor, DSV Al Markaz] → AAA→Indoor, Indoor→AlMarkaz
            prev = None
            for wh in wh_list:
                if prev is None:
                    timeline.append((ts, wh, qty))
                else:
                    edges.append((str(case), ts, prev, wh, qty))  # MOVE(WH→WH)
                prev = wh

        # ② 연속 동일 위치 축약(노이즈 제거)
        compact: List[Tuple[pd.Timestamp, str, int]] = []
        for ts, loc, qty in sorted(timeline, key=lambda x: (x[0], WH_PRIO.get(x[1], 999))):
            if compact and compact[-1][1] == loc and compact[-1][0] == ts:
                # 동일 시각 동일 위치 → 하나로
                compact[-1] = (ts, loc, max(compact[-1][2], qty))
            else:
                compact.append((ts, loc, qty))

        # ③ 전이 해석
        prev_loc: Optional[str] = None
        for ts, loc, qty in compact:
            ym = ts.strftime("%Y-%m")
            if prev_loc is None:
                # 비창고→창고 : IN
                if loc in WAREHOUSES:
                    events.append(Event(str(case), ym, "IN", loc, qty, ts, src=None, dst=loc))
            else:
                if prev_loc in WAREHOUSES and loc in WAREHOUSES and prev_loc != loc:
                    # WH→WH : MOVE + OUT/IN 동시 반영(집계는 OUT/IN으로 분해)
                    edges.append((str(case), ts, prev_loc, loc, qty))
                    events.append(Event(str(case), ym, "OUT", prev_loc, qty, ts, src=prev_loc, dst=loc))
                    events.append(Event(str(case), ym, "IN",  loc,      qty, ts, src=prev_loc, dst=loc))
                elif prev_loc in WAREHOUSES and loc in SITES:
                    # WH→SITE : OUT
                    events.append(Event(str(case), ym, "OUT", prev_loc, qty, ts, src=prev_loc, dst=loc))
                elif prev_loc not in WAREHOUSES and loc in WAREHOUSES:
                    # 비창고→창고 : IN
                    events.append(Event(str(case), ym, "IN", loc, qty, ts, src=prev_loc, dst=loc))
                # 그 외 조합은 이벤트 없음
            prev_loc = loc

    # ---- 레저 집계 ------------------------------------------
    if not events:
        cols = ["Year_Month","Warehouse","Kind","Qty"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["case","ts","src","dst","qty"])

    ev_df = pd.DataFrame([e.__dict__ for e in events])
    ledger = (
        ev_df.groupby(["year_month","warehouse","kind"], as_index=False)["qty"]
        .sum()
        .rename(columns={"year_month":"Year_Month","warehouse":"Warehouse","kind":"Kind","qty":"Qty"})
    )

    edges_df = pd.DataFrame(edges, columns=["case","ts","src","dst","qty"]).sort_values(["case","ts"])

    return ledger, edges_df

# ---- 월별 입/출고 표 + 누적(러닝밸런스) ---------------------------------------

def monthly_inout_table(ledger: pd.DataFrame, warehouses: Optional[List[str]] = None) -> pd.DataFrame:
    if ledger is None or ledger.empty:
        return pd.DataFrame(columns=["입고월"])

    warehouses = warehouses or _warehouse_labels()

    # 피벗
    piv = ledger.pivot_table(index="Year_Month", columns=["Warehouse","Kind"], values="Qty",
                             aggfunc="sum", fill_value=0).sort_index()

    # 출력 구성
    out = pd.DataFrame({"입고월": piv.index})

    for w in warehouses:
        in_s  = piv.get((w,"IN"),  pd.Series(0, index=piv.index))
        out_s = piv.get((w,"OUT"), pd.Series(0, index=piv.index))
        out[f"{w} (입고)"] = in_s.astype(int).values
        out[f"{w} (출고)"] = out_s.astype(int).values
        out[f"누적_{w}"]   = (in_s - out_s).cumsum().astype(int).values

    return out.reset_index(drop=True)
```

---

# 2) `report_generator.py`(또는 호출부) 통합

```python
# 1) 원본(마스터) 로드/정규화까지 끝난 뒤…
from core.flow_ledger import build_flow_ledger, monthly_inout_table, _warehouse_labels

master_df = self.combined_data  # 혹은 stats["processed_data"]
ledger_df, edges_df = build_flow_ledger(master_df)

# 필요시 전이 상세(edges_df)를 리콘 탭으로 저장해 진단에 활용
# edges_df.to_excel(writer, sheet_name="전이_상세", index=False)

# 2) 월별 입출고/누적 표 생성
warehouses = _warehouse_labels()
df_monthly = monthly_inout_table(ledger_df, warehouses)

# 3) '창고_월별_입출고' 시트에 df_monthly를 사용
```

---

# 3) 구현 포인트 정리(문제로 바로 이어진 부분)

* **동일시각 병합 규칙**

  * 같은 케이스·동일 타임스탬프에 **여러 창고**가 찍히면, `WH_PRIO` 순서대로 **체인 전이**로 간주: `AAA → DSV Indoor → DSV Al Markaz` 처럼.
  * WH가 **연속 반복**되면 하나로 축약(중복 제거).
* **전이 우선순위(타임라인 정렬)**

  * `Pre Arrival < Warehouse < Site < Shipping` 순으로 동일시각 tie-break.
  * 창고 내부는 `WH_PRIO`로 tie-break.
* **누적(러닝밸런스)**

  * `누적 = cumsum(입고 - 출고)` — **Opening/앵커링 없음.**
* **검증**

  * 최종월 `누적`이 **스냅샷(최종 위치 피벗)** 과 **자연히 일치**해야 한다. 안 맞으면 **원데이터의 상태 타임스탬프/순서**가 문제.

---

필요하면 `WH_PRIO`/사이트 목록만 네 환경에 맞게 조정하면 된다. 이 모듈로 돌리면 “DSV Indoor 월별 입·출고·누적”이 **실제 전이** 기반으로 맞춰지고, 너가 지적한 “거짓 누적” 증상이 사라진다.
