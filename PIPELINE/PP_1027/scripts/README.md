# HVDC Pipeline 스크립트 구조 v4.0.51

**Samsung C&T Logistics | ADNOC·DSV Partnership**

HVDC Pipeline의 모든 스크립트에 대한 구조 설명입니다.

## 🚀 최신 업데이트 (v4.0.51 - 2025-10-29)

### 주요 개선사항
- **v4.0.51**: 프로젝트 전체 중복예전파일 정리 완료
- **v4.0.50**: Stage 2 사이트 컬럼 인식 수정
- **v4.0.30**: 헤더 순서 정렬 완료, Hybrid 접근 구현
- **v4.0.22**: SQM/Stack_Status 계산 시스템 구축
- **v4.0.21**: Core 모듈 데이터 파싱 유틸리티 추가

## 📁 프로젝트 실행 방법 (v4.0.51+)

### 권장 실행 방법
```bash
# 방법 1: run/ 폴더 사용 (권장)
python run/run_pipeline.py --all

# 방법 2: run/ 폴더 내에서 실행
cd run
python run_pipeline.py --all
```

### 중요 사항
- config 파일은 프로젝트 루트의 config/ 폴더를 참조합니다
- run/ 폴더는 실행 스크립트만 포함합니다
- 모든 Stage는 통합 실행을 권장합니다

## 📁 스크립트 구조

### 🔄 Stage 1 - 데이터 동기화 (v3.0)

#### 정렬 버전 (Sorted Version)
```
scripts/stage1_sync_sorted/
├── __init__.py                    # 패키지 초기화
├── data_synchronizer_v30.py       # 정렬 버전 동기화 스크립트
└── README.md                      # 정렬 버전 설명
```

**특징**:
- Master NO. 순서로 정렬
- 보고서 작성 최적화
- 색상 자동 적용 (주황/노랑)
- 처리 시간: 약 35초

#### 비정렬 버전 (No Sorting Version)
```
scripts/stage1_sync_no_sorting/
├── __init__.py                              # 패키지 초기화
├── data_synchronizer_v30_no_sorting.py      # 비정렬 버전 동기화 스크립트
└── README.md                                # 비정렬 버전 설명
```

**특징**:
- 원본 Warehouse 순서 유지
- 빠른 처리 속도
- 색상 자동 적용 (주황/노랑)
- 처리 시간: 약 30초

### 📊 Stage 2 - 파생 컬럼 처리 (v4.0.50)

```
scripts/stage2_derived/
├── derived_columns_processor.py    # 13개 파생 컬럼 처리
├── stack_and_sqm.py                # SQM/Stack_Status 계산
├── site_location_processor.py       # 사이트 위치 처리 (v4.0.50)
└── README.md                       # Stage 2 가이드
```

**주요 기능**:
- **Status_Location**: 창고/현장/사이트 위치 식별
- **Status_SITE**: 사이트별 상태 관리
- **Status_WAREHOUSE**: 창고별 상태 관리
- **SQM**: 치수 기반 면적 계산
- **Stack_Status**: 적재 가능성 파싱

### 📈 Stage 3 - 종합 보고서 생성 (v3.0-corrected)

```
scripts/stage3_report/
├── report_generator.py             # KPI 보고서 생성 (Hybrid 접근)
├── hvdc_excel_reporter_final_sqm_rev.py  # Excel 리포터
├── utils.py                        # 컬럼 정규화 유틸리티
├── column_definitions.py           # 컬럼 정의 상수
└── README.md                       # Stage 3 가이드
```

**주요 기능**:
- **12개 시트**: 창고/현장 월별 입출고, Flow 분석, KPI 검증 등
- **벡터화 최적화**: 성능 82% 개선 (155초 → 28초)
- **Excel 컬럼 보존**: 단일 ExcelWriter 컨텍스트 사용
- **SQM 분석**: 누적재고, Invoice과금, 피벗테이블

### 🔍 Stage 4 - 이상치 탐지 (Balanced Boost Edition v4.0)

```
scripts/stage4_anomaly/
├── anomaly_detector_balanced.py    # v4 Balanced Boost 이상치 탐지
├── anomaly_visualizer.py            # 색상 시각화
├── analysis_reporter.py             # 분석 리포트 생성
├── config.yaml                      # 설정 파일
└── README.md                        # Stage 4 가이드
```

**주요 기능**:
- **3-Layer Hybrid**: Rule-Based + Statistical + ML Ensemble
- **Balanced Boost**: 위험도 포화 문제 완전 해결
- **ECDF 캘리브레이션**: 0.0~1.0 정규화
- **색상 자동 적용**: 빨강/주황/노랑/보라

### 🏗️ Core 모듈 (v4.0.21+)

```
scripts/core/
├── header_registry.py              # 헤더 정의 및 관리
├── semantic_matcher.py             # 의미 기반 매칭
├── data_parser.py                  # Stack_Status 파싱 (v4.0.21)
├── standard_header_order.py        # 헤더 순서 관리 (v4.0.30)
├── name_resolver.py                # 이름 해석기
└── __init__.py                     # 패키지 초기화
```

**주요 기능**:
- **중앙 집중식 관리**: 모든 Stage에서 공통 사용
- **개선된 파싱 로직**: 하중 표기 제거, 슬래시 패턴 지원
- **유연한 헤더 매칭**: 동의어 및 변형 자동 인식
- **표준 헤더 순서**: Stage 간 일관성 보장

## 🚀 스크립트 사용법

### 파이프라인 통합 실행 (권장)
```bash
# 전체 파이프라인 실행
python run/run_pipeline.py --all

# 특정 Stage만 실행
python run/run_pipeline.py --stage1
python run/run_pipeline.py --stage2
python run/run_pipeline.py --stage3
python run/run_pipeline.py --stage4

# 정렬 옵션
python run/run_pipeline.py --all --no-sorting
```

### 개별 스크립트 실행

#### Stage 1 직접 실행
```bash
# 정렬 버전
python scripts/stage1_sync_sorted/data_synchronizer_v30.py \
  --master "data/raw/HITACHI/Case List_Hitachi.xlsx" \
  --warehouse "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "output_sorted.xlsx"

# 비정렬 버전
python scripts/stage1_sync_no_sorting/data_synchronizer_v30_no_sorting.py \
  --master "data/raw/HITACHI/Case List_Hitachi.xlsx" \
  --warehouse "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "output_no_sorting.xlsx"
```

#### Stage 2 직접 실행
```bash
python scripts/stage2_derived/derived_columns_processor.py \
  --input "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx" \
  --output "data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).derived_v3.4.xlsx"
```

#### Stage 3 직접 실행
```bash
python scripts/stage3_report/report_generator.py \
  --input "data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).derived_v3.4.xlsx" \
  --output "data/processed/reports/HVDC_입고로직_종합리포트_20251029_v3.0-corrected.xlsx"
```

#### Stage 4 직접 실행
```bash
python scripts/stage4_anomaly/anomaly_detector_balanced.py \
  --input "data/processed/reports/HVDC_입고로직_종합리포트_20251029_v3.0-corrected.xlsx" \
  --output "data/processed/anomaly/anomaly_report_20251029.xlsx"
```

## 📊 버전별 스크립트 비교

| 항목 | 정렬 버전 | 비정렬 버전 |
|------|----------|------------|
| 스크립트 위치 | `stage1_sync_sorted/` | `stage1_sync_no_sorting/` |
| 메인 클래스 | `DataSynchronizerV30` | `DataSynchronizerV30NoSorting` |
| 정렬 처리 | Master NO 기준 정렬 | 정렬 없음 |
| 처리 시간 | ~35초 | ~30초 |
| 메모리 사용량 | 높음 | 낮음 |
| 색상 적용 | 자동 (주황/노랑) | 자동 (주황/노랑) |

## 🔧 개발 및 확장

### 새로운 버전 추가
1. 새 폴더 생성 (예: `stage1_sync_custom/`)
2. `__init__.py` 파일 생성
3. 동기화 스크립트 작성
4. `README.md` 작성
5. `run/run_pipeline.py`에 import 경로 추가

### 스크립트 수정 시 주의사항
- 정렬 버전과 비정렬 버전은 독립적으로 수정 가능
- 공통 기능은 두 버전 모두에 적용 필요
- 각 버전의 README.md 업데이트 필요
- Core 모듈 수정 시 모든 Stage에 영향

## 📚 관련 문서

### 패치 문서 (docs/reports/)
- [Stage 3 Excel Writer Fix](../docs/reports/STAGE3_EXCEL_WRITER_FIX_v4.0.22.md)
- [Stage 3 Inbound Calculation Fix](../docs/reports/STAGE3_INBOUND_CALCULATION_FIX_v4.0.29.md)

### 개발 가이드 (docs/development/)
- [Header Order Standardization](../docs/development/header-order-standardization.md)
- [Development Plan](../docs/development/plan.md)

### 공통 문서 (docs/common/)
- [Pipeline Overview](../docs/common/PIPELINE_OVERVIEW.md)
- [Stage 1 Guide](../docs/common/STAGE1_SYNC_GUIDE.md)
- [Stage 2 Guide](../docs/common/STAGE2_DERIVED_GUIDE.md)
- [Stage 3 Guide](../docs/common/STAGE3_USER_GUIDE.md)
- [Stage 4 Guide](../docs/common/STAGE4_ANOMALY_GUIDE.md)

### 버전별 문서
- [정렬 버전 문서](../docs/sorted_version/)
- [비정렬 버전 문서](../docs/no_sorting_version/)

## 🔍 디버깅 및 로그

### 로그 확인
```bash
# 파이프라인 실행 로그
tail -f logs/pipeline.log

# 특정 스크립트 로그
grep "data_synchronizer" logs/pipeline.log
grep "Stage 1" logs/pipeline.log
```

### 스크립트별 디버깅
```bash
# 정렬 버전 디버깅
python -m pdb scripts/stage1_sync_sorted/data_synchronizer_v30.py \
  --master "data/raw/HITACHI/Case List_Hitachi.xlsx" \
  --warehouse "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 비정렬 버전 디버깅
python -m pdb scripts/stage1_sync_no_sorting/data_synchronizer_v30_no_sorting.py \
  --master "data/raw/HITACHI/Case List_Hitachi.xlsx" \
  --warehouse "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx"
```

## 🆕 v4.0.51 주요 변경사항 (2025-10-29)

### 프로젝트 구조 정리
- **루트 디렉토리**: 약 50개 중복/임시 파일 제거
- **run/ 폴더**: 실행 스크립트만 보존, config 중복 제거
- **archive/notebooks/**: 분석 완료된 노트북 정리
- **실행 경로**: run/run_pipeline.py가 상위 config/ 폴더 참조

### 문서 정리
- **패치 문서**: scripts/ → docs/reports/ 이동
- **중복 코드**: stack status.md, STACK.MD 삭제 (이미 구현됨)
- **README 업데이트**: v4.0.51 기준 전체 재구성

## 🔧 v4.0.50 핵심 개선사항 (2025-10-28)

### Stage 2 사이트 컬럼 인식 수정
- **문제**: Status_Location에서 사이트 위치 0개 인식
- **원인**: header_registry.py에서 사이트명 별칭 제거
- **해결**: 사이트명 별칭 재추가 + 스마트 컬럼 선택 로직
- **결과**: Status_Location 사이트 위치 5,701개 정상 인식

## 🔧 v4.0.30 핵심 개선사항 상세

### 헤더 순서 정렬 (v4.0.30)
- **문제**: Stage 2와 Stage 3의 헤더 순서 불일치
- **해결**: `standard_header_order.py`에서 HVDC CODE 제거, 실제 데이터 구조에 맞게 수정
- **결과**: Stage 2/3 헤더 일치율 100% 달성

### Hybrid 접근 구현 (v4.0.29)
- **문제**: 벡터화 로직의 과도한 필터링으로 입고 데이터 부정확
- **해결**: 루프 기반 입고 + 수정된 출고 로직 조합
- **결과**: 입고 6개 → 5,517개 (완전 복원), 출고 22개 → 2,574개 (117배 증가)

### SQM/Stack_Status 계산 (v4.0.22)
- **추가**: `scripts/stage2_derived/stack_and_sqm.py` 모듈
- **기능**: 치수 기반 SQM 계산 (L×W/10,000), Stack 텍스트 파싱
- **통합**: `core/data_parser.py`에서 중앙 관리

### Excel 컬럼 보존 (v4.0.22)
- **문제**: DataFrame에 컬럼 존재하지만 Excel에서 누락
- **해결**: 모든 시트를 단일 `pd.ExcelWriter()` 컨텍스트에서 저장
- **결과**: Total sqm, Stack_Status 컬럼 정상 저장

### 벡터화 최적화 (v4.0.17)
- **성능**: Stage 3 실행 시간 82% 개선 (155초 → 28초)
- **방법**: `iterrows()` → `melt()`, `groupby()`, `apply()` 벡터화
- **안정성**: 자동 폴백 시스템으로 안정성 보장

---

**📅 최종 업데이트**: 2025-10-29
**🔖 버전**: v4.0.51
**👥 작성자**: HVDC 파이프라인 개발팀