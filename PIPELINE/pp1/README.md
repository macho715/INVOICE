# HVDC Pipeline v4.0.44

**Samsung C&T Logistics | ADNOC·DSV Partnership**

통합된 HVDC 파이프라인으로 데이터 동기화부터 이상치 탐지까지 전체 프로세스를 자동화합니다.

## 🚀 최근 업데이트

### v4.0.44 - 루트 폴더 정리 (2025-10-27)

#### 프로젝트 루트 대폭 단순화
- **3단계 접근**: 안전 삭제 (11개) + 아카이브 (25개) + 보류 (자료 폴더)
- **루트 파일**: 48개 → **9개** (81% 감소)
- **아카이브 구조**: temp_scripts/ + patch_docs/ + old_reports/
- **최종 루트**: 9개 핵심 파일만 유지
- **효과**: 유지보수성 극대화, 프로젝트 구조 명확화 ✅

### v4.0.43 - 전체 Stage 폴더 정리 (2025-10-27)

#### 프로젝트 구조 대폭 단순화
- **백업 폴더 제거**: 4개 폴더에서 18개의 오래된 백업 파일 삭제
- **캐시 폴더 제거**: 4개의 __pycache__ 폴더 삭제 (자동 재생성)
- **최종 구조**: 31개 파일 (Core 11 + Stage1 3 + Stage2 5 + Stage3 7 + Stage4 8)
- **검증 완료**: Core v1.2.0 정상 작동 (27개 컴포넌트)
- **효과**: 22개 파일/폴더 제거로 유지보수성 크게 개선 ✅

### v4.0.42 - Core 벤더 메타데이터 표준화 (2025-10-27)

#### 🎯 Core v1.2.0: 벤더 메타데이터 완전 통합

**문제 해결**:
- Source_Vendor 누락: 30.7% → **99.3%** (6,025건 → 63건 NULL)
- Source_File 오류: 모두 "HITACHI(HE)" → 벤더별 정확한 매핑
- SIEMENS 전용 시트: 비어있음 → **1,606건 완전 분리**

**실행 결과**:
| 항목 | Before | After | 개선 |
|------|--------|-------|------|
| **Source_Vendor coverage** | 30.7% (2,672/8,697) | **99.3% (8,634/8,697)** | +68.6% |
| **HITACHI 메타데이터** | 1,066건 | **7,028건** | +5,962건 |
| **SIEMENS 메타데이터** | 1,606건 | **1,606건** | 유지 |
| **Source_File 정확성** | 0% | **100%** | 완전 해결 |
| **Source_Sheet coverage** | - | **100%** | 신규 추가 |

**Core 모듈 확장**:
```python
from core import get_source_file_name, normalize_vendor_name

# 벤더별 Source_File 동적 생성
source_file = get_source_file_name('HITACHI')  # → "HITACHI(HE)"
source_file = get_source_file_name('SIEMENS')  # → "SIEMENS(SIM)"

# 벤더명 정규화
vendor = normalize_vendor_name('SIMENSE')  # → "SIEMENS" (typo 교정)
```

**수정된 파일 (5개)**:
1. `scripts/core/header_registry.py` - METADATA 헤더 3개 추가
2. `scripts/core/file_registry.py` - get_source_file_name() 추가
3. `scripts/core/__init__.py` - v1.2.0, export 추가
4. `scripts/stage1_sync_sorted/data_synchronizer_v30.py` - Source_Vendor 전면 설정
5. `scripts/stage3_report/report_generator.py` - Source_File 동적 설정

**검증 완료**:
- ✅ Source_Vendor: 99.3% coverage
- ✅ Source_File: HITACHI→"HITACHI(HE)", SIEMENS→"SIEMENS(SIM)"
- ✅ Source_Sheet: 100% coverage
- ✅ SIEMENS 전용 시트: 1,606건 완전 분리

---

### v4.0.41 - Master 파일 정정 + Core 파일 관리 시스템 (2025-10-27)

#### 🚨 CRITICAL FIX: Master 파일 설정 오류 (1,172행 복구)
- **문제**: 동일 파일을 Master/Warehouse로 사용 → 1,006건 누락
- **해결**: Case List_Hitachi.xlsx를 Master로 정정
- **결과**: 7,525행 → **8,697행** (+1,172행 복구)

| 항목 | Before | After | 변화 |
|------|--------|-------|------|
| **Master 파일** | HVDC WAREHOUSE | **Case List_Hitachi** | ✅ |
| **HITACHI Case** | 5,850 | **8,525** (병합 후) | **+2,675** |
| **전체 SYNCED** | 7,525 | **8,697** | **+1,172** |

#### ⚡ NEW: Core 파일명 관리 시스템
**신규**: `scripts/core/file_registry.py` - 중앙집중식 파일 경로 관리

```python
from core import FileRegistry

# 파일 경로 중앙 관리
master = FileRegistry.get_master_file('hitachi')
synced = FileRegistry.get_synced_file('3.10', merged=True)
variants = FileRegistry.get_sheet_variants('case_list')
```

**Benefits**:
- ✅ 파일명 하드코딩 제거
- ✅ 버전 관리 자동화
- ✅ 시트명 Variants 동적 매칭
- ✅ Core v1.1.0 (헤더 + 파일명 완전 통합)

---

### v4.0.40 - SIEMENS 중복 제거 버그 수정 (2025-10-27)

#### 문제 해결
- **문제**: Stage 1에서 SIEMENS 데이터 중복 미제거 (2,239개 중복)
- **원인**: `pd.concat()` 후 Case No 기준 중복 제거 로직 없음
- **해결**: `drop_duplicates(subset=['Case No.'])` 로직 추가

#### 결과
- **SIEMENS**: 3,845행 (중복) → **1,606행** (고유 Case만 유지)
- **전체 SYNCED**: 9,930행 → **7,525행**
- **Case No 중복**: 2,405개 → **0개** ✅
- **데이터 무결성**: 각 Case No당 1개의 레코드만 유지

#### 영향
- Stage 1 출력: v3.9 (중복 제거 완료)
- Stage 2-3: 일관성 유지 (7,525행)
- 문서 업데이트: 모든 건수 정정 완료

---

### v4.0.39 - Core 중앙집중식 헤더 관리 완성 (2025-10-27)

### Core 중앙집중식 헤더 관리 100% 달성 (2025-10-27)
- **Achievement**: 완전한 SSOT(Single Source of Truth) 구현 완료
  - Stage 3, 4의 하드코딩 제거
  - 모든 창고/현장 헤더를 `@core/header_registry.py`에서 관리
  - Core 사용률: 65% → **100%** 달성 🎯

- **Refactored Files**:
  1. **`scripts/stage3_report/report_generator.py`** (5개 위치)
     - 창고/현장 컬럼, 위치 우선순위, 창고 우선순위, 기본 SQM
     - 하드코딩 → `get_warehouse_columns()`, `get_site_columns()` 사용
  
  2. **`scripts/stage3_report/hvdc_excel_reporter_final_sqm_rev.py`** (2개 위치)
     - 창고/현장 컬럼을 Core에서 동적으로 가져오기
  
  3. **`scripts/stage4_anomaly/anomaly_detector_balanced.py`** (2개 위치)
     - 대문자+언더스코어 형식으로 자동 변환하여 Core 사용

- **Verification Results**:
  - ✅ 전체 파이프라인 실행 성공 (Stage 1-4)
  - ✅ 9개 창고 정확히 적용: `['DHL WH', 'DSV Indoor', 'DSV Al Markaz', 'AAA Storage', 'DSV Outdoor', 'DSV MZP', 'MOSB', 'Hauler Indoor', 'JDN MZD']`
  - ✅ Stage 2: 9930행, 54컬럼
  - ✅ Stage 3: 12개 시트, 123.50초
  - ✅ Stage 4: 202개 이상치 탐지
  - ✅ Linter: 오류 없음

- **Benefits**:
  - **새 창고 추가**: `header_registry.py` 한 곳만 수정
  - **자동 동기화**: 모든 Stage 자동 반영
  - **유지보수성**: 하드코딩 완전 제거
  - **일관성**: Stage 1-4 완벽히 통합

**Core 사용률 진화**:
| Stage | v4.0.38 | v4.0.39 | 개선 |
|-------|---------|---------|------|
| Stage 1 | 100% | 100% | - |
| Stage 2 | 100% | 100% | - |
| Stage 3 | 60% | **100%** | +40% |
| Stage 4 | 0% | **100%** | +100% |
| **평균** | **65%** | **100%** | **+35%** |

---

## 🚀 이전 업데이트 (v4.0.38 - HAULER 중복 제거)

### Stage 3 HAULER 중복 컬럼 제거 (2025-10-27)
- **Problem**: 입고로직 종합 리포트에 HAULER 빈 컬럼 존재
  - Hauler Indoor와 중복 (동일 창고)
  - 총 컬럼 수: 66개 (HAULER 포함)
  - `header_registry.py`에서는 별칭으로 정의되어 있으나 `report_generator.py`에서 별도 창고로 하드코딩

- **Solution**: report_generator.py에서 HAULER 제거
  - 4개 위치에서 하드코딩 제거 (warehouse_columns, location_priority, warehouse_priority, warehouse_base_sqm)
  - Hauler Indoor만 유지
  - 우선순위 재조정 (DSV MZP: 7→6, JDN MZD: 8→7, MOSB: 9→8)

- **Result**:
  - ✅ 총 컬럼 수: 65개 (정상화)
  - ✅ 중복 제거 완료
  - ✅ 총 9개 창고로 정리
  - ✅ Stage 3 실행 시간: 109.37초 (정상)

**향후 개선**:
- `@core/get_warehouse_columns()` 사용으로 완전 중앙집중화
- 새 창고 추가 시 header_registry만 수정
- 하드코딩 제거로 유지보수성 향상

---

## 🚀 이전 업데이트 (v4.0.34 - 스냅샷 앵커링 패치)

### 창고_월별_입출고 누적 재고 정확도 개선 (2025-10-25)
- **Problem**: 월별 누적 재고 계산 시 기초재고 누락
  - 흐름(Flow)만 합산하여 누적 계산 → 부정확
  - 예시: DSV Indoor 누적 44 vs 실제 스냅샷 789
  - 전체 시계열 누적 재고가 실제와 불일치

- **Solution**: 스냅샷 앵커링으로 누적 재고 보정
  - **스냅샷 생성**: Final_Location 기준 현재고 계산
  - **앵커링 적용**: 마지막 달 누적을 스냅샷에 일치
  - **기초재고 보정**: 누락된 기초재고를 delta로 전 기간에 반영
  - **안전장치**: try-except로 실패 시 기존 로직 유지

- **Result**:
  - ✅ DSV Indoor 누적 789 달성 (목표값 정확히 일치)
  - ✅ 전체 파이프라인 정상 실행 (158초)
  - ✅ 기존 기능 유지 (정규화 패치 포함)

**핵심 개선**:
- 누적 재고 정확도 향상
- 시계열 일관성 확보
- Data Integrity 유지 (흐름 데이터 보존)
- Failure Safe 보장

**기술적 세부사항**:
- 스냅샷 소스: stats["processed_data"]에서 Final_Location별 집계
- 헤더 정규화: HeaderNormalizer로 창고명 표기 차이 처리
- 앵커링 방식: last_snap - last_flow = delta, 전체 누적에 delta 추가

**성능 영향**: Stage 3 실행 시간 +2초 (수용 가능)

---

## 🚀 이전 업데이트 (v4.0.33 - 창고_월별_입출고 정규화 패치)

### Stage 3 창고 정규화 시스템 구현 (2025-10-25)
- **Problem**: 창고명 표기 불일치로 중복 컬럼 생성 및 데이터 분산
  - `DSV Indoor`, `DSV_Indoor`, `DSV In` 등이 별도 컬럼으로 분리
  - `DHL WH`, `DHL Warehouse` 등이 중복 표시
  - 창고별 집계가 부정확 (데이터가 여러 컬럼에 분산)

- **Solution**: HeaderRegistry/Normalizer 기반 정규화 시스템
  - **Single Source of Truth**: `header_registry.py`를 창고 정의 중앙 관리소로 사용
  - **자동 별칭 매핑**: 대소문자/공백/구분자 차이 자동 처리
  - **정규화 피벗**: 모든 변형을 정식 창고명으로 통합하여 집계
  - **코드 변경 불필요**: 새 창고 추가는 레지스트리만 수정

- **Result**:
  - ✅ DSV Indoor 통합: 모든 변형이 단일 컬럼으로 통합
  - ✅ DHL WH 통합: 모든 변형이 단일 컬럼으로 통합
  - ✅ 데이터 정확성: 분산된 데이터가 올바르게 합산
  - ✅ 전체 파이프라인: Stage 1-4 정상 실행 (159초)

**주요 기능**:
- 창고 정의 중앙 집중화 (`header_registry.py`)
- 별칭 자동 정규화 (`HeaderNormalizer`)
- 정규화 피벗 테이블 (중복 제거)
- 유지보수성 향상 (창고 추가는 레지스트리만 수정)

**검증 결과**:
- 창고_월별_입출고: 39컬럼 (9개 창고 × 4개 타입 + 누계 + 입고월) ✅
- DSV Indoor 2025-09: 입고 18건, 출고 21건 정확 집계 ✅
- 전체 파이프라인: 7,182행 정상 처리 ✅

**향후 창고 추가 방법**:
```python
# header_registry.py에만 추가하면 자동 반영
warehouse_locations = [
    ("new_warehouse", "New Warehouse", ["New WH", "새창고"]),
]
```

---

## 🚀 이전 업데이트 (v4.0.32 - Stage 1 멀티시트/합쳐진 파일 출력)

### Stage 1 멀티시트 및 합쳐진 파일 출력 (2025-10-24)
- **2개 파일 생성**: Stage 1이 이제 2가지 형태로 출력
  - 멀티시트 파일: 3개 시트 유지 + 컬러링 (원본 구조 보존)
  - 합쳐진 파일: 단일 시트 (Stage 2 처리용 최적화)
- **Source_Sheet 컬럼**: 각 행이 어느 시트에서 왔는지 추적
- **명시적 데이터 순서**: Case List, RIL → HE Local → HE-0214,0252
- **Stage 2 최적화**: 합쳐진 파일을 직접 읽어 처리 속도 향상

**주요 기능**:
- 멀티시트 파일: 시트별 독립 데이터 + 컬러 하이라이트
- 합쳐진 파일: 전체 데이터 통합 + Source_Sheet 컬럼
- 시트 순서 보장: Case List, RIL (6,919행) 먼저
- Stage 2 입력 최적화: 사전 병합된 데이터 사용

**파일 출력**:
```
data/processed/synced/
├── HVDC WAREHOUSE_HITACHI(HE).synced_v3.6.xlsx         # 멀티시트 (3개 시트)
└── HVDC WAREHOUSE_HITACHI(HE).synced_v3.6_merged.xlsx  # 합쳐진 (단일 시트)
```

**검증 결과**:
- 멀티시트 파일: 3개 시트 정상 생성 + 컬러링 적용 ✅
- 합쳐진 파일: 7,091행, 42컬럼, 시트 순서 확인 ✅
- Stage 2 처리: 100% 성공, SQM 계산률 100% ✅

---

## 🚀 이전 업데이트 (v4.0.31 - Stage 1 데이터 완전성 수정)

### Stage 1 신규 케이스 데이터 완전성 수정 (2025-10-24)
- **Problem**: 신규 케이스 추가 시 semantic matching 안 된 컬럼이 빈 셀로 남음
  - EQ No, Description, L/W/H 등의 컬럼이 복사되지 않음
  - Master의 일부 데이터만 Warehouse로 전달됨
- **Solution**: Master의 모든 컬럼을 복사하되, semantic matching으로 컬럼명 매핑
  - STEP 1: 모든 Master 컬럼 복사
  - STEP 2: Semantic name mapping 적용
  - STEP 3: 누락 컬럼 초기화
  - Core 모듈 호환성 100% 유지
- **Result**:
  - 모든 컬럼 완전히 채워짐 (40개 컬럼)
  - SQM 계산률: 85% → 100% (15% 향상)
  - 데이터 무결성 100% 달성

**주요 기능**:
- Master 데이터 완전 보존
- Semantic matching 로직 유지
- 컬럼명 자동 매핑
- 누락 컬럼 자동 초기화

**검증 결과**: 이전에 비어있던 행들(4371-4405) 모두 데이터 채워짐 ✅

---

## 🚀 이전 업데이트 (v4.0.30 - 헤더 순서 정렬 & Stage 2/3/4 실행 완료)

### Stage 2/3/4 실행 결과 (2025-10-24)
- **🔧 헤더 순서 정렬 완료**: Stage 2와 Stage 3의 헤더 순서 100% 일치
  - HVDC CODE 문제 해결 (실제 데이터에 존재하지 않음 확인)
  - 실제 데이터 구조에 맞는 헤더 순서로 복원
- **📊 Stage 3 종합 보고서**: 12개 시트, 7,256행 데이터 처리
  - SQM 계산: 98.8% 성공률 (7,172개)
  - Stack_Status 파싱: 97.9% 성공률 (7,102개)
  - 창고 월별 입출고: Hybrid 접근으로 정확도 달성
- **🔍 Stage 4 이상 탐지**: 549개 이상치 탐지 및 분류
  - 5가지 이상치 유형 자동 분류
  - 심각도별 위험도 평가 (심각: 12개, 치명적: 525개, 경고: 12개)
- **⚡ 성능 최적화**: 총 실행 시간 51.48초
  - Stage 3: 28.90초 (보고서 생성)
  - Stage 4: 22.58초 (이상 탐지)

### 이전 업데이트 (v4.0.29 - 하이브리드 접근 구현)

### 하이브리드 접근: 오리지널 로직 복원 + 벡터화 최적화 (2025-10-24)
- **Problem**: 오리지널 파일 벤치마크 결과, 기존 로직의 근본적 문제 발견
  - 입고 필터링 너무 엄격 (6개만 집계)
  - 출고 날짜 조건이 실제 데이터와 완전 불일치
    - 오리지널: "다음 날 이동만" 조건
    - 실제 데이터: 평균 수백 일 소요 (3~554일), 다음 날 이동은 0.3%만
  - 창고간 이동 제외 로직 과도
- **Solution**: 데이터 분석 기반 하이브리드 접근
  - **입고**: 루프 기반, 모든 창고 입고 포함 (필터링 제거)
  - **출고**: 창고 입고일 이후 모든 현장 이동 인정 (실제 데이터 반영)
  - **창고간 이동**: 행별 추적으로 정확도 향상
- **Result**: 월별 입출고 계산 정확도 대폭 개선
  - 입고: 6 → 5,517 (완전 복원) ✅
  - 출고: 22 → 2,574 (117배 증가) ✅
  - 창고 재고: 2,943 (목표 범위 2,800~3,200) ✅

**주요 기능**:
- 실제 데이터 분석 기반 로직 개선
- 루프 기반 입고로 안정성 확보
- 정확한 출고 날짜 조건 (창고 입고 후 모든 현장 이동)
- 행별 창고간 이동 추적

**테스트 결과**: 입고/재고 목표 범위 달성 ✅

## 이전 업데이트 (v4.0.25 - 창고_월별_입출고 계산 수정)

### 창고_월별_입출고 시트 데이터 정상화 (2025-10-24)
- **Problem**: 창고_월별_입출고 시트의 데이터가 대부분 0으로 표시
  - 벡터화 입고 계산에서 Inbound_Type 필드 누락
  - create_warehouse_monthly_sheet()에서 조건 미충족
- **Solution**: _calculate_warehouse_inbound_vectorized()에 Inbound_Type 명시적 설정
- **Result**: 입고 데이터 정상 표시
  - 입고_DHL WH: 0 → 408
  - 입고_DSV Indoor: 0 → 2,360
  - 입고_DSV Outdoor: 0 → 2,846
  - 입고_MOSB: 0 → 2,286

**주요 기능**:
- 벡터화 함수에 Inbound_Type="external_arrival" 명시적 설정
- 창고별/월별 집계 정확성 확보
- 입고 데이터 정상화로 월별 분석 가능

**테스트 결과**: 10개 창고 모두 정상 입고 데이터 표시 ✅

## 이전 업데이트 (v4.0.24 - SCT Ref.No 컬럼 위치 수정)

### SCT Ref.No 컬럼 위치 최적화 (2025-10-23)
- **Problem**: SCT Ref.No가 65번째 위치에 있어서 찾기 어려움
- **Solution**: STANDARD_HEADER_ORDER에서 SCT Ref.No를 4번째 위치로 이동
- **Result**:
  - 1. no.
  - 2. Shipment Invoice No.
  - 3. SCT Ref.No ← 이동 완료
  - 4. Site

**주요 기능**:
- 컬럼 순서 일관성 확보
- Stage 2와 Stage 3 헤더 순서 통일
- 데이터 접근성 향상

**검증 결과**: 66개 컬럼, SCT Ref.No 3번째 위치 ✅

## 이전 업데이트 (v4.0.23 - Stage 3 Excel 컬럼 보존)

### Stage 3 Excel 컬럼 누락 문제 해결 (2025-10-23)
- **Problem**: Stage 3 실행 시 Stack_Status, Total sqm 컬럼이 DataFrame에는 존재하지만 Excel 파일에서 누락
  - DataFrame: 66개 컬럼 (Total sqm, Stack_Status 포함)
  - Excel 출력: 64개 컬럼 (Total sqm, Stack_Status 누락)
  - 근본 원인: 닫힌 ExcelWriter 컨텍스트 밖에서 to_excel() 호출
- **Solution**: 모든 시트를 단일 ExcelWriter 컨텍스트 안에서 저장
  - scripts/stage3_report/report_generator.py 재구성
  - SQM 관련 시트를 사전 계산 (writer 컨텍스트 밖)
  - 모든 to_excel() 호출을 단일 with pd.ExcelWriter() 블록 안으로 이동

**주요 기능**:
- DataFrame과 Excel 파일 간 데이터 무결성 보장
- 모든 66개 컬럼이 Excel 파일에 정상 저장
- 창고 적재 효율 분석 가능 (Total sqm = SQM × PKG)

**테스트 결과**: 66개 컬럼 모두 Excel 저장 완료 ✅

## 이전 업데이트 (v4.0.22 - Stage 3 Total sqm 계산)

### 📊 Stage 3 Total sqm 계산 로직 추가 (2025-10-23)
- **신규 컬럼 추가**: Stage 3 통합_원본데이터_Fixed 시트에 `Stack_Status`, `Total sqm` 추가
- **Stack_Status 파싱**: 기존 "Stack" 컬럼 텍스트 파싱 (core.data_parser 활용)
- **Total sqm 계산**: PKG × SQM × Stack_Status 공식으로 실제 적재 면적 계산
- **헤더 순서**: SQM → Stack_Status → Total sqm
- **core 통합**: 헤더 순서 및 데이터 파싱 로직 core 모듈에서 중앙 관리

**주요 기능**:
- **Stack_Status**: "X2" → 2, "Stackable / 3" → 3, "Not stackable" → 0
- **Total sqm**: 실제 적재 시 차지하는 총 면적 (창고 공간 계획 활용)
- **엣지 케이스**: Pkg=0, SQM=None, Stack_Status=None → None 처리

**예시**:
```
통합_원본데이터_Fixed 시트:
... | SQM | Stack_Status | Total sqm | ...
... | 9.84 | 2 | 196.80 | ...  (PKG=10, SQM=9.84, Stack=2)
... | 5.20 | 3 | 156.00 | ...  (PKG=10, SQM=5.20, Stack=3)
```

**테스트 결과**: 8개 테스트 모두 통과 ✅

### 이전 업데이트 (v4.0.20 - 헤더 관리 통합)

### 🔧 헤더 관리 로직 Core 통합 (2025-10-23)
- **중앙 집중식 관리**: 헤더 정규화 로직을 core 모듈로 통합
- **코드 중복 제거**: Stage별 중복 로직 완전 제거
- **일관성 향상**: 모든 Stage에서 동일한 헤더 처리 규칙
- **유지보수성**: 한 곳만 수정하면 모든 Stage 자동 적용
- **DRY 원칙**: 단일 책임 원칙 준수

**주요 개선사항**:
- normalize_header_names_for_stage2/3() 함수에 중복 'no' 컬럼 제거 로직 통합
- derived_columns_processor.py에서 중복 로직 제거 (4줄 코드 정리)
- 모든 Stage에서 core 함수만 호출하여 일관된 헤더 처리

**관련 문서**:
- [헤더 관리 통합 보고서](docs/reports/centralized-header-management-report.md) - 상세 구현 내역

### 이전 업데이트 (v4.0.17 - Stage 3 벡터화 최적화)

### ⚡ Stage 3 벡터화 최적화 (2025-10-23)
- **🚀 82% 성능 개선**: Stage 3 실행 시간 155초 → 28초 (82% 개선)
- **📊 전체 파이프라인**: 217초 → 140초 (35% 개선)
- **🔧 완전 벡터화**: `iterrows()` → `melt()`, `groupby()`, `apply()` 벡터화 연산
- **⚙️ 자동 폴백**: 벡터화 실패 시 레거시 버전으로 자동 전환
- **🖥️ Windows 호환**: multiprocessing spawn 방식 지원
- **📈 확장성**: 대용량 데이터 처리 시 선형 확장성

**성능 비교**:
```
이전 (iterrows):     155초
벡터화:              28초  ✅ (82% 개선)
병렬 처리:           29초  (벡터화 대비 3.3% 느림)
프로덕션 권장:        벡터화 버전 사용
```

**관련 문서**:
- [프로덕션 권장사항](docs/reports/PRODUCTION-RECOMMENDATION.md) - 벡터화 버전 사용 권장
- [벡터화 최적화 보고서](docs/reports/stage3-performance-optimization-completed.md) - 상세 구현 내역
- [병렬 처리 테스트](docs/reports/stage3-parallel-optimization-final-report.md) - 병렬 처리 성능 분석

### 이전 업데이트 (v4.0.16 - Raw Data Protection 검증 시스템)

### 🔒 Raw Data Protection 검증 시스템 (2025-10-23)
- **✨ 완전 자동화된 무결성 검증**: MD5 해시, 파일 크기, 수정 시간, 데이터 행 수 검증
- **🛡️ 100% 보안 보장**: Raw data 파일이 파이프라인 실행 중 절대 수정되지 않음을 검증
- **📊 상세 검증 보고서**: 검증 과정과 결과를 완전히 문서화한 323줄 보고서 제공
- **🔧 자동화 도구**: `scripts/verification/verify_raw_data_protection.py`로 언제든지 검증 가능
- **✅ 검증 결과**: 2개 raw data 파일 모두 PASS (MD5 해시 100% 일치, 파일 크기 100% 일치)

**검증 대상 파일**:
- `Case List.xlsx`: 1,179,971 bytes, MD5: 174459d39602d436...
- `HVDC Hitachi.xlsx`: 911,226 bytes, MD5: 9b90732f6dbb12aa...

**사용법**:
```bash
# 1. Raw data baseline 수집
python scripts\verification\verify_raw_data_protection.py

# 2. 파이프라인 실행
python run_pipeline.py --all

# 3. 검증 재실행 (자동으로 baseline과 비교)
python scripts\verification\verify_raw_data_protection.py
```

**상세 보고서**: [Raw Data Protection 검증 보고서](docs/reports/RAW_DATA_PROTECTION_VERIFICATION_REPORT.md)

### 이전 업데이트 (v4.0.12 - Complete Documentation & Column Order Fix)

### 중요 기능 추가 (2025-10-22)
- **✨ Stage 1 컬럼 순서 최적화**: Shifting/Source_Sheet 위치 원본 데이터 순서 유지
- **🔧 DHL WH 데이터 복구**: 102건 데이터 정상 처리 및 Location 컬럼 자동 처리
- **📊 완전한 문서화**: 모든 Stage별 README 문서 완성 및 아카이브 시스템 구축
- **🎯 코드 정리 완료**: 임시/분석 스크립트 체계적 아카이브 처리

### 이전 업데이트 (v4.0.2 - Stage 3 Path Fix)
- **🐛 Stage 3 Path Fix**: Stage 3가 Stage 2 derived 폴더를 올바르게 읽도록 수정
- **✅ DHL WH Data Recovery**: 누락된 DHL WH 102건 데이터 복구
- **📊 Column Name Unification**: "DHL Warehouse" → "DHL WH" 통일
- **⚡ Performance**: 전체 실행 시간 ~3.6분 (216초)

### 이전 업데이트 (v4.0.2 - Multi-Sheet + Stable Sorting)
- **📊 Multi-Sheet Support**: 엑셀 파일의 모든 시트 자동 로드 및 병합 (3 sheets → 7,172 records)
- **🔧 DSV WH Consolidation**: "DSV WH" → "DSV Indoor" 자동 병합 (1,226 records total)
- **✅ Stable Sorting**: 복합 정렬 키 (No, Case No.)로 HVDC HITACHI 순번 유지
- **✨ Semantic Header Matching**: 하드코딩 100% 제거, 의미 기반 자동 매칭
- **🎯 자동 헤더 탐지**: 97% 신뢰도로 헤더 행 자동 인식

### 이전 버전 (v3.0.2)

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

### 전체 실행 시간 (v4.0.17 - 벡터화 최적화)
- Stage 1 (v3.0 Multi-Sheet): ~36초 ⚡ (3 sheets 병합 + DSV WH 통합 + 안정 정렬)
- Stage 2 (파생 컬럼): ~16초
- Stage 3 (벡터화 최적화): ~28초 ⚡ (155초 → 28초, 82% 개선)
- Stage 4 (이상치 + 색상): ~50초 (탐지 + 색상화)
- **총 실행 시간**: ~130초 (약 2분 10초) ⚡ (217초 → 130초, 40% 개선)

### 색상 시각화 ✨ NEW

Stage 1과 Stage 4의 이상치 및 변경사항이 **자동으로 색상화**됩니다:

**Stage 1 색상**:
- 🟠 주황: 날짜 변경 셀
- 🟡 노랑: 신규 레코드 전체 행

**Stage 4 색상**:
- 🔴 빨강: 시간 역전 (날짜 컬럼만)
- 🟠 주황: ML 이상치 (치명적/높음)
- 🟡 노랑: ML 이상치 (보통/낮음) + 과도 체류
- 🟣 보라: 데이터 품질

**⚠️ 중요**: Stage 4 색상화를 활성화하려면 `--stage4-visualize` 플래그가 **필수**입니다!

**플래그 없이 실행하면 색상이 적용되지 않습니다.**

```bash
# 권장: 배치 스크립트 사용 (플래그 자동 포함)
.\run_full_pipeline.bat

# 수동 실행 시 플래그 필수
python run_pipeline.py --all --stage4-visualize
```

자세한 내용: [색상 작업 완료 보고서](docs/reports/COLOR_FIX_SUMMARY.md)

## 📊 실행 결과 (v4.0 Balanced Boost)

### 이상치 탐지 성능
- **ML 이상치**: 115건 (기존 3,724건에서 97% 감소)
- **위험도 범위**: 0.981~0.999 (포화 문제 완전 해결)
- **위험도 1.000**: 0건 (100% 해결)

### 이상치 유형별 분포
- 데이터 품질: 1건
- 시간 역전: 790건 (치명적)
- 과도 체류: 258건
- ML 이상치: 115건

### 실행 시간 (5,834행 기준)
- Stage 1: ~29초
- Stage 2: ~7초
- Stage 3: ~43초
- Stage 4: ~4초
- **총 실행 시간**: ~83초

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
│   │   ├── CASE LIST.xlsx
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

### Stage 4: 이상치 탐지 (Balanced Boost Edition v4.0)
- **ECDF 캘리브레이션**: 위험도를 0.001~0.999 범위로 정규화
- **Balanced Boost**: 룰/통계/ML 혼합 위험도 시스템
  - 시간 역전 감지: +0.25 가산
  - 통계 이상(높음/치명): +0.15 가산
  - 통계 이상(보통): +0.08 가산
- **위치별 임계치**: MOSB/DSV 등 지점별 IQR+MAD 과도 체류 판정
- **PyOD 앙상블 ML**: IsolationForest 기반 이상치 탐지 (sklearn 자동 폴백)
- **실시간 시각화**: 색상 기반 이상치 표시
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

## 🔧 Stage 4 튜닝 가이드

### Contamination 조정
```bash
# Stage 4만 실행 (contamination 조정)
python run_pipeline.py --stage 4 --contamination 0.01  # 보수적
python run_pipeline.py --stage 4 --contamination 0.02  # 권장 (기본값)
python run_pipeline.py --stage 4 --contamination 0.05  # 공격적
```

### 가산치 조정
`scripts/stage4_anomaly/anomaly_detector_balanced.py` 수정:
```python
class DetectorConfig:
    rule_boost: float = 0.25      # 시간역전 가산
    stat_boost_high: float = 0.15 # 통계 높음/치명 가산
    stat_boost_med: float = 0.08  # 통계 보통 가산
```

## 🏢 지원 창고 및 사이트

### 창고 (9개)
- DHL WH, DSV Indoor, DSV Al Markaz
- Hauler Indoor, DSV Outdoor, DSV MZP
- JDN MZD, MOSB, AAA Storage

**참고**: HAULER는 Hauler Indoor와 동일한 창고로 통합됨 (v4.0.38)

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
- [Stage 3: 종합 보고서 생성](docs/STAGE3_USER_GUIDE.md) - 5개 시트 KPI 분석 보고서 (벡터화 최적화)
- [Stage 4: 이상치 탐지](docs/STAGE4_USER_GUIDE.md) - 5가지 이상치 유형 자동 탐지

### 🚀 성능 최적화 가이드
- [프로덕션 권장사항](docs/reports/PRODUCTION-RECOMMENDATION.md) - Stage 3 벡터화 버전 사용 권장
- [벡터화 최적화 보고서](docs/reports/stage3-performance-optimization-completed.md) - 82% 성능 개선 상세
- [병렬 처리 테스트](docs/reports/stage3-parallel-optimization-final-report.md) - 병렬 처리 성능 분석

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

## 📚 추가 문서

- [Core Module 통합 보고서](docs/reports/CORE_MODULE_INTEGRATION_REPORT.md) - Semantic matching 시스템 상세
- [최종 통합 요약](docs/reports/FINAL_INTEGRATION_SUMMARY.md) - v4.0.1 변경 사항
- [Core Module 가이드](scripts/core/README.md) - 사용법 및 예제
- [통합 가이드](scripts/core/INTEGRATION_GUIDE.md) - 개발자 가이드

---

**버전**: v4.0.38 (HAULER 중복 제거 패치)
**최종 업데이트**: 2025-10-27
**문의**: AI Development Team
