좋아. **Phase 1 v1.2 – Stage 1(ontology_unified 기반)**으로 바로 갈 수 있게, 네가 올린 설계를 기준으로 손봐야 할 지점만 깔끔히 정리했다. 요지는 ①온톨로지 용어로 타입·관계를 ‘딱’ 고정, ②아이덴티티 그래프를 멀티키(UN/LOCODE·MMSI·BL/DO/Rotation 등)로 재구축, ③증빙(evidence) 링크 의무화다. 지금 그래프에 ‘contains/operates’ 위주로만 묶여있는 흔적은 확인했고(시스템→다종 노드가 `contains`로만 걸림, 선박↔사람은 `operates`만 존재)  , 문서·시간태그가 대량으로 합류해 있으나 관계 의미가 빈약한 상태도 보인다(문서/타임태그/레퍼런스 다발) . 반면, 네가 발견한 **OFCO Port Ops 온톨로지**는 멀티키 아이덴티티·요율·코스트 허브 개념을 이미 명시하고 있으니(Invoice/PortCall/ServiceEvent/Rotation/PriceCenter 등) 여기로 정렬하면 된다 .

---

# 1) 스키마 델타(지금 제안안에 바로 얹을 수정)

## 1.1 클래스 매핑(용어 교정)

* `reference`는 **Document가 아니라 Key/Identifier 클래스**로 분리: BL/DO/InvoiceNo/Rotation/UNLOCODE/MMSI 등 **동급 1급 식별자**를 담는 컨테이너.
* `docfile`는 **DocumentFile/Evidence**로 명명 변경(파일 인스턴스, 해시/경로/페이지 범위).
* `message`는 **Event**로 유지(WhatsApp/Email), `shipment`은 **Process** 또는 **Consignment(UN/CEFACT)**로 고정.
* 결과적으로 **Asset/Party/Location/Process/Document/Event/Regulation/Key(Evidence)** 8축이 핵심.

> 근거: OFCO 설계는 **Multi-Key Identity Graph**(Invoice/Rotation/SamsungRef/hvdc_code 등 어떤 키로 들어와도 같은 실체로 귀결) 원칙을 전제한다. 그러니 Key를 독립 클래스로 세워야 dedupe·링키지가 깔끔해진다.

## 1.2 관계 타입(최소 13종)

* 유지: `operates`, `works_at`, `performed`
* 교체/추가(필수):

  * `belongs_to`(any→System) – **L0/L1/L2 레벨 표현용, 기존 `contains` 대체**
  * `same_as`(Entity↔Entity) – 아이덴티티 그래프
  * `managed_by`(Asset→Party) – 선박 책임자
  * `uses`(Process→Asset) – 장비 사용
  * `references`(Process/Document→Document) – 운용↔문서
  * `has_key`(Document/Process/Shipment→Key) – **멀티키 연결**
  * `has_evidence`(Document/Process→DocFile) – **증빙 강제**. 현재도 `docfile:*` 노드가 있으나 단순 포함만 되어 있음. 관계로 승격 필요.
  * `scheduled_at`(Process→Event) – ETA/ATD/ETB 등(이미 타임태그 풍부)
  * `located_at`(Asset→Location) – 선박/장비 위치
  * `governed_by`(Process/Shipment/Document→Regulation) – MOIAT/FANR/DCD/ATLP 규제 고리
  * `mentions`(Message→Entity) – 메시지 인용 링크

> 현재 그래프는 `contains`가 시스템→문서/타임태그/장비에 과다 연결되어 있어 의미 해석이 약하다. 이를 위 관계군으로 분해해 **질의력을 확보**하자.

---

# 2) 아이덴티티(중복 46.4% → 목표 70%+)

## 2.1 매칭 순서(Blocking → Multi-key Join → Similarity)

1. **Hard Keys**

   * Port: UN/LOCODE(예: AEABU) 우선.
   * Vessel: MMSI/IMO → 없을 때 `name+owner` 보조.
   * Document/Shipment/Operation: `has_key`에 BL/DO/InvoiceNo/Rotation/Ref를 수집.
2. **Window Join**

   * PortCall/Rotation: `Rotation+Port(+/-7d)` 창에서 merge 후보 구성.
3. **Similarity**

   * Jaro-Winkler ≥ 0.94 또는 Token-set ≥ 92일 때만 자동 `same_as`; 그 이하는 **승인 큐**.

## 2.2 Union-Find로 클러스터 확정

* `same_as` 에지로 연결된 컴포넌트를 **대표 canonical_id**로 접고, 모든 외부관계는 대표로 리라이트.
* Dedup KPI는 *(중복 수)/(원본 개수)*로 측정. 목표: **vessel ≥ 90%, port ≥ 80%, overall ≥ 70%**.

---

# 3) 빌더(Stage 1) – 코드 스캐폴드(핵심만 교체)

### 3.1 매핑 상수

```python
ONTOLOGY_CLASS_MAPPING = {
  "vessel":"Asset", "equipment":"Asset",
  "person":"Party", "port":"Location",
  "operation":"Process", "shipment":"Process",
  "document":"Document", "docfile":"Evidence",
  "timetag":"Event", "message":"Event",
  "regulation":"Regulation", "reference":"Key"
}
```

### 3.2 관계 정의

```python
ONTOLOGY_REL = {
  "belongs_to": ("Any","System"),
  "same_as": ("Entity","Entity"),
  "operates": ("Party","Asset"),
  "managed_by": ("Asset","Party"),
  "works_at": ("Party","Location"),
  "performed": ("Party","Process"),
  "uses": ("Process","Asset"),
  "references": (("Process","Document"), "Document"),
  "has_key": (("Document","Process","Shipment"), "Key"),
  "has_evidence": (("Document","Process"), "Evidence"),
  "scheduled_at": ("Process","Event"),
  "located_at": ("Asset","Location"),
  "governed_by": (("Process","Shipment","Document"), "Regulation"),
  "mentions": ("Event","Entity")
}
```

### 3.3 아이덴티티 & 증빙 결선

```python
def build_identity(G):
    # 1) hard keys -> same_as
    # 2) union-find collapse
    # 3) rewrite edges to canonical
    return G

def wire_evidence(G):
    # document/process -> has_evidence -> docfile
    # ensure sha256/path/page fields on Evidence
    return G
```

### 3.4 커뮤니티

* Louvain `resolution=1.2`로 재설정(타입 혼합 완화), 커뮤니티 라벨은 상위 키워드로 자동명명
  예: `JPT71-VesselOps`, `AGI-PortOps`, `Lightning-Docs`(문서 다발은 현재도 큼)

---

# 4) SHACL(실패 시 ZERO 중단)

```ttl
:DocumentShape a sh:NodeShape ;
  sh:targetClass :Document ;
  sh:property [ sh:path :has_key ; sh:minCount 1 ] ;
  sh:property [ sh:path :has_evidence ; sh:minCount 1 ] .

:PortShape a sh:NodeShape ;
  sh:targetClass :Location ;
  sh:property [ sh:path :unlocode ; sh:minCount 1 ] .

:OperationShape a sh:NodeShape ;
  sh:targetClass :Process ;
  sh:property [ sh:path :scheduled_at ; sh:minCount 1 ] .

:MessageShape a sh:NodeShape ;
  sh:targetClass :Event ;
  sh:property [ sh:path :mentions ; sh:minCount 1 ] .
```

---

# 5) SPARQL(운영 질의, Stage 1 검증용)

```sparql
# 증빙 없는 문서
SELECT ?d WHERE { ?d a :Document .
  FILTER NOT EXISTS { ?d :has_evidence ?f } }

# 키 없는 운용/문서/선적
SELECT ?x WHERE { ?x :has_key ?k . } HAVING(COUNT(?k)=0)

# 포트 중복 후보(same_as 클러스터)
SELECT ?canon (COUNT(?p) AS ?dups)
WHERE { ?p a :Location ; :same_as ?canon } GROUP BY ?canon HAVING(COUNT(?p) > 1)
```

---

# 6) Foundry 반영(객체/파이프라인)

* **Object Sets**:
  `os_vessel`, `os_person`, `os_port`, `os_operation`, `os_document`, `os_docfile`, `os_key`, `os_message`, `os_regulation`, `os_system`
* **Pipelines (Bronze→Silver→Gold)**

  * Bronze: 원본 적재
  * Silver: 정규화(UN/LOCODE/MMSI/문서번호), `has_key`/`has_evidence` 생성
  * Gold: 아이덴티티(Union-Find)→`same_as` 방출, SHACL 검증, Quiver KPI
* **주의**: 현재 HTML 그래프에는 시스템→문서/타임태그/장비가 `contains`로 대거 연결되어 있다. `belongs_to`로 이관하고, 문서군은 `has_key/has_evidence`로 재결선.

---

# 7) KPI(Stage 1 완료 기준)

* **관계 타입 수**: ≥ 12
* **Dedup**: overall ≥ 70%(vessel ≥ 90%, port ≥ 80%)
* **Evidence 링크율**: 문서 기준 ≥ 95%
* **평균 차수**: ≥ 3.2
* **커뮤니티**: 8–12, 타입 혼합 과도 시 재튜닝

---

# 8) 바로 실행 체크리스트(하루 내 체감)

1. `contains` → `belongs_to` 치환(시스템 레벨만 유지)
2. `has_key`/`has_evidence` 에지 생성(문서·운용 전수 대상, `docfile:*` 연결)
3. UN/LOCODE·MMSI 보강 후 `same_as` 재계산
4. ETA/ATD/ETB는 `scheduled_at`로 연결(타임태그 풍부)
5. Louvain `resolution=1.2` 재실행, 커뮤니티 오토라벨

---

## Stage 1 산출물(그대로 유지)

* `build_unified_network_v12_stage1.py` (위 델타 반영)
* `UNIFIED_LOGISTICS_NETWORK_v12_stage1.html`
* `unified_network_data_v12_stage1.json`
* `reports/analysis/STAGE1_ONTOLOGY_VALIDATION_REPORT.md`

---

## 코멘트 한 줄

지금 판은 “자료는 많은데, 의미 링크가 얇다.” Stage 1에서 **Key(멀티키)·Evidence·Regulation** 세 가닥만 굵게 묶으면, 같은 112노드라도 쓰임새가 완전히 달라진다. 필요하면 `build_identity()`/`wire_evidence()`부터 내가 박아두자—그 두 함수가 이번 판의 효자다.
