HVDC Pipeline 시스템 아키텍처 문서 v4.0.54

**Samsung C&T Logistics | ADNOC·DSV Strategic Partnership**

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [Core 모듈 아키텍처](#core-모듈-아키텍처)
4. [Stage별 상세 아키텍처](#stage별-상세-아키텍처)
5. [데이터 흐름](#데이터-흐름)
6. [컴포넌트 상호작용](#컴포넌트-상호작용)
7. [설정 및 구성](#설정-및-구성)
8. [확장성 및 유지보수성](#확장성-및-유지보수성)

---

## 시스템 개요

### 목적

HVDC Pipeline은 물류 데이터 처리 자동화 시스템으로, 원본 Excel 파일부터 종합 보고서 및 이상치 탐지까지 4단계 파이프라인을 제공합니다.

### 핵심 원칙

- **Single Source of Truth (SSOT)**: Core 모듈을 통한 중앙 집중식 관리
- **의미 기반 매칭**: 하드코딩 제거, 시맨틱 매칭으로 유연성 확보
- **모듈화**: 각 Stage는 독립적이면서도 Core 모듈을 통해 통합
- **확장성**: 새 벤더/헤더 추가 시 Registry만 수정

---

## 전체 아키텍처

### 시스템 레이어 구조

```mermaid
graph TB
    subgraph "Input Layer"
        A1[Raw Excel Files]
        A2[Case List_Hitachi.xlsx]
        A3[Case List_Simense.xlsx]
        A4[HVDC WAREHOUSE_HITACHI.xlsx]
        A5[HVDC WAREHOUSE_SIMENSE.xlsm]
    end
  
    subgraph "Core Module Layer"
        B1[Header Registry]
        B2[Semantic Matcher]
        B3[Header Detector]
        B4[Header Normalizer]
        B5[File Registry]
        B6[Data Parser]
        B7[File Finder]
    end
  
    subgraph "Processing Layer"
        C1[Stage 1: Data Synchronization]
        C2[Stage 2: Derived Columns]
        C3[Stage 3: Report Generation]
        C4[Stage 4: Anomaly Detection]
    end
  
    subgraph "Output Layer"
        D1[Synced Files]
        D2[Derived Files]
        D3[Report Files]
        D4[Anomaly Reports]
    end
  
    A1 --> B1
    A2 --> C1
    A3 --> C1
    A4 --> C1
    A5 --> C1
  
    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    B5 --> C1
    B6 --> C2
    B7 --> C1
  
    C1 --> C2
    C2 --> C3
    C3 --> C4
  
    C1 --> D1
    C2 --> D2
    C3 --> D3
    C4 --> D4
```

### 전체 파이프라인 흐름

```mermaid
flowchart TD
    Start([시작]) --> LoadConfig[설정 파일 로드]
    LoadConfig --> InitCore[Core 모듈 초기화]
    InitCore --> Stage1[Stage 1: 데이터 동기화]
  
    Stage1 --> S1_HeaderDetect[헤더 자동 탐지]
    S1_HeaderDetect --> S1_SemanticMatch[시맨틱 매칭]
    S1_SemanticMatch --> S1_Sync[Master-Warehouse 동기화]
    S1_Sync --> S1_Metadata[메타데이터 설정]
    S1_Metadata --> S1_Color[색상 표시]
    S1_Color --> Stage1Out[*.synced_v3.4.xlsx]
  
    Stage1Out --> Stage2[Stage 2: 파생 컬럼]
    Stage2 --> S2_Derived[13개 파생 컬럼 계산]
    S2_Derived --> S2_SQM[SQM 계산]
    S2_SQM --> S2_Stack[Stack_Status 파싱]
    S2_Stack --> S2_Split[벤더별 파일 분리]
    S2_Split --> Stage2Out[*.xlsx]
  
    Stage2Out --> Stage3[Stage 3: 보고서 생성]
    Stage3 --> S3_Flow[Flow Code 계산]
    S3_Flow --> S3_Monthly[월별 입출고 분석]
    S3_Monthly --> S3_Pivot[피벗 테이블 생성]
    S3_Pivot --> S3_Sheets[12개 시트 생성]
    S3_Sheets --> Stage3Out[종합리포트.xlsx]
  
    Stage3Out --> Stage4[Stage 4: 이상치 탐지]
    Stage4 --> S4_Balanced[Balanced Boost 분석]
    S4_Balanced --> S4_Rule[룰 기반 검증]
    S4_Rule --> S4_ML[ML 기반 탐지]
    S4_ML --> S4_Visualize[색상 시각화]
    S4_Visualize --> Stage4Out[anomaly_report.xlsx]
  
    Stage4Out --> End([완료])
  
    style Start fill:#90EE90
    style End fill:#FFB6C1
    style Stage1 fill:#87CEEB
    style Stage2 fill:#87CEEB
    style Stage3 fill:#87CEEB
    style Stage4 fill:#87CEEB
```

---

## Core 모듈 아키텍처

### Core 모듈 구조

```mermaid
graph LR
    subgraph "Core Module v1.2.0"
        A[Header Registry<br/>63개 표준 헤더 정의]
        B[Semantic Matcher<br/>의미 기반 매칭]
        C[Header Detector<br/>자동 헤더 탐지]
        D[Header Normalizer<br/>헤더 정규화]
        E[File Registry<br/>파일 경로 관리]
        F[Data Parser<br/>데이터 파싱]
        G[File Finder<br/>파일 자동 탐지]
        H[Name Resolver<br/>유연한 이름 매칭]
    end
  
    A --> B
    D --> B
    C --> B
    E --> B
    F --> B
    G --> E
    H --> B
  
    style A fill:#FFE4B5
    style B fill:#FFE4B5
    style C fill:#FFE4B5
    style D fill:#FFE4B5
    style E fill:#FFE4B5
    style F fill:#FFE4B5
    style G fill:#FFE4B5
    style H fill:#FFE4B5
```

### Header Registry 구조

```mermaid
classDiagram
    class HeaderRegistry {
        +register(HeaderDefinition)
        +get_by_category(HeaderCategory)
        +get_aliases(semantic_key)
        +get_warehouse_columns()
        +get_site_columns()
        +get_date_columns()
    }
  
    class HeaderDefinition {
        +semantic_key: str
        +category: HeaderCategory
        +aliases: List[str]
        +description: str
        +required: bool
        +data_type: str
    }
  
    class HeaderCategory {
        <<enumeration>>
        IDENTIFICATION
        TEMPORAL
        LOCATION
        QUANTITY
        STATUS
        HANDLING
        DERIVED
        METADATA
    }
  
    HeaderRegistry "1" --> "*" HeaderDefinition
    HeaderDefinition --> HeaderCategory
```

### Semantic Matcher 동작 원리

```mermaid
sequenceDiagram
    participant DF as DataFrame
    participant SM as SemanticMatcher
    participant HR as HeaderRegistry
    participant HN as HeaderNormalizer
  
    DF->>SM: match_dataframe(df, semantic_keys)
    SM->>HR: get_aliases(semantic_key)
    HR-->>SM: aliases list
    SM->>HN: normalize(column_name)
    HN-->>SM: normalized_name
    SM->>SM: calculate_confidence()
    SM-->>DF: MatchReport
```

---

## Stage별 상세 아키텍처

### Stage 1: 데이터 동기화

```mermaid
graph TD
    subgraph "Stage 1: Data Synchronization"
        S1_Input[입력 파일]
        S1_HD[Header Detector]
        S1_SM[Semantic Matcher]
        S1_Load[데이터 로드]
        S1_Match[Case No. 매칭]
        S1_Update[데이터 업데이트]
        S1_Merge[SIEMENS 병합]
        S1_Meta[메타데이터 설정]
        S1_Color[색상 적용]
        S1_Output[출력 파일]
    end
  
    S1_Input --> S1_HD
    S1_HD --> S1_Load
    S1_Load --> S1_SM
    S1_SM --> S1_Match
    S1_Match --> S1_Update
    S1_Update --> S1_Merge
    S1_Merge --> S1_Meta
    S1_Meta --> S1_Color
    S1_Color --> S1_Output
  
    style S1_HD fill:#FFB6C1
    style S1_SM fill:#FFB6C1
    style S1_Meta fill:#FFB6C1
```

### Stage 2: 파생 컬럼 생성

```mermaid
graph LR
    subgraph "Stage 2: Derived Columns"
        S2_Input[Synced File]
        S2_Status[Status 컬럼<br/>6개]
        S2_Handling[Handling 컬럼<br/>5개]
        S2_Analysis[Analysis 컬럼<br/>2개]
        S2_Split[벤더별 분리]
        S2_Output[Derived Files]
    end
  
    S2_Input --> S2_Status
    S2_Input --> S2_Handling
    S2_Input --> S2_Analysis
    S2_Status --> S2_Split
    S2_Handling --> S2_Split
    S2_Analysis --> S2_Split
    S2_Split --> S2_Output
  
    style S2_Status fill:#87CEEB
    style S2_Handling fill:#87CEEB
    style S2_Analysis fill:#87CEEB
```

### Stage 3: 보고서 생성

```mermaid
graph TD
    subgraph "Stage 3: Report Generation"
        S3_Input[Derived Files]
        S3_Flow[Flow Code 계산]
        S3_Inbound[입고 분석]
        S3_Outbound[출고 분석]
        S3_Monthly[월별 집계]
        S3_SQM[SQM 재고 분석]
        S3_Stats[통계 시트]
        S3_Sheets[12개 시트 생성]
        S3_Output[종합리포트.xlsx]
    end
  
    S3_Input --> S3_Flow
    S3_Flow --> S3_Inbound
    S3_Flow --> S3_Outbound
    S3_Inbound --> S3_Monthly
    S3_Outbound --> S3_Monthly
    S3_Monthly --> S3_Sheets
    S3_SQM --> S3_Sheets
    S3_Stats --> S3_Sheets
    S3_Sheets --> S3_Output
  
    style S3_Flow fill:#98FB98
    style S3_Monthly fill:#98FB98
    style S3_Sheets fill:#98FB98
```

### Stage 4: 이상치 탐지

```mermaid
graph TD
    subgraph "Stage 4: Anomaly Detection"
        S4_Input[Report File]
        S4_Rule[룰 기반 검증]
        S4_Stat[통계 기반 검증]
        S4_ML[ML 기반 탐지]
        S4_Boost[Balanced Boost]
        S4_ECDF[ECDF 캘리브레이션]
        S4_Risk[위험도 계산]
        S4_Visualize[색상 시각화]
        S4_Output[Anomaly Report]
    end
  
    S4_Input --> S4_Rule
    S4_Input --> S4_Stat
    S4_Input --> S4_ML
    S4_Rule --> S4_Boost
    S4_Stat --> S4_Boost
    S4_ML --> S4_Boost
    S4_Boost --> S4_ECDF
    S4_ECDF --> S4_Risk
    S4_Risk --> S4_Visualize
    S4_Visualize --> S4_Output
  
    style S4_Boost fill:#DDA0DD
    style S4_ECDF fill:#DDA0DD
    style S4_Visualize fill:#DDA0DD
```

---

## 데이터 흐름

### 전체 데이터 변환 파이프라인

```mermaid
flowchart LR
    subgraph "Raw Data"
        R1[Case List<br/>Hitachi<br/>~6,919 rows]
        R2[Case List<br/>Simense<br/>~1,606 rows]
        R3[Warehouse<br/>Hitachi<br/>~8,930 rows]
        R4[Warehouse<br/>Simense<br/>~1,526 rows]
    end
  
    subgraph "Stage 1 Output"
        S1O[Synced File<br/>~8,697 rows<br/>45 columns]
    end
  
    subgraph "Stage 2 Output"
        S2O1[HITACHI<br/>~7,028 rows<br/>57 columns]
        S2O2[SIEMENS<br/>~1,606 rows<br/>57 columns]
    end
  
    subgraph "Stage 3 Output"
        S3O[종합리포트<br/>12 sheets<br/>63 columns]
    end
  
    subgraph "Stage 4 Output"
        S4O[Anomaly Report<br/>~182 anomalies<br/>JSON + Excel]
    end
  
    R1 --> S1O
    R2 --> S1O
    R3 --> S1O
    R4 --> S1O
  
    S1O --> S2O1
    S1O --> S2O2
  
    S2O1 --> S3O
    S2O2 --> S3O
  
    S3O --> S4O
  
    style R1 fill:#FFE4B5
    style R2 fill:#FFE4B5
    style R3 fill:#FFE4B5
    style R4 fill:#FFE4B5
    style S1O fill:#87CEEB
    style S2O1 fill:#87CEEB
    style S2O2 fill:#87CEEB
    style S3O fill:#98FB98
    style S4O fill:#DDA0DD
```

### 메타데이터 흐름

```mermaid
sequenceDiagram
    participant S1 as Stage 1
    participant Core as Core Module
    participant S2 as Stage 2
    participant S3 as Stage 3
  
    S1->>Core: Source_Vendor 설정
    Core-->>S1: 99.3% coverage
    S1->>S2: Source_Vendor 전달
    S2->>S2: Source_Vendor 보존
    S2->>S3: Source_Vendor 전달
    S3->>Core: get_source_file_name(vendor)
    Core-->>S3: Source_File 동적 생성
    S3->>S3: Source_Sheet 설정
```

---

## 컴포넌트 상호작용

### Core 모듈과 Stage 간 상호작용

```mermaid
graph TB
    subgraph "Core Module"
        C1[Header Registry]
        C2[Semantic Matcher]
        C3[File Registry]
        C4[Data Parser]
    end
  
    subgraph "Stage 1"
        S1A[Data Synchronizer]
        S1B[Header Detection]
        S1C[Metadata Setting]
    end
  
    subgraph "Stage 2"
        S2A[Derived Processor]
        S2B[SQM Calculator]
        S2C[Stack Parser]
    end
  
    subgraph "Stage 3"
        S3A[Report Generator]
        S3B[Flow Calculator]
        S3C[Sheet Creator]
    end
  
    subgraph "Stage 4"
        S4A[Anomaly Detector]
        S4B[Risk Calculator]
        S4C[Visualizer]
    end
  
    C1 --> S1A
    C2 --> S1A
    C3 --> S1A
    C1 --> S1B
    C3 --> S1C
  
    C1 --> S2A
    C4 --> S2B
    C4 --> S2C
  
    C1 --> S3A
    C3 --> S3A
    C1 --> S3C
  
    C1 --> S4A
    C2 --> S4A
```

### 파일 탐지 및 선택 프로세스

```mermaid
flowchart TD
    Start([파이프라인 시작]) --> FF[File Finder]
    FF --> Scan[data/raw 폴더 스캔]
    Scan --> Match[Vendor 매칭]
    Match --> Score[점수 계산]
    Score --> Select[최고 점수 파일 선택]
    Select --> HE{HITACHI?}
    Select --> SIM{SIEMENS?}
    HE -->|Yes| HE_File[Case List_Hitachi.xlsx]
    SIM -->|Yes| SIM_File[Case List_Simense.xlsx]
    HE_File --> Stage1[Stage 1 실행]
    SIM_File --> Stage1
    Stage1 --> End([완료])
  
    style FF fill:#FFB6C1
    style Score fill:#FFB6C1
    style Select fill:#FFB6C1
```

---

## 설정 및 구성

### 설정 파일 구조

```mermaid
graph TD
    subgraph "Configuration Files"
        CF1[pipeline_config.yaml<br/>전체 파이프라인 설정]
        CF2[stage2_derived_config.yaml<br/>Stage 2 설정]
        CF3[stage4_anomaly.yaml<br/>Stage 4 설정]
    end
  
    subgraph "Core Configuration"
        CC1[header_registry.py<br/>63개 헤더 정의]
        CC2[file_registry.py<br/>파일 경로 정의]
        CC3[standard_header_order.py<br/>헤더 순서 정의]
    end
  
    CF1 --> Stage1
    CF1 --> Stage2
    CF1 --> Stage3
    CF1 --> Stage4
  
    CF2 --> Stage2
    CF3 --> Stage4
  
    CC1 --> AllStages[모든 Stage]
    CC2 --> AllStages
    CC3 --> AllStages
  
    style CF1 fill:#FFE4B5
    style CF2 fill:#FFE4B5
    style CF3 fill:#FFE4B5
    style CC1 fill:#FFB6C1
    style CC2 fill:#FFB6C1
    style CC3 fill:#FFB6C1
```

---

## 확장성 및 유지보수성

### 새 벤더 추가 프로세스

```mermaid
flowchart TD
    Start([새 벤더 추가]) --> Reg1[Header Registry<br/>헤더 별칭 추가]
    Reg1 --> Reg2[File Registry<br/>벤더 정의 추가]
    Reg2 --> Test[테스트 실행]
    Test --> Pass{테스트 통과?}
    Pass -->|No| Fix[수정]
    Fix --> Test
    Pass -->|Yes| Deploy[배포]
    Deploy --> End([완료])
  
    style Reg1 fill:#90EE90
    style Reg2 fill:#90EE90
    style Test fill:#FFB6C1
```

### 새 헤더 추가 프로세스

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant HR as Header Registry
    participant SM as Semantic Matcher
    participant S1 as Stage 1
    participant S2 as Stage 2
    participant S3 as Stage 3
    participant S4 as Stage 4
  
    Dev->>HR: HeaderDefinition 추가
    HR->>SM: 자동 반영
    SM->>S1: 자동 인식
    SM->>S2: 자동 인식
    SM->>S3: 자동 인식
    SM->>S4: 자동 인식
    Note over S1,S4: 코드 수정 불필요!
```

---

## 성능 최적화

### 벡터화 최적화 (Stage 3)

```mermaid
graph LR
    subgraph "이전 방식"
        O1[iterrows<br/>155초]
    end
  
    subgraph "최적화 후"
        N1[벡터화 연산<br/>28초]
        N2[melt/groupby<br/>82% 개선]
    end
  
    O1 --> N1
    N1 --> N2
  
    style O1 fill:#FFB6C1
    style N1 fill:#90EE90
    style N2 fill:#90EE90
```

---

## 보안 및 데이터 무결성

### Raw Data Protection

```mermaid
flowchart TD
    Start([파이프라인 실행]) --> Hash1[MD5 해시 계산]
    Hash1 --> Store[Baseline 저장]
    Store --> Process[데이터 처리]
    Process --> Hash2[MD5 해시 재계산]
    Hash2 --> Compare[Baseline과 비교]
    Compare --> Match{일치?}
    Match -->|Yes| Pass[검증 통과]
    Match -->|No| Fail[검증 실패]
    Fail --> Alert[알림 발송]
    Pass --> End([완료])
  
    style Hash1 fill:#FFB6C1
    style Hash2 fill:#FFB6C1
    style Compare fill:#FFB6C1
```

---

## 결론

HVDC Pipeline v4.0.54는 다음과 같은 아키텍처 특징을 가집니다:

1. **중앙 집중식 Core 모듈**: 모든 Stage가 공통 Core 모듈 사용
2. **의미 기반 매칭**: 하드코딩 완전 제거
3. **모듈화된 구조**: 각 Stage는 독립적이면서도 통합
4. **확장성**: 새 벤더/헤더 추가 시 Registry만 수정
5. **성능 최적화**: 벡터화 연산으로 82% 성능 개선
6. **데이터 무결성**: Raw Data Protection으로 검증

이 아키텍처는 유지보수성, 확장성, 성능을 모두 고려한 설계입니다.

---

**버전**: v4.0.54
**최종 업데이트**: 2025-01-25
**작성자**: AI Development Team

```

이 문서는 다음을 포함합니다:

1. 전체 시스템 아키텍처 다이어그램
2. Core 모듈 상세 구조
3. Stage별 상세 아키텍처
4. 데이터 흐름 및 변환 과정
5. 컴포넌트 간 상호작용
6. 설정 및 구성 관리
7. 확장성 및 유지보수성 가이드

모든 다이어그램은 Mermaid 형식으로 작성되어 GitHub, GitLab, Notion 등에서 렌더링됩니다.
```
