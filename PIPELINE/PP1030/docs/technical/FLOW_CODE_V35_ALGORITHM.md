# Flow Code v3.5 알고리즘 상세 문서

**버전**: v3.5  
**작성일**: 2025-10-31  
**프로젝트**: HVDC Logistics Pipeline - Stage 3 Report Generation  
**관련 파일**: `scripts/stage3_report/report_generator.py`, `scripts/stage3_report/hvdc_excel_reporter_final_sqm_rev.py`

---

## 📋 목차

1. [개요](#개요)
2. [알고리즘 개요](#알고리즘-개요)
3. [상세 계산 로직](#상세-계산-로직)
4. [도메인 룰 (AGI/DAS 강제)](#도메인-룰-agi-das-강제)
5. [예외 케이스 처리 (Flow 5)](#예외-케이스-처리-flow-5)
6. [데이터 구조 및 필드](#데이터-구조-및-필드)
7. [우선순위 및 평가 순서](#우선순위-및-평가-순서)
8. [예제 케이스](#예제-케이스)
9. [검증 및 로깅](#검증-및-로깅)
10. [구현 참고사항](#구현-참고사항)

---

## 개요

### 목적

Flow Code v3.5는 HVDC 프로젝트의 물류 흐름을 0~5 범위로 분류하는 알고리즘입니다. 이전 버전(v3.4)의 0~4 범위에서 **Flow 5 (혼합/미완료 케이스)**를 추가하고, **AGI/DAS 도메인 룰**을 적용하여 실제 물류 운영 규칙을 반영합니다.

### 주요 변경사항

| 항목 | v3.4 | v3.5 |
|------|------|------|
| Flow Code 범위 | 0~4 | **0~5** |
| 계산 방식 | 산술 계산 + clip | **관측 기반 규칙 적용** |
| AGI/DAS 처리 | 없음 | **도메인 룰 강제 적용** |
| 혼합 케이스 | 없음 | **Flow 5로 명시적 분류** |
| 원본 값 보존 | 없음 | **FLOW_CODE_ORIG 컬럼** |
| 오버라이드 추적 | 없음 | **FLOW_OVERRIDE_REASON 컬럼** |

### 비즈니스 규칙

1. **AGI/DAS는 MOSB 레그 필수**: Final_Location이 AGI 또는 DAS인 경우, Flow Code는 반드시 3 이상이어야 함 (MOSB 레그 포함)
2. **MIR/SHU 직송 허용**: MIR/SHU는 Port → Site 직접 배송 가능 (Flow 1)
3. **혼합/미완료 케이스 분류**: 비정상적인 데이터 패턴은 Flow 5로 분류

---

## 알고리즘 개요

### 전체 처리 흐름

```
[입력 데이터]
    ↓
[1단계] 필드 검증 및 전처리
    ↓
[2단계] 관측값 계산 (WH 개수, MOSB 존재, Site 존재)
    ↓
[3단계] 기본 Flow Code 계산 (0~4)
    ↓
[4단계] AGI/DAS 도메인 오버라이드 (0/1/2 → 3)
    ↓
[5단계] 혼합 케이스 처리 (→ 5)
    ↓
[6단계] 검증 및 최종 반영
    ↓
[출력] FLOW_CODE, FLOW_DESCRIPTION, FLOW_CODE_ORIG, FLOW_OVERRIDE_REASON
```

### Flow Code 정의

| Flow Code | 설명 | 패턴 | 조건 |
|-----------|------|------|------|
| **0** | Pre Arrival | - | Status_Location에 "Pre Arrival" 포함 |
| **1** | Port → Site | 직접 배송 | WH=0, MOSB=0, Pre Arrival 아님 |
| **2** | Port → WH → Site | 창고 경유 | WH≥1, MOSB=0, Pre Arrival 아님 |
| **3** | Port → MOSB → Site | MOSB 경유 | WH=0, MOSB=1, Pre Arrival 아님<br>**또는** AGI/DAS 강제 승급 |
| **4** | Port → WH → MOSB → Site | 창고+MOSB 경유 | WH≥1, MOSB=1, Pre Arrival 아님 |
| **5** | Mixed/Waiting/Incomplete | 혼합/미완료 | MOSB 있으나 Site 없음<br>**또는** WH 2개 이상 + MOSB 없음 |

---

## 상세 계산 로직

### 단계 1: 필드 검증 및 전처리

#### 1.1 필수 컬럼 검증

```python
required_cols = ["Status_Location"] + warehouse_columns + site_columns
missing_cols = [c for c in required_cols if c not in combined_data.columns]

if missing_cols:
    logger.warning(f"필수 컬럼 누락 (기본값 사용): {missing_cols}")
    # 기본값으로 계속 진행
```

**처리 방식**:
- 필수 컬럼이 없으면 경고 로그 출력
- 기본값(False, 0, NaN)으로 처리 계속 진행
- 파이프라인 중단 없이 실행

#### 1.2 창고/오프쇼어 컬럼 분리

```python
WH_COLS = [w for w in warehouse_columns if w != "MOSB"]
MOSB_COLS = [w for w in warehouse_columns if w == "MOSB"]
```

**컬럼 분류 예시**:
- **WH_COLS**: `['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'DSV Outdoor', 'DSV MZP', 'AAA Storage', 'Hauler Indoor', 'JDN MZD']`
- **MOSB_COLS**: `['MOSB']`

**이유**: MOSB는 일반 창고와 다른 오프쇼어 시설이므로 별도 처리

#### 1.3 데이터 정규화

```python
for col in WH_COLS + MOSB_COLS:
    if col in combined_data.columns:
        combined_data[col] = combined_data[col].replace({0: np.nan, "": np.nan})
```

**목적**: 0과 빈 문자열을 NaN으로 통일하여 `notna()` 계산 일관성 확보

**영향**: 
- `wh_cnt` 계산 시 정확한 창고 개수 추출
- `has_mosb` 계산 시 MOSB 존재 여부 정확히 판별

---

### 단계 2: 관측값 계산

#### 2.1 Pre Arrival 판별

```python
status_col = "Status_Location"
if status_col in combined_data.columns:
    is_pre_arrival = combined_data[status_col].astype(str).str.contains(
        "Pre Arrival", case=False, na=False
    )
else:
    is_pre_arrival = pd.Series(False, index=combined_data.index)
    logger.warning(f"'{status_col}' 컬럼 없음 - Pre Arrival 판별 불가")
```

**로직**:
- `Status_Location` 컬럼에서 "Pre Arrival" 문자열 검색 (대소문자 무시)
- 매칭되면 `is_pre_arrival = True`
- 컬럼이 없으면 기본값 `False` 사용

#### 2.2 창고 개수 계산 (wh_cnt)

```python
wh_cnt = (
    combined_data[WH_COLS].notna().sum(axis=1)
    if WH_COLS
    else pd.Series(0, index=combined_data.index)
)
```

**계산 방식**:
- 각 행에서 WH_COLS 컬럼들 중 NaN이 아닌 값의 개수를 세어 합산
- 예: `DSV Indoor=2024-01-01`, `DSV Outdoor=2024-01-02`, `DHL WH=NaN` → `wh_cnt = 2`

**예외 처리**: WH_COLS가 비어 있으면 모든 행에 0 할당

#### 2.3 MOSB 존재 여부 계산 (has_mosb)

```python
has_mosb = (
    combined_data[MOSB_COLS].notna().any(axis=1)
    if MOSB_COLS
    else pd.Series(False, index=combined_data.index)
)
```

**계산 방식**:
- 각 행에서 MOSB_COLS 컬럼들 중 하나라도 NaN이 아니면 `has_mosb = True`
- 예: `MOSB=2024-01-01` → `has_mosb = True`

**예외 처리**: MOSB_COLS가 비어 있으면 모든 행에 False 할당

#### 2.4 Site 존재 여부 계산 (has_site)

```python
SITE_COLS = site_columns if hasattr(self, "site_columns") else []
has_site = (
    combined_data[SITE_COLS].notna().any(axis=1)
    if SITE_COLS
    else pd.Series(True, index=combined_data.index)
)
```

**계산 방식**:
- 각 행에서 SITE_COLS 컬럼들 중 하나라도 NaN이 아니면 `has_site = True`
- Site 컬럼이 없으면 기본값 `True` 사용 (혼합 케이스 판별에서 제외)

**Site 컬럼 예시**: `['MIR', 'SHU', 'DAS', 'AGI']`

---

### 단계 3: 기본 Flow Code 계산 (0~4)

#### 3.1 초기화

```python
flow = pd.Series(0, index=combined_data.index, dtype="int64")
flow_desc = pd.Series("", index=combined_data.index, dtype="object")
```

모든 행을 기본값 0으로 초기화

#### 3.2 Flow 0: Pre Arrival

```python
flow[is_pre_arrival] = 0
flow_desc[is_pre_arrival] = "Flow 0: Pre Arrival"
```

**조건**: `Status_Location`에 "Pre Arrival" 포함

**의미**: 아직 도착하지 않았거나 입고 전 상태

#### 3.3 Flow 1: Port → Site (직접 배송)

```python
not_pre = ~is_pre_arrival
mask_1 = not_pre & (wh_cnt == 0) & (~has_mosb)
flow[mask_1] = 1
flow_desc[mask_1] = "Flow 1: Port → Site"
```

**조건**:
- Pre Arrival 아님 (`not_pre = True`)
- 창고 경유 없음 (`wh_cnt == 0`)
- MOSB 경유 없음 (`has_mosb = False`)

**의미**: 포트에서 현장으로 직접 배송 (MIR/SHU 등 허용)

#### 3.4 Flow 2: Port → WH → Site (창고 경유)

```python
mask_2 = not_pre & (wh_cnt >= 1) & (~has_mosb)
flow[mask_2] = 2
flow_desc[mask_2] = "Flow 2: Port → WH → Site"
```

**조건**:
- Pre Arrival 아님
- 창고 1개 이상 경유 (`wh_cnt >= 1`)
- MOSB 경유 없음

**의미**: 포트 → 창고 → 현장 배송 (일반 경유)

#### 3.5 Flow 3: Port → MOSB → Site (MOSB 경유)

```python
mask_3 = not_pre & (wh_cnt == 0) & has_mosb
flow[mask_3] = 3
flow_desc[mask_3] = "Flow 3: Port → MOSB → Site"
```

**조건**:
- Pre Arrival 아님
- 창고 경유 없음 (`wh_cnt == 0`)
- MOSB 경유 (`has_mosb = True`)

**의미**: 포트 → MOSB(오프쇼어) → 현장 배송 (AGI/DAS 주로)

**참고**: 이후 AGI/DAS 도메인 룰에서 0/1/2가 3으로 승급될 수 있음

#### 3.6 Flow 4: Port → WH → MOSB → Site (창고+MOSB 경유)

```python
mask_4 = not_pre & (wh_cnt >= 1) & has_mosb
flow[mask_4] = 4
flow_desc[mask_4] = "Flow 4: Port → WH → MOSB → Site"
```

**조건**:
- Pre Arrival 아님
- 창고 1개 이상 경유 (`wh_cnt >= 1`)
- MOSB 경유 (`has_mosb = True`)

**의미**: 포트 → 창고 → MOSB → 현장 배송 (복합 경유)

---

### 단계 4: AGI/DAS 도메인 오버라이드

#### 4.1 Final_Location 컬럼 찾기

```python
final_col_candidates = [
    "Final_Location",
    "Final location",
    "Final_Location_Site",
    "Site_Final"
]
final_col = None
for cand in final_col_candidates:
    if cand in combined_data.columns:
        final_col = cand
        break
```

**목적**: 데이터 소스별 컬럼명 차이 대응 (유연성 확보)

**우선순위**: 첫 번째 매칭되는 컬럼 사용

#### 4.2 원본 값 보존

```python
combined_data["FLOW_CODE_ORIG"] = flow.copy()
```

**목적**: 오버라이드 전 원본 Flow Code 값을 보존하여 추적 가능

**용도**: 
- 디버깅
- 비즈니스 분석
- 규칙 변경 영향 평가

#### 4.3 AGI/DAS 강제 승급

```python
if final_col is not None:
    final_location = combined_data[final_col].astype(str).str.upper()
    is_agi_das = final_location.isin(["AGI", "DAS"])
    
    # AGI/DAS가 0/1/2인 경우 강제 3 승급
    need_force = is_agi_das & flow.isin([0, 1, 2])
    flow[need_force] = 3
    flow_desc[need_force] = "Flow 3: Port → MOSB → Site (AGI/DAS forced)"
    combined_data.loc[need_force, "FLOW_OVERRIDE_REASON"] = "AGI/DAS requires MOSB leg"
    
    if need_force.sum() > 0:
        logger.info(f" AGI/DAS 강제 승급: {need_force.sum()}건 (0/1/2 → 3)")
else:
    logger.warning("Final_Location 컬럼을 찾을 수 없음 - AGI/DAS 강제 승급 불가")
    combined_data["FLOW_OVERRIDE_REASON"] = np.nan
```

**도메인 룰**: 
> **AGI/DAS는 MOSB 레그가 필수입니다.**  
> Final_Location이 AGI 또는 DAS인 경우, Flow Code가 0, 1, 2이면 무조건 3으로 승급합니다.

**처리 순서**:
1. Final_Location 값 대문자 변환
2. "AGI" 또는 "DAS" 여부 확인
3. 현재 Flow Code가 0, 1, 2인지 확인
4. 조건 만족 시 Flow Code를 3으로 변경
5. 설명을 "AGI/DAS forced"로 변경
6. 오버라이드 사유 기록

**예시**:
- 원래 Flow 1 (Port → Site) + Final_Location = "AGI" → Flow 3으로 승급
- 원래 Flow 2 (Port → WH → Site) + Final_Location = "DAS" → Flow 3으로 승급
- 원래 Flow 3 이상인 경우 변경 없음 (이미 MOSB 레그 포함)

**비즈니스 근거**: AGI/DAS 현장은 오프쇼어 시설이므로 반드시 MOSB를 경유해야 함

---

### 단계 5: 혼합 케이스 처리 (Flow 5)

#### 5.1 Flow 5 조건 1: MOSB 있으나 Site 없음

```python
cond_mosb_no_site = has_mosb & (~has_site)
```

**조건**:
- MOSB 경유 (`has_mosb = True`)
- Site 도착 없음 (`has_site = False`)

**의미**: 
- MOSB에 도착했으나 현장으로 전달되지 않음
- 대기 중이거나 미완료 상태

**비즈니스 케이스**: 
- 현장 보관 공간 부족으로 대기 중
- 데이터 입력 누락

#### 5.2 Flow 5 조건 2: WH 2개 이상 + MOSB 없음

```python
cond_weird_wh = (wh_cnt >= 2) & (~has_mosb) & (~is_pre_arrival)
```

**조건**:
- 창고 2개 이상 경유 (`wh_cnt >= 2`)
- MOSB 경유 없음 (`has_mosb = False`)
- Pre Arrival 아님

**의미**: 
- 비정상적인 다중 창고 경유
- 데이터 오류 또는 특수 케이스

**비즈니스 케이스**:
- 창고 간 이동이 여러 번 발생
- 데이터 입력 오류로 중복 기록

#### 5.3 Flow 5 최종 적용

```python
need_5 = cond_mosb_no_site | cond_weird_wh

flow[need_5] = 5
flow_desc[need_5] = "Flow 5: Mixed / Waiting / Incomplete leg"
```

**로직**: 두 조건 중 하나라도 만족하면 Flow 5로 분류

**우선순위**: 
- Flow 5는 도메인 오버라이드(4단계) 이후에 적용
- 따라서 AGI/DAS 강제 승급된 경우에도 Flow 5 조건이 만족되면 5로 변경됨

---

### 단계 6: 최종 반영 및 검증

#### 6.1 최종 컬럼 생성

```python
combined_data["FLOW_CODE"] = flow.astype("int64")
combined_data["FLOW_DESCRIPTION"] = flow_desc
```

**생성 컬럼**:
- `FLOW_CODE`: 최종 Flow Code (0~5)
- `FLOW_DESCRIPTION`: Flow Code 설명
- `FLOW_CODE_ORIG`: 오버라이드 전 원본 Flow Code (4단계에서 생성)
- `FLOW_OVERRIDE_REASON`: 오버라이드 사유 (4단계에서 생성)

#### 6.2 분포 검증

```python
dist = combined_data["FLOW_CODE"].value_counts().sort_index()
logger.info(f"[FlowCode v3.5] 분포: {dict(dist)}")
```

**출력 예시**:
```
[FlowCode v3.5] 분포: {0: 173, 1: 3681, 2: 3799, 3: 430, 4: 524, 5: 388}
```

#### 6.3 범위 검증

```python
invalid_codes = combined_data[
    ~combined_data["FLOW_CODE"].isin([0, 1, 2, 3, 4, 5])
]
if len(invalid_codes) > 0:
    logger.error(f"⚠️ 잘못된 Flow Code 발견: {invalid_codes['FLOW_CODE'].unique()}")
```

**목적**: 0~5 범위를 벗어난 값 감지 및 경고

**예외**: 이상값 발견 시 에러 로그 출력 (파이프라인 중단 없음)

---

## 도메인 룰 (AGI/DAS 강제)

### 룰 정의

> **AGI/DAS는 MOSB 레그가 필수입니다.**  
> Final_Location이 AGI 또는 DAS인 경우, Flow Code는 반드시 3 이상이어야 합니다.

### 우선순위

**Priority: 999** (최우선순위)

- 도메인 룰은 기본 계산(3단계) 이후에 적용
- 혼합 케이스 처리(5단계) 이전에 적용
- 하지만 Flow 5 조건이 만족되면 도메인 오버라이드 결과를 덮어쓸 수 있음

### 처리 시나리오

| 시나리오 | 원본 Flow | Final_Location | 결과 Flow | 설명 |
|----------|-----------|----------------|-----------|------|
| 1 | 0 (Pre Arrival) | AGI | **3** | Pre Arrival이지만 AGI이므로 강제 승급 |
| 2 | 1 (Port → Site) | AGI | **3** | 직송으로 보였지만 AGI이므로 MOSB 경유로 승급 |
| 3 | 2 (Port → WH → Site) | DAS | **3** | 창고 경유였지만 DAS이므로 MOSB 경유로 승급 |
| 4 | 3 (Port → MOSB → Site) | AGI | **3** | 이미 MOSB 경유이므로 변경 없음 |
| 5 | 4 (Port → WH → MOSB → Site) | DAS | **4** | 이미 MOSB 경유이므로 변경 없음 |
| 6 | 1 (Port → Site) | MIR | **1** | MIR은 AGI/DAS가 아니므로 변경 없음 |

### 오버라이드 추적

오버라이드된 레코드는 다음 컬럼에 정보가 기록됩니다:

- `FLOW_CODE_ORIG`: 오버라이드 전 원본 Flow Code
- `FLOW_OVERRIDE_REASON`: "AGI/DAS requires MOSB leg"

**분석 용도**:
- AGI/DAS 강제 승급된 레코드 개수 파악
- 원본 Flow Code 분포 분석
- 비즈니스 규칙 준수 검증

---

## 예외 케이스 처리 (Flow 5)

### Flow 5 정의

**Flow 5: Mixed / Waiting / Incomplete leg**

비정상적인 데이터 패턴이나 미완료 상태를 나타냅니다.

### 조건 1: MOSB 있으나 Site 없음

**패턴**: `has_mosb = True` AND `has_site = False`

**비즈니스 의미**:
- MOSB(오프쇼어)에 도착했으나 현장으로 전달되지 않음
- 현장 보관 공간 부족으로 대기 중
- 데이터 입력 누락

**예시 데이터**:
```
MOSB: 2024-01-15
MIR: NaN
SHU: NaN
DAS: NaN
AGI: NaN
Final_Location: NaN
```

**처리**: Flow 5로 분류

### 조건 2: WH 2개 이상 + MOSB 없음

**패턴**: `wh_cnt >= 2` AND `has_mosb = False` AND `not is_pre_arrival`

**비즈니스 의미**:
- 창고 간 이동이 비정상적으로 많음
- 데이터 입력 오류 가능성
- 특수한 창고 간 이동 케이스

**예시 데이터**:
```
DSV Indoor: 2024-01-10
DSV Outdoor: 2024-01-12
DHL WH: 2024-01-14
MOSB: NaN
```

**처리**: Flow 5로 분류

### Flow 5 우선순위

Flow 5는 다음 순서로 적용됩니다:

1. **기본 Flow 계산** (0~4) → 3단계
2. **AGI/DAS 도메인 오버라이드** (0/1/2 → 3) → 4단계
3. **Flow 5 처리** (→ 5) → 5단계

**중요**: Flow 5 조건이 만족되면 AGI/DAS 강제 승급 결과를 덮어씁니다.

**예시**:
- 원래 Flow 1 + Final_Location = "AGI" → Flow 3으로 승급 (4단계)
- 하지만 `has_mosb = True`, `has_site = False` → Flow 5로 변경 (5단계)

---

## 데이터 구조 및 필드

### 입력 필드

#### 필수 필드

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `Status_Location` | str | 상태 및 위치 정보 | "Pre Arrival", "MIR Site", "DSV Indoor" |
| `warehouse_columns` | list | 창고 컬럼 목록 | `['DHL WH', 'DSV Indoor', ..., 'MOSB']` |
| `site_columns` | list | 현장 컬럼 목록 | `['MIR', 'SHU', 'DAS', 'AGI']` |

#### 선택 필드

| 필드명 | 타입 | 설명 | 우선순위 |
|--------|------|------|----------|
| `Final_Location` | str | 최종 위치 | 1 |
| `Final location` | str | 최종 위치 (대체명) | 2 |
| `Final_Location_Site` | str | 최종 위치 (대체명) | 3 |
| `Site_Final` | str | 최종 위치 (대체명) | 4 |

### 출력 필드

| 필드명 | 타입 | 설명 | 값 범위/예시 |
|--------|------|------|--------------|
| `FLOW_CODE` | int64 | 최종 Flow Code | 0, 1, 2, 3, 4, 5 |
| `FLOW_DESCRIPTION` | str | Flow Code 설명 | "Flow 0: Pre Arrival", "Flow 3: Port → MOSB → Site (AGI/DAS forced)" |
| `FLOW_CODE_ORIG` | int64 | 오버라이드 전 원본 Flow Code | 0, 1, 2, 3, 4 |
| `FLOW_OVERRIDE_REASON` | str | 오버라이드 사유 | "AGI/DAS requires MOSB leg" 또는 NaN |

### 중간 계산 필드

| 변수명 | 타입 | 설명 | 계산 방식 |
|--------|------|------|-----------|
| `is_pre_arrival` | bool Series | Pre Arrival 여부 | `Status_Location.str.contains("Pre Arrival")` |
| `wh_cnt` | int Series | 창고 개수 | `WH_COLS.notna().sum(axis=1)` |
| `has_mosb` | bool Series | MOSB 존재 여부 | `MOSB_COLS.notna().any(axis=1)` |
| `has_site` | bool Series | Site 존재 여부 | `SITE_COLS.notna().any(axis=1)` |
| `is_agi_das` | bool Series | AGI/DAS 여부 | `Final_Location.str.upper().isin(["AGI", "DAS"])` |

---

## 우선순위 및 평가 순서

### 전체 평가 순서

```
1. 필드 검증 및 전처리
   └─ 필수 컬럼 확인
   └─ 창고/MOSB 분리
   └─ 데이터 정규화 (0, "" → NaN)

2. 관측값 계산
   └─ is_pre_arrival 계산
   └─ wh_cnt 계산
   └─ has_mosb 계산
   └─ has_site 계산

3. 기본 Flow Code 계산 (0~4)
   └─ Flow 0: Pre Arrival
   └─ Flow 1: Port → Site (WH=0, MOSB=0)
   └─ Flow 2: Port → WH → Site (WH≥1, MOSB=0)
   └─ Flow 3: Port → MOSB → Site (WH=0, MOSB=1)
   └─ Flow 4: Port → WH → MOSB → Site (WH≥1, MOSB=1)

4. AGI/DAS 도메인 오버라이드 (Priority: 999)
   └─ Final_Location 확인
   └─ 원본 값 보존 (FLOW_CODE_ORIG)
   └─ AGI/DAS 강제 승급 (0/1/2 → 3)

5. 혼합 케이스 처리 (→ Flow 5)
   └─ 조건 1: MOSB 있으나 Site 없음
   └─ 조건 2: WH 2개 이상 + MOSB 없음
   └─ Flow 5 적용

6. 최종 반영 및 검증
   └─ FLOW_CODE, FLOW_DESCRIPTION 생성
   └─ 분포 검증
   └─ 범위 검증 (0~5)
```

### 우선순위 매트릭스

| 단계 | 우선순위 | 설명 | 덮어쓰기 가능 여부 |
|------|----------|------|-------------------|
| 기본 계산 (0~4) | 100~150 | 관측 기반 기본 분류 | 도메인 오버라이드에 의해 덮어쓰기 가능 |
| AGI/DAS 오버라이드 | **999** | 도메인 룰 강제 적용 | Flow 5 처리에 의해 덮어쓰기 가능 |
| Flow 5 처리 | 150 | 혼합 케이스 분류 | 최종 적용 (덮어쓰기 불가) |

### 특수 케이스 처리 순서

**케이스 1: AGI/DAS + Flow 5 조건 동시 만족**

```
1. 기본 계산 → Flow 1 (Port → Site)
2. AGI/DAS 오버라이드 → Flow 3 (MOSB 경유로 승급)
3. Flow 5 조건 확인:
   - has_mosb = True
   - has_site = False
   → Flow 5로 최종 변경
```

**결과**: Flow 5 (AGI/DAS 강제 승급 결과가 Flow 5에 의해 덮어쓰기됨)

---

## 예제 케이스

### 예제 1: 일반 창고 경유 (Flow 2)

**입력 데이터**:
```
Status_Location: "DSV Indoor"
DSV Indoor: 2024-01-10
SHU: 2024-01-15
Final_Location: "SHU"
```

**계산 과정**:
1. `is_pre_arrival = False` ("Pre Arrival" 미포함)
2. `wh_cnt = 1` (DSV Indoor 1개)
3. `has_mosb = False` (MOSB 없음)
4. `has_site = True` (SHU 있음)
5. 기본 계산: `mask_2 = True` → **Flow 2**
6. AGI/DAS 확인: Final_Location = "SHU" (AGI/DAS 아님) → 변경 없음
7. Flow 5 조건: 불만족 → 변경 없음

**결과**: `FLOW_CODE = 2`, `FLOW_DESCRIPTION = "Flow 2: Port → WH → Site"`

---

### 예제 2: AGI 강제 승급 (Flow 1 → 3)

**입력 데이터**:
```
Status_Location: "MIR Site"
MIR: 2024-01-10
Final_Location: "AGI"
```

**계산 과정**:
1. `is_pre_arrival = False`
2. `wh_cnt = 0` (창고 없음)
3. `has_mosb = False` (MOSB 없음)
4. `has_site = True` (MIR 있음)
5. 기본 계산: `mask_1 = True` → **Flow 1**
6. 원본 보존: `FLOW_CODE_ORIG = 1`
7. AGI/DAS 확인: Final_Location = "AGI" → `is_agi_das = True`
8. 강제 승급: `need_force = True` → **Flow 3**
9. 오버라이드 기록: `FLOW_OVERRIDE_REASON = "AGI/DAS requires MOSB leg"`
10. Flow 5 조건: 불만족 → 변경 없음

**결과**: 
- `FLOW_CODE = 3`
- `FLOW_DESCRIPTION = "Flow 3: Port → MOSB → Site (AGI/DAS forced)"`
- `FLOW_CODE_ORIG = 1`
- `FLOW_OVERRIDE_REASON = "AGI/DAS requires MOSB leg"`

---

### 예제 3: 혼합 케이스 (Flow 5)

**입력 데이터**:
```
Status_Location: "MOSB"
MOSB: 2024-01-15
MIR: NaN
SHU: NaN
DAS: NaN
AGI: NaN
Final_Location: NaN
```

**계산 과정**:
1. `is_pre_arrival = False`
2. `wh_cnt = 0` (창고 없음)
3. `has_mosb = True` (MOSB 있음)
4. `has_site = False` (Site 없음)
5. 기본 계산: `mask_3 = True` → **Flow 3**
6. AGI/DAS 확인: Final_Location = NaN → 변경 없음
7. Flow 5 조건 확인:
   - `cond_mosb_no_site = True` (MOSB 있으나 Site 없음)
   - → **Flow 5**

**결과**: `FLOW_CODE = 5`, `FLOW_DESCRIPTION = "Flow 5: Mixed / Waiting / Incomplete leg"`

---

### 예제 4: 다중 창고 경유 (Flow 5)

**입력 데이터**:
```
Status_Location: "DHL WH"
DSV Indoor: 2024-01-10
DSV Outdoor: 2024-01-12
DHL WH: 2024-01-14
MOSB: NaN
SHU: 2024-01-20
Final_Location: "SHU"
```

**계산 과정**:
1. `is_pre_arrival = False`
2. `wh_cnt = 3` (DSV Indoor, DSV Outdoor, DHL WH)
3. `has_mosb = False` (MOSB 없음)
4. `has_site = True` (SHU 있음)
5. 기본 계산: `mask_2 = True` → **Flow 2** (일반적으로는 Flow 2)
6. AGI/DAS 확인: Final_Location = "SHU" → 변경 없음
7. Flow 5 조건 확인:
   - `cond_weird_wh = True` (WH 2개 이상 + MOSB 없음)
   - → **Flow 5**

**결과**: `FLOW_CODE = 5`, `FLOW_DESCRIPTION = "Flow 5: Mixed / Waiting / Incomplete leg"`

---

### 예제 5: AGI + Flow 5 조건 동시 만족

**입력 데이터**:
```
Status_Location: "MOSB"
MOSB: 2024-01-15
MIR: NaN
SHU: NaN
DAS: NaN
AGI: NaN
Final_Location: "AGI"
```

**계산 과정**:
1. `is_pre_arrival = False`
2. `wh_cnt = 0` (창고 없음)
3. `has_mosb = True` (MOSB 있음)
4. `has_site = False` (Site 없음)
5. 기본 계산: `mask_3 = True` → **Flow 3**
6. AGI/DAS 확인: Final_Location = "AGI" → 이미 Flow 3이므로 변경 없음
7. Flow 5 조건 확인:
   - `cond_mosb_no_site = True` (MOSB 있으나 Site 없음)
   - → **Flow 5** (AGI 강제 승급 결과를 덮어씀)

**결과**: `FLOW_CODE = 5` (AGI 강제 승급이 Flow 5에 의해 덮어쓰기됨)

---

## 검증 및 로깅

### 검증 단계

#### 1. 필수 컬럼 검증

```python
required_cols = ["Status_Location"] + warehouse_columns + site_columns
missing_cols = [c for c in required_cols if c not in combined_data.columns]

if missing_cols:
    logger.warning(f"필수 컬럼 누락 (기본값 사용): {missing_cols}")
```

**로깅 레벨**: WARNING  
**처리**: 기본값 사용하여 계속 진행

#### 2. Flow Code 범위 검증

```python
invalid_codes = combined_data[
    ~combined_data["FLOW_CODE"].isin([0, 1, 2, 3, 4, 5])
]
if len(invalid_codes) > 0:
    logger.error(f"⚠️ 잘못된 Flow Code 발견: {invalid_codes['FLOW_CODE'].unique()}")
```

**로깅 레벨**: ERROR  
**처리**: 경고만 출력 (파이프라인 중단 없음)

#### 3. 분포 로깅

```python
dist = combined_data["FLOW_CODE"].value_counts().sort_index()
logger.info(f"[FlowCode v3.5] 분포: {dict(dist)}")
logger.info(f" Pre Arrival: {is_pre_arrival.sum()}건")
logger.info(" Flow Code 재계산 완료 (v3.5: 0~5 확장)")
```

**로깅 레벨**: INFO  
**출력 예시**:
```
[FlowCode v3.5] 분포: {0: 173, 1: 3681, 2: 3799, 3: 430, 4: 524, 5: 388}
 Pre Arrival: 173건
 Flow Code 재계산 완료 (v3.5: 0~5 확장)
```

#### 4. AGI/DAS 강제 승급 로깅

```python
if need_force.sum() > 0:
    logger.info(f" AGI/DAS 강제 승급: {need_force.sum()}건 (0/1/2 → 3)")
```

**로깅 레벨**: INFO  
**용도**: 도메인 룰 적용 건수 확인

### 검증 체크리스트

실행 후 다음 사항을 확인해야 합니다:

- [ ] Flow Code 분포에 0, 1, 2, 3, 4, 5 모두 포함되어 있는가?
- [ ] Pre Arrival 레코드가 모두 Flow 0인가?
- [ ] AGI/DAS 레코드가 Flow 3 이상인가? (0/1/2 없어야 함)
- [ ] Flow 5 레코드의 `FLOW_DESCRIPTION`이 올바른가?
- [ ] `FLOW_CODE_ORIG`가 AGI/DAS 오버라이드된 레코드에 존재하는가?
- [ ] `FLOW_OVERRIDE_REASON`이 올바르게 기록되어 있는가?
- [ ] 범위 검증에서 에러가 없는가?

---

## 구현 참고사항

### 성능 최적화

#### 벡터화 연산 사용

모든 계산은 Pandas 벡터화 연산을 사용합니다:

```python
# ✅ Good: 벡터화 연산
wh_cnt = combined_data[WH_COLS].notna().sum(axis=1)

# ❌ Bad: 반복문 사용 (느림)
# for idx in combined_data.index:
#     wh_cnt[idx] = sum(combined_data.loc[idx, WH_COLS].notna())
```

**성능**: 7,366건 처리 시간 약 0.3초

#### 메모리 효율성

- 원본 데이터 복사 최소화
- 필요한 경우에만 `.copy()` 사용
- `FLOW_CODE_ORIG` 생성 시에만 복사

### 데이터 소스 호환성

#### 컬럼명 유연성

다양한 데이터 소스의 컬럼명 차이를 대응하기 위해 후보 리스트를 사용합니다:

```python
final_col_candidates = [
    "Final_Location",
    "Final location",
    "Final_Location_Site",
    "Site_Final"
]
```

**확장 방법**: 새로운 컬럼명이 발견되면 `final_col_candidates`에 추가

### 오류 처리 전략

#### 방어적 프로그래밍

모든 단계에서 예외 상황을 고려합니다:

1. **컬럼 누락**: 기본값 사용
2. **데이터 타입 오류**: `.astype(str)` 사용
3. **빈 리스트**: 조건문으로 분기
4. **NaN 값**: `.notna()` 사용

#### 로깅 전략

- **INFO**: 정상 진행 상황
- **WARNING**: 예외 상황이지만 처리 가능
- **ERROR**: 심각한 오류 (하지만 파이프라인 중단 없음)

### 테스트 권장사항

#### 단위 테스트

각 Flow Code (0~5)에 대한 테스트 케이스 작성:

```python
def test_flow_code_0_pre_arrival():
    # Pre Arrival 케이스 테스트
    
def test_flow_code_1_direct_delivery():
    # Port → Site 케이스 테스트
    
def test_flow_code_2_warehouse_transit():
    # Port → WH → Site 케이스 테스트
    
def test_flow_code_3_mosb_transit():
    # Port → MOSB → Site 케이스 테스트
    
def test_flow_code_4_warehouse_mosb_transit():
    # Port → WH → MOSB → Site 케이스 테스트
    
def test_flow_code_5_mixed_case():
    # 혼합 케이스 테스트
    
def test_agi_das_force_upgrade():
    # AGI/DAS 강제 승급 테스트
```

#### 통합 테스트

실제 데이터로 전체 파이프라인 실행:

```python
def test_flow_code_v35_integration():
    # 실제 데이터 로드
    # Flow Code 계산
    # 분포 및 범위 검증
```

### 향후 개선 사항

#### Phase 2 (선택적)

1. **MIR/SHU 직송 구분**: Flow 1 계산 시 MIR/SHU만 허용
2. **events_count 기반 혼합 케이스 판별**: 더 정교한 Flow 5 분류
3. **AGI/DAS 직송 불허**: Flow 1에서 AGI/DAS 제외

**현재 상태**: 기본 로직으로는 모든 직송을 Flow 1로 처리 (Phase 2는 선택적 구현)

#### 추가 검증

1. **AGI/DAS 케이스 실제 데이터 확인**: Final_Location 컬럼명 정확히 확인
2. **Flow 5 케이스 상세 분석**: 388건의 Flow 5 케이스 비즈니스 룰 개선 여부 검토

---

## 부록: JSON 룰셋 매핑

### flow-rules-v3.5.json과 구현 코드 매핑

| JSON 룰 ID | 우선순위 | 구현 코드 단계 | 설명 |
|------------|----------|----------------|------|
| FLOW-000 | 100 | 3단계 | Pre Arrival → Flow 0 |
| FLOW-100 | 110 | 3단계 | Port → Site (MIR/SHU, Phase 2) |
| FLOW-200 | 120 | 3단계 | Port → WH → Site |
| FLOW-300 | 130 | 3단계 | Port → MOSB → Site |
| FLOW-400 | 140 | 3단계 | Port → WH → MOSB → Site |
| FLOW-500 | 150 | 5단계 | 혼합 케이스 → Flow 5 |
| FLOW-AGI-DAS-FORCE | **999** | 4단계 | AGI/DAS 강제 승급 |

**참고**: 현재 구현은 Phase 1만 완료되었으며, Phase 2 (MIR/SHU 직송 구분, events_count 기반 판별)는 선택적입니다.

---

## 결론

Flow Code v3.5 알고리즘은 다음과 같은 특징을 가집니다:

1. **명시적 규칙 기반**: 관측 이벤트를 기반으로 명확한 규칙 적용
2. **도메인 룰 반영**: AGI/DAS MOSB 필수 룰 강제 적용
3. **예외 케이스 처리**: 혼합/미완료 케이스를 Flow 5로 명시적 분류
4. **추적 가능성**: 원본 값 및 오버라이드 사유 보존
5. **호환성**: 다양한 데이터 소스 컬럼명 차이 대응
6. **안정성**: 방어적 프로그래밍 및 예외 처리

이 문서는 Flow Code v3.5 알고리즘의 상세한 로직과 구현 방법을 제공하여 향후 유지보수 및 확장에 도움이 됩니다.

---

**문서 버전**: v1.0  
**최종 업데이트**: 2025-10-31  
**작성자**: AI Assistant (Cursor)  
**검토**: 필요 시 사용자 검토



