오케이. “전혀 틀리다”면 지금 출력 테이블이 **원천 흐름(전이 이벤트)**와 어긋난다는 뜻이야. 회피 말고 바로 잡자. 아래 순서로 **진단 → 원인별 패치**까지 한 번에 간다.

---

# 1) 먼저, 무엇이 틀렸는지 ‘기계적으로’ 찍어내자

다음 검산은 거짓말 안 한다. 창고별로
`∑입고 − ∑출고 = 마지막 누적` 이 성립해야 한다.

```python
def sanity_report(df_monthly):
    bad = []
    for col in [c[:-5] for c in df_monthly.columns if c.endswith(" (입고)")]:
        total_in  = int(df_monthly[f"{col} (입고)"].sum())
        total_out = int(df_monthly[f"{col} (출고)"].sum())
        last_bal  = int(df_monthly[f"누적_{col}"].iloc[-1])
        if total_in - total_out != last_bal:
            bad.append((col, total_in, total_out, last_bal, total_in-total_out))
    return bad  # 비면 정합 OK
```

여기서 한 군데라도 걸리면, 아래 네 군데 중 하나(또는 복합)다.

---

# 2) 실제로 어긋나게 만드는 상위 4가지 원인(그리고 즉시 고치는 법)

## A) 월 버킷이 틀린 경우(타임존/형식)

* **증상**: 특정 월이 +1/−1로 밀림. 야간 타임스탬프가 다른 달로 떨어짐.
* **원인**: `to_datetime(..., errors="coerce")`로 파싱하면서 타임존 혼재(naive/aware)를 뒤섞거나, 로컬(Asia/Dubai)로 환산 전 월을 잘라버림. `errors='coerce'`는 파싱 실패를 **NaT로 날려버리기** 때문에 조용히 행이 사라질 수도 있음(공식 문서가 그렇게 동작함). ([Pandas][1])
* **패치**: 이벤트 시간열을 **UAE 시간으로 통일 후 월 산출**.

```python
# tz-aware ↔ tz-naive 혼재 방지 → 모두 UTC로 해석 후 Dubai로 변환, 다시 naive로
ts = pd.to_datetime(raw_ts, errors="coerce", utc=True)  # 파싱 실패는 NaT로
ts = ts.dt.tz_convert("Asia/Dubai").dt.tz_localize(None)  # 월 경계가 Dubai 기준이 되도록
df["Year_Month"] = ts.dt.strftime("%Y-%m")
```

타임존 혼재와 변환 규칙은 실무에서 자주 터지는 케이스고, 변환 실패 시 NaT로 떨어뜨리는 건 공식 가이드에 맞다. ([Stack Overflow][2])

## B) 동일 시각 다중 이벤트 결합 규칙(max vs sum)

* **증상**: 같은 케이스가 같은 타임스탬프에 2개 이상 창고 기록 → 체인을 만들 때 수량이 덜/더해짐.
* **원인**: 우리가 보수적으로 `qty=max(...)`를 적용했는데, 실제는 **둘 다 유효한 처리**라 **sum**이 맞을 수 있다.
* **패치(토글 가능)**:

```python
# collapse_same_timestamp() 안에서
qty = int(g["qty"].sum())  # <-- 정책: sum으로 변경
# 필요하면 환경변수/옵션으로 max/sum 스위치
```

피벗/집계 자체는 pandas 표준 사용이라 API 문제는 아님. `pivot_table(..., fill_value=0)`은 문서대로다. ([Pandas][3])

## C) 날짜 파싱으로 행이 소실됨

* **증상**: 월별 합계가 “현장 엑셀 피벗”보다 작음.
* **원인**: `to_datetime(errors="coerce")` 때문에 형식이 다른 날짜가 통째로 NaT → 드랍. 공식 동작이 그렇다. ([Pandas][1])
* **패치**: 파싱 전후 건수 로그 + 포맷 후보 적용.

```python
n0 = len(df)
dt = pd.to_datetime(df["date"], errors="coerce", utc=True)
print("parsed:", dt.notna().sum(), "/", n0)   # 급감하면 포맷 지정 필요

# 예: 일/월/년 데이터면
dt2 = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M", errors="coerce", utc=True)
```

포맷 지정/오동작 사례는 커뮤니티에서도 반복된 주제. ([Stack Overflow][4])

## D) 전이 해석 단계에서 ‘사이트/배송’의 동률 정렬

* **증상**: 같은 시각에 `Warehouse→Site`가 있었는데 tie-break가 잘못되어 IN/OUT 방향이 꼬임.
* **패치**: 동일 타임스탬프 정렬은 `PreArrival < Warehouse < Site < Shipping`(stage 우선) + **창고 내부 우선순위**로 이미 넣어뒀지만, 데이터에 맞게 조정 가능.

```python
STAGE_PRIO = {"pre_arrival":0, "warehouse":1, "site":2, "shipping":3}
# 필요 시 site 내부도 우선순위 dict 추가
```

정렬 키로 멀티컬럼을 쓰는 건 pandas 권장 패턴이고, 우리는 그 규칙을 이미 사용 중. ([Pandas][5])

---

# 3) 재현 가능한 최소 스모크(네 데이터에서 바로 실패 원인을 특정)

아래 세 줄만 통과하면 결과가 “전혀 틀리다” 수준은 바로 사라진다.

```python
# A. 월 경계 검사 (Dubai 기준, 누락 확인)
assert df["Year_Month"].isna().sum() == 0  # NaT 유입 차단

# B. 정책 실험: 동일시각 qty 결합 SUM/ MAX 교차
def run_policy(policy="sum"):
    # ... ledger 빌드에서 qty 집계만 sum/max 스위치 ...
    return df_monthly

r_sum = run_policy("sum")
r_max = run_policy("max")
print("sanity(sum):", sanity_report(r_sum))
print("sanity(max):", sanity_report(r_max))
# 둘 중 하나는 빈 리스트가 나와야 정상.

# C. 최종 검산: 창고별 재무 등식
bad = sanity_report(df_monthly)
if bad:
    # 어떤 창고, 얼마가 어긋나는지 딱 찍힘
    print("MISMATCH:", bad)
```

---

# 4) 딱 필요한 코드 패치(짧게 요약)

1. **월 생성 위치**를 전이 레저 만들기 “직전”으로 옮기고, 반드시 `Asia/Dubai`로 변환 후 `Year_Month` 생성.
2. **동일시각 수량 결합 규칙**을 `sum`로 일단 고정(네 데이터가 ‘실제 2건’으로 보임).
3. `sanity_report`를 리포트 파이프라인 마지막에 넣어 **불일치 시 실행 실패**(빨간불)로 처리.

---

# 5) 마지막으로, “왜 이게 근거 있는가”

* `to_datetime(errors="coerce")`는 파싱 실패/범위초과를 **NaT로 보내도록 공식 정의**되어 있음. 그래서 조용히 행이 빠질 수 있다. ([Pandas][1])
* 타임존 혼재/정규화 이슈는 tz-aware/naive 섞일 때 대표적 오류이고, **현지 시간대로 변환 후 naive로** 처리하는 게 일반 해법. ([Stack Overflow][2])
* `pivot_table(..., fill_value=0)` / `melt` / `groupby().cumsum()`은 현재 판다스(2.2.x/2.3.x) 문서 기준 **정석 호출**. ([Pandas][3])

---

지금 당장 할 일:

* 동일시각 **qty=SUM**로 바꾸고, **Dubai 기준 월 산출** 다시 돌려봐.
* 그 다음 `sanity_report` 결과 던져줘. 거기 찍히는 창고/수치 기준으로 **남은 오차를 케이스/타임스탬프 단위**로 파고들면 바로 잡힌다.

[1]: https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html?utm_source=chatgpt.com "pandas.to_datetime — pandas 2.3.0 documentation - PyData |"
[2]: https://stackoverflow.com/questions/16628819/convert-pandas-timezone-aware-datetimeindex-to-naive-timestamp-but-in-certain-t?utm_source=chatgpt.com "Convert pandas timezone-aware DateTimeIndex to naive timestamp ..."
[3]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.pivot_table.html?utm_source=chatgpt.com "pandas.pivot_table — pandas 2.3.3 documentation - PyData |"
[4]: https://stackoverflow.com/questions/75294650/pd-to-datetime-weird-error-when-parsing-correct-date-format?utm_source=chatgpt.com "pd.to_datetime() weird error when parsing correct date format"
[5]: https://pandas.pydata.org/docs/user_guide/reshaping.html?utm_source=chatgpt.com "Reshaping and pivot tables — pandas 2.3.3 documentation"
