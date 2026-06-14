# 파이프라인 단계별 실행 스크립트 모음

이 폴더는 OFCO 파이프라인의 단계별 실행 스크립트 사본을 포함합니다.

## 파일 구조

### 전체 파이프라인 실행
- `00_run_full_pipeline.py` - 전체 파이프라인 실행 (Step 1-7) 및 통합

### 메인 파이프라인
- `01_ofco_pdf_to_complete_pipeline.py` - PDF → Complete Pipeline 변환
- `02_ofco_complete_pipeline_v2.py` - Complete Pipeline v2.0 (Phase 1-3)

### 단계별 스크립트

#### Step 1: PDF 파싱
- `step01_ofco_parse_pdf_patched.py` - PDF 파싱

#### Step 3: Phase 1 - Standard Lines
- `step03_ofco_to_standard_lines_excel.py` - Standard Lines 형식 변환

#### Step 4: Phase 2 - 매핑
- `step04_ofco_mapping_v3.py` - Cost/Price Center 매핑 v3
- `step04_ofco_map_price_center.py` - Price Center 매핑

#### Step 6: Phase 3 - EA Slots
- `step06_ofco_ea_allocator_v1p3.py` - EA 할당 v1.3
- `step06_ofco_ea_slot_v13.py` - EA 슬롯 알고리즘 v1.3

#### Step 7: 최종 통합
- `step07_ofco_integrate_pipeline_to_excel.py` - 파이프라인 결과 → OFCO INVOICE.xlsx 통합
- `step07_ofco_integrate_excel.py` - Excel 통합 (구버전)
- `step07_ofco_to_list_excel.py` - LIST 시트 추가
- `step07_validate_integration.py` - 통합 검증

### 공유 모듈
- `shared_ofco_header_core.py` - HeaderCore 모듈 (컬럼 순서 관리)

### 분석 보고서
- `OFCO_INVOICE_INTEGRATION_FLOW.md` - 6단계 통합 프로세스 흐름도
- `OFCO_INVOICE_INTEGRATION_MAPPING_REPORT.md` - 컬럼 매핑 상세 규칙
- `OFCO_INVOICE_STRUCTURE_DETAILED_ANALYSIS.md` - 구조 상세 분석
- `M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md` - M:CV ↔ DA:DH 상관관계 분석

## 사용 방법

### 전체 파이프라인 실행
```bash
python 00_run_full_pipeline.py <pdf_file> [--integrate] [--target "OFCO INVOICE.xlsx"]
```

### 개별 단계 실행
각 스크립트는 독립적으로 실행 가능하지만, 전체 파이프라인을 통한 실행을 권장합니다.

## 원본 파일 위치

- 메인 파이프라인: `pipeline_docs/main/`
- 단계별 스크립트: `pipeline_docs/pipeline_steps/step_XX_*/scripts/`
- 공유 모듈: `pipeline_docs/shared/scripts/`

## 주의사항

이 폴더의 파일들은 **사본**입니다. 원본 파일을 수정하면 이 사본도 업데이트해야 합니다.

