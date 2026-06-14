아래는 **Pure Windows(WSL 불필요)** 환경에서 바로 돌릴 수 있도록, 주신 스크립트를 대폭 업그레이드한 버전입니다.
핵심 개선점은 다음과 같습니다.

* **Docling CLI 호출을 정식 옵션으로 수정** (`--to html` 또는 **`html_split_page`** 지원, `--output`, `--tables` 등)  ([docling-project.github.io][1])
* **폴더/파일 입력, 재귀 처리, HTML 자동 수집**, 변환 실패 시 건너뛰기/로그 남기기
* **헤더 매핑 강화 + 퍼지 매칭(SequenceMatcher)** 로 낯선 헤더도 대부분 정규화
* **숫자 파서 고급화**: 천단위/소수점(유럽식 포함), **괄호 음수 (accounting)** 처리, 통화/공백/기호 제거  ([pandas.pydata.org][2])
* **줄바꿈/랩핑된 설명행 자동 병합**, 헤더 반복행/빈행 제거
* **검증 컬럼**: `CalcAmount`, `Delta`, `DeltaFlag`(기준 초과 여부) 추가
* **Excel 리포트**(XLSX)로 저장 + **조건부 서식**(Delta>임계치 빨간 음영)  ([xlsxwriter.readthedocs.io][3])

> ⚠️ 참고: Docling CLI에는 `--layout=stream` 옵션이 없습니다. (이는 Camelot의 개념에 가깝습니다.) Docling은 `--to`로 **`html`/`html_split_page`** 형식을 지원하며, `--output`으로 출력 폴더를 지정합니다.  ([docling-project.github.io][1])

---

## 설치(한번만)

PowerShell(관리자 아님)에서:

```powershell
pip install docling pandas lxml html5lib xlsxwriter
```

* `pandas.read_html`는 `lxml`/`bs4`를 사용합니다. 기본은 `lxml` 권장.  ([pandas.pydata.org][2])
* XLSX 저장과 조건부 서식은 `XlsxWriter` 예제를 참조했습니다.  ([xlsxwriter.readthedocs.io][3])

---

## 업그레이드된 스크립트 (drop‑in)

아래 내용을 `invoice_extract_win.py` 로 저장하세요.

```python
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd

# ---------------------------
# 0) 설정
# ---------------------------
CANON_COLS = ["SourcePDF", "SourceHTML", "Page", "Description", "Quantity", "UoM", "UnitPrice", "Amount", "HSCode"]
NUM_COLS = ["Quantity", "UnitPrice", "Amount"]
DELTA_THRESHOLD = 0.01  # 통화 미지정 환경: 1센트/원 단위 기준(필요시 조정)

# 헤더 표준화 사전(언어/표기 변형 확장)
HEADER_MAP = {
    # Description
    "description": "Description", "item desc": "Description", "item description": "Description",
    "product": "Description", "part": "Description", "품명": "Description", "설명": "Description", "내역": "Description",
    # Quantity
    "qty": "Quantity", "quantity": "Quantity", "수량": "Quantity", "q'ty": "Quantity", "q-ty": "Quantity",
    # Unit price
    "unit price": "UnitPrice", "rate": "UnitPrice", "unit cost": "UnitPrice", "price": "UnitPrice", "단가": "UnitPrice",
    # Amount
    "amount": "Amount", "line total": "Amount", "ext price": "Amount", "extended price": "Amount",
    "금액": "Amount", "합계": "Amount", "total": "Amount", "라인합계": "Amount",
    # UoM
    "uom": "UoM", "unit": "UoM", "단위": "UoM",
    # HSCode
    "hs code": "HSCode", "hs": "HSCode", "hscode": "HSCode", "hs-code": "HSCode", "h.s. code": "HSCode",
}

# UoM 표준화(필요시 확장)
UOM_MAP = {
    "ea": "EA", "each": "EA", "pcs": "EA", "pc": "EA",
    "kg": "KG", "g": "G", "lb": "LB", "l": "L", "m": "M", "cm": "CM", "mm": "MM",
}

def norm_text(s: str) -> str:
    """NFKC 정규화 + 소문자 + 연속 공백 축소 + 주변 공백 제거"""
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def normalize_header(col: str) -> str:
    """헤더 맵 + 퍼지 매칭으로 표준화"""
    raw = norm_text(col)
    if raw in HEADER_MAP:
        return HEADER_MAP[raw]
    # 퍼지 매칭 (간단 유사도)
    candidates = list(HEADER_MAP.keys())
    best = max(candidates, key=lambda k: SequenceMatcher(None, raw, k).ratio(), default=None)
    if best and SequenceMatcher(None, raw, best).ratio() >= 0.82:
        return HEADER_MAP[best]
    return col.strip()

def parse_page_from_filename(html_path: Path) -> pd.Series:
    """파일명에서 페이지 번호 추출 (html_split_page 대비). ex) invoice_page_3.html"""
    m = re.search(r"page[_\-](\d+)", html_path.stem, flags=re.I)
    return int(m.group(1)) if m else pd.NA

def to_number(x):
    """
    문자열→실수 변환:
    - 통화/문자 제거
    - 괄호 음수 (e.g. (1,234.56) → -1234.56)
    - 천단위/소수점: 둘 다 있을 때 마지막 구분자를 소수점으로 간주 (EU/US 혼합 허용)
    - 콤마만 있을 경우: 마지막 토막 길이(2~3) & 중간 토막 3자리 반복이면 소수점으로 해석, 아니면 천단위로 제거
    참고: pandas.read_html의 thousands/decimal 인자와 별개로 셀 단위 후처리에 안전하게 동작. 
    """
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "-"}:
        return pd.NA

    # 괄호 음수 (accounting)
    neg = False
    if re.match(r"^\((.*)\)$", s):
        neg = True
        s = s[1:-1]

    # 통화/문자 제거(숫자, . , - , , 만 남김)
    s = re.sub(r"[^\d\.,\-]", "", s)

    # -, ., , 순서 정리(부호는 맨 앞으로)
    # 양쪽에 -가 여러개면 첫 것만
    s = re.sub(r"(?<=\d)-", "", s)

    if "," in s and "." in s:
        # 마지막 구분자를 소수점으로 간주
        last_pos = max(s.rfind(","), s.rfind("."))
        dec = s[last_pos]
        thou = "," if dec == "." else "."
        s = s.replace(thou, "")
        s = s.replace(dec, ".")
    elif "," in s:
        parts = s.split(",")
        # (천단위,천단위,소수) 패턴인지 체크
        if len(parts) >= 2 and (len(parts[-1]) in (2, 3)) and all(len(p) == 3 for p in parts[1:-1] if p.isdigit()):
            s = "".join(parts[:-1]) + "." + parts[-1]
        else:
            s = s.replace(",", "")
    # else: 점만 있거나 아무 구분자 없음 -> 그대로

    try:
        val = float(s)
        if neg:
            val = -val
        return val
    except Exception:
        return pd.NA

def read_html_tables(html_path: Path) -> list[pd.DataFrame]:
    """pandas.read_html로 테이블 읽기. lxml 실패 시 bs4로 폴백."""
    html_file = str(html_path)
    try:
        dfs = pd.read_html(html_file, flavor="lxml", displayed_only=True)
        if dfs:
            return dfs
    except Exception:
        pass
    try:
        dfs = pd.read_html(html_file, flavor="bs4", displayed_only=True)
        return dfs
    except Exception:
        return []

def clean_and_standardize(df: pd.DataFrame) -> pd.DataFrame:
    # 헤더 표준화
    df.columns = [normalize_header(str(c)) for c in df.columns]

    # 관심 열이 없으면 생성
    for need in ["Description", "Quantity", "UoM", "UnitPrice", "Amount", "HSCode"]:
        if need not in df.columns:
            df[need] = pd.NA

    slim = df[["Description", "Quantity", "UoM", "UnitPrice", "Amount", "HSCode"]].copy()

    # 헤더 반복/노이즈 행 제거: Description이 "Description/품명/설명/내역" 같은 행 제거
    slim = slim[~slim["Description"].astype(str).str.fullmatch(r"(?i)description|품명|설명|내역")]

    # 숫자 정제
    for col in NUM_COLS:
        slim[col] = slim[col].map(to_number)

    # UoM 표준화
    slim["UoM"] = slim["UoM"].map(lambda x: UOM_MAP.get(str(x).strip().lower(), x) if pd.notna(x) else x)

    # 빈 행 제거(모든 값이 결측)
    slim = slim.dropna(how="all")
    return slim

def merge_wrapped_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """수치/HSCode 없고 설명만 있는 행을 앞행에 이어붙임."""
    if df.empty:
        return df
    rows = []
    for _, r in df.iterrows():
        only_desc = pd.notna(r.get("Description")) and all(pd.isna(r.get(c)) for c in ["Quantity", "UnitPrice", "Amount", "HSCode"])
        if only_desc and rows:
            prev = rows[-1]
            prev["Description"] = (str(prev.get("Description") or "").rstrip() + " " + str(r["Description"]).strip()).strip()
        else:
            rows.append({k: r.get(k, pd.NA) for k in df.columns})
    return pd.DataFrame(rows, columns=df.columns)

def run_docling_convert(pdf: Path, out_dir: Path, split_pages: bool = True, extra: list[str] | None = None) -> bool:
    """Docling CLI 호출. 실패 시 False."""
    if shutil.which("docling") is None:
        print("❌ Docling CLI를 찾을 수 없습니다. 'pip install docling' 후 PATH를 확인하세요.")
        return False
    to_fmt = "html_split_page" if split_pages else "html"
    cmd = ["docling", "--to", to_fmt, "--tables", "--output", str(out_dir), str(pdf)]
    # table 구조 정밀도 우선 (옵션 존재 시)
    cmd += ["--table-mode", "accurate"]
    if extra:
        cmd += extra
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ Docling 변환 실패: {pdf.name} -> {e}")
        return False

def main():
    ap = argparse.ArgumentParser(description="Invoice PDF → HTML(docling) → DataFrame 병합 → Excel/CSV 저장 (Pure Windows)")
    ap.add_argument("--input", "-i", required=True, help="PDF 파일 경로 또는 폴더")
    ap.add_argument("--outdir", "-o", default="out_html", help="Docling HTML 출력 폴더 (기본: out_html)")
    ap.add_argument("--split-pages", action="store_true", help="페이지 단위 HTML 생성 (권장)")
    ap.add_argument("--excel", default="invoice_lines_merged.xlsx", help="엑셀 출력 파일명")
    ap.add_argument("--csv", default="invoice_lines_merged.csv", help="CSV 출력 파일명")
    ap.add_argument("--skip-convert", action="store_true", help="Docling 변환 스킵(기존 HTML만 파싱)")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_html_dir = Path(args.outdir)
    out_html_dir.mkdir(parents=True, exist_ok=True)

    # 1) PDF → HTML (docling)
    pdf_list = []
    if in_path.is_file() and in_path.suffix.lower() == ".pdf":
        pdf_list = [in_path]
    elif in_path.is_dir():
        pdf_list = [Path(p) for p in glob.glob(str(in_path / "**/*.pdf"), recursive=True)]
    else:
        print("❌ 입력 경로가 잘못되었거나 PDF가 아닙니다.")
        sys.exit(2)

    if not args.skip_convert:
        for pdf in pdf_list:
            ok = run_docling_convert(pdf, out_html_dir, split_pages=args.split_pages)
            if not ok:
                # 실패해도 다음 파일 진행
                continue

    # 2) HTML 수집
    html_files = [Path(p) for p in glob.glob(str(out_html_dir / "**/*.html"), recursive=True)]
    if not html_files:
        print("❌ HTML이 없습니다. --skip-convert 를 제거하고 다시 실행하거나 출력 폴더를 확인하세요.")
        sys.exit(3)

    # 3) HTML → DF 파싱 & 정규화
    tables = []
    for html in html_files:
        dfs = read_html_tables(html)
        if not dfs:
            continue
        for df in dfs:
            slim = clean_and_standardize(df)
            slim = merge_wrapped_descriptions(slim)
            # 소스 추적 컬럼
            slim.insert(0, "SourceHTML", str(html))
            # PDF 추정(부모 폴더 또는 파일명 기원)
            # docling은 일반적으로 원본 stem을 유지하므로 상위폴더/파일명으로 유추
            # 가장 가까운 .pdf 파일명 추정 (없을 수 있음)
            pdf_guess = None
            # 같은 이름의 pdf를 입력 리스트에서 찾기
            stem = re.sub(r"_page[_\-]?\d+$", "", Path(html).stem, flags=re.I)
            for pdf in pdf_list:
                if pdf.stem.lower() == stem.lower() or pdf.stem.lower() in Path(html).stem.lower():
                    pdf_guess = str(pdf)
                    break
            slim.insert(0, "SourcePDF", pdf_guess or pd.NA)
            # 페이지 번호 추출
            page_no = parse_page_from_filename(html)
            slim.insert(2, "Page", page_no)
            tables.append(slim)

    if not tables:
        print("❌ HTML에서 테이블을 찾지 못했습니다.")
        sys.exit(4)

    merged = pd.concat(tables, ignore_index=True)

    # 4) 기본 후처리: 동일 행 병합(옵션) - 설명+UoM 동일 시 수량/금액 합산
    grouped = (merged
               .groupby(["SourcePDF", "SourceHTML", "Page", "Description", "UoM"], dropna=False, as_index=False)
               .agg(Quantity=("Quantity", "sum"),
                    UnitPrice=("UnitPrice", "first"),
                    Amount=("Amount", "sum"),
                    HSCode=("HSCode", "first")))

    # 5) 파생/검증 컬럼
    grouped["CalcAmount"] = (grouped["UnitPrice"] * grouped["Quantity"]).round(2)
    grouped["Delta"] = (grouped["Amount"] - grouped["CalcAmount"]).abs()
    grouped["DeltaFlag"] = grouped["Delta"] > DELTA_THRESHOLD

    # 6) 요약 시트용 집계
    summary = (grouped
               .groupby(["SourcePDF"], dropna=False, as_index=False)
               .agg(lines=("Description", "count"),
                    qty=("Quantity", "sum"),
                    amount=("Amount", "sum"),
                    mismatches=("DeltaFlag", "sum")))

    # 7) 저장 (CSV + Excel with conditional formatting)
    grouped.to_csv(args.csv, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(args.excel, engine="xlsxwriter") as writer:
        grouped[CANON_COLS + ["CalcAmount", "Delta", "DeltaFlag"]].to_excel(writer, sheet_name="Lines", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)

        wb = writer.book
        ws = writer.sheets["Lines"]
        # Delta > 임계치 빨간 음영
        # Delta 열 위치 찾기
        header_cols = list(grouped[CANON_COLS + ["CalcAmount", "Delta", "DeltaFlag"]].columns)
        delta_idx = header_cols.index("Delta")  # 0-based
        nrows = len(grouped) + 1  # header 포함
        ncols = len(header_cols)
        red_fmt = wb.add_format({"bg_color": "#FFC7CE"})
        ws.conditional_format(1, delta_idx, nrows - 1, delta_idx,
                              {"type": "cell", "criteria": ">", "value": DELTA_THRESHOLD, "format": red_fmt})

        # DeltaFlag == TRUE 음영
        flag_idx = header_cols.index("DeltaFlag")
        ws.conditional_format(1, flag_idx, nrows - 1, flag_idx,
                              {"type": "cell", "criteria": "==", "value": True, "format": red_fmt})

    print(f"✅ 병합 완료. 라인 수: {len(grouped)}  |  불일치 라인 수: {int(grouped['DeltaFlag'].sum())}")
    print(f"→ CSV: {args.csv}")
    print(f"→ Excel: {args.excel}")


if __name__ == "__main__":
    main()
```

### 어떻게 실행하나요?

```powershell
# 예시 1) 폴더 내 모든 PDF 변환+파싱(페이지 분할 HTML 권장)
python invoice_extract_win.py --input "C:\pdf" --split-pages

# 예시 2) 단일 파일, 기존 HTML 재활용(이미 out_html에 생성되어 있다면)
python invoice_extract_win.py --input "C:\pdf\invoiceA.pdf" --skip-convert

# 출력 위치 바꾸기
python invoice_extract_win.py --input "C:\pdf" --outdir "C:\work\html" --excel "C:\work\result.xlsx"
```

---

## 왜 이렇게 바꿨나요? (디자인 근거)

* **Docling CLI 옵션 정합성**
  Docling은 CLI에서 `--to`로 출력 형식(`html`, `html_split_page`, `md`, `json`, `text`, `doctags`)을 지정하며, `--output`으로 저장 폴더를 정합니다. `--tables`, `--table-mode` 같은 테이블 추출 옵션도 제공합니다. `--layout=stream`은 Docling 옵션이 아닙니다.  ([docling-project.github.io][1])

* **HTML → DataFrame 안정화**
  `pandas.read_html`는 내부적으로 lxml/bs4 파서를 사용하며, `displayed_only` 등 파라미터 동작이 버전별로 문서화되어 있습니다. 본 스크립트는 lxml → bs4 폴백 순서로 시도하여 폭넓은 HTML을 안전하게 수집합니다.  ([pandas.pydata.org][2])

* **숫자 파싱의 지역화/회계 포맷**
  국가별 천단위/소수점 차이(예: `1.234,56` vs `1,234.56`)와 **괄호 음수** 표기(`(1,234.56)` → `-1234.56`)를 처리하는 후처리 로직을 포함했습니다. 이는 `read_html`의 `thousands/decimal`만으로는 개별 셀의 다양한 조합을 100% 해결하기 어려워, 보정 계층을 두었습니다.  ([pandas.pydata.org][2])

* **Excel 조건부 서식**
  `XlsxWriter`의 조건부 서식 예제를 기반으로 `Delta` 초과 셀을 빨간색으로 표시합니다. 검토가 쉬워집니다.  ([xlsxwriter.readthedocs.io][3])

---

## 추가 팁

* 멀티컬럼 인보이스에서 열이 좌/우로 나뉘는 경우, **`--split-pages`**로 페이지 단위 HTML을 생성하면 페이지별 테이블 순서가 보존되어 열 재구성이 쉬워집니다. (Docling은 `html_split_page`를 공식 지원)  ([docling-project.github.io][4])
* OCR 언어가 한국어/영어 혼용인 스캔본이라면 필요 시 Docling CLI에 `--ocr-lang ko,eng`를 추가해보세요(엔진에 따라 지원 언어 이름이 다를 수 있음).  ([docling-project.github.io][1])

---

원하시면 **조건부 서식 강화(예: 통화기호별 임계치/소수 자리 자동 적용)**, **벤더별 맞춤 헤더 매핑 프로파일**(예: `--vendor samsung` → 별도 사전 적용)도 바로 확장해 드릴게요.

[1]: https://docling-project.github.io/docling/reference/cli/ "CLI reference - Docling"
[2]: https://pandas.pydata.org/docs/reference/api/pandas.read_html.html?utm_source=chatgpt.com "pandas.read_html — pandas 2.3.3 documentation - PyData |"
[3]: https://xlsxwriter.readthedocs.io/example_pandas_conditional.html?utm_source=chatgpt.com "Example: Pandas Excel output with conditional formatting"
[4]: https://docling-project.github.io/docling/reference/cli/?utm_source=chatgpt.com "CLI reference - Docling - GitHub Pages"
