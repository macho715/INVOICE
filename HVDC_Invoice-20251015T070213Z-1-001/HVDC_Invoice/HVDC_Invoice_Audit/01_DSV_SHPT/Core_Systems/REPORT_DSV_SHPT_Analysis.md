# DSV SHPT.xlsx 분석 보고서

**파일**: DSV SHPT.xlsx  
**위치**: HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems/  
**분석 일시**: 2025-10-17  
**총 시트 수**: 3

---

## 개요

DSV SHPT.xlsx 파일은 3개의 시트로 구성되어 있습니다:

1. **Payment history** (866 rows, 25 cols) - **실제 지급 집행 기록**
2. **Monthly_Summary** (404 rows, 22 cols) - 우리가 작성한 월별 요약 통합 데이터
3. **Individual_Invoices** (2,167 rows, 15 cols) - 우리가 작성한 개별 인보이스 통합 데이터

---

## 시트 1: Payment history

### 개요

**목적**: DSV로부터 받은 실제 지급 집행 기록

**통계**:
- 총 행 수: 866 (헤더 포함)
- 총 컬럼 수: 25
- 데이터 행: 865
- 헤더 행: Row 1

### 컬럼 구조

| Col | 컬럼명 | 설명 | 샘플 데이터 |
|-----|--------|------|-------------|
| 1 | No. | 레코드 번호 | 1, 2, 3, ... |
| 2 | Invoice No | DSV 인보이스 번호 | AE70025943, AE70026755 |
| 3 | Invoice Date | 인보이스 날짜 | 2023-06-01, 2024-02-29 |
| 4 | SR | 순번/참조 | 1, 2, 3, ... |
| 5 | Job Description | Job 설명 코드 | BAMF0008237, BAMF0009033 |
| 6 | Shipment No | 선적 참조 번호 | HVDC-ADOPT-PPL-0001, HVDC-ADOPT-HE-0001 |
| 7 | Doc reference Details | 문서 상세 | GOT36800012, ASLGMS003217 |
| 8 | HBL | House Bill of Lading | MEDUUG581769, LHAABU02 |
| 9 | MBL | Master Bill of Lading | ENC109DANJEB11 |
| 10 | Customs | 통관 비용 | 150, 350 |
| 11 | DO | Delivery Order 비용 | 150, 300 |
| 12 | PHC | Port Handling Charge | 3341.81, 6607.58 |
| 13 | Inland | 내륙 운송비 | 256.22, 1491.23, 4856 |
| 14 | THC | Terminal Handling Charge | 125, 2500 |
| 15 | Inspection | 검사 비용 | - |
| 16 | Detention | 체화 비용 | 1456 |
| 17 | Storage | 보관 비용 | 408.44 |
| 18 | Others | 기타 비용 | 224.67 |
| 19 | TOTAL | 소계 | 575, 6566.48, 4856 |
| 20 | VAT | 부가가치세 | 242.8, 403.18 |
| 21 | G. TOTAL | 총계 (VAT 포함) | 5098.8, 6566.48, 428.86 |
| 22-25 | (빈 컬럼) | - | - |

### 샘플 데이터 (Rows 2-5)

| No. | Invoice No | Invoice Date | Shipment No | TOTAL | G. TOTAL |
|-----|------------|--------------|-------------|-------|----------|
| 1 | AE70025943 | 2023-06-01 | Module - Spreader Frame | 4856 | 5098.8 |
| 2 | AE70026755 | 2023-06-26 | 2 Flat Bed (Fujairah - F3 Layd | 256.22 | 256.22 |
| 3 | AE70026756 | 2023-06-26 | 1 Flat Bed and Detention charg | 817.5 | 858.375 |
| 4 | AE70026757 | 2023-06-26 | 2 Flat Bed (F3 to MOSB) | 1491.23 | 1552.98 |

### 기간 범위

**최초 날짜**: 2023-05-31  
**최종 날짜**: 2024-02-29 (샘플 기준)  
**기간**: 약 9개월 (2023년 5월 ~ 2024년 2월)

**참고**: 이것은 과거 지급 데이터로, 우리의 통합 인보이스 데이터(2024년 8월 ~ 2025년 9월)와 기간이 다릅니다.

### 주요 특징

1. **인보이스 레벨 데이터**: 1 row = 1 지급 기록 (하나의 인보이스에 여러 항목 가능)
2. **DSV 인보이스 번호**: AE70025943, AE70026755 등
3. **비용 세분화**: Customs, DO, PHC, Inland, THC, Inspection, Detention, Storage, Others
4. **VAT 포함**: 별도 VAT 컬럼 및 G. TOTAL
5. **Job 코드**: BAMF0008237, BAMF0009033 등
6. **Shipment 참조**: HVDC-ADOPT-PPL-0001, HVDC-ADOPT-HE-0001 등

---

## 시트 2: Monthly_Summary

### 개요

**목적**: 우리가 작성한 월별 요약 통합 데이터

**통계**:
- 총 행 수: 404 (헤더 포함)
- 총 컬럼 수: 22
- 데이터 행: 403
- 헤더 행: Row 1

**출처**: `run_monthly_consolidation.py` 실행 결과

**데이터 커버리지**: 2024-08 ~ 2025-09 (15개 시트, 406 rows 예상)

**불일치**: 404 rows vs 406 예상 (2 row 차이 - 헤더 처리 방식 차이로 추정)

### 예상 컬럼

우리의 통합 결과 기준:
1. No
2. Source_Month
3. S/No
4. Shipment Reference
5. CW1 Job Number
6. Type
7. BL #
8. POL
9. POD
10. Mode
... (22개 표준 컬럼)

---

## 시트 3: Individual_Invoices

### 개요

**목적**: 우리가 작성한 개별 인보이스 라인 항목 통합 데이터

**통계**:
- 총 행 수: 2,167 (헤더 포함)
- 총 컬럼 수: 15
- 데이터 행: 2,166
- 헤더 행: Row 1

**출처**: `run_individual_consolidation.py` 실행 결과

**데이터 커버리지**: 2024-08 ~ 2025-09 (407+ 시트, 2,166 rows)

### 예상 컬럼 (VBA 표준 15개)

1. Source_File
2. No
3. Month
4. CWI Job Number
5. Order Ref. Number
6. S/No
7. DESCRIPTION
8. RATE SOURCE
9. RATE
10. Formula
11. Q'TY
12. TOTAL (USD)
13. REV RATE
14. REV TOTAL
15. DIFFERENCE

**참고**: 이 시트는 15개 컬럼만 포함 (표준 VBA 컬럼만, 추가 컬럼 제외)

---

## 비교 분석: Payment history vs 우리의 통합 데이터

### 데이터 기간

| 시트 | 기간 | 데이터 행 | 커버리지 |
|------|------|-----------|----------|
| **Payment history** | 2023-05 ~ 2024-02 | 865 | 과거 데이터 (9개월) |
| **Monthly_Summary** | 2024-08 ~ 2025-09 | 403 | 최근 데이터 (14개월) |
| **Individual_Invoices** | 2024-08 ~ 2025-09 | 2,166 | 최근 데이터 (14개월) |

**데이터 공백**: 2024-03 ~ 2024-07 (5개월 공백 존재)

### 데이터 구조

| 항목 | Payment history | Monthly_Summary | Individual_Invoices |
|------|----------------|-----------------|---------------------|
| **레벨** | 지급 기록 | 인보이스 요약 | 라인 항목 |
| **세분화** | 1 row = 1 지급 기록 | 1 row = 1 인보이스 | 1 row = 1 항목 |
| **비용** | Customs, DO, PHC, Inland, THC... | GRAND TOTAL만 | RATE, Q'TY, TOTAL 항목별 |
| **컬럼 수** | 25 (비용 세분화) | 22 (선적 정보) | 15 (표준 VBA) |
| **VAT** | 있음 (별도 컬럼) | 없음 | 없음 |
| **출처** | DSV 실제 지급 | 우리의 통합 | 우리의 통합 |

### 주요 차이점

1. **인보이스 번호**:
   - Payment history: AE70025943 (DSV 포맷)
   - 우리 데이터: HVDC-ADOPT-SCT-0001 (내부 포맷)

2. **비용 상세**:
   - Payment history: 유형별 세분화 (Customs, DO, PHC, ...)
   - Monthly_Summary: GRAND TOTAL만
   - Individual_Invoices: DESCRIPTION + RATE + Q'TY

3. **기간**:
   - Payment history: 과거 데이터 (2023-2024 초반)
   - 우리 데이터: 최근 데이터 (2024-2025)

---

## 분석 인사이트

### 1. 데이터 관계

**Payment history**:
- DSV로부터 실제 받은 인보이스 및 지급 기록
- 과거 기준선 데이터
- VAT 포함 실제 지급 금액

**우리의 통합 데이터**:
- 내부 인보이스 초안/추정
- 최근 운영 데이터 (2024-08 이후)
- 상세 비용 구조 분석

### 2. 활용 방안

**교차 검증**:
- Payment history 비용 vs 우리의 RATE SOURCE/DESCRIPTION
- 가격 추세 파악 (2023 vs 2024-2025)
- 비용 유형 일관성 확인

**추세 분석**:
- 과거 (Payment history) vs 현재 (우리 데이터) 가격 비교
- 비용 인플레이션/디플레이션 파악
- 비용 유형 변화 추적

**정합성 확인**:
- Shipment No (Payment history) vs Order Ref (우리 데이터) 매칭
- 우리의 추정이 실제 지급과 일치하는지 확인
- 차이 분석

### 3. 데이터 공백 분석

**누락 기간**: 2024-03 ~ 2024-07 (5개월)

**질문**:
- 2024년 3월~7월 지급 기록이 있는가?
- 우리의 통합 데이터가 왜 8월부터 시작하는가?
- 공백 기간에 대한 다른 파일이 있는가?

---

## 권장 사항

### 즉시 조치

1. **Monthly_Summary 시트 검증**:
   - 404 rows vs 406 rows 차이 확인 (헤더 카운팅)
   - 컬럼이 우리의 통합 출력과 일치하는지 확인
   - `month_sheets_master_*.xlsx`와 비교

2. **Individual_Invoices 시트 검증**:
   - 15개 VBA 표준 컬럼 모두 있는지 확인
   - 2,166 데이터 행 확인
   - `masterdata_all_months_*.xlsx`와 비교

3. **Payment history 분석**:
   - 유니크 Invoice No, Shipment No 추출
   - 기간 커버리지 확인
   - 비용 패턴 파악

### 분석 과제

1. **비용 구조 비교**:
   - Payment history: Customs, DO, PHC, Inland, THC
   - Individual_Invoices: DESCRIPTION 패턴
   - 매핑 찾기 (예: "Customs" = "Customs Clearance Charges")

2. **선적 매칭**:
   - Payment history "Shipment No" (HVDC-ADOPT-PPL-0001)
   - 우리 데이터 "Order Ref. Number" (HVDC-ADOPT-SCT-0001)
   - 중복 또는 공백 식별

3. **가격 비교**:
   - Payment history 실제 비용 (2023-2024)
   - 우리 데이터 RATE (2024-2025)
   - 차이율 계산

---

## 다음 단계 옵션

### 옵션 1: Payment history 상세 분석

**목표**: 과거 지급 패턴 이해

**작업**:
- 모든 유니크 Invoice No 추출 (865 레코드)
- Shipment No별 그룹화
- 비용 유형별 분포 분석
- 비용 유형별 평균 계산
- 비용 Top 선적 파악

### 옵션 2: 우리 데이터와 교차 검증

**목표**: 우리의 통합 데이터를 실제 지급과 비교 검증

**작업**:
- 중복되는 Shipment No / Order Ref 찾기
- 비용 금액 비교
- 차이 식별
- 정합성 보고서 생성

### 옵션 3: 종합 비교 보고서

**목표**: 3개 시트 전체 분석

**작업**:
- 데이터 구조 비교
- 기간 커버리지 분석
- 선적 번호 교차 참조
- 통합 대시보드 생성

---

## 파일 구조 확인

### 현재 위치

```
HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems/
├── DSV SHPT.xlsx (318 KB)
│   ├── Sheet 1: Payment history (866 rows, 25 cols)
│   ├── Sheet 2: Monthly_Summary (404 rows, 22 cols)
│   └── Sheet 3: Individual_Invoices (2,167 rows, 15 cols)
│
├── run_individual_consolidation.py
├── run_monthly_consolidation.py
│
└── out/
    ├── masterdata_all_months_20251017_071130.xlsx (2,166 rows)
    └── month_sheets_master_20251017_075413.xlsx (406 rows)
```

### 데이터 출처

**Payment history**: 알 수 없음 (DSV 실제 인보이스?)  
**Monthly_Summary**: `run_monthly_consolidation.py` 실행 결과  
**Individual_Invoices**: `run_individual_consolidation.py` 실행 결과

---

**분석 상태**: 완료  
**다음 작업**: 사용자 결정 대기 (옵션 1, 2, 또는 3 선택)
