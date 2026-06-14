# OFCO Parser CSV Export功能

## 概要

OFCO Parser에 CSV 출력 기능이 추가되어 파싱 결과를 엑셀에서 바로 열어볼 수 있는 테이블 형식으로 저장할 수 있습니다.

## 사용 방법

### 1. PDF에서 직접 CSV 생성

```bash
# CSV만 생성
python ofco_parser.py "OFCO-INV-0001178_Samsung.pdf" --csv invoice.csv

# JSON과 CSV 동시 생성
python ofco_parser.py "OFCO-INV-0001178_Samsung.pdf" --out invoice.json --csv invoice.csv
```

### 2. 기존 JSON에서 CSV 변환

```bash
# 독립 실행형 변환 스크립트
python json_to_csv.py invoice.json --out invoice.csv
```

## CSV 테이블 구조

### 헤더 (26개 컬럼)

| 컬럼명 | 설명 |
|--------|------|
| Invoice Number | 송장 번호 (예: OFCO-INV-0001178) |
| Date | 송장 날짜 (예: 15-Jul-2025) |
| Samsung Ref | Samsung 참조 번호 (예: B-SAMSG-0625-1) |
| VAT% | 부가세율 (예: 5.0) |
| Currency | 통화 (예: AED) |
| Total Amount | 총액 (예: 41375.75) |
| Vessel Name | 선박명 (BUSHRA 형식용) |
| Rotation No | 회전 번호 (BUSHRA 형식용) |
| Voyage No | 항해 번호 (BUSHRA 형식용) |
| GRT | 총톤수 |
| DWT | 재화중량톤수 |
| LOA | 전장 |
| Customer Reg No | 고객 등록 번호 |
| Item# | 항목 번호 (1부터 시작) |
| Subject | 항목 설명 |
| EA | 수량 |
| Rate | 단가 |
| Amount (AED) | 금액 (부가세 제외) |
| Cost Main | 주요 비용 분류 |
| Cost Center A | 비용 센터 A |
| Cost Center B | 비용 센터 B |
| Price Center | 가격 센터 |
| UOM | 단위 (예: LS, HRS) |
| Tax Rate | 세율 (예: 5%, 15%) |
| Total Incl VAT | 부가세 포함 총액 |
| Notes | 추가 정보 |

### 데이터 행

- 각 Line Item이 하나의 행으로 표시됨
- Invoice Metadata가 모든 행에 반복됨 (엑셀 필터링/피벗 테이블 용이)

### Audit Summary (마지막 부분)

```
[빈 행]
AUDIT SUMMARY:
Items Total:           41294.07
Invoice Total:         41375.75
Deviation %:           0.2
Within Tolerance:      PASS
EA×Rate Checks Passed: 45/45
```

## 출력 예시

### Samsung OFCO 송장 (OFCO-INV-0001178)

- **총 행 수**: 53행 (헤더 1 + 데이터 45 + 빈행 1 + Audit 6)
- **총 항목**: 45개
- **Audit 상태**: PASS (편차 0.2%)
- **파일 크기**: ~25KB

### 컬럼 예시 (첫 번째 항목)

```csv
OFCO-INV-0001178,15-Jul-2025,B-SAMSG-0625-1,5.0,AED,41375.75,VAT,2501019241,B-SAMSG-0625-1,929.00,1063.07,64.0000,006450,1,Agency fee: Berthing Arrangement...,1.0,490.13,490.13,CONTRACT,CONTRACT(AF FOR BA),CONTRACT,AGENCY FEE FOR BERTHING ARRANGEMENT,LS,15%,514.64,UOM=LS; VAT=15%; TotalInclVAT=514.64
```

## 엑셀에서 활용

### 1. CSV 파일 열기

Excel에서 CSV 파일을 열면 자동으로 컬럼이 분리됩니다.

### 2. 권장 활용법

- **필터링**: 상단 헤더 행에서 필터 적용 (Cost Main, Cost Center A 등)
- **피벗 테이블**: 비용 센터별 집계, 항목별 금액 분석
- **조건부 서식**: Amount 컬럼에 색상 적용
- **정렬**: Amount 기준 내림차순 정렬로 주요 항목 확인

### 3. UTF-8 BOM 인코딩

CSV 파일은 `utf-8-sig` 인코딩으로 저장되어 Excel에서 한글이 깨지지 않습니다.

## 파일 구조

```
OFCO_Collection/
├── ofco_parser.py              # 메인 파서 (CSV 출력 기능 포함)
├── json_to_csv.py              # 독립 실행형 JSON→CSV 변환기
├── samsung_invoice.csv         # 출력 예시 (Samsung 형식)
└── CSV_EXPORT_README.md        # 이 문서
```

## 기술 사양

- **CSV 라이브러리**: Python 표준 `csv` 모듈
- **인코딩**: UTF-8 with BOM (utf-8-sig)
- **줄바꿈**: Windows/Mac/Linux 호환 (`newline=''`)
- **따옴표 처리**: 자동 (컬럼에 쉼표 포함 시)

## 버전 정보

- **OFCO Parser**: v0.9
- **CSV Export**: v1.0
- **최종 업데이트**: 2025-01-28

## 지원 형식

1. **Samsung OFCO 형식**: 복잡한 다중 라인 테이블 ✅
2. **BUSHRA 선박 형식**: 단순한 테이블 + Vessel 정보 ✅

## 추가 기능

향후 추가 가능한 기능:
- Excel (.xlsx) 직접 출력 (openpyxl 사용)
- 복수 PDF 일괄 처리
- 사용자 정의 컬럼 선택
- 차트/그래프 자동 생성

## 문의

문제가 발생하거나 개선 제안이 있으면 이슈를 등록해 주세요.

---

**🎊 OFCO Parser v0.9 - 완벽한 CSV 출력 지원!**


