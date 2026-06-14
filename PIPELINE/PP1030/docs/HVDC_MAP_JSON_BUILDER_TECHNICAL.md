# HVDC Map JSON Builder 기술문서

## 개요

`scripts/utils/build_map_json_from_hvdc_all_status.py`는 `HVDC STATUS1.xlsx`의 `hvdc all status` 시트를 읽어, 운송 건별 경로 정보와 집계 그래프를 JSON으로 생성하는 유틸리티 스크립트다. 이 문서는 현재 코드와 현재 생성된 산출물을 기준으로 스크립트의 입력 계약, 처리 흐름, 함수 역할, JSON 구조, 운영상 주의사항을 정리한다.

이 스크립트의 목적은 다음 두 가지다.

- shipment 단위로 origin -> POD -> UAE 운영 구간 -> 최종 site 경로를 구조화한다.
- 전체 shipment를 그래프 형태로 집계해 글로벌 경로와 UAE 운영 경로를 별도 JSON으로 출력한다.

기준 스크립트:

- `scripts/utils/build_map_json_from_hvdc_all_status.py`

기본 입력/출력:

- 기본 입력 Excel: `docs/HVDC STATUS1.xlsx`
- 기본 시트명: `hvdc all status`
- 기본 출력 디렉터리: `data/processed/map_json`
- 기본 출력 파일:
  - `shipment_paths.json`
  - `global_graph.json`
  - `uae_ops_graph.json`

## 실행 방법

기본 실행:

```bash
python scripts/utils/build_map_json_from_hvdc_all_status.py
```

명시적 입력/출력 지정:

```bash
python scripts/utils/build_map_json_from_hvdc_all_status.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --header-row 0 --output-dir data/processed/map_json
```

CLI 인터페이스:

- positional `excel_path`
  - 입력 Excel 파일 경로
  - 기본값: `docs/HVDC STATUS1.xlsx`
- positional `sheet_name`
  - 읽을 시트명
  - 기본값: `hvdc all status`
- option `--header-row`
  - 헤더 행 인덱스
  - 기본값: `0`
- option `--output-dir`
  - JSON 출력 디렉터리
  - 기본값: `data/processed/map_json`

## 입력 계약

스크립트는 실행 초기에 필수 컬럼 존재 여부를 검증한다. 아래 컬럼이 하나라도 없으면 예외를 발생시키고 중단한다.

- `SCT SHIP NO.`
- `MR#`
- `VENDOR`
- `CATEGORY`
- `COE`
- `POL`
- `POD`
- `SHIP MODE`
- `ETD`
- `ATD`
- `ETA`
- `ATA`
- `Customs Start`
- `Customs Close`
- `Custom Code`
- `FINAL DELIVERY`
- `CIF VALUE (A+B+C)`
- `GWT (KG)`
- `CBM`
- `QTY OF CNTR`

추가로 다음 컬럼군은 경로와 상태 계산에 직접 사용된다.

- planned site marker: `DOC_SHU`, `DOC_DAS`, `DOC_MIR`, `DOC_AGI`
- actual site visit date: `SHU`, `MIR`, `DAS`, `AGI`
- warehouse visit date:
  - `DSV Indoor`
  - `DSV Outdoor`
  - `DSV MZD`
  - `DSV Kizad`
  - `JDN MZD`
  - `JDN Waterfront`
  - `AAA Storage`
  - `ZENER (WH)`
  - `Hauler DG Storage`
  - `Vijay Tanks`
- MOSB visit date: `MOSB`

## 처리 흐름

스크립트의 전체 동작은 4단계로 나뉜다.

### 1. 입력 로드 및 시트 해석

- `build_cli_args()`가 CLI 인자를 파싱한다.
- `load_input_dataframe()`가 Excel 파일 존재 여부를 확인한다.
- 시트명 비교는 대소문자, 공백, `_`, `-` 차이를 무시하고 수행한다.
- 대상 시트가 없으면 현재 파일명과 사용 가능한 시트 목록을 포함한 예외를 발생시킨다.

### 2. 필수 컬럼 검증 및 전처리

- `validate_required_columns()`가 필수 컬럼 누락 여부를 검사한다.
- `preprocess_dataframe()`가 날짜 컬럼과 숫자 컬럼을 정규화한다.
- 날짜는 `pd.to_datetime(..., errors="coerce")`로 변환한다.
- 숫자는 `pd.to_numeric(..., errors="coerce")`로 변환한다.
- `valid_date()`는 변환된 값 중 유효한 날짜만 `YYYY-MM-DD` 문자열로 반환한다.
- `valid_date()`는 연도가 2000년 미만인 값은 placeholder 또는 오류 가능성으로 간주하고 무시한다.

### 3. row 단위 shipment path 생성

- `main()`은 `SCT SHIP NO.`가 있는 행만 처리한다.
- `build_paths_for_row()`는 각 row를 shipment 단위 구조로 변환한다.
- 이 단계에서 다음 정보가 계산된다.
  - planned site 목록
  - actual site 목록 및 actual site 날짜
  - warehouse 방문 목록
  - MOSB 방문일
  - entry node
  - customs node
  - global path 목록
  - UAE ops path 목록
  - planned / actual flow code
  - 현재 status
  - 수치 metric
  - 보조 flag

### 4. graph 집계 및 JSON 출력

- `build_graphs()`가 shipment별 path를 전체 노드/엣지 그래프로 집계한다.
- 글로벌 그래프는 origin region, origin POL, POD, site 중심으로 구성한다.
- UAE 운영 그래프는 POD, customs, warehouse, MOSB, site 중심으로 구성한다.
- `write_outputs()`가 3개 JSON 파일을 출력한다.

## 핵심 도메인 규칙

### Planned / Actual site 규칙

- `DOC_*` 컬럼은 planned site marker로 사용한다.
- 값이 비어 있지 않으면 planned site로 간주한다.
- `SHU`, `MIR`, `DAS`, `AGI` 컬럼은 actual site visit date로 사용한다.
- actual site 날짜가 존재하면 해당 site는 actual site로 간주한다.
- 실제 경로 생성 시에는 actual site가 있으면 actual site를 우선 사용하고, 없으면 planned site를 사용한다.

### AGI / DAS MOSB 규칙

- `DAS` 또는 `AGI`로 가는 경로는 MOSB leg가 필요하다고 가정한다.
- `mosb_visit`이 비어 있어도 effective site가 `DAS` 또는 `AGI`이면 UAE ops path에 `mosb:mosb`를 강제로 포함한다.
- 이 규칙은 `flow_code_from_sites_and_staging()`의 flow code 계산에도 반영된다.

### Multi-site row 규칙

- 하나의 row에 site가 여러 개면 path를 복수 생성한다.
- 그래프 집계 시 row 전체 weight를 path 수로 나누어 `1/n` 비율로 분배한다.
- 이 weight는 `shipment_count`, `allocation_weight_sum`, 금액/중량 합계에 적용된다.

### POD / Customs 매핑 규칙

- POD는 문자열 alias 매칭 기반으로 entry node를 결정한다.
- customs node도 POD alias 기반으로 결정한다.
- 현재 기본 매핑은 다음을 포함한다.
  - `khalifa`
  - `mina zayed`
  - `jebel ali`
  - `abu dhabi airport`
  - `auh`
- alias에 매칭되지 않으면 slug 기반의 동적 node id를 생성한다.
  - 예: `port:<slug>`
  - 예: `customs:<slug>`

### Status 계산 규칙

`status_from_row()`는 다음 우선순위로 현재 상태를 결정한다.

1. `FINAL DELIVERY`가 있으면 `delivered`
2. actual site가 있으면 `at_site_pending_close`
3. `MOSB` 방문이 있으면 `mosb_pending`
4. warehouse 방문이 있으면 `warehouse_staging`
5. `Customs Close`가 있으면 `customs_cleared_pending_dispatch`
6. `Customs Start`가 있으면 `customs_in_progress`
7. `ATA`가 있으면 `arrived_pending_customs`
8. 그 외는 `in_transit`

### Flow code 계산 규칙

`flow_code_from_sites_and_staging()`는 site와 warehouse/MOSB 여부를 이용해 flow code를 계산한다.

- `SHU`, `MIR`
  - warehouse 경유 없음: `1`
  - warehouse 경유 있음: `2`
- `DAS`, `AGI`
  - warehouse 경유 없음: `3`
  - warehouse 경유 있음: `4`
- 최종 site가 불명확하면 `None`

## 함수 구조

### 입력 / 전처리 계층

- `build_cli_args()`
  - CLI 인자를 정의하고 기본값을 설정한다.
- `load_input_dataframe()`
  - Excel 파일 존재 확인, 시트명 해석, DataFrame 로드를 담당한다.
- `validate_required_columns()`
  - 필수 컬럼 누락 시 예외를 발생시킨다.
- `preprocess_dataframe()`
  - 날짜/숫자 컬럼을 사전 정규화한다.

### 변환 계층

- `build_paths_for_row()`
  - row를 shipment 단위 구조로 변환하는 중심 함수다.
- `flow_code_from_sites_and_staging()`
  - site와 warehouse/MOSB 여부로 flow code를 계산한다.
- `status_from_row()`
  - row의 진행 상태를 상태 문자열로 정리한다.
- 보조 함수:
  - `has_marker()`
  - `valid_date()`
  - `safe_number()`
  - `map_pod_to_entry_node()`
  - `map_pod_to_customs_node()`
  - `region_from_coe()`
  - `choose_effective_sites()`
  - `sort_visits_by_date()`

### 집계 계층

- `build_graphs()`
  - shipment path 목록을 `global_graph`와 `uae_ops_graph`로 집계한다.
- `add_node()`
  - node registry에 node를 추가한다.
- `add_edge()`
  - source/target/route_type 기준으로 edge를 집계한다.

### 출력 계층

- `write_outputs()`
  - 3개 JSON 파일을 생성한다.
- `main()`
  - 전체 실행 흐름을 조립하는 엔트리 포인트다.

## 출력 계약

공통 출력 파일:

- `shipment_paths.json`
- `global_graph.json`
- `uae_ops_graph.json`

공통 `meta` 필드:

- `source_file`
- `sheet_name`
- `row_count`
- `grain`
- `rules`
- `assumptions`

현재 샘플 실행 결과:

- 출력 디렉터리: `data/processed/map_json`
- `row_count=893`
- 생성 파일 수: 3

## JSON 구조

### 1. `shipment_paths.json`

상위 구조:

```json
{
  "meta": {
    "source_file": "C:\\HVDC_WORK\\PIPELINE\\PP1030\\docs\\HVDC STATUS1.xlsx",
    "sheet_name": "hvdc all status",
    "row_count": 893,
    "grain": "1 row = 1 shipment / 1 voyage case",
    "rules": {},
    "assumptions": []
  },
  "shipments": []
}
```

`meta` 실제 필드 목록:

- `assumptions`
- `grain`
- `row_count`
- `rules`
- `sheet_name`
- `source_file`

shipment 1건 대표 구조:

```json
{
  "shipment_id": "HVDC-ADOPT-PPL-0001",
  "mr_no": "E02",
  "vendor": "Prysmian",
  "category": "Elec",
  "coe": "FRANCE",
  "origin_region": "Europe",
  "pol": "Le Havre",
  "pod": "Mina Zayed",
  "ship_mode": "B",
  "etd": "2023-11-12",
  "atd": "2023-11-12",
  "eta": "2023-11-30",
  "ata": "2023-12-01",
  "customs_start": "2023-11-29",
  "customs_close": "2023-12-01",
  "custom_code": "47150.0",
  "planned_sites": ["MIR", "AGI"],
  "actual_sites": ["MIR"],
  "actual_site_dates": {
    "SHU": null,
    "MIR": "2025-12-04",
    "DAS": null,
    "AGI": null
  },
  "warehouse_visits": [
    {
      "column": "JDN MZD",
      "node_ref": "wh:jdn_mzd",
      "date": "2023-12-05"
    }
  ],
  "mosb_visit": null,
  "final_delivery": "2023-12-05",
  "entry_node_ref": "port:mina_zayed",
  "customs_node_ref": "customs:mina_zayed",
  "global_paths": [
    [
      "origin_region:europe",
      "origin_pol:france:le_havre",
      "port:mina_zayed",
      "site:MIR"
    ]
  ],
  "uae_ops_paths": [
    [
      "port:mina_zayed",
      "customs:mina_zayed",
      "wh:jdn_mzd",
      "site:MIR"
    ]
  ],
  "flow_code_planned": null,
  "flow_code_actual": 2,
  "status": "delivered",
  "metrics": {
    "cif_value": 8034397.02,
    "gross_weight_kg": 659580.0,
    "cbm": 1290.89,
    "qty_of_container": 0.0
  },
  "flags": {
    "wh_any": true,
    "mosb_required": false,
    "mosb_any": false,
    "multi_planned_site": true,
    "multi_actual_site": false
  }
}
```

shipment 객체의 실제 키 목록:

- `actual_sites`
- `actual_site_dates`
- `ata`
- `atd`
- `category`
- `coe`
- `customs_close`
- `customs_node_ref`
- `customs_start`
- `custom_code`
- `entry_node_ref`
- `eta`
- `etd`
- `final_delivery`
- `flags`
- `flow_code_actual`
- `flow_code_planned`
- `global_paths`
- `metrics`
- `mosb_visit`
- `mr_no`
- `origin_region`
- `planned_sites`
- `pod`
- `pol`
- `shipment_id`
- `ship_mode`
- `status`
- `uae_ops_paths`
- `vendor`
- `warehouse_visits`

### 2. `global_graph.json`

상위 구조:

```json
{
  "meta": {},
  "nodes": [],
  "edges": []
}
```

node 구조:

```json
{
  "id": "airport:auh",
  "type": "airport",
  "name": "Abu Dhabi Airport"
}
```

node 필드:

- `id`
- `name`
- `type`

edge 구조:

```json
{
  "id": "airport:auh__site:AGI",
  "source": "airport:auh",
  "target": "site:AGI",
  "route_type": "pod_to_site",
  "shipment_count": 20.25,
  "shipment_ids": [
    "HVDC-ADOPT-HE-0371",
    "HVDC-ADOPT-HE-0415"
  ],
  "allocation_weight_sum": 20.25,
  "cif_value_sum": 9246197.066666668,
  "gross_weight_kg_sum": 50076.26666666666,
  "flow_codes": [3, 4]
}
```

edge 필드:

- `allocation_weight_sum`
- `cif_value_sum`
- `flow_codes`
- `gross_weight_kg_sum`
- `id`
- `route_type`
- `shipment_count`
- `shipment_ids`
- `source`
- `target`

`global_graph.json`의 `route_type` 예시:

- `origin_region_to_pol`
- `pol_to_pod`
- `pod_to_site`
- `global_path`

### 3. `uae_ops_graph.json`

구조는 `global_graph.json`과 동일하게 `meta`, `nodes`, `edges`를 가진다. 차이는 route_type과 node type의 의미가 UAE 운영 구간에 맞춰져 있다는 점이다.

`uae_ops_graph.json`의 `route_type` 예시:

- `port_to_customs`
- `customs_to_wh`
- `customs_to_site`
- `wh_to_mosb`
- `wh_to_site`
- `mosb_to_site`
- `uae_ops_path`

## 운영상 주의사항

### 1. 입력 시트가 다르면 바로 실패한다

- 시트명 비교는 느슨하지만, 실제로 매칭되는 시트가 없으면 예외가 발생한다.
- 운영 시 입력 파일의 시트명 변경 여부를 먼저 확인해야 한다.

### 2. 필수 컬럼 검증은 엄격하다

- 계약 컬럼이 하나라도 없으면 실행이 중단된다.
- 이 스크립트는 header registry 기반 alias 해석을 사용하지 않는다.
- 따라서 현재는 컬럼명이 코드에 하드코딩된 이름과 맞아야 한다.

### 3. 날짜 해석은 보수적으로 처리된다

- `pd.to_datetime()`으로 파싱되지 않으면 `null` 처리된다.
- 2000년 이전 날짜는 placeholder 또는 오류 가능성으로 보고 무시한다.
- 따라서 Excel의 날짜 포맷 오류는 경로 누락으로 이어질 수 있다.

### 4. Warehouse / site / POD / customs 정의가 하드코딩되어 있다

- warehouse 컬럼 목록이 코드 내부 `WAREHOUSE_COLS`에 고정되어 있다.
- site planned/actual 컬럼도 `SITE_DOC_COLS`, `SITE_ACTUAL_COLS`에 고정되어 있다.
- POD / customs alias도 코드 내부 맵에 제한적으로 정의되어 있다.
- 새로운 location이 추가되면 코드 수정 없이 자동 반영되지 않는다.

### 5. Graph 집계는 allocation weight를 사용한다

- multi-site row는 path가 여러 개 생성될 수 있다.
- 이 경우 edge별 shipment count가 정수 건수가 아니라 가중치 합으로 표현된다.
- 그래프의 `shipment_count`는 물리적 row 개수와 항상 일치하지 않는다.

## 현재 한계와 후속 개선 후보

현재 한계:

- header registry와 연동되지 않아 입력 컬럼 alias를 유연하게 해석하지 못한다.
- warehouse, site, POD, customs 매핑이 코드에 하드코딩되어 있다.
- 일부 소스 주석과 기존 문서에는 한글 인코딩이 깨진 부분이 남아 있다.

후속 개선 후보:

- `scripts/core/header_registry.py`와 연동해 입력 컬럼 alias를 중앙 관리한다.
- warehouse/site/POD/customs 정의를 config 또는 registry로 분리한다.
- JSON 스키마를 별도 문서 또는 validation 규칙으로 고정한다.
- 예외 메시지에 누락 컬럼과 추천 대응을 더 상세히 포함한다.

## 검증 기준

문서와 코드가 일치하는지 확인할 때 다음 항목을 기준으로 검증한다.

- 함수명:
  - `load_input_dataframe`
  - `validate_required_columns`
  - `preprocess_dataframe`
  - `build_cli_args`
  - `build_paths_for_row`
  - `flow_code_from_sites_and_staging`
  - `status_from_row`
  - `build_graphs`
  - `add_node`
  - `add_edge`
  - `write_outputs`
  - `main`
- CLI 인자:
  - `excel_path`
  - `sheet_name`
  - `--header-row`
  - `--output-dir`
- 기본 실행 결과:
  - `data/processed/map_json` 아래 3개 JSON 생성
  - 샘플 기준 `row_count=893`
- JSON 구조:
  - `shipment_paths.json` 상위 키 `meta`, `shipments`
  - `global_graph.json` 상위 키 `meta`, `nodes`, `edges`
  - `uae_ops_graph.json` 상위 키 `meta`, `nodes`, `edges`
