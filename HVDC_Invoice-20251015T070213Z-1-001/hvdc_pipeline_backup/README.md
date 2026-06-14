# HVDC Pipeline Backup

이 폴더는 HVDC Invoice Audit 프로젝트의 pipe1과 pipe2 필수 파일들의 백업입니다.

## 폴더 구조

```
hvdc_pipeline_backup/
├── pipe1/                    # 데이터 동기화 및 Post-AGI 처리
│   ├── scripts/             # Python 스크립트
│   │   ├── post_agi_column_processor.py    # Post-AGI 컬럼 처리
│   │   ├── data_synchronizer_v29.py        # 데이터 동기화
│   │   ├── agi_columns.py                  # 컬럼 정의 상수
│   │   └── __init__.py                     # 패키지 초기화
│   ├── docs/                # 문서
│   │   └── README.md                       # Pipe1 실행 가이드
│   ├── data/                # 필수 데이터 파일
│   │   ├── CASE LIST.xlsx                  # Master 파일 (968KB)
│   │   └── HVDC WAREHOUSE_HITACHI(HE).xlsx # Warehouse 파일 (855KB)
│   ├── tests/               # 테스트
│   │   └── test_post_agi_column_processor.py
│   └── requirements.txt     # Python 의존성
├── pipe2/                    # 종합 보고서 생성
│   ├── scripts/             # Python 스크립트
│   │   └── hvdc_excel_reporter_final_sqm_rev (1).py  # 종합 보고서 생성
│   ├── docs/                # 문서
│   │   ├── README.md                       # Pipe2 실행 가이드
│   │   └── PIPELINE_USER_GUIDE.md         # 전체 파이프라인 가이드
│   ├── data/                # 필수 데이터 파일
│   │   └── HVDC WAREHOUSE_HITACHI(HE).xlsx # 입력 파일 (855KB)
│   └── requirements.txt     # Python 의존성
├── tests/                    # 공통 테스트
│   └── test_stage1_warehouse_alignment.py  # Stage-1 테스트
└── README.md                # 이 파일
```

## 설치 및 실행

### 1. Python 환경 설정
```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r pipe1/requirements.txt
pip install -r pipe2/requirements.txt
```

### 2. Pipe1 실행 (데이터 동기화 및 Post-AGI 처리)
```bash
cd pipe1
python scripts/data_synchronizer_v29.py
python scripts/post_agi_column_processor.py
```

### 3. Pipe2 실행 (종합 보고서 생성)
```bash
cd pipe2
python scripts/hvdc_excel_reporter_final_sqm_rev\ \(1\).py
```

### 4. 테스트 실행
```bash
# Pipe1 테스트
pytest pipe1/tests/ -v

# Pipe2 테스트
pytest tests/test_stage1_warehouse_alignment.py -v
```

## 주요 기능

### Pipe1
- **데이터 동기화**: Master ↔ Warehouse 데이터 동기화
- **Post-AGI 처리**: 13개 컬럼 자동 계산 (Status_*, handling, SQM 등)
- **색상 표시**: 변경사항 시각화 (🟠주황/🟡노랑)

### Pipe2
- **종합 보고서**: 다중 시트 Excel 보고서 생성
- **이상치 탐지**: ML + 규칙 기반 탐지
- **시각화**: 색상 기반 이상치 표시

## 버전 정보

- **백업 생성일**: 2025-10-19
- **Pipe1 코드**: v1.0 (2025-10-18 패치 적용)
- **Pipe2 코드**: v3.0-corrected (2025-01-09 패치 적용)
- **테스트**: 최근 생성됨 (2025-10-19)

## 파일 크기

- **총 크기**: ~2.8MB
- **코드**: ~100KB
- **데이터**: ~2.7MB
- **문서**: ~50KB

## 원본 위치

- **Pipe1 원본**: `./pipe1/`
- **Pipe2 원본**: `./pipe2/`
- **Hitachi 원본**: `./hitachi/`

## 주의사항

1. **데이터 파일**: Excel 파일들은 실행에 필수입니다
2. **의존성**: requirements.txt의 모든 패키지가 필요합니다
3. **테스트**: 실행 전 테스트를 통해 환경을 확인하세요
4. **백업**: 원본 파일을 수정하기 전에 백업을 권장합니다

## 문제 해결

### 일반적인 문제
- **ImportError**: requirements.txt의 패키지가 설치되지 않음
- **FileNotFoundError**: 데이터 파일 경로 확인 필요
- **PermissionError**: Excel 파일이 다른 프로그램에서 열려있음

### 로그 확인
- Pipe1: 콘솔 출력으로 진행상황 확인
- Pipe2: 생성된 보고서 파일 확인

## 연락처

- **프로젝트**: HVDC Invoice Audit
- **생성자**: Samsung C&T Logistics | ADNOC·DSV Partnership
- **최종 업데이트**: 2025-10-19
