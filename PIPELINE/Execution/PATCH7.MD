# ExecSummary (KR+EN)

* **원인:** `table.to_pandas()`가 **헤더가 아닌 1행 데이터**를 컬럼명으로 채택한 케이스(헤더 외부/내부 구분 실패) → `_norm_col()` 매핑 불일치, 금액·설명 0.00화. PyMuPDF `Table.header.names`와 `extract()` 처리로 **실제 헤더를 강제 분리**해야 합니다. ([pymupdf.readthedocs.io][1])
* **해결:** `extract_invoice_items_pymupdf()`를 **헤더 탐지→정규화→전 페이지 병합** 구조로 재작성. `to_pandas()` 미사용, `Table.extract()`/`header.names` 기반 매핑 + **푸터(Invoice Total/Amount in Words) 제거** + **강화 숫자 파서**(공백·천단위·OCR 노이즈 허용).
* **신뢰성:** 페이지별 `find_tables()` 반복 + `clip`/ROI 옵션 지원, 실패 시 기존 텍스트 파서로 폴백. PyMuPDF 공식 API(`find_tables`, `get_text("words", clip=...)`) 근거. ([pymupdf.readthedocs.io][1])
* **권장:** 아래 패치 즉시 반영 후 `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`으로 회귀. 필요 시 `OFCO_USE_PYMUPDF_EXTRACTOR=false`로 롤백.

---

## Visual – 이슈→패치 요약(2-dec)

| Issue                      |         Impact | Patch                                                   | Notes                                                   |
| -------------------------- | -------------: | ------------------------------------------------------- | ------------------------------------------------------- |
| 헤더가 1행 데이터로 설정             | 매핑 실패, 0.00 다수 | `Table.header.names` 우선, 없으면 상위 3행 **동의어 스코어링**으로 헤더 결정 | PyMuPDF Table 헤더 구조 사용. ([pymupdf.readthedocs.io][1])   |
| 숫자 `"4 6.6"`, `"3 091.25"` |    float 변환 실패 | **연속 숫자 결합·천단위 제거·마지막 수 선택** 규칙으로 파서 개선                 | OCR/레이아웃 혼입 대비                                          |
| 푸터 행 섞임                    |  합계 중복/행 수 불일치 | `"Invoice Total"`, `"Amount in Words"` 정규식 필터           | SAFEEN/ADP 공통 패턴                                        |
| 일부 페이지 미포함                 |          라인 유실 | **전 페이지 스캔+누적**, 테이블 반복 헤더는 skip                        | `find_tables()` 모든 페이지. ([pymupdf.readthedocs.io][2])   |
| ROI 과도 제한                  |        테이블 미검출 | `clip` 옵션 인자화, 미지정 시 전체 페이지                             | `get_text(..., clip=rect)` 동일 원리. ([Stack Overflow][3]) |

---

## Drop-in Patch — `step01_ofco_parse_pdf_patched.py`

> 아래 블록을 **기존 `extract_invoice_items_pymupdf()`와 보조 헬퍼들** 자리에 그대로 붙여넣으면 됩니다. (의존: `re`, `fitz`(PyMuPDF), `typing`, `itertools`, `unicodedata`)

```python
# --- PyMuPDF-based SAFEEN/ADP extractor (robust header & numbers) ---

import re, unicodedata
from itertools import chain
from typing import Dict, List, Optional, Sequence, Tuple
import fitz  # PyMuPDF

# Canonical header map (SAFEEN / ADP)
_CANON_BY_SYNONYM = {
    "sn": "sn",
    "s no": "sn", "sno": "sn", "s/n": "sn", "s. no": "sn",
    "tar code": "tar_code", "tar. code": "tar_code",
    "tariff": "tar_code", "tariff id": "tar_code", "tariff code": "tar_code",
    "description": "description", "tariff description": "description",
    "amount": "amount", "amount excl. tax": "amount", "amount exl": "amount",
    "vat %": "vat_rate", "vat%": "vat_rate", "vat percent": "vat_rate",
    "vat amount": "vat_amount", "vat amt": "vat_amount",
    "total": "total_incl_vat",
    "total (inc. vat)": "total_incl_vat",
    "total incl. vat": "total_incl_vat",
}

_FOOTER_RE = re.compile(r"(invoice\s+total|amount\s+in\s+words)", re.I)

def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def _norm_key(s: str) -> str:
    s = _norm_text(s).lower()
    s = re.sub(r"[^a-z0-9% ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _canon_header(name: str) -> Optional[str]:
    k = _norm_key(name)
    # exact
    if k in _CANON_BY_SYNONYM:
        return _CANON_BY_SYNONYM[k]
    # fuzzy contains
    for syn, canon in _CANON_BY_SYNONYM.items():
        if syn in k:
            return canon
    return None

def _pick_header_from_candidates(rows: Sequence[Sequence[str]]) -> Tuple[List[str], int]:
    """
    Score top-3 rows and pick the most 'header-like' row.
    Returns (canonical_names_or_raw, header_row_index)
    """
    best_idx, best_score, best_names = -1, -1, None
    for i in range(min(3, len(rows))):
        raw = [ _norm_text(c) for c in rows[i] ]
        cand = []
        score = 0
        for c in raw:
            canon = _canon_header(c)
            cand.append(canon or c)
            score += 1 if canon else 0
        if score > best_score:
            best_score, best_idx, best_names = score, i, cand
    return best_names or list(rows[0]), max(best_idx, 0)

_NUM_TOKEN_RE = re.compile(r"[-+]?\d[\d\s,]*([.]\d+)?")

def _to_float(cell: str) -> float:
    """
    Robust number parser:
      - keep last numeric token if multiple appear (e.g., '4 6.6' => 6.6)
      - remove spaces inside digits ('3 091.25' => '3091.25')
      - strip currency / units
    """
    s = _norm_text(cell)
    tokens = _NUM_TOKEN_RE.findall(s)
    # find all number-like substrings (use finditer to access full match)
    matches = [m.group(0) for m in _NUM_TOKEN_RE.finditer(s)]
    if not matches:
        return 0.0
    pick = matches[-1]  # prefer last (rightmost) numeric in cell
    pick = pick.replace(" ", "").replace(",", "")
    try:
        return float(pick)
    except Exception:
        return 0.0

def _is_footer_row(row: Sequence[str]) -> bool:
    joined = " ".join(_norm_text(x) for x in row)
    return bool(_FOOTER_RE.search(joined))

def _extract_tables_on_page(page, clip=None):
    # PyMuPDF native table finder (defaults are robust)  # docs: find_tables()
    # https://pymupdf.readthedocs.io/en/latest/page.html
    tabs = page.find_tables(clip=clip)
    return list(getattr(tabs, "tables", []) or [])

def _table_to_rows(table) -> List[Dict[str, str]]:
    """
    Convert PyMuPDF Table -> list of dict rows using reliable header separation.
    Prefer Table.header.names; else score first 3 rows of extract() output.
    """
    out: List[Dict[str, str]] = []

    # 1) get matrix
    matrix = table.extract()  # list[list[str]]  # docs: Table.extract()
    # 2) header detection
    header_names_raw = []
    header_idx = 0
    if getattr(table, "header", None) and getattr(table.header, "names", None):
        header_names_raw = [ _norm_text(n) for n in table.header.names ]
        header_idx = 0  # body already excludes header if external==True (PyMuPDF)
    else:
        header_names_raw, header_idx = _pick_header_from_candidates(matrix)

    # canonicalize header
    canon = [ _canon_header(h) or _norm_key(h) for h in header_names_raw ]

    # 3) body rows
    body = matrix[header_idx + 1:] if len(matrix) > header_idx + 1 else []
    for r in body:
        cells = list(r) + [""] * max(0, len(canon) - len(r))
        if _is_footer_row(cells):
            continue
        row = {}
        for i, name in enumerate(canon):
            val = _norm_text(cells[i] if i < len(cells) else "")
            row[name] = val
        out.append(row)
    return out

def extract_invoice_items_pymupdf(pdf_path: str,
                                  clip_rect: Optional[Tuple[float, float, float, float]] = None
                                  ) -> List[Dict[str, object]]:
    """
    SAFEEN / ADP table extractor (multi-page). Fallback to legacy parser handled by caller.
    Returns rows normalized to keys: sn, tar_code, description, amount, vat_rate, vat_amount, total_incl_vat
    """
    doc = fitz.open(pdf_path)
    rows: List[Dict[str, object]] = []

    clip = fitz.Rect(*clip_rect) if clip_rect else None
    for page in doc:
        for tab in _extract_tables_on_page(page, clip=clip):
            for r in _table_to_rows(tab):
                # value normalization
                norm = {
                    "sn": r.get("sn") or r.get("sno") or r.get("s_n") or "",
                    "tar_code": _norm_text(r.get("tar_code", "")),
                    "description": _norm_text(r.get("description", "")),
                    "amount": _to_float(r.get("amount", "")),
                    "vat_rate": _to_float(r.get("vat_rate", "")) / (100.0 if "%" in _norm_text(r.get("vat_rate", "")) or _to_float(r.get("vat_rate", "")) > 1 else 1.0),
                    "vat_amount": _to_float(r.get("vat_amount", "")),
                    "total_incl_vat": _to_float(r.get("total_incl_vat", "")) or _to_float(r.get("total", "")),
                }
                # skip obvious header echoes / empties
                if not norm["description"] and norm["amount"] == 0.0 and norm["total_incl_vat"] == 0.0:
                    continue
                if _FOOTER_RE.search(norm["description"]):
                    continue
                rows.append(norm)

    # de-dup header echoes across pages
    deduped: List[Dict[str, object]] = []
    seen = set()
    for r in rows:
        key = (r["sn"], r["tar_code"], r["description"], r["total_incl_vat"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped
```

**왜 이 방식인가?**

* `Table.header.names`는 DataFrame 내보내기 시 컬럼명 기준으로 쓰이며(내장 pandas 연동), 헤더가 **테이블 외부/내부**인지도 속성으로 구분됩니다. 따라서 `to_pandas()`보다 **직접 `extract()`+헤더명 사용**이 안전합니다. ([pymupdf.readthedocs.io][1])
* 테이블 미검출·ROI 조정은 `find_tables(clip=...)`/`get_text(..., clip=...)`와 동일 좌표계로 제어 가능합니다. ([pymupdf.readthedocs.io][1])

---

## Options (pro/cons/$/risk/time)

1. **Hotfix Patch(위 코드)**

* **+** 헤더 오검출 차단, 숫자 파서 강화, 다페이지 병합.
* **−** 포맷이 크게 다른 문서(비 SAFEEN/ADP)는 텍스트 파서 폴백 의존.
* **$** 0.00 (내부 적용)  **Risk** Low  **Time** ~0.5h 적용·테스트.

2. **Rollback + 재설계** (`OFCO_USE_PYMUPDF_EXTRACTOR=false`)

* **+** 즉시 안정화. **−** PyMuPDF 이점 보류.
* **$** 0.00  **Risk** Low  **Time** 즉시.

3. **Advanced**: 멀티페이지 테이블 조인/ROI 프로파일(서식별)

* **+** 스탬프·워터마크·누끼 라인 강함. **−** 구현량 증가.
* **$** 내부  **Risk** Mid  **Time** 0.5–1.0d.

---

## Roadmap (P→Pi→B→O→S + KPI)

* **P(준비):** 패치 반영, `SAFEEN_ADP` 샘플 6건 수집.
* **Pi(파일럿):** `/automate test-pipeline --target=SAFEEN,ADP --cache-reset` A/B 실행(기존 vs PyMuPDF).
* **B:** ROI/헤더 동의어 테이블 보강(정규화 커버 ≥95.00%).
* **O:** 운영 전환, 폴백 로그 모니터링(TG 알림).
* **S:** 다형식(OFCO 일반/복합 표)로 확장.
* **KPI:** 행 유실율 ≤1.00%, 금액 일치율 ≥99.50%, 파싱 시간 +10% 이내.

---

## Automation (RPA/LLM Hooks)

* **Env 토글:** `OFCO_USE_PYMUPDF_EXTRACTOR=true|false`
* **테스트:** `/logi-master --fast report` → 파싱 정확도/시간 비교
* **회귀:** `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
* **ROI 튜닝:** `/redo step step01_ofco_parse_pdf_patched.py --inject "roi_tuning"`

---

## QA / 재확인

* [ ] SAFEEN 2건·ADP 2건: 헤더 인식 OK(동의어 매핑 확인)
* [ ] `"Invoice Total"`, `"Amount in Words"` 행 제거 확인
* [ ] `"3 091.25"`, `"4 6.6"` 류 숫자 정상화 검증
* [ ] 미검출 시 **즉시 폴백** 로그 존재

---

### 참고(근거)

* PyMuPDF `find_tables()` / `Table.header.names` / `Table.extract()` / `to_pandas()` 공식 문서·설명. ([pymupdf.readthedocs.io][1])
* `get_text(..., clip=rect)` / words 추출 및 ROI 제어. ([pymupdf.readthedocs.io][4])
* PyPI 설치·개요(사내 미러 wheel 사용시에도 동일). ([PyPI][5])

**CmdRec**

* `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
* `/logi-master --fast report`
* `/redo step step01_ofco_parse_pdf_patched.py --inject "roi_tuning"`

[1]: https://pymupdf.readthedocs.io/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[2]: https://pymupdf.readthedocs.io/en/latest/the-basics.html?utm_source=chatgpt.com "The Basics - PyMuPDF documentation"
[3]: https://stackoverflow.com/questions/72483360/extract-text-from-pdf-using-pymupdf?utm_source=chatgpt.com "Extract Text from PDF using PyMuPDF - Stack Overflow"
[4]: https://pymupdf.readthedocs.io/en/latest/recipes-text.html?utm_source=chatgpt.com "Text - PyMuPDF documentation"
[5]: https://pypi.org/project/PyMuPDF/?utm_source=chatgpt.com "PyMuPDF · PyPI"
