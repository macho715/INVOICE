# 루트 폴더 파일 중복 내용 검증 보고서

**생성 시간**: 2025-11-04

## 검증 목적

루트 폴더에 있는 검증 스크립트들의 중복 코드와 내용을 확인하여 정리 계획 수립

## 중복 내용 분석 결과

### 1. `print_section` 함수 중복

**공통 유틸리티 위치**: `scripts/core/verification_utils.py` (Line 13-17)

**중복 정의 위치**:
- ✅ `verify_all_merge_logic.py` (Line 17-21) - **중복 발견**
- ✅ `verify_pipeline_merge.py` (Line 17-21) - **중복 발견**
- ⚠️ `scripts/legacy/verify_excel_colors_*.py` (여러 파일) - Legacy이므로 제외

**중복 내용**:
```python
def print_section(title: str, char="="):
    """섹션 제목 출력"""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")
```

**해결 방안**: 
- `verify_all_merge_logic.py`에서 `print_section` 제거 → `from scripts.core.verification_utils import print_section`
- `verify_pipeline_merge.py`에서 `print_section` 제거 → `from scripts.core.verification_utils import print_section`

### 2. `find_case_col` 함수 중복

**공통 유틸리티 위치**: `scripts/core/verification_utils.py` (Line 20-31)

**중복 정의 위치**:
- ✅ `verify_all_merge_logic.py` (Line 72-81) - **중복 발견** (로컬 함수)
- ⚠️ `verify_excel_colors_unified.py` (Line 249) - `find_case_col_idx` (다른 함수, 제외)

**중복 내용**:
```python
def find_case_col(df):
    """데이터프레임에서 Case No 컬럼 찾기"""
    case_patterns = ["caseno", "case no", "case number"]
    for col in df.columns:
        col_str = str(col).lower().strip()
        if any(p in col_str for p in case_patterns):
            return col
        if col_str in ["no", "no.", "no ."]:
            return col
    return None
```

**차이점**:
- `verification_utils.py`: 타입 힌트 있음, 반환 타입 `Optional[str]`
- `verify_all_merge_logic.py`: 타입 힌트 없음, 로컬 함수

**해결 방안**:
- `verify_all_merge_logic.py`의 로컬 `find_case_col` 제거 → `from scripts.core.verification_utils import find_case_col` 사용

### 3. 파일 경로 처리 로직 중복

**중복 위치**:
- `verify_all_merge_logic.py`: 파일 경로 직접 정의
- `verify_merge_detailed.py`: 파일 경로 직접 정의
- `verify_pipeline_merge.py`: 파일 경로 직접 정의

**공통 패턴**:
```python
master_file = Path("data/raw/Case List(HE).xlsx")
warehouse_file = Path("data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx")
stage1_multi = Path("data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx")
```

**해결 방안**:
- `verification_utils.py`에 파일 경로 상수 추가 또는 `load_data_file()` 함수 활용

### 4. Stage 1 분석 로직 중복

**중복 위치**:
- `verify_all_merge_logic.py` - `verify_pipeline_stages()` 함수
- `verify_merge_detailed.py` - `analyze_stage1_sheet_merge()` 함수
- `verify_pipeline_merge.py` - `analyze_stage1_merge()` 함수

**중복 내용**:
- Stage 1 멀티 시트 파일 분석
- Stage 1 병합 파일 분석
- Source_Sheet 분포 확인
- Source_Vendor 분포 확인

**해결 방안**:
- 공통 분석 함수를 `verification_utils.py`에 추출
- 각 스크립트는 공통 함수를 호출하도록 수정

## 중복 제거 우선순위

### 우선순위 1 (즉시 제거)
1. `print_section` 함수 중복 (2개 파일)
2. `find_case_col` 함수 중복 (1개 파일)

### 우선순위 2 (리팩토링)
3. 파일 경로 상수화
4. Stage 1 분석 로직 통합

## 정리 계획 업데이트

기존 정리 계획에 다음 항목 추가:

### Phase 7-1: 중복 코드 제거
- `print_section` 함수 중복 제거
- `find_case_col` 함수 중복 제거
- 파일 경로 상수화
- 공통 분석 로직 추출

### Phase 7-2: 임포트 경로 업데이트
- 모든 검증 스크립트에서 `verification_utils` 임포트 추가
- 중복 함수 제거 후 임포트로 교체

## 검증 결과 요약

| 항목 | 중복 발견 | 우선순위 | 해결 방법 |
|------|----------|----------|-----------|
| `print_section` 함수 | 2개 파일 | 높음 | verification_utils 임포트 |
| `find_case_col` 함수 | 1개 파일 | 높음 | verification_utils 임포트 |
| 파일 경로 처리 | 3개 파일 | 중간 | 상수화 또는 함수화 |
| Stage 1 분석 로직 | 3개 파일 | 중간 | 공통 함수 추출 |

## 다음 단계

1. 중복 코드 제거 작업 실행
2. 임포트 경로 업데이트
3. 실행 테스트
4. 최종 검증

