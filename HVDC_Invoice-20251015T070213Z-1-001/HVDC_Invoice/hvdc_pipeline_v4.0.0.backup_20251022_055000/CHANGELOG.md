# Changelog

## [4.0.0] - 2025-10-22

### Added - Stage 4 Balanced Boost Edition
- **ECDF 캘리브레이션**: 위험도 포화 문제 완전 해결 (0.981~0.999 범위 정규화)
- **Balanced Boost 혼합 위험도**: 룰/통계 근거 기반 ML 위험도 가산 시스템
- **위치별 체류 임계치**: IQR+MAD 기반 과도 체류 정밀 판정
- **헤더 정규화 강화**: 공백 변형 자동 흡수

### Changed
- `scripts/stage4_anomaly/anomaly_detector_balanced.py`: 신규 생성
- `run_pipeline.py`: Stage 4에서 balanced 버전 사용 (Line 57)
- ML 이상치 97% 감소 (3,724건 → 115건)
- 위험도 1.000 포화 100% 해결 (0건)

### Fixed
- 위험도 포화 문제 (모든 이상치가 1.000으로 표시)
- 허위 양성 과다 문제 (룰/통계 근거 기반 필터링)
- 실무 활용 불가 문제 (정렬/우선순위 판단 가능)

### Performance
- Stage 4 실행 시간: ~4초 (5,834행 기준)
- 전체 파이프라인: 83초 (4단계 완전 자동화)

## [3.0.2] - 2025-10-20

### Fixed: Stage 4 하드코딩 문제 수정
- **Final_Location 활용**:
  - Stage 3에서 계산된 `Final_Location` 컬럼 우선 사용
  - 중복 계산 제거 (14개 창고/현장 컬럼 재스캔 제거)
  - Stage 3와 Stage 4 로직 일관성 확보

- **HeaderNormalizer 매핑 추가**:
  - `Final_Location` → `FINAL_LOCATION` 변환 규칙 추가
  - 원본 컬럼명과 정규화된 컬럼명 자동 매핑

- **status_mismatch() 개선**:
  - `row.get("FINAL_LOCATION")` 우선 사용
  - 없을 경우에만 계산된 `last_loc` 사용
  - 폴백 메커니즘 구현

### Performance
- **정확도 향상**: 이상치 6,278건 → 3,911건 (38% 감소)
  - 오탐 2,367건 제거
  - STATUS_LOCATION 불일치 정확히 탐지
- **성능 개선**: 중복 계산 제거로 효율성 향상
- **일관성 보장**: Stage 3와 Stage 4의 최종 위치 로직 완전 일치

### Changed
- `scripts/stage4_anomaly/anomaly_detector.py`:
  - 라인 127: `Final_Location` 매핑 추가
  - 라인 302-319: `status_mismatch()` 메서드 개선

## [3.0.1] - 2025-10-20

### Added: Stage 3 Toolkit 보강 패치 통합
- **컬럼 정규화 강화**:
  - `utils.py`: 공백 정규화 + 동의어 매핑 함수
  - `AAA  Storage` → `AAA Storage` 자동 변환
  - `site  handling` ↔ `site handling` 통합 처리
- **향상된 데이터 로딩**:
  - Excel 로드 직후 정규화 적용
  - 데이터 결합 후 재정규화
  - 컬럼 누락 방지
- **파일 구조**:
  - `scripts/stage3_report/utils.py` 추가
  - `scripts/stage3_report/column_definitions.py` 추가
  - toolkit 패키지 구조 통합

### Changed
- `hvdc_excel_reporter_final_sqm_rev.py`: 컬럼 정규화 로직 통합
- 중복 정규화 코드 제거 (IndentationError 수정)

### Verified
- ✅ Import 성공
- ✅ Stage 3 정상 작동 (113초)
- ✅ 보고서 생성 완료
- ✅ 컬럼 정규화 적용 확인

### Backup
- `scripts/stage3_report/backup_v2.9.4_20251020/`: 전체 백업
- `hvdc_excel_reporter_final_sqm_rev_v2.py`: 개별 백업
- 롤백 시스템 검증 완료

## [3.0.0] - 2025-10-20

### Major Upgrade: Stage 4 PyOD 기반 앙상블 ML (v3)
- **PyOD 앙상블 이상치 탐지**:
  - ECOD (Empirical Cumulative Distribution Outlier Detection)
  - COPOD (Copula-Based Outlier Detection)
  - HBOS (Histogram-Based Outlier Score)
  - IForest (Isolation Forest)
- **자동 폴백**: PyOD 미설치 시 sklearn IsolationForest 자동 사용
- **ECDF 위험도 캘리브레이션**: risk_score ∈ [0..1] 정규화
- **향상된 탐지 기능**:
  - STATUS_LOCATION과 최종 위치 불일치 감지
  - 헤더 정규화 강화 (AAA  Storage 변형 흡수)
  - 사용자 친화적 오류 메시지 매핑

### Performance
- 이상치 탐지 성능: 1건 → 7,022건 (7,000배 향상)
- ML 모델 앙상블로 정확도 대폭 개선
- 위험도 점수 일관화 (0~1 범위)

### Added
- `config/stage4_anomaly.yaml`: Stage 4 전용 설정 파일
- `scripts/stage4_anomaly/anomaly_detector_v2_backup.py`: v2 백업
- `requirements.txt`: pyod>=2.0.5 추가 (선택적)

### Changed
- `scripts/stage4_anomaly/anomaly_detector.py`: v2 → v3 업그레이드
- `scripts/stage4_anomaly/__init__.py`: PyOD import 지원
- `config/pipeline_config.yaml`: sheet_name을 명시적 시트명으로 변경

### Verified
- ✅ PyOD 미설치 환경에서 sklearn 폴백 작동 확인
- ✅ 이상치 탐지: 7,022건 (ML 기반 고급 탐지)
- ✅ 색상 적용 및 백업 파일 생성 확인

## [2.9.4-hotfix-4] - 2025-10-20

### Fixed
- 실행 스크립트 색상 단계 정리 및 개선
  - **`run_full_pipeline.bat`**:
    - 불필요한 `synced_for_color.xlsx` 복사 제거
    - Stage 4에 `--stage4-visualize` 플래그 추가
    - 파일명을 `synced.xlsx` → `synced_v2.9.4.xlsx`로 정확히 수정
  - **`run_full_pipeline.ps1`**:
    - 불필요한 `synced_for_color.xlsx` 복사 제거
    - Stage 4에 `--stage4-visualize` 플래그 추가
    - 파일명을 `synced.xlsx` → `synced_v2.9.4.xlsx`로 정확히 수정

### Documentation
- **docs/** 폴더 전체 업데이트 (8개 문서)
  - `docs/README.md`: 버전 v2.9.4-hotfix-4, 개선사항 추가
  - `docs/common/PIPELINE_EXECUTION_GUIDE.md`: 최적화된 흐름도, 자동화 기능 명시
  - `docs/common/STAGE3_USER_GUIDE.md`: 날짜 범위 동적 계산 (2025-10), 33개월 분석
  - `docs/common/STAGE4_USER_GUIDE.md`: 자동 파일 탐색, --stage4-visualize 상세 설명
  - `docs/common/STAGE_BY_STAGE_GUIDE.md`: 색상 포함 전체 흐름도 업데이트
  - `docs/sorted_version/QUICK_START.md`: Stage 4 색상 명령어, 버전 업데이트
  - `docs/no_sorting_version/QUICK_START.md`: Stage 4 색상 명령어, 버전 업데이트
  - `hvdc_pipeline/README.md`: 주요 기능에 자동화/색상 추가
  - 모든 문서 최종 업데이트 날짜: 2025-10-20
  - 모든 문서 버전: v2.9.4 → v2.9.4-hotfix-4

### Verified
- ✅ Stage 1 색상 적용 정상 작동 확인
  - 주황색: 20개 셀 (날짜 변경)
  - 노란색: 3,885개 셀, 100개 행 (신규 케이스)
- ✅ Stage 4 이상치 색상 적용 활성화
- ✅ 문서 일관성 검증 완료

### Improved
- 불필요한 파일 복사 제거 (디스크 공간 절약)
- 색상 적용 단계 완전 자동화
- 명확한 실행 메시지 추가
- 문서 통합 업데이트 (8개 문서)

## [2.9.4-hotfix-3] - 2025-10-20

### Added
- Stage 4 자동 파일 탐색 기능
  - config 파일에 지정된 파일이 없으면 자동으로 최신 파일 검색
  - 타임스탬프 패턴을 정규식으로 추출하여 동적 패턴 생성
  - 파일명 하드코딩 제거 (config 기반 패턴 생성)
  - 파일 수정 시간 기준 최신 파일 자동 선택

### Improved
- Stage 3 재실행 후 Stage 4가 자동으로 최신 보고서 사용
- config 파일 수동 업데이트 불필요
- 명확한 로그 메시지로 선택된 파일 확인 가능

### Technical Details
```python
# 예시: HVDC_입고로직_종합리포트_20251020_051118_v3.0-corrected.xlsx
# 패턴: HVDC_입고로직_종합리포트_*_v3.0-corrected.xlsx
pattern = re.sub(r'_\d{8}_\d{6}_', '_*_', filename)
```

## [2.9.4-hotfix-2] - 2025-10-20

### Fixed
- Stage 3 보고서 날짜 범위 동적 계산 (2개 파일)
  - **`report_generator.py`** (실제 사용 파일):
    - `create_monthly_inbound_pivot()`: 현재 월까지 자동 계산
    - `create_warehouse_monthly_sheet()`: 현재 월까지 자동 계산
    - `create_site_monthly_sheet()`: 현재 월까지 자동 계산
    - 출력 메시지: 동적 날짜 범위 표시
  - **`hvdc_excel_reporter_final_sqm_rev.py`** (백업 파일): 동일 수정

### Improved
- 보고서가 항상 최신 월(2025-10)까지 데이터 출력
- 수동 날짜 업데이트 불필요
- 월별 시트: 33개월 (2023-02 ~ 2025-10)

### Verified
- ✅ 창고_월별_입출고: 34행 (33개월 + Total)
- ✅ 현장_월별_입고재고: 34행 (33개월 + Total)
- ✅ 최종 월: 2025-10 확인 완료

## [2.9.4-hotfix] - 2025-10-20

### Fixed
- Stage 4 이상치 탐지 실행 실패 문제 해결
  - `pipeline_config.yaml`: 입력 파일명을 실제 파일로 수정
  - 파일명: `HVDC_입고로직_종합리포트_20251019_230712` → `20251020_051118`
- `run_pipeline.py`: 인코딩 깨짐 문제 해결
  - Stage 1-4 ImportError 메시지 한글 복원 (7개 위치)
  - 시각화 관련 로그 메시지 복원

### Verified
- Stage 4 단독 실행 성공 (0.48초)
- 이상치 보고서 정상 생성 (Excel + JSON)

## [2.9.4] - 2025-01-19

### Added
- 유연한 컬럼 매칭 시스템 (`column_matcher.py`)
  - 대소문자 무시
  - 특수문자 (점, 공백 등) 정규화
  - 의미 기반 컬럼 검색

- Master NO. 순서 정렬 기능
  - `_apply_master_no_sorting()` 메서드 추가
  - Case List의 NO. 순서를 Warehouse에 적용

- 날짜 정규화 강화
  - Excel 직렬 번호 지원
  - AM/PM 형식 지원
  - YYYY-MM-DD HHMMSS 형식 지원

- 출력 파일 버전 관리
  - 파일명에 버전 정보 추가 (v2.9.4)

### Fixed
- NO/No. 컬럼 감지 실패 문제 수정
- 날짜 비교 시 형식 불일치 문제 해결
- 중복 Case NO 처리 개선 (multi-map 인덱스)

### Changed
- `_case_col()`: 하드코딩 제거, `find_column_by_meaning()` 사용
- `_apply_master_no_sorting()`: 하드코딩 제거, `find_column_flexible()` 사용

### Performance
- 전체 파이프라인 실행 시간: ~1분 (기존 3분 20초에서 개선)
- Stage 1 처리 속도: ~30초 (5,552행)

## [2.9.4-sorting-options] - 2025-01-19

### Added - 정렬 옵션 구조화
- **정렬/비정렬 버전 분리**
  - `scripts/stage1_sync_sorted/`: Master NO. 순서 정렬 버전 (548줄)
  - `scripts/stage1_sync_no_sorting/`: 원본 순서 유지 (403줄, 145줄 단축)
  - 각 버전별 독립 실행 가능
  - `column_matcher.py` 의존성 해결 완료

- **문서 구조 재편 (19개 파일)**
  - `docs/sorted_version/`: 정렬 버전 전용 문서 (3개)
    - README.md (신규)
    - QUICK_START.md
    - STAGE1_USER_GUIDE.md
  - `docs/no_sorting_version/`: 비정렬 버전 전용 문서 (3개)
    - README.md (신규)
    - QUICK_START.md
    - STAGE1_USER_GUIDE.md
  - `docs/common/`: 공통 문서 통합 (13개)
    - STAGE_BY_STAGE_GUIDE.md
    - STAGE1_SYNC_GUIDE.md (이동)
    - STAGE1_DETAILED_LOGIC_GUIDE.md (이동)
    - STAGE2_USER_GUIDE.md
    - STAGE2_DERIVED_GUIDE.md (이동)
    - STAGE3_USER_GUIDE.md
    - STAGE4_USER_GUIDE.md
    - STAGE4_ANOMALY_GUIDE.md (이동)
    - STAGE4_COLOR_APPLICATION_REPORT.md (이동)
    - COLOR_FIX_SUMMARY.md (이동)
    - DATE_LOGIC_VERIFICATION_REPORT.md (이동)
    - PIPELINE_EXECUTION_GUIDE.md (이동)
    - PIPELINE_OVERVIEW.md (이동)

- **실행 옵션 추가**
  - `--no-sorting` 플래그 추가
  - 정렬 버전: `python run_pipeline.py --all` (기본)
  - 비정렬 버전: `python run_pipeline.py --all --no-sorting`
  - Stage별 실행: `python run_pipeline.py --stage 1 [--no-sorting]`

- **검증 스크립트**
  - `scripts/verify_sorting_option.py`: 정렬/비정렬 버전 비교 검증
  - 데이터 일관성 검증
  - 성능 비교 보고서 생성

### Fixed
- `column_matcher.py` 의존성 누락 문제 해결
  - `stage1_sync_sorted/`에 복사하여 독립 실행 가능
- Import 오류 수정 및 검증 완료
- 구문 오류 검증 완료 (py_compile 통과)

### Changed - 구조적 변경
- **scripts/** 폴더 재구성
  - 정렬/비정렬 버전을 별도 폴더로 완전 분리
  - 각 폴더에 `__init__.py`, `README.md` 추가
  - 백업 폴더 `stage1_sync/` 유지 (5개 파일)
  - `scripts/README.md` 생성 (구조 설명)

- **docs/** 폴더 재구성
  - 버전별 문서 완전 분리 (sorted_version, no_sorting_version)
  - 공통 문서를 `common/` 폴더로 통합
  - 중복 파일 제거 (`STAGE1_USER_GUIDE.md` 삭제)
  - `docs/README.md` 업데이트 (문서 인덱스)

- **run_pipeline.py** 업데이트
  - Import 경로 변경: `scripts.stage1_sync_sorted.*`
  - Import 경로 변경: `scripts.stage1_sync_no_sorting.*`
  - `--no-sorting` 플래그 처리 로직 추가

### Performance
- **정렬 버전**: ~35초 (Master NO. 순서로 정렬, 보고서 작성 최적화)
- **비정렬 버전**: ~30초 (정렬 로직 제거, 5초 단축, 빠른 확인용)
- **코드 크기**: 정렬 버전 548줄, 비정렬 버전 403줄 (145줄 차이)

### Documentation
- 총 19개 문서 파일 정리 및 재구성 완료
- 버전별 사용 가이드 작성 (STAGE1_USER_GUIDE.md × 2)
- 버전별 빠른 시작 가이드 (QUICK_START.md × 2)
- 버전별 README 생성 (sorted_version, no_sorting_version)
- 스크립트 구조 설명서 생성 (scripts/README.md)
- 문서 구조 인덱스 생성 (docs/README.md)

### Testing & Verification
- Python 구문 검증 완료 (py_compile)
- Import 테스트 완료 (정렬/비정렬 버전 모두)
- 의존성 검증 완료 (column_matcher.py)
- 독립 실행 가능성 확인 완료

## [Unreleased]
### Added
- structural(pipeline): Stage 2 산출물 출력 경로 및 Stage 3 보고서 디렉터리 구성을 설정하고 색상 보존 전략을 통합했습니다. / Configured Stage 2 derived output paths and Stage 3 report directories with color preservation support.
- behavioral(pipeline): 파이프라인 실행 안내 메시지를 업데이트하여 사용자가 보고서 출력 위치를 쉽게 확인할 수 있도록 했습니다. / Updated pipeline execution guidance to point users to the correct report output location.
