# HVDC Pipeline v4.0.54

**Samsung C&T Logistics | ADNOC·DSV Strategic Partnership**

HVDC 프로젝트를 위한 통합 데이터 처리 파이프라인으로, 원본 Excel 데이터부터 종합 보고서 및 이상치 탐지까지 전체 프로세스를 자동화합니다.

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [주요 기능](#주요-기능)
3. [시스템 요구사항](#시스템-요구사항)
4. [설치 및 설정](#설치-및-설정)
5. [빠른 시작](#빠른-시작)
6. [파이프라인 아키텍처](#파이프라인-아키텍처)
7. [Stage별 상세 가이드](#stage별-상세-가이드)
8. [프로젝트 구조](#프로젝트-구조)
9. [설정 파일](#설정-파일)
10. [사용 예시](#사용-예시)
11. [문제 해결](#문제-해결)
12. [개발 가이드](#개발-가이드)
13. [성능 지표](#성능-지표)
14. [기여 가이드](#기여-가이드)
15. [라이선스](#라이선스)

---

## 🎯 프로젝트 개요

### 목적

HVDC 프로젝트는 삼성물산과 ADNOC·DSV 간의 전략적 파트너십을 위한 물류 데이터 처리 시스템입니다. 이 파이프라인은 다음을 자동화합니다:

- **데이터 동기화**: Master 파일과 Warehouse 파일 간 데이터 통합 및 동기화
- **데이터 품질 관리**: 벤더별 메타데이터 자동 설정 및 검증
- **파생 컬럼 계산**: 13개 파생 컬럼 자동 계산 (SQM, Stack_Status 등)
- **종합 보고서 생성**: 12개 시트로 구성된 다차원 분석 보고서
- **이상치 탐지**: ML 기반 이상치 탐지 및 시각화

### 핵심 특징

- ✅ **4단계 파이프라인**: 데이터 동기화 → 파생 컬럼 → 보고서 생성 → 이상치 탐지
- ✅ **벤더 자동 분리**: HITACHI와 SIEMENS 데이터 자동 분리 및 처리
- ✅ **메타데이터 관리**: Source_Vendor, Source_File, Source_Sheet 자동 설정 (99.3% coverage)
- ✅ **표준 헤더 시스템**: 63개 표준 헤더로 전체 파이프라인 통일
- ✅ **색상 시각화**: 변경사항 및 이상치 자동 색상 표시
- ✅ **Standalone 실행 파일**: Python 설치 없이 GUI/CLI 실행 가능

---

## ✨ 주요 기능

### Stage 1: 데이터 동기화 (Data Synchronization)

- **자동 헤더 탐지**: 벤더별 헤더 위치 자동 인식 (SIEMENS=행0, HITACHI=행4)
- **시맨틱 매칭**: 헤더명 변형에도 유연하게 대응하는 의미 기반 매칭
- **Master-Warehouse 동기화**: Case No. 기준 데이터 통합 및 업데이트 추적
- **벤더 메타데이터 설정**: Source_Vendor, Source_Sheet 자동 설정
- **SIEMENS 자동 병합**: SIEMENS Master 파일 자동 감지 및 병합
- **색상 표시**: 변경된 날짜(주황), 신규 레코드(노랑) 자동 표시
- **멀티시트 지원**: 여러 시트 자동 로드 및 병합

### Stage 2: 파생 컬럼 생성 (Derived Columns)

- **13개 파생 컬럼 자동 계산**:
  - 상태 관련 (6개): Status_SITE, Status_WAREHOUSE, Status_Current, Status_Location, Status_Location_Date, Status_Storage
  - 처리량 관련 (5개): Site_AGI_handling, WH_AGI_handling, Total_AGI_handling, Minus, Final_AGI_handling
  - 분석 관련 (2개): Stack_Status, SQM
- **SQM 계산**: L(cm) × W(cm) / 10,000 또는 PKG 기반 추정
- **Stack_Status 파싱**: 텍스트에서 적재 가능 층수 추출
- **벤더별 파일 분리**: Source_Vendor 기반 HITACHI/SIEMENS 파일 자동 분리

### Stage 3: 보고서 생성 (Report Generation)

- **12개 시트 종합 보고서**:
  - 통합_원본데이터_Fixed (벤더별 분리)
  - 창고_월별_입출고
  - 현장_월별_입출고
  - SQM 기반 재고 분석
  - 창고별 통계
  - 현장별 통계
  - 기타 분석 시트
- **벤더별 전용 시트**: HITACHI_원본데이터_Fixed, SIEMENS_원본데이터_Fixed
- **Source_File 동적 생성**: Source_Vendor 기반 파일명 자동 설정
- **월별 입출고 분석**: 창고 및 현장별 월별 입출고 추적
- **SQM 기반 재고 관리**: 면적 기반 창고 용량 분석

### Stage 4: 이상치 탐지 (Anomaly Detection)

- **Balanced Boost v4.0**: 룰/통계/ML 혼합 위험도 시스템
- **5가지 이상치 유형**:
  - 시간 역전 (치명적)
  - ML 이상치 (높음/보통/낮음)
  - 과도 체류
  - 데이터 품질
- **ECDF 캘리브레이션**: 위험도 0.001~0.999 범위로 정규화
- **위치별 임계치**: MOSB/DSV 등 지점별 IQR+MAD 과도 체류 판정
- **색상 시각화**: 심각도별 색상 자동 표시

---

## 💻 시스템 요구사항

### 필수 요구사항

- **Python**: 3.13 이상 (권장: 3.13)
- **운영체제**: Windows 10/11 (Windows COM 자동화 지원)
- **메모리**: 최소 4GB RAM (권장: 8GB 이상)
- **디스크 공간**: 최소 500MB 여유 공간

### Python 패키지

핵심 의존성:

- `pandas>=2.0.0` - 데이터 처리
- `openpyxl>=3.1.0` - Excel 파일 읽기/쓰기
- `XlsxWriter>=3.1.0` - Excel 파일 생성
- `polars[excel]>=0.20.0` - 고성능 데이터 처리
- `great-expectations>=0.18.0` - 데이터 검증

Excel 자동화:

- `xlwings>=0.31.0` - VBA-Python 통합
- `pywin32>=306` - Windows COM 자동화

선택적 의존성:

- `pandera>=0.18.0` - DataFrame 스키마 검증
- `prefect>=2.14.0` - 파이프라인 오케스트레이션
- `structlog>=24.1.0` - 구조화 로깅
- `rich>=13.7.0` - 터미널 출력 개선
- `hypothesis>=6.92.0` - 속성 기반 테스트
- `duckdb>=0.10.0` - 고성능 인메모리 분석
- `diskcache>=5.6.0` - 디스크 기반 캐싱
- `joblib>=1.3.0` - 병렬 처리

---

## 🚀 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd PP1030
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# 또는
source venv/bin/activate  # Linux/Mac
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 설정 파일 확인

주요 설정 파일:

- `config/pipeline_config.yaml` - 전체 파이프라인 설정
- `config/stage2_derived_config.yaml` - Stage 2 전용 설정
- `config/stage4_anomaly.yaml` - Stage 4 이상치 탐지 설정

### 5. 입력 파일 준비

`data/raw/` 폴더에 다음 파일 배치:

- `Case List_Hitachi.xlsx` - HITACHI Master 파일
- `Case List_Simense.xlsx` - SIEMENS Master 파일 (선택)
- `HVDC WAREHOUSE_HITACHI(HE).xlsx` - HITACHI Warehouse 파일
- `HVDC WAREHOUSE_SIMENSE(SIM).xlsm` - SIEMENS Warehouse 파일 (선택)

---

## 🏃 빠른 시작

### 전체 파이프라인 실행

```bash
# 프로젝트 루트에서 실행
python run/run_pipeline.py --all
```

**실행 결과**:

- Stage 1: 데이터 동기화 완료 → `data/processed/synced/*.synced_v3.4.xlsx`
- Stage 2: 파생 컬럼 생성 완료 → `data/processed/derived/*.xlsx`
- Stage 3: 종합 보고서 생성 완료 → `data/processed/reports/*.xlsx`
- Stage 4: 이상치 탐지 완료 → `data/anomaly/*.xlsx`

### 개별 Stage 실행

```bash
# Stage 1만 실행
python run/run_pipeline.py --stage 1

# Stage 2만 실행
python run/run_pipeline.py --stage 2

# 여러 Stage 동시 실행
python run/run_pipeline.py --stage 1 2 3
```

### 실행 옵션

```bash
# 정렬 없이 빠른 실행
python run/run_pipeline.py --all --no-sorting

# Stage 4 색상 시각화 포함
python run/run_pipeline.py --all --stage4-visualize

# Stage 4 contamination 조정
python run/run_pipeline.py --stage 4 --contamination 0.05
```

---

## 🏗️ 파이프라인 아키텍처

### 전체 데이터 흐름

```
Raw Data (Excel)
    ↓
Stage 1: 데이터 동기화 + 벤더 메타데이터 설정
    ├─ Master 파일 로드 (HITACHI + SIEMENS)
    ├─ Warehouse 파일 로드
    ├─ 시맨틱 매칭 및 동기화
    ├─ Source_Vendor/Sheet 자동 설정
    └─ 색상 표시 (변경/신규)
    ↓
Synced Data (*.synced_v3.4.xlsx)
    ↓
Stage 2: 파생 컬럼 생성
    ├─ 13개 파생 컬럼 계산
    ├─ SQM 및 Stack_Status 계산
    ├─ 벤더별 파일 분리 (HITACHI/SIEMENS)
    └─ 표준 헤더 순서 재정렬 (63개)
    ↓
Derived Data (*.xlsx)
    ↓
Stage 3: 종합 보고서 생성
    ├─ 12개 시트 생성
    ├─ 벤더별 전용 시트 (HITACHI/SIEMENS)
    ├─ Source_File 동적 생성
    ├─ 월별 입출고 분석
    └─ SQM 기반 재고 분석
    ↓
Reports (*.xlsx)
    ↓
Stage 4: 이상치 탐지
    ├─ Balanced Boost 분석
    ├─ 5가지 이상치 유형 탐지
    ├─ 위험도 계산 및 정규화
    └─ 색상 시각화
    ↓
Final Output (*.xlsx, *.json)
```

### Core 모듈 (v1.2.0)

모든 Stage에서 공통으로 사용하는 중앙 집중식 모듈:

- **Header Registry**: 63개 표준 헤더 정의 및 관리
- **Semantic Matcher**: 의미 기반 헤더 매칭
- **File Registry**: 파일 경로 중앙 관리
- **Vendor Metadata**: 벤더명 정규화 및 Source_File 생성

---

## 📖 Stage별 상세 가이드

### Stage 1: 데이터 동기화

**목적**: Master 파일과 Warehouse 파일 간 데이터 통합 및 동기화

**주요 기능**:

- 자동 헤더 탐지 (벤더별 최적 위치 자동 인식)
- 시맨틱 매칭 (헤더명 변형 자동 처리)
- Case No. 기준 데이터 매칭 및 업데이트
- SIEMENS 데이터 자동 병합
- Source_Vendor/Sheet 메타데이터 자동 설정
- 변경사항 색상 표시 (주황: 변경, 노랑: 신규)

**입력 파일**:

- Master: `Case List_Hitachi.xlsx`, `Case List_Simense.xlsx`
- Warehouse: `HVDC WAREHOUSE_HITACHI(HE).xlsx`, `HVDC WAREHOUSE_SIMENSE(SIM).xlsm`

**출력 파일**:

- `data/processed/synced/*.synced_v3.4.xlsx` (멀티시트)
- `data/processed/synced/*.synced_v3.4_merged.xlsx` (단일 시트)

**실행 시간**: 약 5분 (8,930행 기준)

**상세 문서**: [Stage 1 사용자 가이드](docs/common/STAGE1_USER_GUIDE.md)

### Stage 2: 파생 컬럼 생성

**목적**: 13개 파생 컬럼 자동 계산 및 벤더별 파일 분리

**파생 컬럼 상세**:

1. **Status_SITE**: 사이트 위치 여부 판별
2. **Status_WAREHOUSE**: 창고 위치 여부 판별
3. **Status_Current**: 현재 상태 (최신 위치 기반)
4. **Status_Location**: 최종 위치 (창고 또는 사이트)
5. **Status_Location_Date**: 위치 변경 날짜
6. **Status_Storage**: 저장 상태 (Indoor/Outdoor)
7. **Site_AGI_handling**: 사이트별 처리량
8. **WH_AGI_handling**: 창고별 처리량
9. **Total_AGI_handling**: 총 처리량
10. **Minus**: 차감량 계산
11. **Final_AGI_handling**: 최종 처리량
12. **Stack_Status**: 적재 가능 층수 (텍스트 파싱)
13. **SQM**: 면적 계산 (L×W/10000 또는 PKG 기반)

**입력 파일**: Stage 1 출력 (`*.synced_v3.4_merged.xlsx`)

**출력 파일**:

- `data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- `data/processed/derived/HVDC WAREHOUSE_SIMENSE(SIM).xlsx` (Source_Vendor 기반 분리)

**실행 시간**: 약 30초

**상세 문서**: [Stage 2 사용자 가이드](docs/common/STAGE2_USER_GUIDE.md)

### Stage 3: 보고서 생성

**목적**: 12개 시트로 구성된 종합 분석 보고서 생성

**생성되는 시트**:

1. **통합_원본데이터_Fixed**: 전체 데이터 통합 (벤더별 분리)
2. **HITACHI_원본데이터_Fixed**: HITACHI 전용 데이터
3. **SIEMENS_원본데이터_Fixed**: SIEMENS 전용 데이터
4. **창고_월별_입출고**: 창고별 월별 입출고 추적
5. **현장_월별_입출고**: 현장별 월별 입출고 추적
6. **SQM 기반 재고**: 면적 기반 창고 용량 분석
7. **창고별 통계**: 창고별 집계 통계
8. **현장별 통계**: 현장별 집계 통계
9. **기타 분석 시트**: 추가 분석 데이터

**입력 파일**: Stage 2 출력 (HITACHI/SIEMENS 분리 파일)

**출력 파일**: `data/processed/reports/HVDC_입고로직_종합리포트_*.xlsx`

**실행 시간**: 약 1분 46초 (벡터화 최적화)

**상세 문서**: [Stage 3 사용자 가이드](docs/common/STAGE3_USER_GUIDE.md)

### Stage 4: 이상치 탐지

**목적**: ML 기반 이상치 탐지 및 위험도 평가

**이상치 유형**:

1. **시간 역전** (치명적): 날짜 순서 역전 감지
2. **ML 이상치** (높음/보통/낮음): IsolationForest 기반 이상치
3. **과도 체류**: 위치별 IQR+MAD 기반 체류 시간 분석
4. **데이터 품질**: 누락값, 이상값 등 데이터 품질 문제

**Balanced Boost 시스템**:

- 룰 기반 가산: 시간 역전 +0.25
- 통계 기반 가산: 통계 이상(높음/치명) +0.15, 통계 이상(보통) +0.08
- ML 기반 탐지: IsolationForest 앙상블
- ECDF 캘리브레이션: 위험도 0.001~0.999 정규화

**입력 파일**: Stage 3 출력 (`통합_원본데이터_Fixed` 시트)

**출력 파일**:

- `data/anomaly/HVDC_anomaly_report.xlsx` (Excel)
- `data/anomaly/HVDC_anomaly_report.json` (JSON)

**실행 시간**: 약 1분

**상세 문서**: [Stage 4 사용자 가이드](docs/common/STAGE4_USER_GUIDE.md)

---

## 📁 프로젝트 구조

```
PP1030/
├── config/                          # 설정 파일
│   ├── pipeline_config.yaml        # 전체 파이프라인 설정
│   ├── stage2_derived_config.yaml  # Stage 2 설정
│   └── stage4_anomaly.yaml        # Stage 4 설정
│
├── core/                           # Core 모듈 (v1.2.0)
│   ├── header_registry.py         # 표준 헤더 정의 (63개)
│   ├── semantic_matcher.py        # 시맨틱 매칭 엔진
│   ├── file_registry.py           # 파일 경로 관리
│   └── data_parser.py             # 데이터 파싱 유틸리티
│
├── data/
│   ├── raw/                       # 원본 데이터 (읽기 전용)
│   │   ├── Case List_Hitachi.xlsx
│   │   ├── Case List_Simense.xlsx
│   │   ├── HVDC WAREHOUSE_HITACHI(HE).xlsx
│   │   └── HVDC WAREHOUSE_SIMENSE(SIM).xlsm
│   ├── processed/
│   │   ├── synced/               # Stage 1 출력
│   │   ├── derived/              # Stage 2 출력
│   │   └── reports/              # Stage 3 출력
│   └── anomaly/                  # Stage 4 출력
│
├── docs/                          # 문서
│   ├── common/                   # 공통 가이드
│   ├── technical/                # 기술 문서
│   ├── reports/                  # 보고서
│   └── INDEX.md                  # 문서 인덱스
│
├── run/                          # 실행 스크립트
│   └── run_pipeline.py          # 메인 실행 스크립트
│
├── scripts/
│   ├── core/                    # Core 모듈
│   ├── stage1_sync_sorted/      # Stage 1: 데이터 동기화
│   ├── stage1_Standalone/       # Stage 1 Standalone 패키지
│   ├── stage2_derived/          # Stage 2: 파생 컬럼
│   ├── stage3_report/           # Stage 3: 보고서 생성
│   └── stage4_anomaly/          # Stage 4: 이상치 탐지
│
├── tests/                        # 테스트
│   └── test_*.py
│
├── vba/                          # VBA 통합
│   └── python_bridge.py         # xlwings 브리지
│
├── requirements.txt              # Python 의존성
├── pyproject.toml                # 프로젝트 설정
└── README.md                     # 이 문서
```

---

## ⚙️ 설정 파일

### pipeline_config.yaml

전체 파이프라인 설정:

```yaml
stages:
  stage1:
    io:
      master_file: auto              # 자동 감지
      warehouse_file: data/raw/...
      output_file: data/processed/synced/...
    options:
      include_all_sheets: true
      header_fallback: true
    sorting:
      enabled: true
      sort_by_master_no: true
  
  stage2:
    enabled: true
  
  stage3:
    io:
      hitachi_file: data/processed/derived/...
      siemens_file: data/processed/derived/...
      report_directory: data/processed/reports
  
  stage4:
    io:
      input_file: data/processed/reports/...
      excel_output: data/anomaly/...
      visualization:
        enable_by_default: true
```

### stage2_derived_config.yaml

Stage 2 전용 설정:

```yaml
output:
  derived_file: data/processed/derived/...
  siemens_file: data/processed/derived/...
  split_by_vendor: true              # Source_Vendor 기반 분리
  preserve_colors: true
```

---

## 💡 사용 예시

### 예시 1: 전체 파이프라인 실행

```bash
# 기본 실행 (Master NO. 순서 정렬)
python run/run_pipeline.py --all

# 결과:
# - Stage 1: 8,930행 동기화 완료
# - Stage 2: 13개 파생 컬럼 생성 완료
# - Stage 3: 12개 시트 보고서 생성 완료
# - Stage 4: 182개 이상치 탐지 완료
```

### 예시 2: Stage 1만 실행 (데이터 동기화)

```bash
python run/run_pipeline.py --stage 1

# 결과:
# - data/processed/synced/*.synced_v3.4.xlsx 생성
# - Source_Vendor 99.3% coverage
# - 변경사항 색상 표시 (주황/노랑)
```

### 예시 3: Stage 4 이상치 탐지 (색상 시각화 포함)

```bash
python run/run_pipeline.py --stage 4 --stage4-visualize

# 결과:
# - data/anomaly/HVDC_anomaly_report.xlsx 생성
# - 이상치 색상 표시 (빨강/주황/노랑/보라)
```

### 예시 4: Standalone 실행 파일 사용

```bash
# GUI 실행 (더블클릭)
dist\Stage1Sync.exe

# CLI 실행
dist\stage1_cli.exe --master "Master.xlsx" --warehouse "Warehouse.xlsx" --out "output.xlsx"
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. 파일을 찾을 수 없음

**증상**: `FileNotFoundError: Stage 1 창고 파일을 찾을 수 없습니다`

**해결**:

- `config/pipeline_config.yaml`에서 파일 경로 확인
- `data/raw/` 폴더에 입력 파일이 있는지 확인
- 파일명이 정확한지 확인 (대소문자, 공백 포함)

#### 2. SIEMENS 데이터가 처리되지 않음

**증상**: Stage 2 출력에 SIEMENS 데이터가 없음

**해결**:

- `config/stage2_derived_config.yaml`에서 `split_by_vendor: true` 확인
- Stage 1 출력에서 Source_Vendor 컬럼 확인
- Stage 1 로그에서 SIEMENS 데이터 병합 여부 확인

#### 3. 색상이 표시되지 않음

**증상**: Stage 4 실행 후 색상이 적용되지 않음

**해결**:

- `--stage4-visualize` 플래그 포함 여부 확인
- `config/pipeline_config.yaml`에서 `visualization.enable_by_default: true` 확인

#### 4. Python 3.13 호환성 문제

**증상**: 일부 라이브러리 설치 실패

**해결**:

- `validate_requirements.py` 실행하여 호환성 확인
- 필요시 Python 3.12로 다운그레이드
- 라이브러리 버전 조정

### 로그 확인

```bash
# 파이프라인 로그 확인
tail -f logs/pipeline.log

# 특정 Stage 로그 필터링
grep "Stage 1" logs/pipeline.log
```

---

## 👨‍💻 개발 가이드

### 코드 품질 도구

```bash
# 테스트 실행
pytest

# 코드 포맷팅
black .
isort .

# 린팅
ruff check .

# 타입 체크
mypy .
```

### TDD 개발 프로세스

프로젝트는 Kent Beck의 TDD 원칙을 따릅니다:

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 최소 코드로 테스트 통과
3. **REFACTOR**: 구조 개선 (행위 불변)

**커밋 규칙**:

- `[STRUCTURAL]`: 구조적 변경 (리팩토링)
- `[BEHAVIORAL]`: 행위적 변경 (기능 추가/수정)

### Core 모듈 확장

새로운 헤더 추가:

```python
# scripts/core/header_registry.py
WAREHOUSE_LOCATIONS = [
    ("new_warehouse", "New Warehouse", ["New WH", "새창고"]),
]
```

새로운 벤더 추가:

```python
# scripts/core/file_registry.py
def get_source_file_name(vendor: str) -> str:
    mapping = {
        "HITACHI": "HITACHI(HE)",
        "SIEMENS": "SIEMENS(SIM)",
        "NEW_VENDOR": "NEW_VENDOR(CODE)",  # 추가
    }
    return mapping.get(normalize_vendor_name(vendor), "UNKNOWN")
```

---

## 📊 성능 지표

### 실행 시간 (8,930행 기준, 2025-01-25)

| Stage          | 실행 시간           | 처리량                    |
| -------------- | ------------------- | ------------------------- |
| Stage 1        | ~5분                | 8,930행, 3개 시트         |
| Stage 2        | ~30초               | 13개 파생 컬럼            |
| Stage 3        | ~1분 46초           | 12개 시트, 63개 헤더      |
| Stage 4        | ~1분                | 182개 이상치              |
| **전체** | **~8분 12초** | **전체 파이프라인** |

### 데이터 품질 지표

- **Source_Vendor Coverage**: 99.3% (8,634/8,697)
- **SQM 계산률**: 99.7% (8,905/8,930)
- **Stack_Status 파싱률**: 98.9% (8,831/8,930)
- **표준 헤더 매칭률**: 100% (63/63)

### 최적화 성과

- **Stage 3 벡터화**: 155초 → 28초 (82% 개선)
- **전체 파이프라인**: 217초 → 130초 (40% 개선)
- **메모리 효율성**: Polars 사용으로 30-50% 절약

---

## 🤝 기여 가이드

### 기여 프로세스

1. **Fork** 저장소
2. **Feature Branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **변경사항 커밋** (커밋 메시지 규칙 준수)
4. **테스트 실행** (`pytest`)
5. **Pull Request** 제출

### 커밋 메시지 규칙

```
[STRUCTURAL] Extract function for better readability
[BEHAVIORAL] Add SQM calculation fallback logic
[FIX] Correct Source_Vendor assignment in Stage 1
[FEAT] Add SIEMENS data auto-merge in Stage 1
```

### 코드 리뷰 체크리스트

- [ ] 모든 테스트 통과
- [ ] 코드 포맷팅 (black, isort)
- [ ] 린팅 오류 없음
- [ ] 문서 업데이트
- [ ] 성능 영향 평가

---

## 📄 라이선스

이 프로젝트는 Samsung C&T Logistics와 ADNOC·DSV Partnership을 위한 내부 프로젝트입니다.

---

## 📚 추가 문서

### 빠른 시작

- [빠른 시작 가이드](docs/common/PIPELINE_EXECUTION_GUIDE.md) - 5분 안에 전체 파이프라인 실행
- [Stage별 상세 가이드](docs/common/STAGE_BY_STAGE_GUIDE.md) - 통합 실행 가이드

### 기술 문서

- [파이프라인 아키텍처](docs/technical/PIPELINE_ARCHITECTURE.md) - 전체 시스템 구조
- [파이프라인 실행 흐름](docs/technical/PIPELINE_EXECUTION_FLOW_DETAILED.md) - 상세 실행 흐름
- [Core 모듈 가이드](scripts/core/README.md) - Core 모듈 사용법

### Stage별 문서

- [Stage 1 사용자 가이드](docs/common/STAGE1_USER_GUIDE.md)
- [Stage 1 Standalone 가이드](scripts/stage1_Standalone/standalone/README_STANDALONE.md)
- [Stage 2 사용자 가이드](docs/common/STAGE2_USER_GUIDE.md)
- [Stage 3 사용자 가이드](docs/common/STAGE3_USER_GUIDE.md)
- [Stage 4 사용자 가이드](docs/common/STAGE4_USER_GUIDE.md)

### 보고서

- [Core 모듈 통합 보고서](docs/reports/CORE_MODULE_INTEGRATION_REPORT.md)
- [벡터화 최적화 보고서](docs/reports/stage3-performance-optimization-completed.md)
- [Stage 4 Balanced Boost 보고서](docs/reports/STAGE4_BALANCED_BOOST_UPGRADE_REPORT.md)

---

## 📞 문의

프로젝트 관련 문의사항은 개발팀에 연락해주세요.

---

**버전**: v4.0.54
**최종 업데이트**: 2025-01-25
**Python 버전**: 3.13+
**프로젝트**: HVDC PROJECT - Samsung C&T Logistics & ADNOC·DSV Strategic Partnership

이 README는 다음을 포함합니다:

1. 프로젝트 개요 및 목적
2. 주요 기능 (Stage별)
3. 시스템 요구사항 및 설치 방법
4. 빠른 시작 가이드
5. 파이프라인 아키텍처 설명
6. Stage별 상세 가이드
7. 프로젝트 구조
8. 설정 파일 설명
9. 사용 예시
10. 문제 해결 가이드
11. 개발 가이드
12. 성능 지표
13. 기여 가이드
