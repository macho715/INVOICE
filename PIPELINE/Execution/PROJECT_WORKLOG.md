# OFCO 파이프라인 작업 로그 (2025-11-09)

본 문서는 `OFCO-INV-0001178` 케이스를 중심으로 진행한 로컬 검증, 코드 패치, 실행 결과를 상세히 기록한다.

---

## 1. 초기 분석 및 문서 확인
- 참조 문서
  - `OFCO_COMPREHENSIVE_ANALYSIS.md`
  - `M_CV_DA_DH_RELATIONSHIP_ANALYSIS.md`
- 주요 확인사항
  - 단계 구성: PDF 파싱 → Standard Lines → Cost/Price Center → EA → 통합/검증
  - M:CV ↔ DA:DH 변환 규칙 및 검증 항목 파악

---

## 2. 단계별 실행 검증 (수동 실행)
실행 경로: `data/OFCO-INV-0001178_Samsung.pdf`

| 단계 | 실행 명령 | 주요 결과 |
|------|-----------|-----------|
| Step 1 | `python step01_ofco_parse_pdf_patched.py ...` | 46개 항목 추출, 중복 제거 정상 확인 |
| Step 3 | `step03_ofco_to_standard_lines_excel.py` (모듈 수동 로드) | `temp_step03.xlsx` 생성, Standard Lines 스키마 검증 |
| Phase1~3 Core | `02_ofco_complete_pipeline_v2.py` (모듈 수동 로드) | Phase 1→2→3 순차 실행, Price Center→EA 변환 로직 확인 |
| Step 6 | `python step06_ofco_ea_slot_v13.py` | EA 알고리즘 정상 기동(버전 출력) |
| Step 7 통합 | `step07_ofco_integrate_pipeline_to_excel.py` (소스 `temp_step03.xlsx`) | `temp_OFCO.xlsx`에 통합 |
| Step 7 검증 | `python step07_validate_integration.py ...` | 6개 검증 항목 모두 PASS |

→ 해당 내용은 `PIPELINE_STEP_VERIFICATION.md`에 요약 본으로 기록.

---

## 3. Phase C 패치 적용
### 대상
- `step07_ofco_integrate_pipeline_to_excel.py`

### 변경 사항
- 기존 `except Exception` 단일 블록을 아래와 같이 세분화:
  - `FileNotFoundError`
  - `PermissionError` (롤백 시도 포함)
  - `pd.errors.EmptyDataError`
  - `KeyError`
  - `ValueError`
  - 기타 `Exception`
- 각 예외별 맞춤 메시지 및 롤백 처리 강화.
- `read_lints` 실행 결과: 새로운 lint 오류 없음.

---

## 4. 전체 파이프라인 재실행
### 실행 절차
1. 의존 모듈 수동 로드 (`temp_run_pipeline.py` 생성)
2. `python temp_run_pipeline.py`

### 실행 로그 요약
- Step 1~7 전체 성공 (`ofco_pipeline_pdf_OFCO_INV_0001178_v3.xlsx` 생성)
- `OFCO INVOICE.xlsx` 통합 및 백업(`.backup`) 생성
- 검증 경고: `calc_check` 15행, `vat_check` 46행 (`OFCO-INV-0001178` 특유의 금액 누락 이슈로 기존에 확인된 사항)
- 완료 메시지: `[SUCCESS] 전체 파이프라인 실행 완료`

---

## 5. 생성 / 업데이트된 주요 파일
- `PIPELINE_STEP_VERIFICATION.md` : 단계별 실행 검증 보고서
- `PROJECT_WORKLOG.md` : 본 작업 로그
- `step07_ofco_integrate_pipeline_to_excel.py` : Phase C 예외 처리 패치 반영
- 실행 산출물: `ofco_pipeline_pdf_OFCO_INV_0001178_v3.xlsx`, `OFCO INVOICE.xlsx` (동일 행수 유지), `OFCO INVOICE.xlsx.backup`

---

## 6. 현재 상태 요약
- 단계 검증 및 파이프라인 실행 모두 완료.
- Phase C 패치(예외 처리 강화) 적용 및 확인.
- 잔여 경고(`calc_check`, `vat_check`)는 원본 데이터 문제로 인한 것으로 문서와 동일.

---

## 7. 후속 권장 사항
1. `/logi-master invoice-audit` : 파이프라인 변경 이후 라인별 검증 재수행
2. `/system_status diagnostic` : 환경 및 설정 점검
3. `/automate test-pipeline` : 전체 파이프라인 재검증 및 캐시 초기화
4. (선택) `OFCO-INV-0001178` PDF 금액 데이터를 재확인하여 `calc_check` 경고 감소 방안 검토

---

## 8. PyMuPDF SAFEEN·ADP 추출기 패치 (2025-11-11)
- 적용 파일: `step01_ofco_parse_pdf_patched.py`
- 주요 변경
  - PyMuPDF `find_tables()` → `Table.extract()` 기반 SAFEEN·ADP 테이블 전용 추출 로직 추가
  - 헤더 동의어 매핑, ROI 클립(헤더 키워드 기준), VAT 5→0.05 정규화, `Invoice Total / Amount in Words` 등 푸터 제거
  - `OFCO_USE_PYMUPDF_EXTRACTOR` 환경 변수로 즉시 롤백 가능하도록 토글 추가
  - PyMuPDF 추출 결과를 기존 `build_items()` 흐름으로 연결하기 위한 변환 브리지 `_convert_pymupdf_records` 작성
- 검증
  - `py -m pip install --no-index --find-links wheels PyMuPDF pymupdf4llm tabulate`
  - `py -c "… extract_invoice_items_pymupdf('data/OFCO-INV-0001178_Samsung.pdf')"` : PyMuPDF 추출 레코드 확인
  - `py -c "… parse_ofco_invoice('data/OFCO-INV-0001178_Samsung.pdf')"` : 전체 파서 성공 및 67개 라인 아이템 산출
- 문서
  - patch 가이드(`patch5.md`) 반영, 롤백/검증 절차 본 로그에 기록 완료

---

## 9. PyMuPDF SAFEEN·ADP 추출기 안정화 리포트 (2025-11-11)
- 적용 파일: `step01_ofco_parse_pdf_patched.py`
- 주요 보강
  - 헤더 동의어 사전 확장 및 `_looks_like_line_table` 추가로 SAFEEN·ADP 전용 라인 테이블을 정확히 인식
  - ROI 자동 탐지(`_find_roi`)와 `Table.extract()` 기반 스코어링으로 다중 페이지 테이블을 안정적으로 획득
  - `parse_numeric()` 개선 및 `_harmonize_amounts()` 적용으로 `3,091 25 → 3091.25`, `·100.00 → 100.00` 등 스페이스·중점 혼용 숫자 보정
  - `_validate_rows()` 신뢰도 계산을 0.40 이상으로 재조정하여 합계·VAT가 일치하는 경우 PyMuPDF 경로를 유지, 실패 시 자동 텍스트 파서 폴백
  - 행 Dedup 로직과 기존 `build_items()` 브리지 유지로 기존 파이프라인 호환성 보장
- 검증
  - `py -c "from step01_ofco_parse_pdf_patched import extract_invoice_items_pymupdf; rows = extract_invoice_items_pymupdf(r'C:\pipeline_execution_scripts\SAFEEN_ADP.PDF'); print(len(rows))"`
  - `py -c "from step01_ofco_parse_pdf_patched import parse_ofco_invoice; payload = parse_ofco_invoice(r'C:\pipeline_execution_scripts\SAFEEN_ADP.PDF'); print(len(payload.items))"`
  - 추출 행 15건, PyMuPDF 경로 신뢰도 0.80으로 승인, 텍스트 폴백 미사용 경로 확인
- 후속 조치
  - `/automate test-pipeline` : 전체 파이프라인 회귀 검증 권장
  - `/logi-master invoice-audit` : SAFEEN/ADP 표준 시나리오 재검증

---

*작성자: MACHO-GPT v3.4-mini*  
*작성일: 2025-11-09*


