# ExecSummary

PyMuPDF(fitz) 기반 **SAFEEN·ADP 테이블 전용 추출기**를 `step01_ofco_parse_pdf_patched.py`에 **드롭-인**으로 붙이는 패치입니다. `Page.find_tables()`→`Table.extract()` 1순위, 실패 시 `get_text("words")` ROI 폴백, 최종 폴백은 기존 텍스트 파서로 분기합니다. 헤더 동의어 정규화, VAT 5→0.05, `Invoice Total/Amount in Words` 푸터 제거를 포함합니다. 토글: `OFCO_USE_PYMUPDF_EXTRACTOR=true`(기본). API 근거는 공식 문서의 `get_text(...)`, `find_tables(...)`, `Table.extract()/to_pandas()` 명세를 따릅니다. ([PyMuPDF][1])

---

## Visual (변경 요약)

| 영역    | 내용                                                                      | 기본값          |
| ----- | ----------------------------------------------------------------------- | ------------ |
| 탐지 전략 | `find_tables(strategy="lines_strict"→"lines"→"text")` 순회                | lines_strict |
| ROI   | 헤더 키워드(S No, Description, Amount, VAT %) bbox로 상단 라인 탐지 → 아래로 확장        | on           |
| 푸터 필터 | `Invoice Total`, `Total (Inc. VAT)`, `Amount in Words`, `Payment Terms` | 제거           |
| 수치정규화 | 천단위 구분자 제거, `5`→`0.05`(VAT%), 통화 기호 제거                                  | on           |
| 토글/폴백 | `OFCO_USE_PYMUPDF_EXTRACTOR=false` → 기존 파서 직행                           | on           |

---

## Patch — `step01_ofco_parse_pdf_patched.py`에 그대로 붙여넣기

```diff
@@
-# (기존 import 유지)
+import os
+import re
+from typing import List, Dict, Any, Optional, Tuple
+try:
+    import fitz  # PyMuPDF
+except Exception:
+    fitz = None  # 오프라인/미설치 환경 폴백
+
+# -------------------------
+# PyMuPDF SAFEEN/ADP 전용 추출기 (drop-in)
+# -------------------------
+SAFEEN_ADP_HEADER_SYNONYMS: Dict[str, Tuple[str, ...]] = {
+    "sn": ("s no", "sno", "s/n", "sn", "s. no"),
+    "tariff": ("tar. code", "tar code", "tariff id", "tariff code", "tar code"),
+    "desc": ("description", "particulars", "tariff description"),
+    "amount": ("amount", "amount (aed)", "amount excl. vat (aed)"),
+    "vat_pct": ("vat %", "vat%", "tax %", "tax rate"),
+    "vat_amt": ("vat amount", "tax amount"),
+    "total_inc": ("total (inc. vat)", "total incl. tax (aed)", "amount incl. vat (aed)", "total incl. vat"),
+}
+FOOTER_KEYS = ("invoice total", "amount in words", "payment terms", "total amount (aed)")
+
+_NUM = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")
+
+def _norm(s: Any) -> str:
+    return re.sub(r"\s+", " ", str(s or "")).strip().lower()
+
+def _as_float(s: Any) -> Optional[float]:
+    if s is None:
+        return None
+    m = _NUM.search(str(s))
+    if not m:
+        return None
+    return float(m.group(0).replace(",", ""))
+
+def _norm_vat_percent(v: Any) -> Optional[float]:
+    """5 -> 0.05, 0 -> 0.00"""
+    f = _as_float(v)
+    if f is None:
+        return None
+    return f/100.0 if f > 1.0 else f
+
+def _map_headers(cells: List[str]) -> Dict[int, str]:
+    mapped: Dict[int, str] = {}
+    for i, raw in enumerate(cells):
+        k = _norm(raw)
+        for std, aliases in SAFEEN_ADP_HEADER_SYNONYMS.items():
+            if any(k == a for a in aliases):
+                mapped[i] = std
+                break
+    return mapped
+
+def _is_footer_row(row_texts: List[str]) -> bool:
+    j = " ".join(_norm(x) for x in row_texts)
+    return any(key in j for key in FOOTER_KEYS)
+
+def _header_bbox_words(page) -> Optional[fitz.Rect]:
+    """헤더 키워드 2개 이상(bbox)로 ROI 상단선 추정 후 페이지 하단까지 확장."""
+    words = page.get_text("words", sort=True)  # [(x0,y0,x1,y1,word, block_no, line_no, word_no), ...]
+    hits = [fitz.Rect(*w[:4]) for w in words if _norm(w[4]) in ("s", "s no", "sno", "description", "amount", "vat %", "tar. code", "tar code")]
+    if not hits:
+        return None
+    top = min(r.y0 for r in hits)
+    left = min(r.x0 for r in hits)
+    right = max(r.x1 for r in hits)
+    # 헤더 바로 아래부터 전표 끝까지
+    return fitz.Rect(left-10, top-6, max(right+300, page.rect.x1), page.rect.y1)
+
+def _extract_table_matrix(tbl) -> List[List[str]]:
+    # PyMuPDF Table.extract() → 셀 텍스트 매트릭스 (문서화된 API)
+    # ref: Page.find_tables / Table.extract / to_pandas. :contentReference[oaicite:1]{index=1}
+    try:
+        return tbl.extract()
+    except Exception:
+        # 일부 버전은 to_pandas() 제공
+        try:
+            df = tbl.to_pandas()
+            return [[str(x) if x is not None else "" for x in row] for row in df.values.tolist()]
+        except Exception:
+            return []
+
+def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict[str, Any]]:
+    """SAFEEN·ADP 인보이스에서 라인아이템 표를 PyMuPDF로 파싱."""
+    rows_out: List[Dict[str, Any]] = []
+    if not fitz:
+        return rows_out
+    with fitz.open(pdf_path) as doc:
+        for page in doc:
+            # 1) 표 탐지: lines_strict → lines → text
+            roi = _header_bbox_words(page) or page.rect
+            for strategy in ("lines_strict", "lines", "text"):
+                try:
+                    tf = page.find_tables(clip=roi, strategy=strategy)
+                except Exception:
+                    tf = None
+                if not tf or not getattr(tf, "tables", []):
+                    continue
+                # 후보 테이블들 중 헤더 매핑률이 높은 한 개 선택
+                best = None
+                best_score = -1
+                for t in tf.tables:
+                    mat = _extract_table_matrix(t)
+                    if not mat or len(mat) < 2:
+                        continue
+                    header = [re.sub(r"\s+", " ", c or "").strip().lower() for c in mat[0]]
+                    mapped = _map_headers(header)
+                    score = len(mapped)
+                    if score > best_score:
+                        best = (mat, mapped)
+                        best_score = score
+                if best and best_score >= 3:
+                    mat, mapped = best
+                    # 데이터 행 처리
+                    for r in mat[1:]:
+                        if not any(str(x).strip() for x in r):
+                            continue
+                        if _is_footer_row([str(x) for x in r]):
+                            continue
+                        rec = {
+                            "sn": _as_float(r[list(mapped.keys())[0]]) if "sn" in mapped.values() else None,
+                            "tariff": None,
+                            "description": None,
+                            "amount": None,
+                            "vat_percent": None,
+                            "vat_amount": None,
+                            "total_incl_vat": None,
+                        }
+                        for idx, std in mapped.items():
+                            val = r[idx] if idx < len(r) else ""
+                            if std == "desc":
+                                rec["description"] = re.sub(r"\s+", " ", str(val)).strip()
+                            elif std == "tariff":
+                                rec["tariff"] = str(val).strip()
+                            elif std == "amount":
+                                rec["amount"] = _as_float(val)
+                            elif std == "vat_pct":
+                                rec["vat_percent"] = _norm_vat_percent(val)
+                            elif std == "vat_amt":
+                                rec["vat_amount"] = _as_float(val)
+                            elif std == "total_inc":
+                                rec["total_incl_vat"] = _as_float(val)
+                        # 최소 필드 존재성
+                        if rec["description"] and (rec["amount"] is not None or rec["total_incl_vat"] is not None):
+                            rows_out.append(rec)
+                    # 한 페이지에 다수 테이블이더라도 첫 유효 테이블만 사용
+                    break
+            # 2) words 폴백 (테이블 미탐지시)
+            if not rows_out:
+                clip = _header_bbox_words(page)
+                words = page.get_text("words", sort=True, clip=clip)  # :contentReference[oaicite:2]{index=2}
+                # 간단 라인그리드: y0로 버킷팅
+                lines: Dict[int, List[str]] = {}
+                for x0, y0, x1, y1, w, *_ in words:
+                    key = int(round(y0))
+                    lines.setdefault(key, []).append((x0, w))
+                for key in sorted(lines):
+                    line = " ".join(w for _, w in sorted(lines[key]))
+                    if _is_footer_row([line]):
+                        continue
+                    # 금액이 포함된 라인만 후보
+                    if _NUM.search(line):
+                        rows_out.append({
+                            "sn": None,
+                            "tariff": None,
+                            "description": line,
+                            "amount": None,
+                            "vat_percent": None,
+                            "vat_amount": None,
+                            "total_incl_vat": None,
+                        })
+    return rows_out
+
+def _should_use_pymupdf() -> bool:
+    val = os.getenv("OFCO_USE_PYMUPDF_EXTRACTOR", "true").lower()
+    return val not in ("0", "false", "no")
+
@@
-def parse_ofco_invoice(pdf_path: str, *args, **kwargs):
-    # 기존 구현 ...
-    pass
+def parse_ofco_invoice(pdf_path: str, *args, **kwargs):
+    """
+    기존 텍스트 파서를 유지하되, PyMuPDF 결과가 있으면 우선 사용.
+    (기존 OFCOPayload 빌더와의 결합부는 프로젝트 함수에 맞춰 호출)
+    """
+    if fitz and _should_use_pymupdf():
+        try:
+            pym_rows = extract_invoice_items_pymupdf(pdf_path)
+            if pym_rows:
+                # TODO: 프로젝트의 표준 라인아이템 빌더에 연결하십시오.
+                # 예) items = rows_to_lineitems(pym_rows)
+                # return build_payload(meta_from_pdf(...), items, audit=...)
+                return _parse_with_rows_bridge(pym_rows, pdf_path)  # ← 팀 내 브리지 함수(존재 시)
+        except Exception as e:
+            logger.exception("[PyMuPDF] extractor failed → fallback: %s", e)
+    # 폴백: 기존 텍스트 파서
+    return _parse_with_text_engine(pdf_path, *args, **kwargs)
```

> 주: `Page.get_text(..., clip=Rect)`·`get_text("words")`·`find_tables()`·`Table.extract()/to_pandas()`는 PyMuPDF 공식 문서의 명세입니다. 옵션/전략의 정의와 파라미터는 문서 원문을 참고하세요. ([PyMuPDF][1])

---

## 빠른 검증 (Windows, 오프라인 설치 OK)

```powershell
# 1) 오프라인 설치(로컬 wheels 디렉토리)
py -m pip install --no-index --find-links wheels PyMuPDF pymupdf4llm tabulate

# 2) 단일 함수 스모크 테스트
py - << 'PY'
from step01_ofco_parse_pdf_patched import extract_invoice_items_pymupdf
rows = extract_invoice_items_pymupdf(r".\data\OFCO-INV-0000845_Samsung.pdf")
print(f"rows={len(rows)}"); print(rows[0] if rows else "EMPTY")
PY
```

---

## 옵션(운영 톤)

1. **보수형**: `OFCO_USE_PYMUPDF_EXTRACTOR=false`로 즉시 롤백(리스크↓, 이행시간 0.00d).
2. **혼합형**: SAFEEN/ADP 감지 시만 PyMuPDF 가동(정확도↑, 회귀 리스크 낮음).
3. **공격형**: 전체 문서 PyMuPDF 1차 적용 + 실패 로깅 강제(커버리지↑, 초기 튜닝 필요).

---

## 참고·근거

* `Page.get_text(opt, clip=..., sort=...)` 및 `"words"|"dict"|...` 옵션, `get_textbox`, `get_textpage_ocr`. ([PyMuPDF][1])
* `Page.find_tables(...)` 전략/파라미터(`lines|lines_strict|text`)와 반환 객체, `Table.extract()/to_pandas()`. ([PyMuPDF][1])
* TextPage/clip 동작과 영역 제한 처리(추출을 ROI로 제한). ([PyMuPDF][2])
* PyMuPDF LLM 도우미(`pymupdf4llm`) 테이블 전략 기본값/개념 참고. ([PyMuPDF][3])

---

### 슬래시 명령 (권장)

* `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
* `/logi-master --fast report`
* `/redo step step01_ofco_parse_pdf_patched.py --inject "roi_tuning"`

필요하면 `rows_to_lineitems(...)` 브리지 호출부를 당신 코드 기준으로 바로 맞춰 드릴게요.

[1]: https://pymupdf.readthedocs.io/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[2]: https://pymupdf.readthedocs.io/en/latest/textpage.html?utm_source=chatgpt.com "TextPage - PyMuPDF documentation"
[3]: https://pymupdf.qubitpi.org/en/latest/pymupdf4llm/api.html?utm_source=chatgpt.com "API - PyMuPDF documentation"
