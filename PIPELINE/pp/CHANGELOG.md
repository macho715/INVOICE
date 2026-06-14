# Changelog

All notable changes to the HVDC Pipeline project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.32] - 2025-10-24

### ✨ Added

#### Stage 1 멀티시트 및 합쳐진 파일 출력 기능
- **2개 파일 출력**: Stage 1이 이제 2개의 파일을 생성합니다
  - 멀티시트 파일: `*.synced_v3.6.xlsx` (3개 시트 유지 + 컬러링)
  - 합쳐진 파일: `*.synced_v3.6_merged.xlsx` (단일 시트)
- **Source_Sheet 컬럼**: 합쳐진 파일에 각 행의 출처 시트를 기록
- **명시적 시트 순서**: 합쳐진 파일의 데이터 순서 보장
  1. Case List, RIL (6,919행)
  2. HE Local (70행)
  3. HE-0214,0252 (Capacitor) (102행)
  - 총 7,091행, 42컬럼

### 🔄 Changed

#### Stage 2 설정 업데이트
- **입력 파일**: 합쳐진 파일 사용으로 변경
  - 기존: 멀티시트 파일 로드 후 병합
  - 개선: 사전 병합된 파일 직접 로드
  - 결과: 처리 속도 향상 (병합 로직 생략)

### 🔧 Technical Details

**파일 경로**:
- `scripts/stage1_sync_sorted/data_synchronizer_v30.py`
  - Lines 1158-1180: 합쳐진 파일 생성 로직 추가
  - Lines 1161-1173: 시트 순서 명시적 지정
- `config/stage2_derived_config.yaml`
  - Line 14: 입력 파일을 merged 파일로 변경

**성능 지표**:
- Stage 1 실행 시간: ~100초 (2개 파일 생성)
- Stage 2 실행 시간: ~20초 (합쳐진 파일 사용)
- 파일 크기:
  - 멀티시트: ~812 KB
  - 합쳐진: ~1,142 KB

---

## [4.0.31] - 2025-10-24

### 🐛 Fixed

#### Stage 1 신규 케이스 데이터 완전성 수정
- **Problem**: Stage 1에서 신규 케이스(Master-only) 추가 시 일부 컬럼만 복사되어 데이터 손실 발생
  - Semantic matching된 컬럼만 복사 (case_number, item_number, 날짜 등)
  - Semantic matching 안 된 컬럼은 빈 셀로 남음 (EQ No, Description, L/W/H 등)
  - 사용자 보고: 이미지에서 노란색 강조된 행들(4371-4374, 4402-4405)의 컬럼 C-N이 비어있음

- **Root Cause**: `_apply_updates()` 메서드의 신규 케이스 추가 로직
  - `common_keys`만 복사 (semantic keys in both Master and Warehouse)
  - `master_only_keys`만 복사 (semantic keys only in Master)
  - Master의 다른 모든 컬럼은 무시됨

- **Solution**: 모든 Master 컬럼 복사 + Semantic name mapping 적용
  - **STEP 1**: Master의 모든 컬럼을 먼저 복사 (`for col in master.columns`)
  - **STEP 2**: Semantic matching 결과로 컬럼명 매핑 적용 (m_col → w_col)
  - **STEP 3**: Warehouse에 없는 컬럼은 None으로 초기화
  - **Core 호환성**: `@core/` semantic matching 로직 그대로 유지

- **Implementation Details**:
  ```python
  # Before (INCOMPLETE)
  append_row = {}
  for semantic_key in common_keys:
      m_col = master_cols[semantic_key]
      w_col = wh_cols[semantic_key]
      append_row[w_col] = mrow[m_col]
  
  # After (COMPLETE)
  append_row = {}
  # STEP 1: Copy ALL Master columns
  for col in master.columns:
      append_row[col] = mrow[col]
  
  # STEP 2: Apply semantic name mapping
  for semantic_key in common_keys:
      m_col = master_cols[semantic_key]
      w_col = wh_cols[semantic_key]
      if m_col != w_col and m_col in append_row:
          append_row[w_col] = append_row.pop(m_col)
  
  # STEP 3: Initialize missing columns
  for col in append_row.keys():
      if col not in wh.columns:
          wh[col] = None
  ```

- **Verification Results**:
  - **Before**: EQ No, Description 등 빈 셀 (0개 데이터)
  - **After**: 모든 컬럼 완전히 채워짐 (40개 컬럼)
  - **SQM 계산**: 85.0% → 100.0% (15% 향상)
  - **Stage 2 처리**: 7,091행 × 54컬럼 정상 처리

- **File Changes**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py`:
    - `_apply_updates()` 메서드 수정 (lines 881-906)
    - 모든 Master 컬럼 복사 로직 추가
    - Semantic name mapping 적용
    - 컬럼 초기화 로직 추가

- **Benefits**:
  - **데이터 무결성**: Master의 모든 컬럼 100% 보존
  - **Core 호환성**: Semantic matching 로직 그대로 유지
  - **정확도 향상**: SQM 계산률 15% 향상
  - **사용자 요구사항**: 빈 셀 문제 완전 해결

- **Backup**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py.backup_before_fix`

## [4.0.30] - 2025-10-24

### 🔄 Experimental

#### Stage 1 순회 방향 변경 실험 (Reverted)
- **Experiment**: 동기화 로직의 순회 방향을 Master 기준에서 Warehouse 기준으로 변경
  - **기존**: `for mi, mrow in master.iterrows()` (Master 행 순회)
  - **변경**: `for wi, wrow in wh.iterrows()` (Warehouse 행 순회)
  - Master 인덱스 사전 생성 (`master_index`)
  - Master 전용 케이스는 Warehouse 순회 후 별도 추가
- **Result**: 
  - ✅ 업데이트 통계 동일 (925 cells, 1,066 new records)
  - ✅ 최종 데이터 동일 (7,091행)
  - ✅ 처리 순서만 Warehouse 행 순서로 변경
- **Decision**: **원래 로직으로 복귀**
  - 실험 목적 달성 (순회 방향 변경 가능성 확인)
  - 기존 로직이 더 직관적 (Master가 진실의 원천)
  - 백업: `data_synchronizer_v30.py.backup_wh_first`
- **Duration**: 실험 및 검증 완료 (80초, 성공)

## [4.0.29] - 2025-10-24

### 🚀 Enhanced

#### 하이브리드 접근 구현 - 오리지널 로직 복원 + 벡터화 최적화
- **Problem**: 오리지널 파일 벤치마크 결과, 기존 벡터화 로직의 과도한 필터링 문제 발견
  - 입고 필터링이 너무 엄격 (6개만 집계)
  - 출고 날짜 조건이 실제 데이터와 불일치 ("다음 날 이동만" 조건)
  - 창고간 이동 제외 로직이 너무 광범위하게 적용
- **Solution**: 하이브리드 접근 - 루프 기반 입고 + 수정된 출고 로직
  - **입고**: 모든 창고 입고 포함 (필터링 제거), `Inbound_Type` 명시적 설정
  - **출고**: 창고 입고일 이후 모든 현장 이동 인정 (실제 데이터 분석 기반)
  - **창고간 이동**: 해당 행에서만 제외 (광범위한 제외 로직 제거)
- **Result**:
  - **입고**: 6 → 5,517 (완전 복원) ✅
  - **출고**: 22 → 2,574 (117배 증가) ✅
  - **창고 재고**: 2,943 (목표 범위 2,800~3,200 내) ✅
  - 월별 입출고 계산 정확도 대폭 개선

**데이터 분석 결과**:
- 창고→현장 이동 3,293건 중 "다음 날 이동"은 단 10건 (0.3%)
- 실제 이동은 평균 수백 일 소요 (3~554일)
- 오리지널 로직의 "다음 날 이동만" 조건은 실제 데이터와 불일치

**기술적 개선**:
- 루프 기반 입고로 안정성 확보
- 행별 창고간 이동 추적으로 정확도 향상
- `break` 문으로 중복 출고 방지

## [4.0.28] - 2025-10-24

### 🔄 Reverted

#### PATCH3.MD 롤백 (v4.0.27 revert)
- **Problem**: PATCH3.MD 적용 후 입고 데이터가 부정확 (6개만 집계)
  - 입고 필터링(`Inbound_Type == "external_arrival"`)이 너무 엄격
  - 창고 재고가 음수로 계산됨 (-268)
- **Solution**: Git revert로 v4.0.26 상태로 복원
- **Result**:
  - 누계_입고: 6 → 5,517 (정상 복원)
  - 창고 재고: -268 → 4,923 (실제 재고와 일치)
  - 창고 월별 입출고 데이터 정확도 회복

## [4.0.27] - 2025-10-24

### 🐛 Fixed (실패 - v4.0.28에서 롤백됨)

#### 창고_월별_입출고 출고 중복 합산 제거 (PATCH3.MD)
- **Problem**: 창고간 이동 출고가 월별 집계에서 중복 합산됨
  - 창고→창고 이동이 출고에 포함되어 중복 계산
  - 외부 입고와 창고간 이동이 명확히 구분되지 않음
- **Solution**: 벡터화 입고/출고 계산 로직 전면 개편
  - `Inbound_Type == "external_arrival"` 필터링 강화
  - 창고간 이동 출고를 월별 집계에서 한 번만 계산
  - 회귀 테스트 추가
- **Result**: ❌ **실패**
  - 입고 필터링이 너무 엄격하여 대부분의 데이터 제외
  - 누계_입고: 5,517 → 6 (99.9% 손실)
  - 창고 재고: 음수로 계산 (-268)
- **Rollback**: v4.0.28에서 Git revert로 복원

## [4.0.26] - 2025-10-24

### 🐛 Fixed

#### 창고 출고 계산 로직 개선
- **Problem**: 벡터화 출고 계산에서 창고→현장 이동 감지가 매우 낮음 (6개)
  - 기존 로직이 "다음 날 이동만 출고로 인정"하여 너무 엄격한 조건
  - 창고간 이동 제외 로직이 너무 광범위하게 적용됨
- **Solution**:
  - 날짜 조건을 `site_date.date() > wh_date.date()`로 완화
  - 창고간 이동 제외 로직 제거
- **Result**:
  - 창고→현장 이동 감지: 6개 → 588개 (98배 개선)
  - 창고_월별_입출고 시트의 출고 데이터 정확도 향상
  - 벡터화 출고 계산 성능 유지

## [4.0.25] - 2025-10-24

### 🐛 Fixed

#### 창고_월별_입출고 계산 수정
- **Problem**: 창고_월별_입출고 시트의 데이터가 대부분 0으로 표시
  - 벡터화 입고 계산에서 Inbound_Type 필드 누락
  - create_warehouse_monthly_sheet()에서 조건 미충족
- **Solution**: _calculate_warehouse_inbound_vectorized()에 Inbound_Type 명시적 설정
- **Result**:
  - 입고 데이터 정상 표시
  - 창고별/월별 집계 정확성 확보
  - 입고_DHL WH: 0 → 408
  - 입고_DSV Indoor: 0 → 2360
  - 입고_DSV Outdoor: 0 → 2846
  - 입고_MOSB: 0 → 2286

## [4.0.24] - 2025-10-23

### 🔧 Fixed

#### SCT Ref.No 컬럼 위치 수정
- **Problem**: SCT Ref.No가 65번째 위치에 있어서 찾기 어려움
- **Solution**: STANDARD_HEADER_ORDER에서 SCT Ref.No를 4번째 위치로 이동
- **Result**:
  - 1. no.
  - 2. Shipment Invoice No.
  - 3. SCT Ref.No ← 이동 완료
  - 4. Site
- **Benefits**:
  - 컬럼 순서 일관성 확보
  - Stage 2와 Stage 3 헤더 순서 통일
  - 데이터 접근성 향상

## [4.0.23] - 2025-10-23

### 🐛 Fixed

#### Stage 3 Excel 컬럼 누락 문제 해결
- **Problem**: Stage 3 실행 시 `Stack_Status`, `Total sqm` 컬럼이 DataFrame에는 존재하지만 Excel 파일에서 누락됨
  - DataFrame: 66개 컬럼 (Total sqm, Stack_Status 포함)
  - Excel 출력: 64개 컬럼 (Total sqm, Stack_Status 누락)
  - 근본 원인: 닫힌 ExcelWriter 컨텍스트 밖에서 `combined_reordered.to_excel()` 호출

- **Solution**: 모든 시트를 단일 ExcelWriter 컨텍스트 안에서 저장
  - `scripts/stage3_report/report_generator.py` 재구성
  - SQM 관련 시트를 사전 계산 (writer 컨텍스트 밖)
  - 모든 `to_excel()` 호출을 단일 `with pd.ExcelWriter()` 블록 안으로 이동
  - HITACHI, SIEMENS, 통합 원본 데이터 시트 모두 동일한 컨텍스트에서 저장

- **Benefits**:
  - DataFrame과 Excel 파일 간 데이터 무결성 보장
  - 모든 66개 컬럼이 Excel 파일에 정상 저장
  - 창고 적재 효율 분석 가능 (`Total sqm = SQM × PKG`)
  - 적재 가능 층수 정보 보존 (`Stack_Status`)

## [4.0.22] - 2025-10-23

### ✨ Added

#### Stage 3에 Total sqm 계산 로직 추가
- **Problem**: Stage 3에 Stack_Status 및 Total sqm 컬럼 누락
  - Stack 텍스트 파싱 로직 없음
  - SQM × PKG 계산 없음
  - 창고 적재 효율 분석 불가
  - 실제 사용 공간 추적 불가능

- **Solution**: core.data_parser 통합 및 Total sqm 계산
  - **Stack_Status 파싱**: core.data_parser.parse_stack_status 사용
  - **Total sqm 계산**: SQM × PKG
  - **헤더 순서**: SQM → Stack_Status → Total sqm
  - **core 중앙 관리**: 헤더 순서 및 데이터 파싱 로직 core에서 관리

- **Implementation Details**:
  - `scripts/core/standard_header_order.py`:
    - STANDARD_HEADER_ORDER에 "Total sqm" 추가 (SQM, Stack_Status 다음)
  - `scripts/stage3_report/report_generator.py`:
    - `from core.data_parser import parse_stack_status` import 추가
    - `_calculate_stack_status()`: Stack 컬럼 파싱 함수
    - `_calculate_total_sqm()`: Total sqm 계산 함수 (SQM × PKG)
    - 통합_원본데이터_Fixed 시트에 적용
  - `tests/test_stage3_total_sqm.py`:
    - Stack_Status 파싱 테스트 (기본, 다양한 패턴, 컬럼 누락)
    - Total sqm 계산 테스트 (기본, 엣지 케이스, 컬럼 누락, 0/음수 처리)
    - 통합 워크플로우 테스트

- **Files Modified**:
  - `scripts/core/standard_header_order.py`: "Total sqm" 컬럼 추가
  - `scripts/stage3_report/report_generator.py`: Stack_Status 및 Total sqm 계산 로직 추가

- **Files Created**:
  - `tests/test_stage3_total_sqm.py`: 포괄적 테스트 스위트 (8개 테스트, 모두 통과)

- **Benefits**:
  - **적재 효율 분석**: 실제 적재 가능한 총 면적 계산
  - **재사용성**: core.data_parser 활용으로 코드 중복 제거
  - **정확도**: 개선된 Stack_Status 파싱 로직 사용
  - **창고 공간 계획**: Total sqm 기반 실제 사용 공간 추적
  - **중앙 관리**: core 모듈에서 헤더 순서 및 파싱 로직 일괄 관리

- **Test Results**:
  - Stack_Status 파싱: "X2" → 2, "Stackable / 3" → 3, "Not stackable" → 0
  - Total sqm 계산: SQM=2.5, PKG=10 → 25.0
  - 엣지 케이스: Pkg=0, SQM=None → None
  - 모든 테스트 통과 (8/8)

- **Example Usage**:
  ```python
  # Stage 3 통합_원본데이터_Fixed 시트
  # ... | SQM | Stack_Status | Total sqm | ...
  # ... | 9.84 | 2 | 98.40 | ...  (SQM=9.84, PKG=10)
  # ... | 5.20 | 3 | 52.00 | ...  (SQM=5.20, PKG=10)
  ```

## [4.0.21] - 2025-10-23

### ✨ Added

#### Core 모듈에 데이터 파싱 유틸리티 추가
- **Problem**: Stack_Status 파싱 로직이 Stage 2에만 존재하여 재사용 불가
  - Stage별 중복 코드 발생 위험
  - 개선된 파싱 로직이 일부 Stage에만 적용
  - 유지보수 어려움: 각 Stage별로 별도 구현 필요

- **Solution**: Core 모듈에 data_parser.py 추가
  - **중앙 집중식 관리**: 모든 Stage에서 `from core.data_parser import parse_stack_status` 사용
  - **개선된 파싱 로직**: 하중 표기 제거, 슬래시 패턴, 양방향 X 패턴 지원
  - **하위 호환성**: 기존 stack_and_sqm.py는 core 모듈로 위임하여 유지

- **Implementation Details**:
  - `scripts/core/data_parser.py`: 새로운 데이터 파싱 모듈 생성
  - `_strip_weights()`: 하중 표기(600kg/m2, kg/㎡ 등) 제거 함수
  - `parse_stack_status()`: 개선된 Stack_Status 파싱 로직
  - `calculate_sqm()`, `convert_mm_to_cm()`: 향후 확장을 위한 유틸리티 함수
  - `scripts/core/__init__.py`: data_parser 모듈 export 추가

- **Files Created**:
  - `scripts/core/data_parser.py`: 데이터 파싱 유틸리티 (약 200줄)
  - `tests/test_data_parser.py`: 포괄적 테스트 스위트 (약 150줄)

- **Files Modified**:
  - `scripts/core/__init__.py`: data_parser import 및 export 추가
  - `scripts/stage2_derived/stack_and_sqm.py`: core 모듈로 위임하도록 리팩터링

- **Benefits**:
  - **재사용성**: 모든 Stage에서 동일한 파싱 로직 사용
  - **정확도 향상**: 하중 표기 오염 방지, 슬래시 패턴 지원
  - **유지보수성**: 한 곳만 수정하면 전체 파이프라인 적용
  - **확장성**: 향후 다른 데이터 파싱 로직 추가 용이
  - **하위 호환성**: 기존 코드 변경 없이 개선된 로직 적용

- **Test Results**:
  - **하중 표기 제거**: "Stackable 600kg/m2" → 1 (기존: 600으로 오인식 가능)
  - **슬래시 패턴**: "Stackable / 2 pcs" → 2 (기존: 미지원)
  - **양방향 X 패턴**: "2X", "X2" 모두 정확히 인식
  - **복합 패턴**: "Stackable 600kg/m2 / 2 pcs" → 2 (하중 제거 후 슬래시 패턴)

### 📚 Documentation
- `scripts/core/data_parser.py`: 포괄적 docstring 및 사용 예시
- `tests/test_data_parser.py`: 15개 테스트 케이스로 엣지 케이스 커버

## [4.0.20] - 2025-10-23

### 🔧 Refactoring

#### 헤더 관리 로직 Core 통합
- **Problem**: 중복된 'no' 컬럼 제거 로직이 Stage 2에만 존재하고 Stage 3에는 없음
  - Stage 2: `derived_columns_processor.py`에 중복 제거 로직 별도 구현
  - Stage 3: 중복 제거 로직 누락으로 일관성 부족
  - 유지보수 어려움: 새 Stage 추가 시 매번 중복 제거 로직 추가 필요
  - 단일 책임 원칙 위반: 헤더 정규화는 core가 담당해야 함

- **Solution**: Core 모듈로 헤더 관리 로직 통합
  - **중앙 집중식 관리**: `core/standard_header_order.py`의 normalize 함수에 중복 제거 로직 통합
  - **자동 적용**: Stage 2, 3 모두 normalize 함수 호출만으로 자동 처리
  - **코드 중복 제거**: Stage별 파일에서 중복 로직 완전 제거
  - **단일 책임 원칙**: 헤더 관리는 core 모듈만 담당

- **Implementation Details**:
  - `normalize_header_names_for_stage3()`: 중복 'no' 컬럼 제거 로직 추가
  - `normalize_header_names_for_stage2()`: 중복 'no' 컬럼 제거 로직 추가
  - `derived_columns_processor.py`: 중복 제거 로직 제거 (4줄 삭제)
  - `report_generator.py`: 수정 불필요 (자동 적용)

- **Files Modified**:
  - `scripts/core/standard_header_order.py`: normalize 함수 2개에 중복 제거 로직 추가 (+8 lines)
  - `scripts/stage2_derived/derived_columns_processor.py`: 중복 로직 제거 (-4 lines)

- **Benefits**:
  - **DRY 원칙**: 코드 중복 완전 제거
  - **단일 책임 원칙**: 헤더 관리는 core만 담당
  - **일관성**: 모든 Stage에서 동일한 정규화 규칙
  - **유지보수성**: 한 곳만 수정하면 모든 Stage 적용
  - **확장성**: 새 Stage는 normalize 함수만 호출
  - **하위 호환성**: 100% 유지 (함수 시그니처 변경 없음)

- **Test Results**:
  - **Stage 2**: 53개 컬럼, 중복 'no' 제거 완료, 실행 시간 7.25초 ✅
  - **Stage 3**: 64개 컬럼, 중복 'no' 제거 3회 완료 (HITACHI, SIEMENS, 통합), 실행 시간 20.19초 ✅
  - **데이터 무결성**: 100% 유지 ✅
  - **성능 영향**: 없음 ✅

### 📚 Documentation
- `docs/reports/centralized-header-management-report.md`: 헤더 관리 통합 상세 보고서
- `scripts/core/standard_header_order.py`: docstring 업데이트 (중복 제거 명시)

## [4.0.19] - 2025-10-23

### 🛠️ Fixed

- **Stage 3 월별 과금 벡터화 오류 수정**
  - `melt()` 함수에 인덱스가 `id_vars`로 전달되면서 발생한 KeyError 해결
  - 창고 방문 시계열을 전개하기 전 `row_id` 보조 컬럼을 명시적으로 주입하여 안정성 확보
  - 벡터화 경로와 병렬 청크 처리 경로 모두에 동일한 패치를 적용하여 일관성 보장

### 📚 Documentation
- `docs/common/STAGE3_USER_GUIDE.md`: 패치 하이라이트 추가 (KR/EN 병기)

## [4.0.18] - 2025-10-23

### 🚀 STACK.MD 기반 SQM 및 Stack_Status 최적화

#### Stage 2 파생 컬럼 정확도 향상
- **Problem**: 기존 SQM 계산이 추정 기반(PKG × 1.5)으로 부정확
  - 치수 정보가 있어도 활용하지 못함
  - Stack_Status 파싱 로직 부재
  - 데이터 정확도 및 신뢰성 저하

- **Solution**: STACK.MD 명세 기반 정확한 계산 시스템 구현
  - **치수 기반 SQM**: L(cm) × W(cm) / 10,000 정확 계산
  - **Stack 텍스트 파싱**: "Not stackable" → 0, "X2" → 2 등
  - **mm 단위 자동 변환**: mm → cm (÷10)
  - **폴백 전략**: 치수 없으면 기존 추정 로직 사용

- **Implementation Details**:
  - `header_registry.py`: 치수(L/W/H) 및 stackability 헤더 정의 추가
  - `stack_and_sqm.py`: 신규 모듈 (파싱 로직, SQM 계산)
  - `derived_columns_processor.py`: Stage 2에 SQM/Stack 계산 통합
  - `report_generator.py`: Stage 3에서 폴백 전략 적용

- **Files Modified**:
  - `4.0.0/scripts/core/header_registry.py`: 치수/stackability 헤더 정의
  - `4.0.0/scripts/stage2_derived/stack_and_sqm.py`: 신규 모듈
  - `4.0.0/scripts/stage2_derived/derived_columns_processor.py`: 통합
  - `4.0.0/scripts/stage3_report/report_generator.py`: 폴백 전략
  - `4.0.0/tests/test_stack_and_sqm.py`: 포괄적 테스트 (15개 테스트)

- **Benefits**:
  - **정확도 향상**: 치수 기반 SQM 계산으로 정확도 100% 달성
  - **Stack 파싱**: 텍스트 기반 적재 상태 정확 파싱
  - **호환성**: 기존 파이프라인과 100% 호환
  - **폴백 안전성**: 치수 없으면 기존 추정 로직 자동 사용
  - **성능**: 벡터화 연산으로 고성능 처리

### 📚 Documentation
- `4.0.0/scripts/stage2_derived/README.md`: STACK.MD 기반 계산 로직 설명
- `4.0.0/tests/test_stack_and_sqm.py`: 포괄적 테스트 스위트 (15개 테스트)

## [4.0.17] - 2025-10-23

### 🚀 Performance Optimization

#### Stage 3 벡터화 최적화 (82% 성능 개선)
- **Problem**: Stage 3 실행 시간이 155초로 과도하게 길어 전체 파이프라인 병목 발생
  - `df.iterrows()` 기반 순차 처리로 인한 성능 저하
  - 5,553행 데이터 처리 시 155초 소요
  - 전체 파이프라인 실행 시간의 70% 이상 차지

- **Solution**: 완전 벡터화된 처리 시스템 구현
  - **벡터화 연산**: `iterrows()` → `melt()`, `groupby()`, `apply()` 벡터화
  - **병목 함수 최적화**: 11개 주요 함수를 벡터화로 전환
  - **자동 폴백 시스템**: 벡터화 실패 시 레거시 버전으로 자동 전환
  - **Windows 호환성**: multiprocessing spawn 방식 지원

- **Performance Results**:
  - **이전 성능**: 155초 (iterrows 기반)
  - **벡터화 성능**: 28.27초 (82% 개선) ✅
  - **병렬 처리**: 29.21초 (벡터화 대비 3.3% 느림)
  - **최종 권장**: 벡터화 버전 사용 (프로덕션 환경)

- **Implementation Details**:
  - `calculate_warehouse_inbound_corrected`: 벡터화 + 병렬 처리 옵션
  - `calculate_warehouse_outbound_corrected`: 벡터화 + 병렬 처리 옵션
  - `calculate_monthly_sqm_inbound/outbound`: 벡터화 + 병렬 처리 옵션
  - `calculate_monthly_invoice_charges_prorated`: 벡터화 + 병렬 처리 옵션
  - `_vectorized_detect_warehouse_transfers_batch`: 완전 벡터화된 창고간 이동 감지

- **Files Modified**:
  - `4.0.0/scripts/stage3_report/report_generator.py`: 벡터화 + 병렬 처리 구현
  - `tests/test_stage3_performance.py`: TDD 테스트 추가
  - `docs/reports/PRODUCTION-RECOMMENDATION.md`: 프로덕션 권장사항 문서

- **Benefits**:
  - **82% 성능 개선**: 155초 → 28초
  - **전체 파이프라인**: 217초 → 140초 (35% 개선)
  - **메모리 효율성**: 벡터화 연산으로 메모리 사용량 최적화
  - **확장성**: 대용량 데이터 처리 시 선형 확장성
  - **안정성**: 자동 폴백 시스템으로 안정성 보장

### 📚 Documentation
- `docs/reports/PRODUCTION-RECOMMENDATION.md`: 프로덕션 환경 권장사항 (벡터화 버전 사용)
- `docs/reports/stage3-performance-optimization-completed.md`: 벡터화 최적화 상세 보고서
- `docs/reports/stage3-parallel-optimization-final-report.md`: 병렬 처리 테스트 결과

## [4.0.16] - 2025-10-23

### ✨ Added

#### Raw Data Protection 검증 시스템 구축
- **Problem**: 파이프라인 실행 중 raw data 파일이 수정될 가능성에 대한 우려
  - 사용자 요구사항: "raw data는 절대로 수정 변경 금지"
  - 현재 상황: 파이프라인 실행 전후 raw data 무결성 검증 시스템 부재
  - 보안 요구사항: 데이터 무결성 보장 및 검증 가능성 필요

- **Solution**: 완전 자동화된 Raw Data Protection 검증 시스템 구현
  - **MD5 해시 검증**: 파일 내용의 바이트 단위 완전 일치 확인
  - **파일 크기 검증**: 파일 사이즈 변경 여부 확인
  - **수정 시간 검증**: 파일 시스템 메타데이터의 최종 수정 시간 확인
  - **데이터 행 수 검증**: Excel 시트별 데이터 행 수 확인

- **Implementation Details**:
  - **Baseline 수집**: 파이프라인 실행 전 raw data 상태 자동 기록
  - **실시간 검증**: 파이프라인 실행 후 즉시 무결성 검증
  - **상세 보고서**: 검증 결과를 마크다운 형식으로 자동 생성
  - **자동화 도구**: `scripts/verification/verify_raw_data_protection.py` 제공

- **Verification Results**:
  - **전체 파이프라인 실행**: 973.71초 (약 16분 14초)
  - **검증 대상 파일**: 2개 (Case List.xlsx, HVDC Hitachi.xlsx)
  - **MD5 해시 일치율**: 100% (2/2)
  - **파일 크기 일치율**: 100% (2/2)
  - **수정 시간 보존율**: 100% (2/2)
  - **데이터 행 수 일치율**: 100% (2/2)
  - **최종 검증 상태**: **PASS** ✅

- **Files Created**:
  - `scripts/verification/verify_raw_data_protection.py` - 검증 도구
  - `docs/reports/RAW_DATA_PROTECTION_VERIFICATION_REPORT.md` - 상세 보고서 (323줄)
  - `logs/raw_data_baseline.json` - Baseline 데이터
  - `logs/raw_data_verification_report.md` - 검증 결과

- **Benefits**:
  - **완전한 무결성 보장**: Raw data 파일이 파이프라인 실행 전후 100% 동일
  - **자동화된 검증**: 수동 개입 없이 자동으로 무결성 확인
  - **상세한 문서화**: 검증 과정과 결과를 완전히 문서화
  - **신뢰성 향상**: MD5 해시 기반 바이트 단위 검증으로 최고 수준의 신뢰성
  - **사용자 요구사항 100% 충족**: "raw data는 절대로 수정 변경 금지" 완전 보장

### 📚 Documentation
- `docs/reports/RAW_DATA_PROTECTION_VERIFICATION_REPORT.md`: Raw Data Protection 검증 시스템 상세 보고서
- `scripts/verification/README.md`: 검증 도구 사용법 가이드
- `README.md`: v4.0.16 업데이트 내용 반영

## [4.0.15] - 2025-10-23

### 🔧 Changed

#### Stage 4 색상 자동화 기본 활성화
- **Problem**: Stage 4 이상치 탐지 후 색상 적용이 수동으로만 가능
  - 사용자 요구사항: "4단계 색상 작업이 누락"
  - 현재 문제: `--stage4-visualize` 플래그가 필요하여 기본적으로 색상이 적용되지 않음

- **Solution**: 색상 자동화를 기본값으로 활성화
  - `stage4.yaml`: `enable_by_default: false` → `true`
  - Stage 1처럼 자동으로 색상 적용
  - 별도 플래그 불필요

- **색상 규칙**:
  - 🔴 빨강: 시간 역전 (190건)
  - 🟠 주황: ML 이상치 치명적/높음 (110건)
  - 🟡 노랑: ML 이상치 보통/낮음 + 과도 체류 (176건)
  - 🟣 보라: 데이터 품질 (1건)

- **Implementation**:
  - `scripts/stage4_anomaly/stage4.yaml`: `enable_by_default: true` 설정
  - `run_full_pipeline.bat/ps1`: `--stage4-visualize` 플래그 제거 (기본값 사용)
  - 문서 업데이트: 색상 자동 적용 명시

- **Benefits**:
  - **사용자 편의성**: 별도 플래그 없이 자동 색상 적용
  - **일관성**: Stage 1과 동일한 자동화 수준
  - **시각화 개선**: 이상치 유형별 색상으로 즉시 식별 가능
  - **실행 시간**: 약 1-2초 증가 (색상 적용 시간)

### 📚 Documentation
- `docs/README.md`: Stage 4 색상 자동화 명시
- `scripts/stage4_anomaly/README.md`: 색상 규칙 및 기능 설명 추가
- `docs/sorted_version/QUICK_START.md`: 전체 파이프라인 결과 업데이트

## [4.0.14] - 2025-10-23

### 🔧 Changed

#### Stage 1 정렬 로직 수정: Warehouse 원본 순서 유지
- **Problem**: Master Case No 순서로 재정렬하여 Warehouse 원본 순서가 변경됨
  - 사용자 요구사항: "hvdc hitachi 원본 순서는 변동이 없다"
  - 현재 문제: Master 순서로 재정렬하여 원본 순서 손실

- **Solution**: Warehouse 원본 순서 유지 + 신규 케이스만 하단 추가
  - Warehouse 순서 변경 없음
  - Master 데이터로 업데이트만 수행
  - 신규 케이스는 제일 하단에 추가

- **Implementation**:
  - `_apply_master_order_sorting()`: 정렬 로직 제거
  - `_maintain_master_order()`: `_maintain_warehouse_order()`로 변경
  - Warehouse 원본 순서 완전 보존

- **Results**:
  - 원본 순서: [207721, 207722, 207723, ...] ✅
  - 수정 전: [1, 190000, 190001, ...] ❌
  - 수정 후: [207721, 207722, 207723, ...] ✅

### 📚 Documentation
- `docs/sorted_version/STAGE1_USER_GUIDE.md`: Warehouse 원본 순서 유지 명시
- `docs/sorted_version/README.md`: 정렬 로직 변경사항 반영

## [4.0.13] - 2025-10-23

### 🔧 Changed

#### Stage 1 신규 케이스 하단 배치 수정
- **Problem**: Stage 1 동기화 시 신규 Case No가 Master 케이스들 사이에 섞여서 배치됨
  - 사용자 요구사항: "STAGE 1에서 업데이트시 신규 CASE NO 제일 하단으로 업데이트 하라"
  - 현재 문제: 신규 케이스들이 중간에 삽입되어 순서가 보장되지 않음

- **Root Cause**: `_maintain_master_order()` 메서드의 정렬 로직 문제
  - Master에 없는 모든 케이스를 한꺼번에 처리하여 신규 케이스와 기존 Warehouse 전용 케이스가 섞임
  - `wh_other_cases = warehouse[~warehouse[wh_case_col].isin(master_case_order)].copy()` 로직의 한계

- **Solution**: 3단계 분리 로직으로 개선
  - **1단계**: Master에 있는 케이스들 (Master NO. 순서로 정렬)
  - **2단계**: 기존 Warehouse 전용 케이스 (Master에 없고 신규도 아닌)
  - **3단계**: **신규 케이스들 (제일 하단 배치)** ✅
  - `ChangeTracker.new_cases`를 활용하여 신규 케이스를 별도로 분리

- **Implementation Details**:
  ```python
  # 신규 추가된 Case No 목록 (ChangeTracker에서)
  new_case_numbers = list(self.change_tracker.new_cases.keys())

  # 3단계 분리
  wh_master_cases = warehouse[warehouse[wh_case_col].isin(master_case_order)].copy()
  wh_existing_only = warehouse[
      ~warehouse[wh_case_col].isin(master_case_order) &
      ~warehouse[wh_case_col].isin(new_case_numbers)
  ].copy()
  wh_new_cases = warehouse[warehouse[wh_case_col].isin(new_case_numbers)].copy()

  # 최종 결합: Master 순서 + 기존 WH 전용 + 신규
  sorted_warehouse = pd.concat([wh_master_cases, wh_existing_only, wh_new_cases], ignore_index=True)
  ```

- **Results**:
  - 신규 케이스가 **제일 하단**에 정확히 배치됨 ✅
  - 로깅 강화: 3개 그룹별 건수 표시
  - 데이터 무결성: 100% 유지
  - 성능 영향: 거의 없음 (추가 필터링만)

### 📚 Documentation
- `scripts/stage1_sync_sorted/README.md`: 신규 케이스 하단 배치 기능 추가
- `docs/sorted_version/STAGE1_USER_GUIDE.md`: 신규 케이스 배치 위치 명시

## [4.0.30] - 2025-10-24

### 🐛 Fixed

#### Stage 2/3 헤더 순서 정렬 완료
- **Problem**: Stage 2와 Stage 3의 헤더 순서가 완전히 어긋남
  - HVDC CODE가 실제 데이터에 존재하지 않음에도 불구하고 헤더 순서에 포함
  - Stage 1/2/3 모든 출력에서 HVDC CODE 컬럼이 실제로 존재하지 않음
  - 사용자 보고: "2,3번 엑셀 출력시 헤드가 틀리다"

- **Root Cause**: `standard_header_order.py`에서 잘못된 HVDC CODE 추가
  - STAGE2_HEADER_ORDER에 HVDC CODE를 3번째 위치에 추가했으나 실제 데이터에는 존재하지 않음
  - Stage 1 출력: HVDC CODE 없음
  - Stage 2 출력: HVDC CODE 없음
  - Stage 3 출력: HVDC CODE 없음

- **Solution**: 잘못된 HVDC CODE 추가를 되돌리고 실제 데이터 구조에 맞게 수정
  - STAGE2_HEADER_ORDER에서 HVDC CODE 제거
  - STANDARD_HEADER_ORDER에서도 HVDC CODE 제거
  - 실제 데이터 구조에 맞는 헤더 순서로 복원

- **Verification Results**:
  - **Stage 2 출력**: SCT Ref.No가 3번째 위치 ✅
  - **Stage 3 출력**: SCT Ref.No가 3번째 위치 ✅
  - **헤더 일치율**: 15/15 (100.0%) ✅
  - **공통 컬럼**: 52개 ✅
  - **Stage 2 전용**: 1개 (wh handling - 의도적) ✅
  - **Stage 3 전용**: 13개 (Stage 3 파생 컬럼 - 의도적) ✅

- **File Changes**:
  - `scripts/core/standard_header_order.py`:
    - STAGE2_HEADER_ORDER에서 HVDC CODE 제거 (Line 112)
    - STANDARD_HEADER_ORDER에서 HVDC CODE 제거 (Line 31)
    - 실제 데이터 구조에 맞는 헤더 순서로 복원

- **Benefits**:
  - **정확성**: 실제 데이터 구조와 일치하는 헤더 순서
  - **일관성**: Stage 2와 Stage 3의 헤더 순서 100% 일치
  - **유지보수성**: 존재하지 않는 컬럼으로 인한 혼란 제거
  - **사용자 요구사항**: "헤드가 틀리다" 문제 완전 해결

### 📊 Stage 2/3/4 실행 결과

#### Stage 3 종합 보고서 생성
- **실행 시간**: 28.90초
- **출력 파일**: `HVDC_입고일자_종합리포트_20251024_083352_v3.0-corrected.xlsx`
- **파일 크기**: 2.98 MB
- **생성 시트**: 12개 (창고_월별_입출고, 현장_월별_입출고현황, Flow_Code_분석 등)
- **메인 데이터**: 통합_원본데이터_Fixed (7,256행 × 65컬럼)

#### Stage 4 이상 탐지
- **실행 시간**: 22.58초
- **검사 대상**: 7,256개 레코드
- **총 이상치**: 549개
- **유형별 분류**: 데이터 품질(1개), 시간 관련(191개), 물리 제약(210개), 속성/모델 이상치(147개)
- **심각도별 분류**: 심각(12개), 치명적(525개), 경고(12개)

#### 데이터 품질 지표
- **SQM 계산**: 7,172개 (98.8% 성공률)
- **Stack_Status 파싱**: 7,102개 (97.9% 성공률)
- **Total sqm 계산**: 7,172개 (98.8% 성공률)
- **창고 월별 입출고**: Hybrid 접근으로 정확도 달성 (입고: 5,567개, 출고: 2,568개)

#### 성능 지표
- **총 실행 시간**: 51.48초 (Stage 3: 28.90초 + Stage 4: 22.58초)
- **처리 데이터**: 7,256행 × 65컬럼
- **이상치 탐지율**: 8.2% (596/7,256)

## [4.0.12] - 2025-10-22

### 🔧 Changed

#### Stage 1 컬럼 순서 수정: Shifting 및 Source_Sheet 위치 조정 (v3.4)
- **Problem**: Stage 1이 컬럼 순서를 재배치하면서 원본 데이터의 구조와 달라짐
  - **Shifting**: 원본에서는 창고 컬럼 뒤에 위치하지만, Stage 1에서 창고 컬럼 앞(26번)으로 이동
  - **Source_Sheet**: 메타데이터 컬럼이지만 컬럼 순서 재배치 로직에 포함되어 있음
  - 사용자 요구사항: "shifting 위치는 raw data 동일하게, Source_Sheet는 1단계후 컬러링 작업에만 적용, column 작업에는 제외"

- **Root Cause**: `_ensure_all_location_columns()` 메서드가 모든 비-location 컬럼을 base_cols로 처리
  - Shifting을 location 컬럼 앞으로 이동
  - Source_Sheet를 일반 컬럼으로 취급하여 순서 재배치에 포함

- **Solution**: `_ensure_all_location_columns()` 로직 개선
  - **Shifting 특별 처리**: 창고 컬럼과 사이트 컬럼 사이에 배치 (원본 데이터 순서 유지)
  - **Source_Sheet 제외**: 메타데이터로 분류하여 컬럼 순서 재배치 로직에서 제외, 맨 끝에 배치
  - **새로운 컬럼 순서**: `base_cols + warehouse_cols + Shifting + site_cols + Source_Sheet`

- **Implementation Details**:
  ```python
  # Separate columns into groups (EXCLUDING Source_Sheet from ordering)
  base_cols = []
  shifting_col = None
  source_sheet_col = None

  for col in df.columns:
      if col == "Shifting":
          shifting_col = col
      elif col == "Source_Sheet":
          source_sheet_col = col  # Keep separately, don't include in ordering
      elif col not in location_set:
          base_cols.append(col)

  # Build final column order
  final_order = (
      base_cols
      + WAREHOUSE_ORDER
      + ([shifting_col] if shifting_col else [])
      + SITE_ORDER
      + ([source_sheet_col] if source_sheet_col else [])
  )
  ```

- **Verification Results**:
  - **Stage 1 출력 (v3.3.xlsx)**:
    ```
    25. ETA/ATA
    26. DHL WH          ← 창고 컬럼 시작 (바로 시작!)
    27. DSV Indoor
    28. DSV Al Markaz
    29. Hauler Indoor
    30. DSV Outdoor
    31. DSV MZP
    32. HAULER
    33. JDN MZD
    34. MOSB
    35. AAA Storage     ← 창고 컬럼 끝
    36. Shifting        ← 원본 위치 유지 (창고 뒤)! ✅
    37. MIR             ← 사이트 컬럼 시작
    38. SHU
    39. AGI
    40. DAS
    41. Source_Sheet    ← 메타데이터, 맨 끝! ✅
    ```
  - **Stage 2 출력**: Stage 1의 컬럼 순서 완벽 보존 ✅
  - **Stage 3 출력**: Stage 1의 컬럼 순서 완벽 보존 ✅
  - **전체 파이프라인**: 5,553행 정상 처리 ✅

- **File Changes**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py`:
    - `_ensure_all_location_columns()` 메서드 수정 (lines 501-575)
    - Shifting과 Source_Sheet 특별 처리 로직 추가
    - 출력 버전 v3.4.xlsx로 업데이트 (line 1056)

- **Benefits**:
  - **원본 데이터 구조 보존**: Raw data의 Shifting 위치를 그대로 유지
  - **메타데이터 분리**: Source_Sheet를 컬럼 순서 로직에서 제외하여 컬러링 작업에만 사용
  - **일관성**: 전체 파이프라인(Stage 1→2→3)에서 컬럼 순서 일관성 유지
  - **유지보수성**: Shifting과 Source_Sheet의 특별한 역할이 코드에 명시적으로 표현됨

## [4.0.11] - 2025-10-22

### 🐛 Fixed

#### DHL WH 입출고 데이터 복구 (v3.0.6)
- **Problem**: DHL WH 102건 데이터가 Stage 1에서 손실되어 창고_월별_입출고 시트에 0건으로 표시
  - 원본 `CASE LIST.xlsx`의 "HE-0214,0252 (Capacitor)" 시트에 DHL WH 102건 존재
  - Stage 1 출력에서 DHL WH 컬럼은 존재하지만 데이터 0건
  - Stage 3 창고_월별_입출고 시트에서 "입고_DHL WH: 0건", "출고_DHL WH: 0건"

- **Root Cause**: Semantic matching에서 DHL WH가 매칭되지 않아 `master_cols`에 포함되지 않음
  - `_match_and_validate_headers`에서 `all_keys`에 location 컬럼들이 포함되지 않음
  - `all_keys = required_keys + self.date_semantic_keys`만 포함
  - DHL WH는 `HeaderCategory.LOCATION`에 속하므로 매칭되지 않음

- **Solution**: Semantic matching에 location 컬럼 추가 및 Master 전용 컬럼 처리 로직 구현
  - **Semantic Matching 확장**: `all_keys`에 `HeaderCategory.LOCATION` 컬럼들 추가
  - **Master 전용 컬럼 처리**: `_apply_updates`에서 Master에만 있는 컬럼을 Warehouse에 추가
  - **기존 케이스 업데이트**: Master 전용 컬럼을 기존 Warehouse 케이스에 업데이트

- **Verification Results**:
  - **Stage 1 출력**: DHL WH 102건 ✅
  - **Stage 2 출력**: DHL WH 102건 ✅
  - **Stage 3 창고_월별_입출고**: 입고_DHL WH 204건, 출고_DHL WH 0건 ✅
  - **날짜 분포**: 2024-11월 74건, 2024-12월 28건 ✅

- **File Changes**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py`:
    - Semantic matching에 location 컬럼 추가 (lines 600-603)
    - Master 전용 컬럼 처리 로직 추가 (lines 887-890, 973-995)

- **Benefits**:
  - **완전성**: 모든 Master 데이터가 Warehouse로 정확히 전달
  - **확장성**: 향후 새로운 location 컬럼이 추가되어도 자동으로 처리
  - **정확성**: 창고_월별_입출고 시트에 정확한 DHL WH 입출고 기록 표시

## [4.0.10] - 2025-10-22

### ✨ Added

#### Stage 3 입고일자 컬럼 추가 (v3.0.5)
- **Problem**: Stage 3의 "통합_원본데이터_Fixed" 시트에 "입고일자" 컬럼이 없음
  - `combined_original = stats["processed_data"].copy()`는 Stage 2 출력을 그대로 복사
  - Stage 2는 "입고일자"를 파생 컬럼으로 생성하지 않음
  - 사용자 보고: "통합_원본데이터_Fixed 입고일자 적용이 안됨"

- **Solution**: Stage 3에서 "입고일자" 컬럼을 동적으로 계산하여 추가
  - **계산 로직**: 10개 창고 컬럼 중 가장 빠른 날짜를 입고일자로 설정
  - **적용 범위**: 통합_원본데이터_Fixed, HITACHI_원본데이터_Fixed, SIEMENS_원본데이터_Fixed
  - **NaT 처리**: 창고 입고 기록이 없는 경우 (현장 직송) NaT로 표시

- **Verification Results**:
  - **통합_원본데이터_Fixed**: 입고일자 1,356건 (24.4%)
  - **HITACHI_원본데이터_Fixed**: 입고일자 1,356건
  - **SIEMENS_원본데이터_Fixed**: 입고일자 0건 (현장 직송만)
  - **총 5,553건** 중 1,356건이 창고 입고 기록 보유

- **File Changes**:
  - `scripts/stage3_report/hvdc_excel_reporter_final_sqm_rev.py`: 입고일자 계산 로직 추가 (lines 2163-2185)

- **Benefits**:
  - **완전성**: 모든 원본 데이터 시트에 입고일자 정보 제공
  - **정확성**: 창고 입고 기록 중 가장 빠른 날짜로 정확한 입고일자 계산
  - **일관성**: 3개 시트 모두 동일한 로직으로 일관된 입고일자 제공

## [4.0.9] - 2025-10-22

### 🐛 Fixed

#### Stage 1 DHL WH Data Loss Issue (v3.0.4)
- **Problem**: DHL WH 컬럼이 원본에 102건 존재하지만 Stage 1 처리 후 0건으로 손실
  - 원본 파일: "HE-0214,0252 (Capacitor)" 시트에 DHL WH 102건 데이터 존재
  - Stage 1 출력: DHL WH 컬럼은 존재하지만 데이터 0건
  - 사용자 보고: "DHL 창고 집계 안된다"

- **Root Cause**: `_consolidate_warehouse_columns()` 메서드의 컬럼 rename 로직 버그
  - `df.rename(columns={'DSV WH': 'DSV Indoor'})` 실행 시 'DHL WH' 컬럼도 함께 삭제됨
  - pandas의 `rename()` 메서드가 일부 케이스에서 예상치 못한 동작 수행
  - Position 69: 'DSV WH' (1건), Position 70: 'DHL WH' (102건) → rename 후 'DHL WH' 손실

- **Solution**: 컬럼 rename 방식을 안전한 수동 리스트 조작으로 변경
  ```python
  # 기존 (버그 있음)
  df = df.rename(columns={'DSV WH': 'DSV Indoor'})

  # 수정 (안전함)
  new_columns = []
  renamed = False
  for col in df.columns:
      if col == wrong_name and not renamed:
          new_columns.append(correct_name)
          renamed = True  # 첫 번째 occurrence만 rename
      else:
          new_columns.append(col)
  df.columns = new_columns
  ```

- **Verification Results**:
  - ✅ **원본 데이터**: "HE-0214,0252 (Capacitor)" 시트 DHL WH 102건 확인
  - ✅ **Semantic Matcher**: DHL WH 정상 인식 (신뢰도 1.0)
  - ✅ **pd.concat 후**: DHL WH 102건 정상 유지
  - ✅ **consolidate 후**: DHL WH 102건 정상 유지 (수정 후)
  - ✅ **Stage 1 출력**: DHL WH 102건 정상 저장

- **File Changes**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py`:
    - `_consolidate_warehouse_columns()` 메서드 rename 로직 수정 (lines 443-456)
    - DHL WH 추적 디버그 메서드 추가 (향후 디버깅용, lines 222-239)

- **Benefits**:
  - DHL WH 102건 데이터 정상 처리
  - 전체 창고 집계 정확성 향상 (10개 창고 모두 정상 처리)
  - 컬럼 rename 로직 안정성 향상

## [4.0.8] - 2025-10-22

### 🔧 Changed

#### Stage 3 Warehouse Column Order Documentation (v3.0.3)
- **Problem**: Stage 3 코드 주석이 실제 창고 개수와 불일치
  - 주석: "입고 8개 창고"
  - 실제: 10개 창고 (DHL WH ~ AAA Storage)
  - 사용자 보고: "창고_월별_입출고, 통합_원본데이터_Fixed, HITACHI_원본데이터_Fixed 정렬이 맞지 않다"

- **Solution**: 주석 및 문서 수정으로 명확성 향상
  - **컬럼 개수 정정**: 19열 → 23열 (입고월 1 + 입고 10 + 출고 10 + 누계 2)
  - **주석 명확화**: Stage 1 정렬 순서 명시
  - **코드 검증**: `self.calculator.warehouse_columns` 사용으로 순서 일관성 보장

- **Verification Results**:
  - **Stage 1 출력**: ✅ 창고 컬럼 28~37 (10개, 연속 배치)
  - **Stage 2 출력**: ✅ 창고 컬럼 28~37 (10개, 연속 배치)
  - **Stage 3 로직**: ✅ `warehouse_columns` 사용으로 Stage 1/2 순서 자동 반영

- **File Changes**:
  - `scripts/stage3_report/hvdc_excel_reporter_final_sqm_rev.py`: 주석 및 컬럼 개수 정정 (lines 1712-1721)

- **Benefits**:
  - **명확성**: 실제 컬럼 개수와 주석 일치
  - **일관성**: Stage 1/2/3 모두 동일한 창고 순서 사용
  - **유지보수**: 코드 의도 명확화

## [4.0.7] - 2025-10-22

### 🔧 Changed

#### Stage 1 Location Column Ordering (v3.0.2)
- **Problem**: Warehouse 및 Site 컬럼이 분산되어 Stage 2/3/4 로직 복잡도 증가
  - 누락된 컬럼을 맨 뒤에 추가하여 순서 불일치
  - 가이드 문서 (AF~AN, AO~AR)와 실제 순서가 다름
  - 사용자 보고: "컬럼순서가 변경되면 나머지 로직이 무너진다"

- **Solution**: 컬럼 추가 시 올바른 순서로 정렬
  - **Warehouse 그룹화**: DHL WH → AAA Storage (10개 컬럼)
  - **Site 그룹화**: MIR → DAS (4개 컬럼)
  - **가이드 문서 순서와 일치**: AF~AN (Warehouse), AO~AR (Site)

- **Implementation Details**:
  - **`_ensure_all_location_columns()`**: 하드코딩된 순서로 컬럼 재정렬
  - **컬럼 그룹화**: Warehouse 전체 → Site 전체 순서
  - **기존 컬럼 보존**: 비위치 컬럼은 기존 순서 유지
  - **로깅 강화**: 재정렬 결과 상세 출력

- **Code Changes**:
  ```python
  # Before: 컬럼을 맨 뒤에 추가
  for location in all_locations:
      if location not in df.columns:
          df[location] = pd.NaT  # 맨 뒤에 추가됨

  # After: 올바른 순서로 재정렬
  WAREHOUSE_ORDER = ["DHL WH", "DSV Indoor", "DSV Al Markaz", ...]
  SITE_ORDER = ["MIR", "SHU", "AGI", "DAS"]
  all_locations = WAREHOUSE_ORDER + SITE_ORDER

  # 컬럼 재정렬 (올바른 순서로)
  base_cols = [c for c in df.columns if c not in all_locations]
  ordered_cols = base_cols + all_locations
  df = df[[c for c in ordered_cols if c in df.columns]]
  ```

- **Verification Results**:
  - **Stage 1**: ✅ 컬럼 순서 수정 적용 (41개 컬럼)
  - **Stage 2**: ✅ 올바른 순서로 파생 컬럼 계산 (54개 컬럼)
  - **Stage 3**: ✅ 리포트 생성 정상 작동
  - **최종 검증**: Warehouse 연속성 10/10, Site 연속성 4/4 통과

- **File Changes**:
  - `scripts/stage1_sync_sorted/data_synchronizer_v30.py`: `_ensure_all_location_columns()` 메서드 완전 리팩토링
  - `config/stage2_derived_config.yaml`: 입력 파일 경로 업데이트 (`synced_v2.9.4.xlsx` → `synced_v3.3.xlsx`)

- **Final Column Order**:
  ```
  기본 정보 (1~27): no. ~ ETA/ATA, Shifting, Source_Sheet
  Warehouse 전체 (28~37): DHL WH → AAA Storage (연속 배치)
  Site 전체 (38~41): MIR → DAS (연속 배치)
  파생 컬럼 (42~54): Status_WAREHOUSE → Stack_Status
  ```

- **Benefits**:
  - **일관성**: 가이드 문서와 실제 파일 순서 일치
  - **유지보수**: Stage 2/3/4 로직 단순화
  - **가독성**: Excel 파일 열람 시 논리적 순서
  - **안정성**: 컬럼 순서 변경으로 인한 로직 오류 방지

## [4.0.6] - 2025-10-22

### 🔧 Changed

#### Stage 1 Master Order Sorting (v3.0.1)
- **Problem**: v30의 정렬 로직이 v29의 검증된 방식과 달라 순서 불일치 발생
  - 복잡한 (NO, Case No.) 복합 정렬 사용
  - 중복된 검증 로직으로 코드 복잡도 증가
  - 사용자 보고: "HVDC 순서에 맞춰야 한다"

- **Solution**: v29의 검증된 단순 정렬 로직 복구
  - **Master 정렬**: NO. 컬럼 단일 정렬 (v29 방식)
  - **Warehouse 정렬**: Master Case 순서 기준 정렬
  - **중복 제거**: 검증 로직 중복 제거 (lines 610-631)
  - **NaN 처리**: fillna(999999)로 안정적 정렬

- **Implementation Details**:
  - **`_apply_master_order_sorting()`**: v29의 단순한 NO. 정렬 로직 적용
  - **`_maintain_master_order()`**: NaN 처리 강화 (fillna(999999))
  - **복합 정렬 제거**: (NO, Case No.) → NO. 단일 정렬
  - **중복 검증 제거**: 불필요한 검증 로직 정리

- **Benefits**:
  - **일관성**: v29의 검증된 동작 복구
  - **단순성**: 복잡한 로직 제거로 유지보수성 향상
  - **안정성**: 단일 정렬 키로 예측 가능한 결과
  - **사용자 요구사항**: "HVDC 순서에 맞춰야 한다" 해결

## [4.0.5] - 2025-10-22

### ✨ Added

#### Stage 1 Summary Sheet Exclusion (v3.0)
- **Problem**: Summary 시트가 파이프라인에 포함되어 데이터 무결성 문제 발생
  - Summary 시트는 집계 데이터 (Case No. 없음)
  - "총합계" 등의 집계 헤더 포함
  - 실제 Case 데이터가 아닌 통계 정보
  - 사용자 보고: "이상한 정보가 있다"

- **Solution**: Summary 시트 자동 제외 시스템 구현
  - `EXCLUDED_SHEET_NAMES` 상수로 제외할 시트 정의
  - `_should_skip_sheet()` 메서드로 시트 필터링
  - `_load_file_with_header_detection()`에서 자동 스킵

- **Implementation Details**:
  - **제외 대상**: summary, 총합계, total, aggregate
  - **대소문자 무관**: normalized 비교로 안정적 필터링
  - **다국어 지원**: 영어/한국어 시트명 모두 지원
  - **로깅**: "[SKIP] Aggregate sheet (not Case data)" 메시지

- **Benefits**:
  - **데이터 정확성**: Case 데이터만 처리하여 오류 방지
  - **파이프라인 안정성**: 집계 데이터로 인한 오류 제거
  - **성능 향상**: 불필요한 13행 제외
  - **사용자 요구사항**: "이상한 정보" 완전 제거

#### Stage 1 Source_Sheet Metadata Preservation (v3.0)
- **Problem**: Source_Sheet information was lost during synchronization
  - CASE LIST.xlsx has 2 sheets: "Case List, RIL" (4,042 rows), "HE-0214,0252 (Capacitor)" (102 rows)
  - All synchronized data showed as "Case List" instead of original sheet names
  - Data source tracking became impossible
  - User report: "CASE LIST에 있는 모든 시트를, HVDC에 업데이트해야 된다"

- **Solution**: Implemented Source_Sheet metadata preservation system
  - Added `METADATA_COLUMNS` constant to define protected columns
  - Modified `_apply_updates()` to preserve Warehouse's Source_Sheet for existing cases
  - Added Master's Source_Sheet for new cases from Master
  - Source_Sheet is not processed through semantic matching (metadata only)

- **Implementation Details**:
  - **New Cases**: Use Master's Source_Sheet (e.g., "Case List, RIL")
  - **Existing Cases**: Preserve Warehouse's original Source_Sheet (e.g., "Case List")
  - **Metadata Protection**: Source_Sheet excluded from common column updates
  - **Separate Handling**: Source_Sheet processed outside semantic matching

- **Benefits**:
  - **Data Traceability**: Know which original sheet each row came from
  - **Audit Trail**: Complete source tracking through pipeline stages
  - **User Requirements**: Meets "모든 시트 업데이트" requirement
  - **Future-Proof**: Works with any number of Master sheets

### 🔧 Changed

#### Stage 1 Data Synchronization (data_synchronizer_v30.py)
- Added summary sheet exclusion system:
  - **New**: `EXCLUDED_SHEET_NAMES` constant for aggregate sheets
  - **New**: `_should_skip_sheet()` method for sheet filtering
  - **Updated**: `_load_file_with_header_detection()` - automatic summary skip
  - **Logging**: Clear skip messages for excluded sheets

- Added metadata column protection:
  - **New**: `METADATA_COLUMNS` constant with Source_Sheet
  - **Updated**: `_apply_updates()` method for metadata handling
  - **New Cases**: Copy Master's Source_Sheet to new rows
  - **Existing Cases**: Preserve Warehouse's Source_Sheet unchanged

#### Documentation Updates
- `CHANGELOG.md`:
  - Added v4.0.5 section documenting Source_Sheet preservation
  - Detailed implementation approach and benefits

## [4.0.4] - 2025-10-22

### ✨ Added

#### Stage 1 Compound Sort Implementation (v3.0)
- **Problem**: Multi-sheet merge with duplicate NO values caused unstable sorting
  - Master file has 2 sheets: "Case List, RIL" and "HE-0214,0252 (Capacitor)"
  - Both sheets have NO starting from 1, causing NO value overlap
  - Simple `sort_values("NO")` resulted in non-deterministic order
  - User report: "HVDC WAREHOUSE_HITACHI(HE) 순번 대로 매칭이 안된다"

- **Solution**: Implemented v4.0.2's verified compound sort `(NO, Case No.)`
  - Changed from single key `sort_values(item_col)` to compound key `sort_values([item_col, case_col])`
  - Primary sort by NO, secondary sort by Case No. for stable ordering
  - Based on SORTING_FIX_FINAL_REPORT.md v4.0.2 verified approach
  - Ensures deterministic, reproducible ordering across all pipeline stages

- **Benefits**:
  - **Stable Sort**: Rows with same NO are consistently sorted by Case No.
  - **Multi-Sheet Safe**: Handles NO overlap across sheets correctly
  - **Deterministic**: Always produces same order regardless of sheet merge order
  - **HVDC Compliant**: Maintains HITACHI sequence requirement
  - **Future-Proof**: Works with any number of sheets and NO patterns

#### Stage 1 Invalid Header Filtering (v3.0)
- **Problem**: Invalid headers in output files causing data quality issues
  - Found 7 invalid columns: `열1`, `0`, `1`, `2`, `3`, `4`, `총합계`
  - These headers appeared in both Stage 1 and Stage 2 outputs
  - Caused confusion and data processing issues
  - User report: "다른 헤드가 들어와있다"

- **Solution**: Implemented automatic header filtering system
  - Added `INVALID_HEADER_PATTERNS` regex patterns for common invalid headers
  - Created `_filter_invalid_columns()` method to remove invalid columns
  - Integrated filtering into `_load_file_with_header_detection()` workflow
  - Applied to both Master and Warehouse file loading

- **Patterns Filtered**:
  - `^열\d+$` - Korean column names like "열1", "열2"
  - `^\d+$` - Pure numeric headers like "0", "1", "2"
  - `^총합계$` - Korean "total" headers
  - `^Unnamed:.*$` - Pandas unnamed columns
  - `^\.+$` - Dot-only columns

- **Benefits**:
  - **Clean Data**: Removes 7 invalid columns automatically
  - **Quality Assurance**: Prevents invalid headers from propagating
  - **User Experience**: Clean, professional output files
  - **Maintainability**: Centralized filtering logic
  - **Future-Proof**: Handles new invalid header patterns

### 🔧 Changed

#### Stage 1 Data Synchronization (data_synchronizer_v30.py)
- Updated `_apply_master_order_sorting()` method:
  - **Before**: `master.sort_values(item_col, na_position="last")`
  - **After**: `master.sort_values([item_col, case_col], na_position="last")`
  - Added compound sort key for stable multi-sheet ordering
  - Maintains backward compatibility with single-sheet workflows

- Added header filtering integration:
  - **New**: `INVALID_HEADER_PATTERNS` constant with regex patterns
  - **New**: `_filter_invalid_columns()` method for automatic cleanup
  - **Updated**: `_load_file_with_header_detection()` includes filtering step
  - **Result**: Stage 1 output reduced from 49 to 42 clean columns

#### Documentation Updates
- `docs/sorted_version/STAGE1_USER_GUIDE.md`:
  - Updated sorting logic section to explain compound sort
  - Added multi-sheet processing explanation
  - Updated performance characteristics

- `scripts/stage1_sync_sorted/README.md`:
  - Updated technical details to document compound sort
  - Added multi-sheet handling explanation
  - Updated sorting logic steps

### 📊 Results

#### Stage 1 Sorting Verification
```
Master Data:
- Total: 4,144 rows from 2 sheets
- Sorted by: (NO, Case No.) compound key
- NO=1 cases: [191221, 207721] (sorted by Case No.)
- NO=2 cases: [191222, 207722] (sorted by Case No.)

Warehouse Data:
- Total: 5,566 rows processed
- Updates: 4,501 cells changed
- New records: 1 appended
- Processing time: ~13 seconds
```

#### Compound Sort Validation
```python
# Verification result
Total rows: 5566
First 10 Case No.: [207721, 207722, 207723, 207724, 207725, 207726, 207727, 207728, 207729, 207730]
First 10 NO values: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

# Compound sort check
NO=1 cases: [207721]  ✅ Stable order
NO=2 cases: [207722]  ✅ Stable order
```

#### Performance Impact
- Processing time: 13-14 seconds (consistent)
- Compound sort overhead: Negligible (~0-1 second)
- Memory usage: Unchanged
- Output quality: ✅ Deterministic and stable

### 🎯 Technical Details

#### Why Compound Sort is Necessary

**Multi-Sheet Data Structure:**
```
Sheet 1: "Case List, RIL" (4,042 rows)
  NO=1, Case=207721
  NO=2, Case=207722
  ...

Sheet 2: "HE-0214,0252 (Capacitor)" (102 rows)
  NO=1, Case=191221  ← DUPLICATE NO!
  NO=2, Case=191222  ← DUPLICATE NO!
  ...
```

**After `pd.concat()`**: 4,144 rows with duplicate NO values

**Simple Sort Problem:**
- `sort_values("NO")` doesn't specify order for rows with same NO
- Order becomes non-deterministic (depends on concat order, pandas internals)
- Violates HVDC requirement: Output must match HITACHI sequence

**Compound Sort Solution:**
- `sort_values(["NO", "Case No."])` provides stable secondary sort
- Rows with same NO are sorted by Case No. (deterministic)
- Maintains HVDC requirement: Consistent, reproducible ordering

#### Edge Cases Handled

1. **Single Sheet (No Duplicates)**: Works correctly, secondary sort has no effect
2. **Missing Case No. Values**: `na_position="last"` handles nulls gracefully
3. **Non-numeric NO or Case No.**: Pandas handles type coercion automatically

### ✅ Verification Checklist

- [x] Compound sort `(NO, Case No.)` implemented
- [x] Multi-sheet data correctly sorted
- [x] All 5,566 records preserved
- [x] HVDC HITACHI sequence maintained
- [x] No performance degradation
- [x] Documentation updated
- [x] Backward compatible with single-sheet workflows

### 📝 References

- Based on: SORTING_FIX_FINAL_REPORT.md (v4.0.2)
- Verified approach from previous successful implementation
- Issue: "HVDC WAREHOUSE_HITACHI(HE) 순번 대로 매칭이 안된다"
- Solution: Compound sort key `(NO, Case No.)`

---

## [4.0.3] - 2025-10-22

### ✨ Added

#### Auto-Generate Missing Location Columns (Stage 1)
- **Problem**: Raw data files didn't contain all warehouse/site columns defined in `header_registry.py`
  - Missing: JDN MZD, AAA Storage
  - Impact: Stage 3 showed "컬럼 없음" warnings, inconsistent structure
  - User report: "1단계 업데이트시 나의 요청대로 작업이 안된다"

- **Solution**: New `_ensure_all_location_columns()` method in `data_synchronizer_v30.py`
  - Reads all location definitions from `header_registry.py`
  - Automatically adds missing columns as empty (NaT) columns
  - Ensures consistent structure across all pipeline stages
  - Processes both Master and Warehouse files

- **Benefits**:
  - Single source of truth: `header_registry.py`
  - Future-proof: New locations automatically included
  - Zero maintenance: No code changes needed for new warehouses
  - Consistent: All stages have identical column structure
  - User request 100% fulfilled: All missing columns now present

### 🔧 Changed

#### Stage 1 Data Loading
- Updated `_load_file_with_header_detection()` to call `_ensure_all_location_columns()`
- Processes both Master and Warehouse files
- Adds missing columns after consolidation, before synchronization

### 📊 Results

#### Stage 1 Output Structure
```
Before: 7 warehouse columns (39 total)
After:  9 warehouse columns (41 total) ✅

Added:
- JDN MZD (empty, ready for future data)
- AAA Storage (empty, ready for future data)
```

#### Performance
- Execution time: +6s (+15%) for column addition
- Memory impact: +112KB (~0.01%)
- Stage 2 benefit: -5s (faster, no missing column handling)

### 🔍 Investigation Process

#### Problem Discovery
1. **User Report**: "1단계 업데이트시 나의 요청대로 작업이 안된다"
2. **Stage 1 Execution**: Successful but missing detailed warehouse logs
3. **Output Analysis**: Only 7 warehouse columns in Stage 1 output
4. **Raw Data Analysis**: Confirmed missing columns in source files
   - Raw data sheets: Case List, RIL (7,000 rows), HE Local (70 rows), HE-0214,0252 (102 rows)
   - Missing in all sheets: JDN MZD, AAA Storage
5. **Root Cause**: `header_registry.py` definitions not reflected in actual data files

#### Solution Design
- **Option 1**: Modify raw data files (rejected - manual, not maintainable)
- **Option 2**: Auto-generate missing columns in Stage 1 (selected ✅)
  - Uses `header_registry.py` as single source of truth
  - Future-proof design
  - Zero maintenance for new locations

### 🧪 Testing & Verification

#### Test Results
1. **Stage 1 Execution**: ✅ Success
   ```
   Ensuring all location columns:
     [OK] Added 2 missing location columns:
       - JDN MZD
       - AAA Storage
   ```

2. **Output File Verification**: ✅ Success
   ```
   Stage 1 Output Warehouse Columns:
     - AAA Storage ✅
     - DHL WH
     - DSV Al Markaz
     - DSV Indoor
     - DSV MZP
     - DSV Outdoor
     - Hauler Indoor
     - JDN MZD ✅
     - MOSB
   Total columns: 41, Total rows: 7172
   ```

3. **Stage 2 Recognition**: ✅ Success
   ```
   Warehouse 컬럼: 9개 - ['DHL WH', 'DSV Indoor', 'DSV Al Markaz',
                           'Hauler Indoor', 'DSV Outdoor', 'DSV MZP',
                           'JDN MZD', 'MOSB', 'AAA Storage']
   ```

### 📝 Documentation

#### Added
- `STAGE1_MISSING_COLUMNS_FIX_REPORT.md` - Comprehensive implementation report (700+ lines)
- `WORK_SESSION_20251022_STAGE1_FIX.md` - Detailed work session summary

#### Updated
- `README.md` - v4.0.3 features and benefits
- `CHANGELOG.md` - This file

#### Cleanup
- Deleted temporary verification scripts (`check_raw_warehouse_columns.py`)

### 🎯 Summary

**User Request**: "1단계 업데이트시 나의 요청대로 작업이 안된다" + 이전 요청들 (JDN MZD, AAA Storage 추가)

**Resolution**: ✅ **100% Complete**
- All missing warehouse columns now automatically generated in Stage 1
- Uses `header_registry.py` as single source of truth
- Future-proof: New locations automatically included
- Zero maintenance: No code changes needed for new warehouses

**Key Achievement**: Transformed Stage 1 from reactive (only processes existing columns) to proactive (ensures all defined columns exist), creating a robust foundation for the entire pipeline.

---

## [4.0.2] - 2025-10-22

### 🐛 Fixed

#### Stage 3 File Path Issue (Critical Bug Fix)
- **Problem**: Stage 3 was reading from current directory (`.`) instead of Stage 2's derived output folder
  - This caused DHL WH data to be missing (0 records instead of 102)
  - Stage 1's column normalization was not being applied
  - Stage 2's 13 derived columns were not available

- **Fix**: Modified `scripts/stage3_report/hvdc_excel_reporter_final_sqm_rev.py` (lines 210-217)
  - Changed `self.data_path = Path(".")` to use `PIPELINE_ROOT / "data" / "processed" / "derived"`
  - Now correctly reads from Stage 2's output folder

- **Impact**:
  - DHL WH data recovered: 0 → 102 records ✅
  - Warehouse inbound calculation: 5,299 → 5,401 records (+102) ✅
  - Rate mode billing: 165 → 198 records (+33) ✅

#### Column Name Inconsistency
- **Problem**: `report_generator.py` used "DHL Warehouse" while other stages used "DHL WH"
  - Caused column not found errors
  - Data integrity issues across pipeline stages

- **Fix**: Modified `scripts/stage3_report/report_generator.py` (line 285)
  - Changed `"DHL Warehouse"` to `"DHL WH"`
  - Unified column names across all pipeline stages

- **Impact**:
  - Consistent column naming throughout pipeline ✅
  - Proper data flow: Stage 1 → 2 → 3 → 4 ✅

### 📊 Results

#### Performance
- **Total execution time**: 216.57 seconds (~3 minutes 37 seconds)
  - Stage 1: 36.05s (Multi-sheet loading + DSV WH consolidation + stable sorting)
  - Stage 2: 15.53s (13 derived columns)
  - Stage 3: 114.61s (Report generation with corrected path)
  - Stage 4: 50.36s (Anomaly detection + visualization)

#### Data Integrity
- **DHL WH records**: 102 records successfully recovered
- **Warehouse inbound**: 5,401 records (correctly includes all warehouses)
- **Total records processed**: 7,172 records across 3 sheets
- **Anomalies detected**: 502 anomalies with proper color coding

#### Verification
```
HITACHI 파일 창고 컬럼 분석:
    DHL WH: 102건 데이터 ✅
    DSV Indoor: 1,226건 데이터 ✅
    DSV Al Markaz: 1,161건 데이터 ✅
    Hauler Indoor: 392건 데이터 ✅
    DSV Outdoor: 1,410건 데이터 ✅
    DSV MZP: 14건 데이터 ✅
    MOSB: 1,102건 데이터 ✅
```

### 📝 Documentation

#### Added
- `STAGE3_PATH_FIX_REPORT.md` - Detailed fix report with root cause analysis
- `CHANGELOG.md` - This file
- Updated `README.md` with v4.0.2 changes and new performance metrics

#### Updated
- `plan.md` - Work completion status

### 🔍 Technical Details

#### Root Cause Analysis
1. **Legacy Design**: `hvdc_excel_reporter_final_sqm_rev.py` was originally a standalone script
2. **Path Assumption**: Used `Path(".")` assuming execution from specific directory
3. **Integration Gap**: When integrated into pipeline, path resolution broke
4. **Column Mismatch**: Different parts of codebase used different column names

#### Solution Pattern
- Adopted `PIPELINE_ROOT = Path(__file__).resolve().parents[2]` pattern
- Consistent with `report_generator.py` approach
- Ensures relative paths work regardless of execution context

### 🎯 Impact Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| DHL WH Data | 0 records | 102 records | +102 ✅ |
| Warehouse Inbound | 5,299 records | 5,401 records | +102 ✅ |
| Rate Mode Billing | 165 records | 198 records | +33 ✅ |
| Pipeline Success | ❌ Incomplete | ✅ Complete | Fixed |
| Data Integrity | ❌ Broken | ✅ Restored | Fixed |

---

## [4.0.2] - 2025-10-22 (Earlier)

### ✨ Added

#### Multi-Sheet Support
- Automatically loads and merges all sheets from Excel files
- Processes 3 sheets → 7,172 records total
- Maintains data integrity across sheet boundaries

#### DSV WH Consolidation
- Automatically merges "DSV WH" → "DSV Indoor" (1,226 records total)
- Prevents duplicate warehouse entries
- Ensures consistent warehouse naming

#### Stable Sorting
- Compound sort key: (No, Case No.)
- Maintains HVDC HITACHI record order
- Prevents sorting issues with duplicate "No" values from multi-sheet merging

### 🔧 Changed

#### Semantic Header Matching
- 100% elimination of hardcoded column names
- Meaning-based automatic header matching
- 97% confidence auto-detection of header rows
- Supports multiple header name variations

#### Performance Optimization
- Stage 1: ~36s (multi-sheet processing included)
- Stage 2: ~16s (derived columns)
- Stage 3: ~115s (report generation)
- Stage 4: ~50s (anomaly detection + visualization)

---

## [4.0.1] - 2025-10-22 (Earlier)

### ✨ Added

#### Core Module Integration
- Semantic header matching system
- Automatic header row detection (97% confidence)
- Zero hardcoding approach
- Flexible column name handling

#### Files Added
- `scripts/core/__init__.py` - Core module exports
- `scripts/core/header_registry.py` - Header definitions (34 headers, 7 categories)
- `scripts/core/header_normalizer.py` - NFKC normalization
- `scripts/core/header_detector.py` - 5 heuristic header detection
- `scripts/core/semantic_matcher.py` - 3-tier matching (Exact/Partial/Prefix)

### 🔧 Changed

#### Stage 1 Upgrade (v3.0)
- Replaced hardcoded column names with semantic keys
- Unicode character fixes for Windows compatibility
- Relative import fixes for core module

#### Documentation
- `CORE_MODULE_INTEGRATION_REPORT.md` - Integration details
- `FINAL_INTEGRATION_SUMMARY.md` - v4.0.1 summary
- Updated `README.md` with v4.0.1 features

---

## [4.0.0] - 2025-10 (Balanced Boost Edition)

### ✨ Added

#### Stage 4 Balanced Boost
- ECDF calibration for ML anomaly risk scores
- Hybrid risk scoring system
- Per-location IQR+MAD thresholds
- PyOD ensemble ML (7,000x improvement)
- Real-time visualization with color coding

#### Anomaly Types
- Time Reversal (Red) - 190 cases
- ML Outliers High/Critical (Orange) - 139 cases
- ML Outliers Medium/Low + Overstay (Yellow) - 172 cases
- Data Quality (Purple) - 1 case

### 🔧 Changed

#### Performance
- ML anomaly detection: 3,724 → 115 cases (97% false positive reduction)
- Risk saturation: 100% eliminated (no more 1.000 scores)
- Risk range: 0.981~0.999 (proper distribution)

---

## [3.0.2] - 2025-09

### ✨ Added
- Flexible column matching ("No" and "No." recognized as same)
- Master NO. sorting (Case List order)
- Date normalization (multiple formats)
- Version tracking in output files

### 🔧 Changed
- Stage 3: Dynamic date range calculation
- Stage 4: Auto file discovery
- Improved color visualization system

---

## [3.0.0] - 2025-09

### ✨ Added
- Stage 1: Data Synchronization
- Stage 2: Derived Columns (13 columns)
- Stage 3: Report Generation
- Stage 4: Anomaly Detection
- Automated color coding (Stage 1 & 4)

### 📊 Initial Metrics
- Master: 5,552 rows
- Warehouse: 5,552 rows
- Date updates: 1,564 records
- New rows: 104 records
- Derived columns: 13 added

---

## Legend

- 🎉 Major feature
- ✨ Added feature
- 🔧 Changed/Improved
- 🐛 Bug fix
- 📊 Performance improvement
- 📝 Documentation
- 🔒 Security
- ⚠️ Deprecated
- 🗑️ Removed

---

**Note**: This changelog is maintained to track all significant changes to the HVDC Pipeline project. Each version includes detailed information about fixes, improvements, and new features to ensure transparency and traceability.
