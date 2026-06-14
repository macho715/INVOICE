# Flow Code를 특정 시트에만 적용하는 방법

**대상:** `docs/HVDC STATUS1.xlsx` 같은 외부 Excel 파일에서 **"hvdc all status"** 시트에만 파이프라인과 동일한 Flow Code(0~5)를 적용하고 싶을 때.

---

## 1. 요약

- **적용 스크립트:** `scripts/utils/apply_flow_code_to_sheet.py` — 지정 시트에만 Flow Code 적용 후 해당 시트만 덮어써 저장.
- **점검 스크립트:** `scripts/utils/inspect_excel_for_flow_code.py` — 읽기 전용. 시트 목록·컬럼 목록·필수 컬럼 존재 여부 및 alias 매칭 결과를 출력.
- **동작:** Excel 컬럼명이 파이프라인 primary alias와 다르면(예: "DHL Warehouse") core 레지스트리 alias로 매칭한 뒤 Flow 로직을 적용하고, 저장 시 원본 컬럼명을 유지합니다.

---

## 2. Excel 파일/시트 확인 (실행 전 권장)

대상 파일 경로와 시트명·컬럼을 먼저 확인하려면 **inspect** 스크립트를 실행하세요.

**프로젝트 루트**에서:

```bash
# 시트 목록 + "hvdc all status" 시트의 컬럼 + 필수 컬럼 매칭 결과 출력
python scripts/utils/inspect_excel_for_flow_code.py "docs/HVDC STATUS1.xlsx"

# 시트명·헤더 행 지정
python scripts/utils/inspect_excel_for_flow_code.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --header-row 0
```

- **출력:** 파일 내 시트 목록, 해당 시트의 컬럼 목록, `Status_Location` / 창고 / 현장 컬럼의 존재 여부. Excel 컬럼명이 primary와 다를 경우 "OK (Excel: '...')" 형태로 alias 매칭된 실제 컬럼명이 표시됩니다.
- 실제 경로가 `docs/` 가 아닐 수 있으므로, 사용 중인 **Excel 파일의 전체 경로**를 인자로 넣어 실행하면 됩니다.

---

## 3. 사용 방법 (Flow Code 적용)

**프로젝트 루트**에서 실행:

```bash
# 기본 시트명 "hvdc all status", 헤더 1행(header=0)
python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx"

# 시트명 지정
python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx" "hvdc all status"

# 헤더가 2행(0-based로 1)인 경우
python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --header-row 1

# 적용하지 않고 분포만 확인 (파일 수정 없음)
python scripts/utils/apply_flow_code_to_sheet.py "docs/HVDC STATUS1.xlsx" "hvdc all status" --dry-run
```

- **`--header-row`:** 컬럼명이 있는 행의 0-based 인덱스. 기본값 0(첫 번째 행). 2행이 헤더면 `--header-row 1`.
- **주의:** `~$HVDC STATUS1.xlsx`는 Excel이 파일을 연 동안 생성되는 잠금 파일이므로 사용하지 마세요. **`HVDC STATUS1.xlsx`** 를 지정하고, 필요하면 Excel에서 해당 파일을 닫은 뒤 실행하세요.
- 저장 후 **시트 개수·시트명**이 저장 전과 동일한지 자동 검증합니다. 다르면 경고가 출력됩니다.

---

## 4. 컬럼명과 alias 매칭

Excel 시트의 컬럼명이 파이프라인 primary alias(예: `DHL WH`, `DSV Indoor`)와 다를 수 있습니다. apply 스크립트는 **core 레지스트리**(`scripts/core/header_registry.py`)에 정의된 **alias 목록**으로 매칭합니다.

- 예: Excel에 `DHL Warehouse`, `Al Markaz` 가 있으면 각각 `DHL WH`, `DSV Al Markaz` 로 인식됩니다.
- Flow 로직은 내부적으로 primary alias 기준으로 계산하고, **저장 시에는 원본 Excel 컬럼명을 그대로 유지**합니다(FLOW_CODE, FLOW_DESCRIPTION만 추가/갱신).

inspect 스크립트로 "OK (Excel: '...')" 출력을 확인하면 alias로 매칭된 컬럼을 볼 수 있습니다.

---

## 5. 필요한 컬럼

Flow Code 계산에 사용하는 컬럼은 파이프라인 Stage3와 동일합니다.

| 구분 | 컬럼 예시 |
|------|------------|
| **필수** | `Status_Location` |
| **창고** | `DHL WH`, `DSV Indoor`, `DSV Al Markaz`, `DSV Outdoor`, `DSV MZP`, `Hauler Indoor`, `JDN MZD`, `AAA Storage`, `MOSB` 등 (core 레지스트리 순서) |
| **현장** | `MIR`, `SHU`, `DAS`, `AGI` |
| **선택** | `Final_Location` (또는 `Final location` 등) — AGI/DAS 강제 Flow 3 적용 시 사용 |

일부 컬럼이 없으면 해당 조건은 무시되고, 기본값/Flow 5로 처리될 수 있습니다. 스크립트 실행 시 누락 컬럼은 경고로 출력됩니다.

---

## 6. 적용 결과

- **추가되는 컬럼**
  - **FLOW_CODE:** 0 ~ 5 정수  
    - 0: Pre Arrival  
    - 1: Port → Site  
    - 2: Port → WH → Site  
    - 3: Port → MOSB → Site (AGI/DAS)  
    - 4: Port → WH → MOSB → Site (AGI/DAS)  
    - 5: Mixed / Waiting / Incomplete leg  
  - **FLOW_DESCRIPTION:** 위 코드에 대응하는 설명 문자열

- **수정 범위:** 지정한 시트만 갱신됩니다. 같은 통합 문서의 다른 시트는 그대로 둡니다.

---

## 7. 로직 출처

- Stage3 `report_generator.py`의 `_override_flow_code()` (v3.5: 0~5 확장, AGI/DAS 도메인 룰)와 동일한 규칙을 `apply_flow_code_to_dataframe()`에서 구현했습니다.
- 창고/현장 컬럼 목록은 `core.get_warehouse_columns()`, `core.get_site_columns()`를 사용해 파이프라인과 동일하게 맞춥니다.

---

## 8. 트러블슈팅

| 현상 | 확인 사항 |
|------|-----------|
| `File not found` | 경로가 프로젝트 루트 기준인지, `HVDC STATUS1.xlsx`(잠금 파일 `~$...` 아님)인지 확인. |
| `Sheet not found` | 시트명 띄어쓰기/대소문자. 스크립트는 공백·대소문자 무시하고 매칭합니다. |
| `Permission denied` / 파일이 덮어써지지 않음 | Excel에서 해당 파일을 닫은 뒤 다시 실행. |
| FLOW_CODE가 전부 5로 나옴 | `Status_Location` 및 창고/현장 날짜 컬럼 존재 여부와 값 확인. |
| 헤더가 2행 이상인 경우 | `--header-row 1` 등으로 컬럼명이 있는 행 인덱스 지정. |
| Excel 컬럼명이 다름 | `inspect_excel_for_flow_code.py`로 alias 매칭 여부 확인. 레지스트리에 alias가 없으면 추가 검토. |
