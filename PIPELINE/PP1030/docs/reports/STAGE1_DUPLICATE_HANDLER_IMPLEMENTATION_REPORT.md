# Stage 1 중복 케이스 처리 구현 완료 보고서

## 📋 문서 정보
- **작성일**: 2025-11-02
- **작업 내용**: Stage 1 중복 Case No. 처리 로직 구현
- **버전**: v1.0
- **상태**: ✅ 완료

---

## 1. 개요

### 1.1 문제 상황
Stage 1 단계에서 시트 병합(`pd.concat`) 후 `Case No.` 기준 전역 중복 제거가 적용되지 않아, v3.4→v3.6로 갈수록 중복이 누적되는 문제가 발생했습니다.

**실제 데이터 분석 결과:**
- Raw 파일: Case List, RIL 시트에 중복 10개
- Synced 파일: Case List, RIL 시트에 중복 193개로 증가
- **원인**: 시트별 로컬 중복은 감지되었으나, **워크북 전역 중복 제거 로직 부재**

### 1.2 해결 방안
`core/duplicate_handler.py` 신규 모듈을 추가하여 다음 기능을 구현:
- **의미론적 헤더 탐지**: `SemanticMatcher`를 활용한 Case No. 컬럼 자동 탐지
- **정규화 키 생성**: Case No. 값을 정규화하여 동일 키 생성
- **시트 내 중복 플래깅**: 개별 시트에서 중복 감지 및 "고유/중복" 라벨 추가
- **워크북 전역 중복 제거**: 모든 시트 병합 후 전역 기준으로 중복 제거
- **Excel A열 표시**: "고유 중복" 컬럼을 첫 번째 컬럼으로 자동 삽입

---

## 2. 구현 단계별 상세 내용

### Step 1: core/duplicate_handler.py 모듈 생성

**파일 경로**: `scripts/core/duplicate_handler.py`

**생성 내용**:
1. **NormalizationProfile**: 정규화 규칙 설정을 위한 dataclass
   - `squeeze_spaces`: 공백 제거 여부
   - `uppercase`: 대문자 변환 여부
   - `keep_chars`: 허용 문자 집합
   - `unify_sep`: 구분자 통일 여부 (_, / → -)
   - `zero_pad_digits`: 숫자 제로 패딩 자릿수 (선택)

2. **정규화 함수들**:
   - `_normalize_case_no_scalar()`: 스칼라 값 정규화
   - `normalize_case_series()`: 시리즈 전체 정규화

3. **컬럼 탐지 함수들**:
   - `default_semantic_finder()`: SemanticMatcher 사용 또는 휴리스틱 fallback
   - `detect_case_column()`: Case No. 컬럼 자동 탐지

4. **중복 처리 함수들**:
   - `mark_duplicates()`: 시트 내 중복 마킹 및 플래그 생성
   - `compute_global_dup_flags()`: 전역 중복 플래그 계산 및 요약 생성
   - `drop_duplicates_by_case()`: Case No. 기준 중복 제거
   - `drop_duplicates_global()`: 여러 DataFrame 전역 중복 제거

5. **Excel 어댑터**:
   - `inject_excel_dup_column()`: Excel 파일에 "고유 중복" 컬럼 주입

6. **검증 함수**:
   - `validate_duplicate_removal()`: 중복 제거 검증 및 통계 생성

**핵심 코드 구조**:
```python
# 정규화 예시
def _normalize_case_no_scalar(x: object, prof: NormalizationProfile) -> str:
    if x is None or pd.isna(x):
        return ""
    s = str(x)
    s = unicodedata.normalize("NFKC", s).strip()  # 전각→반각
    if prof.squeeze_spaces:
        s = re.sub(r"\s+", "", s)
    if prof.unify_sep:
        s = re.sub(r"[_/]", "-", s)
    if prof.uppercase:
        s = s.upper()
    # 제로 패딩 (선택)
    if prof.zero_pad_digits:
        m = re.match(r"^(.*?)(\d+)$", s)
        if m:
            head, digits = m.groups()
            s = f"{head}{int(digits):0{prof.zero_pad_digits}d}"
    return s

# 중복 마킹 예시
def mark_duplicates(df, semantic_finder=None, keep="first", profile=None):
    out = df.copy()
    col = detect_case_column(out, semantic_finder=semantic_finder, required=True)
    key = normalize_case_series(out[col], profile)
    out["__case_key__"] = key
    dup_mask = out.duplicated(subset=["__case_key__"], keep=keep)
    out["__dup_label__"] = np.where(dup_mask, "중복", "고유")
    return out, dup_mask
```

---

### Step 2: core/__init__.py 업데이트

**파일 경로**: `scripts/core/__init__.py`

**변경 내용**:
- `duplicate_handler` 모듈에서 모든 함수 import 추가
- `__all__` 리스트에 export할 함수명 추가

**추가된 import**:
```python
from .duplicate_handler import (
    NormalizationProfile,
    normalize_case_series,
    detect_case_column,
    mark_duplicates,
    compute_global_dup_flags,
    drop_duplicates_by_case,
    drop_duplicates_global,
    inject_excel_dup_column,
    validate_duplicate_removal,
)
```

---

### Step 3: data_synchronizer_v30.py 통합

**파일 경로**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`

#### 3.1 Import 추가 (Line 70-86)

```python
# DUP-GUARD imports (new)
from scripts.core.duplicate_handler import (
    compute_global_dup_flags,
    drop_duplicates_by_case,
    NormalizationProfile,
    mark_duplicates,
    detect_case_column,
)
try:
    from scripts.core import SemanticMatcher as CoreSemanticMatcher
    _SEM = CoreSemanticMatcher()
    def _find_col(df, tag, required=False):
        return _SEM.find_column(df, tag, required=required)
except Exception:
    def _find_col(df, tag, required=False):
        from scripts.core.duplicate_handler import default_semantic_finder
        return default_semantic_finder(df, tag, required=required)
```

#### 3.2 개별 시트 저장 직전: 중복 마킹 (Line 1850-1862)

**통합 지점**: `synchronize()` 메서드 내, 개별 시트를 Excel로 저장하기 직전

```python
# Apply standard 63-column header order before saving
df_reordered = reorder_dataframe_columns(
    df, is_stage2=False, keep_unlisted=False, use_semantic_matching=True
)
# DUP-GUARD (A): within-sheet duplicate flags + A-column injection
try:
    df_with_flag, dup_mask = mark_duplicates(
        df_reordered, semantic_finder=_find_col, keep="first"
    )
    df_reordered = df_with_flag
    # place visible label as first column for Excel output
    if "고유 중복" not in df_reordered.columns:
        df_reordered.insert(0, "고유 중복", np.where(dup_mask, "중복", "고유"))
except Exception as e:
    print(f"    [WARNING][DUP-GUARD][{sheet_name}] skip marking duplicates: {e}")
df_reordered.to_excel(writer, sheet_name=clean_sheet_name, index=False)
```

**작동 원리**:
1. `reorder_dataframe_columns()`로 표준 헤더 순서 적용
2. `mark_duplicates()` 호출하여 시트 내 중복 감지
3. `__dup_label__` 컬럼을 "고유 중복"으로 이름 변경 후 첫 번째 컬럼으로 삽입
4. Excel 파일로 저장

#### 3.3 병합 후: 전역 중복 제거 (Line 1914-1921)

**통합 지점**: 모든 시트를 `pd.concat()`으로 병합한 직후

```python
# Concatenate all sheets
merged_df = pd.concat(combined_dfs, ignore_index=True, sort=False)
print(f"  - 합쳐진 데이터: {len(merged_df)}행, {len(merged_df.columns)}컬럼")
print(f"  - Source_Sheet 컬럼 추가됨")
# DUP-GUARD (B): workbook-level dedup by Case key
try:
    merged_df = drop_duplicates_by_case(
        merged_df, semantic_finder=_find_col, keep="first"
    )
    print(f"  - 전역 중복 제거 후: {len(merged_df)}행")
except Exception as e:
    print(f"  [WARNING][DUP-GUARD][merge] skip global dedup: {e}")
```

**작동 원리**:
1. 모든 시트 병합 완료
2. `drop_duplicates_by_case()` 호출하여 Case No. 기준 중복 제거
3. `keep="first"` 정책으로 첫 번째 발생만 유지

#### 3.4 병합 파일 저장 전: "고유 중복" 컬럼 추가 (Line 1934-1949)

**통합 지점**: 병합 파일을 Excel로 저장하기 직전

```python
# Apply standard 63-column header order before saving
merged_df_reordered = reorder_dataframe_columns(
    merged_df, is_stage2=False, keep_unlisted=False, use_semantic_matching=True
)
# DUP-GUARD: Add "고유 중복" column to merged file if not present
if "고유 중복" not in merged_df_reordered.columns and "__dup_label__" in merged_df_reordered.columns:
    merged_df_reordered.insert(0, "고유 중복", merged_df_reordered["__dup_label__"])
elif "고유 중복" not in merged_df_reordered.columns:
    # If no __dup_label__, compute it
    try:
        merged_with_flag, dup_mask = mark_duplicates(
            merged_df_reordered, semantic_finder=_find_col, keep="first"
        )
        merged_df_reordered = merged_with_flag
        if "고유 중복" not in merged_df_reordered.columns:
            merged_df_reordered.insert(0, "고유 중복", np.where(dup_mask, "중복", "고유"))
    except Exception as e:
        print(f"  [WARNING][DUP-GUARD][merged] skip adding duplicate column: {e}")
with pd.ExcelWriter(merged_output_path, engine="openpyxl") as writer:
    merged_df_reordered.to_excel(writer, sheet_name="Merged Data", index=False)
```

---

### Step 4: 코드 품질 검증

#### 4.1 Black 포맷팅
```bash
black scripts/core/duplicate_handler.py scripts/core/__init__.py scripts/stage1_sync_sorted/data_synchronizer_v30.py
```
**결과**: 2개 파일 포맷팅 완료

#### 4.2 Import 테스트
```bash
python -c "from scripts.core.duplicate_handler import mark_duplicates, drop_duplicates_by_case, NormalizationProfile; print('Import successful')"
python -c "from scripts.core import mark_duplicates, drop_duplicates_by_case; print('Core __init__ export successful')"
python -c "from scripts.stage1_sync_sorted.data_synchronizer_v30 import DataSynchronizerV30; print('DataSynchronizerV30 import successful')"
```
**결과**: 모든 import 성공

---

### Step 5: 단위 테스트 작성

**파일 경로**: `tests/core/test_duplicate_handler.py`

**테스트 케이스 구성**:

1. **TestNormalization** (4개 테스트)
   - `test_normalize_basic`: 기본 정규화 (대문자, 공백 제거)
   - `test_normalize_separator_unification`: 구분자 통일 (_, / → -)
   - `test_normalize_zero_pad`: 숫자 제로 패딩
   - `test_normalize_nan_handling`: NaN/None 처리

2. **TestDetectCaseColumn** (3개 테스트)
   - `test_detect_case_column_exists`: Case No. 컬럼 존재 시 탐지
   - `test_detect_case_column_fallback`: 휴리스틱 fallback 테스트
   - `test_detect_case_column_missing_required`: 필수 컬럼 누락 시 에러

3. **TestMarkDuplicates** (2개 테스트)
   - `test_mark_duplicates_basic`: 기본 중복 마킹
   - `test_mark_duplicates_no_duplicates`: 중복 없을 때 처리

4. **TestDropDuplicatesByCase** (2개 테스트)
   - `test_drop_duplicates_basic`: 기본 중복 제거
   - `test_drop_duplicates_keep_last`: keep="last" 정책

5. **TestComputeGlobalDupFlags** (2개 테스트)
   - `test_compute_global_dup_flags_basic`: 기본 전역 플래그 계산
   - `test_compute_global_dup_flags_no_duplicates`: 중복 없을 때 처리

6. **TestDropDuplicatesGlobal** (1개 테스트)
   - `test_drop_duplicates_global_basic`: 전역 중복 제거

7. **TestValidateDuplicateRemoval** (1개 테스트)
   - `test_validate_duplicate_removal`: 검증 함수 테스트

**테스트 실행 명령**:
```bash
python -m pytest tests/core/test_duplicate_handler.py -v
```

**테스트 결과**: ✅ **15개 테스트 모두 통과**

---

## 3. 실행 방법

### 3.1 Stage 1 파이프라인 실행

**기본 명령**:
```bash
python run/run_pipeline.py --stage 1
```

**실행 단계**:
1. **PHASE 1: 파일 로드**
   - Master 파일 로드: `Case List.xlsx`
   - Warehouse 파일 로드: `HVDC WAREHOUSE_HITACHI(HE).xlsx`
   - 각 시트별로 DataFrame 생성

2. **PHASE 2: 시트별 동기화**
   - 공통 시트 매칭 및 데이터 병합
   - 개별 시트 처리

3. **PHASE 3: 저장**
   - **개별 시트 저장**: 각 시트에 "고유 중복" 컬럼 추가 후 저장
   - **병합 파일 생성**: 모든 시트 병합 → 전역 중복 제거 → "고유 중복" 컬럼 추가 → 저장

### 3.2 출력 파일

**개별 시트 파일**:
- 경로: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx`
- 내용: 각 시트별로 "고유 중복" 컬럼이 첫 번째 컬럼으로 포함됨

**병합 파일**:
- 경로: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`
- 내용: 모든 시트가 병합되고 전역 중복 제거 완료, "고유 중복" 컬럼 포함

### 3.3 실행 결과 확인

**병합 파일 확인 스크립트**:
```python
import pandas as pd

df = pd.read_excel('data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx', 
                   sheet_name='Merged Data')

print(f"총 행 수: {len(df):,}개")
print(f"'고유 중복' 컬럼 존재: {'고유 중복' in df.columns}")
if "고유 중복" in df.columns:
    print(f"고유/중복 분포:\n{df['고유 중복'].value_counts()}")
print(f"Case No. 고유: {df['Case No.'].nunique():,}개")
print(f"Case No. 중복: {df['Case No.'].duplicated().sum():,}개")
```

---

## 4. 실행 결과 및 검증

### 4.1 Stage 1 실행 결과 (2025-11-02)

**실행 시간**: 79.30초

**처리 통계**:
- 업데이트: 1,029개 셀
- 신규 레코드: 168개
- 출력 파일 생성: 2개 (개별 시트 + 병합 파일)

### 4.2 중복 처리 검증 결과

**병합 파일 분석**:
- **총 행 수**: 7,176개
- **총 컬럼 수**: 45개
- **"고유 중복" 컬럼**: ✅ 첫 번째 컬럼(위치 0)에 정상 추가
- **고유/중복 분포**: 모든 7,176개 행이 "고유"로 표시
- **Case No. 고유**: 7,176개
- **Case No. 중복**: 0개 ✅

**전역 중복 제거 효과**:
- 병합 전 데이터: 7,350행
- 병합 후(중복 제거): 7,176행
- **제거된 중복**: 174개 ✅

**개별 시트 파일 분석**:
- Case List, RIL: 7,169행, 35개 중복 감지
- HE Local: 79행, 모두 고유
- HE-0214,0252 (Capacitor): 102행, 모두 고유

### 4.3 테스트 결과

**단위 테스트**: ✅ 15개 테스트 모두 통과
```
tests/core/test_duplicate_handler.py::TestNormalization::test_normalize_basic PASSED
tests/core/test_duplicate_handler.py::TestNormalization::test_normalize_separator_unification PASSED
tests/core/test_duplicate_handler.py::TestNormalization::test_normalize_zero_pad PASSED
tests/core/test_duplicate_handler.py::TestNormalization::test_normalize_nan_handling PASSED
tests/core/test_duplicate_handler.py::TestDetectCaseColumn::test_detect_case_column_exists PASSED
tests/core/test_duplicate_handler.py::TestDetectCaseColumn::test_detect_case_column_fallback PASSED
tests/core/test_duplicate_handler.py::TestDetectCaseColumn::test_detect_case_column_missing_required PASSED
tests/core/test_duplicate_handler.py::TestMarkDuplicates::test_mark_duplicates_basic PASSED
tests/core/test_duplicate_handler.py::TestMarkDuplicates::test_mark_duplicates_no_duplicates PASSED
tests/core/test_duplicate_handler.py::TestDropDuplicatesByCase::test_drop_duplicates_basic PASSED
tests/core/test_duplicate_handler.py::TestDropDuplicatesByCase::test_drop_duplicates_keep_last PASSED
tests/core/test_duplicate_handler.py::TestComputeGlobalDupFlags::test_compute_global_dup_flags_basic PASSED
tests/core/test_duplicate_handler.py::TestComputeGlobalDupFlags::test_compute_global_dup_flags_no_duplicates PASSED
tests/core/test_duplicate_handler.py::TestDropDuplicatesGlobal::test_drop_duplicates_global_basic PASSED
tests/core/test_duplicate_handler.py::TestValidateDuplicateRemoval::test_validate_duplicate_removal PASSED
```

---

## 5. 생성/수정된 파일 목록

### 5.1 신규 생성 파일

1. **`scripts/core/duplicate_handler.py`**
   - 크기: ~270 라인
   - 주요 함수: 10개
   - 역할: 중복 처리 핵심 로직

2. **`tests/core/test_duplicate_handler.py`**
   - 크기: ~230 라인
   - 테스트 케이스: 15개
   - 역할: 단위 테스트

### 5.2 수정된 파일

1. **`scripts/core/__init__.py`**
   - 변경: `duplicate_handler` 모듈 export 추가
   - 추가된 함수: 9개

2. **`scripts/stage1_sync_sorted/data_synchronizer_v30.py`**
   - 변경 사항:
     - Import 추가 (Line 70-86)
     - 개별 시트 저장 직전 중복 마킹 (Line 1850-1862)
     - 병합 후 전역 중복 제거 (Line 1914-1921)
     - 병합 파일 저장 전 "고유 중복" 컬럼 추가 (Line 1934-1949)

---

## 6. 기술적 세부사항

### 6.1 정규화 알고리즘

**정규화 순서**:
1. **NFKC 정규화**: 전각→반각 변환 (예: `ＣＡＳＥ` → `CASE`)
2. **공백 제거**: 모든 공백 문자 제거 (옵션)
3. **문자 필터링**: 허용 문자만 유지 (영문자, 숫자, 구분자)
4. **구분자 통일**: `_`, `/` → `-` (옵션)
5. **대문자 변환**: 모든 문자 대문자로 변환 (옵션)
6. **제로 패딩**: 숫자 부분을 지정 자릿수로 패딩 (옵션)

**예시**:
```
입력: "Case-001", "case 002", "CASE_003"
출력: "CASE-001", "CASE002", "CASE-003"
```

### 6.2 의미론적 헤더 탐지

**탐지 방식**:
1. **SemanticMatcher 사용** (우선):
   - `SemanticMatcher().find_column(df, "case_number", required=True)`
   - HeaderRegistry의 alias 목록 활용

2. **휴리스틱 Fallback**:
   - 컬럼명에서 "case" 또는 "package" 패턴 검색
   - 정규식: `r"(case|package)"` (대소문자 무시)

**장점**:
- 헤더 변형 자동 대응 (예: "Case No.", "CaseNo", "CASE_NO")
- 다국어 헤더 지원 가능
- 하드코딩 제거

### 6.3 중복 처리 정책

**시트 내 중복 마킹**:
- `keep="first"`: 첫 번째 발생을 유지, 나머지 마킹
- `keep="last"`: 마지막 발생을 유지
- `keep="False"`: 모든 중복 제거

**전역 중복 제거**:
- 정규화된 `__case_key__` 기준으로 중복 판단
- 시트 간 중복도 감지 및 제거
- 첫 번째 발생만 유지 (`keep="first"`)

---

## 7. 에러 처리 및 안전장치

### 7.1 예외 처리

**Case No. 컬럼 탐지 실패**:
```python
try:
    col = detect_case_column(tdf, semantic_finder=semantic_finder, required=True)
except Exception:
    col = None
    tdf[_CASE_KEY] = ""
    tdf[_DUP_LABEL] = ""  # header unresolved
```

**중복 마킹 실패**:
```python
try:
    df_with_flag, dup_mask = mark_duplicates(df_reordered, ...)
    # 처리 계속
except Exception as e:
    print(f"    [WARNING][DUP-GUARD][{sheet_name}] skip marking duplicates: {e}")
    # 원본 데이터로 계속 진행
```

### 7.2 Fallback 메커니즘

1. **SemanticMatcher 실패 시**: 휴리스틱 탐지로 fallback
2. **중복 처리 실패 시**: 경고 메시지 출력 후 원본 데이터 유지
3. **정규화 실패 시**: 빈 문자열 반환

---

## 8. 성능 고려사항

### 8.1 벡터화 연산
- `pandas.Series.map()` 활용한 벡터화 정규화
- `pandas.DataFrame.duplicated()` 벡터화 중복 감지
- 대용량 데이터에서도 효율적 처리

### 8.2 메모리 효율
- DataFrame copy 최소화
- 필요한 컬럼만 추가 (`__case_key__`, `__dup_label__`)

---

## 9. 향후 개선 사항

### 9.1 단기 개선 (1-2주)
- [ ] 성능 벤치마크 측정 (10k rows/시트 × N 시트)
- [ ] 로깅 개선 (중복 처리 통계 자동 보고)
- [ ] 병합 파일의 "고유 중복" 컬럼 정렬 최적화

### 9.2 중기 개선 (1-2개월)
- [ ] 정규화 프로파일 설정 파일화 (YAML/JSON)
- [ ] 중복 제거 정책 선택 가능 (keep="first"/"last"/"False")
- [ ] 중복 원인 분석 리포트 생성

### 9.3 장기 개선 (3-6개월)
- [ ] Stage 2/3에도 동일 로직 적용
- [ ] 중복 패턴 자동 학습 및 분류
- [ ] 실시간 중복 감지 대시보드

---

## 10. 참고 문서

### 10.1 관련 문서
- `patch1102.md`: 초기 구현 계획 및 코드 스켈레톤
- `docs/reports/FlowCode_v35_완료보고서.md`: Flow Code v3.5 구현 보고서
- `scripts/core/README.md`: Core 모듈 개요

### 10.2 코드 참조
- `scripts/core/semantic_matcher.py`: 의미론적 헤더 매칭 엔진
- `scripts/core/header_registry.py`: 헤더 정의 중앙 레지스트리
- `scripts/stage1_sync_sorted/data_synchronizer_v30.py`: Stage 1 메인 스크립트

---

## 11. 결론

Stage 1 중복 Case No. 처리 로직이 성공적으로 구현되었습니다. 

### 주요 성과
1. ✅ **전역 중복 제거**: 174개 중복 자동 제거
2. ✅ **의미론적 헤더 탐지**: 하드코딩 제거, 유연성 향상
3. ✅ **사용자 친화적 표시**: "고유 중복" 컬럼으로 시각적 확인 가능
4. ✅ **코드 품질**: 단위 테스트 15개 통과, Black 포맷팅 적용

### 검증 완료
- ✅ Stage 1 파이프라인 정상 실행
- ✅ 병합 파일 중복 제거 검증
- ✅ 개별 시트 중복 마킹 검증
- ✅ 단위 테스트 모두 통과

**모든 목표 달성 및 프로덕션 준비 완료** ✅

---

**문서 버전**: v1.0  
**최종 업데이트**: 2025-11-02  
**작성자**: AI Assistant (Cursor)

