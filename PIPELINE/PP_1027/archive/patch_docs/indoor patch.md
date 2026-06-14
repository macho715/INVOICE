오케이. 헤더는 `header_registry/header_normalizer` 쪽 “단일 출처(SoT)”로 묶여 있으니까, 월별 집계에서도 **별칭→정규 헤더(창고명)** 매핑을 전부 레지스트리에서 가져오도록 바꿉니다. 그러면 `DSV Indoor`가 어떤 표기로 들어와도(공백/대소문자/전각/오타 근접) 한 키로 귀속돼서 월별 입·출고 수치가 더이상 갈라지지 않습니다. 핵심은 두 가지:

1. **창고별 canonical 라벨**을 `HeaderRegistry`에서 뽑고
2. 모든 **별칭은 `HeaderNormalizer`로 normalize**해서 매핑(look-up)합니다.
   레지스트리 구조와 노멀라이저 역할은 여기 정의돼 있어요:

---

# 패치: `report_generator.py` 내 “창고_월별_입출고” 생성부 교체

아래 블록을 **기존 함수 전체 대체**로 붙여 넣으면 됩니다.
(레지스트리에서 창고 LOCATION만 필터링, `HeaderNormalizer`로 별칭 정규화 → `alias_map` 생성 → groupby/pivot)

```python
# report_generator.py

from datetime import datetime
import pandas as pd
from typing import Dict, List, Tuple

# 🔗 헤더 SoT
from header_registry import HVDC_HEADER_REGISTRY, HeaderCategory
from header_normalizer import HeaderNormalizer

# --- 내부 헬퍼: 레지스트리 기반 창고 목록 & 별칭맵 -----------------------------

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

def _warehouse_defs():
    reg = HVDC_HEADER_REGISTRY
    return [reg.get_definition(k) for k in _WAREHOUSE_KEYS]

def _canonical_warehouses() -> List[str]:
    """
    표에 찍을 '정식 창고 라벨' 목록(표시 순서 고정).
    header_registry.HeaderDefinition.description 사용.
    """
    return [d.description for d in _warehouse_defs()]

def _alias_map_normalized() -> Dict[str, str]:
    """
    별칭 → 정식 라벨 매핑(노멀라이즈된 키).
    모든 별칭을 HeaderNormalizer로 정규화해 lookup 키로 사용.
    """
    normalizer = HeaderNormalizer()
    amap: Dict[str, str] = {}
    for d in _warehouse_defs():
        canonical = d.description  # e.g., "DSV Indoor"
        for alias in d.aliases:
            k = normalizer.normalize(alias)  # ex) "dhlwarehouse", "dsvalmarkaz"
            amap[k] = canonical
        # 정식 라벨 자체도 키로 허용
        amap[normalizer.normalize(canonical)] = canonical
    return amap

def _canon_warehouse(value: object, _amap=_alias_map_normalized()) -> str | None:
    """
    임의 표기의 창고 텍스트를 '정식 라벨'로 치환. 미매칭 시 None.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    k = HeaderNormalizer().normalize(s)
    return _amap.get(k)

# --- 메인: 창고_월별_입출고 ------------------------------------------------------

def create_warehouse_monthly_sheet(self, stats: Dict) -> pd.DataFrame:
    """
    창고_월별_입출고 (레지스트리 구동 + 정규화 피벗)
    - Inbound: external_arrival + warehouse_transfers(to_warehouse)
    - Outbound: warehouse_transfers(from_warehouse) + outbound_items(From_Location→Site)
    """
    logger.info("창고_월별_입출고 시트 생성(레지스트리/노멀라이저 기반)")

    # 1) 월 인덱스 정의
    end_month = datetime.now().strftime("%Y-%m")
    months = pd.date_range("2023-02", end_month, freq="MS")
    month_keys = [m.strftime("%Y-%m") for m in months]

    warehouses = _canonical_warehouses()  # 표에 나올 고정 순서 라벨
    alias_map = _alias_map_normalized()   # 별칭→정식 라벨

    # 2) 원본 DF 안전 취득
    in_items = pd.DataFrame(stats.get("inbound_result", {}).get("inbound_items", []))
    wh_tx    = pd.DataFrame(stats.get("inbound_result", {}).get("warehouse_transfers", []))
    out_items= pd.DataFrame(stats.get("outbound_result", {}).get("outbound_items", []))

    def _mk_inbound_df() -> pd.DataFrame:
        frames = []

        # 2-1) 외부→창고 입고
        if not in_items.empty:
            t = in_items.copy()
            # Year_Month, Warehouse, Inbound_Type, Pkg_Quantity 존재 가정(없어도 에러 안 나게)
            t["Year_Month"] = t.get("Year_Month", "").astype(str)
            t["Warehouse"]  = t.get("Warehouse")
            t["Qty"]        = t.get("Pkg_Quantity", 1).fillna(1)
            t = t[t.get("Inbound_Type").eq("external_arrival")]
            t["Warehouse"]  = t["Warehouse"].map(_canon_warehouse)
            t = t[["Year_Month", "Warehouse", "Qty"]].dropna(subset=["Warehouse"])
            frames.append(t)

        # 2-2) 창고간 이동(→ to_warehouse는 '입고'로 본다)
        if not wh_tx.empty:
            t = wh_tx.copy()
            t["Year_Month"]   = t.get("Year_Month", "").astype(str)
            to_wh_col         = "to_warehouse" if "to_warehouse" in t.columns else "To_Warehouse"
            qty_col           = "pkg_quantity" if "pkg_quantity" in t.columns else "Pkg_Quantity"
            t["Warehouse"]    = t[to_wh_col].map(_canon_warehouse)
            t["Qty"]          = t.get(qty_col, 1).fillna(1)
            t = t[["Year_Month", "Warehouse", "Qty"]].dropna(subset=["Warehouse"])
            frames.append(t)

        if not frames:
            return pd.DataFrame(columns=["Year_Month", "Warehouse", "Qty"])
        return pd.concat(frames, ignore_index=True)

    def _mk_outbound_df() -> pd.DataFrame:
        frames = []

        # 2-3) 창고간 이동(← from_warehouse는 '출고'로 본다)
        if not wh_tx.empty:
            t = wh_tx.copy()
            t["Year_Month"]    = t.get("Year_Month", "").astype(str)
            from_wh_col        = "from_warehouse" if "from_warehouse" in t.columns else "From_Warehouse"
            qty_col            = "pkg_quantity" if "pkg_quantity" in t.columns else "Pkg_Quantity"
            t["Warehouse"]     = t[from_wh_col].map(_canon_warehouse)
            t["Qty"]           = t.get(qty_col, 1).fillna(1)
            t = t[["Year_Month", "Warehouse", "Qty"]].dropna(subset=["Warehouse"])
            frames.append(t)

        # 2-4) 창고→현장 출고(From_Location을 창고로 해석)
        if not out_items.empty:
            t = out_items.copy()
            t["Year_Month"]    = t.get("Year_Month", "").astype(str)
            t["Warehouse"]     = t.get("From_Location").map(_canon_warehouse)
            t["Qty"]           = t.get("Pkg_Quantity", t.get("pkg_quantity", 1)).fillna(1)
            t = t[["Year_Month", "Warehouse", "Qty"]].dropna(subset=["Warehouse"])
            frames.append(t)

        if not frames:
            return pd.DataFrame(columns=["Year_Month", "Warehouse", "Qty"])
        return pd.concat(frames, ignore_index=True)

    inbound  = _mk_inbound_df()
    outbound = _mk_outbound_df()

    # 3) 피벗 (월×창고) — 누락 조합은 0으로 채움
    in_pvt  = inbound.groupby(["Year_Month", "Warehouse"])["Qty"].sum().unstack(fill_value=0)
    out_pvt = outbound.groupby(["Year_Month", "Warehouse"])["Qty"].sum().unstack(fill_value=0)

    # 4) 인덱스/컬럼 정렬(월 전체, 창고 순서 고정)
    for m in month_keys:
        if m not in in_pvt.index:  in_pvt.loc[m]  = 0
        if m not in out_pvt.index: out_pvt.loc[m] = 0
    in_pvt  = in_pvt.reindex(index=month_keys, columns=warehouses, fill_value=0)
    out_pvt = out_pvt.reindex(index=month_keys, columns=warehouses, fill_value=0)

    # 5) 출력 테이블: [입고월] + 각 창고(입고) + 각 창고(출고)
    header = (["입고월"]
              + [f"{w} (입고)" for w in warehouses]
              + [f"{w} (출고)" for w in warehouses])

    rows = []
    for m in month_keys:
        rows.append(
            [m]
            + [int(in_pvt.at[m, w])  for w in warehouses]
            + [int(out_pvt.at[m, w]) for w in warehouses]
        )

    df_out = pd.DataFrame(rows, columns=header)
    logger.info("창고_월별_입출고 시트 생성 완료")
    return df_out
```

### 포인트

* **창고 정의·별칭**은 전부 `HeaderRegistry`에서 가져옵니다(하드코딩 금지). 레지스트리 카테고리/정의 구조는 모듈 주석과 클래스에 정리돼 있습니다.
* **정규화 키**는 `HeaderNormalizer.normalize()`를 사용(대소문자·공백·전각·구분자 제거 + 약어 확장)합니다. 그래서 `DHL Warehouse / DHL_WH / DHL` 모두 **동일 키**로 붙습니다.
* 창고 라벨은 사람이 보는 **`HeaderDefinition.description`**(예: “DSV Indoor”)로 통일해 열 제목을 만듭니다.

---

## 빠른 검증(DSV Indoor 이슈 리체크)

1. `warehouse_transfers`에서 `to_warehouse`가 DSV Indoor 계열(아무 표기나)인 2025-09 합계를 구해보세요.
2. 생성된 시트의 `2025-09 / DSV Indoor (입고)` 값과 **일치**해야 합니다.
3. `DHL WH`가 예전처럼 `DHL Warehouse`로 갈라지지 않고 **한 열만** 남는지 확인.

필요하면 창고 추가/표기 변형은 **레지스트리에만** 보태면 됩니다. (코드 수정 無)
