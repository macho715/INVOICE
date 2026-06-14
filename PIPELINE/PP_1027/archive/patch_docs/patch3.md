맞네. 지금 우리 “월별 입·출고”는 **흐름(Flow)**만 합산해서 누적을 만들고 있고, **기초재고(Opening Balance)**를 안 얹고 있어. 그래서 DSV Indoor가 44처럼 보였던 거고, 네가 만든 피벗(스냅샷)은 **현재고(Stock Snapshot)**라서 789가 맞게 나온 거야.
요약: `누적 = (기초재고) + Σ(입고−출고)`인데, 기초재고가 0으로 깔려 있으니 뒤끝이 다 틀어진 상황.

아래처럼 “스냅샷-앵커링(Anchoring)”을 한 줄 추가하면 맞춰진다. 마지막 달의 흐름누적을 **최신 스냅샷(=Final_Location 기준 재고)**에 강제로 일치시키고, 그 차이를 전월까지 일정하게 더해준다. (즉, *빠져있던 기초재고*를 보정)

---

# 패치(요점만): 월말 스냅샷으로 누적 보정

`report_generator.py`의 월별 테이블을 만든 뒤(= `df_out` 반환 직전), 아래 2개 헬퍼를 넣고 호출하세요.
창고명 매핑은 이미 `HeaderRegistry/HeaderNormalizer`를 쓰고 있다는 전제 그대로입니다.

```python
def _build_latest_snapshot_from_master(stats) -> dict[str, int]:
    """
    최신 스냅샷(창고별 현재고)을 만든다.
    우선순위:
      1) stats["snapshot_result"]["final_locations"] 형태가 있으면 사용
      2) 아니면 stats["master"] 또는 stats["case_master"]에서
         Final_Location(=창고)별 Pkg 합계로 계산
    반환: {"DSV Indoor": 789, "DSV Outdoor": 792, ...}
    """
    import pandas as pd

    # 1) 명시 스냅샷이 있으면
    snap = (stats.get("snapshot_result", {}) or {}).get("final_locations")
    if isinstance(snap, dict) and snap:
        return {str(k): int(v) for k, v in snap.items()}

    # 2) 마스터에서 Final_Location 스냅샷 계산
    for key in ("master", "case_master", "master_rows", "final_table"):
        rows = stats.get(key)
        if isinstance(rows, list) and rows:
            df = pd.DataFrame(rows)
            break
    else:
        return {}

    # 컬럼 유연 매핑
    loc_col = next((c for c in df.columns if c.lower().replace(" ", "_") in
                   ("final_location","status_location_final","location_final")), None)
    qty_col = next((c for c in df.columns if c.lower().replace(" ", "_") in
                   ("pkg","pkg_quantity","quantity","qty")), None)
    if not loc_col or not qty_col:
        return {}

    # 헤더 정규화(별칭→정식 라벨)
    from header_normalizer import HeaderNormalizer
    from header_registry import HVDC_HEADER_REGISTRY
    normalizer = HeaderNormalizer()

    # 레지스트리에서 창고 라벨(정식) 수집
    WAREHOUSE_LABELS = {d.description for d in
                        [HVDC_HEADER_REGISTRY.get_definition(k) for k in (
                            "dhl_wh","dsv_indoor","dsv_al_markaz","dsv_outdoor",
                            "dsv_mzp","jdn_mzd","hauler_indoor","aaa_storage","mosb"
                        )]}

    # 별칭 맵 만들기
    amap = {}
    for label in WAREHOUSE_LABELS:
        amap[normalizer.normalize(label)] = label
    # 행마다 매핑
    tmp = df[[loc_col, qty_col]].copy()
    tmp[loc_col] = tmp[loc_col].astype(str).map(lambda s: amap.get(normalizer.normalize(s)))
    tmp = tmp[tmp[loc_col].isin(WAREHOUSE_LABELS)]
    snap_df = tmp.groupby(loc_col)[qty_col].sum().astype(int)
    return snap_df.to_dict()

def _anchor_cumulative_to_snapshot(df_monthly: pd.DataFrame, snapshot: dict[str, int]) -> pd.DataFrame:
    """
    월별 테이블(df_monthly)을 스냅샷에 맞춰 보정.
    각 창고에 대해:
      last_flow = 마지막달 누적
      last_snap = snapshot[창고]
      delta = last_snap - last_flow
      → 누적 열 전체에 delta를 더해 고정
    """
    out = df_monthly.copy()
    # 대상 창고 추출: "... (입고)/(출고)" 패턴에서 라벨 뽑기
    warehouses = sorted({c[:-5] for c in out.columns if c.endswith(" (입고)")})
    for w in warehouses:
        in_col  = f"{w} (입고)"
        out_col = f"{w} (출고)"
        if in_col not in out.columns or out_col not in out.columns:
            continue
        # 누적 계산(없으면 생성)
        cum_col = f"누적_{w}"
        if cum_col not in out.columns:
            out[cum_col] = (out[in_col].astype(int) - out[out_col].astype(int)).cumsum()

        # 스냅샷 앵커링
        last_flow = int(out[cum_col].iloc[-1])
        last_snap = int(snapshot.get(w, last_flow))
        delta = last_snap - last_flow
        if delta != 0:
            out[cum_col] = out[cum_col] + delta
    return out
```

**사용 위치(요약)**

```python
df_monthly = ...  # create_warehouse_monthly_sheet() 결과 (입/출고 피벗 포함)
snapshot = _build_latest_snapshot_from_master(stats)   # ← Final_Location 스냅샷 계산
df_monthly = _anchor_cumulative_to_snapshot(df_monthly, snapshot)

# 이후 DSV Indoor 요약 표 생성 시 df_monthly['누적_DSV Indoor']를 사용
```

---

## 기대 결과 (DSV Indoor 예)

* 마지막달 `누적_DSV Indoor`가 **789**로 딱 맞게 고정(= 너의 피벗과 동일).
* 앞선 달들도 **같은 델타**가 더해져 일관된 시계열이 됨 → *기초재고를 전기간에 반영*한 것과 동일 효과.
* 입고/출고의 월간 합계 값은 **변하지 않음**(흐름 데이터는 건드리지 않음).

## 왜 이 방식이 안전한가

* 스냅샷(현재고)은 “사실”이고, 흐름 누적은 “모델”이야.
* 모델이 놓친 **과거 재고(오래된 Opening)**를 스냅샷으로 1회 보정하면, 양쪽 진실을 동시에 만족.
* 데이터에 따라 스냅샷 기준월을 “마지막달”이 아니라 **임의 월(예: 연말)**로 바꿔도 동일 패턴으로 작동.

---

원하면 “월말 스냅샷” 자체를 시계열로 뽑아서(매월 `Final_Location` 기준) **흐름누적 vs 스냅샷** 두 라인을 함께 보여주는 리콘 탭도 붙일 수 있어. 지금은 급한 DSV Indoor 789 맞추는 라인만 꽂아놨다.
