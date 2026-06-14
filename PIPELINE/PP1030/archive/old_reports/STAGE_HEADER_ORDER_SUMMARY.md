# Stage 1, 2, 3 헤더 정렬 순서 보고서

## 📋 요약

각 Stage는 독립적인 헤더 정렬 순서를 사용하며, **창고 10개 + 현장 4개**의 핵심 순서는 모든 Stage에서 일관되게 유지됩니다.

---

## 🔷 Stage 1: Data Synchronization

**파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`  
**목적**: HITACHI + SIEMENS 원본 데이터 병합 및 정규화  
**방식**: 기능별 그룹화

### 정렬 구조
```
base_cols + WAREHOUSE_ORDER + Shifting + SITE_ORDER + Source_Sheet
```

### 창고 컬럼 순서 (10개)
```
1. DHL WH
2. DSV Indoor
3. DSV Al Markaz
4. Hauler Indoor
5. DSV Outdoor
6. DSV MZP
7. HAULER
8. JDN MZD
9. MOSB
10. AAA Storage
```

### 현장 컬럼 순서 (4개)
```
1. MIR
2. SHU
3. AGI
4. DAS
```

### 최종 컬럼 구조
1. **기본 컬럼** (base_cols): no., Shipment Invoice No., SCT Ref.No, Site, EQ No, Case No., Pkg, Storage, Description, L/W/H, CBM, Weight, Stack, HS Code, Currency, Price, Vessel, COE, POL, POD, ETD/ATD, ETA/ATA
2. **창고 컬럼** (10개): WAREHOUSE_ORDER
3. **Shifting** (1개)
4. **현장 컬럼** (4개): SITE_ORDER
5. **Source_Sheet** (1개)

**로그 확인**:
```
[OK] Column order: base + warehouses(10) + Shifting + sites(4) + Source_Sheet
```

**총 컬럼**: ~51개

---

## 🔷 Stage 2: Derived Columns

**파일**: `scripts/core/standard_header_order.py` (STAGE2_HEADER_ORDER)  
**목적**: 파생 컬럼 추가 (SQM, Stack_Status, Status_*)  
**방식**: 표준 순서 (64개 컬럼)

### 표준 순서 (64개)

#### 1-9. 기본 식별 정보
```
1. no.
2. Shipment Invoice No.
3. SCT Ref.No          ⭐ 3번째 위치 (중요)
4. Site
5. EQ No
6. Case No.
7. Pkg
8. Storage
9. Description
```

#### 10-15. 치수 정보
```
10. L(CM)
11. W(CM)
12. H(CM)
13. CBM
14. N.W(kgs)
15. G.W(kgs)
```

#### 16-25. 물류 정보
```
16. Stack
17. HS Code
18. Currency
19. Price
20. Vessel
21. COE
22. POL
23. POD
24. ETD/ATD
25. ETA/ATA
```

#### 26-35. 창고 컬럼 (10개) - Stage 1과 동일
```
26. DHL WH
27. DSV Indoor
28. DSV Al Markaz
29. Hauler Indoor
30. DSV Outdoor
31. DSV MZP
32. HAULER
33. JDN MZD
34. MOSB
35. AAA Storage
```

#### 36. Shifting
```
36. Shifting
```

#### 37-40. 현장 컬럼 (4개)
```
37. MIR
38. SHU
39. AGI
40. DAS
```

#### 41. 메타데이터
```
41. Source_Sheet
```

#### 42-47. 상태 정보 (파생 컬럼)
```
42. Status_WAREHOUSE
43. Status_SITE
44. Status_Current
45. Status_Location
46. Status_Location_Date
47. Status_Storage
```

#### 48-52. Handling 정보 (파생 컬럼)
```
48. wh handling         ⚠️ 공백 1개
49. site  handling      ⚠️ 공백 2개 (의도적)
50. total handling
51. minus
52. final handling
```

#### 53-54. SQM 계산 (파생 컬럼)
```
53. SQM                 (L × W × H / 10000)
54. Stack_Status        (Stack 필드 파싱)
```

**특이 사항**:
- `wh handling`: 공백 1개
- `site  handling`: 공백 2개 (Stage 2 원본 형식)

---

## 🔷 Stage 3: Final Report

**파일**: `scripts/core/standard_header_order.py` (STANDARD_HEADER_ORDER)  
**목적**: 최종 통합 보고서 생성 (통합_원본데이터_Fixed 시트)  
**방식**: 완전한 표준 순서 (73개 컬럼)

### 표준 순서 (73개)

#### 1-25. 기본 정보 (Stage 2와 동일)
```
1-9.   기본 식별 정보 (no. ~ Description)
10-15. 치수 정보 (L(CM) ~ G.W(kgs))
16-25. 물류 정보 (Stack ~ ETA/ATA)
```

#### 26-35. 창고 컬럼 (10개) - Stage 1/2와 동일
```
26. DHL WH
27. DSV Indoor
28. DSV Al Markaz
29. Hauler Indoor
30. DSV Outdoor
31. DSV MZP
32. HAULER
33. JDN MZD
34. MOSB
35. AAA Storage
```

#### 36. Shifting
```
36. Shifting
```

#### 37-40. 현장 컬럼 (4개)
```
37. MIR
38. SHU
39. AGI
40. DAS
```

#### 41. 메타데이터
```
41. Source_Sheet
```

#### 42-47. 상태 정보
```
42. Status_WAREHOUSE
43. Status_SITE
44. Status_Current
45. Status_Location
46. Status_Location_Date
47. Status_Storage
```

#### 48-52. Handling 정보 (⚠️ 정규화됨)
```
48. wh_handling_legacy  ⭐ "wh handling" → 변경 (언더스코어)
49. site handling       ⭐ 공백 1개로 정규화
50. total handling
51. minus
52. final handling
```

#### 53-55. SQM 및 Stack
```
53. SQM
54. Stack_Status
55. Total sqm           ⭐ Stage 3 추가: PKG × SQM × Stack_Status
```

#### 56-64. Stage 3 추가 메타 컬럼
```
56. Vendor
57. Source_File
58. Status_Location_YearMonth
59. site_handling_original
60. total_handling_original
61. wh_handling_original
62. FLOW_CODE
63. FLOW_DESCRIPTION
64. Final_Location
```

#### 65. 입고일자
```
65. 입고일자
```

**주요 변경 사항**:
- `wh handling` → `wh_handling_legacy` (언더스코어 사용)
- `site  handling` (공백 2개) → `site handling` (공백 1개)
- `Total sqm` 추가: PKG × SQM × Stack_Status
- 9개 메타 컬럼 추가 (FLOW_CODE, Final_Location 등)

---

## 📊 Stage별 비교표

| 항목 | Stage 1 | Stage 2 | Stage 3 |
|------|---------|---------|---------|
| **방식** | 기능별 그룹화 | 표준 순서 | 표준 순서 + 추가 |
| **컬럼 수** | ~51개 | 64개 | 73개 |
| **창고 순서** | ✅ 10개 동일 | ✅ 10개 동일 | ✅ 10개 동일 |
| **현장 순서** | ✅ 4개 동일 | ✅ 4개 동일 | ✅ 4개 동일 |
| **wh handling** | - | "wh handling" | "wh_handling_legacy" |
| **site handling** | - | "site  handling" (공백 2) | "site handling" (공백 1) |
| **Total sqm** | ❌ | ❌ | ✅ 추가 |
| **Flow/Location** | ❌ | ❌ | ✅ 추가 (9개) |
| **Status_*** | ❌ | ✅ 6개 | ✅ 6개 |
| **SQM 계산** | ❌ | ✅ 2개 | ✅ 3개 |

---

## 🔑 핵심 일관성

### 모든 Stage에서 동일한 순서

#### 창고 컬럼 (10개)
```
1. DHL WH          → 2. DSV Indoor     → 3. DSV Al Markaz
4. Hauler Indoor   → 5. DSV Outdoor    → 6. DSV MZP
7. HAULER          → 8. JDN MZD        → 9. MOSB
10. AAA Storage
```

#### 현장 컬럼 (4개)
```
1. MIR  →  2. SHU  →  3. AGI  →  4. DAS
```

**배치 규칙**:
- 기본 정보 선순위 (식별 → 치수 → 물류)
- 창고 10개 → Shifting → 현장 4개
- 메타데이터 후순위 (Source_Sheet 끝)

---

## 🎯 실제 실행 결과

### Stage 1 출력
```
[OK] Column order: base + warehouses(10) + Shifting + sites(4) + Source_Sheet
Total: 8,388 rows (HITACHI 5,913 + SIEMENS 2,303)
Columns: 51
```

### Stage 3 출력
```
🔄 헤더 재정렬 시작 (Stage 3): 73개 컬럼
헤더 매칭 완료: 66/73개 (90.4%)
✅ 헤더 재정렬 완료: 65개 표준 순서, 8개 추가 컬럼

[SUCCESS] SQM: 7,971개 계산됨 (95.0%)
[SUCCESS] Stack_Status: 8,316개 파싱됨 (99.1%)
```

**매칭 성공률**: 90.4% (66/73개)

---

## 💡 코드 위치

### Stage 1
- **파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`
- **메서드**: `_ensure_column_order()` (line ~800)
- **정의**: `WAREHOUSE_ORDER`, `SITE_ORDER`

### Stage 2 & 3
- **파일**: `scripts/core/standard_header_order.py`
- **정의**: `STAGE2_HEADER_ORDER` (line 108), `STANDARD_HEADER_ORDER` (line 27)
- **클래스**: `HeaderOrderManager` (line 325)
- **메서드**: `reorder_dataframe()` (line 416)

### 헤더 매칭 로직
- **파일**: `scripts/core/header_normalizer.py`
- **클래스**: `HeaderNormalizer` (정규화)
- **파일**: `scripts/core/semantic_matcher.py`
- **클래스**: `SemanticMatcher` (의미론적 매칭)

---

## 📈 성능 지표

| 항목 | 값 | Stage |
|------|-----|-------|
| **헤더 매칭률** | 90.4% | Stage 3 |
| **표준 순서 컬럼** | 65개 | Stage 3 |
| **추가 컬럼** | 8개 | Stage 3 |
| **SQM 계산률** | 95.0% | Stage 3 |
| **Stack 파싱률** | 99.1% | Stage 3 |

---

## 🎉 결론

HVDC Pipeline은 3단계에 걸쳐 점진적으로 컬럼을 추가하고 정렬하는 전략을 사용합니다:

1. **Stage 1**: 원본 데이터 병합 + 기본 정렬 (그룹화) → 51개 컬럼
2. **Stage 2**: 파생 컬럼 추가 + 표준 순서 적용 → 64개 컬럼
3. **Stage 3**: 최종 메타 추가 + 완전한 표준 순서 → 73개 컬럼

**핵심 일관성**: 창고 10개 + 현장 4개의 순서는 모든 Stage에서 동일하게 유지되어 데이터 추적성과 일관성을 보장합니다.

---

**생성일**: 2025-10-26  
**버전**: HVDC Pipeline v3.6 (SIEMENS Integration Complete)


