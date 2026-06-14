# Exec Summary

* 요청대로 `step01_ofco_parse_pdf_patched.py` 안에 **그대로 붙여 넣어 작동**하는 PyMuPDF 테이블 추출(+words 폴백) 함수를 드립니다. 우선 `Page.find_tables()`→`Table.to_pandas()`로 표를 받고, 실패 시 `get_text("words")` 라인 재조립로 파싱합니다. (PyMuPDF 문서: find_tables / to_pandas / words 포맷) ([PyMuPDF][1])
* 헤더는 표준 컬럼으로 리네임(`S N, Description, … → sn, description, …`), 수치는 콤마·기호 제거 후 float로 정규화합니다.
* **후킹 한 줄**도 함께 제공합니다: 기존 RegEx 파서 전에 `records = extract_invoice_items_pymupdf(pdf_path)` 호출→값이 있으면 그대로 사용.

---

## ⬇️ 그대로 붙여 넣는 패치(파일 상단 import 아래 배치)

```python
# === [PATCH] PyMuPDF table-first extractor (drop-in) =========================
# Requirements: PyMuPDF >= 1.23 (find_tables / to_pandas), pandas.
# Docs: Page.find_tables() / Table.to_pandas() / Page.get_text("words")
#  - find_tables / to_pandas: https://pymupdf.readthedocs.io/en/latest/page.html
#  - words tuple format: https://pymupdf.readthedocs.io/en/latest/app1.html
from __future__ import annotations
from typing import List, Dict
import re
import unicodedata

try:
    import fitz  # PyMuPDF
except Exception as e:
    fitz = None  # 환경에 따라 Optional (오프라인 설치 후 사용)

import pandas as pd

# 표 헤더 표준화 매핑
_STD_RENAME = {
    "S N": "sn",
    "S/N": "sn",
    "Description": "description",
    "Tax Rate": "tax_rate",
    "Qty": "qty",
    "Unit Price": "unit_price",
    "Unit": "unit",
    "Amount excl. VAT": "amount_excl_vat",
    "Tax Amount": "tax_amount",
    "Amount incl. VAT": "amount_incl_vat",
}

_NUM = re.compile(r"[^\d\.\-]")  # 숫자/부호 외 제거

def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s) if isinstance(s, str) else s

def _to_float(x):
    if x is None:
        return None
    s = _nfkc(str(x)).strip().replace(",", "")
    s = _NUM.sub("", s)
    return float(s) if s else None

def _post_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in ("tax_rate","qty","unit_price","amount_excl_vat","tax_amount","amount_incl_vat"):
        if c in df.columns:
            df[c] = df[c].apply(_to_float)
    # %가 포함된 원시값이 넘어온 경우(폴백 경로) 보정
    if "tax_rate" in df.columns and df["tax_rate"].notna().any():
        # 1.00~20.00 범위면 이미 비율로 본다(0~1 사이면 그대로)
        m = df["tax_rate"].dropna()
        if (m >= 1.5).any():  # 5 → 0.05 식 변환
            df["tax_rate"] = df["tax_rate"].apply(lambda v: v/100.0 if v is not None and v >= 1.5 else v)
    return df

def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict]:
    """
    우선: PyMuPDF 테이블 추출(find_tables→to_pandas)
    폴백: words 라인 재조립으로 헤더/바디 파싱
    반환: [{sn, description, tax_rate, qty, unit_price, unit, amount_excl_vat, tax_amount, amount_incl_vat}, ...]
    """
    frames: List[pd.DataFrame] = []

    # ---- 1) Table-first (find_tables → to_pandas) ---------------------------
    if fitz is not None:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                tf = page.find_tables()  # 표 감지 (텍스트/선 혼합 알고리즘)
                if tf and getattr(tf, "tables", None):
                    for t in tf.tables:
                        df = t.to_pandas()  # 바로 DataFrame 변환
                        # 헤더 정규화
                        df.columns = [_STD_RENAME.get(_nfkc(str(c)).strip(), _nfkc(str(c)).strip()) for c in df.columns]
                        # 멀티라인 Description 정리
                        if "description" in df.columns:
                            df["description"] = df["description"].astype(str).apply(lambda s: _nfkc(s.replace("\n"," ").replace("\r"," ").strip()))
                        frames.append(df)
            doc.close()
        except Exception:
            pass  # 테이블 인식 실패 → 폴백 경로로 계속

    # ---- 2) Fallback: words 라인 재조립 --------------------------------------
    if not frames:
        try:
            doc = fitz.open(pdf_path) if fitz is not None else None
            if doc is not None:
                from collections import defaultdict
                for page in doc:
                    words = page.get_text("words", sort=True)  # (x0,y0,x1,y1,word,block,line,idx)
                    lines = defaultdict(list)
                    for x0,y0,x1,y1,w,b,l,wn in words:
                        lines[(b,l)].append((x0, _nfkc(w)))
                    text_lines = [" ".join(w for _, w in sorted(v)) for v in lines.values()]
                    # 헤더 라인 탐색
                    hdr_idx = next((i for i, s in enumerate(text_lines)
                                    if "Description" in s and ("Amount incl" in s or "Amount incl. VAT" in s)), None)
                    if hdr_idx is None:
                        continue
                    body = text_lines[hdr_idx + 1 :]
                    rows = []
                    cur = {}
                    for ln in body:
                        # 넓은 공백(두 칸 이상) 기준으로 칼럼 분할
                        cells = [c.strip() for c in re.split(r"\s{2,}", ln) if c.strip()]
                        # S/N 정수면 신규 행
                        if cells and cells[0].isdigit():
                            if cur:
                                rows.append(cur)
                            cur = {"sn": int(cells[0]), "description": cells[1] if len(cells) > 1 else ""}
                            tail = cells[2:]
                            # [tax, qty, unit_price, unit, excl, tax_amt, incl] 예상
                            if len(tail) >= 6:
                                cur["tax_rate"] = _to_float(tail[0])
                                cur["qty"] = _to_float(tail[1])
                                cur["unit_price"] = _to_float(tail[2])
                                cur["unit"] = _nfkc(tail[3])
                                cur["amount_excl_vat"] = _to_float(tail[4])
                                cur["tax_amount"] = _to_float(tail[5])
                                if len(tail) >= 7:
                                    cur["amount_incl_vat"] = _to_float(tail[6])
                        else:
                            # 멀티라인 Description 이어붙이기
                            if "description" in cur:
                                cur["description"] = (cur["description"] + " " + ln).strip()
                    if cur:
                        rows.append(cur)
                    if rows:
                        df = pd.DataFrame(rows)
                        frames.append(df)
                if doc is not None:
                    doc.close()
        except Exception:
            pass

    if not frames:
        return []

    df_all = pd.concat(frames, ignore_index=True)

    # 최소 컬럼 세트 보정
    need = ["sn","description","tax_rate","qty","unit_price","unit","amount_excl_vat","tax_amount","amount_incl_vat"]
    for c in need:
        if c not in df_all.columns:
            df_all[c] = None

    df_all = _post_numeric(df_all)
    # 정렬: sn > 원문 순서(가능하면)
    if "sn" in df_all.columns:
        try:
            df_all = df_all.sort_values("sn", kind="stable")
        except Exception:
            pass

    # 최종 dict 레코드로 반환
    return df_all[need].to_dict(orient="records")
# === [/PATCH] =================================================================
```

### 호출(후킹) 위치 — 기존 RegEx 파서 앞에 한 줄

```python
# (예) parse_items(...) 또는 build_line_items(...) 시작부에 추가
records = extract_invoice_items_pymupdf(pdf_path)
if records:  # PyMuPDF에서 표를 확보한 경우, 그대로 사용
    return records
# ↓ 아래는 기존 RegEx / 상태기계 파서 폴백 로직 지속
```

---

### 참고(근거)

* `find_tables()` / `Table.to_pandas()` 공식 문서 – PyMuPDF 1.23+ 제공. 표→DataFrame 변환을 지원. ([PyMuPDF][1])
* `get_text("words")` 포맷: `(x0, y0, x1, y1, "word", block_no, line_no, word_no)` — 라인 재구성·열 분할의 기준으로 활용. ([PyMuPDF][2])

원하시면 이 함수에 **헤더 ROI 고정(`search_for`+`clip`)** 보정 루틴도 바로 덧붙여 드릴게요.

[1]: https://pymupdf.readthedocs.io/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[2]: https://pymupdf.readthedocs.io/en/latest/app1.html?utm_source=chatgpt.com "Appendix 1: Details on Text Extraction - PyMuPDF documentation"
