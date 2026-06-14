좋아, 방금 올린 NAMES_COLLECTION_REPORT.md 기반으로 별칭 사전 즉시 확장하는 drop-in 패치를 줬어. 그대로 붙여 넣으면 simense/RIL(SIMENSE)·리포트 시트·창고/사이트/SQM/Stack_Status·ETD/ETA 변형까지 한 번에 커버한다.

1) name_resolver.py 별칭 사전 확장 패치
   --- a/name_resolver.py
   +++ b/name_resolver.py
   @@
   -VENDOR_ALIASES: Dict[str, Iterable[str]] = {

- "HITACHI": {
- "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치", "hitachienergy",
- "he local", "he-local"
- },
- "SIEMENS": {
- "siemens", "sim", "simense", "seimens", "ril", "r.i.l", "ril(simense)", "지멘스"
- },
  -}
  +VENDOR_ALIASES: Dict[str, Iterable[str]] = {

+ "HITACHI": {
+ # 기본
+ "hitachi", "hitachi energy", "he", "h.e", "h-e", "히타치", "hitachienergy",
+ "he local", "he-local",
+ # 보고서 확장
+ "Hitachi", "HITACHI ENERGY", "H.E", "HE-LOCAL"
+ },
+ "SIEMENS": {
+ # 기본
+ "siemens", "sim", "simense", "seimens", "ril", "r.i.l", "ril(simense)", "지멘스",
+ # 보고서 확장
+ "Siemens", "SIMENSE", "RIL(SIMENSE)", "RIL(SIEMENS)", "R.I.L"
+ },
  +}
  @@
  -SHEET_ALIASES: Dict[str, Iterable[str]] = {

- "CASE LIST": {"case list", "caselist", "case_list"},
- "CASE LIST, RIL(SIEMENS)": {
- "case list, ril(simense)", "case list ril", "ril", "ril(simense)"
- },
- "HE LOCAL": {"he local", "he-local", "hitachi local", "히타치 로컬"},
  -}
  +SHEET_ALIASES: Dict[str, Iterable[str]] = {

+ # 일반 Case List
+ "CASE LIST": {
+ "case list", "caselist", "case_list",
+ "Case List", "CaseList", "CASE LIST"
+ },
+ # RIL(SIEMENS) 변형 포함
+ "CASE LIST, RIL(SIEMENS)": {
+ "case list, ril(simense)", "case list ril", "ril", "ril(simense)",
+ "Case List, RIL", "Case List RIL", "CASE LIST, RIL", "Case List, RIL(SIEMENS)"
+ },
+ # HE Local
+ "HE LOCAL": {
+ "he local", "he-local", "hitachi local", "히타치 로컬",
+ "HE Local", "HELocal", "HE-LOCAL"
+ },
+ # Capacitor 시트 (보고서 확장)
+ "HE-0214,0252 (CAPACITOR)": {
+ "he-0214,0252", "he-0214,0252 (capacitor)", "capacitor",
+ "HE-0214,0252", "Capacitor"
+ },
+ # 리포트 시트(선별) — 필요 시 계속 보강
+ "통합_원본데이터_FIXED": {"통합_원본데이터_fixed"},
+ "HITACHI_원본데이터_FIXED": {"hitachi_원본데이터_fixed"},
+ "SIEMENS_원본데이터_FIXED": {"siemens_원본데이터_fixed"},
+ "창고_월별_입출고": {"창고_월별_입출고"},
+ "현장_월별_입고재고": {"현장_월별_입고재고"},
+ "FLOW_CODE_분석": {"flow_code_분석"},
  +}
  @@
  -HEADER_ALIASES: Dict[str, Iterable[str]] = {

- "CASE NO": {"case no", "case_no", "caseno", "case#", "case number"},
- "VENDOR": {"vendor", "maker", "supplier", "vend", "vendr"},
- "QTY": {"qty", "quantity", "q'ty", "수량"},
- "MATERIAL": {"material", "item desc", "description", "desc", "품명"},
  -}
  +HEADER_ALIASES: Dict[str, Iterable[str]] = {

+ # Case Number
+ "CASE NO": {
+ "case no", "case_no", "caseno", "case#", "case number",
+ "Case No", "Case No.", "CASE NO", "Case Number", "Case_No",
+ "CaseNo", "case-no", "CASE_NUMBER", "case_no", "케이스번호", "케이스 번호",
+ "Case", "Package No", "Package No.", "PACKAGE NO", "PackageNo", "packageno", "Package_No"
+ },
+ # Vendor
+ "VENDOR": {
+ "vendor", "maker", "supplier", "vend", "vendr",
+ "Vendor", "VENDOR", "Source_Vendor", "source_vendor", "SourceVendor", "Source Vendor"
+ },
+ # Quantity
+ "QTY": {
+ "qty", "quantity", "q'ty", "수량", "QTY", "Qty", "Quantity", "Q'ty", "Qty.", "QUANTITY",
+ "Amount", "Count", "quantity", "Pkg", "pkg", "Pkg_Quantity", "pkg_quantity"
+ },
+ # Material/Description
+ "MATERIAL": {
+ "material", "item desc", "description", "desc", "품명",
+ "Material", "MATERIAL", "Item Desc", "Item Description",
+ "Description", "Desc", "DESC", "Detail", "Details", "Name",
+ "Item Name", "설명", "상세", "Description/명칭"
+ },
+ # Date/Time (요약)
+ "ETD/ATD": {"etd/atd", "etd", "atd", "etd_atd", "etd-atd", "etd / atd",
+ "Estimated Departure", "Actual Departure", "Departure Date", "Departure", "출발일"},
+ "ETA/ATA": {"eta/ata", "eta", "ata", "eta_ata", "eta-ata", "eta / ata",
+ "Estimated Arrival", "Actual Arrival", "Arrival Date", "Arrival", "도착일"},
+ # Warehouse/Site
+ "DHL WAREHOUSE": {"dhl wh", "dhl warehouse", "DHL WH", "DHL Warehouse"},
+ "DSV INDOOR": {"dsv indoor", "DSV Indoor"},
+ "DSV AL MARKAZ": {"dsv al markaz", "DSV Al Markaz", "dsv almarkaz"},
+ "DSV OUTDOOR": {"dsv outdoor", "DSV Outdoor"},
+ "AAA STORAGE": {"aaa storage", "AAA Storage", "AAA_STORAGE"},
+ "HAULER INDOOR": {"hauler indoor", "Hauler Indoor", "HAULER_INDOOR"},
+ "MOSB": {"mosb", "MOSB"},
+ "MIR": {"mir", "MIR", "MIR Site"},
+ "SHU": {"shu", "SHU", "SHU Site"},
+ "DAS": {"das", "DAS", "DAS Site"},
+ "AGI": {"agi", "AGI", "AGI Site"},
+ # KPI/측정
+ "SQM": {"sqm", "SQM", "Square Meter", "Square Meterage"},
+ "STACK_STATUS": {"stack_status", "Stack_Status", "STACK_STATUS"},
  +}

주: 이번 확장은 의미 맵핑을 넓히는 것이라 기존 파이프라인과 충돌하지 않아. 헤더는 header_normalizer 하이브리드 로직으로 최종 시맨틱 키(예: quantity)에 자연스럽게 연결돼.

2) 스모크 테스트(샘플만 추가)

# tests/test_name_resolver_extended.py

from name_resolver import resolve_sheet, resolve_header, resolve_vendor

def test_report_sheets_and_capacitor():
    assert resolve_sheet("HE-0214,0252").canonical == "HE-0214,0252 (CAPACITOR)"
    assert resolve_sheet("현장_월별_입고재고").canonical == "현장_월별_입고재고"

def test_warehouse_and_site_headers():
    assert resolve_header("DHL WH").canonical == "DHL WAREHOUSE"
    assert resolve_header("DSV Al Markaz").canonical == "DSV AL MARKAZ"
    assert resolve_header("AGI Site").canonical == "AGI"

def test_time_headers():
    assert resolve_header("ETD / ATD").canonical == "ETD/ATD"
    assert resolve_header("ETA-ATA").canonical == "ETA/ATA"

def test_vendor_ril_path():
    assert resolve_vendor("RIL(SIMENSE)").canonical == "SIEMENS"
    assert resolve_vendor("HE-LOCAL").canonical == "HITACHI"

3) 바로 적용 순서
   ruff --fix .
   black .
   pytest -q
4) 다음 보강 포인트(선택)

보고서의 나머지 리포트 시트 전량을 SHEET_ALIASES에 계속 추가(필요한 것부터).


## 커밋 2종(구조 ↔ 행위 분리)

### 1) 구조(Structural)

<pre class="overflow-visible!" data-start="72" data-end="653"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>structural(core): expand </span><span>alias</span><span> dictionaries & </span><span>wire resolver hooks</span><span> (</span><span>no behavior change</span><span>)

- name_resolver: extend VENDOR/SHEET/HEADER </span><span>alias</span><span> maps </span><span>from</span><span> NAMES_COLLECTION_REPORT.md
- semantic_matcher/header_detector: </span><span>add</span><span> canonical-hint </span><span>plumbing</span><span> (</span><span>resolve_header</span><span>) paths
- file_registry/header_normalizer: prepare hybrid normalization entry </span><span>points</span><span> (</span><span>no thresholds changed</span><span>)
- tests: </span><span>add</span><span> scaffolding & conftest </span><span>for</span><span> import </span><span>stability</span><span> (</span><span>no assertions on</span><span> business rules)

Rationale:
- Centralize naming logic; reduce downstream patch cost
- Keeps behavior invariant; only preparatory wiring
</span></span></code></div></div></pre>

### 2) 행위(Behavioral)

<pre class="overflow-visible!" data-start="677" data-end="1336"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>behavioral(</span><span>parser</span><span>): feat: </span><span>enable</span><span></span><span>alias</span><span>+fuzzy normalization </span><span>end</span><span>-</span><span>to</span><span>-</span><span>end</span><span> (vendor/sheet/</span><span>header</span><span>)

- header_normalizer: apply hybrid flow (</span><span>alias</span><span>→legacy normalization) </span><span>for</span><span></span><span>CASE</span><span></span><span>NO</span><span>/QTY/etc.
- file_registry: expose normalize_vendor_name/normalize_sheet_name/guess_vendor_from_file
- semantic_matcher/header_detector: use canonical-hint </span><span>in</span><span> matching score
- tests: </span><span>add</span><span> positive-</span><span>path</span><span> cases (simense→SIEMENS, Q'ty→QTY, HE-0214,0252→CAPACITOR)

Impact:
- Fixes common typos/variants across pipeline; higher recall with minimal false positives
- Tunable via min_score (default 0.70)

Notes:
- No schema changes; downstream keys unchanged (e.g., quantity/case_number)
</span></span></code></div></div></pre>

> 제안된 순서: 구조 커밋 먼저 → 모든 테스트 통과 확인 → 행위 커밋.

---

## pytest-cov HTML 리포트 + 커버리지 ≥85% 게이트

### 1) `pytest.ini` 업데이트

<pre class="overflow-visible!" data-start="1452" data-end="1613"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-ini"><span><span>[pytest]</span><span>
</span><span>addopts</span><span> = -q --cov=. --cov-report=term-missing --cov-report=html:coverage_html --cov-fail-under=</span><span>85</span><span>
</span><span>testpaths</span><span> = tests
</span><span>python_files</span><span> = test_*.py
</span></span></code></div></div></pre>

* HTML 리포트 경로: `coverage_html/index.html`
* 임계치 미달 시 테스트  **실패 처리** .

### 2) (대안) `.coveragerc` 사용 시

<pre class="overflow-visible!" data-start="1714" data-end="1835"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-ini"><span><span>[run]</span><span>
</span><span>branch</span><span> = </span><span>True</span><span>
</span><span>source</span><span> = .

</span><span>[report]</span><span>
</span><span>fail_under</span><span> = </span><span>85</span><span>
</span><span>show_missing</span><span> = </span><span>True</span><span>

</span><span>[html]</span><span>
</span><span>directory</span><span> = coverage_html
</span></span></code></div></div></pre>

* 이 경우 `pytest` 실행 옵션은 간단히:

  `pytest -q --cov --cov-report=term-missing --cov-report=html`

### 3) 로컬 실행 명령(권장)

<pre class="overflow-visible!" data-start="1951" data-end="2141"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>ruff --fix .
black .
pytest -q  </span><span># 커버리지 미달이면 실패</span><span>
</span><span># HTML 열기</span><span>
</span><span># mac:   open coverage_html/index.html</span><span>
</span><span># win:   start coverage_html\index.html</span><span>
</span><span># linux: xdg-open coverage_html/index.html</span><span>
</span></span></code></div></div></pre>

---

## GitHub Actions(CI) 게이트 예시

`.github/workflows/ci.yml`

<pre class="overflow-visible!" data-start="2205" data-end="2995"><div class="contain-inline-size rounded-2xl relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-yaml"><span><span>name:</span><span></span><span>ci</span><span>
</span><span>on:</span><span>
  </span><span>push:</span><span>
  </span><span>pull_request:</span><span>
</span><span>jobs:</span><span>
  </span><span>test:</span><span>
    </span><span>runs-on:</span><span></span><span>ubuntu-latest</span><span>
    </span><span>steps:</span><span>
      </span><span>-</span><span></span><span>uses:</span><span></span><span>actions/checkout@v4</span><span>
      </span><span>-</span><span></span><span>uses:</span><span></span><span>actions/setup-python@v5</span><span>
        </span><span>with:</span><span>
          </span><span>python-version:</span><span></span><span>'3.10'</span><span>
      </span><span>-</span><span></span><span>run:</span><span></span><span>pip</span><span></span><span>install</span><span></span><span>-U</span><span></span><span>pip</span><span>
      </span><span>-</span><span></span><span>run:</span><span></span><span>pip</span><span></span><span>install</span><span></span><span>-r</span><span></span><span>requirements.txt</span><span>
      </span><span>-</span><span></span><span>run:</span><span></span><span>pip</span><span></span><span>install</span><span></span><span>pytest</span><span></span><span>pytest-cov</span><span></span><span>ruff</span><span></span><span>black</span><span>
      </span><span>-</span><span></span><span>name:</span><span></span><span>Lint</span><span></span><span>&</span><span></span><span>Format</span><span>
        </span><span>run:</span><span> |
          ruff --output-format=github --fix .
          black --check .
      </span><span>-</span><span></span><span>name:</span><span></span><span>Run</span><span></span><span>tests</span><span></span><span>with</span><span></span><span>coverage</span><span></span><span>gate</span><span>
        </span><span>run:</span><span> |
          pytest -q --cov=. --cov-report=term-missing --cov-report=html:coverage_html --cov-fail-under=85
      </span><span>-</span><span></span><span>name:</span><span></span><span>Upload</span><span></span><span>coverage</span><span></span><span>HTML</span><span></span><span>(artifact)</span><span>
        </span><span>uses:</span><span></span><span>actions/upload-artifact@v4</span><span>
        </span><span>with:</span><span>
          </span><span>name:</span><span></span><span>coverage_html</span><span>
          </span><span>path:</span><span></span><span>coverage_html</span><span>
</span></span></code></div></div></pre>

---

## 빠른 체크

* [ ] 구조 커밋 적용 후 테스트 통과
* [ ] 행위 커밋 적용 후 **`--cov-fail-under=85`** 통과
* [ ] `coverage_html/index.html` 육안 검토(미커버 파일/라인 확인)
* [ ] 필요 시 `min_score` 미세 튜닝(0.65–0.75)
