봤다. 지금 스냅샷(노드 112 / 엣지 168 / 커뮤니티 9 / 중복제거율 46.4%)은 “움직이기 시작한 그래프” 수준이야. 쓸만한데, 운용하려면 뼈대를 두세 군데 갈아껴야 한다. 아래는 v1.2 재설계 제안—바로 손댈 순서까지 적었다.

# 0) 핵심 진단 (한 줄씩)

* **엣지 스키마가 얇다**: contains/operates/works_at/performed 4종만 써서, 문서·규제·시스템·동일성 링크가 빠져 있음 → 질의력이 약해짐.
* **아이덴티티 그래프 미흡**: vessel·port 중복제거율이 낮다(특히 port 33.3%). `same_as`/`id:Key` 계층과 정규화 룰이 필요.
* **계층 구조 과도 분할**: 5단은 과함. 시스템/코어/지원/증거 4단으로 재정렬 권장.
* **메시지·증빙 결여**: WhatsApp/Email 스레드, 파일(docfile)의 “증거 링크”가 희박 → 운영 감사선(trace)이 끊긴다.
* **커뮤니티 9개는 적정**인데, 해석 친화도가 떨어짐(타입 혼합). 타입/도메인 레이어드 커뮤니티가 필요.

---

# 1) v1.2 목표(KPI)

* **중복 제거율**: overall ≥ **85%**, vessel ≥ **90%**, port ≥ **80%**
* **엣지 다양성**: 관계타입 ≥ **12**(현재 4) / 문서↔레퍼런스 커버리지 ≥ **90%**
* **질의 SLA**: 핵심 질의(sub-5s) 10개 패스(Shipment/DO/Permit/Cost/WhatsApp 태그 기반)
* **감사성**: 모든 문서·메시지에 **evidence 링크 ≥ 95%** (docfile/page/line 또는 hash)

---

# 2) 스키마 우선(패치 목록)

## 2.1 노드 타입(추가/정리)

* 유지: `vessel, person, port, operation, document, equipment, reference, timetag, docfile`
* **추가**: `system(JPT71/ABU/Lightning/docs)`, `message(WhatsApp/Email)`, `regulation(MOIAT/FANR/DCD/ATLP)`, `shipment`
* **정리**: `document` = 의미객체(예: BL), `docfile` = 파일 인스턴스(버전·페이지·해시)

## 2.2 관계타입(v1.2 표준)

| 관계               | From      | To        |          |            |           |
| ---------------- | --------- | --------- | -------- | ---------- | --------- |
| **belongs_to**   | any       | system    |          |            |           |
| **same_as**      | entity    | entity    |          |            |           |
| **managed_by**   | vessel    | person    |          |            |           |
| **operates**     | person    | vessel    |          |            |           |
| **works_at**     | person    | port      |          |            |           |
| **performed**    | person    | operation |          |            |           |
| **uses**         | operation | equipment |          |            |           |
| **references**   | operation | document  |          |            |           |
| **has_evidence** | document  | docfile   |          |            |           |
| **has_key**      | document  | reference | shipment | reference  |           |
| **scheduled_at** | operation | timetag   |          |            |           |
| **communicates** | person    | person    |          |            |           |
| **mentions**     | message   | vessel    | port     | document   | equipment |
| **governed_by**  | operation | shipment  | document | regulation |           |

> 최소 이 13종은 v1.2에서 **반드시** 써.

---

# 3) 아이덴티티 & 정규화(중복율을 ‘수학’으로 잡기)

## 3.1 Multi-Key Identity Graph

* `reference`를 **슈퍼키(id:Key)**로 삼고, BL/DO/Invoice/Rotation/SamsungRef/hvdc_code/UNLOCODE를 **동급 1급 엔티티**로 수집.
* 규칙:

  1. `Rotation+港(+/-7d)` → 같은 PortCall 후보
  2. `BL or SamsungRef` 동일 → 같은 Shipment/Operation 배치
  3. `UN/LOCODE + Port 별칭` → 같은 Port 후보

## 3.2 정규화 룰(패치 세트)

* **Port**: UN/LOCODE(예: AEABU), 좌표±500m, 영문·약어 동의어 사전 → 3중 매칭 후 score≥0.9에만 `same_as`
* **Vessel**: MMSI/IMO 우선, 없다면 `name+owner` 동형·철자거리 ≤ 0.1
* **Person**: 이메일/전화 해시, 역할 태그(“PCC/LS”) + 동음 이의 분리(조직 소속 포함)
* **Document**: `docType(BL/DO/…) + number` 표준화, 파일명 패턴 `YYYYMMDD_[KEY]_[DOC]_v##`

---

# 4) 그래프 빌드(코드/검증)

## 4.1 빌더 함수(보강안)

```python
def link_identity(G):
    # reference(Key) <-[has_key]- document/shipment/operation
    # then collapse clusters to canonical_id, emit owl:sameAs between duplicates
    ...

def attach_evidence(G):
    # document --has_evidence--> docfile(page, sha256)
    ...

def ingest_messages(G, wa_txt, email_json):
    # message(nodes) + mentions edges to entities via regex/alias map
    ...

def bind_regulations(G):
    # governed_by edges: FANR/MOIAT/DCD/ATLP rules per doc/op/shipment
    ...
```

## 4.2 SHACL(필수 제약—실패 시 ZERO 중단)

* **DocumentShape**: `docType in {BL,DO,CIPL,Invoice,Permit}` ∧ `has_key ≥1` ∧ `has_evidence ≥1`
* **PortShape**: `has UNLOCODE or (lat,lon)`
* **MessageShape**: `hasTag ≥1`(URGENT/ACTION/…) ∧ `sentAt` in Asia/Dubai
* **OperationShape**: `scheduled_at` 존재 ∧ `uses` 장비 명시(필수 작업군)
* **RegulationLink**: `governed_by` 누락 시 해당 Activity 시작 차단

## 4.3 SPARQL(운영 질의 예)

* **중복 감지(포트)**

```sparql
SELECT ?p_norm (COUNT(DISTINCT ?p) AS ?dups)
WHERE { ?p a :Port ; :same_as ?p_norm . } GROUP BY ?p_norm HAVING(COUNT(?p)>1)
```

* **증빙 없는 문서**

```sparql
SELECT ?d WHERE { ?d a :Document . FILTER NOT EXISTS { ?d :has_evidence ?f } }
```

* **규제 미연결 작업**

```sparql
SELECT ?op WHERE { ?op a :Operation . FILTER NOT EXISTS { ?op :governed_by ?reg } }
```

---

# 5) 커뮤니티(읽히는 클러스터로)

* **알고리즘**: Louvain(resolution ~ **1.2**) + 타입별 마스크(사람/문서/작업) → 혼합군 제거
* **레이블링**: 커뮤니티별 상위 엔티티(Top-5 키)로 자동 이름: `AGI-PortOps`, `JPT71-VesselOps`, `OFCO-Invoice` …
* **목표**: 8–12개 유지. 각 커뮤니티에 **대표 규제/문서/시스템** 3축이 모두 보여야 한다.

---

# 6) 계층 구조(4단으로 리팩터)

```
L0  ProjectRoot(HVDC)
L1  Systems(JPT71/ABU/Lightning/docs)
L2  Domain(Vessel/Port/Person/Operation/Shipment/Equipment)
L3  Evidence/Time/Keys/Regulation/Message (docfile, timetag, reference, regulation, message)
```

* `contains`는 **L0→L1**에서만.
* **L2↔L3**는 관계 타입 위주(`has_evidence/scheduled_at/has_key/governed_by/mentions`), 트리 종속 아님.

---

# 7) Foundry 설계(오브젝트/파이프라인)

## 7.1 Ontology Objects

* **Entities**: Vessel, Port, Person, Operation, Shipment, Equipment, Document, DocFile, Reference(Key), Regulation, Message, System
* **Linkers**: `same_as`, `has_key`, `has_evidence`, `governed_by`, `mentions`, `belongs_to`, `scheduled_at`, `uses`

## 7.2 Pipelines

* **Bronze**: 원천 수집(JPT71/ABU/Lightning/docs/WA/Email) 그대로 저장
* **Silver**: 정규화(UNLOCODE/MMSI/포맷·단위), **아이덴티티 매칭(score 산출)**, 타임존 정합(Asia/Dubai)
* **Gold**: 온톨로지 바인딩(엔티티/링커 생성), **SHACL 검증 → 실패 ZERO 로그 + 수리 큐**
* **Quiver/Workshop**: 커뮤니티/예외피드 대시보드 + 알림(TG/Email)

---

# 8) “지금 당장” 패치 순서(하루 안에 체감)

1. **관계 타입 확장**: `belongs_to/same_as/has_key/has_evidence/governed_by/mentions` 추가 생성
2. **포트·선박 정규화**: UNLOCODE·MMSI 채움 → `same_as` 재계산 → dedup 목표치 달성
3. **문서–증빙 연결**: 문서 당 docfile 1건 이상 강제(없으면 ZERO)
4. **WhatsApp 인입**: `[TAG]` 헤더 파싱 → `message` 노드 + `mentions` 엣지 부여
5. **커뮤니티 재계산**: resolution 1.2, 타입 마스크 적용 → 라벨링

---

# 9) 검증 게이트 & 알림(운영용)

* **Gate-1 Identity**: `same_as` 없는 후보 > 0 → `/halt --context identity --needed "UNLOCODE or MMSI"`
* **Gate-2 Evidence**: 문서 `has_evidence`=0 → `/halt --context evidence --owner "Doc Control"`
* **Gate-3 Regulation**: FANR/MOIAT/DCD 필요 작업인데 미연결 → `/halt --context compliance`
* **Exception Feed**: 위반건 실시간 → Telegram “OpsRoom”

---

# 10) 목표 수치(빌드 후 체크)

* 평균 차수(2E/N): **≥ 3.5** (현재 3.0 → 관계 확장으로 상향)
* 문서↔증빙 링크율: **≥ 95%**
* 메시지↔실세계(`mentions`) 링크율: **≥ 70%**(초기), 85% 목표
* 커뮤니티당 대표 규제/문서/시스템 3축 모두 존재: **100%**

---

# 11) 샘플 명령 세트(운영 명령어)

```
/graph-patch --add-relations managed_by,uses,references,has_evidence,has_key,governed_by,mentions
/normalize --port UNLOCODE --vessel MMSI --person role-alias
/identity-recalc --threshold 0.90 --emit same_as
/ingest-wa --file abu_wa_2p5mb.txt --tag-header true --link mentions
/shacl-validate --target ALL --zero-on-fail true
/community-run --algo louvain --resolution 1.2 --type-mask true --autolabel
```

---

# 12) 네트워크 HTML(업로드본) 개선 팁

* **레벨별 LOD 토글**(L1/L2/L3) + **타입별 필터**(문서/규제/메시지)
* 노드 라벨링: `name | type | system` 3줄 이내, 문서는 `docType#number`
* 툴팁에 evidence/page/hash, regulation 코드(예: FANR-IMP-60D) 노출

---

## 한 줄 정리

그래프는 **종류가 아니라 관계의 밀도**가 힘이다. v1.2에서 **아이덴티티 + 증거 + 규제 + 메시지** 네 개만 제대로 물리면, 같은 112노드라도 ‘운영이 되는’ 네트워크로 바뀐다. 필요하면 위 순서대로 바로 집행하자.
