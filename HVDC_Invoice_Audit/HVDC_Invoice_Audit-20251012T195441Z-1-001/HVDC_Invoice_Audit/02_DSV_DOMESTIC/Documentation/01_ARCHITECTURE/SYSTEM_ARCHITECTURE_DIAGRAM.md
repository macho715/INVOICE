# 시스템 아키텍처 다이어그램

**프로젝트**: 9월 2025 DSV Domestic Invoice 검증 시스템
**버전**: PATCH4 (v4.0)
**작성일**: 2025-10-13
**최종 성능**: 95.5% 매칭률 달성

---

## 1. 전체 시스템 플로우

```mermaid
graph TB
    subgraph INPUT["📥 Input Layer"]
        I1["📊 Invoice Excel<br/>44 items<br/>SCNT HVDC DRAFT INVOICE"]
        I2["🗺️ ApprovedLaneMap<br/>124 lanes<br/>Enhanced JSON"]
        I3["📄 DN PDFs<br/>36 documents<br/>Supporting Documents"]
    end

    subgraph PROCESSING["⚙️ Processing Layer"]
        P1["🔍 Enhanced Lane Matching<br/>4-level fallback<br/>79.5% (35/44)"]
        P2["📖 PDF Parsing<br/>Multi-layer fallback<br/>91.7% (33/36)"]
        P3["🔗 Cross-Validation<br/>1:1 Greedy Matching<br/>95.5% (42/44)"]
        P4["📋 Status Classification<br/>PASS/WARN/FAIL<br/>47.7% PASS"]
    end

    subgraph OUTPUT["📤 Output Layer"]
        O1["📈 Final Excel<br/>25 columns, 44 rows<br/>Hyperlinks + Validation"]
        O2["📊 Supply-Demand CSV<br/>dn_supply_demand.csv<br/>Gap Analysis"]
        O3["📝 Validation Report<br/>Complete Analysis<br/>Recommendations"]
    end

    I1 --> P1
    I2 --> P1
    I3 --> P2
    P1 --> P3
    P2 --> P3
    P3 --> P4
    P4 --> O1
    P4 --> O2
    P4 --> O3

    classDef inputStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef processStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef outputStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px

    class I1,I2,I3 inputStyle
    class P1,P2,P3,P4 processStyle
    class O1,O2,O3 outputStyle
```

---

## 2. Enhanced Lane Matching 상세

```mermaid
flowchart LR
    A["📋 Invoice Item<br/>(Origin, Destination, Vehicle)"] --> B{"🔍 Level 1<br/>Exact Match<br/>(100%)"}
    B -->|"✅ Match"| C["🎯 Return Lane<br/>Match Level: Exact"]
    B -->|"❌ No Match"| D{"🔍 Level 2<br/>Similarity Match<br/>(≥0.65)"}
    D -->|"✅ Found"| C
    D -->|"❌ No Match"| E{"🔍 Level 3<br/>Region Match<br/>(권역별)"}
    E -->|"✅ Found"| C
    E -->|"❌ No Match"| F{"🔍 Level 4<br/>Vehicle Type Match<br/>(차량 타입)"}
    F -->|"✅ Found"| C
    F -->|"❌ No Match"| G["❌ No Match<br/>Result: Unmatched"]

    classDef levelStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef resultStyle fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef failStyle fill:#ffebee,stroke:#c62828,stroke-width:2px

    class A levelStyle
    class B,D,E,F levelStyle
    class C resultStyle
    class G failStyle
```

---

## 3. PDF Parsing 다층 폴백

```mermaid
graph TD
    A["📄 DN PDF Document"] --> B{"🔧 PyMuPDF<br/>(Primary)"}
    B -->|"✅ Success"| C["📝 Extract Text<br/>Layout Preserved"]
    B -->|"❌ Fail"| D{"🔧 pypdf<br/>(Secondary)"}
    D -->|"✅ Success"| C
    D -->|"❌ Fail"| E{"🔧 pdfminer.six<br/>(Complex Layout)"}
    E -->|"✅ Success"| C
    E -->|"❌ Fail"| F{"🔧 pdftotext<br/>(External Tool)"}
    F -->|"✅ Success"| C
    F -->|"❌ Fail"| G["❌ Extraction Failed<br/>Status: No Text"]

    C --> H["🔍 Field Extraction<br/>Origin, Destination, Vehicle<br/>Destination Code, DO #"]

    classDef primaryStyle fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef secondaryStyle fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
    classDef successStyle fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef failStyle fill:#ffebee,stroke:#c62828,stroke-width:2px

    class B primaryStyle
    class D,E,F secondaryStyle
    class C,H successStyle
    class G failStyle
```

---

## 4. 1:1 Greedy Matching 알고리즘

```mermaid
sequenceDiagram
    participant I as 📋 Invoice Items<br/>(44 items)
    participant D as 📄 DN List<br/>(36 DNs)
    participant M as 🔗 Matcher<br/>(Greedy Algorithm)

    I->>M: Load 44 invoice items
    D->>M: Load 36 DN documents

    M->>M: Calculate all similarities<br/>(Origin, Dest, Vehicle)
    M->>M: Sort by score (descending)<br/>Priority: Highest first

    loop Greedy Assignment Process
        M->>M: Pick highest score pair
        M->>M: Check DN capacity

        alt Capacity Available
            M->>I: ✅ Assign DN to invoice
            M->>D: Decrease DN capacity
            Note over M: Mark as MATCHED
        else Capacity Exhausted
            M->>I: ❌ Mark CAPACITY_EXHAUSTED
            Note over M: Skip to next candidate
        end
    end

    M->>I: 🎯 Final Results<br/>42/44 matched (95.5%)

    Note over I,D: Unmatched: 2 items<br/>Reasons: BELOW_MIN_SCORE, NO_CANDIDATES
```

---

## 5. 모듈 의존성 그래프

```mermaid
graph TD
    A["🚀 validate_sept_2025_with_pdf.py<br/>(Main Script)"] --> B["🔍 enhanced_matching.py<br/>(Lane Matching)"]
    A --> C["🔧 src/utils/utils_normalize.py<br/>(Normalization)"]
    A --> D["📍 src/utils/location_canon.py<br/>(Location Expansion)"]
    A --> E["📖 src/utils/pdf_extractors.py<br/>(PDF Field Extraction)"]
    A --> F["📄 src/utils/pdf_text_fallback.py<br/>(Text Extraction)"]
    A --> G["⚙️ src/utils/dn_capacity.py<br/>(Capacity Management)"]
    A --> H["⚙️ config_domestic_v2.json<br/>(Configuration)"]

    E --> F
    G --> C
    B --> C
    B --> D
    E --> C

    classDef mainStyle fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef utilStyle fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef configStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class A mainStyle
    class B,C,D,E,F,G utilStyle
    class H configStyle
```

---

## 6. 성능 메트릭스 시각화

### 매칭 결과 분포
```mermaid
pie title "🎯 최종 매칭 결과 (44 items)"
    "✅ Matched (95.5%)" : 42
    "❌ Unmatched (4.5%)" : 2
```

### 검증 상태 분포
```mermaid
pie title "📊 검증 상태 분포 (42 matched items)"
    "✅ PASS (47.7%)" : 21
    "⚠️ WARN (47.7%)" : 21
    "❌ FAIL (0%)" : 0
```

### Enhanced Matching vs Cross-Validation
```mermaid
graph LR
    A["🔍 Enhanced Lane Matching<br/>79.5% (35/44)"] --> B["🔗 Cross-Validation<br/>95.5% (42/44)"]

    C["📈 Improvement<br/>+16% (+7 items)"]

    A --> C
    B --> C

    classDef originalStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef improvedStyle fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef improvementStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    class A originalStyle
    class B improvedStyle
    class C improvementStyle
```

---

## 7. 데이터 처리 파이프라인

```mermaid
graph TB
    subgraph INPUT_DATA["📥 Input Data"]
        ID1["📊 Invoice: 44 items<br/>Origin, Destination, Vehicle, Rate"]
        ID2["🗺️ ApprovedLaneMap: 124 lanes<br/>Enhanced JSON with rates"]
        ID3["📄 DN PDFs: 36 documents<br/>Supporting Documents"]
    end

    subgraph PROCESSING_STEPS["⚙️ Processing Steps"]
        PS1["🔧 Normalization<br/>Location & Vehicle<br/>Synonyms & Abbreviations"]
        PS2["🔍 Enhanced Matching<br/>4-level fallback<br/>79.5% success"]
        PS3["📖 PDF Parsing<br/>Multi-layer fallback<br/>91.7% success"]
        PS4["🔗 Cross-Validation<br/>1:1 Greedy matching<br/>95.5% success"]
        PS5["📋 Status Classification<br/>PASS/WARN/FAIL<br/>47.7% PASS rate"]
    end

    subgraph OUTPUT_DATA["📤 Output Data"]
        OD1["📈 Final Excel<br/>25 columns, 4 sheets<br/>Hyperlinks + Validation"]
        OD2["📊 Analysis CSVs<br/>Supply-Demand + Candidates<br/>Debug information"]
        OD3["📝 Reports<br/>Complete validation<br/>Performance metrics"]
    end

    ID1 --> PS1
    ID2 --> PS1
    ID3 --> PS3
    PS1 --> PS2
    PS2 --> PS4
    PS3 --> PS4
    PS4 --> PS5
    PS5 --> OD1
    PS5 --> OD2
    PS5 --> OD3

    classDef inputStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef processStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef outputStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px

    class ID1,ID2,ID3 inputStyle
    class PS1,PS2,PS3,PS4,PS5 processStyle
    class OD1,OD2,OD3 outputStyle
```

---

## 8. DN Capacity 관리 시스템

```mermaid
stateDiagram-v2
    [*] --> DN_Available : Initialize DN

    DN_Available --> Check_Capacity : Match Request

    Check_Capacity --> Capacity_OK : Available
    Check_Capacity --> Capacity_Full : Exhausted

    Capacity_OK --> Assign_DN : Match Success
    Capacity_Full --> Auto_Bump : Enable Auto-Bump

    Auto_Bump --> Check_Max_Capacity : Increase Capacity
    Check_Max_Capacity --> Capacity_OK : Under Limit (16)
    Check_Max_Capacity --> Capacity_Full : At Limit

    Assign_DN --> DN_In_Use : Decrease Capacity
    DN_In_Use --> DN_Available : Release

    Capacity_Full --> [*] : DN_CAPACITY_EXHAUSTED

    note right of Auto_Bump
        DN_AUTO_CAPACITY_BUMP=true
        DN_MAX_CAPACITY=16
        Based on demand analysis
    end note
```

---

## 📊 성능 요약

| 지표 | 결과 | 목표 대비 |
|------|------|----------|
| **전체 매칭률** | **95.5%** (42/44) | +5.5%p 초과 🚀 |
| **Enhanced Matching** | 79.5% (35/44) | 기반 성과 |
| **PDF 파싱 성공률** | 91.7% (33/36) | 높은 안정성 |
| **Cross-Validation** | 95.5% (42/44) | 최종 목표 달성 |
| **PASS 비율** | 47.7% (21/42) | 고품질 검증 |
| **FAIL 비율** | 0% (0/42) | **완벽!** 🏆 |

---

## 🔧 주요 설정값

### 유사도 임계값
- **Origin**: 0.27 (낮은 임계값으로 유연성 확보)
- **Destination**: 0.50 (중간 임계값으로 정확성 유지)
- **Vehicle**: 0.30 (낮은 임계값으로 차량 유형 유연성)

### DN Capacity 설정
- **기본 용량**: 1 (1:1 매칭 기본)
- **최대 용량**: 16 (수요 기반 자동 증가)
- **자동 증가**: 활성화 (DN_AUTO_CAPACITY_BUMP=true)

### PDF 추출 우선순위
1. **PyMuPDF** (다단/표 혼합 문서에 강함)
2. **pypdf** (빠르고 경량)
3. **pdfminer.six** (복잡한 레이아웃에 강함)
4. **pdftotext** (외부 도구, 가장 견고)

---

**Last Updated**: 2025-10-13 23:20:00
**Version**: PATCH4 (v4.0)
**Status**: ✅ Production Ready - 95.5% 자동화 달성!
