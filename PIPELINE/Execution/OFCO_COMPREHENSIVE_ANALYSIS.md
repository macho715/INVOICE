---
title: "OFCO System - Comprehensive Analysis"
type: "comprehensive-analysis"
domain: "port-operations-ofco"
version: "1.0"
date: "2025-01-25"
language: "ko"
tags: ["ofco", "comprehensive", "analysis", "port-operations", "invoice", "multi-key"]
status: "active"
---

# OFCO 시스템 - 6대 핵심 영역 종합 분석

## Executive Summary

**OFCO (Offshore Operations) 시스템**은 삼성물산 HVDC 프로젝트의 항만 운영을 관리하는 핵심 온톨로지 기반 Port Ops & Invoice 허브입니다. 6개 핵심 영역으로 구성되어 있으며, Multi-Key Identity Graph 시스템을 통해 Invoice, PortCall, ServiceEvent, Tariff, PriceCenter를 통합적으로 관리합니다.

### 6대 핵심 영역
1. **항만 대행(Agency) 서비스**
2. **항만요금 관리**
3. **장비/인력 배치**
4. **수배(수자원/게이트패스) 서비스**
5. **Multi-Key Identity Graph 시스템**
6. **Invoice ↔ PortCall ↔ ServiceEvent ↔ Tariff ↔ Price Center 연계**

---

## Part 1: 항만 대행(Agency) 서비스

### 개요

OFCO는 12종의 ServiceEvent 클래스를 통해 포괄적인 항만 대행 서비스를 제공합니다.

### ServiceEvent 클래스 체계 (12종)

#### 1. ops:ChannelCrossing
- **설명**: 항만 입항 전 수로 통과 서비스
- **제공업체**: SAFEEN
- **Cost Center 매핑**:
  - Cost A: `PORT HANDLING CHARGE`
  - Cost B: `CHANNEL TRANSIT CHARGES`
  - Price Center: `CHANNEL TRANSIT CHARGES`
- **실제 사례**: 
  ```ttl
  ops:service/CHANNEL-CROSSING-ROT2504053298 a ops:ServiceEvent ;
      ops:serviceType "Channel Crossing" ;
      ops:relatesToPortCall ops:portcall/ROT-2504053298 ;
      ops:provider "SAFEEN" ;
      ops:cost "6621.52"^^xsd:decimal ;
      ops:currency "AED" .
  ```
- **비즈니스 로직**: Subject에 "SAFEEN" 키워드 포함 시 자동 매핑

#### 2. ops:Berthing
- **설명**: 선박 접안 서비스
- **제공업체**: ADP (Abu Dhabi Ports)
- **Cost Center 매핑**:
  - Cost A: `PORT HANDLING CHARGE`
  - Cost B: `PORT HANDLING CHARGE`
  - Price Center: `PORT DUES`
- **실제 사례**:
  ```ttl
  ops:service/BERTHING-ROT2504053298 a ops:ServiceEvent ;
      ops:serviceType "Berthing" ;
      ops:relatesToPortCall ops:portcall/ROT-2504053298 ;
      ops:provider "ADP" ;
      ops:berth "Khalifa Container Terminal - Berth 3" ;
      ops:cost "3500.00"^^xsd:decimal ;
      ops:currency "AED" .
  ```
- **비즈니스 로직**: ADP INV + "Port Dues" 키워드 조합으로 식별

#### 3. ops:Pilotage
- **설명**: 항만 기사 서비스
- **제공업체**: ADP
- **Cost Center 매핑**: PORT HANDLING CHARGE 계열
- **비즈니스 로직**: "Pilotage" 키워드 패턴 매칭

#### 4. ops:PilotLaunch
- **설명**: 기사 승선용 런치 보트 서비스
- **제공업체**: ADP
- **Cost Center 매핑**: PORT HANDLING CHARGE 계열

#### 5. ops:PHC_BulkHandling
- **설명**: Port Handling Charge - 벌크 화물 처리
- **제공업체**: ADP/OFCO
- **Cost Center 매핑**: PORT HANDLING CHARGE / PHC 계열
- **사용 사례**: 중량/벌크 화물 (Zayed Port 전용)

#### 6. ops:PortDues
- **설명**: 항만 사용료
- **제공업체**: ADP
- **Cost Center 매핑**:
  - Cost A: `PORT HANDLING CHARGE`
  - Cost B: `PORT DUES & SERVICES CHARGES`
  - Price Center: `PORT DUES`

#### 7. ops:Waste
- **설명**: 폐기물 처리 서비스
- **제공업체**: ADP/OFCO
- **Cost Center 매핑**: AT COST 계열

#### 8. ops:FW_Supply
- **설명**: 식수 공급 서비스 (Fresh Water Supply)
- **제공업체**: ADP/OFCO
- **Cost Center 매핑**:
  - Cost A: `CONTRACT`
  - Cost B: `AF FOR FW SA`
  - Price Center: `SUPPLY WATER 5000IG`
- **Subject 패턴**: "Arranging FW Supply" | "FW Supply" | "5000 IG FW"
- **실제 사례**: WhatsApp 대화에서 "5000 IG FW" 패턴 확인

#### 9. ops:EquipmentHire
- **설명**: 장비 임대 서비스
- **제공업체**: OFCO
- **Cost Center 매핑**: CONTRACT 계열
- **실제 사례**: WhatsApp 대화 - "F.lift" (Forklift), "Crane" 등 언급

#### 10. ops:Manpower
- **설명**: 인력 배치 서비스
- **제공업체**: OFCO
- **Cost Center 매핑**: CONTRACT 계열
- **실제 사례**: WhatsApp 대화 - "manpower deployment", "competent manpower" 언급

#### 11. ops:GatePass
- **설명**: CICPA 게이트패스 발행
- **제공업체**: CICPA
- **Cost Center 매핑**: Price Center C (수수료 카테고리)
- **비즈니스 로직**: 특수 Pass/Document 처리

#### 12. ops:DocProcessing
- **설명**: 문서 수수료 처리
- **제공업체**: OFCO
- **Cost Center 매핑**: Price Center C (수수료 카테고리)
- **비즈니스 로직**: 문서 검증 비용

### Cost Center v2.5 매핑 규칙

| Subject 패턴 | Cost A | Cost B | Price Center | Priority |
|---|---|---|---|---|
| "SAFEEN" | PORT HANDLING CHARGE | CHANNEL TRANSIT CHARGES | CHANNEL TRANSIT CHARGES | 1 |
| "ADP INV" + "Port Dues" | PORT HANDLING CHARGE | PORT DUES & SERVICES CHARGES | PORT DUES | 2 |
| "Cargo Clearance" | CONTRACT | AF FOR CC | AGENCY FEE FOR CARGO CLEARANCE | 3 |
| "Arranging FW Supply" \| "FW Supply" | CONTRACT | AF FOR FW SA | SUPPLY WATER 5000IG | 4 |
| "Berthing Arrangement" | CONTRACT(AF FOR BA) | CONTRACT | AGENCY FEE FOR BERTHING ARRANGEMENT | 5 |
| "5000 IG FW" | AT COST | AT COST(WATER SUPPLY) | SUPPLY WATER 5000IG | 6 |

---

## Part 2: 항만요금 관리

### Invoice 온톨로지 구조

#### 1. fin:Invoice (OFCO 소스)
- **IRI 패턴**: `ofco:invoice/OFCO-INV-0000181`
- **주요 속성**:
  - `fin:currency`: "AED" (고정)
  - `fin:total`: Invoice 총액
  - `fin:invoiceDate`: 발행일
  - `id:hasOFCOInvNo`: OFCO 인보이스 번호

#### 2. fin:InvoiceLine (최대 4 RatePair)
- **IRI 패턴**: `ofco:line/OFCO-INV-0000181#2015` (NO.=2015)
- **주요 속성**:
  - `fin:belongsToInvoice`: 소속 Invoice
  - `fin:lineNo`: 라인 번호
  - `fin:subject`: SUBJECT (패턴 매핑 트리거)
  - `fin:currency`: "AED"
  - `fin:vat`: 0.00 또는 5.00
  - `rate:hasEA_i`: EA 값 (i=1..4)
  - `rate:hasRate_i`: Rate 값 (i=1..4)
  - `fin:lineAmount`: 라인 총액
  - `prov:hasEvidence`: 증거 추적

#### RatePair 분해 예시
```ttl
ofco:line/OFCO-INV-0000181#2002 a fin:InvoiceLine ;
    fin:belongsToInvoice ofco:invoice/OFCO-INV-0000181 ;
    fin:lineNo 2002 ;
    fin:subject "SAFEEN … Channel Crossing – Rot# 2503123133" ;
    rate:hasEA_1 2.00 ; rate:hasRate_1 3091.25 ;
    rate:hasEA_2 2.00 ; rate:hasRate_2 100.00 ;
    rate:hasEA_3 1.00 ; rate:hasRate_3 239.00 ;
    fin:lineAmount 6621.52 .
```
**검증**: (2.00 × 3091.25) + (2.00 × 100.00) + (1.00 × 239.00) = 6621.52 ✓

#### 3. rate:TariffRef 버전 관리
- **목적**: 요율 변동 추적
- **구조**: TariffRef는 유효일(Best Before)을 포함하여 버전별 요율 관리
- **COST-GUARD 통합**: 기준요율 대비 Δ% 밴드 검증

### 회계 일관성 검증 (SHACL)

#### InvoiceLineShape 검증 규칙
```shacl
InvoiceLineShape:
  - rate:hasEA_* × rate:hasRate_*의 합 = fin:lineAmount ±0.01
  - RatePair 최대 4, 결측 시 0.00 채움
  - fin:currency = "AED"
  - fin:vat ∈ {0.00, 5.00}
  - prov:hasEvidence 필수
```

#### InvoiceShape 검증 규칙
```shacl
InvoiceShape:
  - Σ(InvoiceLine.fin:lineAmount) = fin:total ±2.00%
  - [EXT] 라벨 행 금액 집계 제외
```

#### 운영 규칙 예외 처리
- **EA 결측 시**: EA=1.00 & Rate=Amount 규칙 허용 (내 ±2.00%)
- **VAT 불일치**: VAT=0.00% 또는 5.00% 외 **[MISMATCH]** 플래그
- **[EXT] 메타**: 금액 집계 제외, 근거(M열) 필수
- **증거 필수**: 파일명/페이지/라인 또는 참조시트(Row) 필수 기록

### COST-GUARD 시스템

**목적**: 기준요율 대비 Δ% 밴드 검증

| 등급 | Δ% 범위 | 조치 |
|---|---|---|
| PASS | ±5% 이내 | 정상 처리 |
| WARN | ±5~10% | 수동 검토 |
| HIGH | ±10~20% | 승인 필요 |
| CRITICAL | ±20% 초과 | 즉시 중단, 재확인 |

---

## Part 3: 장비/인력 배치

### ops:EquipmentHire 서비스 이벤트

#### 실제 사례 (WhatsApp 대화 분석)
- **Forklift (F.lift)**: "F.lift check by OFCO", "4T F.lift after tea break"
- **Crane**: "CRANE SHIFTING POSITION FOR LOADING", "crane position"
- **Spreader Beam**: "if need spreader beam please inform to OFCO in advance"

#### Cost/Price Center 매핑
- **Cost A**: `CONTRACT`
- **Cost B**: `CONTRACT`
- **Price Center**: `EQUIPMENT HIRE`

### ops:Manpower 인력 배치

#### 실제 사례
- "he will coordinate to deploy the manpowers ASAP"
- "Despite of lack of competent manpower and lifting tools"
- "manpower deployment"

#### Cost/Price Center 매핑
- **Cost A**: `CONTRACT`
- **Cost B**: `CONTRACT`
- **Price Center**: `MANPOWER`

### 장비/인력 일관성 체크
- OFCO가 장비와 인력을 통합 관리
- 실시간 WhatsApp 대화로 조정
- GatePass 사전 발행 필요

---

## Part 4: 수배(수자원/게이트패스) 서비스

### ops:FW_Supply (Fresh Water 공급)

#### Subject 패턴 매핑
- **패턴 1**: "Arranging FW Supply" → `CONTRACT / AF FOR FW SA`
- **패턴 2**: "FW Supply" → `CONTRACT / AF FOR FW SA`
- **패턴 3**: "5000 IG FW" → `AT COST / AT COST(WATER SUPPLY)`

#### Price Center 분류
- **Price Center**: `SUPPLY WATER 5000IG`
- **계산 방식**: IG(Imperial Gallon) × 5000 단위

### ops:GatePass (CICPA 게이트패스)

#### 비즈니스 로직
- **발행기관**: CICPA
- **Price Center**: C 카테고리 (수수료)
- **필수성**: 화물 반출입 전 필수

#### Price Center 3-Way 분류
- **A**: 주요 서비스 (Channel Crossing, Port Dues 등)
- **B**: 보조 서비스 (Transit Charges, Services 등)
- **C**: 수수료/Pass/Document (**Gate Pass, Doc Processing** 포함)

#### Price Center 3-Way 분개 규칙
```
규칙:
1. C=0 의심 재검토
2. A>B 또는 B<0 시 일부 C로 이동
3. A+B+C = Original_TOTAL
4. Diff = 0.00 (절대 차이 없음)
```

---

## Part 5: Multi-Key Identity Graph 시스템

### 개요

**문제**: 단일 키 의존 시 연쇄조인 실패·누락 위험  
**해법**: **id:Key** 슈퍼클래스 아래 모든 키를 동등 1급 엔터티로 수집하고, **Same-As/LinkSet**으로 실체를 클러스터링

### id:Key 슈퍼클래스 구조

#### 주요 키 타입
1. **id:OFCOInvNo** - OFCO 인보이스 번호
2. **id:SAFEENInvNo** - SAFEEN 인보이스 번호
3. **id:ADPInvNo** - ADP 인보이스 번호
4. **id:RotationNo** - PortCall 회전 번호
5. **id:SamsungRef** - Samsung 참조 코드 (예: HVDC-AGI-GRM-J71-50)
6. **id:HVDCCode** - HVDC 프로젝트 코드

### 클러스터링 규칙

#### 규칙 1: PortCall 클러스터링
```
RotationNo 같고,
날짜 창(±7d) 및 항만 동일
→ 같은 PortCall 후보
```

**예시**:
```ttl
id:key/ROT-2504053298 a id:RotationNo ;
    id:linksToPortCall ops:portcall/ROT-2504053298 ;
    id:hasDateWindow "2024-11-10"^^xsd:date ;
    id:hasPort port:port/KHALIFA .
```

#### 규칙 2: Operation Batch 클러스터링
```
SamsungRef 동일 +
Subject 패턴 일치
→ 같은 Operation Batch
```

**예시**:
```ttl
id:key/HVDC-AGI-GRM-J71-50 a id:SamsungRef ;
    id:hasSubject "Channel Crossing" ;
    id:linksToPortCall ops:portcall/ROT-2504053298 .
```

#### 규칙 3: Invoice 클러스터링
```
InvoiceNo 묶음
Σ(lineAmount) = Invoice Total(±2.00%)
→ 같은 Invoice
```

**검증 로직**:
```python
def cluster_invoice_by_lines(invoice_lines):
    total_amount = sum(line.lineAmount for line in invoice_lines)
    invoice_total = invoice.total
    diff_percent = abs(total_amount - invoice_total) / invoice_total
    return diff_percent <= 0.02  # ±2.00%
```

### Same-As/LinkSet 알고리즘

#### 구현 예시
```python
def cluster_entities_by_keys(keys):
    clusters = []
    for key in keys:
        # Find matching cluster or create new
        cluster = find_matching_cluster(key, clusters)
        if not cluster:
            cluster = LinkSet()
            clusters.append(cluster)
        cluster.add(key)
    return clusters

def find_matching_cluster(key, clusters):
    for cluster in clusters:
        if any(is_same_entity(key, existing_key) for existing_key in cluster):
            return cluster
    return None

def is_same_entity(key1, key2):
    # Rule 1: Same RotationNo, same date window (±7d), same port
    if key1.type == 'RotationNo' and key2.type == 'RotationNo':
        if key1.value == key2.value:
            if abs(key1.date - key2.date) <= 7:
                if key1.port == key2.port:
                    return True
    
    # Rule 2: Same SamsungRef + Subject pattern match
    if key1.type == 'SamsungRef' and key2.type == 'SamsungRef':
        if key1.value == key2.value and key1.subject_pattern == key2.subject_pattern:
            return True
    
    # Rule 3: Same Invoice No
    if key1.type == 'InvoiceNo' and key2.type == 'InvoiceNo':
        if key1.value == key2.value:
            return True
    
    return False
```

---

## Part 6: Invoice ↔ PortCall ↔ ServiceEvent ↔ Tariff ↔ Price Center 연계

### RDF/OWL 관계 구조

#### 핵심 관계 프로퍼티
```
InvoiceLine → PortCall
  ops:relatesToPortCall

InvoiceLine → Invoice
  fin:belongsToInvoice

InvoiceLine → ServiceEvent
  ops:hasServiceEvent (추론)

ServiceEvent → TariffRef
  ops:referencesTariff

ServiceEvent → PriceCenter
  cost:hasPriceCenter

InvoiceLine → CostCenter
  cost:hasCostCenterA
  cost:hasCostCenterB
```

### 통합 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                      OFCO Invoice Flow                        │
└─────────────────────────────────────────────────────────────┘

Invoice (OFCO-INV-0000181)
  │
  ├─→ InvoiceLine #2002
  │     │
  │     ├─→ RatePair #1: EA=2.00, Rate=3091.25
  │     ├─→ RatePair #2: EA=2.00, Rate=100.00
  │     ├─→ RatePair #3: EA=1.00, Rate=239.00
  │     │
  │     ├─→ PortCall (ROT-2503123133)
  │     │     │
  │     │     └─→ ServiceEvent: ChannelCrossing (SAFEEN)
  │     │           │
  │     │           └─→ TariffRef: SAFEEN-2024-RATE-v1.2
  │     │
  │     ├─→ CostCenterA: PORT_HANDLING_CHARGE
  │     ├─→ CostCenterB: CHANNEL_TRANSIT_CHARGES
  │     └─→ PriceCenter: CHANNEL_TRANSIT_CHARGES
  │
  └─→ Total: Σ(lineAmount) = 2799.99 (±2.00%)
```

### SPARQL 쿼리 예시

#### 1. PortCall별 총 ServiceEvent 비용 집계
```sparql
PREFIX ops: <https://hvdc-project.com/ontology/operations/>
PREFIX port: <https://hvdc-project.com/ontology/port-operations/>
PREFIX fin: <https://hvdc-project.com/ontology/financial/>

SELECT ?portCall ?rotationNumber (SUM(?cost) AS ?totalCost)
WHERE {
    ?portCall a port:PortCall ;
              port:rotationNumber ?rotationNumber .
    
    ?invoiceLine fin:relatesToPortCall ?portCall ;
                 ops:hasServiceEvent ?serviceEvent .
    
    ?serviceEvent ops:cost ?cost .
}
GROUP BY ?portCall ?rotationNumber
ORDER BY DESC(?totalCost)
```

#### 2. Price Center별 비용 분포 분석
```sparql
PREFIX cost: <https://hvdc-project.com/ontology/cost/>
PREFIX fin: <https://hvdc-project.com/ontology/financial/>

SELECT ?priceCenter (COUNT(?invoiceLine) AS ?lineCount) 
       (SUM(?lineAmount) AS ?totalAmount)
WHERE {
    ?invoiceLine fin:lineAmount ?lineAmount ;
                 cost:hasPriceCenter ?priceCenter .
}
GROUP BY ?priceCenter
ORDER BY DESC(?totalAmount)
```

#### 3. Multi-Key Cluster 크기 분석
```sparql
PREFIX id: <https://hvdc-project.com/ontology/identity/>
PREFIX ops: <https://hvdc-project.com/ontology/operations/>

SELECT ?cluster (COUNT(?key) AS ?keyCount)
WHERE {
    ?cluster id:hasKey ?key .
}
GROUP BY ?cluster
HAVING (?keyCount > 1)
ORDER BY DESC(?keyCount)
```

### 파이프라인 (운영·검증)

#### 9단계 OCR→RDF 변환 파이프라인
1. **Pre-Prep**: 회전/데스큐/샤프닝 (DPI<300 경고)
2. **OCR v2.4**: 레이아웃·토큰 conf 수집
3. **Smart Table Parser 2.1**: 병합셀 해제·세로표 가로화·단위/통화 분리
4. **NLP Refine**: NULL/단위 보정, 추정 금지
5. **Field Tagger**: Parties/IDs/Incoterms/Rotation/Subject
6. **LDG Payload Build**: 해시·CrossLinks·Evidence
7. **Mapping & QC**: EA×Rate 분해, Cost/Price Center 적용, VAT·통화·합계 검증
8. **COST-GUARD**: 기준요율 대비 Δ% 밴드 (PASS/WARN/HIGH/CRITICAL)
9. **Report(7+2)**: Discrepancy Table, Compliance Matrix, DEM/DET Forecast 등

#### KPI 게이트
- **MeanConf ≥ 0.92**: 평균 OCR 신뢰도
- **TableAcc ≥ 0.98**: 테이블 정확도
- **NumericIntegrity = 1.00**: 수치 무결성
- **미달 시**: **ZERO** 중단 로그

---

## Report 표준 (7+2)

### 1. Auto Guard Summary
- 전체 검증 결과 요약
- 통과/경고/실패 통계

### 1.5. Risk Assessment
- 등급/동인/신뢰도 분석
- 고위험 항목 우선순위

### 2. Discrepancy Table
- Δ(차이)·허용오차·상태
- 라인별 상세 차이 분석

### 3. Compliance Matrix
- UAE·근거 링크
- 규제 준수 검증 (MOIAT/FANR/TRA)

### 4. Auto-Fill
- Freight/Insurance 자동 채움
- 휴리스틱 기반 추정

### 5. Auto Action Hooks
- 명령·가이드 자동 생성
- 다음 단계 추천

### 6. DEM/DET & Gate-Out Forecast
- 예상 통관 시간 예측
- 게이트 패스 발행 일정

### 7. Evidence & Citations
- 파일명/페이지/라인 참조
- SPARQL 쿼리 결과 링크

### 8. Weak Spot & Improvements
- 약점 분석
- 개선 제안

### 9. Changelog
- 변경 이력
- 버전 추적

---

## 운영 명령 & 자동화 훅

### 인식/검증
```bash
/ocr_basic {file} mode:LDG+
→ KPI Pass 확인
→ /ocr_table / /ocr_retry
```

### 코스트가드
```bash
/switch_mode COST-GUARD
+ /logi-master invoice-audit --AEDonly
```

### 매핑
```bash
/mapping run
→ /run pricecenter map
→ /mapping update pricecenter
```

### 규제 체크
```bash
/logi-master cert-chk (MOIAT/FANR/TRA)
```

### 배치
```bash
/workflow bulk …
→ /export excel
```

---

## 로드맵 (P→Pi→B→O→S + KPI)

### Prepare (2주)
- 스키마/네임스페이스/IRI 설계
- SHACL 초안
- 키-링크 룰 정의
- **KPI**: 스키마 커버리지 ≥90.00%

### Pilot (3주)
- 1개 인보이스 묶음 (예: OFCO-INV-0000181) E2E
- Δ오차≤2.00%
- **KPI**: ZERO 트리거=0, Evidence 100.00%

### Build (4주)
- CostCenter v2.5·3-Way 분개·COST-GUARD 통합
- **KPI**: Pass율≥95.00%

### Operate (지속)
- 배치 처리 및 리포트(7+2) 자동 발행
- **KPI**: TAT ≤ 0.50h/건

### Scale (지속)
- SAFEEN/ADP 직조인, PortCall API, DEM/DET 2.0 연계
- **KPI**: 오탐율 ≤ 2.00%

---

## 리스크 & 완화

| 리스크 | 완화 전략 |
|---|---|
| 키 불일치/누락 | Multi-Key 흡수 + 휴리스틱 윈도우(±7d) |
| OCR 품질 저하 | KPI 게이트 + `/ocr_lowres_fix` + ZERO 중단 |
| 요율 변동 | TariffRef 버전드(유효일) + COST-GUARD Δ% 밴드 |

---

## 구현 노트

### 코드베이스
- **Location**: `logiontology/`
- **Modules**: mapping/validation/reasoning/rdfio/report/pipeline

### 기술 스택
- **SHACL Runner**: 검증 엔진
- **JSON-LD**: 컨텍스트 제공
- **RDFLib + DuckDB**: 라인-레벨 집계 검증

### 외부 연계
- **PortCall(AD Ports)**: API 연동
- **SAFEEN 청구 스냅샷**: TariffRef Evidence로 보관

---

## 부록: Subject→Cost/PriceCenter 매핑 예시

| Subject | Cost A | Cost B | Price Center |
|---|---|---|---|
| SAFEEN … Channel Crossing | PORT HANDLING CHARGE | CHANNEL TRANSIT CHARGES | CHANNEL TRANSIT CHARGES |
| ADP INV … Port Dues | PORT HANDLING CHARGE | PORT DUES & SERVICES CHARGES | PORT DUES |
| Agency fee: Cargo Clearance | CONTRACT | AF FOR CC | AGENCY FEE FOR CARGO CLEARANCE |
| Arranging FW Supply | CONTRACT | AF FOR FW SA | SUPPLY WATER 5000IG |
| Berthing Arrangement | CONTRACT(AF FOR BA) | CONTRACT | AGENCY FEE FOR BERTHING ARRANGEMENT |
| 5000 IG FW | AT COST | AT COST(WATER SUPPLY) | SUPPLY WATER 5000IG |

---

## 참조 문서

1. **`ontology/extended/2_EXT-01-hvdc-ofco-port-ops-en.md`** (v4.1 영문)
2. **`ontology/extended/2_EXT-02-hvdc-ofco-port-ops-ko.md`** (v4.1 한글)
3. **`Logi ontol core doc/CONSOLIDATED-07-port-operations.md`** (통합본 v1.1)
4. **`logiontology/configs/ontology/hvdc_ontology.ttl`** (온톨로지 정의)
5. **`ABU/Abu Dhabi Logistics님과의 WhatsApp 대화.txt`** (실무 사례)

---

**생성일**: 2025-01-25  
**버전**: 1.0  
**상태**: Active  
**주석**: 숫자 2 decimals, ISO 날짜 사용, NDA/PII 마스킹 준수

