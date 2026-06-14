# LogiOntology System Architecture v2.0

## 📋 Executive Summary

LogiOntology는 HVDC 프로젝트의 물류 데이터를 시맨틱 웹 표준(RDF/OWL)으로 변환하고 추론하는 AI 기반 온톨로지 시스템입니다. 삼성물산과 ADNOC·DSV 파트너십을 위한 고도화된 물류 지능화 플랫폼으로, Excel 데이터를 RDF로 변환하고 SPARQL 쿼리를 통한 지능형 분석을 제공합니다.

## 🏗️ System Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    LogiOntology Platform v2.0                  │
├─────────────────────────────────────────────────────────────────┤
│  Input Layer          │  Processing Layer    │  Output Layer    │
│  ┌─────────────────┐  │  ┌─────────────────┐ │  ┌─────────────┐  │
│  │ Excel Files     │  │  │ Data Ingestion  │ │  │ RDF/TTL     │  │
│  │ HVDC Reports    │  │  │ Mapping Engine  │ │  │ SPARQL      │  │
│  │ CSV/JSON        │  │  │ Validation     │ │  │ Reports     │  │
│  └─────────────────┘  │  │ Reasoning      │ │  │ Dashboards  │  │
│                       │  └─────────────────┘ │  └─────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Quality Assurance Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Unit Tests      │  │ Integration     │  │ E2E Tests       │  │
│  │ (92% Coverage)  │  │ Tests           │  │ (Performance)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Technical Architecture

### 1. Data Ingestion Layer

#### 1.1 Excel Processing Engine
```python
# logiontology/ingest/excel.py
class ExcelProcessor:
    """Excel 파일 로드 및 정규화"""

    def load_excel(self, path: str, sheet: str = 0) -> pd.DataFrame:
        """Excel 파일 로드 및 컬럼 정규화"""

    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명 정규화 (한글 → 영문)"""

    def validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 타입 검증 및 변환"""
```

#### 1.2 Data Normalization
- **컬럼명 매핑**: 한글 → 영문 표준화
- **데이터 타입 변환**: Excel → Python 타입
- **인코딩 처리**: UTF-8 통일
- **결측치 처리**: 전략적 대체

### 2. Mapping & Transformation Layer

#### 2.1 Mapping Registry
```python
# logiontology/mapping/registry.py
class MappingRegistry:
    """데이터 매핑 규칙 관리"""

    def load_rules(self, config_path: str) -> None:
        """매핑 규칙 로드"""

    def apply_hvdc_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """HVDC 비즈니스 규칙 적용"""

    def dataframe_to_rdf(self, df: pd.DataFrame, output_path: str) -> str:
        """DataFrame → RDF 변환"""
```

#### 2.2 HVDC Business Rules
- **벤더 필터링**: HE (Hitachi), SIM (Siemens)만 처리
- **월 매칭 검증**: Operation Month = ETA Month
- **압력 한계**: ≤ 4.0 t/m² 준수
- **창고 코드**: DSV 표준 코드 검증

### 3. Validation & Quality Layer

#### 3.1 Schema Validator
```python
# logiontology/validation/schema_validator.py
class SchemaValidator:
    """스키마 검증 및 품질 관리"""

    def validate_document(self, doc: Dict) -> Tuple[bool, List[str]]:
        """문서 스키마 검증"""

    def validate_confidence(self, doc: Dict) -> List[str]:
        """신뢰도 임계값 검증"""

    def validate_hvdc_patterns(self, doc: Dict) -> List[str]:
        """HVDC 패턴 검증"""
```

#### 3.2 Quality Metrics
- **신뢰도 임계값**: ≥ 0.90 (Critical), ≥ 0.85 (Standard)
- **필수 필드 검증**: BOE, DO, Invoice 문서 타입별
- **패턴 매칭**: MBL, Container, HS Code 형식
- **데이터 무결성**: 재고 수식 검증

### 4. RDF Generation Layer

#### 4.1 RDF Writer
```python
# logiontology/rdfio/writer.py
class RDFWriter:
    """RDF/TTL 파일 생성"""

    def generate_rdf(self, data: Dict, output_path: str) -> str:
        """RDF 트리플 생성"""

    def serialize_ttl(self, graph: Graph) -> str:
        """Turtle 직렬화"""
```

#### 4.2 Namespace Management
```python
# 표준 네임스페이스
EX = "http://samsung.com/project-logistics#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"
```

### 5. Reasoning & Intelligence Layer

#### 5.1 Ontology Reasoning
```python
# logiontology/reasoning/engine.py
class ReasoningEngine:
    """온톨로지 추론 엔진"""

    def infer_transport_events(self, data: List[Dict]) -> List[TransportEvent]:
        """운송 이벤트 추론"""

    def calculate_kpis(self, events: List[TransportEvent]) -> Dict[str, float]:
        """KPI 자동 계산"""
```

#### 5.2 AI-Powered Analysis
- **패턴 인식**: 이상치 탐지
- **예측 분석**: 재고 수요 예측
- **최적화**: 창고 배치 최적화
- **리스크 관리**: 지연/손실 예측

## 📊 Data Flow Architecture

### Phase 1: Data Ingestion
```
Excel Files → ExcelProcessor → Normalized DataFrame
     ↓
Column Mapping → Data Type Conversion → Validation
```

### Phase 2: Business Logic Processing
```
DataFrame → HVDC Filters → Business Rules → Filtered DataFrame
     ↓
Vendor Filtering → Month Matching → Pressure Validation
```

### Phase 3: RDF Transformation
```
Filtered DataFrame → Mapping Rules → RDF Triples → TTL Files
     ↓
Namespace Binding → Property Mapping → Class Instantiation
```

### Phase 4: Quality Assurance
```
RDF Data → Schema Validation → Confidence Check → Quality Report
     ↓
Pattern Matching → Business Rule Validation → Error Reporting
```

## 🎯 Core Algorithms

### 1. HVDC Code Normalization
```python
def normalize_code_num(code: str) -> str:
    """HVDC 코드 정규화"""
    if pd.isna(code):
        return ""

    # 숫자 부분만 추출
    numbers = re.sub(r'\D', '', str(code))
    return numbers if numbers else ""
```

### 2. Code Matching Algorithm
```python
def codes_match(code1: str, code2: str) -> bool:
    """HVDC 코드 매칭 검증"""
    norm1 = normalize_code_num(code1)
    norm2 = normalize_code_num(code2)

    if not norm1 or not norm2:
        return False

    return norm1 == norm2
```

### 3. Month Matching Validation
```python
def validate_month_matching(df: pd.DataFrame) -> pd.DataFrame:
    """월 매칭 검증"""
    df["OP_MONTH"] = pd.to_datetime(df["Operation Month"]).dt.strftime("%Y-%m")
    df["ETA_MONTH"] = pd.to_datetime(df["ETA"]).dt.strftime("%Y-%m")

    return df[df["OP_MONTH"] == df["ETA_MONTH"]]
```

### 4. Pressure Limit Validation
```python
def validate_pressure_limit(df: pd.DataFrame) -> pd.DataFrame:
    """압력 한계 검증 (≤ 4.0 t/m²)"""
    if "Pressure" in df.columns:
        return df[df["Pressure"] <= 4.0]
    return df
```

## 🔍 Quality Assurance Architecture

### Test Coverage Matrix
```
┌─────────────────┬──────────┬──────────┬──────────┐
│ Module          │ Unit     │ Integration │ E2E    │
├─────────────────┼──────────┼──────────┼──────────┤
│ Excel Ingest    │ 99%      │ 100%     │ 100%     │
│ Mapping Registry│ 99%      │ 100%     │ 100%     │
│ Schema Validator│ 97%      │ 100%     │ 100%     │
│ RDF Writer      │ 43%      │ 100%     │ 100%     │
│ Overall         │ 92%      │ 100%     │ 100%     │
└─────────────────┴──────────┴──────────┴──────────┘
```

### CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: LogiOntology CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python 3.13
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff bandit

      - name: Run tests
        run: |
          pytest tests/ --cov=logiontology --cov-report=xml

      - name: Lint check
        run: ruff check .

      - name: Security check
        run: bandit -r logiontology/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 🚀 Performance Architecture

### Performance Metrics
- **처리 속도**: 10,000 rows/분
- **메모리 사용량**: ≤ 2GB (대용량 파일)
- **응답 시간**: ≤ 2초 (API 호출)
- **동시 처리**: 100개 파일 병렬

### Scalability Design
```python
# 병렬 처리 아키텍처
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelProcessor:
    """병렬 데이터 처리"""

    async def process_multiple_files(self, file_paths: List[str]) -> List[Dict]:
        """다중 파일 병렬 처리"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = [
                asyncio.create_task(self.process_single_file(path))
                for path in file_paths
            ]
            return await asyncio.gather(*tasks)
```

## 🔒 Security Architecture

### Data Protection
- **PII 필터링**: 개인정보 자동 탐지 및 제거
- **NDA 준수**: 기밀 정보 보호
- **암호화**: 전송 중 데이터 암호화
- **접근 제어**: 역할 기반 권한 관리

### Compliance Framework
```python
class ComplianceValidator:
    """규제 준수 검증"""

    def validate_fanr_compliance(self, data: Dict) -> bool:
        """FANR 규제 준수 검증"""

    def validate_moiat_compliance(self, data: Dict) -> bool:
        """MOIAT 규제 준수 검증"""

    def audit_trail(self, operation: str) -> None:
        """감사 추적 로그"""
```

## 📈 Monitoring & Observability

### Health Checks
```python
class HealthMonitor:
    """시스템 상태 모니터링"""

    def check_database_health(self) -> bool:
        """데이터베이스 상태 확인"""

    def check_memory_usage(self) -> float:
        """메모리 사용량 확인"""

    def check_processing_queue(self) -> int:
        """처리 대기열 확인"""
```

### Metrics Dashboard
- **처리량**: 시간당 처리 파일 수
- **성공률**: 처리 성공 비율
- **오류율**: 실패율 및 오류 유형
- **성능**: 평균 처리 시간

## 🔄 Deployment Architecture

### Container Strategy
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY logiontology/ ./logiontology/
COPY tests/ ./tests/

CMD ["python", "-m", "logiontology.cli"]
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logiontology
spec:
  replicas: 3
  selector:
    matchLabels:
      app: logiontology
  template:
    metadata:
      labels:
        app: logiontology
    spec:
      containers:
      - name: logiontology
        image: logiontology:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## 🎯 Future Roadmap

### Phase 1: Enhanced AI (Q2 2024)
- **ML 모델 통합**: 예측 분석 강화
- **자동 분류**: 문서 타입 자동 인식
- **이상 탐지**: 실시간 이상치 탐지

### Phase 2: Real-time Processing (Q3 2024)
- **스트리밍 처리**: 실시간 데이터 처리
- **이벤트 기반**: 메시지 큐 통합
- **동적 스케일링**: 자동 확장/축소

### Phase 3: Advanced Analytics (Q4 2024)
- **시각화 대시보드**: 실시간 KPI 모니터링
- **예측 모델**: 수요 예측 및 최적화
- **의사결정 지원**: AI 기반 추천 시스템

## 📚 API Documentation

### Core Endpoints
```python
# REST API 엔드포인트
POST /api/v1/process/excel
GET  /api/v1/status/{job_id}
GET  /api/v1/results/{job_id}
POST /api/v1/query/sparql
GET  /api/v1/health
```

### GraphQL Schema
```graphql
type Query {
  transportEvents(filter: EventFilter): [TransportEvent]
  stockSnapshots(filter: SnapshotFilter): [StockSnapshot]
  kpiMetrics(timeRange: TimeRange): KPIMetrics
}

type Mutation {
  processExcelFile(file: Upload!): ProcessingJob
  validateData(data: JSON!): ValidationResult
}
```

## 🔧 Configuration Management

### Environment Variables
```bash
# .env
LOGIONTOLOGY_DEBUG=false
LOGIONTOLOGY_LOG_LEVEL=INFO
LOGIONTOLOGY_MAX_WORKERS=4
LOGIONTOLOGY_MEMORY_LIMIT=2GB
LOGIONTOLOGY_CACHE_TTL=3600
```

### Configuration Files
```yaml
# config/production.yaml
database:
  url: "postgresql://user:pass@localhost/logiontology"
  pool_size: 10

redis:
  url: "redis://localhost:6379"
  ttl: 3600

processing:
  max_file_size: "100MB"
  timeout: 300
  retry_attempts: 3
```

---

## 📞 Support & Contact

- **Repository**: https://github.com/macho715/logi_ontol
- **Documentation**: https://logiontology.readthedocs.io
- **Issues**: https://github.com/macho715/logi_ontol/issues
- **Email**: support@logiontology.com

---

**LogiOntology v2.0 - Transforming Logistics Data into Intelligent Insights** 🚀
