# HVDC PDF Parser System

**Version**: 1.0.0
**Last Updated**: 2025-10-13
**Author**: HVDC Logistics Team

---

## 📋 개요

HVDC 프로젝트 물류 서류를 자동으로 파싱하고 검증하는 통합 시스템입니다.

### 주요 기능

- **PDF 자동 파싱**: BOE, DO, DN, Carrier Invoice 등 다중 문서 처리
- **온톨로지 통합**: RDF 기반 의미론적 데이터 모델링
- **Cross-Document 검증**: 문서 간 일관성 자동 검증
- **규제 준수**: HS Code 기반 FANR/MOIAT 인증 자동 추론
- **워크플로우 자동화**: Telegram/Slack 알림, Demurrage Risk 체크

### 기대효과

| 항목 | 현재 | 목표 | 개선율 |
|------|------|------|--------|
| 처리 시간 | 4시간/BL | 15분/BL | 94% ↓ |
| 데이터 정확도 | 85% | 99% | 16% ↑ |
| 통관 지연 | 15-25% | 3-5% | 80% ↓ |

---

## 🚀 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 수정

`config.yaml` 파일을 프로젝트에 맞게 수정합니다:

```yaml
# 알림 설정
notifications:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    channel_id: "@hvdc-alerts"

# 파일 경로
files:
  paths:
    input_dir: "./input"
    output_dir: "./output"
```

---

## 📖 사용 방법

### CLI 사용

#### 단일 PDF 파싱

```bash
python praser.py input/HVDC-ADOPT-SCT-0126_BOE.pdf -o output/result.json
```

#### 폴더 전체 파싱

```bash
python praser.py "DSV 202509/SCNT Import (Sept 2025) - Supporting Documents" \
  --recursive \
  --output output/batch_result.json
```

#### 문서 타입 지정

```bash
python praser.py input/document.pdf --type BOE
```

### Python 코드에서 사용

#### 1. PDF 파싱

```python
from praser import DSVPDFParser

# 파서 초기화
parser = DSVPDFParser(log_level="INFO")

# PDF 파싱
result = parser.parse_pdf("input/BOE.pdf", doc_type="BOE")

print(f"Parsed: {result['header']['doc_type']}")
print(f"Data: {result['data']}")
```

#### 2. 온톨로지 매핑

```python
from ontology_mapper import OntologyMapper

# 매퍼 초기화
mapper = OntologyMapper()

# BOE 데이터를 온톨로지로 매핑
boe_data = {
    'dec_no': '20252101030815',
    'mbl_no': 'CHN2595234',
    'hs_code': '9405500000',
    'containers': ['CMAU2623154', 'TGHU8788690']
}

shipment_uri = mapper.map_boe_to_ontology(boe_data, 'HVDC-ADOPT-SCT-0126')

# RDF 통계
stats = mapper.get_graph_stats()
print(f"Total triples: {stats['total_triples']}")

# Turtle 형식으로 내보내기
mapper.export_to_turtle("output/ontology.ttl")
```

#### 3. Cross-Document 검증

```python
from cross_doc_validator import CrossDocValidator

# 검증기 초기화
validator = CrossDocValidator()

# 파싱된 문서들
documents = [
    {'doc_type': 'BOE', 'data': boe_data},
    {'doc_type': 'DO', 'data': do_data},
    {'doc_type': 'DN', 'data': dn_data}
]

# 검증 실행
report = validator.generate_validation_report('HVDC-ADOPT-SCT-0126', documents)

print(f"Status: {report['overall_status']}")
print(f"Issues: {report['total_issues']}")

for issue in report['all_issues']:
    print(f"  - {issue['type']}: {issue['details']}")
```

#### 4. 워크플로우 자동화

```python
from workflow_automator import WorkflowAutomator

# 자동화 초기화
automator = WorkflowAutomator(config_path="config.yaml")

# Demurrage Risk 체크
do_data = {
    'do_number': 'DOCHP00042642',
    'delivery_valid_until': '09/09/2025',
    'quantity': 3,
    'item_code': 'HVDC-ADOPT-SCT-0126'
}

risk = automator.check_demurrage_risk(do_data)

if risk:
    print(f"Risk Level: {risk['risk_level']}")
    print(f"Days Remaining: {risk['days_remaining']}")

# 검증 보고서 자동 플래그 및 알림
result = automator.auto_flag_inconsistencies(report)
print(f"Flagged: {result['flagged_count']} issues")
print(f"Notified: {result['notified_count']} alerts sent")
```

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                      │
│          CLI / Python API / FastAPI (Optional)          │
└─────────────────┬───────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  PDF Controller │
         │  (praser.py)    │
         └────┬──────┬─────┘
              │      │
     ┌────────▼──┐ ┌▼──────────┐
     │ OCR Engine│ │Ontology   │
     │ (Cloud)   │ │Mapper     │
     └─────┬─────┘ └─────┬─────┘
           │             │
      ┌────▼─────────────▼────┐
      │  Cross-Doc Validator  │
      │  (Consistency Check)  │
      └────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │  Workflow Automator     │
    │  - Alerts (Telegram)    │
    │  - Demurrage Check      │
    │  - Auto Flagging        │
    └─────────────────────────┘
```

---

## 📂 파일 구조

```
PDF/
├── praser.py                  # 메인 PDF 파서 (기존)
├── ontology_mapper.py         # RDF 온톨로지 매핑
├── cross_doc_validator.py     # 문서 간 검증
├── workflow_automator.py      # 워크플로우 자동화
├── config.yaml                # 시스템 설정
├── requirements.txt           # 의존성 패키지
├── test_pdf_system.py         # 통합 테스트
├── README.md                  # 이 파일
│
├── input/                     # 입력 PDF 파일
├── output/                    # 파싱 결과 및 RDF
│   ├── ontology/              # RDF Turtle 파일
│   └── reports/               # JSON 보고서
└── logs/                      # 로그 파일
```

---

## 🧪 테스트

### 전체 테스트 실행

```bash
pytest test_pdf_system.py -v
```

### 특정 테스트 클래스 실행

```bash
pytest test_pdf_system.py::TestOntologyMapping -v
```

### 커버리지 포함

```bash
pytest test_pdf_system.py --cov=. --cov-report=html
```

---

## 📊 지원 문서 타입

### 1. BOE (Bill of Entry) - UAE Customs 통관 신고서

**필수 필드**:
- `dec_no`: DEC No
- `mbl_no`: MBL/AWB No
- `hs_code`: HS Code
- `containers`: Container 번호 리스트
- `duty_aed`, `vat_aed`: 관세/VAT

### 2. DO (Delivery Order) - 선사 배송 지시서

**필수 필드**:
- `do_number`: D.O. Number
- `mbl_no`: MBL No
- `containers`: Container 및 Seal 번호
- `delivery_valid_until`: 유효기한

### 3. DN (Delivery Note) - 창고/현장 운송 기록

**필수 필드**:
- `waybill_no`: Waybill Number
- `container_no`: Container Number
- `loading_date`: 적재 일자
- `driver_name`: 운전자

### 4. CarrierInvoice - 선사 청구서

**필수 필드**:
- `invoice_number`: Invoice Number
- `bl_number`: B/L Number
- `total_incl_tax`: 총액

---

## 🔧 고급 설정

### OCR 엔진 활성화 (선택사항)

#### AWS Textract

```yaml
ocr:
  engines:
    - name: "AWS Textract"
      enabled: true
      confidence_threshold: 0.95
```

환경변수 설정:
```bash
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Google Document AI

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Telegram 봇 설정

1. BotFather에서 봇 생성: https://t.me/BotFather
2. Token 획득
3. `config.yaml`에 설정:

```yaml
notifications:
  telegram:
    enabled: true
    bot_token: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    channel_id: "@hvdc-alerts"
```

### SPARQL 엔드포인트 연동

```yaml
ontology:
  sparql_endpoint: "http://localhost:3030/hvdc/query"
```

---

## 🔍 검증 규칙

### Cross-Document 검증

| 규칙 | 검증 내용 | 허용 오차 |
|------|-----------|-----------|
| **MBL 일치** | BOE ↔ DO ↔ DN 간 MBL 번호 | 정확히 일치 |
| **Container 일치** | BOE ↔ DO ↔ DN 간 Container 번호 | 정확히 일치 |
| **Weight 일치** | BOE ↔ DO 간 Gross Weight | ±3% |
| **Quantity 일치** | BOE ↔ DO 간 수량 | 정확히 일치 |
| **Date 논리** | CI.date ≤ PL.date ≤ BL.etd | 순서 준수 |

### 규제 준수 규칙

| 규제 | 조건 | Lead Time |
|------|------|-----------|
| **MOIAT** | HS Code 84xx, 85xx | 14일 |
| **FANR** | HS Code 2844xx 또는 "nuclear" keyword | 30일 |
| **DCD** | Hazmat keywords | 21일 |

---

## 🔧 문제 해결

### 오류: "pdfplumber not installed"

```bash
pip install pdfplumber PyPDF2
```

### 오류: "RDFlib not found"

```bash
pip install rdflib>=7.0.0
```

### OCR 신뢰도가 낮을 때

1. PDF 품질 확인 (최소 300 DPI)
2. 스캔본이면 이미지 전처리 수행
3. `config.yaml`에서 `confidence_threshold` 조정

### Telegram 알림이 안 올 때

1. Bot Token 확인
2. Channel ID 형식 확인 (`@channel_name` 또는 `-100123456789`)
3. 봇을 채널에 관리자로 추가

---

## 📈 성능 최적화

### 배치 처리

```python
# 여러 PDF 동시 처리
pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]

results = []
for pdf_file in pdf_files:
    result = parser.parse_pdf(pdf_file)
    results.append(result)

# JSON으로 일괄 저장
parser.export_to_json(results, "output/batch_results.json")
```

### 캐싱 활성화

```yaml
performance:
  cache:
    enabled: true
    ttl_seconds: 3600
```

---

## 🤝 통합 가이드

### HVDC Invoice Audit 시스템과 통합

```python
# Rate 데이터와 통합
import sys
sys.path.append("../00_Shared")
from rate_loader import UnifiedRateLoader

# PDF 파싱 후 Invoice Audit에 연동
parsed_data = parser.parse_pdf("input/invoice.pdf")

# Rate 검증
rate_loader = UnifiedRateLoader("../Rate")
rate_loader.load_all_rates()

ref_rate = rate_loader.get_standard_rate("DO Fee", "Khalifa Port")
print(f"Reference Rate: ${ref_rate}")
```

---

## 📞 지원

- **Email**: hvdc-logistics@samsung.com
- **Slack**: #hvdc-logistics
- **Telegram**: @hvdc-alerts

---

## 📄 라이선스

Internal Use Only - Samsung C&T Corporation

---

## 🔄 업데이트 로그

### v1.0.0 (2025-10-13)
- 초기 릴리스
- PDF 파싱 엔진 통합
- 온톨로지 매핑 구현
- Cross-document 검증
- 워크플로우 자동화

---

**🚀 HVDC PDF Parser System - Automating Logistics Documentation**

