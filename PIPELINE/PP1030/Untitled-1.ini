판정: **예 — `hvdc all status` 시트를 기준으로 맵을 적용해야 합니다. 그리고 적용 방식은 `전세계 항차 데이터`와 `UAE 실행 네트워크 데이터`를 같은 행에서 분리 추출하는 구조가 맞습니다.**
근거: 시트 직접 확인 결과 `hvdc all status`는 **893개 shipment row**와 `POL / POD / ETA / ATA / Customs Start / Customs Close / SHU~AGI / DSV Indoor~MOSB / FINAL DELIVERY`를 모두 갖고 있어, `Global`과 `UAE Ops`를 한 시트에서 동시에 만들 수 있습니다. 문서 규칙도 Flow Code를 `Port→Site`, `Port→WH→Site`, `Port→MOSB→Site`, `Port→WH→MOSB→Site`로 정의하고, **AGI/DAS는 MOSB 경유 필수**로 고정합니다.  
다음행동: **`hvdc all status` 1행 = 1 shipment`를 기준 grain으로 고정하고, 같은 row에서 `Global용 path`와 `UAE Ops용 path`를 각각 생성하십시오.**

---

# 1) 시트 기준으로 먼저 고정해야 할 것

`hvdc all status`는 맵용 기준 시트로 충분합니다.
이유는 이 시트가 한 행 안에 아래 3가지를 모두 담고 있기 때문입니다.

1. **항차/수입 정보**

   * `COE`
   * `POL`
   * `POD`
   * `SHIP MODE`
   * `ETD / ATD / ETA / ATA`

2. **통관 정보**

   * `Attestation Date`
   * `DO Collection`
   * `Customs Start`
   * `Customs Close`
   * `Custom Code`

3. **운영 이동 정보**

   * `SHU / MIR / DAS / AGI`
   * `DSV Indoor / DSV Outdoor / DSV MZD / DSV Kizad / JDN MZD / JDN Waterfront / AAA Storage / ZENER (WH) / Hauler DG Storage / Vijay Tanks`
   * `MOSB`
   * `FINAL DELIVERY`

즉 이 시트는 이미 **항차 + 통관 + 창고/현장 + 완료**를 한 줄에 갖고 있습니다.

---

# 2) 맵에 어떻게 적용하나 — 핵심 원칙

## 원칙 1

**`hvdc all status` 1행 = 1 shipment / 1 voyage case`로 본다.**

이걸 깨면 맵이 다시 꼬입니다.

## 원칙 2

같은 row에서 **두 개의 path**를 뽑습니다.

```text id="hvdc-path-dual-01"
A. Global path
B. UAE Ops path
```

## 원칙 3

`WH`는 노드 중 하나일 뿐이고, 중심축은 아닙니다.

* Global 중심축 = `Origin → POD → Final Site`
* UAE Ops 중심축 = `Port/Air → Customs → (WH) → (MOSB) → Site`

---

# 3) 컬럼을 어떻게 맵핑해야 하나

## A. Global 모드에 쓰는 컬럼

Global은 **전체 항차 흐름**이므로 아래만 먼저 씁니다.

| 구분       | 컬럼                                         |
| -------- | ------------------------------------------ |
| 출발 지역    | `COE`, `POL`                               |
| UAE 진입점  | `POD`                                      |
| 운송수단     | `SHIP MODE`                                |
| 항차 시점    | `ETD`, `ATD`, `ETA`, `ATA`                 |
| 최종 목적 힌트 | `DOC_SHU`, `DOC_MIR`, `DOC_DAS`, `DOC_AGI` |
| 최종 완료    | `FINAL DELIVERY`                           |

### 적용 규칙

* `COE` → Origin country cluster
* `POL` → Origin port/airport label
* `POD` → UAE entry node
* `DOC_*` → planned destination
* `FINAL DELIVERY` → delivered flag

### 핵심

Global에서는 `DSV Indoor`, `MOSB` 같은 중간 staging 날짜를 **주연으로 쓰지 않습니다.**

---

## B. UAE Ops 모드에 쓰는 컬럼

UAE Ops는 **실행 네트워크**이므로 아래를 씁니다.

| 구분             | 컬럼                                                                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Port/Air entry | `POD`, `ATA`                                                                                                                                      |
| Customs        | `Customs Start`, `Customs Close`, `Custom Code`                                                                                                   |
| Warehouse      | `DSV Indoor`, `DSV Outdoor`, `DSV MZD`, `DSV Kizad`, `JDN MZD`, `JDN Waterfront`, `AAA Storage`, `ZENER (WH)`, `Hauler DG Storage`, `Vijay Tanks` |
| MOSB           | `MOSB`                                                                                                                                            |
| Site           | `SHU`, `MIR`, `DAS`, `AGI`                                                                                                                        |
| Completion     | `FINAL DELIVERY`                                                                                                                                  |

### 적용 규칙

* `POD` 기반으로 **Port/Air node**
* `Customs Start/Close`로 **Customs node 상태**
* warehouse date 중 non-null 있으면 **WH node visit**
* `MOSB` non-null이면 **MOSB visit**
* `SHU/MIR/DAS/AGI` 중 non-null이면 **actual site arrival**
* `FINAL DELIVERY`는 site node가 아니라 **done 상태**

---

# 4) 가장 중요한 구분: `DOC_*` vs `SHU/MIR/DAS/AGI`

이 부분을 잘못 쓰면 맵이 틀어집니다.

## `DOC_*`

* 계획/지정 목적지
* 아직 안 도착했어도 들어갈 수 있음
* route planning에 사용

## `SHU/MIR/DAS/AGI`

* 실제 현장 도착 날짜
* actual route / delivered 상태에 사용

### 적용 원칙

```text id="hvdc-site-rule-01"
Global planned destination = DOC_*
UAE actual destination = SHU/MIR/DAS/AGI
```

### 시트 직접 확인값

* `DOC_SHU 368`
* `DOC_MIR 325`
* `DOC_DAS 297`
* `DOC_AGI 281`

실제 site date는

* `SHU 381`
* `MIR 333`
* `DAS 294`
* `AGI 234`

즉 **계획과 실제는 다릅니다.**
그래서 두 값을 섞으면 안 됩니다.

---

# 5) Flow Code를 시트에서 어떻게 복원하나

문서 규칙은 아래와 같습니다.

* `MIR/SHU`

  * warehouse 필요 없음 → **Flow 1**
  * warehouse 필요 → **Flow 2**
* `AGI/DAS`

  * warehouse 없음 + MOSB 필수 → **Flow 3**
  * warehouse 있음 + MOSB → **Flow 4**  

## 시트에서 복원하는 실제 로직

```text id="hvdc-flow-rebuild-01"
site = DOC_* 또는 actual site
wh_any = warehouse 컬럼 중 하나라도 날짜 존재
mosb_any = MOSB 날짜 존재
```

### 추천 로직

```text id="hvdc-flow-rebuild-02"
if final_site in [SHU, MIR]:
    if wh_any: flow = 2
    else: flow = 1

if final_site in [DAS, AGI]:
    if wh_any or mosb_any: flow = 4 또는 3
    if wh_any: flow = 4
    else: flow = 3
```

### 중요한 예외

`AGI/DAS`는 MOSB leg 강제입니다.
따라서 `DOC_DAS` 또는 `DOC_AGI`가 있는데 `MOSB`가 비어 있으면:

* planned route는 `via MOSB`
* actual state는 `MOSB pending`
  으로 잡아야 합니다.  

---

# 6) 이 시트 기준으로 실제 path를 만드는 방법

## A. Global path 생성

각 row에서 아래 path를 만듭니다.

```text id="hvdc-global-path-01"
COE/POL → POD → nominated site
```

예:

```text id="hvdc-global-path-02"
FRANCE / Le Havre → Mina Zayed → MIR / AGI
KOREA / Dangjin → Jebel Ali → SHU / DAS
```

### 노드

* Origin region
* Origin port
* UAE POD
* Final site cluster

### 간선

* Origin → POD
* POD → Site

여기서 `WH`는 line style 속성으로만 표현합니다.

---

## B. UAE Ops path 생성

각 row에서 아래 path를 만듭니다.

```text id="hvdc-uae-path-01"
POD → Customs → (WH) → (MOSB) → Site
```

### 실제 생성 규칙

1. `POD`로 entry node 결정
2. `Customs Start/Close` 있으면 customs node 통과
3. warehouse 컬럼 중 날짜 있으면 해당 warehouse node 포함
4. `MOSB` 있으면 MOSB 포함
5. `SHU/MIR/DAS/AGI` 중 날짜 있는 site로 종료

### 예시

```text id="hvdc-uae-path-02"
Khalifa Port → Khalifa Customs → DSV Indoor → SHU
Mina Zayed → MZ Customs → MOSB → AGI
Khalifa Port → Khalifa Customs → DSV Outdoor → MOSB → DAS
```

---

# 7) 노드 표준화가 필요합니다

시트에는 warehouse/location 컬럼이 많아서 그대로 쓰면 노드가 너무 많아집니다.

## 권장 표준화

| 원본 컬럼                                                           | 맵 노드               |
| --------------------------------------------------------------- | ------------------ |
| `DSV Indoor`                                                    | DSV Indoor         |
| `DSV Outdoor`                                                   | DSV Outdoor        |
| `DSV MZD`, `JDN MZD`                                            | MZ Yard            |
| `DSV Kizad`                                                     | KIZAD WH           |
| `AAA Storage`, `ZENER (WH)`, `Hauler DG Storage`, `Vijay Tanks` | Special WH cluster |
| `MOSB`                                                          | MOSB               |

### Customs도 표준화

| POD                 | Customs node              |
| ------------------- | ------------------------- |
| `Khalifa port`      | Khalifa Customs           |
| `Mina Zayed`        | Mina Zayed Customs        |
| `Jebel Ali`         | Dubai / Jebel Ali Customs |
| `Abu Dhabi Airport` | AUH Customs               |

---

# 8) 실제 적용 순서

## 1단계: row 기준 정리

* `SCT SHIP NO.`를 unique key
* `DOC_*`로 planned site array 생성
* `site date`로 actual site 생성
* `warehouse date` array 생성
* `mosb flag` 생성

## 2단계: path 두 개 생성

* `global_path`
* `uae_ops_path`

## 3단계: flow code 복원

* Flow 1~4
* Flow 5는 review

## 4단계: 맵용 JSON 생성

```json id="ycd30l"
{
  "shipment_id": "...",
  "global_path": [...],
  "uae_ops_path": [...],
  "flow_code": 4,
  "site": "AGI",
  "pod": "Mina Zayed",
  "wh_nodes": ["DSV Outdoor"],
  "mosb": true,
  "status": "in_transit"
}
```

---

# 9) 시트 직접 확인 기준으로 바로 적용 가능한 운영 해석

시트 직접 확인 결과 route 분류를 단순화하면 대략 아래처럼 나옵니다.

| route class            | rows |
| ---------------------- | ---: |
| Direct→Site            |  330 |
| WH→Site                |  195 |
| MOSB→Site              |  202 |
| WH→MOSB→Site           |  157 |
| In Transit/Undelivered |    9 |

이 값은 아주 중요합니다.

왜냐하면 맵이 지금처럼 `WH 중심`으로 보이면,
실제론 `Direct→Site + MOSB→Site`가 큰 비중인데도 잘못 읽히기 때문입니다.

---

# 10) 최종 적용 규칙 한 줄

```text id="hvdc-apply-rule-01"
Global  = COE/POL/POD/DOC_* 중심
UAE Ops = POD/Customs/WH/MOSB/SHU~AGI 중심
```

그리고 가장 중요한 실무 규칙은 이것입니다.

```text id="hvdc-apply-rule-02"
DOC_* = 계획
SHU~AGI = 실제
WH = 선택 staging
MOSB = AGI/DAS 필수 경유
FINAL DELIVERY = 완료 플래그
```

---

# 11) 바로 실행 가능한 구현 체크리스트

* `hvdc all status`만으로 두 모드 생성
* `wh status`는 보조 KPI/재고용만 사용
* `DOC_*`와 `site actual date` 절대 혼용 금지
* `POD → customs` 매핑 테이블 고정
* `warehouse columns` 표준화 후 노드 축소
* `AGI/DAS + no MOSB`는 `MOSB pending`로 표시

---

## 최종 한 줄

**`hvdc all status` 시트는 이미 Global과 UAE Ops 두 맵을 동시에 만들 수 있는 구조입니다. 문제는 데이터가 없는 게 아니라, 컬럼을 잘못 섞어 써서 WH 중심처럼 보였다는 점입니다.**

원하시면 다음 답변에서 바로
**`hvdc all status → map JSON 변환 규칙`을 Python 코드로 작성**해드리겠습니다.
