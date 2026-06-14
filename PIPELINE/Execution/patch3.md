# Exec Summary

SAFEEN·ADP 인보이스 표 레이아웃(이미지 제공)에 맞춰 `step01_ofco_parse_pdf_patched.py`에 **즉시 붙여넣는 확장 패치**를 드립니다. 파이프라인은 `find_tables()→to_pandas()` 우선, 실패 시 `get_text("words")` 라인 재조립 폴백을 사용합니다. 헤더 동의어(예: `S No|S/N`, `Tar. Code|Tariff ID`, `VAT %`, `Total (Inc. VAT)` 등)를 **표준 9컬럼**으로 정규화하고, `Invoice Total / Amount in Words` 같은 푸터는 자동 스킵합니다. ROI 보정은 `search_for(..., clip=...)` 기반으로 구현(선택). 근거: PyMuPDF `get_text`/`search_for`/`clip`, `find_tables()`·`to_pandas()` 문서, `words` 튜플 스펙, pip 오프라인 설치 가이드. ([PyMuPDF][1]) ([PyMuPDF][1]) ([PyMuPDF][2]) ([pip.pypa.io][3])

---

## Visual – 헤더 매핑(표준 9컬럼, 2 decimals)

| Vendor 패턴  | 원본 헤더 예시                                            | 표준 컬럼             | 처리 메모         |
| ---------- | --------------------------------------------------- | ----------------- | ------------- |
| SAFEEN     | `S No`                                              | `sn`              | 정수 증가 검증      |
| SAFEEN/ADP | `Tar. Code` / `Tariff ID`                           | `tariff_code`     | 문자열 유지        |
| SAFEEN/ADP | `Description` / `Tariff Description`                | `description`     | 멀티라인 병합       |
| SAFEEN/ADP | `Amount` / `Amount Excl TAX (AED)`                  | `amount_excl_vat` | 숫자 정규화        |
| SAFEEN/ADP | `VAT %` / `TAX Rate`                                | `tax_rate`        | 5→0.05 변환     |
| SAFEEN/ADP | `VAT amount` / `TAX Type/Amount (AED)`              | `tax_amount`      | 없으면 0.00      |
| SAFEEN/ADP | `Total (Inc. VAT)` / `Total Amount incl. TAX (AED)` | `amount_incl_vat` | 필수            |
| SAFEEN     | `Unit`(있을 때)                                        | `unit`            | `LS/HR/DAY` 등 |
| SAFEEN     | `Qty`(있을 때)                                         | `qty`             | float         |

---

## ⬇️ 붙여넣는 코드(파일 상단 import 아래·기존 패치 대체/추가)

> **함수 1개 + 유틸**만 추가하면 됩니다. 기존 RegEx 파서는 그대로 두고, **앞단에서 먼저 호출**해 있으면 해당 레코드를 사용하세요.

```python
# === [PATCH+SAFEEN/ADP] PyMuPDF table-first extractor (with header synonyms) ==
from __future__ import annotations
from typing import List, Dict, Iterable, Optional, Tuple
import re, unicodedata
import pandas as pd

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

# 표준 컬럼 세트(최종 출력)
_STD_ORDER = [
    "sn","tariff_code","description","qty","unit",
    "amount_excl_vat","tax_rate","tax_amount","amount_incl_vat"
]

# 헤더 동의어(대소/공백/점 제거 후 매칭)
_SYNONYMS = {
    "sn": {"sno", "sn", "s/n"},
    "tariff_code": {"tarcode", "tar.code", "tariffid", "tariff id", "tariff", "tariffcode"},
    "description": {"description", "tariffdescription"},
    "qty": {"qty", "quantity"},
    "unit": {"unit"},
    "amount_excl_vat": {
        "amountexcl.vat", "amountexcltax(aed)", "amountexcltax", "amount",
        "amount(aed)"
    },
    "tax_rate": {"vat%", "vatpercent", "taxrate", "taxrate(aed)", "tax%", "taxpercent"},
    "tax_amount": {"vatamount", "taxtype/amount(aed)", "taxamount", "tax(aed)"},
    "amount_incl_vat": {"total(inc.vat)", "totalamountincl.tax(aed)", "total", "total(aed)"}
}

# 숫자 정규화
_NUM = re.compile(r"[^\d\.\-]")
def _nfkc(s: Optional[str]) -> Optional[str]:
    return unicodedata.normalize("NFKC", s) if isinstance(s, str) else s

def _to_float(x) -> Optional[float]:
    if x is None: return None
    s = _nfkc(str(x)).strip().replace(",", "")
    s = _NUM.sub("", s)
    return float(s) if s else None

def _canon(s: str) -> str:
    return re.sub(r"[\s\.\:_\-]+", "", _nfkc(s or "").lower())

def _rename_by_synonyms(cols: Iterable[str]) -> List[str]:
    mapped = []
    for c in cols:
        key = _canon(c)
        target = None
        for std, ks in _SYNONYMS.items():
            if key in ks:
                target = std; break
        mapped.append(target or _nfkc(c).strip())
    return mapped

def _postfix_numeric(df: pd.DataFrame) -> pd.DataFrame:
    # 수치 필드 변환
    for c in ("qty","amount_excl_vat","tax_rate","tax_amount","amount_incl_vat"):
        if c in df.columns:
            df[c] = df[c].apply(_to_float)
    # 세율 보정(5 → 0.05)
    if "tax_rate" in df.columns and df["tax_rate"].notna().any():
        s = df["tax_rate"].dropna()
        if (s >= 1.5).any():
            df["tax_rate"] = df["tax_rate"].apply(lambda v: v/100.0 if v is not None and v >= 1.5 else v)
    return df

def _drop_footers(df: pd.DataFrame) -> pd.DataFrame:
    # 표 하단 합계/금액문구 라인 제거
    footer_masks = []
    if "description" in df.columns:
        footer_masks.append(df["description"].str.contains(r"invoice total|amount in words", flags=re.I, na=False))
    if footer_masks:
        m = footer_masks[0]
        for mm in footer_masks[1:]:
            m |= mm
        df = df.loc[~m]
    # 전열이 비거나 SN이 비정상인 행 제거
    if "sn" in df.columns:
        df = df[~df["sn"].astype(str).str.contains(r"[^\d]", na=False)]
    return df

def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for c in _STD_ORDER:
        if c not in df.columns:
            df[c] = None
    return df[_STD_ORDER]

def _roi_clip(page: "fitz.Page") -> Optional["fitz.Rect"]:
    """선택: 헤더 주변을 ROI로 제한(잡음 많은 문서용)."""
    try:
        hits = page.search_for("Description", clip=None)  # 헤더 라벨 근처
        if not hits:
            return None
        r = hits[0]
        # 헤더 상단에서 우측/하단으로 넓게 확장
        return fitz.Rect(r.x0 - 30, r.y0 - 20, page.rect.width - 20, page.rect.height - 20)
    except Exception:
        return None

def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict]:
    """
    SAFEEN / ADP 인보이스 표 전용:
    1) find_tables()->to_pandas() 우선
    2) 실패 시 get_text('words') 라인 재조립
    3) 헤더 동의어 기반 표준 9컬럼으로 정규화
    4) 합계/문구 행 제거
    """
    frames: List[pd.DataFrame] = []

    # ---- 1) Table-first ------------------------------------------------------
    if fitz is not None:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                roi = _roi_clip(page)  # 선택적 ROI
                tf = page.find_tables(clip=roi) if roi else page.find_tables()
                if tf and getattr(tf, "tables", None):
                    for t in tf.tables:
                        df = t.to_pandas()  # DataFrame 변환
                        # 헤더 매핑
                        df.columns = _rename_by_synonyms(df.columns)
                        # 멀티라인 설명 정리
                        if "description" in df.columns:
                            df["description"] = (
                                df["description"].astype(str)
                                  .str.replace(r"[\r\n]+", " ", regex=True)
                                  .str.strip()
                            )
                        frames.append(df)
            doc.close()
        except Exception:
            pass

    # ---- 2) Fallback: words 재조립 ------------------------------------------
    if not frames and fitz is not None:
        try:
            doc = fitz.open(pdf_path)
            from collections import defaultdict
            for page in doc:
                words = page.get_text("words", sort=True)  # (x0,y0,x1,y1,word,b,l,idx)
                lines = defaultdict(list)
                for x0,y0,x1,y1,w,b,l,wn in words:
                    lines[(b,l)].append((x0, _nfkc(w)))
                text_lines = [" ".join(w for _, w in sorted(v)) for v in lines.values()]
                # 헤더 탐색: SAFEEN / ADP 공통 키
                hdr_i = next((i for i,s in enumerate(text_lines)
                              if ("description" in s.lower() and "total" in s.lower())), None)
                if hdr_i is None:
                    continue
                body = text_lines[hdr_i+1:]
                rows = []
                cur: Dict[str, object] = {}
                for ln in body:
                    if re.search(r"invoice total|amount in words", ln, flags=re.I):
                        break
                    cells = [c.strip() for c in re.split(r"\s{2,}", ln) if c.strip()]
                    if not cells: 
                        continue
                    # 신규 행 시작: 첫 셀 정수
                    if cells[0].isdigit():
                        if cur: rows.append(cur)
                        cur = {"sn": int(cells[0])}
                        # SAFEEN 형태(7~8열) 가정 + 유도 파싱
                        # ex) [sn, tariff?/desc, desc..., amount, vat%, vat_amt, total]
                        # desc가 길어 공간 분할이 흔들리므로 뒤 3~4칸은 숫자 필드로 역-채움
                        if len(cells) >= 5:
                            # 뒤에서 숫자 3~4개 추출
                            nums = []
                            tail = list(reversed(cells))
                            for c in tail:
                                if _NUM.sub("", c):
                                    nums.append(c)
                                if len(nums) >= 4:
                                    break
                            nums = list(reversed(nums))
                            # 나머지는 desc로 결합
                            desc_part = " ".join(cells[1:len(cells)-len(nums)]) or ""
                            cur["description"] = desc_part
                            # 숫자 필드 매핑
                            if len(nums) >= 3:
                                cur["amount_excl_vat"] = _to_float(nums[-3])
                                cur["tax_rate"] = _to_float(nums[-2])
                                cur["tax_amount"] = _to_float(nums[-2]) and 0.0 if "%" in nums[-2] and len(nums)==3 else _to_float(nums[-2])
                                cur["amount_incl_vat"] = _to_float(nums[-1])
                            # tariff code 추출 시도
                            m = re.match(r"^([0-9\.]+)\s+(.*)$", desc_part)
                            if m:
                                cur["tariff_code"] = m.group(1)
                                cur["description"] = m.group(2)
                    else:
                        if "description" in cur:
                            cur["description"] = (cur["description"] + " " + ln).strip()
                if cur: rows.append(cur)
                if rows:
                    frames.append(pd.DataFrame(rows))
            doc.close()
        except Exception:
            pass

    if not frames:
        return []

    df = pd.concat(frames, ignore_index=True)
    df = _drop_footers(df)
    df = _postfix_numeric(df)
    df = _ensure_columns(df)

    # 정렬: sn
    try:
        df = df.sort_values("sn", kind="stable")
    except Exception:
        pass

    return df.to_dict(orient="records")
# === [/PATCH] ================================================================
```

**후킹:** 기존 RegEx 파서 진입부에서 먼저 호출하세요. 값이 있으면 그대로 사용.

```python
records = extract_invoice_items_pymupdf(pdf_path)
if records:
    return records   # 표 파싱 성공 시 그대로 반환
# … 이하 기존 RegEx/state-machine 폴백
```

---

## Options (pro / con / $ / time)

1. **Table-first + words 폴백(권장)**: 정확도↑, 구현 단순 / 일부 PDF에서 테이블 미검(ROI 보정 포함) / 비용 無 / 0.5d. ([PyMuPDF][1])
2. **ROI 고정 강화**: `search_for('Description', clip=…)`로 영역 제한 → 오검 줄임 / 라벨 다국어 변형 시 튜닝 필요 / 비용 無 / 0.5d. ([pymupdftest.readthedocs.io][4])
3. **OCR TextPage 보완**: 스캔 품질 저하 파일용(부분 OCR) / 속도↓ / 비용 無 / 0.5–1.0d. ([PyMuPDF][1])

---

## Roadmap (P→Pi→B→O→S + KPI)

* **Prepare**: `PyMuPDF>=1.23`(find_tables) + pandas 의존성 명시; 폐쇄망은 `pip download -d wheels …` → `--no-index --find-links wheels`로 설치. KPI: 설치 실패 0.00%. ([pip.pypa.io][3])
* **Pilot**: SAFEEN 2건 + ADP 1건으로 A/B(기존 RegEx 대비) → KPI: 라인 파싱 성공률 +20.00pp, 금액합 오차 ≤0.01.
* **Build**: 패치 반영, 헤더 동의어 YAML 외부화(선택).
* **Operate**: 실패 페이지는 ROI 재시도 로그 + 썸네일 저장. KPI: 재시도율 ≤5.00%.
* **Scale**: `Tariff ID` 사전·단위 사전(LS/HR/DAY) 공통화.

---

## Automation / 오프라인 설치

* 온라인: `pip download -d wheels "PyMuPDF>=1.23,<2" pandas` → 폐쇄망: `pip install --no-index --find-links wheels PyMuPDF pandas` (동일 파이썬/플랫폼 wheel 준비). ([pip.pypa.io][3])

---

## QA / Re-check

* [ ] SAFEEN 표에서 `3,091.25 / 0% / 0.00 / 3,091.25` 라인이 정확히 캡처되는가(푸터 미포함).
* [ ] ADP 표에서 `Tariff ID=201.3, Unit1=760.000, Rate=6.50 → Amount Excl=4,940.00`이 `amount_excl_vat=4940.00`으로 수치화되는가.
* [ ] `tax_rate`가 `5 → 0.05`로 변환되는가.
* [ ] 합계/문구(Invoice Total/Amount in Words) 라인 제거 확인.

---

## CmdRec

* `/automate test-pipeline --target=SAFEEN,ADP --cache-reset`
* `/logi-master --fast report` (A/B 성능·정확도)
* `/redo step step01_ofco_parse_pdf_patched.py --inject "find_tables+synonyms+roi_fallback"`

**참고 소스**: PyMuPDF `get_text`/`search_for`/`clip`·`get_textpage`/OCR·`find_tables()`·`to_pandas()`·`words` 포맷, pip 오프라인 설치 문서. ([PyMuPDF][1]) ([PyMuPDF][1]) ([PyMuPDF][1]) ([PyMuPDF][2]) ([pip.pypa.io][3])

[1]: https://pymupdf.readthedocs.io/en/latest/page.html?utm_source=chatgpt.com "Page - PyMuPDF documentation"
[2]: https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html?utm_source=chatgpt.com "API - PyMuPDF documentation"
[3]: https://pip.pypa.io/en/stable/cli/pip_download/?utm_source=chatgpt.com "pip download - pip documentation v25.3"
[4]: https://pymupdftest.readthedocs.io/en/stable/page.html?utm_source=chatgpt.com "Page — PyMuPDF 1.20.2 documentation"
