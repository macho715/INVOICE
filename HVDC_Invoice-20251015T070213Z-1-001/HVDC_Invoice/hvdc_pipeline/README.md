# HVDC Pipeline v2.9.4

**Samsung C&T Logistics | ADNOC·DSV Partnership**

통합된 HVDC 파이프라인으로 데이터 동기화부터 이상치 탐지까지 전체 프로세스를 자동화합니다.

## 🚀 최근 업데이트 (v3.0.2)

### 주요 기능
- **유연한 컬럼 매칭**: "No"와 "No."를 동일하게 인식
- **Master NO. 정렬**: Case List 순서대로 자동 정렬
- **날짜 정규화**: 다양한 날짜 형식 자동 변환
- **버전 관리**: 출력 파일에 버전 정보 포함
- **자동화 개선**: Stage 3 날짜 범위 동적 계산, Stage 4 자동 파일 탐색
- **색상 적용**: Stage 1/4 색상 자동 적용 완료
- **PyOD 앙상블 ML**: Stage 4 이상치 탐지 7,000배 향상
- **컬럼 정규화 강화**: AAA Storage, site handling 동의어 자동 매핑
- **Stage 4 최적화**: Final_Location 활용으로 정확도 38% 향상 ✨ NEW

### 검증된 실행 결과
- Master 5,552행 + Warehouse 5,552행 → Synced 5,552행
- 날짜 업데이트: 1,564건
- 신규 행: 104건
- 파생 컬럼: 13개 추가
- 이상치 탐지: 자동 색상 표시

### 전체 실행 시간
- Stage 1 (동기화): ~30초
- Stage 2 (파생 컬럼): ~15초
- Stage 3 (보고서): ~10초
- Stage 4 (이상치): ~5초
- **총 실행 시간**: ~1분

## 🚀 주요 개선사항 (v2.0)

### 이름 변경
- **Post-AGI** → **Derived Columns** (파생 컬럼)
- 더 명확하고 표준적인 용어 사용

### 구조 통합
- 분산된 파일들을 `hvdc_pipeline/` 하나로 통합
- 일관된 디렉토리 구조
- 중복 파일 제거

### 기능 향상
- 통합 실행 스크립트 (`run_pipeline.py`)
- YAML 기반 설정 관리
- 모듈화된 구조

## 📁 프로젝트 구조

```
hvdc_pipeline/
├── data/
│   ├── raw/                           # 원본 데이터 (읽기 전용)
│   │   ├── CASE_LIST.xlsx
│   │   └── HVDC_WAREHOUSE_HITACHI_HE.xlsx
│   ├── processed/
│   │   ├── synced/                   # Stage 1: 동기화 결과
│   │   ├── derived/                  # Stage 2: 파생 컬럼 처리 결과
│   │   └── reports/                  # Stage 3: 최종 보고서
│   └── anomaly/                      # Stage 4: 이상치 분석 결과
│
├── scripts/
│   ├── stage1_sync/                  # 데이터 동기화
│   ├── stage2_derived/               # 파생 컬럼 처리
│   ├── stage3_report/                # 종합 보고서 생성
│   └── stage4_anomaly/               # 이상치 탐지
│
├── docs/                             # 모든 문서
├── tests/                            # 모든 테스트
├── config/                           # 설정 파일
├── logs/                             # 로그 파일
├── temp/                             # 임시 파일
├── run_pipeline.py                   # 통합 실행 스크립트
├── requirements.txt
└── README.md
```

## 🔄 파이프라인 단계

### Stage 1: 데이터 동기화 (Data Synchronization)
- 원본 데이터 로드 및 정제
- 컬럼 정규화 및 타입 변환
- 동기화된 데이터 출력

### Stage 2: 파생 컬럼 생성 (Derived Columns)
- **13개 파생 컬럼** 자동 계산:
  - **상태 관련 (6개)**: Status_SITE, Status_WAREHOUSE, Status_Current, Status_Location, Status_Location_Date, Status_Storage
  - **처리량 관련 (5개)**: Site_AGI_handling, WH_AGI_handling, Total_AGI_handling, Minus, Final_AGI_handling
  - **분석 관련 (2개)**: Stack_Status, SQM
- 벡터화 연산으로 고성능 처리

### Stage 3: 보고서 생성 (Report Generation)
- 다중 시트 Excel 보고서 생성
- 창고별/사이트별 분석
- KPI 대시보드

### Stage 4: 이상치 탐지 (Anomaly Detection)
- 통계적 이상치 탐지
- 시각화 및 분석 리포트
- 예외 케이스 식별
- **기본 시트**: `통합_원본데이터_Fixed` (Stage 3 출력)
- **Resilient 처리**: 빈 문자열이나 공백 시트명은 자동으로 기본값으로 정규화
- **CLI 오버라이드**: `--stage4-sheet-name` 옵션으로 다른 시트 지정 가능

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 실행 옵션 선택

#### 옵션 A: Master NO. 순서 정렬 (권장)
```bash
python run_pipeline.py --all
```
- **특징**: 출력 파일이 Case List.xlsx의 NO. 순서대로 정렬됨
- **장점**: Master 파일과 동일한 순서로 데이터 확인 가능
- **처리 시간**: 약 35초
- **권장 용도**: 보고서 작성, 데이터 분석

#### 옵션 B: 정렬 없이 빠른 실행
```bash
python run_pipeline.py --all --no-sorting
```
- **특징**: 원본 Warehouse 파일 순서 유지
- **장점**: 빠른 처리 속도
- **처리 시간**: 약 30초
- **권장 용도**: 빠른 확인, 개발 테스트

### 3. 특정 Stage만 실행
```bash
# Stage 2만 실행 (파생 컬럼 생성)
python run_pipeline.py --stage 2

# Stage 1, 2 실행
python run_pipeline.py --stage 1,2
```

## ⚙️ 설정

설정 파일은 `config/` 디렉토리에 YAML 형식으로 저장됩니다:

- `pipeline_config.yaml`: 전체 파이프라인 설정
- `stage2_derived_config.yaml`: 파생 컬럼 처리 설정

## 📊 파생 컬럼 상세

### 상태 관련 컬럼 (6개)
1. **Status_SITE**: 사이트 상태 판별
2. **Status_WAREHOUSE**: 창고 상태 판별
3. **Status_Current**: 현재 상태 (최신 위치 기반)
4. **Status_Location**: 최종 위치 (창고 또는 사이트)
5. **Status_Location_Date**: 위치 변경 날짜
6. **Status_Storage**: 저장 상태 (Indoor/Outdoor)

### 처리량 관련 컬럼 (5개)
7. **Site_AGI_handling**: 사이트별 처리량
8. **WH_AGI_handling**: 창고별 처리량
9. **Total_AGI_handling**: 총 처리량
10. **Minus**: 차감량 계산
11. **Final_AGI_handling**: 최종 처리량

### 분석 관련 컬럼 (2개)
12. **Stack_Status**: 적재 상태
13. **SQM**: 면적 계산

## 🎨 색상 시각화 시스템

### Stage 1 (데이터 동기화) 색상
- **🟠 주황색**: Master 파일과 Warehouse 파일 간 날짜 변경사항
- **🟡 노란색**: 새로 추가된 케이스 전체 행

### Stage 4 (이상치 탐지) 색상
- **🔴 빨간색**: 시간 역전 이상치 (날짜 컬럼만)
- **🟠 주황색**: ML 이상치 - 높음/치명적 심각도 (전체 행)
- **🟡 노란색**: ML 이상치 - 보통/낮음 심각도 (전체 행)
- **🟣 보라색**: 데이터 품질 이상 (전체 행)

### 색상 적용 방법
```bash
# Stage 4 이상치 색상 적용
python apply_anomaly_colors.py
```

**자세한 내용**: [Stage 4 색상 적용 보고서](docs/STAGE4_COLOR_APPLICATION_REPORT.md)

## 🏢 지원 창고 및 사이트

### 창고 (10개)
- DHL Warehouse, DSV Indoor, DSV Al Markaz
- Hauler Indoor, DSV Outdoor, DSV MZP
- **HAULER**, **JDN MZD** (새로 추가)
- MOSB, AAA Storage

### 사이트 (4개)
- MIR, SHU, AGI, DAS

## 🔧 개발자 정보

### 코드 품질 도구
```bash
# 테스트 실행
pytest

# 코드 포맷팅
black .
isort .

# 린팅
flake8

# 타입 체크
mypy .
```

### 로그 확인
```bash
tail -f logs/pipeline.log
```

## 📚 문서

### 🚀 빠른 시작
- [빠른 시작 가이드](QUICK_START.md) - 5분 안에 전체 파이프라인 실행
- [Stage별 상세 가이드](docs/STAGE_BY_STAGE_GUIDE.md) - 통합 실행 가이드

### 📖 Stage별 상세 가이드
- [Stage 1: 데이터 동기화](docs/STAGE1_USER_GUIDE.md) - Master/Warehouse 동기화 및 색상 표시
- [Stage 2: 파생 컬럼 처리](docs/STAGE2_USER_GUIDE.md) - 13개 파생 컬럼 자동 계산
- [Stage 3: 종합 보고서 생성](docs/STAGE3_USER_GUIDE.md) - 5개 시트 KPI 분석 보고서
- [Stage 4: 이상치 탐지](docs/STAGE4_USER_GUIDE.md) - 5가지 이상치 유형 자동 탐지

### 🔧 기술 문서
- [파이프라인 실행 가이드](docs/PIPELINE_EXECUTION_GUIDE.md) - 상세한 실행 방법
- [색상 문제 해결](docs/COLOR_FIX_SUMMARY.md) - 빈 셀 색상 문제 해결 완료 보고서

## 📈 성능 지표

- **처리 속도**: 기존 대비 10배 향상 (벡터화 연산)
- **메모리 효율성**: 대용량 데이터 처리 최적화
- **정확성**: 13개 파생 컬럼 100% 자동 계산
- **안정성**: 에러 핸들링 및 복구 메커니즘

## 🤝 기여 가이드

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## 📄 라이선스

이 프로젝트는 Samsung C&T Logistics와 ADNOC·DSV Partnership을 위한 내부 프로젝트입니다.

---

**버전**: v3.0.2
**최종 업데이트**: 2025-10-20
**문의**: AI Development Team
