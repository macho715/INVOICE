# Stage 3 File Path Fix Report

**날짜**: 2025-10-22  
**버전**: v4.0.2  
**작업**: Stage 3 파일 경로 수정 및 컬럼명 통일

## 문제 진단

### 발견된 문제
Stage 3 실행 시 "DHL WH" 데이터가 누락되는 현상 발생:
```
HITACHI 파일 창고 컬럼 분석:
    DHL Warehouse: 컬럼 없음 - 빈 컬럼 추가  # 문제!
    통합 데이터 컬럼 검증:
    DHL Warehouse: 0건 데이터  # 문제!
```

### 근본 원인
1. **잘못된 파일 경로** (`hvdc_excel_reporter_final_sqm_rev.py`):
   - 현재 디렉토리(`.`)에서 raw 파일을 읽으려 시도
   - Stage 2의 processed/derived 폴더를 읽어야 함
   
2. **일관되지 않은 컬럼명** (`report_generator.py`):
   - "DHL Warehouse"를 사용 (Stage 1/2는 "DHL WH" 사용)

## 수정 내용

### 1. hvdc_excel_reporter_final_sqm_rev.py (lines 210-217)

**변경 전**:
```python
self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 실제 데이터 경로 설정 (현재 디렉토리 기준)
self.data_path = Path(".")  # 현재 hitachi 디렉토리
self.hitachi_file = self.data_path / "HVDC WAREHOUSE_HITACHI(HE).xlsx"
self.simense_file = self.data_path / "HVDC WAREHOUSE_SIMENSE(SIM).xlsx"
self.invoice_file = self.data_path / "HVDC WAREHOUSE_INVOICE.xlsx"
```

**변경 후**:
```python
self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 파이프라인 루트 기준 경로 설정 (Stage 2 출력 사용)
PIPELINE_ROOT = Path(__file__).resolve().parents[2]
self.data_path = PIPELINE_ROOT / "data" / "processed" / "derived"
self.hitachi_file = self.data_path / "HVDC WAREHOUSE_HITACHI(HE).xlsx"
self.simense_file = self.data_path / "HVDC WAREHOUSE_SIMENSE(SIM).xlsx"
self.invoice_file = self.data_path / "HVDC WAREHOUSE_INVOICE.xlsx"
```

**이유**:
- Stage 2의 출력 파일은 이미 Stage 1의 column normalization 적용됨
- "DHL Warehouse" → "DHL WH" 변환 완료 상태
- 13개 derived columns 포함

### 2. report_generator.py (line 285)

**변경 전**:
```python
self.warehouse_columns = [
    "DHL Warehouse",  # 문제!
    "DSV Indoor",
    ...
]
```

**변경 후**:
```python
self.warehouse_columns = [
    "DHL WH",  # 수정!
    "DSV Indoor",
    ...
]
```

**이유**:
- Stage 1의 core module은 "DHL Warehouse" → "DHL WH"로 정규화
- Stage 2/3/4 모두 "DHL WH" 사용해야 함

## 검증 결과

### Before (수정 전)
```
HITACHI 파일 창고 컬럼 분석:
    DHL Warehouse: 컬럼 없음 - 빈 컬럼 추가
통합 데이터 컬럼 검증:
    DHL Warehouse: 0건 데이터
입고 계산: 5,299건
```

### After (수정 후)
```
HITACHI 파일 창고 컬럼 분석:
    DHL WH: 102건 데이터  ✅
통합 데이터 컬럼 검증:
    DHL WH: 102건 데이터  ✅
입고 계산: 5,401건  ✅ (+102건)
```

### 전체 파이프라인 실행
```
Stage 1: 36.05초
Stage 2: 15.53초
Stage 3: 114.61초
Stage 4: 50.36초
총 실행 시간: 216.57초 (약 3분 37초)

✅ 모든 스테이지 성공!
```

## 영향 분석

### 데이터 무결성
- **DHL WH 데이터**: 102건 복구
- **입고 계산**: +102건 증가 (5,299 → 5,401)
- **Rate 모드 과금**: +33건 증가 (165 → 198)

### 파이프라인 일관성
- ✅ Stage 1 → Stage 2 → Stage 3 데이터 흐름 복원
- ✅ Core module의 column normalization 효과 적용
- ✅ 모든 warehouse columns 통일 ("DHL WH")

## 교훈

### 1. 파일 경로 관리
- **문제**: 독립 실행 스크립트를 파이프라인에 통합 시 경로 불일치
- **해결**: `PIPELINE_ROOT` 기반 상대 경로 사용
- **패턴**: `Path(__file__).resolve().parents[2]`

### 2. 컬럼명 일관성
- **문제**: 여러 파일에서 동일 컬럼을 다른 이름으로 참조
- **해결**: Core module의 정규화된 이름 사용
- **패턴**: Stage 1의 output이 canonical name

### 3. 데이터 흐름
- **원칙**: Stage N은 Stage N-1의 output을 입력으로 사용
- **검증**: 각 Stage의 입력 경로가 이전 Stage의 output 경로와 일치

## 권장 사항

### 즉시 적용
1. ✅ 모든 warehouse columns을 "DHL WH"로 통일
2. ✅ Stage 3가 `data/processed/derived/` 읽도록 수정

### 향후 개선
1. **중앙 집중식 경로 관리**:
   ```python
   # config/paths.py
   STAGE1_OUTPUT = "data/processed/synced/"
   STAGE2_OUTPUT = "data/processed/derived/"
   STAGE3_OUTPUT = "data/processed/reports/"
   ```

2. **컬럼명 검증 테스트**:
   ```python
   def test_column_consistency():
       """모든 Stage가 동일한 warehouse columns 사용하는지 검증"""
       assert stage1_cols == stage2_cols == stage3_cols
   ```

3. **자동화된 통합 테스트**:
   ```bash
   pytest tests/integration/test_stage_data_flow.py
   ```

## 결론

✅ **문제 완전 해결**:
- Stage 3가 올바른 파일 경로에서 데이터 읽음
- 모든 warehouse columns 통일됨
- DHL WH 데이터 102건 복구
- 전체 파이프라인 정상 작동

✅ **데이터 무결성 보장**:
- Stage 1 → 2 → 3 → 4 완전한 데이터 흐름
- Core module의 semantic matching 효과 적용
- 색상 시각화 정상 작동

🎉 **HVDC Pipeline v4.0.2 안정화 완료!**






