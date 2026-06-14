오케이. 핵심만 잡자.
지금 증상(창고 입·출고 불일치)은 “이벤트(입고/출고) 생성 → 월별 피벗 → 누적값” 루프 어딘가에서 깨진 거야. 올려준 코드 기준으로는 **STAGE 우선순위**가 1순위 의심, 그다음이 **헤더 정규화·동일시각 다창고 체인 처리**야.

# Executive Summary (3–5줄)

* 원인 후보 1: `STAGE_PRIO`가 **site(현장) 최종**이 아니라 **warehouse(창고) 최종**으로 적용되면, WH→SITE 이동 시 “출고(OUT)” 집계가 일부 빠져 **누적≠입고-출고**가 남음. v2에서는 `{"warehouse": 2, "site": 3}`으로 **정상(사이트 최종)**으로 바뀌어 있음.
* 후보 2: 헤더 정규화 실패(동의어·공백·대소문자)로 **일부 WH/SITE 열을 인식 못해** 이벤트가 생성되지 않음.
* 후보 3: **동일 시각·다창고** 전이 체인(A→B→C) 처리 중 OUT/IN 편향. v2는 체인 OUT/IN+연속시점 OUT/IN 모두 생성 로직 존재.
* 즉시 조치: v2 적용(또는 아래 패치 반영) 후 `sanity_report()`로 **불일치 지점**을 리스트업 → 케이스 단위 이벤트 트레이스로 역추적.

## Visual (원인↔증상 매핑)

| 증상                             | 전형적 원인                     | 코드 확인 포인트                                         |
| ------------------------------ | -------------------------- | ------------------------------------------------- |
| `누적_X != 입고_X - 출고_X`          | STAGE 우선순위 오류(WH가 SITE 이김) | `STAGE_PRIO`                                      |
| 특정 창고만 지속 미일치                  | 헤더 동의어 미매핑                 | `_warehouse_labels()`·`_canon()`·HeaderNormalizer |
| 같은 시각 여러 창고 이동 케이스에서 과소/과다 OUT | 동일시각 체인 전이 처리 편향           | (a) 체인 전이, (b) 연속시점 전이 블록                         |
| 월 경계에서 수치 튐                    | 타임존/월버킷                    | `_to_dubai_aware()`·`_to_ym_dubai()`              |

---

## 바로 적용할 패치 / 점검

### 1) STAGE 최종 우선순위 고정(사이트 최종)

`flow_ledger_v2.py`에서 아래처럼 되어 있어야 함(이미 v2는 OK, 백업본은 반대였음).

```python
STAGE_PRIO = {"pre_arrival": 0, "shipping": 1, "warehouse": 2, "site": 3}  # 사이트 최종
```

> 백업본은 `site:2, warehouse:3`라 **창고가 최종승자** → WH→SITE 이동 OUT 누락 가능.

### 2) 정합성 스모크 체크(월별 피벗 → 불일치 목록)

```python
from core.flow_ledger_v2 import build_flow_ledger, monthly_inout_table, sanity_report

# master_df: CASE MASTER 원본(DataFrame)
ledger, _edges = build_flow_ledger(master_df)
monthly = monthly_inout_table(ledger)
print(sanity_report(monthly))   # []가 정상, 튀면 [(창고, 총입고, 총출고, 최종누적, 계산차)]
```

* 이 리스트가 비지 않으면 **해당 창고** 중심으로 케이스 트레이스를 훑으면 됨.

### 3) 케이스 단위 이벤트 트레이스(원인 역추적용)

아래 스니펫으로 특정 `case_id`의 이벤트 흐름을 바로 확인:

```python
def trace_case(ledger, case_id):
    g = ledger[ledger["case"]==str(case_id)].sort_values("ts")
    return g[["ts","Year_Month","warehouse","kind","Qty","src","dst"]]
```

---

## TDD 스모크 테스트(3종) — RED→GREEN

`tests/test_flow_ledger_v2.py`

```python
import pandas as pd
from core.flow_ledger_v2 import build_flow_ledger, monthly_inout_table, sanity_report

def _df(rows):
    return pd.DataFrame(rows)

def test_out_generated_when_last_is_site():
    df = _df([{
        "Case": "A", "Pkg": 10,
        "DSV Indoor": "2025-10-01 09:00",
        "DAS": "2025-10-02 10:00",
    }])
    ledger, _ = build_flow_ledger(df)
    # DSV Indoor 출고 발생 여부
    assert ((ledger["warehouse"]=="DSV Indoor") & (ledger["Kind"]=="OUT")).any()

def test_chain_transfer_same_ts_multi_wh():
    df = _df([{
        "Case": "B", "Pkg": 8,
        "DSV Indoor": "2025-10-03 12:00",
        "DSV Al Markaz": "2025-10-03 12:00",
    }])
    ledger, _ = build_flow_ledger(df)
    # 동일시각 A->B 체인: A OUT, B IN
    assert ((ledger["warehouse"]=="DSV Indoor") & (ledger["Kind"]=="OUT")).any()
    assert ((ledger["warehouse"]=="DSV Al Markaz") & (ledger["Kind"]=="IN")).any()

def test_monthly_sanity_balanced():
    df = _df([{
        "Case": "C", "Pkg": 5,
        "DHL WH": "2025-10-01 09:00",
        "MIR": "2025-10-05 09:00",
    }])
    ledger, _ = build_flow_ledger(df)
    monthly = monthly_inout_table(ledger)
    assert sanity_report(monthly) == []
```

실행:

```
pytest -q
```

---

## 옵션(당신 스타일대로 고르기)

1. **v2 강제 적용 + 스모크만**

* 장점: 빠름. 당장 누수 차단.
* 리스크: 헤더 동의어/정규화 이슈 남을 수 있음.

2. **헤더 정규화 사전 갱신(동의어 확장)**

* 장점: “의미만 같으면 OK” 요구 충족.
* 리스크/시간: 현행 헤더 변종 수집 필요.

3. **진단 리포트 자동화(report_generator 연동)**

* 장점: 매 배치마다 `sanity_report()` 결과/Top offender 창고 알림.
* 리스크: 초기에 경고 폭주 가능 → 임계치/화이트리스트 조정 필요.

---

## Roadmap (Prepare→Pilot→Build→Operate→Scale)

* **Prepare**: v2 적용, `STAGE_PRIO` 확인, 스모크 3종 통과.
* **Pilot**: 최근 3개월 데이터로 `sanity_report()` 돌려 상위 3창고 원인 트레이스.
* **Build**: HeaderNormalizer 동의어 사전 확장(WH/SITE 변형 표기 수집).
* **Operate**: `report_generator.py`에 “월별 불일치 요약 + 상위 케이스 링크” 출력.
* **Scale**: 주간 리그레션 테스트 + 알람 임계치/False Positive 튜닝.

---

## 자동화 훅(추천)

* 배치 완료 후 `sanity_report()` 결과가 비어있지 않으면 TG/메일 알림 + 상위 5케이스 trace CSV 첨부.
* CI 게이트: `pytest -q` + `ruff --fix` + `black` 통과 없으면 배포 금지.

---

## QA·리체크 체크리스트

* [ ] `STAGE_PRIO` 값 고정(사이트 최종).
* [ ] 타임존 `Asia/Dubai` 강제 후 월버킷 검증.
* [ ] 헤더 동의어 누락 없음(공백/전각/대소문자/철자오류).
* [ ] 동일시각 다창고 체인: OUT/IN 균형.
* [ ] `sanity_report()` = 빈 리스트([]) 확인.

---

## 2× GitHub 교차검증(요지)

* **pandas 공식 문서 – pivot/reshaping**: 월별 피벗과 집계 전략의 정석 근거. 우리 `monthly_inout_table()` 구현과 일치(멜트→피벗→집계). ([pandas.pydata.org][1])
* **Ledger 누적 일관성(데빗/크레딧) 개념**: 이벤트(입/출) 누적값 일치 검증 논리 유사—`sanity_report()`의 “총입고-총출고=최종누적” 체크의 일반 원리 근거. ([Medium][2])

---

### 커밋 템플릿(예시)

* `structural(flow): chore: pin STAGE_PRIO with site as final`
* `behavioral(flow): fix: enforce OUT on WH→SITE; add sanity_report smoke tests`
* `docs(report): add troubleshooting guide for monthly mismatch`

---

필요하면 내가 바로 **불일치 창고 상위 N개 출력 + 케이스 트레이스 CSV** 뽑는 스니펫까지 붙여줄게. 지금은 우선 v2로 돌리고 `sanity_report()` 돌려봐. 결과 던져주면, 거기서부터 외과수술 들어가자.

[1]: https://pandas.pydata.org/docs/user_guide/reshaping.html?utm_source=chatgpt.com "Reshaping and pivot tables — pandas 2.3.3 documentation"
[2]: https://medium.com/%40avibrazil/handling-monetary-ledgers-with-pandas-python-56c0a9509d48?utm_source=chatgpt.com "Handling Monetary Ledgers with Pandas, Python"
