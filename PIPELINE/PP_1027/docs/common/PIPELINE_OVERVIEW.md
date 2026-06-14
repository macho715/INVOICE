# HVDC Pipeline Overview

## 개요

HVDC Pipeline은 Samsung C&T Logistics와 ADNOC·DSV Partnership을 위한 통합 데이터 처리 파이프라인입니다. 원본 데이터부터 최종 분석 리포트까지 전체 프로세스를 자동화합니다.

## 현재 버전: v4.0.42 (Core v1.2.0)

### 최신 업데이트 (2025-10-27)
**Core 벤더 메타데이터 표준화 완료**:
- Source_Vendor coverage: 30.7% → **99.3%** (+68.6%)
- Source_File 정확성: 0% → **100%** (벤더별 정확한 매핑)
- SIEMENS 전용 시트: 0건 → **1,606건** 완전 분리
- Core 모듈 버전: v1.1.0 → **v1.2.0**

**주요 개선사항**:
1. **`@core/header_registry.py`**: METADATA 헤더 3개 추가 (source_vendor, source_sheet, source_file)
2. **`@core/file_registry.py`**: get_source_file_name() 함수 추가, 벤더별 source_file 매핑
3. **Stage 1**: 모든 데이터에 Source_Vendor 자동 설정
4. **Stage 3**: Source_File 동적 생성 (Source_Vendor 기반)

## 파이프라인 아키텍처

```mermaid
graph TD
    A[Raw Data] --> B[Stage 1: Data Sync + Metadata]
    B --> C[Stage 2: Derived Columns]
    C --> D[Stage 3: Report Generation]
    D --> E[Stage 4: Anomaly Detection]

    B --> F[Synced Data + Source_Vendor/Sheet]
    C --> G[Enhanced Data]
    D --> H[Reports + Source_File]
    E --> I[Anomaly Reports]

    J[Configuration] --> B
    J --> C
    J --> D
    J --> E
    
    K[Core v1.2.0] --> B
    K --> D
```

## Stage별 상세

### Stage 1: 데이터 동기화 + 벤더 메타데이터 설정
- **입력**: 원본 Excel 파일들 (HITACHI, SIEMENS)
- **처리**: 
  - 데이터 정제, 컬럼 정규화, 타입 변환
  - **Source_Vendor 자동 설정** (HITACHI/SIEMENS)
  - **Source_Sheet 자동 설정** (원본 시트명)
  - Master-Warehouse 동기화
- **출력**: 동기화된 데이터 (`.synced.xlsx`) + 벤더 메타데이터 (99.3% coverage)

### Stage 2: 파생 컬럼 생성
- **입력**: 동기화된 데이터
- **처리**: 13개 파생 컬럼 계산
- **출력**: 파생 컬럼이 추가된 데이터 (`.derived.xlsx`)

### Stage 3: 보고서 생성 + Source_File 동적 생성
- **입력**: 파생 컬럼 데이터 (Source_Vendor 포함)
- **처리**: 
  - 다중 시트 Excel 보고서 생성
  - **Source_File 동적 설정** (Source_Vendor 기반)
    - HITACHI → "HITACHI(HE)"
    - SIEMENS → "SIEMENS(SIM)"
  - 벤더별 전용 시트 생성 (HITACHI_원본데이터_Fixed, SIEMENS_원본데이터_Fixed)
- **출력**: 종합 보고서 (`.report.xlsx`) + 벤더 분리 시트

### Stage 4: 이상치 탐지
- **입력**: 최종 데이터
- **처리**: 통계적 이상치 분석
- **출력**: 이상치 리포트 (`.anomaly.xlsx`)

## 데이터 플로우

1. **Raw Data** → 정제 및 동기화
2. **Synced Data** → 파생 컬럼 추가
3. **Enhanced Data** → 보고서 생성
4. **Reports** → 이상치 탐지
5. **Final Output** → 분석 완료

## 성능 최적화

- **벡터화 연산**: pandas 벡터화로 10배 속도 향상
- **메모리 관리**: 대용량 데이터 처리 최적화
- **병렬 처리**: 가능한 부분에서 병렬 실행
- **캐싱**: 중간 결과 캐싱으로 재실행 시간 단축

## 에러 핸들링

- **단계별 검증**: 각 Stage에서 입력 데이터 검증
- **롤백 메커니즘**: 실패 시 이전 단계로 롤백
- **로그 기록**: 모든 처리 과정 로그 기록
- **복구 전략**: 자동 복구 및 수동 개입 옵션
