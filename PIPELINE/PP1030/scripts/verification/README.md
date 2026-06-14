# 검증 스크립트

파이프라인 검증을 위한 통합 스크립트 모음입니다.

## 주요 스크립트

### `complete.py` - 통합 검증 스크립트 (메인)

모든 검증 기능을 통합하여 한 번에 실행합니다.

**사용법:**
```bash
# 모든 검증 실행
python scripts/verification/complete.py --all

# 특정 검증만 실행
python scripts/verification/complete.py --merge
python scripts/verification/complete.py --colors --color-mode=ultra_fast
python scripts/verification/complete.py --dedup
python scripts/verification/complete.py --master-warehouse

# 보고서만 생성
python scripts/verification/complete.py --report-only
```

**옵션:**
- `--all`: 모든 검증 실행 (기본값)
- `--merge`: 병합 로직만 검증
- `--colors`: Excel 색상만 검증
- `--dedup`: 중복 제거만 검증
- `--master-warehouse`: Master-Warehouse 업데이트만 검증
- `--report-only`: 기존 결과로 보고서만 생성
- `--color-mode`: Excel 색상 검증 모드 (ultra_fast, basic, batch, full)
- `--sheets`: 검증할 시트 수 (기본: 3)
- `--output`: 종합 보고서 출력 경로

## 개별 검증 스크립트

### `merge_logic.py`
병합 로직 검증 (Master-Warehouse, 파이프라인 단계, 중복 제거)

### `excel_colors.py`
Excel 색상 검증 (ORANGE, YELLOW)

### `dedup_logic.py`
중복 제거 로직 검증

### `master_warehouse.py`
Master-Warehouse 업데이트 로직 검증

### `merge_detailed.py`
병합 상세 검증

### `pipeline_merge.py`
파이프라인 병합 검증

## 결과 파일

- `docs/reports/comprehensive_verification_results.json`: 검증 결과 JSON
- `docs/reports/COMPREHENSIVE_VERIFICATION_REPORT.md`: 종합 보고서
- `docs/reports/merge_logic_verification_results.json`: 병합 로직 검증 결과
- `docs/reports/excel_color_verification.json`: Excel 색상 검증 결과

## 공통 유틸리티

`scripts/core/verification_utils.py`에서 공통 함수 제공:
- `print_section()`: 섹션 제목 출력
- `find_case_col()`: Case No 컬럼 찾기
- `normalize_case_no()`: Case No 정규화
- `load_data_file()`: 데이터 파일 안전 로드
- `save_results_json()`: 결과 JSON 저장

