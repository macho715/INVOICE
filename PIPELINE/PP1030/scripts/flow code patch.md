바로 패치 버전으로 정리해서 줄게. 지금 네 리포터(`report_generator.py` / `hvdc_excel_reporter_final_sqm_rev.py`)는 기본적으로

* Pre Arrival → 0
* 그 외는 `1 + (WH 개수) + (MOSB 있으면 +1)` 하고
* 마지막에 `np.clip(..., 1, 4)`로 잘라서 1~4만 나오게 돼 있어. 

우리가 지금 필요한 건 **0~5 전체 스펙** + **AGI/DAS는 무조건 MOSB 레그** + **혼합/미기록 케이스는 5** 이거잖아. 그래서 아래처럼 바꿔주면 된다.

---

## 1) 패치 아이디어

1. **기본계산(관측기반)**

   * 0: Pre Arrival
   * 1: Port → Site (WH=0, MOSB=0)
   * 2: Port → WH → Site (WH=1, MOSB=0)
   * 3: Port → MOSB → Site (WH=0, MOSB=1) **(AGI/DAS 도메인 룰로도 올릴 수 있음)**
   * 4: Port → WH → MOSB → Site (WH≥1, MOSB=1)
   * 5: 위에 안 맞는 것들(WH 2개 이상 이상치, MOSB는 있는데 Site 없음, Final_Location 비었는데 중간까지만 온 것들)

2. **도메인 오버라이드(AGI/DAS 강제)**

   * Final_Location ∈ {AGI, DAS} 이고, 계산된 Flow_Code가 0/1/2라면 → 3으로 올리고,
   * 원래 값은 `FLOW_CODE_ORIG`에 남긴다.

3. **로그 남기기**

   * 왜 2 → 3이 됐는지 추적하려고 `FLOW_OVERRIDE_REASON`에 남긴다.

---

## 2) 수정 코드 (그대로 교체해서 써)

아래는 네 `report_generator.py` 안에 있던 `_override_flow_code()`를 0~5 버전으로 다시 쓴 거야. 지금 파일 구조랑 거의 같게 맞춰놨으니까 이 함수만 갈아끼우면 돼.

```python
def _override_flow_code(self):
    """Flow Code 재계산 (v3.5: 0~5 확장 + AGI/DAS MOSB 강제)"""
    import numpy as np
    import pandas as pd
    import logging

    logger = logging.getLogger(__name__)

    df = self.combined_data
    if df is None:
        raise ValueError("데이터가 로드되지 않았습니다.")

    # 1) 창고/오프쇼어 컬럼 분리
    # 기존 코드에도 self.warehouse_columns 안에 MOSB가 섞여 있어서 한 번 더 분리해준다.
    WH_COLS = [c for c in self.warehouse_columns if c != "MOSB"]
    MOSB_COLS = [c for c in self.warehouse_columns if c == "MOSB"]

    # 2) 0, '' → NaN 치환 (기존 로직 유지) :contentReference[oaicite:1]{index=1}
    for col in WH_COLS + MOSB_COLS:
        if col in df.columns:
            df[col] = df[col].replace({0: np.nan, "": np.nan})

    # 3) Pre Arrival 판별
    status_col = "Status_Location"
    if status_col in df.columns:
        is_pre_arrival = df[status_col].astype(str).str.contains("Pre Arrival", case=False, na=False)
    else:
        is_pre_arrival = pd.Series(False, index=df.index)

    # 4) hop 수 계산
    wh_cnt = df[WH_COLS].notna().sum(axis=1) if WH_COLS else 0
    has_mosb = df[MOSB_COLS].notna().any(axis=1) if MOSB_COLS else pd.Series(False, index=df.index)

    # 5) 기본 Flow 계산 (관측 이벤트 기준)
    # 0: Pre Arrival
    flow = pd.Series(0, index=df.index, dtype="int64")
    flow_desc = pd.Series("", index=df.index, dtype="object")

    # 0번 먼저 세팅
    flow[is_pre_arrival] = 0
    flow_desc[is_pre_arrival] = "Flow 0: Pre Arrival"

    # Pre Arrival 아니면 규칙대로
    not_pre = ~is_pre_arrival

    # (a) WH=0, MOSB=0 → 1
    mask_1 = not_pre & (wh_cnt == 0) & (~has_mosb)
    flow[mask_1] = 1
    flow_desc[mask_1] = "Flow 1: Port → Site"

    # (b) WH=1+, MOSB=0 → 2
    mask_2 = not_pre & (wh_cnt >= 1) & (~has_mosb)
    flow[mask_2] = 2
    flow_desc[mask_2] = "Flow 2: Port → WH → Site"

    # (c) WH=0, MOSB=1 → 3 (Port → MOSB → Site)
    mask_3 = not_pre & (wh_cnt == 0) & (has_mosb)
    flow[mask_3] = 3
    flow_desc[mask_3] = "Flow 3: Port → MOSB → Site (AGI/DAS allowed)"

    # (d) WH≥1, MOSB=1 → 4 (Port → WH → MOSB → Site)
    mask_4 = not_pre & (wh_cnt >= 1) & (has_mosb)
    flow[mask_4] = 4
    flow_desc[mask_4] = "Flow 4: Port → WH → MOSB → Site (AGI/DAS)"

    # 6) 도메인 오버라이드: AGI/DAS는 MOSB 레그 필수
    # Final_Location이 AGI/DAS인데 0/1/2로 잡힌 애들은 3으로 승급
    final_col_candidates = ["Final_Location", "Final location", "Final_Location_Site", "Site_Final"]
    final_col = None
    for cand in final_col_candidates:
        if cand in df.columns:
            final_col = cand
            break

    df["FLOW_CODE_ORIG"] = flow  # 원래 값 보존

    if final_col is not None:
        is_agi_das = df[final_col].astype(str).str.upper().isin(["AGI", "DAS"])
        need_force = is_agi_das & flow.isin([0, 1, 2])
        flow[need_force] = 3
        flow_desc[need_force] = "Flow 3: Port → MOSB → Site (AGI/DAS forced)"
        df.loc[need_force, "FLOW_OVERRIDE_REASON"] = "AGI/DAS requires MOSB leg"
    else:
        df["FLOW_OVERRIDE_REASON"] = np.nan

    # 7) 혼합/미완료 케이스 → 5로 올리기
    # 조건 예시:
    # - MOSB는 찍혀 있는데 최종 위치가 없음
    # - WH가 2개 이상인데 MOSB 없음 (너가 말한 '대기중'으로 보는 케이스)
    has_site = False
    SITE_COLS = getattr(self, "site_columns", [])
    if SITE_COLS:
        has_site = df[SITE_COLS].notna().any(axis=1)
    else:
        has_site = pd.Series(True, index=df.index)  # 없으면 패스

    cond_mosb_no_site = (has_mosb) & (~has_site)
    cond_weird_wh = (wh_cnt >= 2) & (~has_mosb) & (~is_pre_arrival)
    need_5 = cond_mosb_no_site | cond_weird_wh

    flow[need_5] = 5
    flow_desc[need_5] = "Flow 5: Mixed / Waiting / Incomplete leg"

    # 8) 최종 반영
    df["FLOW_CODE"] = flow.astype("int64")
    df["FLOW_DESCRIPTION"] = flow_desc

    # 9) 디버깅 로그
    dist = df["FLOW_CODE"].value_counts().sort_index()
    logger.info(f"[FlowCode v3.5] 분포: {dict(dist)}")
    self.combined_data = df
    return self.combined_data
```

---

## 3) 이게 해결하는 것

1. **AGI/DAS 직송처럼 보이는 오류**

   * 원래는 Port→Site로 들어가버리던 게, 지금은 Final_Location이 AGI/DAS면 3으로 강제 승급돼.
   * 너가 말한 “현장에 공간 없어서 대기 중인 화물”이 MOSB에만 찍혀 있어도 3~4 영역으로 올라가.

2. **대기/혼합 건**

   * WH 두 군데 찍혀 있고 MOSB는 없거나, MOSB는 찍혔는데 Site가 비어 있으면 → 5로 몰아서 “대기/불완전”으로 보인다. 이게 지금 네 설명 “현정에 보관공간이 없어 대기”랑 맞다.

3. **기존 리포트랑 호환**

   * 컬럼 이름은 그대로 `FLOW_CODE`, `FLOW_DESCRIPTION`이라 피벗/리포트가 안 깨진다.
   * 추가로 `FLOW_CODE_ORIG`, `FLOW_OVERRIDE_REASON`만 늘어났으니, 필요 없으면 엑셀 쓸 때 드랍하면 됨.

---

## 4) 주의 2줄

* 지금 패치는 **0~5**를 쓰니까, 너 피벗 만들 때 `clip(0, 4)` 해 놓은 부분 하나만 같이 빼줘. 그 부분이 남아 있으면 또 5가 4로 잘려. (예: `self.combined_data['FLOW_CODE'] = ...clip(0, 4)` 이런 줄들) 
* DAS/AGI 식별 컬럼명이 엑셀마다 미묘하게 다르면 위의 `final_col_candidates` 리스트에 너 현장 컬럼 이름 하나만 더 추가하면 돼.

---

## 5) 다음에 할 것 (짧게)

1. 위 함수 교체 → 실행해서 분포 확인
2. 분포가 `0,1,2,3,4,5` 다 찍히면 OK
3. 리포트 만드는 쪽에서 `FLOW_CODE` 그룹바이 시 5도 포함하게 바꾸기
4. 대시보드 필터에 “Flow 5: Mixed/Waiting” 추가

---

필요하면 이걸 JSON 룰셋 버전으로도 다시 빼줄 수 있어. 지금은 파이썬 쪽부터 맞췄어.
