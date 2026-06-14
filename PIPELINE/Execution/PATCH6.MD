# ExecSummary

PyMuPDF 기반 **SAFEEN·ADP 테이블 파서**를 `step01_ofco_parse_pdf_patched.py`에 “바로 붙여” 동작하도록 완성본을 드립니다. `Page.find_tables()`(+ROI), `get_text("words"/"dict")` 폴백, `search_for` 로 **헤더~푸터 ROI**를 안정적으로 잡고, **VAT 5%→0.05, 통화·천단위 정규화, Invoice Total/Amount in Words 제거**까지 포함합니다. 환경변수 `OFCO_USE_PYMUPDF_EXTRACTOR`로 즉시 롤백/AB 테스트가 가능합니다. PyMuPDF의 테이블/텍스트 API와 ROI 클리핑 동작은 공식 문서 기준으로 구현했습니다. ([PyMuPDF][1])

---

## Visual (핵심 매핑/흐름)

| Stage  | Tech                       | 핵심 로직                                                         | 출력 키                                                                            | 참고                               |
| ------ | -------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------- |
| ROI 탐지 | `search_for`               | “S No” 상단·“Invoice Total”/“Amount in Words” 하단 bbox로 표 영역 클리핑 | `roi: fitz.Rect`                                                                | 텍스트-ROI 탐색 표준 API. ([GitHub][2]) |
| 1차 추출  | `find_tables(clip=roi)`    | 테이블 후보 중 **헤더 동의어 스코어**가 가장 높은 테이블 선택                         | matrix(list[list[str]])                                                         | PyMuPDF 테이블 파인더. ([PyMuPDF][1])  |
| 2차 폴백  | `get_text("words"/"dict")` | 그리드 재구성(열 경계=헤더 단어 bbox 군집)                                   | rows                                                                            | 워즈/딕트 구조 좌표 접근. ([PyMuPDF][3])   |
| 정규화    | 파서 유틸                      | VAT%→소수, 통화·천단위, Tariff Code, 푸터 제거                           | `sn, tariff_code, desc, amount_excl_vat, vat_rate, vat_amount, amount_incl_vat` |                                  |
| DF 정렬  | HeaderCore                 | 표준 63 헤더 + 동적열 유지                                             | Phase 입력 DF                                                                     |                                  |

**헤더 동의어(예시):**

* `S No`⇔`S/N`,`SN`,`S. No` / `Tar. Code`⇔`Tariff Code`,`Tariff` / `Amount`⇔`Amount excl. VAT` / `VAT %`⇔`Tax %` / `VAT Amount`⇔`Tax Amount` / `Total (Inc. VAT)`⇔`Amount incl. VAT`

---

## 바로 붙여 넣는 패치 (drop-in)

> 🔧 아래 블록을 `step01_ofco_parse_pdf_patched.py`에 추가(또는 기존 동명 함수 대체)하세요.
> 기존 텍스트 파서 흐름은 **그대로** 두고, **성공 시 PyMuPDF 결과 우선 사용**하도록 연결 스니펫도 포함했습니다.

```python
# --- [ADD] imports ---
import os
import re
from typing import List, Dict, Optional, Tuple
try:
    import fitz  # PyMuPDF
except Exception:  # Optional import: env 롤백 대비
    fitz = None

# --- [ADD] 헤더 동의어/컬럼 표준화 ---
_HEADER_SYNONYMS = {
    "sn": {"s no", "s/n", "sn", "s. no"},
    "tariff_code": {"tar. code", "tar code", "tariff code", "tariff"},
    "description": {"description", "desc"},
    "amount_excl_vat": {"amount excl. vat", "amount excl", "amount"},
    "vat_rate": {"vat %", "tax %", "vat%", "tax%"},
    "vat_amount": {"vat amount", "tax amount"},
    "amount_incl_vat": {"total (inc. vat)", "amount incl. vat", "total inc vat", "gross total"},
}

_DROP_ROWS_PAT = re.compile(r"(invoice\s+total|amount\s+in\s+words)", re.I)

_NUM_PAT = re.compile(r"[-+]?\d[\d,]*\.?\d*")

def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def _norm_col(name: str) -> Optional[str]:
    k = _clean(name).lower()
    for std, alts in _HEADER_SYNONYMS.items():
        if k in alts:
            return std
    return None

def _to_float(s: str) -> Optional[float]:
    if s is None:
        return None
    m = _NUM_PAT.search(s.replace("\u066b", ".").replace("\u066c", ","))  # Arabic punct.
    if not m:
        return None
    x = m.group(0).replace(",", "")
    try:
        return float(x)
    except ValueError:
        return None

def _norm_vat(s: str) -> Optional[float]:
    s = _clean(s)
    # 5, 5%, 0.05 → 0.05
    if s.endswith("%"):
        v = _to_float(s[:-1])
        return None if v is None else round(v / 100.0, 4)
    v = _to_float(s)
    if v is None:
        return None
    return v if v <= 1.0 else round(v / 100.0, 4)

# --- [ADD] ROI 탐색: 헤더/푸터 기준 ---
def _find_roi(page) -> Optional["fitz.Rect"]:
    tops = page.search_for("S No", quads=False) or page.search_for("S. No") or page.search_for("S/N")
    bots = page.search_for("Invoice Total") or page.search_for("Amount in Words")
    if not tops:
        return None
    top_y = min(r.y0 for r in tops) - 4
    if bots:
        bot_y = max(r.y1 for r in bots) + 2
    else:
        # 하단 여백 3% 남김
        bot_y = page.rect.y1 - max(8, page.rect.height * 0.03)
    return fitz.Rect(page.rect.x0 + 4, top_y, page.rect.x1 - 4, bot_y)

# --- [ADD] Table -> dict rows ---
def _matrix_to_rows(matrix: List[List[str]]) -> List[Dict]:
    if not matrix:
        return []
    # 1) 헤더 행 선택 (첫 행 또는 'S No' 포함 행)
    header_row_idx = 0
    for i, row in enumerate(matrix[:3]):
        if any(re.search(r"\bS\.?\s*No\b|S/?N", c or "", re.I) for c in row):
            header_row_idx = i
            break
    header = matrix[header_row_idx]
    body = matrix[header_row_idx + 1:]
    colmap: Dict[int, str] = {}
    for j, name in enumerate(header):
        std = _norm_col(name)
        if std:
            colmap[j] = std

    rows = []
    for raw in body:
        joined = " ".join(_clean(c) for c in raw if c)
        if not joined or _DROP_ROWS_PAT.search(joined):
            continue
        rec = {
            "sn": None, "tariff_code": None, "description": None,
            "amount_excl_vat": None, "vat_rate": None, "vat_amount": None, "amount_incl_vat": None,
        }
        for j, cell in enumerate(raw):
            key = colmap.get(j)
            if not key:
                continue
            text = _clean(cell)
            if key in ("amount_excl_vat", "vat_amount", "amount_incl_vat"):
                rec[key] = _to_float(text)
            elif key == "vat_rate":
                rec[key] = _norm_vat(text)
            elif key in ("sn", "tariff_code"):
                rec[key] = _clean(text)
            else:
                rec[key] = text
        # 최소 컬럼(설명+금액) 필터
        if rec["description"] and (rec["amount_incl_vat"] is not None or rec["amount_excl_vat"] is not None):
            rows.append(rec)
    return rows

# --- [ADD] words 기반 폴백: 헤더 열폭 추정 → 그리드화 ---
def _fallback_words(page, roi: Optional["fitz.Rect"]) -> List[Dict]:
    drows: List[Dict] = []
    words = page.get_text("words", sort=True, clip=roi)  # (x0,y0,x1,y1, "w", block,line,word)
    if not words:
        return drows
    # 간단화: 첫 줄에서 헤더 후보 어휘를 스캔하여 x-경계 추정
    header_y = min(w[1] for w in words) + 2
    header_line = [w for w in words if abs(w[1] - header_y) <= 6]
    xs = sorted({round(w[0], 1) for w in header_line})
    # 6개 내외 열로 클러스터 (최소 분리 40pt)
    cols = []
    for x in xs:
        if not cols or x - cols[-1] > 40:
            cols.append(x)
    cols.append((roi or page.rect).x1)
    # 헤더 이름 구성
    header_cells = [""] * (len(cols) - 1)
    for w in header_line:
        for i in range(len(cols) - 1):
            if cols[i] <= w[0] < cols[i + 1]:
                header_cells[i] += (" " + w[4])
                break
    matrix = [header_cells]
    # 본문 행 구성(라인별 y-클러스터)
    # (y0 라운드해 그룹핑)
    from collections import defaultdict
    lines = defaultdict(list)
    for w in words:
        if w[1] > header_y + 6:
            lines[round(w[1], 0)].append(w)
    for _, line_words in sorted(lines.items(), key=lambda kv: kv[0]):
        row = [""] * (len(cols) - 1)
        for w in sorted(line_words, key=lambda t: t[0]):
            for i in range(len(cols) - 1):
                if cols[i] <= w[0] < cols[i + 1]:
                    row[i] += (" " + w[4])
                    break
        matrix.append(row)
    return _matrix_to_rows([[c.strip() for c in r] for r in matrix])

# --- [ADD] 메인: PyMuPDF 추출기 ---
def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict]:
    if fitz is None:
        return []
    rows_all: List[Dict] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            roi = _find_roi(page)
            try:
                tf = page.find_tables(clip=roi)
                candidates = tf.tables or []
            except Exception:
                candidates = []
            chosen = None
            # 헤더 적합도 점수로 테이블 선택
            best_score = -1
            for t in candidates:
                mat = t.extract()
                if not mat:
                    continue
                header = " ".join(_clean(c) for c in mat[0] if c)
                score = sum(1 for synset in _HEADER_SYNONYMS.values()
                            if any(k in header.lower() for k in synset))
                if score > best_score:
                    best_score = score
                    chosen = mat
            if chosen:
                rows = _matrix_to_rows(chosen)
            else:
                rows = _fallback_words(page, roi)
            rows_all.extend(rows)
    return rows_all

# --- [ADD] 기존 파이프라인 연결: 성공 시 우선 사용 ---
def parse_ofco_invoice(pdf_path: str, *, use_pymupdf_env: Optional[str] = None):
    """기존 parse_ofco_invoice 흐름에 PyMuPDF 결과를 먼저 시도하고 실패 시 텍스트 파서로 폴백."""
    use_flag = (use_pymupdf_env or os.getenv("OFCO_USE_PYMUPDF_EXTRACTOR", "1")).lower() not in {"0", "false", "no"}
    pymupdf_rows = []
    if use_flag:
        try:
            pymupdf_rows = extract_invoice_items_pymupdf(pdf_path)
        except Exception as e:
            print(f"[WARN] PyMuPDF extractor failed: {e}")
            pymupdf_rows = []
    if pymupdf_rows:
        return _items_to_ofco_payload(pymupdf_rows)  # <-- 기존 LineItem/OFCOPayload 변환 유틸 사용
    # ---- fallback: 기존 텍스트 파서 ----
    return _parse_ofco_invoice_text(pdf_path)
```

> 구현 근거: **테이블 찾기**(`Page.find_tables`), **워즈/딕트 텍스트**(`get_text("words"/"dict", sort=True)`), **ROI 클립**(`clip=`), **검색**(`search_for`) 사용은 공식 문서/레시피에 부합합니다. ([PyMuPDF][1])

---

## 선택지(Options)

1. **ROI+find_tables 우선(현재안)**

* Pros: 속도 빠름(가정: 0.12–0.35s/page), 표 경계 명확한 SAFEEN·ADP에 강함.
* Cons: 희미한 경계/스캔품질 저하 시 누락 가능.
* Risk: 헤더 변형 시 스코어 낮아 선택 실패.
* Time: 즉시.

2. **words 전용 그리드 재구성(경계선 무시)**

* Pros: 라인/경계가 약해도 견고.
* Cons: 헤더 열폭 추정 실패 시 열 섞임 가능.
* Risk: 숫자열 인식 오류(단위 열과 합쳐짐).
* Time: 즉시(코드 포함).

3. **혼합 전략 + pdfplumber 보조(희귀 서식 전용)**

* Pros: 난이도 높은 문서 커버리지 향상.
* Cons: 의존성 증가·속도 저하.
* Risk: 유지보수 복잡.
* Time: 0.5–1.0d.

---

## Roadmap (P→Pi→B→O→S, KPI)

* **P(Prepare)**: 샘플 4종(65362/64935/62707/63404) + `OFCO-INV-0000845_Samsung.pdf`로 골든셋 수립.
  KPI: Table Recall ≥ 99.00%, 숫자 일치율(TableAcc) ≥ 98.00%.
* **Pi(Pilot)**: `/automate test-pipeline --target=SAFEEN,ADP --cache-reset` A/B(기존 vs PyMuPDF).
  KPI: 평균 처리시간 ≤ 0.40s/page, 실패율 ≤ 1.00%.
* **B(Build)**: HeaderCore 스냅샷 고정, 예외 샘플에 동의어 추가.
  KPI: 회귀 테스트 100% 통과.
* **O(Operate)**: `/logi-master --fast report`에 파싱 정확도/시간 리포트 통합.
  KPI: 주간 실패 건 0, 핫픽스 T+0.
* **S(Scale)**: PriceCenter/CostCenter 룰 체인에 Tariff→단위 보강 연동.
  KPI: 수동수정 시간 -80.00%.

---

## 테스트/검증 스니펫

```python
# 1) 휠 오프라인 설치(로컬 미러)
# pip install --no-index --find-links wheels PyMuPDF pymupdf4llm
# 2) 단일 파일 테스트
from step01_ofco_parse_pdf_patched import extract_invoice_items_pymupdf
rows = extract_invoice_items_pymupdf(r"data\OFCO-INV-0000845_Samsung.pdf")
print(f"rows={len(rows)}; sample={rows[0] if rows else 'EMPTY'}")
# 3) 합계 일치성 점검(푸터 Total vs 라인 합계)
tot = sum(x.get("amount_incl_vat") or 0.0 for x in rows)
print("SUM(amount_incl_vat)=", round(tot, 2))
```

> 참고: PyMuPDF 테이블/텍스트/클립 API 및 예제는 최신 문서 기준입니다. ([PyMuPDF][1])

---

## Automation (RPA+LLM+Sheets)

* 파이프라인 진입 명령:
  `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
  `/logi-master --fast report`
* 실패 행 자동 캡처: ROI 스냅샷(페이지 PNG) 저장 → 보고서에 인라인.

---

## QA (gap/recheck)

* 가정: SAFEEN·ADP 헤더 라벨이 “S No / Tar. Code / Description / Amount / VAT % / VAT Amount / Total(Inc. VAT)” 계열.
* 재확인: (1) 정상 문서서체가 PDF 텍스트로 존재(스캔-OCR 제외), (2) Footer 키워드 오타 케이스 추가 필요 시 `_DROP_ROWS_PAT` 확장.

---

## 연결 스니펫(기존 흐름에 접목)

```python
# parse_ofco_invoice(...) 내부 또는 호출부 근처
USE = os.getenv("OFCO_USE_PYMUPDF_EXTRACTOR", "1").lower() not in {"0","false","no"}
if USE:
    rows = extract_invoice_items_pymupdf(pdf_path)
    if rows:
        return _items_to_ofco_payload(rows)
# fallback
return _parse_ofco_invoice_text(pdf_path)
```

---

## 근거(핵심 문서)

* **Tables**: `Page.find_tables()` / `Table.extract()` — 공식 가이드 & API. ([PyMuPDF][1])
* **텍스트 구조**: `get_text("text"|"blocks"|"words"|"dict", sort=True)` — 라인/스팬/워즈 좌표 설명. ([PyMuPDF][3])
* **클리핑/검색**: `clip=` 파라미터, `search_for()` 로 ROI 한정. ([PyMuPDF][4])
* **pymupdf4llm**: 레이아웃 친화 추출 보조(선택). ([GitHub][5])

---

### CmdRec

* `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
* `/logi-master --fast report`
* `/redo step step01_ofco_parse_pdf_patched.py --inject "roi_tuning"`

[1]: https://pymupdf.readthedocs.io/en/latest/the-basics.html?utm_source=chatgpt.com "The Basics - PyMuPDF documentation"
[2]: https://github.com/pymupdf/PyMuPDF/discussions/3095?utm_source=chatgpt.com "Feature request: Extract both texts and tables on the same page · pymupdf PyMuPDF · Discussion #3095 · GitHub"
[3]: https://pymupdf.readthedocs.io/en/latest/app1.html?utm_source=chatgpt.com "Appendix 1: Details on Text Extraction - PyMuPDF documentation"
[4]: https://pymupdf.readthedocs.io/_/downloads/en/latest/pdf/?utm_source=chatgpt.com "PyMuPDF Documentation"
[5]: https://github.com/pymupdf/RAG?utm_source=chatgpt.com "GitHub - pymupdf/pymupdf4llm: PyMuPDF4LLM"
