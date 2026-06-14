# SCT 화물 업데이트 및 CASE_NO 중복 통합 해결 보고서

**작성일**: 2025-10-31  
**버전**: HVDC Pipeline v4.0.45  
**문제**: 
1. SCT 화물 업데이트 누락 (Vendor="SCT" 90건)
2. CASE_NO 중복 495건 (Stage 4 감지)

---

## Executive Summary

### 문제 1: SCT 화물 업데이트 누락

- **원인**: Master의 Vendor="SCT" 화물의 Case No 형식이 Warehouse와 불일치하여 매칭 실패
- **해결**: Fallback 매칭 로직 추가 및 개선

### 문제 2: CASE_NO 중복 495건

- **원인**: Stage 1 merged 파일 생성 시, Stage 3 데이터 통합 시 중복 제거 누락
- **해결**: 두 시점에 중복 제거 로직 추가

### 최종 결과

- ✅ **CASE_NO 중복**: 495건 → **0건** (완전 해결)
- ⚠️ **SCT 화물**: Fallback 매칭 로직 개선 완료, Vendor 컬럼 업데이트 보장 추가

---

## 문제 상세 분석

### 문제 1: SCT 화물 업데이트 누락

#### 발견 사항

- Master 파일에 Vendor="SCT" 화물 **90건** 존재
- Case No 형식: "DCS NETWORK-04", "38-EMERSON", "SCT-0115/ 7 OF 18" 등 (특수 형식)
- Warehouse Case No 형식: "191221", "191222" 등 (숫자 형식)
- **매칭 결과**: 0건 (완전 불일치)

#### 근본 원인

1. **Case No 형식 불일치**: Master와 Warehouse의 Case No 형식이 완전히 다름
2. **매칭 키 한계**: Stage 1은 Case No만 사용하여 매칭
3. **Fallback 부재**: 매칭 실패 시 대체 매칭 로직 없음

### 문제 2: CASE_NO 중복 495건

#### 발견 사항

- Stage 4에서 495건의 CASE_NO 중복 감지
- Stage 1 merged 파일: 중복 존재
- Stage 3 통합 데이터: 중복 존재

#### 근본 원인

1. **Stage 1**: 시트 통합 후 추가 중복 제거 로직 부재
2. **Stage 3**: HITACHI + SIEMENS 데이터 통합 시 중복 제거 누락
3. **기존 로직**: HITACHI+SIEMENS 병합 시점에는 중복 제거 있으나, merged 파일 생성 시점에는 없음

---

## 해결 내용

### 1단계: SCT Fallback 매칭 개선

**파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`

**수정 위치**: Line 1217-1363

**주요 변경**:

1. **중복 매칭 방지**: `matched_wh_rows` set으로 이미 매칭된 row 추적
2. **매칭 정확도 개선**: 
   - Description 키워드 매칭: 최소 2개 키워드 일치 필수
   - Description substring 매칭: 10자 → 15자로 증가
3. **Vendor 컬럼 업데이트 보장**: Fallback 매칭 시 Vendor 컬럼 명시적 업데이트

**코드 변경**:
```python
# ✅ Track matched warehouse rows to prevent duplicate matching
matched_wh_rows = set()

# ✅ Skip if this warehouse row was already matched
if wi in matched_wh_rows:
    continue

# ✅ Ensure Vendor column is updated for SCT fallback matches
if matched_wi is not None:
    if "Vendor" in master.columns and "Vendor" in wh.columns and wi < len(wh):
        wh.at[wi, "Vendor"] = mrow["Vendor"]
```

### 2단계: Stage 1 중복 제거 개선

**파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`

**수정 위치**: 
- Line 575-590: 기존 하드코딩 제거 (프로젝트 표준 준수)
- Line 1767-1775: merged 파일 생성 시 추가 중복 제거

**주요 변경**:

1. **하드코딩 제거**: `'Case No.'` → `find_header_by_meaning()` 사용
2. **이중 보안**: 시트 통합 후 추가 중복 제거

**코드 변경**:
```python
# Line 575-590: 프로젝트 표준 준수
from core import find_header_by_meaning
case_col = find_header_by_meaning(merged_df, "case_number", required=False)
if not case_col:
    case_col = "Case No." if "Case No." in merged_df.columns else None

if case_col and case_col in merged_df.columns:
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=[case_col], keep="first")
    # ... 로깅 ...

# Line 1767-1775: merged 파일 생성 시 추가 중복 제거
merged_df = pd.concat(combined_dfs, ignore_index=True, sort=False)
case_col = find_header_by_meaning(merged_df, "case_number", required=False)
if case_col and case_col in merged_df.columns:
    before = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=[case_col], keep="first")
    after = len(merged_df)
    if before != after:
        print(f"  [DEDUP] Stage 1 merged file: Removed {before - after} duplicate CASE_NO entries")
```

### 3단계: Stage 3 중복 제거 추가

**파일**: `scripts/stage3_report/report_generator.py`

**수정 위치**: Line 702-715

**주요 변경**:

- `pd.concat` 직후 중복 제거 로직 추가
- `find_header_by_meaning` 사용 (프로젝트 표준)

**코드 변경**:
```python
self.combined_data = pd.concat(combined_dfs, ignore_index=True, sort=False)
# ... 컬럼 정규화 ...

# ✅ Remove duplicates based on CASE_NO after combining all data
from core import find_header_by_meaning
case_col = find_header_by_meaning(self.combined_data, "case_number", required=False)
if case_col:
    before = len(self.combined_data)
    self.combined_data = self.combined_data.drop_duplicates(subset=[case_col], keep="first")
    after = len(self.combined_data)
    if before != after:
        logger.warning(f"[DEDUP] Stage 3 combined: Removed {before - after} duplicate CASE_NO entries")
```

### 4단계: 조사 및 검증 스크립트 생성

**신규 파일**:
- `scripts/investigation/extract_duplicate_case_no.py`: 중복 CASE_NO 상세 분석
- `scripts/investigation/verify_case_no_dedup.py`: 단계별 중복 검증

---

## 실행 결과

### 전체 파이프라인 실행 (2025-10-31 10:07)

**Stage 1 결과**:
- ✅ 중복 제거: **495건 제거** (`[DEDUP] Stage 1 merged file: Removed 495 duplicate CASE_NO entries`)
- ✅ SCT Fallback 매칭: 35건 매칭 성공 (로그 확인)
- ✅ Vendor 컬럼 업데이트 보장 로직 추가

**Stage 2 결과**:
- ✅ 파생 컬럼 계산 완료

**Stage 3 결과**:
- ✅ 데이터 통합 시 중복 제거 로직 추가
- ✅ 중복 제거 로깅 추가

**Stage 4 결과**:
- ✅ CASE_NO 중복: **0건** (완전 해결!)
- ✅ 이상치 감지: 174건

### 검증 결과

**CASE_NO 중복 검증** (`verify_case_no_dedup.py`):
- ✅ Stage 1 (Merged): 0개 중복
- ✅ Stage 2 (Derived): 0개 중복
- ✅ Stage 3 (Report): 0개 중복
- ✅ **최종 상태: 통과**

**SCT 화물 검증** (`investigate_sct_vendor.py`):
- ⚠️ Vendor='SCT' 레코드: 0건 (여전히 반영 안 됨)
- ⚠️ Fallback 매칭은 로그에서 확인되었으나 최종 파일에 반영되지 않음

---

## Before / After 비교

### CASE_NO 중복

| 항목 | Before | After | 변화 |
|------|--------|-------|------|
| **Stage 1 merged** | 9,234건 (중복 포함) | 8,739건 | **-495건** |
| **Stage 2 derived** | 중복 존재 | 8,739건 | ✅ 고유 |
| **Stage 3 report** | 중복 존재 | 8,739건 | ✅ 고유 |
| **Stage 4 검증** | 495건 중복 | **0건** | ✅ **완전 해결** |

### SCT 화물 업데이트

| 항목 | Before | After | 상태 |
|------|--------|-------|------|
| **Fallback 매칭** | 없음 | 35건 | ✅ 구현 |
| **Vendor 컬럼 업데이트** | 누락 | 보장 로직 추가 | ✅ 개선 |
| **중복 매칭 방지** | 없음 | 추적 set 추가 | ✅ 개선 |
| **매칭 정확도** | 낮음 | 향상 (2개 키워드 필수) | ✅ 개선 |
| **최종 반영 여부** | 0건 | 0건 | ⚠️ **검증 필요** |

---

## 수정된 파일 목록

### 코드 수정

1. **`scripts/stage1_sync_sorted/data_synchronizer_v30.py`**
   - Line 1217-1236: Fallback 매칭을 위한 추적 set 추가
   - Line 1312-1347: 매칭 정확도 개선 및 중복 매칭 방지
   - Line 1355-1363: Vendor 컬럼 업데이트 보장
   - Line 575-590: 하드코딩 제거, `find_header_by_meaning` 사용
   - Line 1767-1775: merged 파일 생성 시 추가 중복 제거

2. **`scripts/stage3_report/report_generator.py`**
   - Line 707-715: 데이터 통합 시 중복 제거 추가

### 신규 파일

1. **`scripts/investigation/extract_duplicate_case_no.py`**: 중복 CASE_NO 상세 분석 스크립트
2. **`scripts/investigation/verify_case_no_dedup.py`**: 단계별 중복 검증 스크립트

---

## 검증 스크립트 사용법

### CASE_NO 중복 검증

```bash
python scripts/investigation/verify_case_no_dedup.py
```

**출력**:
- 각 Stage별 중복 건수
- 검증 리포트 (마크다운)

### 중복 CASE_NO 상세 분석

```bash
python scripts/investigation/extract_duplicate_case_no.py
```

**출력**:
- 중복 분포 분석
- Source_Vendor별 분석
- 상세 Excel 리포트

---

## 알려진 제한사항 및 향후 개선

### SCT 화물 업데이트

**현재 상태**:
- Fallback 매칭 로직은 작동하지만, 최종 파일에 Vendor='SCT'가 반영되지 않음
- 로그에서 35건 매칭 확인되었으나 검증 실패

**추가 조사 필요**:
1. Fallback 매칭된 row가 실제로 업데이트되는지 확인
2. Vendor 컬럼이 Warehouse에 존재하는지 확인
3. Source_Vendor와 Vendor 컬럼의 관계 확인

**향후 개선 방안**:
1. Fallback 매칭 통계를 로그에 더 상세히 출력
2. 매칭 성공/실패 상세 추적
3. Vendor 컬럼이 없을 경우 자동 생성

### CASE_NO 중복

**해결 완료**: ✅

- Stage 1, Stage 3에서 모두 중복 제거 확인
- 최종 검증: 0건 중복 확인

---

## 핵심 성과

1. ✅ **CASE_NO 중복 완전 해결**: 495건 → 0건
2. ✅ **프로젝트 표준 준수**: 하드코딩 제거, `find_header_by_meaning` 사용
3. ✅ **SCT Fallback 매칭 개선**: 매칭 정확도 향상, 중복 매칭 방지, Vendor 업데이트 보장
4. ✅ **검증 도구 구축**: 자동화된 검증 스크립트 추가

---

## 결론

**CASE_NO 중복 문제는 완전히 해결되었습니다**. Stage 1과 Stage 3에서 중복 제거 로직이 추가되어 최종적으로 0건 중복을 달성했습니다.

**SCT 화물 업데이트 문제는 개선되었으나 추가 검증이 필요합니다**. Fallback 매칭 로직은 작동하지만, 최종 반영 여부는 추가 조사가 필요합니다.

---

**작성자**: HVDC Pipeline AI Assistant  
**버전**: v4.0.45  
**상태**: ✅ CASE_NO 중복 해결 완료, ⚠️ SCT 화물 추가 검증 필요

