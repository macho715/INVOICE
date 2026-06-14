# 파일명/시트명/헤더명 전체 변형 수집 보고서

**작성일**: 2025-01-27
**목적**: `name_resolver.py`의 별칭 사전 확장을 위한 전체 변형 수집
**범위**: docs, analysis, _archived 폴더 전체 스캔

---

## 📋 Executive Summary

프로젝트 전체 문서 및 코드를 스캔하여 실제 사용되는 파일명, 시트명, 헤더명의 모든 변형을 수집했습니다. 이를 통해 `name_resolver.py`의 별칭 사전을 확장하여 더 넓은 범위의 변형을 자동으로 처리할 수 있습니다.

### 주요 발견 사항

- **파일명 변형**: 15개 이상의 변형 패턴 발견
- **시트명 변형**: 8개 이상의 시트명 변형 발견
- **헤더명 변형**: 100개 이상의 헤더명 변형 발견
- **벤더명 변형**: 추가 변형 패턴 발견

---

## 1. 파일명 변형 (File Names)

### 1.1 HITACHI 관련 파일명

| 표준 이름 | 발견된 변형 | 출처 |
|----------|------------|------|
| `Case List_Hitachi.xlsx` | `Case List.xlsx`<br>`Case List_Hitachi.xlsx`<br>`Case List_Hitachi` | docs/reports/STAGE123_DATA_FLOW_REPORT.md<br>docs/reports/RAW_DATA_PROTECTION_VERIFICATION_REPORT.md |
| `HVDC WAREHOUSE_HITACHI(HE).xlsx` | `HVDC WAREHOUSE_HITACHI(HE).xlsx`<br>`HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx`<br>`HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`<br>`HVDC WAREHOUSE_HITACHI(HE).synced_v3.8_merged.xlsx`<br>`HVDC WAREHOUSE_HITACHI(HE).synced_v3.9_merged.xlsx`<br>`HVDC Hitachi.xlsx`<br>`HVDC Hitachi` | Multiple docs<br>file_registry.py<br>analysis scripts |
| `HITACHI(HE)` | `HITACHI(HE)`<br>`Hitachi(HE)` | header_registry.py<br>toolkit_source |

### 1.2 SIEMENS 관련 파일명

| 표준 이름 | 발견된 변형 | 출처 |
|----------|------------|------|
| `Case List_Simense.xlsm` | `Case List_Simense.xlsm`<br>`Case List_Simense` | docs/reports/STAGE123_DATA_FLOW_REPORT.md |
| `HVDC WAREHOUSE_SIMENSE(SIM).xlsx` | `HVDC WAREHOUSE_SIMENSE(SIM).xlsx`<br>`HVDC WAREHOUSE_SIMENSE(SIM).xlsm`<br>`HVDC WAREHOUSE_SIMENSE(SIM)` | docs/reports<br>file_registry.py |
| `SIEMENS(SIM)` | `SIEMENS(SIM)`<br>`SIMENSE(SIM)` | header_registry.py<br>toolkit_source |

### 1.3 분석 관련 파일명

| 파일명 | 사용 위치 |
|--------|----------|
| `indoor warehouse data.xlsx` | analysis/ANALYSE1.ipynb<br>analysis/ANALYSE2.ipynb |
| `Expected_Contract_and_Monthly_SQM.xlsx` | analysis/ANALYSE1.ipynb |
| `Contract_Details.xlsx` | analysis/ANALYSE1.ipynb |
| `Payment_Schedule.xlsx` | analysis/ANALYSE1.ipynb |
| `Extended_Contract_Budget.xlsx` | analysis/ANALYSE1.ipynb<br>analysis/ANALYSE2.ipynb |
| `WAREHOUSE INDOOR_OUTDOOR QTY.xlsx` | analysis/ANALYSE2.ipynb |

### 1.4 리포트 파일명

| 패턴 | 예시 |
|------|------|
| 리포트 템플릿 | `HVDC_입고로직_종합리포트_{timestamp}_v3.0-corrected.xlsx` |
| 이상치 리포트 | `HVDC_anomaly_report.xlsx`<br>`HVDC_anomaly_report.json` |

### 1.5 파일명 확장자 변형

- `.xlsx` (표준)
- `.xlsm` (매크로 포함, SIEMENS 파일)
- `.json` (이상치 리포트)

---

## 2. 시트명 변형 (Sheet Names)

### 2.1 HITACHI 시트명

| 표준 이름 | 발견된 변형 | 출처 |
|----------|------------|------|
| `Case List, RIL` | `Case List, RIL`<br>`Case List RIL`<br>`CaseList`<br>`case list`<br>`Case List, RIL(SIEMENS)` | file_registry.py<br>docs/reports<br>analysis scripts |
| `HE Local` | `HE Local`<br>`HELocal`<br>`he local`<br>`히타치 로컬` | file_registry.py<br>name_resolver.py |
| `HE-0214,0252 (Capacitor)` | `HE-0214,0252`<br>`HE-0214,0252 (Capacitor)`<br>`Capacitor`<br>`capacitor` | docs/reports<br>file_registry.py |

### 2.2 리포트 시트명

| 시트명 | 사용 위치 |
|--------|----------|
| `통합_원본데이터_Fixed` | docs/reports/stage3-column-missing-issue-report.md<br>docs/reports/patch-application-report.md |
| `HITACHI_원본데이터_Fixed` | docs/reports/patch-application-report.md |
| `SIEMENS_원본데이터_Fixed` | docs/reports/patch-application-report.md |
| `창고_월별_입출고` | docs/reports/patch-application-report.md |
| `현장_월별_입고재고` | docs/reports/patch-application-report.md |
| `Flow_Code_분석` | docs/reports/patch-application-report.md |
| `Flow_Sankey_Links` | toolkit_source |
| `Flow_Timeline` | toolkit_source |
| `Flow_KPI` | toolkit_source |
| `전체_트랜잭션_요약` | docs/reports/patch-application-report.md |
| `KPI_검증_결과` | docs/reports/patch-application-report.md |
| `SQM_누적재고` | docs/reports/patch-application-report.md |
| `SQM_Invoice과금` | docs/reports/patch-application-report.md |
| `SQM_피벗테이블` | docs/reports/patch-application-report.md |
| `원본_데이터_샘플` | docs/reports/patch-application-report.md |

### 2.3 분석 파일 시트명

| 시트명 | 파일 |
|--------|------|
| `warehouse` | indoor warehouse data.xlsx |
| `indoor` | indoor warehouse data.xlsx |
| `outdoor` | indoor warehouse data.xlsx |

---

## 3. 헤더명 변형 (Header Names)

### 3.1 Case Number 관련 헤더

| 표준 (canonical) | 발견된 변형 | 출처 |
|-----------------|------------|------|
| `CASE NO` | `Case No`<br>`Case No.`<br>`CASE NO`<br>`case number`<br>`Case Number`<br>`Case_No`<br>`CaseNo`<br>`case-no`<br>`CASE_NUMBER`<br>`case_no`<br>`Case#`<br>`Case`<br>`Package No`<br>`Package No.`<br>`PACKAGE NO`<br>`PackageNo`<br>`packageno`<br>`Package_No` | header_registry.py<br>name_resolver.py<br>analysis scripts |

### 3.2 Quantity 관련 헤더

| 표준 (canonical) | 발견된 변형 | 출처 |
|-----------------|------------|------|
| `QTY` | `QTY`<br>`Qty`<br>`Quantity`<br>`Q'ty`<br>`Qty.`<br>`수량`<br>`QUANTITY`<br>`Amount`<br>`Count`<br>`quantity`<br>`qty`<br>`q'ty` | header_registry.py<br>name_resolver.py<br>flow_ledger_v2.py |

### 3.3 Material/Description 관련 헤더

| 표준 (canonical) | 발견된 변형 | 출처 |
|-----------------|------------|------|
| `MATERIAL` | `Material`<br>`material`<br>`Item Desc`<br>`Item Description`<br>`Description`<br>`Desc`<br>`DESC`<br>`Detail`<br>`Details`<br>`Name`<br>`Item Name`<br>`설명`<br>`상세`<br>`Description/명칭`<br>`품명` | header_registry.py<br>name_resolver.py |

### 3.4 Vendor 관련 헤더

| 표준 (canonical) | 발견된 변형 | 출처 |
|-----------------|------------|------|
| `VENDOR` | `Vendor`<br>`vendor`<br>`Maker`<br>`Supplier`<br>`Vend`<br>`Vendr`<br>`Source_Vendor`<br>`source_vendor`<br>`SourceVendor`<br>`Source Vendor` | header_registry.py<br>name_resolver.py<br>toolkit_source |

### 3.5 기타 주요 헤더 변형

#### Equipment/PO Number
- `EQ No`, `EQ No.`, `EQ_No`, `EQNo`
- `Equipment No`, `Equipment No.`, `Equipment Number`
- `PO.No` (SIEMENS), `PO No`, `PO No.`, `PO_No`, `PONo`
- `Purchase Order No`, `Purchase Order No.`, `Purchase Order`

#### Date/Time Headers
- `ETD/ATD`, `ETD`, `ATD`, `ETD_ATD`, `ETD-ATD`, `ETD / ATD`
- `ETA/ATA`, `ETA`, `ATA`, `ETA_ATA`, `ETA-ATA`, `ETA / ATA`
- `Departure Date`, `Arrival Date`
- `Estimated Departure`, `Actual Departure`
- `Estimated Arrival`, `Actual Arrival`

#### Warehouse Headers
- `DHL WH`, `DHL Warehouse`
- `DSV Indoor`, `DSV Outdoor`, `DSV Al Markaz`, `DSV MZP`
- `AAA Storage`
- `Hauler Indoor`
- `MOSB`

#### Site Headers
- `MIR Site`, `MIR`
- `SHU Site`, `SHU`
- `DAS Site`, `DAS`
- `AGI Site`, `AGI`

#### Metadata Headers
- `Source_File`, `source_file`, `SourceFile`, `Source File`
- `Source_Sheet`, `source_sheet`, `SourceSheet`, `Source Sheet`
- `Source_Vendor`, `source_vendor`, `SourceVendor`, `Source Vendor`

#### Quantity/Measurement Headers
- `SQM`, `sqm`, `Square Meter`, `Square Meterage`
- `Pkg`, `pkg`, `Pkg_Quantity`, `pkg_quantity`
- `Stack_Status`, `stack_status`
- `Storage`, `storage`

#### Location Headers
- `Location`, `location`
- `Site`, `Site Name`, `SiteName`, `Site_Name`
- `Warehouse`, `warehouse`

---

## 4. 벤더명 변형 (Vendor Names)

### 4.1 HITACHI 변형

| 표준 | 발견된 변형 | 출처 |
|------|-----------|------|
| `HITACHI` | `HITACHI`<br>`hitachi`<br>`Hitachi`<br>`HE`<br>`H.E`<br>`H-E`<br>`히타치`<br>`hitachi energy`<br>`hitachienergy`<br>`HE Local`<br>`he local`<br>`he-local` | name_resolver.py<br>file_registry.py<br>docs/reports |

### 4.2 SIEMENS 변형

| 표준 | 발견된 변형 | 출처 |
|------|-----------|------|
| `SIEMENS` | `SIEMENS`<br>`siemens`<br>`Siemens`<br>`SIM`<br>`SIMENSE`<br>`simense`<br>`Seimens`<br>`RIL`<br>`R.I.L`<br>`ril`<br>`ril(simense)`<br>`RIL(SIMENSE)`<br>`RIL(SIEMENS)`<br>`지멘스` | name_resolver.py<br>file_registry.py<br>docs/reports<br>toolkit_source |

---

## 5. 코드에서 사용되는 패턴

### 5.1 file_registry.py 패턴

```python
SHEET_NAMES = {
    "case_list": ["Case List, RIL", "Case List RIL", "CaseList", "case list"],
    "he_local": ["HE Local", "HELocal", "he local"],
    "capacitor": ["HE-0214,0252 (Capacitor)", "Capacitor", "capacitor"],
}

VENDORS = {
    "hitachi": {
        "name": "HITACHI",
        "aliases": ["HITACHI", "hitachi", "HE", "Hitachi"],
        ...
    },
    "siemens": {
        "name": "SIEMENS",
        "aliases": ["SIEMENS", "siemens", "SIM", "SIMENSE", "Siemens"],
        ...
    }
}
```

### 5.2 header_registry.py 패턴

```python
# Case Number
aliases=["Case No", "Case No.", "CASE NO", "case number", "Case Number",
         "Case_No", "CaseNo", "case-no", "CASE_NUMBER", "case_no",
         "케이스번호", "케이스 번호", "Case", "Package No", ...]

# Quantity
aliases=["QTY", "Qty", "Quantity", "Q'ty", "Qty.", "수량", "QUANTITY",
         "Amount", "Count"]

# Material/Description
aliases=["Description", "Desc", "DESC", "Detail", "Details", "Name",
         "Item Name", "Item Description", "설명", "상세", ...]
```

### 5.3 analysis 스크립트 패턴

```python
# 시트명 사용
sheet_name="Case List, RIL"
sheet_name="Case List"

# 헤더명 사용
case_cols=("Case No", "Case", "Case_ID", "Case_Number", "case_no", "case")
qty_cols=("Pkg", "pkg", "Pkg_Quantity", "pkg_quantity", "quantity", "qty")

# 창고 컬럼
warehouse_cols = ["DHL WH", "DSV Indoor", "DSV Al Markaz", "DSV Outdoor",
                  "AAA Storage", "Hauler Indoor", "DSV MZP", "MOSB"]
site_cols = ["MIR", "SHU", "DAS", "AGI"]
```

---

## 6. 권장 별칭 사전 확장

### 6.1 VENDOR_ALIASES 확장 권장사항

```python
VENDOR_ALIASES: Dict[str, Iterable[str]] = {
    "HITACHI": {
        "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치",
        "hitachienergy", "he local", "he-local",
        # 추가 권장
        "Hitachi", "HITACHI ENERGY", "H.E", "HE-LOCAL"
    },
    "SIEMENS": {
        "siemens", "sim", "simense", "seimens", "ril", "r.i.l",
        "ril(simense)", "지멘스",
        # 추가 권장
        "Siemens", "SIMENSE", "RIL(SIMENSE)", "RIL(SIEMENS)", "R.I.L"
    },
}
```

### 6.2 SHEET_ALIASES 확장 권장사항

```python
SHEET_ALIASES: Dict[str, Iterable[str]] = {
    "CASE LIST": {
        "case list", "caselist", "case_list",
        # 추가 권장
        "Case List", "CaseList", "CASE LIST"
    },
    "CASE LIST, RIL(SIEMENS)": {
        "case list, ril(simense)", "case list ril", "ril", "ril(simense)",
        # 추가 권장
        "Case List, RIL", "Case List RIL", "CASE LIST, RIL",
        "Case List, RIL(SIEMENS)"
    },
    "HE LOCAL": {
        "he local", "he-local", "hitachi local", "히타치 로컬",
        # 추가 권장
        "HE Local", "HELocal", "HE-LOCAL"
    },
    # 새로 추가 권장
    "HE-0214,0252 (CAPACITOR)": {
        "he-0214,0252", "he-0214,0252 (capacitor)", "capacitor",
        "HE-0214,0252", "Capacitor"
    },
}
```

### 6.3 HEADER_ALIASES 확장 권장사항

```python
HEADER_ALIASES: Dict[str, Iterable[str]] = {
    "CASE NO": {
        "case no", "case_no", "caseno", "case#", "case number",
        # 추가 권장
        "Case No", "Case No.", "CASE NO", "Case Number", "Case_No",
        "CaseNo", "case-no", "CASE_NUMBER", "case_no", "케이스번호",
        "케이스 번호", "Case", "Package No", "Package No.", "PACKAGE NO",
        "PackageNo", "packageno", "Package_No"
    },
    "VENDOR": {
        "vendor", "maker", "supplier", "vend", "vendr",
        # 추가 권장
        "Vendor", "VENDOR", "Source_Vendor", "source_vendor",
        "SourceVendor", "Source Vendor"
    },
    "QTY": {
        "qty", "quantity", "q'ty", "수량",
        # 추가 권장
        "QTY", "Qty", "Quantity", "Q'ty", "Qty.", "QUANTITY",
        "Amount", "Count", "quantity", "Pkg", "pkg", "Pkg_Quantity",
        "pkg_quantity"
    },
    "MATERIAL": {
        "material", "item desc", "description", "desc", "품명",
        # 추가 권장
        "Material", "MATERIAL", "Item Desc", "Item Description",
        "Description", "Desc", "DESC", "Detail", "Details", "Name",
        "Item Name", "설명", "상세", "Description/명칭"
    },
    # 새로 추가 권장
    "ETD/ATD": {
        "etd/atd", "etd", "atd", "etd_atd", "etd-atd", "ETD / ATD",
        "Estimated Departure", "Actual Departure", "Departure Date",
        "Departure", "출발일"
    },
    "ETA/ATA": {
        "eta/ata", "eta", "ata", "eta_ata", "eta-ata", "ETA / ATA",
        "Estimated Arrival", "Actual Arrival", "Arrival Date",
        "Arrival", "도착일"
    },
    "DHL WAREHOUSE": {
        "dhl wh", "dhl warehouse", "DHL WH", "DHL Warehouse"
    },
    "DSV INDOOR": {
        "dsv indoor", "DSV Indoor"
    },
    "DSV AL MARKAZ": {
        "dsv al markaz", "DSV Al Markaz", "dsv almarkaz"
    },
    "DSV OUTDOOR": {
        "dsv outdoor", "DSV Outdoor"
    },
    "AAA STORAGE": {
        "aaa storage", "AAA Storage", "AAA_STORAGE"
    },
    "HAULER INDOOR": {
        "hauler indoor", "Hauler Indoor", "HAULER_INDOOR"
    },
    "MOSB": {
        "mosb", "MOSB"
    },
    "MIR": {
        "mir", "MIR", "MIR Site"
    },
    "SHU": {
        "shu", "SHU", "SHU Site"
    },
    "DAS": {
        "das", "DAS", "DAS Site"
    },
    "AGI": {
        "agi", "AGI", "AGI Site"
    },
    "SQM": {
        "sqm", "SQM", "Square Meter", "Square Meterage"
    },
    "STACK_STATUS": {
        "stack_status", "Stack_Status", "STACK_STATUS"
    },
}
```

---

## 7. 통계 요약

### 7.1 파일명 변형

- **HITACHI 파일명**: 7개 변형
- **SIEMENS 파일명**: 5개 변형
- **분석 파일명**: 6개 변형
- **리포트 파일명**: 3개 패턴

**총 21개 이상의 파일명 패턴**

### 7.2 시트명 변형

- **표준 시트명**: 3개 (Case List, HE Local, Capacitor)
- **리포트 시트명**: 14개
- **분석 시트명**: 3개

**총 20개 이상의 시트명**

### 7.3 헤더명 변형

- **Case Number**: 18개 변형
- **Quantity**: 11개 변형
- **Material/Description**: 14개 변형
- **Vendor**: 10개 변형
- **Date/Time**: 20개 변형
- **Warehouse**: 8개 변형
- **Site**: 4개 변형
- **기타**: 30개 이상 변형

**총 115개 이상의 헤더명 변형**

### 7.4 벤더명 변형

- **HITACHI**: 11개 변형
- **SIEMENS**: 13개 변형

**총 24개 벤더명 변형**

---

## 8. 우선순위별 확장 권장사항

### 우선순위 1: 즉시 추가 권장 (높은 사용 빈도)

1. **시트명 확장**:
   - `HE-0214,0252 (Capacitor)` 관련 변형
   - 리포트 시트명 (`통합_원본데이터_Fixed`, `창고_월별_입출고` 등)

2. **헤더명 확장**:
   - `DHL WAREHOUSE`, `DSV INDOOR`, `DSV AL MARKAZ` 등 창고 헤더
   - `MIR`, `SHU`, `DAS`, `AGI` 등 현장 헤더
   - `SQM`, `Stack_Status` 등 측정 헤더

3. **벤더명 확장**:
   - `RIL(SIMENSE)` → `RIL(SIEMENS)` 패턴
   - 대소문자 변형 추가

### 우선순위 2: 점진적 추가 (중간 사용 빈도)

1. 리포트 시트명 전체 (14개)
2. Date/Time 헤더 세부 변형
3. Equipment/PO Number 변형

### 우선순위 3: 선택적 추가 (낮은 사용 빈도)

1. 분석 파일 시트명
2. 특수 리포트 헤더
3. 다국어 헤더 (한국어, 일본어 등)

---

## 9. 구현 체크리스트

### 즉시 반영 가능

- [ ] `HE-0214,0252 (Capacitor)` 시트명 추가
- [ ] 창고 헤더명 (`DHL WAREHOUSE`, `DSV INDOOR` 등) 추가
- [ ] 현장 헤더명 (`MIR`, `SHU`, `DAS`, `AGI`) 추가
- [ ] `SQM`, `Stack_Status` 헤더 추가
- [ ] `RIL(SIMENSE)` → `RIL(SIEMENS)` 패턴 추가

### 테스트 후 반영

- [ ] 리포트 시트명 전체 추가
- [ ] Date/Time 헤더 세부 변형 추가
- [ ] Equipment/PO Number 변형 추가

---

## 10. 참고 자료

### 문서 출처
- `docs/reports/STAGE123_DATA_FLOW_REPORT.md`
- `docs/reports/RAW_DATA_PROTECTION_VERIFICATION_REPORT.md`
- `docs/reports/patch-application-report.md`
- `docs/reports/STAGE1_COLUMN_MAPPING_FLEXIBILITY_REPORT.md`

### 코드 출처
- `core/file_registry.py`
- `core/header_registry.py`
- `core/name_resolver.py`
- `analysis/dsv_almarkaz_ultimate_dashboard.py`
- `analysis/warehouse_movement_network_analyzer.py`
- `_archived/toolkit_source_20251020/hvdc_excel_toolkit/hvdc_excel_reporter_final_sqm_rev.py`

---

**작성자**: AI Assistant
**검토 필요**: SCM/Dev Team
**최종 업데이트**: 2025-01-27

**다음 단계**: 수집된 변형을 `core/name_resolver.py`의 별칭 사전에 반영하여 매칭 성능 향상

