# HVDC 파이프라인 전체 실행 흐름 상세 가이드

## 📋 문서 정보
- **작성일**: 2025-11-02
- **버전**: v1.0
- **적용 범위**: Stage 1 ~ Stage 4 전체 파이프라인
- **상태**: ✅ 완료

---

## 1. 개요

이 문서는 HVDC 파이프라인의 Stage 1부터 Stage 4까지의 전체 실행 흐름을 상세히 기록합니다. 각 단계에서 어떤 파일이 실행되고, 어떤 데이터가 처리되며, 다음 단계로 어떻게 전달되는지를 단계별로 설명합니다.

---

## 2. 파이프라인 실행 진입점

### 2.1 메인 실행 스크립트
**파일**: `run/run_pipeline.py`

**실행 명령**:
```bash
# 전체 실행
python run/run_pipeline.py --all

# 개별 Stage 실행
python run/run_pipeline.py --stage 1
python run/run_pipeline.py --stage 2
python run/run_pipeline.py --stage 3
python run/run_pipeline.py --stage 4

# 여러 Stage 동시 실행
python run/run_pipeline.py --stage 1 2 3
```

### 2.2 초기화 단계

**실행 순서**:
1. **프로젝트 경로 설정**
   ```python
   PIPELINE_ROOT = Path(__file__).resolve().parent  # run/
   PROJECT_ROOT = PIPELINE_ROOT.parent              # 프로젝트 루트
   PIPELINE_CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline_config.yaml"
   STAGE2_CONFIG_PATH = PROJECT_ROOT / "config" / "stage2_derived_config.yaml"
   ```

2. **설정 파일 로드**
   - `config/pipeline_config.yaml`: 전체 파이프라인 설정
   - `config/stage2_derived_config.yaml`: Stage 2 전용 설정

3. **모듈 Import**
   - Stage 1: `DataSynchronizerV30` from `scripts.stage1_sync_sorted.data_synchronizer_v30`
   - Stage 2: `process_derived_columns` from `scripts.stage2_derived.derived_columns_processor`
   - Stage 3: `HVDCExcelReporterFinal` from `scripts.stage3_report.report_generator`
   - Stage 4: `HybridAnomalyDetector`, `AnomalyVisualizer` from `scripts.stage4_anomaly`

---

## 3. Stage 1: 데이터 동기화 (Data Synchronization)

### 3.1 실행 진입점

**함수**: `run_stage(stage_num=1, ...)` (Line 156)
**파일**: `run/run_pipeline.py`

**실행 흐름**:
```python
if stage_num == 1:
    # 1. 설정 로드
    stage1_cfg = pipeline_config.get("stages", {}).get("stage1", {}).get("io", {})
    master_path = resolve_repo_path(stage1_cfg.get("master_file"))
    warehouse_path = resolve_repo_path(stage1_cfg.get("warehouse_file"))
    output_path = resolve_repo_path(stage1_cfg.get("output_file"))
    
    # 2. DataSynchronizerV30 인스턴스 생성
    synchronizer = DataSynchronizerV30()
    
    # 3. 동기화 실행
    sync_result = synchronizer.synchronize(master_path, warehouse_path, output_path)
```

### 3.2 입력 파일

**설정 위치**: `config/pipeline_config.yaml` → `stages.stage1.io`

**입력 파일**:
1. **Master 파일** (`master_file`)
   - 경로: `data/raw/Case List.xlsx`
   - 역할: 메인 Case 목록, 날짜 업데이트 소스
   - 내용: Case No., Shipment Invoice No., 각 창고/현장 입고 날짜

2. **Warehouse 파일** (`warehouse_file`)
   - 경로: `data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx`
   - 역할: 창고 데이터, 여러 시트 포함
   - 시트 구성:
     - `Case List, RIL`: 주요 데이터 시트
     - `HE Local`: 로컬 데이터
     - `HE-0214,0252 (Capacitor)`: 특수 케이스

### 3.3 Stage 1 상세 실행 단계

#### Phase 1: 파일 로드 (Line ~1400)

**실행 파일**: `scripts/stage1_sync_sorted/data_synchronizer_v30.py`
**메서드**: `synchronize()` → `_load_files_by_sheets()`

**처리 순서**:
1. **Master 파일 로드**
   ```
   ┌─────────────────────────────────┐
   │ Case List.xlsx                  │
   │ ┌──────────────────────────┐   │
   │ │ Sheet: "Case List"        │   │
   │ │ - 1776 rows               │   │
   │ │ - 32 columns              │   │
   │ └──────────────────────────┘   │
   └─────────────────────────────────┘
              ↓
   [Header Detection]
   - HeaderDetector로 헤더 행 자동 탐지 (row=4)
   - SemanticMatcher로 컬럼 매칭
   - 누락된 컬럼 자동 추가 (DHL WH, AAA Storage, etc.)
              ↓
   [DataFrame 생성]
   - Source_Vendor='HITACHI' 추가
   - Source_Sheet='Case List' 추가
   ```

2. **Warehouse 파일 로드**
   ```
   ┌─────────────────────────────────┐
   │ HVDC WAREHOUSE_HITACHI(HE).xlsx│
   │ ┌──────────────────────────┐   │
   │ │ Sheet 1: Case List, RIL   │   │
   │ │ - 7001 rows               │   │
   │ │ - 38 columns              │   │
   │ ├──────────────────────────┤   │
   │ │ Sheet 2: HE Local         │   │
   │ │ - 79 rows                 │   │
   │ │ - 28 columns              │   │
   │ ├──────────────────────────┤   │
   │ │ Sheet 3: HE-0214,0252     │   │
   │ │ - 102 rows                │   │
   │ │ - 37 columns              │   │
   │ └──────────────────────────┘   │
   └─────────────────────────────────┘
              ↓
   [시트별 처리]
   각 시트에 대해:
   - HeaderDetector로 헤더 탐지
   - 컬럼 정규화 및 매칭
   - 누락 컬럼 추가
   - Source_Sheet 메타데이터 추가
   ```

#### Phase 2: 시트별 동기화 (Line ~1700)

**메서드**: `synchronize()` → Sheet-by-Sheet Synchronization

**처리 순서**:
1. **시트 매칭**
   ```
   Master: ["Case List"]
   Warehouse: ["Case List, RIL", "HE Local", "HE-0214,0252 (Capacitor)"]
   
   → 공통 시트: 1개 ("Case List" ↔ "Case List, RIL")
   → Master 전용: 0개
   → Warehouse 전용: 2개
   ```

2. **공통 시트 동기화** ("Case List" ↔ "Case List, RIL")
   ```
   ┌─────────────────────────────────────┐
   │ Case List (Master)                   │
   │ - 1309 cases                         │
   │ └───────────────────────────────────┘
              ↓
   [Semantic Header Matching]
   - case_number → 'Case No.'
   - etd_atd → 'ETD/ATD'
   - dhl_wh → 'DHL WH'
   - ... (16개 컬럼 매칭)
              ↓
   [데이터 병합]
   - Warehouse 원본 순서 유지
   - Master에서 날짜 업데이트 적용
   - 신규 레코드 추가
              ↓
   ┌─────────────────────────────────────┐
   │ Case List, RIL (Synced)              │
   │ - 7169 rows (원본 7001 + 168 신규)   │
   │ - 1029개 날짜 업데이트               │
   │ └───────────────────────────────────┘
   ```

3. **Warehouse 전용 시트 처리**
   - "HE Local": 79 rows (변경 없음)
   - "HE-0214,0252 (Capacitor)": 102 rows (변경 없음)

#### Phase 3: 중복 처리 (Line ~1840)

**메서드**: `synchronize()` → 개별 시트 저장 직전

**중복 처리 로직** (DUP-GUARD):
```python
# 개별 시트 저장 직전 (Line 1850-1862)
for sheet_name, (df, header_row) in processed_sheets.items():
    df_reordered = reorder_dataframe_columns(df, ...)
    
    # 중복 마킹
    df_with_flag, dup_mask = mark_duplicates(
        df_reordered, semantic_finder=_find_col, keep="first"
    )
    
    # "고유 중복" 컬럼 추가
    df_reordered.insert(0, "고유 중복", 
                       np.where(dup_mask, "중복", "고유"))
    
    df_reordered.to_excel(writer, sheet_name=clean_sheet_name, index=False)
```

**처리 결과**:
- Case List, RIL: 7,169행, 35개 중복 감지
- HE Local: 79행, 모두 고유
- HE-0214: 102행, 모두 고유

#### Phase 4: 병합 및 전역 중복 제거 (Line ~1900)

**메서드**: `synchronize()` → 병합 파일 생성

**처리 순서**:
```python
# 모든 시트 병합
merged_df = pd.concat(combined_dfs, ignore_index=True, sort=False)
# → 7,350행 (Case List, RIL 7169 + HE Local 79 + HE-0214 102)

# 전역 중복 제거
merged_df = drop_duplicates_by_case(
    merged_df, semantic_finder=_find_col, keep="first"
)
# → 7,176행 (174개 중복 제거)
```

#### Phase 5: Excel 저장 및 컬러 포맷팅 (Line ~1850)

**메서드**: 
- `synchronize()` → Excel Writer
- `_apply_excel_formatting()` (Line 2016)

**처리 순서**:
1. **개별 시트 파일 저장**
   - 파일: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx`
   - 각 시트에 "고유 중복" 컬럼 포함
   - 표준 헤더 순서 적용 (63개 컬럼)

2. **컬러 포맷팅 적용**
   ```python
   # Orange (날짜 업데이트): 1029개 셀
   for change in change_tracker.changes:
       if change.change_type == "date_update":
           cell.fill = orange_fill  # FFFFA500
   
   # Yellow (신규 레코드): 4834개 셀
   for case_no in change_tracker.new_cases:
       row.fill = yellow_fill  # FFFFFF00
   ```

3. **병합 파일 저장**
   - 파일: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`
   - 시트: "Merged Data"
   - 행 수: 7,176행 (전역 중복 제거 후)
   - "고유 중복" 컬럼 포함

### 3.4 Stage 1 출력 파일

**출력 파일**:
1. **개별 시트 파일**
   - 경로: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx`
   - 시트:
     - `Case List, RIL`: 7,169행, 43컬럼
     - `HE Local`: 79행, 34컬럼
     - `HE-0214,0252 (Capacitor)`: 102행, 43컬럼
   - 특징: 컬러 포맷팅 적용 (Orange/Yellow)

2. **병합 파일**
   - 경로: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`
   - 시트: `Merged Data`
   - 행 수: 7,176행, 45컬럼
   - 특징: 전역 중복 제거 완료, "고유 중복" 컬럼 포함

### 3.5 Stage 1 통계

**처리 결과**:
- 업데이트: 1,029개 셀 (날짜)
- 신규 레코드: 168개
- 중복 제거: 174개 (병합 파일 기준)
- 실행 시간: ~54-79초

---

## 4. Stage 2: 파생 컬럼 생성 (Derived Columns Generation)

### 4.1 실행 진입점

**함수**: `run_stage(stage_num=2, ...)` (Line 227)
**파일**: `run/run_pipeline.py`

**실행 흐름**:
```python
elif stage_num == 2:
    # 1. 입력 파일 경로 확인
    shared_synced_path = resolve_stage2_synced_input_path(...)
    
    # 2. 파생 컬럼 생성 실행
    success = process_derived_columns(
        pipeline_config_path=PIPELINE_CONFIG_PATH,
        stage2_config_path=STAGE2_CONFIG_PATH,
        project_root=PROJECT_ROOT,
    )
```

### 4.2 입력 파일

**입력 파일**: Stage 1 출력 파일
- 경로: `data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx`
- 또는 개별 시트 파일 (설정에 따라)

**실행 파일**: `scripts/stage2_derived/derived_columns_processor.py`
**메서드**: `process_derived_columns()`

### 4.3 Stage 2 상세 실행 단계

#### Step 1: 입력 파일 로드

**처리**:
```python
# derived_columns_processor.py
synced_file = resolve_synced_input_path(...)
df = pd.read_excel(synced_file, sheet_name="Merged Data")
```

#### Step 2: 파생 컬럼 생성

**생성되는 컬럼** (예시):
- `wh_handling`: 창고 처리 로직
- `site_handling`: 현장 처리 로직
- `total_handling`: 총 처리 로직
- `Status_Location`: 자동 분류된 위치 상태
- 기타 계산된 컬럼들

**처리 파일**: 
- `scripts/stage2_derived/column_definitions.py`: 컬럼 정의
- `scripts/stage2_derived/stack_and_sqm.py`: Stack/SQM 계산

#### Step 3: 출력 파일 저장

**출력 파일**:
- 경로: `data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- 내용: Stage 1 데이터 + 파생 컬럼들

---

## 5. Stage 3: 리포트 생성 (Report Generation)

### 5.1 실행 진입점

**함수**: `run_stage(stage_num=3, ...)` (Line 246)
**파일**: `run/run_pipeline.py`

**실행 흐름**:
```python
elif stage_num == 3:
    # 1. HVDCExcelReporterFinal 인스턴스 생성
    reporter = HVDCExcelReporterFinal()
    calculator = reporter.calculator
    
    # 2. 입력 파일 경로 설정
    hitachi_file = stage3_cfg.get("hitachi_file")
    calculator.hitachi_file = resolve_repo_path(hitachi_file)
    
    # 3. 리포트 생성
    excel_filename = reporter.generate_final_excel_report()
```

### 5.2 입력 파일

**설정 위치**: `config/pipeline_config.yaml` → `stages.stage3.io`

**입력 파일**:
1. **HITACHI 파일** (`hitachi_file`)
   - 경로: `data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx`
   - 역할: Stage 2에서 생성된 파생 컬럼 포함 데이터

2. **SIEMENS 파일** (선택)
   - 경로: `data/processed/derived/HVDC WAREHOUSE_SIMENSE(SIM).xlsx`
   - 역할: SIEMENS 벤더 데이터

3. **Invoice 파일** (선택)
   - 경로: `data/processed/derived/HVDC WAREHOUSE_INVOICE.xlsx`
   - 역할: 인보이스 데이터

### 5.3 Stage 3 상세 실행 단계

**실행 파일**: `scripts/stage3_report/report_generator.py`
**클래스**: `HVDCExcelReporterFinal`
**메서드**: `generate_final_excel_report()` (Line ~3800)

#### Step 1: 데이터 로드

**처리**:
```python
# report_generator.py
master_df = pd.read_excel(calculator.hitachi_file, sheet_name=0)
# → 7,329행 로드
```

#### Step 2: Flow Code v3.5 적용

**처리 파일**: `scripts/stage3_report/report_generator.py`
**메서드**: `_override_flow_code()` (Line ~753)

**처리 순서**:
```
입력 데이터 (7,329행)
    ↓
[Flow Code 계산]
- Pre Arrival 감지 (Flow 0)
- Port → Site 감지 (Flow 1)
- Port → WH → Site 감지 (Flow 2)
- Port → MOSB → Site 감지 (Flow 3) [AGI/DAS 도메인 규칙]
- Port → WH → MOSB → Site 감지 (Flow 4) [AGI/DAS 도메인 규칙]
- Mixed/Incomplete 감지 (Flow 5)
    ↓
[AGI/DAS 도메인 오버라이드]
- Final_Location이 AGI 또는 DAS인 경우
- Flow 0, 1, 2 → 강제로 Flow 3 또는 4로 변경
    ↓
결과: Flow Code 분포
- Flow 0: 47개
- Flow 1: 2,359개
- Flow 2: 3,244개
- Flow 3: 627개
- Flow 4: 699개
- Flow 5: 353개
```

#### Step 3: 창고 통계 계산

**메서드**: `calculate_warehouse_statistics()` (Line ~2000)

**처리 내용**:
- 창고별 입고 건수
- 창고별 SQM 계산
- 월별 집계

#### Step 4: 현장 통계 계산

**메서드**: 현장 입고 분석

**처리 내용**:
- 현장별 입고 건수 (MIR, SHU, DAS, AGI)
- 월별 집계

#### Step 5: SQM 계산

**처리 파일**: `scripts/stage3_report/utils.py`
**메서드**: 벡터화된 SQM 계산

**처리 내용**:
- 입고 SQM 계산: 7,327개 (100.0%)
- 출고 SQM 계산
- 누적 재고 SQM 계산

#### Step 6: Excel 리포트 생성

**생성되는 시트** (총 10개 이상):
1. **창고_월별_집계** (36행, 28열)
   - 창고별 월별 입고/출고 통계
   - Flow Ledger 기반 계산

2. **현장_월별_입고집계** (36행, 9열)
   - 현장별 월별 입고 통계

3. **Flow Code 분석** (6개 코드)
   - Flow 0-5 분포 및 상세 분석

4. **전체 트랜잭션 요약** (8개 차트)
   - 시각화된 통계

5. **SQM 데이터 요약** (315행)
   - SQM 계산 상세 데이터

6. **SQM Invoice 요약** (120행)
   - 인보이스별 SQM 요약

7. **SQM 참조 테이블** (35행, 37열)
   - SQM 계산 참조 데이터

8. **HITACHI_입고로직_종합리포트_Fixed** (7,329행, 63컬럼)
   - 전체 데이터 + 계산된 컬럼들

### 5.4 Stage 3 출력 파일

**출력 파일**:
- 경로: `data/processed/reports/HVDC_입고보관_통합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx`
- 특징: 다중 시트 Excel 파일, 모든 분석 결과 포함
- 크기: ~10MB 이상 (데이터 양에 따라)

### 5.5 Stage 3 통계

**처리 결과**:
- 총 데이터: 7,329행
- SQM 계산: 7,327개 (100.0%)
- Stack_Status 파싱: 7,230개 (98.6%)
- 실행 시간: ~118초

---

## 6. Stage 4: 이상 탐지 (Anomaly Detection)

### 6.1 실행 진입점

**함수**: `run_stage(stage_num=4, ...)` (Line 318)
**파일**: `run/run_pipeline.py`

**실행 흐름**:
```python
elif stage_num == 4:
    # 1. 설정 로드
    stage4_cfg = pipeline_config.get("stages", {}).get("stage4", {})
    
    # 2. DetectorConfig 생성
    config = DetectorConfig(...)
    
    # 3. HybridAnomalyDetector 생성 및 실행
    detector = HybridAnomalyDetector(config)
    results = detector.detect_anomalies()
    
    # 4. 시각화 생성
    visualizer = AnomalyVisualizer(config)
    visualizer.generate_report(results)
```

### 6.2 입력 파일

**입력 파일**: Stage 3 출력 파일
- 경로: `data/processed/reports/HVDC_입고보관_통합리포트_*.xlsx`
- 또는 Stage 2 출력 파일 직접 사용

**설정 파일**:
- `scripts/stage4_anomaly/stage4.yaml`: Stage 4 설정

### 6.3 Stage 4 상세 실행 단계

**실행 파일**: `scripts/stage4_anomaly/anomaly_detector_balanced.py`
**클래스**: `HybridAnomalyDetector`

#### Step 1: 데이터 로드

**처리**:
```python
# anomaly_detector_balanced.py
df = pd.read_excel(config.input_file, sheet_name=config.sheet_name)
```

#### Step 2: 이상 탐지

**탐지 방법**:
1. **통계적 이상 탐지**
   - Z-score 기반 이상치 탐지
   - IQR 기반 이상치 탐지

2. **도메인 규칙 기반 탐지**
   - 날짜 순서 이상
   - Flow Code 불일치
   - SQM 계산 오류

3. **머신러닝 기반 탐지** (선택)
   - Isolation Forest
   - Local Outlier Factor

#### Step 3: 이상 결과 집계

**결과 구조**:
```python
{
    "anomalies": [
        {
            "case_no": "207714",
            "anomaly_type": "date_order",
            "severity": "high",
            "description": "..."
        },
        ...
    ],
    "summary": {
        "total_anomalies": 150,
        "high_severity": 20,
        "medium_severity": 80,
        "low_severity": 50
    }
}
```

#### Step 4: 시각화 및 리포트 생성

**실행 파일**: `scripts/stage4_anomaly/anomaly_visualizer.py`
**클래스**: `AnomalyVisualizer`

**생성되는 출력**:
1. **Excel 리포트**
   - 이상 케이스 목록
   - 이상 유형별 통계
   - 시각화 차트

2. **HTML 대시보드** (선택)
   - 인터랙티브 차트
   - 필터링 기능

### 6.4 Stage 4 출력 파일

**출력 파일**:
- 경로: `data/processed/anomaly/anomaly_report_YYYYMMDD_HHMMSS.xlsx`
- 내용: 이상 탐지 결과 및 분석 리포트

---

## 7. 전체 파이프라인 실행 순서 요약

### 7.1 실행 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│ run/run_pipeline.py                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ main()                                              │ │
│ │  ↓                                                  │ │
│ │ run_specific_stages()                               │ │
│ │  ↓                                                  │ │
│ │ for stage in stages:                                │ │
│ │     run_stage(stage_num)                            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
┌─────────┐         ┌─────────┐
│Stage 1  │         │Stage 2  │
│         │         │         │
│Input:   │         │Input:   │
│- Master │         │Stage 1  │
│- WH     │         │Output   │
│         │         │         │
│Output:  │         │Output:  │
│Synced   │  ───→   │Derived  │
│File     │         │File     │
└─────────┘         └─────────┘
                            ↓
                    ┌─────────┐
                    │Stage 3  │
                    │         │
                    │Input:   │
                    │Stage 2  │
                    │Output   │
                    │         │
                    │Output:  │
                    │Report   │
                    │File     │
                    └─────────┘
                            ↓
                    ┌─────────┐
                    │Stage 4  │
                    │         │
                    │Input:   │
                    │Stage 3  │
                    │Output   │
                    │         │
                    │Output:  │
                    │Anomaly  │
                    │Report   │
                    └─────────┘
```

### 7.2 파일 의존성 체인

```
data/raw/
├── Case List.xlsx                    (Stage 1 입력)
└── HVDC WAREHOUSE_HITACHI(HE).xlsx  (Stage 1 입력)
            ↓
data/processed/synced/
├── HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx      (Stage 1 출력)
└── HVDC WAREHOUSE_HITACHI(HE).synced_v3.4_merged.xlsx (Stage 1 출력)
            ↓
data/processed/derived/
└── HVDC WAREHOUSE_HITACHI(HE).xlsx   (Stage 2 출력)
            ↓
data/processed/reports/
└── HVDC_입고보관_통합리포트_*.xlsx    (Stage 3 출력)
            ↓
data/processed/anomaly/
└── anomaly_report_*.xlsx             (Stage 4 출력)
```

### 7.3 실행 시간 예상

**개별 실행**:
- Stage 1: ~54-79초
- Stage 2: ~10-30초
- Stage 3: ~118초
- Stage 4: ~60-120초

**전체 실행**: ~5-7분 (데이터 양에 따라 다름)

---

## 8. 각 Stage의 핵심 모듈 및 함수

### 8.1 Stage 1 핵심 모듈

| 모듈 | 역할 | 주요 함수 |
|------|------|----------|
| `data_synchronizer_v30.py` | 메인 동기화 로직 | `synchronize()`, `_load_files_by_sheets()`, `_apply_excel_formatting()` |
| `core/semantic_matcher.py` | 의미론적 헤더 매칭 | `find_column()`, `match_dataframe()` |
| `core/header_detector.py` | 헤더 행 자동 탐지 | `detect_header_row()` |
| `core/duplicate_handler.py` | 중복 처리 | `mark_duplicates()`, `drop_duplicates_by_case()` |
| `core/standard_header_order.py` | 표준 헤더 순서 적용 | `reorder_dataframe_columns()` |

### 8.2 Stage 2 핵심 모듈

| 모듈 | 역할 | 주요 함수 |
|------|------|----------|
| `derived_columns_processor.py` | 파생 컬럼 생성 메인 | `process_derived_columns()` |
| `column_definitions.py` | 컬럼 정의 | 컬럼 생성 로직 |
| `stack_and_sqm.py` | Stack/SQM 계산 | SQM 계산 함수들 |

### 8.3 Stage 3 핵심 모듈

| 모듈 | 역할 | 주요 함수 |
|------|------|----------|
| `report_generator.py` | 리포트 생성 메인 | `generate_final_excel_report()`, `_override_flow_code()` |
| `utils.py` | 유틸리티 함수 | 벡터화된 계산 함수들 |
| `hvdc_excel_reporter_final_sqm_rev.py` | Excel 리포트 작성 | 시트 생성 함수들 |

### 8.4 Stage 4 핵심 모듈

| 모듈 | 역할 | 주요 함수 |
|------|------|----------|
| `anomaly_detector_balanced.py` | 이상 탐지 메인 | `detect_anomalies()` |
| `anomaly_visualizer.py` | 시각화 및 리포트 | `generate_report()` |
| `analysis_reporter.py` | 분석 리포트 작성 | 리포트 생성 함수들 |

---

## 9. 설정 파일 구조

### 9.1 pipeline_config.yaml 구조

```yaml
stages:
  stage1:
    io:
      master_file: "data/raw/Case List.xlsx"
      warehouse_file: "data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx"
      output_file: "data/processed/synced/HVDC WAREHOUSE_HITACHI(HE).synced_v3.4.xlsx"
  
  stage2:
    # Stage 2 설정
    
  stage3:
    io:
      hitachi_file: "data/processed/derived/HVDC WAREHOUSE_HITACHI(HE).xlsx"
      siemens_file: "data/processed/derived/HVDC WAREHOUSE_SIMENSE(SIM).xlsx"
      invoice_file: "data/processed/derived/HVDC WAREHOUSE_INVOICE.xlsx"
      report_directory: "data/processed/reports"
  
  stage4:
    # Stage 4 설정
```

---

## 10. 에러 처리 및 로깅

### 10.1 각 Stage의 에러 처리

**Stage 1**:
- 파일 없음: `FileNotFoundError` → 에러 메시지 출력
- 컬럼 매칭 실패: 경고 메시지 → 휴리스틱 fallback
- 중복 처리 실패: 경고 메시지 → 원본 데이터 유지

**Stage 2**:
- 입력 파일 없음: 에러 반환
- 파생 컬럼 계산 실패: 에러 로깅

**Stage 3**:
- 데이터 품질 문제: 경고 메시지 → 계속 진행
- Flow Code 계산 실패: 기본값 사용

**Stage 4**:
- 이상 탐지 실패: 빈 결과 반환

### 10.2 로깅 레벨

- **INFO**: 정상 실행 과정
- **WARNING**: 경고 사항 (계속 진행 가능)
- **ERROR**: 에러 (중단 가능)

---

## 11. 실행 전 체크리스트

### 11.1 필수 파일 확인

- [ ] `data/raw/Case List.xlsx` 존재
- [ ] `data/raw/HVDC WAREHOUSE_HITACHI(HE).xlsx` 존재
- [ ] `config/pipeline_config.yaml` 존재
- [ ] 출력 디렉토리 권한 확인

### 11.2 Python 패키지 확인

- [ ] pandas
- [ ] openpyxl
- [ ] pyyaml
- [ ] numpy

### 11.3 실행 권한 확인

- [ ] 파일 읽기 권한
- [ ] 파일 쓰기 권한
- [ ] Excel 파일이 다른 프로그램에서 열려있지 않은지 확인

---

## 12. 문제 해결 가이드

### 12.1 Stage 1 문제

**문제**: 파일을 찾을 수 없음
- **해결**: `config/pipeline_config.yaml`에서 경로 확인

**문제**: 권한 오류
- **해결**: Excel 파일이 열려있지 않은지 확인

**문제**: 컬럼 매칭 실패
- **해결**: 로그에서 매칭 실패 컬럼 확인, `core/header_registry.py`에 alias 추가

### 12.2 Stage 3 문제

**문제**: Flow Code 계산 오류
- **해결**: 필수 컬럼(Status_Location, warehouse_columns, site_columns) 존재 확인

**문제**: SQM 계산 실패
- **해결**: 입력 데이터의 SQM 관련 컬럼 확인

---

## 13. 성능 최적화 팁

### 13.1 Stage 1 최적화

- 벡터화 연산 사용 (이미 적용됨)
- 대용량 파일의 경우 청크 처리 고려

### 13.2 Stage 3 최적화

- 벡터화된 SQM 계산 사용 (이미 적용됨)
- 병렬 처리 가능 영역 식별

---

## 14. 참고 문서

### 14.1 관련 문서

- `docs/reports/STAGE1_DUPLICATE_HANDLER_IMPLEMENTATION_REPORT.md`: Stage 1 중복 처리 구현 보고서
- `docs/reports/FlowCode_v35_완료보고서.md`: Flow Code v3.5 구현 보고서
- `docs/technical/FLOW_CODE_V35_ALGORITHM.md`: Flow Code 알고리즘 상세

### 14.2 코드 참조

- `run/run_pipeline.py`: 메인 실행 스크립트
- `scripts/stage1_sync_sorted/data_synchronizer_v30.py`: Stage 1 메인 로직
- `scripts/stage3_report/report_generator.py`: Stage 3 메인 로직

---

## 15. 결론

이 문서는 HVDC 파이프라인의 Stage 1부터 Stage 4까지의 전체 실행 흐름을 상세히 기록했습니다. 각 단계에서 어떤 파일이 실행되고, 어떤 데이터가 처리되며, 다음 단계로 어떻게 전달되는지를 명확히 이해할 수 있도록 구성했습니다.

**핵심 포인트**:
1. **진입점**: `run/run_pipeline.py`의 `main()` 함수
2. **설정 기반**: 모든 경로와 설정은 YAML 파일에서 관리
3. **모듈화**: 각 Stage는 독립적인 모듈로 구성
4. **데이터 흐름**: Raw → Synced → Derived → Reports → Anomaly
5. **에러 처리**: 각 Stage별로 독립적인 에러 처리

---

**문서 버전**: v1.0  
**최종 업데이트**: 2025-11-02  
**작성자**: AI Assistant (Cursor)

