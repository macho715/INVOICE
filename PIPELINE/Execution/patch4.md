# Exec Summary

SAFEEN/ADP 표(이미지 샘플) 대응용 **핫픽스**를 드립니다. 기존 `extract_invoice_items_pymupdf()`에 헤더 동의어 추가, ROI 앵커(“S No / Description / Invoice Total (AED)”), “첫 행이 헤더” 교정, 중복 헤더/푸터 드롭을 강화했습니다. 테이블 미검 시 `get_text("words")` 폴백은 유지. 근거: PyMuPDF `find_tables() / to_pandas() / search_for(..., clip=...) / get_text("words")` 공식 문서. ([pymupdf.qubitpi.org][1])

---

## Visual – 추가 매핑(표준 9컬럼)

| 원문(추가)                                              | 표준                | 메모       |
| --------------------------------------------------- | ----------------- | -------- |
| `S No` / `S/N`                                      | `sn`              | 정수 증가 검증 |
| `Tar. Code` / `Tariff ID`                           | `tariff_code`     | 문자열 유지   |
| `VAT %` / `TAX Rate`                                | `tax_rate`        | 5 → 0.05 |
| `VAT Amount` / `TAX Type/Amount (AED)`              | `tax_amount`      | 없으면 0.00 |
| `Total (Inc. VAT)` / `Total Amount incl. TAX (AED)` | `amount_incl_vat` | 필수       |

---

## ⬇️ Drop-in 핫픽스(기존 함수 **대체**; `step01_ofco_parse_pdf_patched.py` 상단 import 아래 붙여넣기)

```python
# === [HOTFIX v2] SAFEEN/ADP 강화: 헤더동의어/ROI/헤더승격/푸터·헤더드롭 ===
from __future__ import annotations
from typing import List, Dict, Iterable, Optional
import re, unicodedata, pandas as pd
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

_STD_ORDER = ["sn","tariff_code","description","qty","unit",
              "amount_excl_vat","tax_rate","tax_amount","amount_incl_vat"]

_SYNONYMS = {
    "sn": {"sno","sn","s/n"},
    "tariff_code": {"tarcode","tar.code","tariffid","tariff id","tariff","tariffcode"},
    "description": {"description","tariffdescription"},
    "qty": {"qty","quantity"},
    "unit": {"unit"},
    "amount_excl_vat": {"amountexcl.vat","amountexcltax(aed)","amountexcltax","amount","amount(aed)"},
    "tax_rate": {"vat%","vatpercent","taxrate","tax%","taxpercent","tax rate","taxrate(aed)"},
    "tax_amount": {"vatamount","taxtype/amount(aed)","taxamount","tax(aed)","vat amount"},
    "amount_incl_vat": {"total(inc.vat)","totalamountincl.tax(aed)","total","total(aed)",
                        "total amount incl. tax (aed)"}
}

_NUM = re.compile(r"[^\d\.\-]")
def _nfkc(s): return unicodedata.normalize("NFKC", s) if isinstance(s,str) else s
def _canon(s:str)->str: return re.sub(r"[\s\.\:_\-]+","",_nfkc(s or "").lower())
def _to_float(x):
    if x is None: return None
    s = _NUM.sub("", _nfkc(str(x)).strip().replace(",", ""))
    return float(s) if s else None

def _rename_by_synonyms(cols: Iterable[str]) -> List[str]:
    mapped=[]
    for c in cols:
        key=_canon(c); tgt=None
        for std, ks in _SYNONYMS.items():
            if key in ks: tgt=std; break
        mapped.append(tgt or _nfkc(c).strip())
    return mapped

def _promote_first_row_as_header_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    """to_pandas()가 첫 행을 데이터로 내보내는 케이스 교정"""
    if not df.shape[0]: return df
    # 헤더 후보가 포함되면 승격
    first = [str(x) for x in list(df.iloc[0])]
    if any("Description" in s or "S No" in s or "Tar" in s for s in first):
        df.columns = _rename_by_synonyms(first)
        df = df.drop(df.index[0]).reset_index(drop=True)
    return df

def _drop_headers_and_footers(df: pd.DataFrame) -> pd.DataFrame:
    # 중복 헤더(페이지 넘어가며 반복) 제거
    header_like = (
        (df.astype(str).apply(lambda r: "description" in " ".join(r.values).lower(), axis=1)) |
        (df.astype(str).apply(lambda r: "total (inc. vat" in " ".join(r.values).lower(), axis=1))
    )
    df = df.loc[~header_like]
    # Invoice Total / Amount in Words 등 푸터 제거
    if "description" in df.columns:
        m = df["description"].str.contains(r"invoice total|amount in words",
                                           flags=re.I, na=False)
        df = df.loc[~m]
    return df

def _postfix_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in ("qty","amount_excl_vat","tax_rate","tax_amount","amount_incl_vat"):
        if c in df.columns: df[c] = df[c].apply(_to_float)
    if "tax_rate" in df.columns and df["tax_rate"].notna().any():
        if (df["tax_rate"].dropna() >= 1.5).any():
            df["tax_rate"] = df["tax_rate"].apply(lambda v: v/100.0 if v is not None and v >= 1.5 else v)
    return df

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for c in _STD_ORDER:
        if c not in df.columns: df[c] = None
    return df[_STD_ORDER]

def _roi_anchor(page: "fitz.Page"):
    """헤더 근처로 ROI 축소 (잡음 많은 스캔 대응)."""
    try:
        for needle in ("S No","Description","Tar. Code","Invoice Total (AED)"):
            hits = page.search_for(needle)  # clip 파라미터는 내부에서 사용 가능
            if hits:
                r = hits[0]
                return fitz.Rect(r.x0-40, r.y0-25, page.rect.width-20, page.rect.height-20)
    except Exception:
        pass
    return None

def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict]:
    frames: List[pd.DataFrame] = []

    # 1) Table-first
    if fitz is not None:
        try:
            doc = fitz.open(pdf_path)
            for p in doc:
                roi = _roi_anchor(p)
                tf = p.find_tables(clip=roi) if roi else p.find_tables()
                if tf and getattr(tf,"tables",None):
                    for t in tf.tables:
                        df = t.to_pandas()
                        df = _promote_first_row_as_header_if_needed(df)
                        df.columns = _rename_by_synonyms(df.columns)
                        if "description" in df.columns:
                            df["description"] = (
                                df["description"].astype(str)
                                .str.replace(r"[\r\n]+"," ",regex=True).str.strip()
                            )
                        frames.append(df)
            doc.close()
        except Exception:
            pass

    # 2) Fallback: words 재조립
    if not frames and fitz is not None:
        try:
            from collections import defaultdict
            doc = fitz.open(pdf_path)
            for p in doc:
                words = p.get_text("words", sort=True)  # (x0,y0,x1,y1,word,block,line,idx)
                lines = defaultdict(list)
                for x0,y0,x1,y1,w,b,l,wn in words:
                    lines[(b,l)].append((x0,_nfkc(w)))
                text_lines = [" ".join(w for _,w in sorted(v)) for v in lines.values()]
                hdr = next((i for i,s in enumerate(text_lines)
                           if "description" in s.lower() and "total" in s.lower()), None)
                if hdr is None: continue
                body = text_lines[hdr+1:]
                rows=[]; cur={}
                for ln in body:
                    if re.search(r"invoice total|amount in words", ln, flags=re.I): break
                    cells = [c.strip() for c in re.split(r"\s{2,}", ln) if c.strip()]
                    if not cells: continue
                    if cells[0].isdigit():
                        if cur: rows.append(cur)
                        cur={"sn": int(cells[0])}
                        # 뒤쪽 숫자 3~4칸(금액, 세율, 세액, 합계) 역으로 추출
                        nums=[c for c in cells if _NUM.sub("", c)]
                        # tariff 코드 + desc 분리 시도
                        desc = " ".join(cells[1:len(cells)-max(3, len(nums)-1)])  # 보수적
                        m = re.match(r"^([0-9\.]+)\s+(.*)$", desc)
                        if m: cur["tariff_code"], desc = m.group(1), m.group(2)
                        cur["description"] = desc
                        # 숫자들 매핑
                        try:
                            cur["amount_excl_vat"] = _to_float(nums[-3])
                            cur["tax_rate"]        = _to_float(nums[-2])
                            cur["amount_incl_vat"] = _to_float(nums[-1])
                        except Exception:
                            pass
                    else:
                        if "description" in cur:
                            cur["description"] = (cur["description"] + " " + ln).strip()
                if cur: rows.append(cur)
                if rows: frames.append(pd.DataFrame(rows))
            doc.close()
        except Exception:
            pass

    if not frames: return []

    df = pd.concat(frames, ignore_index=True)
    df = _promote_first_row_as_header_if_needed(df)
    df = _drop_headers_and_footers(df)
    df = _postfix_numeric(df)
    df = _ensure_columns(df)

    try: df = df.sort_values("sn", kind="stable")
    except Exception: pass

    return df.to_dict(orient="records")
# === [/HOTFIX] ===============================================================
```

**후킹:** 기존 RegEx 파서 앞에서 먼저 호출(값 존재 시 그대로 반환).

```python
records = extract_invoice_items_pymupdf(pdf_path)
if records:
    return records
# … 기존 RegEx/state-machine 폴백 계속
```

---

## Options (pro/con/$/time)

1. **핫픽스만 적용(권장)**: SAFEEN/ADP 즉시 커버, 리스크 낮음 / 다른 양식은 동의어 보강 필요 / 비용 0 / 0.5d.
2. **헤더 동의어 YAML 외부화**: 유지보수 용이 / 초기 매핑 작업 필요 / 비용 0 / 0.5d.
3. **OCR 보강(저품질 스캔 전용)**: 인식률↑ / 속도↓ / 비용 0 / 0.5–1.0d.

---

## Roadmap (P→Pi→B→O→S + KPI)

* **Prepare**: PyMuPDF 설치(폐쇄망 시 wheel 방식)·테스트 PDF 4종 준비. KPI: 설치 실패 0.00%. ([PyMuPDF][2])
* **Pilot**: SAFEEN(두 건), ADP(두 건)로 A/B(기존 파서 대비) → KPI: 라인 파싱 성공률 ≥99.00%, 합계 오차 ≤0.01.
* **Build**: 동의어 YAML/단위 사전(LS/HR/DAY) 공통화.
* **Operate**: 실패 페이지 ROI 재시도 + 썸네일 저장. KPI: 재시도율 ≤5.00%.
* **Scale**: “Tariff ID”·부서별 커스텀 헤더 추가.

---

## QA 체크리스트

* [ ] SAFEEN 표: `3,091.25 / 0% / 0.00 / 3,091.25` 2라인 모두 캡처.
* [ ] ADP 표: `Tariff ID=201.3, Unit1=760.000, Rate=6.50 → Amount Excl=4,940.00` 파싱.
* [ ] `Invoice Total / Amount in Words` 라인 드롭.
* [ ] `tax_rate` 5 → 0.05 변환 확인.

**문서 근거**: `search_for(…, clip=…)`·TextPage/`get_text("words")` 튜플 스펙·`find_tables()`/`to_pandas()` 사용. ([pymupdf.qubitpi.org][1])

[1]: https://pymupdf.qubitpi.org/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[2]: https://pymupdf.readthedocs.io/_/downloads/en/latest/pdf/?utm_source=chatgpt.com "PyMuPDF Documentation"
