# FEBRUARY 2025_rev2.xlsm 파일 구조 분석 보고서

**분석일**: 2025-10-16  
**파일명**: `SCNT SHIPMENT DRAFT INVOICE (FEBRUARY 2025)_rev2.xlsm`

---

## 📋 Executive Summary

FEBRUARY 2025_rev2.xlsm 파일은 기존 FEBRUARY 2025.xlsm과 **완전히 다른 구조**를 가지고 있습니다:

1. **FEB 시트**: 통합 요약 시트 (22개 인보이스 요약)
2. **개별 인보이스 시트**: 20개 (SCT, SEI, HE, SIM, ZEN 등)
3. **기타 시트**: Sheet2, Sheet3, SUMMARY, InvoiceData 등

**주요 발견**:
- FEB 시트는 **통합 요약 데이터**로 개별 시트들의 합계를 보여줌
- 개별 시트들은 기존 FEBRUARY 2025.xlsm의 "Renamed_" 시트들과 **동일한 내용**
- **헤더 구조가 완전히 다름**: Row 6에 복합 헤더 (여러 줄 텍스트 포함)

---

## 📊 파일 구조

### 전체 시트 목록 (총 28개)

| 번호 | 시트명 | Rows | Cols | 타입 |
|-----|--------|------|------|------|
| 1 | Sheet3 | 31 | 8 | 기타 |
| 2 | Sheet2 (2) | 36 | 7 | 기타 |
| 3 | **FEB** | 42 | 29 | **통합 요약** ⭐ |
| 4 | SUMMARY | 23 | 3 | 요약 |
| 5 | Sheet2 | 26 | 12 | 기타 |
| 6 | InvoiceData | 146 | 14 | 데이터 |
| 7-28 | SCT0037, SCT0029, SEI0017-1, ... | 50-60 | 20-21 | **개별 인보이스** |

### 인보이스 시트 (20개)

1. SCT0037 (56 rows)
2. SCT0029 (50 rows)
3. SEI0017-1 (50 rows)
4. SEI0019 (50 rows)
5. SCT0038 (60 rows)
6. SCT0039 (49 rows)
7. SCT0042 (56 rows)
8. Novatech (50 rows)
9. HE-0267 (50 rows)
10. HE-0290 (50 rows)
11. HVDC-SCT-RE-0003 (50 rows)
12. SIM-0036 (53 rows)
13. SIM-0037 (51 rows)
14. HE0254,0255 (50 rows)
15. HE0256,0257 (50 rows)
16. SCT0048 (50 rows)
17. SEI0017-3 (50 rows)
18. ZEN0013 (50 rows)
19. ZEN0006 (50 rows)
20. SCT0056 (50 rows)
21. HE-0302 (50 rows)
22. HE-0307 (50 rows)

---

## 🔍 FEB 시트 상세 구조

### 헤더 구조 (Row 6)

**복합 헤더 (여러 줄 텍스트 포함)**:

| Col | 헤더명 | 설명 |
|-----|--------|------|
| 2 | S/No | 일련번호 |
| 3 | Shipment Reference# | 주문 번호 |
| 4 | Type | 타입 (SHIPMENT) |
| 5 | Job # | CWI Job Number |
| 6 | BL # | Bill of Lading 번호 |
| 7 | POL | Port of Loading |
| 8 | POD | Port of Discharge |
| 9 | Mode | 운송 모드 (CNTR/AIR) |
| 10 | No. Of CNTR | 컨테이너 수 |
| 11 | Volume | 부피 |
| 12 | Quantity | 수량 |
| 13 | BOE | Bill of Entry |
| 14 | BOE Issued Date | BOE 발급일 |
| 15 | # Trips | 트립 수 |
| 16 | **MASTER DO CHARGE** | 마스터 DO 요금 |
| 17 | **CUSTOMS CLEARANCE CH** | 통관 요금 |
| 18 | **HOUSE DO CHARGE (BL)** | 하우스 DO 요금 |
| 19 | **PORT HANDLING CHARGE** | 항만 처리 요금 |
| 20 | **TRANSPORTATION CHARG** | 운송 요금 1 |
| 21 | **TRANSPORTATION CHARG** | 운송 요금 2 |
| 22 | **ADDITIONAL AMOUNT (P)** | 추가 금액 |
| 23 | **AT COST AMOUNT** | At Cost 금액 |
| 24 | **GRAND TOTAL (USD)** | 총합계 |
| 25 | Remarks | 비고 |
| 26 | **GRAND TOTAL (USD)** | 총합계 (검증용) |
| 27 | DIFFERENCE | 차이 |
| 28 | Original | 원본 |

### 데이터 구조 (Row 7-28)

**22개 인보이스 요약 데이터**:

| S/No | Shipment Ref | Job # | MASTER DO | CUSTOMS | PORT HANDLING | TRANSPORT | AT COST | GRAND TOTAL |
|------|--------------|-------|-----------|---------|---------------|-----------|---------|-------------|
| 1 | HVDC-ADOPT-SCT-0037 | BAMF0014693 | 150 | 150 | 1916 | 1008 | 326.08 | 3550.08 |
| 3 | HVDC-ADOPT-SEI-0017- | BAMF0014895 | 150 | 150 | 1330 | 756 | 966.77 | 3352.77 |
| 4 | HVDC-ADOPT-SEI-0019 | BAMF0014720 | 150 | 150 | 372 | 423 | 250.17 | 1345.17 |
| 5 | HVDC-ADOPT-SCT-0038 | BAMF0014962 | 150 | 150 | 3246 | 1764 | 561.20 | 5871.20 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Row 30: 총합계**
- GRAND TOTAL (USD): **61,934.82**

---

## 🔄 개별 인보이스 시트 구조

### 표준 구조 (예: SCT0037)

**헤더 위치**: Row 8  
**데이터 시작**: Row 9

#### 헤더 컬럼 (Col 2-15)

| Col | 헤더명 | 설명 |
|-----|--------|------|
| 2 | S/No | 일련번호 |
| 3 | **RATE SOURCE** | 요금 출처 ⭐ |
| 4 | **DESCRIPTION** | 설명 |
| 5 | **RATE** | 요금 |
| 6 | Formula | 계산식 |
| 7 | Q'TY | 수량 |
| 8 | **TOTAL (USD)** | 합계 |
| 9 | REMARK | 비고 |
| 10 | REV RATE | 검토 요금 |
| 11 | REV TOTAL | 검토 합계 |
| 12 | DIFFERENCE | 차이 |
| 14 | Invoice Line It | 인보이스 라인 |
| 15 | Calculation Log | 계산 로그 |

#### 메타데이터 (Row 2-6)

| Row | 내용 |
|-----|------|
| 2 | Bill to: / Draft Invoice Date: 2025-10-16 |
| 3 | SAMSUNG C&T CORPORATION / Customer ID: 6410059266 |
| 4 | P.O. Box 42654 / CW1 Job Number: BAMF0014693 |
| 5 | Abu Dhabi, UAE / Order Ref. Number: HVDC-ADOPT-SCT-0037 |
| 6 | MBL Number: SELA78951600 |

#### 샘플 데이터 (Row 9-15)

| S/No | RATE SOURCE | DESCRIPTION | RATE | Q'TY | TOTAL (USD) |
|------|-------------|-------------|------|------|-------------|
| 1 | Contract | Master DO Charges | 150 | 1 | 150 |
| 2 | Contract | Customs Clearance Charges | 150 | 1 | 150 |
| 3 | Contract | Terminal Handling Charges | 479 | 4 | 1916 |
| 4 | Contract | Transportation Charges | 252 | 4 | 1008 |
| 5 | At Cost | Carrier Container Release | 8 | 4 | 32 |
| 6 | At Cost | Carrier Container Inspection | 35.4 | 4 | 141.6 |
| 7 | At Cost | Carrier Container Additional | 9.53 | 4 | 38.12 |

---

## ⚠️ 기존 FEBRUARY 2025.xlsm과의 차이점

### 1. 파일명 차이
- **기존**: `SCNT SHIPMENT DRAFT INVOICE (FEBRUARY 2025).xlsm`
- **신규**: `SCNT SHIPMENT DRAFT INVOICE (FEBRUARY 2025)_rev2.xlsm`

### 2. 시트명 차이
- **기존**: "Renamed_SCT0037", "Renamed_SCT0029", ...
- **신규**: "SCT0037", "SCT0029", ... (Renamed_ 접두사 제거)

### 3. 추가 시트
- **FEB**: 통합 요약 시트 (신규 추가) ⭐
- **InvoiceData**: 146행 데이터 시트 (신규 추가)
- **SUMMARY**: 23행 요약 시트 (신규 추가)

### 4. 데이터 내용
- 개별 인보이스 데이터는 **동일**
- 시트명만 변경 (Renamed_ 제거)
- 추가 메타데이터 시트 포함

---

## 🎯 통합 처리 방안

### 옵션 1: FEB 시트만 통합
**장점**:
- 22개 인보이스의 요약 데이터를 한 번에 통합
- 빠른 처리 (1개 시트만 읽기)

**단점**:
- 상세 데이터 (S/No, RATE SOURCE, DESCRIPTION 등) 누락
- 헤더 구조가 다름 (Col 16-23이 요금 컬럼)

### 옵션 2: 개별 시트 통합 (기존 방식)
**장점**:
- 기존 통합 로직 재사용 가능
- 상세 데이터 모두 확보 (RATE SOURCE 포함)

**단점**:
- 20개 시트 개별 처리 필요
- 기존 FEBRUARY 2025.xlsm과 중복 가능성

### 옵션 3: 기존 FEBRUARY 2025.xlsm 교체
**장점**:
- 최신 데이터로 업데이트
- 중복 방지

**단점**:
- 기존 통합 데이터 재생성 필요
- 데이터 비교 필요 (내용이 동일한지 확인)

---

## 📈 데이터 품질 분석

### FEB 시트 데이터 품질

| 항목 | 값 | 비고 |
|------|-----|------|
| 총 인보이스 수 | 22개 | Row 7-28 |
| 데이터 완전성 | 100% | 모든 필수 컬럼 존재 |
| GRAND TOTAL | 61,934.82 USD | 총합계 |
| S/No | 1-22 (일부 누락) | S/No 2 누락 |

### 개별 시트 데이터 품질

| 항목 | 값 | 비고 |
|------|-----|------|
| 헤더 위치 | Row 8 | 모든 시트 일관성 |
| RATE SOURCE | 100% 존재 | Col 3 |
| DESCRIPTION | 100% 존재 | Col 4 |
| RATE | 100% 존재 | Col 5 |
| TOTAL (USD) | 100% 존재 | Col 8 |

---

## 🔧 권장 조치

### 1. 즉시 조치
- **기존 FEBRUARY 2025.xlsm과 데이터 비교**:
  - 내용이 동일한지 확인
  - 차이가 있다면 어느 것이 최신인지 확인

### 2. 통합 방안
- **옵션 A (권장)**: _rev2 파일의 개별 시트를 기존 통합 로직으로 처리
  - `invoice_consolidator_v2.py`가 자동으로 "Renamed_" 없는 시트명 처리 가능
  - RATE SOURCE 99.6% 확보 가능
  
- **옵션 B**: 기존 FEBRUARY 2025.xlsm을 _rev2로 교체 후 재통합
  - 전체 14개월 재통합 필요
  - 약 2-3분 소요

### 3. FEB 시트 활용
- 통합 검증용으로 활용:
  - 개별 시트 통합 결과와 FEB 시트의 GRAND TOTAL 비교
  - 차이가 있다면 데이터 오류 가능성

---

## 📝 결론

1. **FEBRUARY 2025_rev2.xlsm은 기존 파일의 개정판**:
   - 시트명 정리 (Renamed_ 제거)
   - 통합 요약 시트(FEB) 추가
   - 데이터 내용은 동일할 가능성 높음

2. **헤더 구조는 기존 통합 로직과 호환**:
   - 개별 시트: Row 8에 헤더 (기존과 동일)
   - RATE SOURCE, DESCRIPTION, RATE, TOTAL (USD) 모두 존재
   - Robust Header Detection으로 자동 처리 가능

3. **통합 권장 방안**:
   - 기존 FEBRUARY 2025.xlsm과 내용 비교
   - 동일하면 무시 (이미 통합됨)
   - 다르면 _rev2로 교체 후 재통합

---

**작성 완료**: 2025-10-16  
**분석 도구**: `check_feb_rev2_structure.py`, `check_feb_sheet.py`

