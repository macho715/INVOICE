# Exec Summary

* **PyMuPDF(fitz) 우선 추출 → pypdf → PyPDF2 폴백**으로 교체·주입했습니다. `rawdict/words` 재조립 + **NFKC 정규화**로 한자/전각·합자 이슈를 줄이고, **의심률(bad-char ratio)** 기준으로 OCR 폴백 힌트까지 전달합니다. 근거: PyMuPDF `get_text` 모드·flags/clip, `words` 스펙. ([PyMuPDF][1])
* **ROI(clip) + search_for**로 라벨→값 추출(Invoice No, Date, FX, Vessel 등) 안정화; 표 행은 `words`로 동일 line-id 재조립. ([PyMuPDF][2])
* 업로드 PDF(OFCO-INV-0000845)로 검증: Invoice No·Date·Currency·Vessel·FX·Grand Total 등 핵심 메타가 원문에 존재함(아래 표). 
* 오프라인 설치는 `pip download …`→폐쇄망 `--no-index --find-links` 절차 권장(윈도우 OK). ([pip.pypa.io][3])

---

## Visual — 검증 메타(샘플, 2 decimals)

| Field               | Value              | Evidence |
| ------------------- | ------------------ | -------- |
| Invoice No          | OFCO-INV-0000845   |          |
| Date                | 15 September, 2025 |          |
| Currency            | USD                |          |
| Vessel              | Jopetwill 71       |          |
| Exchange Rate (AED) | 3.6725             |          |
| Grand Total (USD)   | 90,665.33          |          |

> 표/라인 예: “ADP Port Dues & Services”, “SAFEEN Channel Crossing”, “MGO Supply…”, “Yard Storage…” 등 항목 다수 확인. 

---

## Patch — `step01_ofco_parse_pdf_patched.py` 교체 블록

아래 함수로 **기존 `extract_text_from_pdf()` 전체 교체**(drop-in). CJK/한자 대응 + 의심률 기반 OCR 힌트 + 폴백 순서 고정.

```python
def extract_text_from_pdf(pdf_path: str, max_pages: int = 2) -> str:
    """CJK/한자 강건 추출: PyMuPDF -> pypdf -> PyPDF2 -> 바이너리 디코드.
    - Page.get_text('rawdict') 재조립 + 'text'(sort=True) 폴백
    - NFKC 정규화 + zero-width 제거
    - 치환문자 비율(bad_ratio) 초과 시 OCR 힌트 라인 주입
    """
    import re, unicodedata
    def _normalize_cjk(s: str) -> str:
        s = unicodedata.normalize("NFKC", s)
        return re.sub(r"[\u200B-\u200D\uFEFF]", "", s)

    # 1) PyMuPDF 우선
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        pages_to_extract = min(max_pages, doc.page_count)
        lines_all: list[str] = []
        for i in range(pages_to_extract):
            page = doc[i]
            try:
                rd = page.get_text("rawdict")  # raw 구조
                page_lines = []
                for b in rd.get("blocks", []):
                    if b.get("type") != 0:
                        continue
                    for ln in b.get("lines", []):
                        spans = [sp.get("text", "") for sp in ln.get("spans", []) if sp.get("text")]
                        if spans:
                            page_lines.append("".join(spans))
                text = "\n".join(page_lines) or page.get_text("text", sort=True)
            except Exception:
                text = page.get_text("text", sort=True)
            lines_all.append(_normalize_cjk(text))
        full_text = "\n".join(lines_all)
        bad_ratio = (full_text.count("�") / max(1, len(full_text))) if full_text else 0.0
        if bad_ratio > 0.005:
            full_text += "\n[[OFCO_HINT: CJK_OCR_FALLBACK_SUGGESTED]]"
        return full_text
    except Exception:
        pass

    # 2) pypdf
    try:
        import pypdf
        r = pypdf.PdfReader(pdf_path)
        buf = [(r.pages[i].extract_text() or "") for i in range(min(max_pages, len(r.pages)))]
        return _normalize_cjk("\n".join(buf))
    except Exception:
        pass

    # 3) PyPDF2
    try:
        import PyPDF2
        r = PyPDF2.PdfReader(pdf_path)
        buf = [(r.pages[i].extract_text() or "") for i in range(min(max_pages, len(r.pages)))]
        return _normalize_cjk("\n".join(buf))
    except Exception:
        with open(pdf_path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
```

### (신규) ROI/Words 유틸 — 라벨→값 & 표 라인 재조립

PyMuPDF 공식 스펙: `words` 튜플(x0,y0,x1,y1,word,block,line,idx), `search_for`, `clip`, `flags`. ([PyMuPDF][4])

```python
def extract_words_by_line(pdf_path: str, page_index: int = 0) -> list[str]:
    import fitz, unicodedata, re
    doc, page = fitz.open(pdf_path), None
    try:
        page = doc[page_index]
        words = page.get_text("words", sort=True)
        from collections import defaultdict
        lines = defaultdict(list)
        for x0,y0,x1,y1,w,b,l,wn in words:
            lines[(b,l)].append((x0,w))
        text_lines = [" ".join(w for _, w in sorted(v)) for v in lines.values()]
        text = "\n".join(text_lines)
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
        return text_lines
    finally:
        if doc: doc.close()

def find_value_after_label(pdf_path: str, label: str, expand=(30,0,220,16), page_index: int = 0) -> str:
    import fitz
    doc, page = fitz.open(pdf_path), None
    try:
        page = doc[page_index]
        rects = page.search_for(label)  # 라벨 bbox
        if not rects: return ""
        r = rects[0] + expand  # 우측 확장
        return (page.get_text("text", sort=True, clip=r) or "").strip()
    finally:
        if doc: doc.close()
```

> 통합 포인트: 기존 `ParserState` 진입 전, `invoice_no / date / currency / vessel / fx`를 `find_value_after_label()`로 1차 시도 → 실패 시 기존 정규식 폴백.

---

## How-To 통합 (요약)

1. `step01_ofco_parse_pdf_patched.py`에 **교체 함수 + 2 유틸 추가**.
2. `parse_invoice_meta()` 초입에서:

```python
meta.invoice_number = meta.invoice_number or find_value_after_label(path, "Invoice number")
meta.invoice_date   = meta.invoice_date   or find_value_after_label(path, "Date")
meta.currency       = meta.currency       or find_value_after_label(path, "Invoice Currency")
meta.vessel_name    = meta.vessel_name    or find_value_after_label(path, "Vessel Name")
meta.exchange_rate  = meta.exchange_rate  or find_value_after_label(path, "Exch. Rate")
```

3. `items` 파트에서 `extract_words_by_line()` 결과를 한 줄씩 상태기계에 공급(현행 정규식 유지) → 숫자 붙어나옴/개행 이슈 완화. 근거: `words` 라인 식별. ([PyMuPDF][4])

---

## Options (pro/con/$/risk/time)

1. **PyMuPDF 우선 + 폴백(권장)**: CJK/레이아웃 안정↑ / 신규 wheel(≈10–20MB) / 리스크 낮음 / 0.5d. ([PyMuPDF][1])
2. **ROI+Words 하이브리드**: 라벨·표 정합성↑ / 구현비용↑ / 레이아웃 대변경 시 룰 업데이트 / 0.5–1.0d. ([PyMuPDF][2])
3. **pymupdf4llm 병행(MD→DF)**: 표 자동추출·RAG 친화 / 일부 표 손실 가능 / 도입 쉬움 / 0.5d. ([GitHub][5])

---

## Roadmap (P→Pi→B→O→S + KPI)

* **Prepare**: `requirements-313.txt`에 `pymupdf==1.26.*` 고정, 오프라인 wheel 캐시. KPI: 설치 실패 0.00%. ([pip.pypa.io][3])
* **Pilot**: OFCO 샘플 10건(스캔/디지털 혼합) A/B. KPI: **메타 추출 성공률 +8.00pp**, **라인 파싱 실패 -30.00%**.
* **Build**: 위 패치 주입, `[[OFCO_HINT:...]]` 인식→OCR 경로 자동 전환.
* **Operate**: 실패 케이스에 `clip ROI` 스냅샷 저장, 리포트 링크. KPI: 재처리율 ≤5.00%.
* **Scale**: `words` 기반 수치 안정화 규칙(통화·소수점) 공통화.

---

## Automation (오프라인 설치/RPA)

* **온라인 머신**: `py -m pip download -d wheels PyMuPDF==1.26.* pymupdf4llm`
* **폐쇄망 머신**: `py -m pip install --no-index --find-links wheels PyMuPDF==1.26.* pymupdf4llm` ([pip.pypa.io][3])
* 파서 실패 시 **TG 알림 + 썸네일**(page clip).

---

## QA / Re-check

* [ ] 업로더 PDF에서 `Invoice No/Date/Currency/Vessel/FX/Grand Total` 추출 확인(위 표 근거). 
* [ ] `bad_ratio > 0.50%` 시 OCR 폴백 힌트 라인 감지.
* [ ] 기존 EA/Price Center 계산 결과 **행위 불변**.
* [ ] `words` 라인 재조립 후 숫자·쉼표·소수점 정확도 유지. ([PyMuPDF][4])

---

## CmdRec

* `/automate_workflow build-wheels --pkgs "PyMuPDF==1.26.* pymupdf4llm" --out wheels`
* `/logi-master --fast report` (A/B: 파싱성공률·처리시간)
* `/redo step step01_ofco_parse_pdf_patched.py --inject "fitz_rawdict, words_reline, roi_search"`

**참고(스펙 문서):** PyMuPDF flags/clip, TextPage/words, search_for, 함수 레퍼런스; pip 오프라인 설치 가이드. ([PyMuPDF][6])

[1]: https://pymupdf.readthedocs.io/_/downloads/en/latest/pdf/?utm_source=chatgpt.com "PyMuPDF Documentation"
[2]: https://pymupdf.readthedocs.io/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[3]: https://pip.pypa.io/en/stable/cli/pip_download/?utm_source=chatgpt.com "pip download - pip documentation v25.3"
[4]: https://pymupdf.readthedocs.io/en/latest/app1.html?utm_source=chatgpt.com "Appendix 1: Details on Text Extraction - PyMuPDF documentation"
[5]: https://github.com/pymupdf/RAG?utm_source=chatgpt.com "GitHub - pymupdf/pymupdf4llm: PyMuPDF4LLM"
[6]: https://pymupdf.readthedocs.io/en/latest/vars.html?utm_source=chatgpt.com "Constants and Enumerations - PyMuPDF documentation"
