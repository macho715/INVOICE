from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import re
import logging
import os
import json
import unicodedata
from functools import lru_cache
from pathlib import Path
import sys
from decimal import Decimal, InvalidOperation
from typing import Sequence

# HeaderCore 통합 (표준 경로)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "shared" / "scripts"))
    from ofco_header_core import get_header_core
    HEADER_CORE_AVAILABLE = True
except ImportError:
    HEADER_CORE_AVAILABLE = False
    print("[WARNING] HeaderCore를 사용할 수 없습니다. 기본 컬럼 순서를 사용합니다.")

logger = logging.getLogger(__name__)
# logger.addHandler(logging.NullHandler())  # 디버깅을 위해 임시 비활성화
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
# 항목 시작: 1~46만 허용(+선행 0 금지), Tar. Code(예: 10.1/13/9.4) 보존,
# 그리고 바로 다음 토큰이 영문/기호로 시작해야 본문으로 간주(괄호/슬래시/하이픈 허용)
# 개선: 항목 번호와 텍스트가 붙어있는 경우(예: "18Agency")도 인식
ITEM_START_RE = re.compile(
    r"^\s*(?P<sn>(?:[1-9]|[1-3]\d|4[0-6]))"  # 1~46
    r"(?:\s+(?P<tar>\d{1,2}(?:\.\d{1,2})?))?"  # Tar. Code(옵션)
    r"(?=\s+[A-Za-z(\-\/]|[A-Za-z(\-\/])"  # 뒤 토큰 영문/기호 시작 (붙어있거나 공백)
)
# 항목 번호만으로 시작하는 경우 (예: "18Agency", "26OFCO") - 붙어있는 케이스 처리
ITEM_START_COMPACT_RE = re.compile(
    r"^\s*(?P<sn>(?:[1-9]|[1-3]\d|4[0-6]))(?P<text>[A-Za-z][A-Za-z0-9\s\-\:\(\)\/]*)"  # 18Agency, 26OFCO 등
)
import json
import argparse
import csv
from typing import cast

# === PyMuPDF SAFEEN/ADP Extractor (robust) ====================================

try:
    import fitz  # type: ignore[import]  # PyMuPDF
except Exception:
    fitz = None

_CANON = {
    "sn": "sn",
    "s no": "sn",
    "s/n": "sn",
    "s. no": "sn",
    "sno": "sn",
    "no": "sn",
    "tar code": "tariff_code",
    "tar. code": "tariff_code",
    "tariff": "tariff_code",
    "tariff code": "tariff_code",
    "tariff id": "tariff_code",
    "tariff description": "description",
    "description": "description",
    "tariff description": "description",
    "desc": "description",
    "amount": "amount_excl_vat",
    "amount excl. vat": "amount_excl_vat",
    "amount excl": "amount_excl_vat",
    "amount excl tax": "amount_excl_vat",
    "amount exel tax aed": "amount_excl_vat",
    "amount exel tax (aed)": "amount_excl_vat",
    "amount (aed)": "amount_excl_vat",
    "amount excl tax (aed)": "amount_excl_vat",
    "vat %": "vat_rate",
    "vat%": "vat_rate",
    "vat percent": "vat_rate",
    "tax %": "vat_rate",
    "tax percent": "vat_rate",
    "tax rate": "vat_rate",
    "vat amount": "vat_amount",
    "vat amt": "vat_amount",
    "tax amount": "vat_amount",
    "tax type amount aed": "vat_amount",
    "tax type amount (aed)": "vat_amount",
    "total": "amount_incl_vat",
    "total (inc. vat)": "amount_incl_vat",
    "total incl. vat": "amount_incl_vat",
    "total inc vat": "amount_incl_vat",
    "amount incl. vat": "amount_incl_vat",
    "total amount incl tax aed": "amount_incl_vat",
    "total amount incl tax (aed)": "amount_incl_vat",
}

_NUM_COLS: Set[str] = {
    "amount",
    "amount_excl_vat",
    "amount_incl_vat",
    "vat_amount",
    "tax_amount",
    "vat_rate",
    "tax_rate",
}

_FOOTER_RE = re.compile(r"(invoice\s+total|amount\s+in\s+words)", re.I)
_THIN_SPACES = "\u00A0\u202F\u2007"


def _should_use_pymupdf() -> bool:
    return os.getenv("OFCO_USE_PYMUPDF_EXTRACTOR", "true").lower() not in {"0", "false", "no"}


def _ntext(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    return re.sub(r"\s+", " ", text)


def _nkey(value: object) -> str:
    key = _ntext(value).lower()
    key = re.sub(r"[^a-z0-9% ]+", " ", key)
    return re.sub(r"\s+", " ", key).strip()


def _canon(name: str) -> str:
    return _CANON.get(_nkey(name), _nkey(name))


def parse_numeric(value: object) -> Optional[float]:
    if value is None:
        return None
    s = unicodedata.normalize("NFKC", str(value))
    s = re.sub(rf"[^\d,\.\-+ {_THIN_SPACES}·•]", "", s)
    for sp in _THIN_SPACES:
        s = s.replace(sp, " ")
    s = re.sub(r"(\d)[ ·•](\d{2})\b", r"\1.\2", s)
    if "." not in s and re.search(r",\d{1,2}\b", s):
        i = s.rfind(",")
        s = s[:i] + "." + s[i + 1 :]
    s = re.sub(r"(?<=\d),(?=\d{3}(?:,\d{3})*\b)", "", s)
    s = re.sub(r"(?<=\d) (?=\d{3}(?: \d{3})*\b)", "", s)
    s = s.replace(" ", "")
    if s.count(".") > 1:
        first = s.find(".")
        s = s[: first + 1] + s[first + 1 :].replace(".", "")
    s = re.sub(r"[^\d.\-+]", "", s)
    if not s or s in {"+", "-", ".", "+.", "-."}:
        return None
    try:
        return float(Decimal(s))
    except (InvalidOperation, ValueError):
        return None


def _norm_vat_rate(val: Optional[float]) -> Optional[float]:
    if val is None:
        return None
    return val / 100.0 if val > 1.0 else val


def _is_footer_row(cells: Sequence[str]) -> bool:
    return bool(_FOOTER_RE.search(" ".join(_ntext(c) for c in cells)))


def _score_header_row(row: Sequence[str]) -> int:
    return sum(1 for cell in row if _canon(cell) in _CANON.values())


def _pick_header(matrix: List[List[str]]) -> Tuple[List[str], int]:
    best_idx, best_score, best_names = 0, -1, matrix[0]
    for idx in range(min(3, len(matrix))):
        raw = [_ntext(c) for c in matrix[idx]]
        score = _score_header_row(raw)
        if score > best_score:
            best_score = score
            best_idx = idx
            best_names = raw
    return ([_canon(n) for n in best_names], best_idx)


def _table_to_rows(table) -> List[Dict[str, object]]:
    matrix = table.extract() or []
    if not matrix:
        return []
    if getattr(table, "header", None) and getattr(table.header, "names", None):
        header = [_canon(n) for n in table.header.names]
        body = matrix[1:]
    else:
        header, idx = _pick_header(matrix)
        body = matrix[idx + 1 :] if len(matrix) > idx + 1 else []

    if "description" not in header and len(header) >= 3:
        fallback = [
            "sn",
            "tariff_code",
            "description",
            "amount_excl_vat",
            "vat_rate",
            "vat_amount",
            "amount_incl_vat",
        ]
        header = fallback[: len(header)]

    rows: List[Dict[str, object]] = []
    for raw in body:
        cells = [_ntext(c) for c in raw]
        if not any(cells) or _is_footer_row(cells):
            continue
        rec: Dict[str, object] = {h: "" for h in header}
        for i, h in enumerate(header):
            if i < len(cells):
                rec[h] = cells[i]
        for key in _NUM_COLS.intersection(rec.keys()):
            rec[key] = parse_numeric(rec[key])
        if "amount_incl_vat" not in rec and "total" in rec:
            rec["amount_incl_vat"] = parse_numeric(rec["total"])
        if "vat_rate" in rec:
            rec["vat_rate"] = _norm_vat_rate(parse_numeric(rec["vat_rate"]))
        _harmonize_amounts(rec)
        rows.append(rec)
    return rows


def _harmonize_amounts(row: Dict[str, object]) -> None:
    amount = row.get("amount_excl_vat")
    total = row.get("amount_incl_vat")
    vat_amount = row.get("vat_amount")

    if isinstance(amount, (int, float)) and isinstance(total, (int, float)):
        if amount and total and amount >= 1000 and total < 500:
            scaled = amount / 100.0
            if abs(scaled - (total or 0.0)) <= max(5.0, 0.05 * (total or 1.0)):
                row["amount_excl_vat"] = scaled
                amount = scaled
    if (
        isinstance(amount, (int, float))
        and isinstance(vat_amount, (int, float))
        and amount >= 1000
        and vat_amount < amount * 0.2
        and vat_amount >= 10
    ):
        scaled_vat = vat_amount / 100.0
        if amount >= 10 and scaled_vat <= amount * 0.2:
            row["vat_amount"] = scaled_vat


def _looks_like_line_table(matrix: List[List[str]]) -> bool:
    if not matrix:
        return False
    first_row = [_ntext(c) for c in matrix[0]]
    if len(first_row) < 4:
        return False
    first_cell = first_row[0]
    third_cell = first_row[2] if len(first_row) > 2 else ""
    return bool(re.fullmatch(r"\d+", first_cell or "")) and any(ch.isalpha() for ch in third_cell)


def _find_roi(page) -> Optional["fitz.Rect"]:
    if fitz is None:
        return None
    tops = page.search_for("S No") or page.search_for("S/N") or page.search_for("S. No")
    bots = page.search_for("Invoice Total") or page.search_for("Amount in Words")
    if not tops:
        return None
    top_y = min(r.y0 for r in tops) - 4
    bot_y = max((r.y1 for r in bots), default=page.rect.y1 - max(8, page.rect.height * 0.03))
    return fitz.Rect(page.rect.x0 + 4, top_y, page.rect.x1 - 4, bot_y)


def _extract_tables_on_page(page, clip: Optional["fitz.Rect"]):
    try:
        finder = page.find_tables(clip=clip)
    except Exception:
        return []
    return list(getattr(finder, "tables", []) or [])


def _validate_rows(rows: List[Dict[str, object]]) -> Tuple[bool, float, float]:
    if not rows:
        return (False, 0.0, 0.0)
    ok_checks = 0
    total_incl = 0.0
    for rec in rows:
        amt = float(rec.get("amount_excl_vat") or 0.0)
        inc = float(rec.get("amount_incl_vat") or 0.0)
        vat = float(rec.get("vat_amount") or 0.0)
        rate = rec.get("vat_rate")
        checks = []
        if amt and inc:
            checks.append(abs(amt - inc) <= max(1.0, 0.01 * max(inc, amt)))
        if amt and inc and rate is not None:
            checks.append(abs(amt * (1.0 + rate) - inc) <= max(1.0, 0.02 * max(inc, amt)))
        if amt and vat and rate is not None:
            checks.append(abs(amt * rate - vat) <= max(1.0, 0.02 * max(vat, amt)))
        if checks and any(checks):
            ok_checks += 1
        elif not checks and inc > 0:
            ok_checks += 1
        total_incl += inc or amt
    confidence = ok_checks / max(1, len(rows))
    return (confidence >= 0.4 and total_incl > 0.0, confidence, total_incl)


def _extract_invoice_items_pymupdf_impl(
    pdf_path: str, *, clip_rect: Optional[Tuple[float, float, float, float]] = None
) -> List[Dict[str, object]]:
    if fitz is None:
        return []

    clip = fitz.Rect(*clip_rect) if clip_rect else None
    raw_rows: List[Dict[str, object]] = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            roi = clip or _find_roi(page)
            page_rows: List[Dict[str, object]] = []
            tables = _extract_tables_on_page(page, roi)
            if tables:
                best, best_score, best_matrix = None, -1, None
                for table in tables:
                    matrix = table.extract() or []
                    if not matrix:
                        continue
                    score = _score_header_row(matrix[0])
                    if score > best_score:
                        best, best_score, best_matrix = table, score, matrix
                if best is not None and (best_score > 0 or _looks_like_line_table(best_matrix or [])):
                    page_rows.extend(_table_to_rows(best))
            if not page_rows:
                # optional lightweight words fallback (skipped to avoid noise)
                pass
            raw_rows.extend(page_rows)

    deduped: List[Dict[str, object]] = []
    seen = set()
    for row in raw_rows:
        key = (
            _ntext(row.get("description")),
            row.get("tariff_code") or row.get("tar_code"),
            row.get("amount_incl_vat") or row.get("amount") or 0.0,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    legacy_rows: List[Dict[str, object]] = []
    for row in deduped:
        amount = row.get("amount_excl_vat")
        inc = row.get("amount_incl_vat")
        legacy_rows.append(
            {
                "sn": row.get("sn"),
                "tariff_code": row.get("tariff_code") or row.get("tar_code"),
                "description": row.get("description"),
                "amount_excl_vat": amount if amount is not None else inc,
                "tax_rate": row.get("vat_rate"),
                "tax_amount": row.get("vat_amount"),
                "amount_incl_vat": inc,
            }
        )
    return legacy_rows


def extract_invoice_items_pymupdf(pdf_path: str) -> List[Dict[str, object]]:
    return _extract_invoice_items_pymupdf_impl(pdf_path)


# ---------- Config ----------
REL_TOL = 0.02
ABS_EPS = 0.01
DEFAULT_CURRENCY = "AED"
MAX_LINES_WITHOUT_AMOUNT = 3  # 3줄 이상 금액 매칭 실패 시 강제 완료

# ============================================================
# Hotfix: 금액 끝 봉인 + 붙은 항목번호(1–2자리)만 안전 분리
# - 금액 소수부 2~4자리 허용
# - 금액 바로 뒤엔 숫자가 오면 안 됨(?!\d)로 봉인 → 내부 분할 방지
# - 다음 토큰이 진짜 항목번호라는 힌트로 [A-Za-z] 시작 요구(문맥 힌트)
# ============================================================
# 예: "159,550.0730Agency"  → (분할 금지)
#     "1,234.56 30Agency"  → "1,234.56\n30Agency" (공백/붙임 모두 허용)
# ============================================================
AMOUNT_PATTERN = r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d+)\.(?:\d{2,4})(?!\d)"

# 금액-텍스트 분리 패턴 집합 (우선순위 순)
SPLIT_PATTERNS = [
    # Pattern 1: 금액 뒤 영문 단어 + 콜론 (Name:, Address:, etc.)
    re.compile(rf"({AMOUNT_PATTERN})(?=[A-Z][a-z]+\s*:)", re.I),
    # Pattern 2: 금액 뒤 숫자+영문 단어 (159,550.0730Agency)
    re.compile(rf"({AMOUNT_PATTERN})(\d{{1,2}}[A-Z][a-z]+)", re.I),
    # Pattern 3: 금액 뒤 1-2자리 숫자 + 영문 (기존 패턴)
    re.compile(rf"({AMOUNT_PATTERN})(?=(?:\s|\u00A0)?([1-9]\d?)(?=[A-Za-z]))"),
]

# 하위 호환성을 위한 단일 패턴 (deprecated)
SPLIT_ITEM_AFTER_TOTAL = SPLIT_PATTERNS[2]  # 기존 패턴

# ------- Noise / Page-marker 필터 --------
NOISE_PATS = [
    re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.I),  # Page 1 of 2
    re.compile(r"^\s*\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*$", re.I),  # 2025 15:30:00
    re.compile(r"^\s*\d{1,2}:\d{2}\s*(AM|PM)?\s*$", re.I),  # 50 minutes / 12:30 PM 류
    re.compile(r"^\s*(Amount in Words|Bank Details|Payment Terms)\b", re.I),
    re.compile(
        r"^\s*(Crew List|Supervisor|Headcount)\b", re.I
    ),  # Crew List/Supervisor 추가
    re.compile(r"^\s*Payment\s+(is\s+)?Due\s+on\b", re.I),  # Payment is Due on...
    re.compile(r"^\s*Total\s+(Tax|Amount)\s*\(AED\)", re.I),  # Total Tax (AED)
    re.compile(r"^\s*Grand\s+Total\b", re.I),  # Grand Total
    re.compile(r"^\s*Invoice\s+Total\b", re.I),  # Invoice Total
    re.compile(r"^\s*Note:\s*", re.I),  # Note:
    re.compile(r"^\s*PORTS\s+AD\s+Ports\s+Group\b", re.I),  # Company footer
    re.compile(r"^\s*Po\s+Box\s+\d+", re.I),  # PO Box address
    re.compile(r"^\s*TAX\s+Type/", re.I),  # TAX Type/ Amount
    re.compile(r"^\s*Payment\s+can\s+be\s+made\s+by\b", re.I),  # Payment instructions
    re.compile(r"adports\.com\b", re.I),  # Website URLs
    re.compile(r"Tel:\s*\+", re.I),  # Phone numbers
    # 메타데이터 필터 강화 (Line 54-62, 68-70)
    re.compile(r"^\s*Name\s*:\s*Samsung", re.I),  # Line 54
    re.compile(r"^Name\s*:\s*Samsung", re.I),  # Without leading spaces
    re.compile(r"^\s*OFFSHORE INTERNATIONAL\b", re.I),  # Company name 노이즈
    re.compile(r"^\s*Company Name\s*:", re.I),  # Company Name: 노이즈
    re.compile(r"^\s*USD\s*-\s*[A-Z\s]+Dollars?$", re.I),  # Amount in words (USD)
    re.compile(r"^\s*Bank Name\s*:", re.I),  # Bank Name 노이즈
    re.compile(r"^\s*Address\s*:\s*Office", re.I),  # Line 55
    re.compile(r"^\s*Attn\s*\.?\s*:", re.I),  # Line 57
    re.compile(r"^\s*TRN\s*:\s*\d+", re.I),  # Line 58
    re.compile(r"^\s*Invoice number\s*$", re.I),  # Line 58
    re.compile(r"^\s*Date\s*:\s*\d+", re.I),  # Line 59
    re.compile(r"^\s*Proj\.Ref", re.I),  # Line 60
    re.compile(r"^\s*P\.O\./Ref", re.I),  # Line 61
    re.compile(r"^\s*Invoice Currency", re.I),  # Line 62
    re.compile(r"^\s*Vessel Name", re.I),  # Line 62
    re.compile(r"^\s*For VAT Purpose", re.I),  # Line 68
    re.compile(r"^\s*Amount \(excl\. VAT\)\s+Exch", re.I),  # Line 69
    re.compile(r"^\s*\d{3},\d{3}\.\d{2}\s+\d\.\d{4}\s+", re.I),  # Line 70 환율표
    re.compile(
        r"^\s*\d{3},\d{3}\.\d{2}\s+\d\.\d{4}\s+\d{3},\d{3}\.\d{2}", re.I
    ),  # 환율표 전체
]


def is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    return any(p.search(s) for p in NOISE_PATS)


# ---------------- Section detection & mode ----------------
# 모드: 'ofco_direct' = Tar. Code 테이블만, 'all' = 모든 섹션, 'custom' = 사용자 선택 섹션
PARSE_MODE = "all"  # 'all' / 'ofco_direct' / 'custom'
ALLOWED_SECTIONS = {"OFCO_DIRECT"}  # PARSE_MODE='custom'일 때 사용

SECTION_RULES = [
    # (섹션명, 매칭 조건)
    (
        "OFCO_DIRECT",
        re.compile(
            r"Tar\.?\s*Code\s+Description\s+Tax\s*Rate\s+Qty\s+Unit\s+Price\s+Unit\s+Amount\s+excl",
            re.I,
        ),
    ),
    ("SAFEEN", re.compile(r"\bSAFEEN\b|\bSAFEEN\s+INV-\d+", re.I)),
    ("AD_PORT", re.compile(r"\bAD\s*PORTS?\b|\bAD\s*PORTS\s+GROUP\b", re.I)),
    ("AGENCY", re.compile(r"\bAgency\s+fee\b", re.I)),
]


def decide_section(line: str, cur: Optional[str]) -> Optional[str]:
    """헤더/키워드로 섹션 전환. 매칭 없으면 기존 섹션 유지."""
    for name, pat in SECTION_RULES:
        if pat.search(line):
            return name
    return cur


def section_allowed(name: Optional[str]) -> bool:
    if PARSE_MODE == "all":
        return True
    if PARSE_MODE == "ofco_direct":
        return name == "OFCO_DIRECT"
    if PARSE_MODE == "custom":
        return (name or "") in ALLOWED_SECTIONS
    return True


# ---------------- Tariff mapping (Tar. Code → default unit/account) -------------
# JSON 예시:
# {
#   "10.1": {"unit": "LS", "account": "BERTHING"},
#   "9.4":  {"unit": "LS", "account": "TUG"},
#   "8.1":  {"unit": "LS", "account": "PILOT LAUNCH"}
# }
TARIFF_MAP_PATH = os.environ.get("OFCO_TARIFF_MAP", "tariff_mapping_20251103.json")


def _norm_tar_code(code: str | None) -> str | None:
    if not code:
        return None
    s = str(code).strip()
    # "13" → "13", "10.10" → "10.1" 정규화(불필요한 0 제거)
    if "." in s:
        head, tail = s.split(".", 1)
        tail = tail.rstrip("0")
        s = head if tail == "" else f"{head}.{tail}"
    return s


@lru_cache(maxsize=1)
def load_tariff_map(path: str | None = None) -> dict:
    p = path or TARIFF_MAP_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 키 정규화
            norm = {}
            # Handle both dict and list formats
            items = (
                data
                if isinstance(data, list)
                else (data.items() if isinstance(data, dict) else [])
            )
            for item in items:
                if isinstance(item, dict) and "tariff_code" in item:
                    # List format: {"tariff_code": "10.1", "unit": "LS", ...}
                    k = item["tariff_code"]
                elif isinstance(item, tuple):
                    # Dict format: ("10.1", {"unit": "LS", ...})
                    k, item = item
                else:
                    continue
                nk = _norm_tar_code(k)
                if nk:
                    norm[nk] = {
                        "unit": (item.get("unit") or item.get("uom") or "").strip(),
                        "account": (
                            item.get("account")
                            or item.get("gl")
                            or item.get("category")
                            or ""
                        ).strip(),
                        "alias": (
                            item.get("alias")
                            or item.get("name")
                            or item.get("item_key")
                            or ""
                        ).strip(),
                    }
            return norm
    except FileNotFoundError:
        logger.warning("Tariff map file not found: %s", p)
        return {}
    except Exception as e:
        logger.exception("Failed to load tariff map: %s", e)
        return {}


def apply_tariff_defaults(row: dict) -> dict:
    """
    row에 tariff_code가 있으면 매핑에서 unit/account/alias를 주입.
    - unit: row에 없거나 빈 경우에만 보완(덮어쓰지 않음)
    - account: 항상 추가(빈 값이면 생략)
    - alias: description 보완은 하지 않되 Notes용 메타로 남김
    """
    code = _norm_tar_code(row.get("tariff_code"))
    if not code:
        return row
    m = load_tariff_map()
    meta = m.get(code)
    if not meta:
        return row
    # unit 보완
    unit_now = (row.get("unit") or "").strip()
    if not unit_now and meta.get("unit"):
        row["unit"] = meta["unit"]
    # account 메타
    if meta.get("account"):
        row["account"] = meta["account"]
    # alias는 주석/노트로만
    if meta.get("alias"):
        prev = row.get("_meta_notes", [])
        prev.append(f"alias={meta['alias']}")
        row["_meta_notes"] = prev
    return row


# ---------- Multiline Parser Constants ----------
NUMERIC_FIELD_ORDER = [
    "qty",  # 0: 수량
    "unit_price",  # 1: 단가
    "amount_excl_vat",  # 2: VAT 제외 금액
    "tax_amount",  # 3: 세금
    "amount_incl_vat",  # 4: VAT 포함 금액
]


class ParserState(Enum):
    SEARCHING_ITEM = "searching"  # 항목 번호 찾는 중
    READING_DESCRIPTION = "description"  # 설명 읽는 중
    READING_DATA = "data"  # 숫자 데이터 읽는 중
    COMPLETED = "completed"  # 항목 완료


# ---------- Mapping Rules (expanded) ----------
SUBJECT_CC_MAP = [
    # Original rules
    (
        re.compile(r"SAFEEN", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PORT HANDLING CHARGE",
            "COST CENTER B": "CHANNEL TRANSIT CHARGES",
            "PRICE CENTER": "CHANNEL TRANSIT CHARGES",
        },
    ),
    (
        re.compile(r"\bPHC\b", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PORT HANDLING CHARGE",
            "COST CENTER B": "PORT HANDLING CHARGES",
            "PRICE CENTER": "PORT HANDLING CHARGE",
        },
    ),
    (
        re.compile(r"ADP\s*INV.*Port\s*Dues", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PORT HANDLING CHARGE",
            "COST CENTER B": "PORT DUES & SERVICES CHARGES",
            "PRICE CENTER": "PORT DUES",
        },
    ),
    (
        re.compile(r"Cargo\s*Clearance", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "CONTRACT(AF FOR CC)",
            "COST CENTER B": "AF FOR CC",
            "PRICE CENTER": "AGENCY FEE FOR CARGO CLEARANCE",
        },
    ),
    (
        re.compile(r"(FW\s*Supply|Arranging\s*FW\s*Supply)", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "CONTRACT",
            "COST CENTER B": "AF FOR FW SA",
            "PRICE CENTER": "SUPPLY WATER 5000IG",
        },
    ),
    (
        re.compile(r"Berthing\s*Arrangement", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "CONTRACT(AF FOR BA)",
            "COST CENTER B": "CONTRACT",
            "PRICE CENTER": "AGENCY FEE FOR BERTHING ARRANGEMENT",
        },
    ),
    (
        re.compile(r"5000\s*IG\s*FW|Supply\s*of\s*5000\s*IG\s*FW", re.I),
        {
            "COST MAIN": "AT COST",
            "COST CENTER A": "AT COST",
            "COST CENTER B": "AT COST(WATER SUPPLY)",
            "PRICE CENTER": "SUPPLY WATER 5000IG",
        },
    ),
    (
        re.compile(r"Handling\s*Fee|Handling\s*Charge", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "CONTRACT",
            "COST CENTER B": "HANDLING FEE 10%",
            "PRICE CENTER": "HANDLING FEE",
        },
    ),
    (
        re.compile(r"Port\s*Charge|Port\s*Charges", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PORT HANDLING CHARGE",
            "COST CENTER B": "PORT CHARGES",
            "PRICE CENTER": "PORT CHARGES",
        },
    ),
    (
        re.compile(r"\bPTW\b|Permit\s*To\s*Work|Gate\s*Permit", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "CONTRACT",
            "COST CENTER B": "PTW APPLICATION",
            "PRICE CENTER": "PTW APPLICATION",
        },
    ),
    (
        re.compile(r"Man\s*power|Manpower|Supervisor|Foreman|Rigger", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "MANPOWER",
            "COST CENTER B": "LABOUR CHARGES",
            "PRICE CENTER": "MANPOWER",
        },
    ),
    (
        re.compile(r"Crane\s*(?:\d+\s*T)?", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "EQUIPMENT CHARGES",
            "COST CENTER B": "CRANE",
            "PRICE CENTER": "CRANE",
        },
    ),
    (
        re.compile(r"Fork\s*lift|Forklift", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "EQUIPMENT CHARGES",
            "COST CENTER B": "FORKLIFT",
            "PRICE CENTER": "FORKLIFT",
        },
    ),
    (
        re.compile(r"\bMGO\b|Fuel\s*Supply|Gas\s*Oil", re.I),
        {
            "COST MAIN": "AT COST",
            "COST CENTER A": "AT COST",
            "COST CENTER B": "FUEL (MGO)",
            "PRICE CENTER": "MGO FUEL",
        },
    ),
    (
        re.compile(r"Consumables?|Packing\s*Material", re.I),
        {
            "COST MAIN": "AT COST",
            "COST CENTER A": "AT COST",
            "COST CENTER B": "CONSUMABLES",
            "PRICE CENTER": "CONSUMABLES",
        },
    ),
    (
        re.compile(r"Gate\s*Pass", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "DOCUMENTATION",
            "COST CENTER B": "GATE PASS",
            "PRICE CENTER": "GATE PASS",
        },
    ),
    (
        re.compile(r"Yard\s*Storage|Port\s*Storage|Laydown\s*Storage", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "STORAGE",
            "COST CENTER B": "YARD STORAGE",
            "PRICE CENTER": "STORAGE",
        },
    ),
    (
        re.compile(r"Pilotage|Pilot\s*Launch", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PILOTAGE",
            "COST CENTER B": "PILOT LAUNCH",
            "PRICE CENTER": "PILOTAGE",
        },
    ),
    (
        re.compile(r"Waste", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "WASTE HANDLING",
            "COST CENTER B": "WASTE",
            "PRICE CENTER": "WASTE HANDLING",
        },
    ),
    # New rules based on tariffs and invoice
    (
        re.compile(r"Permits & certificate", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PERMITS",
            "COST CENTER B": "PERMITS & CERTIFICATES",
            "PRICE CENTER": "PERMITS & CERTIFICATES",
        },
    ),
    (
        re.compile(r"Pass Arrangement", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "DOCUMENTATION",
            "COST CENTER B": "PASS ARRANGEMENT",
            "PRICE CENTER": "PASS ARRANGEMENT",
        },
    ),
    (
        re.compile(r"Short Term Pass", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "DOCUMENTATION",
            "COST CENTER B": "SHORT TERM PASS",
            "PRICE CENTER": "SHORT TERM PASS",
        },
    ),
    (
        re.compile(r"Equipment Pass", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "DOCUMENTATION",
            "COST CENTER B": "EQUIPMENT PASS",
            "PRICE CENTER": "EQUIPMENT PASS",
        },
    ),
    (
        re.compile(r"Deck maintenance", re.I),
        {
            "COST MAIN": "AT COST",
            "COST CENTER A": "AT COST",
            "COST CENTER B": "DECK MAINTENANCE",
            "PRICE CENTER": "DECK MAINTENANCE",
        },
    ),
    (
        re.compile(r"Tug Assistance", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "TUG",
            "COST CENTER B": "TUG ASSISTANCE",
            "PRICE CENTER": "TUG ASSISTANCE",
        },
    ),
    (
        re.compile(r"BAF Surcharges", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "SURCHARGE",
            "COST CENTER B": "BAF",
            "PRICE CENTER": "BAF SURCHARGE",
        },
    ),
    (
        re.compile(r"Fresh Water Delivery|Fresh Water Tugs", re.I),
        {
            "COST MAIN": "AT COST",
            "COST CENTER A": "AT COST",
            "COST CENTER B": "FRESH WATER",
            "PRICE CENTER": "FRESH WATER DELIVERY",
        },
    ),
    (
        re.compile(r"Administration Fees", re.I),
        {
            "COST MAIN": "CONTRACT",
            "COST CENTER A": "ADMIN",
            "COST CENTER B": "ADMIN FEES",
            "PRICE CENTER": "ADMINISTRATION FEES",
        },
    ),
    (
        re.compile(r"Stevedoring", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "STEVEDORING",
            "COST CENTER B": "STEVEDORING CHARGES",
            "PRICE CENTER": "STEVEDORING",
        },
    ),
    (
        re.compile(r"Trucking", re.I),
        {
            "COST MAIN": "LOGISTICS",
            "COST CENTER A": "TRUCKING",
            "COST CENTER B": "TRUCKING CHARGES",
            "PRICE CENTER": "TRUCKING",
        },
    ),
    (
        re.compile(r"Demurrage|Detention", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "DEMURRAGE",
            "COST CENTER B": "DEMURRAGE CHARGES",
            "PRICE CENTER": "DEMURRAGE",
        },
    ),
    (
        re.compile(r"Heavy Lift|Awkward Lifts", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "HEAVY LIFT",
            "COST CENTER B": "HEAVY LIFT CHARGES",
            "PRICE CENTER": "HEAVY LIFT",
        },
    ),
    (
        re.compile(r"Daily Working Overwater|Daily Hot Work", re.I),
        {
            "COST MAIN": "PORT HANDLING",
            "COST CENTER A": "PERMITS",
            "COST CENTER B": "DAILY WORK PERMIT",
            "PRICE CENTER": "DAILY WORK PERMIT",
        },
    ),
]

PRICE_CENTER_HEURISTICS = [
    (re.compile(r"Pilotage", re.I), "PILOTAGE"),
    (re.compile(r"Pilot\s*Launch", re.I), "PILOT LAUNCH"),
    (re.compile(r"Berthing|Unberthing|Shifting", re.I), "BERTHING/SHIFTING"),
    (re.compile(r"Crane|(\d{2,3})\s*T", re.I), "CRANE"),
    (re.compile(r"Fork\s*lift|Forklift", re.I), "FORKLIFT"),
    (re.compile(r"Gate\s*Pass", re.I), "GATE PASS"),
    (re.compile(r"Waste", re.I), "WASTE HANDLING"),
    (re.compile(r"PTW", re.I), "PTW APPLICATION"),
    (re.compile(r"Storage", re.I), "STORAGE"),
    (re.compile(r"MGO|Fuel", re.I), "MGO FUEL"),
    # New
    (re.compile(r"Tug", re.I), "TUG ASSISTANCE"),
    (re.compile(r"BAF", re.I), "BAF SURCHARGE"),
    (re.compile(r"Fresh Water", re.I), "FRESH WATER DELIVERY"),
    (re.compile(r"Stevedoring", re.I), "STEVEDORING"),
    (re.compile(r"Trucking", re.I), "TRUCKING"),
    (re.compile(r"Demurrage", re.I), "DEMURRAGE"),
    (re.compile(r"Heavy Lift", re.I), "HEAVY LIFT"),
]


@dataclass
class InvoiceMeta:
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    customer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    samsung_ref: Optional[str] = None
    vat_percent: Optional[float] = None
    currency: str = DEFAULT_CURRENCY
    total_excl_vat: Optional[float] = None
    total_vat: Optional[float] = None
    total_incl_vat: Optional[float] = None
    alt_currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    alt_excl_vat: Optional[float] = None
    alt_vat: Optional[float] = None
    alt_incl_vat: Optional[float] = None
    vessel_name: Optional[str] = None
    rotation_no: Optional[str] = None
    voyage_no: Optional[str] = None
    grt: Optional[str] = None
    dwt: Optional[str] = None
    loa: Optional[str] = None
    customer_reg_no: Optional[str] = None


@dataclass
class LineItem:
    subject: str
    ea_rates: List[Tuple[float, float]]
    amount: Optional[float] = None
    notes: Optional[str] = None
    cost_main: Optional[str] = None
    cost_center_a: Optional[str] = None
    cost_center_b: Optional[str] = None
    price_center: Optional[str] = None


@dataclass
class ParseAudit:
    total_amount_from_items: float
    total_deviation_pct: Optional[float]
    within_tolerance: bool
    item_ea_rate_checks: List[Dict[str, Any]]


@dataclass
class OFCOPayload:
    meta: InvoiceMeta
    items: List[LineItem]
    audit: ParseAudit


def extract_text_from_pdf(pdf_path: str, max_pages: int = 2) -> str:
    """
    Extract text from PDF (first max_pages only)

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to extract (default: 2 for PAGE 1-2)

    Returns:
        Extracted text
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        pages_to_extract = min(max_pages, total_pages)

        logger.info(f"Extracting first {pages_to_extract} of {total_pages} pages")

        text = ""
        for i in range(pages_to_extract):
            page_text = reader.pages[i].extract_text() or ""
            text += page_text + "\n"
            logger.debug(f"  Page {i+1}: {len(page_text)} chars")

        return text
    except Exception:
        pass
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        pages_to_extract = min(max_pages, total_pages)

        text = ""
        for i in range(pages_to_extract):
            text += reader.pages[i].extract_text() + "\n"

        return text
    except Exception as e:
        with open(pdf_path, "rb") as f:
            data = f.read()
        return data.decode("utf-8", errors="ignore")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def split_item_after_total(line: str, *, src_hint: str = "") -> str:
    """
    금액-텍스트 분리: 여러 패턴을 우선순위로 시도하여 분할
    - Pattern 1: "85.76Name :" → "85.76\nName :"
    - Pattern 2: "159,550.0730Agency" → "159,550.07\n30Agency"
    - Pattern 3: "320.00 30Agency" → "320.00\n30Agency"
    """
    for i, pattern in enumerate(SPLIT_PATTERNS):
        m = pattern.search(line)
        if m:
            try:
                groups = m.groups()
                logger.debug("SPLIT pattern %d hit @%s groups=%s", i, src_hint, groups)
            except Exception:
                pass
            # Group 1은 금액, 나머지는 분리할 텍스트
            # replacement 형식: '\1\n' (1개 그룹) or '\1\n\2\3' (2개 그룹)
            num_groups = len(m.groups())
            if num_groups >= 1:
                if num_groups == 1:
                    # Group 1만 있으면 lookahead 패턴: '\1\n' 뒤에 매칭된 시작
                    replacement = r"\1\n"
                else:
                    # Group 1 + N: '\1\n\2\3...'
                    replacement = r"\1\n" + "".join(
                        f"\\{j+2}" for j in range(num_groups - 1)
                    )
                return pattern.sub(replacement, line, count=1)
            else:
                return line  # 그룹 없으면 분할 안함
    return line


def normalize_line(line: str, *, src_hint: str = "") -> str:
    """
    전처리: 금액-항목번호 붙은 케이스 안전 분리 → 후속 파싱
    Note: This parser doesn't use strip_noise, so we only do item splitting
    """
    s = split_item_after_total(line, src_hint=src_hint)
    return s


def clean_description(desc: str) -> str:
    """
    Description에서 헤더/메타 키워드 제거
    - 회사명/주소 패턴 제거
    - 헤더 키워드 제거
    - 섹션 prefix 제거
    - 연속 공백 정규화
    """
    if not desc:
        return ""

    # 항목 번호 제거 (맨 앞 1-2자리 숫자 제거, 예: "1Agency", "2SAFEEN")
    desc = re.sub(r"^\d{1,2}(?=[A-Z])", "", desc)

    # 섹션 prefix 제거
    desc = re.sub(r"__SEC__[^_]+__\s*", "", desc, flags=re.I)

    # 회사명/주소 패턴 제거 (긴 패턴이면 제거)
    desc = re.sub(
        r"P\.O\.\s*Box\s+No\s+\d+.*?Tax Registration.*?TAX INVOICE",
        "",
        desc,
        flags=re.I | re.S,
    )
    desc = re.sub(
        r"P\.O\.\s*Box\s+No\s+\d+.*?OFCO Offshore Support", "", desc, flags=re.I | re.S
    )
    desc = re.sub(
        r"P\.O\.\s*Box.*?Agency fee", "", desc, flags=re.I | re.S
    )  # 첫 항목까지 제거
    desc = re.sub(
        r"S\s*N\s+Description.*?Amount\s+incl.*?VAT", "", desc, flags=re.I | re.S
    )

    # 헤더 키워드 제거
    keywords = [
        "Tax Registration",
        "TAX INVOICE",
        "Amount excl. VAT",
        "Tax Amount",
        "Unit Price",
        "Amount incl. VAT",
        "DescriptionTax",
        "RateQty",
    ]
    for kw in keywords:
        desc = re.sub(rf"\b{re.escape(kw)}\b", "", desc, flags=re.I)

    # 연속 공백 정규화 및 양끝 공백 제거
    return re.sub(r"\s+", " ", desc).strip()


def classify_line(line: str) -> str:
    """
    라인 타입 분류

    Returns:
        - 'item_start_desc': 항목 번호+설명 붙어있음 (1Agency fee:...)
        - 'item_number': 항목 번호만 (^\d+$)
        - 'tax_rate': 세율 (^\d+%$)
        - 'numeric': 숫자 데이터 (^\d+[,.]?\d*$)
        - 'description': 설명 텍스트
        - 'stop': 종료 키워드 (Grand Total, Bank Details 등)
    """
    line = line.strip()
    if not line:
        return "empty"

    # Check ITEM_START_RE first (covers "1 Agency fee" format with space)
    if ITEM_START_RE.match(line):
        return "item_start_desc"
    # Check ITEM_START_COMPACT_RE (covers "18Agency", "26OFCO" format without space)
    if ITEM_START_COMPACT_RE.match(line):
        return "item_start_desc"
    if re.match(r"^\d+$", line):
        return "item_number"
    elif re.match(r"^\d+%$", line):
        return "tax_rate"
    elif re.match(r"^[\d,]+\.?\d*$", line):
        return "numeric"
    elif re.search(
        r"Grand Total|Bank Details|Payment Terms|Amount in Words", line, re.I
    ):
        return "stop"
    else:
        return "description"


def map_numeric_fields(numeric_values: List[str]) -> Dict[str, float]:
    """
    숫자 리스트를 필드명으로 매핑

    Args:
        numeric_values: ['1.00', '490.13', '490.13', '24.51', '514.64']

    Returns:
        {
            'qty': 1.0,
            'unit_price': 490.13,
            'amount_excl_vat': 490.13,
            'tax_amount': 24.51,
            'amount_incl_vat': 514.64
        }
    """
    result = {}
    f2 = lambda x: float(x.replace(",", "") if isinstance(x, str) else x)

    for i, value in enumerate(numeric_values):
        if i < len(NUMERIC_FIELD_ORDER):
            field_name = NUMERIC_FIELD_ORDER[i]
            result[field_name] = f2(value)

    return result


def infer_unit_field(item: Dict) -> str:
    """
    Unit 필드 추론 (기본값: "EA" - Each)

    추론 규칙:
    - Description에 "hours", "hrs" 포함 → "HR"
    - Description에 "days" 포함 → "DA"
    - Description에 "ton", "MT" 포함 → "MT"
    - 기본값 → "EA"
    """
    description = item.get("description", "")
    if isinstance(description, list):
        description = " ".join(description)
    description = str(description).lower()

    if "hour" in description or "hrs" in description:
        return "HR"
    elif "day" in description:
        return "DA"
    elif "ton" in description or "mt" in description:
        return "MT"
    else:
        return "EA"  # Default: Each


class MultilineOFCOParser:
    """다중라인 OFCO 파서"""

    def __init__(self):
        self.state = ParserState.SEARCHING_ITEM
        self.current_item = None
        self.items = []
        self.data_field_index = 0

    def start_new_item(self, line: str):
        """새 항목 시작 - ITEM_START_RE 또는 ITEM_START_COMPACT_RE 매칭으로 sn/tar 추출"""
        m = ITEM_START_RE.match(line.strip())
        if not m:
            # 붙어있는 케이스 체크 (예: "18Agency", "26OFCO")
            m = ITEM_START_COMPACT_RE.match(line.strip())
            if m:
                sn = m.group("sn")
                tar = None
                # compact 형식: text 그룹 사용
                text_part = (
                    m.group("text")
                    if "text" in m.groupdict()
                    else line[m.end() :].strip()
                )
                desc_part = text_part
                self.current_item = {
                    "sn": sn,
                    "tar": tar,
                    "number": line.strip(),
                    "description": [desc_part] if desc_part else [],
                    "tax_rate": None,
                    "numeric_data": [],
                }
                return
        if m:
            sn = m.group("sn")
            tar = m.group("tar")
            # Remove the matched prefix from the line to get description
            desc_part = line[m.end() :].strip()
            self.current_item = {
                "sn": sn,
                "tar": tar,
                "number": line.strip(),
                "description": [desc_part] if desc_part else [],
                "tax_rate": None,
                "numeric_data": [],
            }
        else:
            # Fallback for numeric-only item numbers
            self.current_item = {
                "number": line.strip(),
                "description": [],
                "tax_rate": None,
                "numeric_data": [],
            }

    def add_numeric_field(self, line: str):
        """숫자 필드 추가"""
        if self.current_item:
            self.current_item["numeric_data"].append(line.strip())
            self.data_field_index += 1

    def complete_item(self):
        """항목 완료 처리"""
        if self.current_item and len(self.current_item["numeric_data"]) >= 5:
            # 숫자 필드 매핑
            numeric_fields = map_numeric_fields(self.current_item["numeric_data"])

            # Unit 필드 추론
            unit = infer_unit_field(self.current_item)

            # 최종 항목 생성
            item = {
                "description": _norm(" ".join(self.current_item["description"])),
                "tax_rate": self.current_item["tax_rate"],
                "unit": unit,
                **numeric_fields,
            }

            # sn/tar 추가 (있으면)
            if "sn" in self.current_item:
                item["sn"] = self.current_item["sn"]
            if "tar" in self.current_item and self.current_item.get("tar"):
                item["tariff_code"] = self.current_item["tar"]

            self.items.append(item)

        # 상태 초기화
        self.current_item = None
        self.data_field_index = 0

    def parse(self, lines: List[str]) -> List[Dict]:
        """상태 머신 기반 파싱 - item_start_desc 지원"""
        for line in lines:
            line_type = classify_line(line)

            if line_type == "stop":
                break

            if self.state == ParserState.SEARCHING_ITEM:
                # ITEM_START_COMPACT_RE도 체크
                if line_type in (
                    "item_number",
                    "item_start_desc",
                ) or ITEM_START_COMPACT_RE.match(line):
                    self.start_new_item(line)
                    self.state = ParserState.READING_DESCRIPTION

            elif self.state == ParserState.READING_DESCRIPTION:
                if line_type == "tax_rate":
                    if self.current_item:
                        self.current_item["tax_rate"] = line.strip()
                        self.state = ParserState.READING_DATA
                        self.data_field_index = 0
                elif line_type in ("description", "item_start_desc"):
                    if self.current_item:
                        self.current_item["description"].append(line.strip())
                elif line_type == "item_number":
                    # 다음 항목 시작 (현재 항목 불완전)
                    self.complete_item()
                    self.start_new_item(line)
                    self.state = ParserState.READING_DESCRIPTION
                elif ITEM_START_COMPACT_RE.match(line):
                    # compact 형식 항목 (예: "18Agency")
                    self.complete_item()
                    self.start_new_item(line)
                    self.state = ParserState.READING_DESCRIPTION

            elif self.state == ParserState.READING_DATA:
                if line_type == "numeric":
                    self.add_numeric_field(line)
                    if self.data_field_index >= 5:  # qty, price, excl, tax, incl
                        self.complete_item()
                        self.state = ParserState.SEARCHING_ITEM
                elif line_type in ("item_number", "item_start_desc"):
                    # 다음 항목 시작
                    self.complete_item()
                    self.start_new_item(line)
                    self.state = ParserState.READING_DESCRIPTION
                elif ITEM_START_COMPACT_RE.match(line):
                    # compact 형식 항목 (예: "18Agency")
                    self.complete_item()
                    self.start_new_item(line)
                    self.state = ParserState.READING_DESCRIPTION

        # 마지막 항목 처리
        if self.current_item:
            self.complete_item()

        return self.items


def detect_invoice_type(text: str) -> str:
    text_upper = text.upper()

    # Check for OFCO first (more specific)
    if "OFCO-INV-" in text_upper:
        return "OFCO"
    if "OFCO" in text_upper and "TAX INVOICE" in text_upper:
        return "OFCO"

    # Then check for ADP
    if "ABU DHABI PORTS" in text_upper or "AD PORTS GROUP" in text_upper:
        return "ADP"

    # Then SAFEEN
    if "PORT: ZAYED PORT" in text_upper or "TAR. CODE" in text_upper:
        return "SAFEEN"

    return "UNKNOWN"


def parse_invoice_number(text: str, invoice_type: str) -> Optional[str]:
    if invoice_type == "OFCO":
        m = re.search(r"\b(OFCO-INV-\d{6,})\b", text, re.I)
        if m:
            return m.group(1)
        m = re.search(
            r"Invoice\s*(?:No\.?|Number)\s*[:\-]?\s*(OFCO-INV-\d{6,})", text, re.I
        )
        if m:
            return m.group(1)
    elif invoice_type == "ADP":
        m = re.search(r"Invoice Number : (INV\d+)", text, re.I)
        if m:
            return m.group(1)
    elif invoice_type == "SAFEEN":
        m = re.search(r"Rotation No (\d+)", text, re.I)
        if m:
            return "ROT-" + m.group(1)

    # Fallback to original logic
    m = re.search(r"Invoice\s*number\s*[:\-]?\s*([A-Z0-9\-]+)", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"Rotation\s*No\s*(\d+)", text, re.I)
    if m:
        return f"ROT-{m.group(1)}"

    return None


def parse_invoice_date(text: str, invoice_type: str) -> Optional[str]:
    pats = [
        r"Date : (\d{1,2} [A-Za-z]+, \d{4})",
        r"(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December), (\d{4})",
        r"Invoice Issue Date : (\d{1,2}-[A-Za-z]{3}-\d{4}) \d{2}:\d{2}",
        r"Date\s*:\s*(\d{1,2}\s*[A-Za-z]+,\s*\d{4})",
        r"Invoice\s*Date\s*[:\-]?\s*([0-3]?\d-[A-Za-z]{3}-\d{2,4})",
        r"INVOICE\s*DATE\s*[:\-]?\s*([0-3]?\d-[A-Za-z]{3}-\d{2,4})",
        r"Invoice\s*Date\s*[:\-]?\s*(\d{4}-\d{2}-\d{2})",
        r"Invoice\s*Date\s*[:\-]?\s*([0-3]?\d[./-][01]?\d[./-]\d{2,4})",
    ]
    for pat in pats:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1)
    m = re.search(r"\b([0-3]?\d-[A-Za-z]{3}-\d{4})\b", text)
    return m.group(1) if m else None


def parse_vat_percent(text: str, invoice_type: str) -> Optional[float]:
    m = re.search(r"VAT % (\d+)", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"TAX Rate (\d+\.\d+)", text, re.I)
    if m:
        return float(m.group(1))
    # For OFCO, 5%
    if "5%" in text:
        return 5.0

    # Fallback to original logic
    m = re.search(
        r"\bVAT\s*(?:Rate|%)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?)\s*%?\b", text, re.I
    )
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    m2 = re.search(r"\b(\d{1,2}(?:\.\d+)?)\s*%\b", text)
    try:
        return float(m2.group(1)) if m2 else None
    except:
        return None


def parse_totals(text: str, meta: InvoiceMeta, invoice_type: str):
    f2 = lambda x: float(x.replace(",", ""))
    if invoice_type == "OFCO":
        m = re.search(
            r"Grand Total (\d{1,3}(?:,\d{3})*?\.\d+) (\d{1,3}(?:,\d{3})*?\.\d+) (\d{1,3}(?:,\d{3})*?\.\d+)",
            text,
            re.I,
        )
        if m:
            meta.total_excl_vat = f2(m.group(1))
            meta.total_vat = f2(m.group(2))
            meta.total_incl_vat = f2(m.group(3))
    elif invoice_type == "ADP":
        m = re.search(r"Invoice Total \(AED\) (\d{1,3}(?:,\d{3})*?\.\d+)", text, re.I)
        if m:
            meta.total_excl_vat = f2(m.group(1))
        m = re.search(r"Total Tax \(AED\) (\d{1,3}(?:,\d{3})*?\.\d+)", text, re.I)
        if m:
            meta.total_vat = f2(m.group(1))
        m = re.search(r"Total Amount \(AED\) (\d{1,3}(?:,\d{3})*?\.\d+)", text, re.I)
        if m:
            meta.total_incl_vat = f2(m.group(1))
    elif invoice_type == "SAFEEN":
        m = re.search(
            r"Invoice Total \(AED\) (\d{1,3}(?:,\d{3})*?\.\d+) (\d+\.\d+) (\d{1,3}(?:,\d{3})*?\.\d+)",
            text,
            re.I,
        )
        if m:
            meta.total_excl_vat = f2(m.group(1))
            meta.total_vat = f2(m.group(2))
            meta.total_incl_vat = f2(m.group(3))

    # Fallback to original logic
    if not meta.total_excl_vat:
        pats = [
            r"Grand Total\s*([\d,]+\.\d+)\s*([\d,]+\.\d+)\s*([\d,]+\.\d+)",
        ]
        for p in pats:
            m = re.search(p, text, re.I)
            if m:
                meta.total_excl_vat = f2(m.group(1))
                meta.total_vat = f2(m.group(2))
                meta.total_incl_vat = f2(m.group(3))
                meta.total_amount = meta.total_incl_vat
                return

    meta.total_amount = meta.total_incl_vat or parse_total_amount_old(text)


def parse_total_amount_old(text: str) -> Optional[float]:
    pats = [
        r"Amount\s*incl\.\s*VAT\s*[:\-]?\s*AED?\s*([\d,]+\.\d+|\d+)",
        r"Grand\s*Total.*?(?:AED)?\s*[:\-]?\s*([\d,]+\.\d+|\d+)",
        r"Total\s*Amount.*?(?:AED)?\s*[:\-]?\s*([\d,]+\.\d+|\d+)",
        r"\bTotal\s*[:\-]?\s*(?:AED)?\s*([\d,]+\.\d+|\d+)",
        r"Total\s*\(Inc\.\s*VAT\)\s*([\d,]+\.\d+|\d+)",
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*0\s*0\.00\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
    ]
    for p in pats:
        m = re.search(p, text, re.I)
        if m:
            try:
                amount_str = m.group(2) if len(m.groups()) > 1 else m.group(1)
                return float(amount_str.replace(",", ""))
            except:
                pass
    return None


def parse_currency(text: str, invoice_type: str) -> str:
    m = re.search(r"Invoice Currency : ([A-Z]{3})", text, re.I)
    if m:
        return m.group(1)
    if "(AED)" in text:
        return "AED"

    # Fallback to original logic
    m = re.search(r"Invoice Currency\s*:\s*([A-Z]{3})", text, re.I)
    return m.group(1) if m else DEFAULT_CURRENCY


def parse_alt_amounts(text: str, meta: InvoiceMeta, invoice_type: str):
    if invoice_type == "OFCO":
        m = re.search(
            r"Amount \(excl\. VAT\) (\d{1,3}(?:,\d{3})*?\.\d+) Exch\. Rate (\d+\.\d+) VAT (\d{1,3}(?:,\d{3})*?\.\d+) Amount \(incl\. VAT\) (\d{1,3}(?:,\d{3})*?\.\d+)",
            text,
            re.I,
        )
        if m:
            f2 = lambda x: float(x.replace(",", ""))
            meta.alt_currency = "AED"
            meta.alt_excl_vat = f2(m.group(1))
            meta.exchange_rate = float(m.group(2))
            meta.alt_vat = f2(m.group(3))
            meta.alt_incl_vat = f2(m.group(4))

    # Fallback to original logic
    m = re.search(
        r"For VAT Purpose \((AED)\)\s*Amount \(excl\. VAT\)\s*([\d,]+\.\d+)\s*Exch\. Rate\s*([\d.]+)\s*VAT\s*([\d,]+\.\d+)\s*Amount \(incl\. VAT\)\s*([\d,]+\.\d+)",
        text,
        re.I,
    )
    if m:

        def f2(x):
            return float(x.replace(",", ""))

        meta.alt_currency = m.group(1)
        meta.alt_excl_vat = f2(m.group(2))
        meta.exchange_rate = float(m.group(3))
        meta.alt_vat = f2(m.group(4))
        meta.alt_incl_vat = f2(m.group(5))


def parse_samsung_ref(text: str, invoice_type: str) -> Optional[str]:
    pats = [
        r"P\.O\./Ref\.No\. : ([A-Z0-9\-]+)",
        r"\b(HVDC-[A-Z0-9\-_/]{3,})\b",
        r"\b(HVDC/[A-Z0-9/\-_.]{3,})\b",
        r"\b(ADOPT-[A-Z0-9\-_/]{3,})\b",
        r"Voyage No\. ([A-Z0-9\-]+)",
        r"Voyage No. : ([A-Z0-9\-]+)",
        r"P\.O\./Ref\.No\.\s*:\s*([A-Z0-9\-]+)",
        r"Voyage\s*No\.\s*([A-Z0-9\-]+)",
    ]
    for pat in pats:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1)
    return None


def parse_customer_name(text: str, invoice_type: str) -> Optional[str]:
    pats = [
        r"Name : (.*?) Date",
        r"Payer Name : (.*?) Tax Registration Number",
        r"Customer (.*?) LOA",
        r"Name\s*:\s*([A-Za-z &\-]+)",
    ]
    for pat in pats:
        m = re.search(pat, text, re.I)
        if m:
            return _norm(m.group(1))
    return None


def parse_supplier_name(text: str, invoice_type: str) -> Optional[str]:
    if invoice_type == "OFCO":
        return "OFCO Offshore Support & Logistic Services LLC"
    elif invoice_type == "ADP":
        return "Abu Dhabi Ports"
    elif invoice_type == "SAFEEN":
        return "SAFEEN"

    # Fallback to original logic
    m = re.search(
        r"^(OFCO Offshore Support & Logistic Services LLC)", text, re.M | re.I
    )
    return m.group(1) if m else None


def parse_vessel_info(text: str) -> Dict[str, Optional[str]]:
    vessel_info = {
        "vessel_name": None,
        "rotation_no": None,
        "voyage_no": None,
        "grt": None,
        "dwt": None,
        "loa": None,
        "customer_reg_no": None,
    }

    m = re.search(r"Vessel Name :? ([\w]+)", text, re.I)
    if m:
        vessel_info["vessel_name"] = m.group(1)

    m = re.search(r"Rotation :? (\d+)", text, re.I)
    if m:
        vessel_info["rotation_no"] = m.group(1)

    m = re.search(r"Voyage No. :? ([A-Z0-9\-]+)", text, re.I)
    if m:
        vessel_info["voyage_no"] = m.group(1)

    m = re.search(r"GRT/DWT (\d+\.\d+)/(\d+\.\d+)", text, re.I)
    if m:
        vessel_info["grt"] = m.group(1)
        vessel_info["dwt"] = m.group(2)

    m = re.search(r"LOA (\d+\.\d+)", text, re.I)
    if m:
        vessel_info["loa"] = m.group(1)

    m = re.search(r"Tax Registration Number : (\d+)", text, re.I)
    if m:
        vessel_info["customer_reg_no"] = m.group(1)

    # Fallback patterns
    if not vessel_info["vessel_name"]:
        m = re.search(r"Vessel Name\s*:\s*([A-Za-z]+)", text, re.I)
        if m:
            vessel_info["vessel_name"] = m.group(1)

    if not vessel_info["rotation_no"]:
        m = re.search(r"Rotation\s*No\s*(\d+)", text, re.I)
        if m:
            vessel_info["rotation_no"] = m.group(1)

    if not vessel_info["voyage_no"]:
        m = re.search(r"Voyage\s*No\.\s*([A-Z0-9\-]+)", text, re.I)
        if m:
            vessel_info["voyage_no"] = m.group(1)

    if not vessel_info["grt"] or not vessel_info["dwt"]:
        m = re.search(r"GRT/DWT\s*([\d.]+)/([\d.]+)", text, re.I)
        if m:
            vessel_info["grt"] = m.group(1)
            vessel_info["dwt"] = m.group(2)

    if not vessel_info["loa"]:
        m = re.search(r"LOA\s*([\d.]+)", text, re.I)
        if m:
            vessel_info["loa"] = m.group(1)

    if not vessel_info["customer_reg_no"]:
        m = re.search(r"Customer\s*REG\.\s*No\s*:\s*(\d+)", text, re.I)
        if m:
            vessel_info["customer_reg_no"] = m.group(1)

    return vessel_info


TAIL_PATTERN = r"(\d+)\s+(.*?)\s*(\d{1,2}%)\s*(\d+\.\d+)\s*(\d{1,3}(?:,\d{3})*?\.\d+)\s*([A-Z]{2,3})\s*(\d{1,3}(?:,\d{3})*?\.\d+)\s*(\d{1,3}(?:,\d{3})*?\.\d+)\s*(\d{1,3}(?:,\d{3})*?\.\d+)"


def parse_bushra_table(text: str) -> List[Dict[str, Any]]:
    """Parse BUSHRA format table with S No, Tar. Code, Description, Amount, VAT%, VAT Amount, Total columns"""
    rows = []

    # Simple and effective pattern for BUSHRA table
    pattern = r"(\d+)\s+([\d.]+)\s+(.*?)\s+([\d,]+\.\d+)\s+(\d+)\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)"

    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    for match in matches:
        sno, tar_code, description, amount, vat_pct, vat_amount, total = match
        rows.append(
            {
                "s_no": int(sno),
                "tar_code": tar_code,
                "description": _norm(description),
                "amount": float(amount.replace(",", "")),
                "vat_pct": int(vat_pct),
                "vat_amount": float(vat_amount.replace(",", "")),
                "total_incl_vat": float(total.replace(",", "")),
                "qty": 1.0,  # Default quantity for BUSHRA format
                "rate": float(amount.replace(",", "")),  # Rate = Amount for BUSHRA
                "uom": "LS",  # Default UOM
                "tax_rate": f"{vat_pct}%",
            }
        )

    return rows


def detect_table_format(lines: List[str]) -> str:
    """
    테이블 형식 감지

    Returns:
        'single_line': 한 줄에 모든 데이터가 있는 형식
        'multiline': 여러 줄로 분산된 형식
    """
    # 첫 번째 항목 번호 찾기
    first_item_idx = None
    first_item_line = None
    for i, line in enumerate(lines):
        if ITEM_START_RE.match(line.strip()):
            first_item_idx = i
            first_item_line = line.strip()
            break

    if first_item_idx is None:
        return "single_line"  # 기본값

    # 분석: 첫 항목 + 다음 N줄을 검사하여 형식 결정
    # 단순히 'multiline'을 반환하지 말고 실제 숫자 블록 분포를 검사

    # 첫 번째 항목 이후 15줄 분석 (더 넓게)
    analysis_lines = lines[first_item_idx : first_item_idx + 15]

    # 숫자/세율 패턴 분석 및 연속 길이(max_consecutive) 측정
    numeric_count = 0
    tax_rate_count = 0
    max_consecutive = 0
    run = 0
    seen_tax = False
    for line in analysis_lines:
        line_type = classify_line(line)
        if line_type == "numeric":
            run += 1
            numeric_count += 1
            if run > max_consecutive:
                max_consecutive = run
        else:
            if line_type == "tax_rate":
                seen_tax = True
            run = 0
    logger.debug(
        "detect_table_format: seen_tax=%s, numeric_count=%d, max_consecutive=%d",
        seen_tax,
        numeric_count,
        max_consecutive,
    )

    # multiline 판정: 세율이 있고 + 연속 숫자가 5개 이상 OR 연속 숫자가 5개 이상
    if (seen_tax and max_consecutive >= 5) or max_consecutive >= 5:
        return "multiline"
    else:
        # OFCO는 기본적으로 single_line 형식이 많음
        return "single_line"


def parse_single_line_format(
    lines: List[str], invoice_type: str
) -> List[Dict[str, Any]]:
    """기존 한 줄 형식 파서"""
    # ========== 전처리: 금액 뒤 붙은 항목 번호 분리 ==========
    preprocessed_lines = []
    # 금액 패턴: 숫자.소수점 뒤에 항목번호(1-2자리)+문자
    # 예: "159,550.0730Agency" → (분할 금지)
    #     "1,234.56 30Agency"  → "1,234.56\n30Agency" (공백/붙임 모두 허용)
    current_section: Optional[str] = None
    for i, raw_line in enumerate(lines, 1):
        if is_noise(raw_line):
            continue
        # 섹션 전환 감지(원본 라인으로 판단: normalize 전에 본다)
        current_section = decide_section(raw_line, current_section)
        hint = f"[{current_section or 'UNK'}]#L{i}"
        normalized = normalize_line(raw_line, src_hint=hint)
        # 개행으로 분리된 경우 여러 라인으로 추가
        for split_line in normalized.split("\n"):
            if split_line.strip():
                # 분리된 라인도 노이즈 체크 (split으로 생성된 "Name : Samsung" 등 제거)
                if not is_noise(split_line):
                    preprocessed_lines.append(
                        f"__SEC__{current_section or 'UNK'}__ {split_line}"
                    )

    lines = preprocessed_lines
    logger.debug(f"Preprocessed lines count: {len(lines)}")
    # ============================================================

    # Find header to start table
    header_pat = {
        # OFCO: 다중라인 헤더 지원 - 핵심 키워드만 매칭
        "OFCO": r"S\s*N\s+.*?Description.*?Tax\s*Rate.*?Amount\s+incl.*?VAT",
        "ADP": r"No Tariff ID Tariff Description Unit 1 Unit 2 Unit 3 Rate Amount Excl TAX \\(AED\\) TAX Rate TAX Type/ Amount \\(AED\\) Total Amount incl\\. TAX \\(AED\\)",
        "SAFEEN": r"S No Tar\\. Code Description Amount VAT % VAT Amount Total \\(Inc\\. VAT\\)",
    }.get(invoice_type, r"Description")

    # Normalize text by replacing newlines with spaces for better pattern matching
    normalized_text = re.sub(r"[\n\r]+", " ", " ".join(lines))
    header_m = re.search(header_pat, normalized_text, re.I)

    # Fallback: Find the first data row (line starting with a number like "1 ")
    start_idx = 0
    for i, line in enumerate(lines):
        # preprocessed에는 "__SEC__<NAME>__ " 접두가 있음
        pure = re.sub(r"^__SEC__[^_]+__\s+", "", line).strip()
        # ITEM_START_RE 또는 ITEM_START_COMPACT_RE로 매칭 체크
        if ITEM_START_RE.match(pure) or ITEM_START_COMPACT_RE.match(
            pure
        ):  # Line starts with number
            start_idx = i
            break

    if start_idx > 0:
        lines = lines[start_idx:]

    rows = []
    buf_desc = ""
    buf_sn: str | None = None
    buf_tar: str | None = None
    buf_sec: Optional[str] = None
    seen_keys: set[tuple] = set()  # 중복 제거 키 (section, sn, desc_norm, amount_excl)
    tail_pat = None
    stop_pat = r"\b(Grand Total|Invoice Total|Bank Details|Payment Terms|Note:|Amount in Words)\b"

    if invoice_type == "OFCO":
        # 패턴 A: 풀 꼬리(세율+수량+단가+UOM+금액3개) - 공백 선택적 허용
        pat_full = re.compile(
            r"(?P<tax_rate>\d{1,2}(?:\.\d+)?%?)\s*"  # 공백 선택 (\s* 사용)
            r"(?P<qty>\d+(?:\.\d+)?)\s*"
            r"(?P<unit_price>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"
            r"(?P<unit>[A-Za-z]{1,6})\s*"
            r"(?P<amount_excl>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"
            r"(?P<tax_amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"
            r"(?P<amount_incl>\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            re.I,
        )
        # 패턴 B: 축약 꼬리(UOM/단가/수량 없음) — 예: "320.00 0 0.00 320.00"
        pat_compact = re.compile(
            r"(?P<amount_excl>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"  # 공백 선택
            r"(?P<tax_rate>\d{1,2}(?:\.\d+)?)\s*"  # 0 또는 5 등
            r"(?P<tax_amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*"
            r"(?P<amount_incl>\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            re.I,
        )
        tail_pat = (pat_full, pat_compact)
    elif invoice_type == "ADP":
        tail_pat = re.compile(
            r"(?P<unit1>\d+\.\d+)\s*(?P<unit2>\d+\.\d+)\s*(?P<unit3>\d+\.\d+)\s*(?P<rate>\d+\.\d+)\s*(?P<amount_excl>\d{1,3}(?:,\d{3})*?\.\d+)\s*(?P<tax_rate>\d+\.\d+)\s*(?P<tax_amount>\d+\.\d+)\s*(?P<amount_incl>\d{1,3}(?:,\d{3})*?\.\d+)",
            re.I,
        )
    elif invoice_type == "SAFEEN":
        tail_pat = re.compile(
            r"(?P<amount_excl>\d{1,3}(?:,\d{3})*?\.\d+)\s*(?P<vat_pct>\d+)\s*(?P<vat_amount>\d+\.\d+)\s*(?P<amount_incl>\d{1,3}(?:,\d{3})*?\.\d+)",
            re.I,
        )

    if not tail_pat:
        return []

    # For multi-line data, combine consecutive lines to search for patterns
    combined_text = ""
    lines_since_last_amount = 0  # 마지막 금액 매칭 이후 줄 수

    for ln in lines:
        # 섹션 접두 제거
        msec = re.match(r"^__SEC__([^_]+)__\s+(.*)$", ln)
        cur_section = msec.group(1) if msec else None
        ln = (msec.group(2) if msec else ln).strip()
        if cur_section is not None:
            # 섹션 바뀌면 SN/버퍼 초기화
            if buf_sec is None or buf_sec != cur_section:
                buf_desc = ""
                buf_sn = None
                buf_tar = None
                combined_text = ""
            buf_sec = cur_section

        # 새 항목 시작 시 버퍼 초기화
        m_start = ITEM_START_RE.match(ln)
        if not m_start:
            # 붙어있는 케이스 체크 (예: "18Agency", "26OFCO")
            m_start = ITEM_START_COMPACT_RE.match(ln)
            if m_start:
                # 기존 버퍼 먼저 플러시 (강제)
                if buf_desc and buf_sn:
                    cleaned_desc = clean_description(buf_desc)
                    row = {"description": _norm(cleaned_desc)}
                    if buf_sn:
                        row["sn"] = buf_sn
                    if buf_tar:
                        row["tariff_code"] = buf_tar
                    if buf_sec:
                        row["section"] = buf_sec
                    # 기본값 추가
                    row["tax_rate"] = "5%"
                    row["amount_excl_vat"] = None
                    row = apply_tariff_defaults(row)
                    if section_allowed(buf_sec):
                        dup_key = (
                            row.get("section"),
                            row.get("sn"),
                            row.get("description"),
                            None,
                        )
                        if dup_key not in seen_keys:
                            seen_keys.add(dup_key)
                            rows.append(row)
                            logger.info(
                                f"Pre-flushed for compact: SN={buf_sn}, desc={cleaned_desc[:50]}"
                            )
                    # 버퍼 리셋
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    lines_since_last_amount = 0

                logger.debug("New item start detected (compact): %s", ln)
                buf_sn = m_start.group("sn")
                buf_tar = None  # compact 형식에는 tar code 없음
                # compact 형식에서는 text 그룹을 사용
                text_part = (
                    m_start.group("text")
                    if "text" in m_start.groupdict()
                    else ln[m_start.end() :].strip()
                )
                buf_desc = text_part
                combined_text = buf_desc

                # 같은 줄에 꼬리가 붙어 있는 케이스를 즉시 탐색
                def _search_tail(s: str):
                    if invoice_type == "OFCO":
                        m1 = tail_pat[0].search(s)
                        if m1:
                            return ("full", m1)
                        m2 = tail_pat[1].search(s)
                        if m2:
                            return ("compact", m2)
                        return (None, None)
                    else:
                        return ("single", tail_pat.search(s))

                kind0, m0 = (
                    _search_tail(combined_text) if combined_text else (None, None)
                )
                if m0 and buf_desc:
                    cleaned_desc = clean_description(buf_desc)
                    row = {"description": _norm(cleaned_desc)}
                    f2 = lambda x: float(
                        x.replace(",", "") if isinstance(x, str) else x
                    )
                    if invoice_type == "OFCO":
                        if kind0 == "full":
                            row.update(
                                {
                                    "tax_rate": m0.group("tax_rate"),
                                    "qty": f2(m0.group("qty")),
                                    "unit_price": f2(m0.group("unit_price")),
                                    "unit": m0.group("unit"),
                                    "amount_excl_vat": f2(m0.group("amount_excl")),
                                    "tax_amount": f2(m0.group("tax_amount")),
                                    "amount_incl_vat": f2(m0.group("amount_incl")),
                                }
                            )
                        elif kind0 == "compact":
                            row.update(
                                {
                                    "tax_rate": m0.group("tax_rate"),
                                    "amount_excl_vat": f2(m0.group("amount_excl")),
                                    "tax_amount": f2(m0.group("tax_amount")),
                                    "amount_incl_vat": f2(m0.group("amount_incl")),
                                }
                            )
                    if buf_sn:
                        row["sn"] = buf_sn
                    if buf_tar:
                        row["tariff_code"] = buf_tar
                    if buf_sec:
                        row["section"] = buf_sec
                    row = apply_tariff_defaults(row)
                    if not section_allowed(buf_sec):
                        buf_desc = ""
                        buf_sn = None
                        buf_tar = None
                        combined_text = ""
                        continue
                    dup_key = (
                        row.get("section"),
                        row.get("sn"),
                        row.get("description"),
                        row.get("amount_excl_vat"),
                    )
                    if dup_key in seen_keys:
                        logger.debug("DUP SKIP %s", dup_key)
                        buf_desc = ""
                        buf_sn = None
                        buf_tar = None
                        combined_text = ""
                        continue
                    seen_keys.add(dup_key)
                    rows.append(row)
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    continue

        if m_start:
            logger.debug("New item start detected: %s", ln)
            buf_sn = m_start.group("sn")
            buf_tar = m_start.group("tar")
            # ITEM_START_RE가 매칭한 부분 제거한 나머지를 description으로
            remainder = ln[m_start.end() :].strip()
            buf_desc = remainder  # clean_description은 나중에 적용
            combined_text = buf_desc  # 같은 라인에 금액이 있을 수 있음

            # 같은 줄에 꼬리가 붙어 있는 케이스를 즉시 탐색
            def _search_tail(s: str):
                if invoice_type == "OFCO":
                    m1 = tail_pat[0].search(s)
                    if m1:
                        return ("full", m1)
                    m2 = tail_pat[1].search(s)
                    if m2:
                        return ("compact", m2)
                    return (None, None)
                else:
                    return ("single", tail_pat.search(s))

            kind0, m0 = _search_tail(combined_text) if combined_text else (None, None)
            if m0 and buf_desc:
                # 항목 시작과 동시에 tail이 있는 경우도 description 정제
                cleaned_desc = clean_description(buf_desc)
                row = {"description": _norm(cleaned_desc)}
                f2 = lambda x: float(x.replace(",", "") if isinstance(x, str) else x)
                if invoice_type == "OFCO":
                    if kind0 == "full":
                        row.update(
                            {
                                "tax_rate": m0.group("tax_rate"),
                                "qty": f2(m0.group("qty")),
                                "unit_price": f2(m0.group("unit_price")),
                                "unit": m0.group("unit"),
                                "amount_excl_vat": f2(m0.group("amount_excl")),
                                "tax_amount": f2(m0.group("tax_amount")),
                                "amount_incl_vat": f2(m0.group("amount_incl")),
                            }
                        )
                    elif kind0 == "compact":
                        row.update(
                            {
                                "tax_rate": m0.group("tax_rate"),
                                "amount_excl_vat": f2(m0.group("amount_excl")),
                                "tax_amount": f2(m0.group("tax_amount")),
                                "amount_incl_vat": f2(m0.group("amount_incl")),
                            }
                        )
                # sn/tar/section 보존
                if buf_sn:
                    row["sn"] = buf_sn
                if buf_tar:
                    row["tariff_code"] = buf_tar
                if buf_sec:
                    row["section"] = buf_sec
                # ---- Tariff defaults 주입 ----
                row = apply_tariff_defaults(row)
                # 섹션 필터링
                if not section_allowed(buf_sec):
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    continue
                # 중복 제거 키 생성
                dup_key = (
                    row.get("section"),
                    row.get("sn"),
                    row.get("description"),
                    row.get("amount_excl_vat"),
                )
                if dup_key in seen_keys:
                    logger.debug("DUP SKIP %s", dup_key)
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    continue
                seen_keys.add(dup_key)
                rows.append(row)
                buf_desc = ""
                buf_sn = None
                buf_tar = None
                combined_text = ""
                continue
            # 같은 줄에 꼬리가 없으면 다음 줄부터 누적 - 아래에서 처리됨
            # continue 제거: 설명 누적을 위해 다음 라인으로 진행

        if not ln:
            continue

        # 추가 체크: compact 형식 항목이 다음 줄에서 계속되는 경우
        # (예: "18Agency fee" 다음 줄에 금액이 올 수 있음)
        if buf_sn and not combined_text.strip() and ITEM_START_COMPACT_RE.match(ln):
            # 이미 compact 형식 항목이 시작되었는데 또 다른 compact 형식 항목이 나오면
            # 이전 항목을 완료하고 새 항목 시작
            if buf_desc:
                # 이전 항목 완료 처리 (금액 정보 없이)
                cleaned_desc = clean_description(buf_desc)
                row = {"description": _norm(cleaned_desc)}
                if buf_sn:
                    row["sn"] = buf_sn
                if buf_tar:
                    row["tariff_code"] = buf_tar
                if buf_sec:
                    row["section"] = buf_sec
                row = apply_tariff_defaults(row)
                if section_allowed(buf_sec):
                    dup_key = (
                        row.get("section"),
                        row.get("sn"),
                        row.get("description"),
                        row.get("amount_excl_vat"),
                    )
                    if dup_key not in seen_keys:
                        seen_keys.add(dup_key)
                        rows.append(row)
            # 새 항목 시작
            m_compact = ITEM_START_COMPACT_RE.match(ln)
            if m_compact:
                buf_sn = m_compact.group("sn")
                buf_tar = None
                text_part = (
                    m_compact.group("text")
                    if "text" in m_compact.groupdict()
                    else ln[m_compact.end() :].strip()
                )
                buf_desc = text_part
                combined_text = buf_desc
                continue

        # Stop pattern: reset buffer but continue parsing (multi-page support)
        if re.search(stop_pat, ln, re.I):
            # Flush current buffer if any
            if buf_desc and combined_text:
                # Try to extract last item before stop pattern
                def _search_tail(s: str):
                    if invoice_type == "OFCO":
                        m1 = tail_pat[0].search(s)
                        if m1:
                            return ("full", m1)
                        m2 = tail_pat[1].search(s)
                        if m2:
                            return ("compact", m2)
                        return (None, None)
                    else:
                        return ("single", tail_pat.search(s))

                kind, m = _search_tail(combined_text)
                if m:
                    # Stop 패턴 전에도 description 정제
                    cleaned_desc = clean_description(buf_desc)
                    row = {"description": _norm(cleaned_desc)}
                    f2 = lambda x: float(
                        x.replace(",", "") if isinstance(x, str) else x
                    )
                    if invoice_type == "OFCO":
                        if kind == "full":
                            row.update(
                                {
                                    "tax_rate": m.group("tax_rate"),
                                    "qty": f2(m.group("qty")),
                                    "unit_price": f2(m.group("unit_price")),
                                    "unit": m.group("unit"),
                                    "amount_excl_vat": f2(m.group("amount_excl")),
                                    "tax_amount": f2(m.group("tax_amount")),
                                    "amount_incl_vat": f2(m.group("amount_incl")),
                                }
                            )
                        elif kind == "compact":
                            row.update(
                                {
                                    "tax_rate": m.group("tax_rate"),
                                    "amount_excl_vat": f2(m.group("amount_excl")),
                                    "tax_amount": f2(m.group("tax_amount")),
                                    "amount_incl_vat": f2(m.group("amount_incl")),
                                }
                            )
                    if buf_sn:
                        row["sn"] = buf_sn
                    if buf_tar:
                        row["tariff_code"] = buf_tar
                    if buf_sec:
                        row["section"] = buf_sec
                    # ---- Tariff defaults 주입 ----
                    row = apply_tariff_defaults(row)
                    # 섹션 필터링
                    if not section_allowed(buf_sec):
                        buf_desc = ""
                        buf_sn = None
                        buf_tar = None
                        combined_text = ""
                        continue
                    # 중복 제거 키
                    dup_key = (
                        row.get("section"),
                        row.get("sn"),
                        row.get("description"),
                        row.get("amount_excl_vat"),
                    )
                    if dup_key not in seen_keys:
                        seen_keys.add(dup_key)
                        rows.append(row)

            # Reset buffer and continue to next table
            buf_desc = ""
            buf_sn = None
            buf_tar = None
            combined_text = ""
            continue

        # compact 형식 항목의 경우 설명에 추가
        if buf_sn and buf_desc and ITEM_START_COMPACT_RE.match(ln) is None:
            # compact 형식 항목이 시작되었고, 현재 라인이 새로운 항목이 아니면 설명에 추가
            buf_desc += " " + ln

        combined_text += " " + ln

        # OFCO는 두 패턴을 순차 적용
        def _search_tail(s: str):
            if invoice_type == "OFCO":
                m1 = tail_pat[0].search(s)
                if m1:
                    return ("full", m1)
                m2 = tail_pat[1].search(s)
                if m2:
                    return ("compact", m2)
                return (None, None)
            else:
                return ("single", tail_pat.search(s))

        kind, m = _search_tail(combined_text)
        if m:
            if buf_desc:
                # __SEC__ prefix 최종 제거 (누적된 buf_desc에서)
                cleaned_desc = clean_description(buf_desc)
                row = {"description": _norm(cleaned_desc)}
                f2 = lambda x: float(x.replace(",", "") if isinstance(x, str) else x)

                if invoice_type == "OFCO":
                    if kind == "full":
                        row.update(
                            {
                                "tax_rate": m.group("tax_rate"),
                                "qty": f2(m.group("qty")),
                                "unit_price": f2(m.group("unit_price")),
                                "unit": m.group("unit"),
                                "amount_excl_vat": f2(m.group("amount_excl")),
                                "tax_amount": f2(m.group("tax_amount")),
                                "amount_incl_vat": f2(m.group("amount_incl")),
                            }
                        )
                    elif kind == "compact":
                        # 수량/단가/UOM 부재 — Unit은 추론, EA×Rate는 금액 기반으로 fallback
                        row.update(
                            {
                                "tax_rate": m.group("tax_rate"),
                                "amount_excl_vat": f2(m.group("amount_excl")),
                                "tax_amount": f2(m.group("tax_amount")),
                                "amount_incl_vat": f2(m.group("amount_incl")),
                            }
                        )
                elif invoice_type == "ADP":
                    row.update(
                        {
                            "unit1": f2(m.group("unit1")),
                            "unit2": f2(m.group("unit2")),
                            "unit3": f2(m.group("unit3")),
                            "rate": f2(m.group("rate")),
                            "amount_excl_vat": f2(m.group("amount_excl")),
                            "tax_rate": f2(m.group("tax_rate")),
                            "tax_amount": f2(m.group("tax_amount")),
                            "amount_incl_vat": f2(m.group("amount_incl")),
                        }
                    )
                elif invoice_type == "SAFEEN":
                    row.update(
                        {
                            "amount_excl_vat": f2(m.group("amount_excl")),
                            "tax_rate": f2(m.group("vat_pct")) / 100,
                            "tax_amount": f2(m.group("vat_amount")),
                            "amount_incl_vat": f2(m.group("amount_incl")),
                        }
                    )

                # Extract sn, tar_code from description if present
                if invoice_type in ["ADP", "SAFEEN"]:
                    tar_m = re.match(r"(\d+)\s*(\d+\.\d+)\s*(.*)", row["description"])
                    if tar_m:
                        row["sn"] = tar_m.group(1)
                        row["tariff_id"] = tar_m.group(2)
                        row["description"] = _norm(tar_m.group(3))
                elif invoice_type == "OFCO":
                    if buf_sn:
                        row["sn"] = buf_sn
                    if buf_tar:
                        row["tariff_code"] = buf_tar
                if buf_sec:
                    row["section"] = buf_sec
                # ---- Tariff defaults 주입 ----
                row = apply_tariff_defaults(row)
                # 섹션 필터링/중복키 처리 (기존 로직 유지)
                if not section_allowed(buf_sec):
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    continue
                # 중복 제거 키
                dup_key = (
                    row.get("section"),
                    row.get("sn"),
                    row.get("description"),
                    row.get("amount_excl_vat"),
                )
                if dup_key in seen_keys:
                    logger.debug("DUP SKIP %s", dup_key)
                    buf_desc = ""
                    buf_sn = None
                    buf_tar = None
                    combined_text = ""
                    continue
                seen_keys.add(dup_key)
                rows.append(row)
                buf_desc = ""
                buf_sn = None
                buf_tar = None
                combined_text = ""  # Reset combined text after successful match
                lines_since_last_amount = 0  # 리셋
        else:
            # 금액 매칭 실패 시 카운터 증가
            lines_since_last_amount += 1

            # 강제 플러시 체크
            if (
                buf_desc
                and buf_sn
                and lines_since_last_amount >= MAX_LINES_WITHOUT_AMOUNT
            ):
                logger.debug(
                    f"Force flushing buffer after {lines_since_last_amount} lines without amount"
                )

                # 금액 없이 항목 생성
                cleaned_desc = clean_description(buf_desc)
                row = {"description": _norm(cleaned_desc)}

                if buf_sn:
                    row["sn"] = buf_sn
                if buf_tar:
                    row["tariff_code"] = buf_tar
                if buf_sec:
                    row["section"] = buf_sec

                # 기본값 추가
                row["tax_rate"] = "5%"
                row["amount_excl_vat"] = None

                row = apply_tariff_defaults(row)

                if section_allowed(buf_sec):
                    dup_key = (
                        row.get("section"),
                        row.get("sn"),
                        row.get("description"),
                        None,
                    )
                    if dup_key not in seen_keys:
                        seen_keys.add(dup_key)
                        rows.append(row)
                        logger.info(
                            f"Force-flushed item: SN={buf_sn}, desc={cleaned_desc[:50]}"
                        )

                # 버퍼 리셋
                buf_desc = ""
                buf_sn = None
                buf_tar = None
                combined_text = ""
                lines_since_last_amount = 0

            # Check if this line is description (not numeric data)
            # compact 형식 항목의 경우 설명에 추가
            if buf_sn and buf_desc:
                # 이미 compact 형식 항목이 시작되었고, 금액 패턴이 매칭되지 않았으면
                # 다음 항목이 아닌 경우에만 설명에 추가
                if not ITEM_START_RE.match(ln) and not ITEM_START_COMPACT_RE.match(ln):
                    if not re.match(r"^[\d%.]+$", ln) and not re.match(r"^\d+%$", ln):
                        buf_desc += " " + ln
            elif not re.match(r"^[\d%.]+$", ln) and not re.match(
                r"^\d+%$", ln
            ):  # Not just numbers or percentages
                buf_desc += " " + ln
            # If it's just numbers, keep accumulating in combined_text

    # 루프 종료 전: 남은 버퍼 처리 (compact 형식 항목 등)
    if buf_desc and buf_sn:
        # 금액 패턴을 한 번 더 시도
        def _search_tail_final(s: str):
            if invoice_type == "OFCO":
                m1 = tail_pat[0].search(s)
                if m1:
                    return ("full", m1)
                m2 = tail_pat[1].search(s)
                if m2:
                    return ("compact", m2)
                return (None, None)
            else:
                return ("single", tail_pat.search(s))

        kind_final, m_final = (
            _search_tail_final(combined_text) if combined_text else (None, None)
        )
        if m_final:
            # 금액 패턴 매칭 성공
            cleaned_desc = clean_description(buf_desc)
            row = {"description": _norm(cleaned_desc)}
            f2 = lambda x: float(x.replace(",", "") if isinstance(x, str) else x)
            if invoice_type == "OFCO":
                if kind_final == "full":
                    row.update(
                        {
                            "tax_rate": m_final.group("tax_rate"),
                            "qty": f2(m_final.group("qty")),
                            "unit_price": f2(m_final.group("unit_price")),
                            "unit": m_final.group("unit"),
                            "amount_excl_vat": f2(m_final.group("amount_excl")),
                            "tax_amount": f2(m_final.group("tax_amount")),
                            "amount_incl_vat": f2(m_final.group("amount_incl")),
                        }
                    )
                elif kind_final == "compact":
                    row.update(
                        {
                            "tax_rate": m_final.group("tax_rate"),
                            "amount_excl_vat": f2(m_final.group("amount_excl")),
                            "tax_amount": f2(m_final.group("tax_amount")),
                            "amount_incl_vat": f2(m_final.group("amount_incl")),
                        }
                    )
        else:
            # 금액 정보 없이 항목 완료 (최소한 SN과 description은 보존)
            cleaned_desc = clean_description(buf_desc)
            row = {"description": _norm(cleaned_desc)}

        if buf_sn:
            row["sn"] = buf_sn
        if buf_tar:
            row["tariff_code"] = buf_tar
        if buf_sec:
            row["section"] = buf_sec
        row = apply_tariff_defaults(row)
        if section_allowed(buf_sec):
            # amount_excl_vat가 None일 수 있으므로 튜플에서 None 처리
            amount_key = row.get("amount_excl_vat")
            dup_key = (
                row.get("section"),
                row.get("sn"),
                row.get("description"),
                amount_key,
            )
            if dup_key not in seen_keys:
                seen_keys.add(dup_key)
                rows.append(row)
                logger.debug(
                    f"Flushed buffer item: SN={buf_sn}, desc={row.get('description')[:50]}"
                )

    return rows


def parse_multiline_format(lines: List[str], invoice_type: str) -> List[Dict[str, Any]]:
    """새로운 다중라인 형식 파서"""
    # NOTE: OFCO PAGE 1-2 형식은 "1Agency fee..."처럼 항목번호+설명이 붙어있지만
    # 숫자 블록이 한 줄로 와서 사실상 parse_single_line_format()이 처리 가능
    # MultilineOFCOParser는 순수 다중라인 숫자 분산 형식만 처리
    logger.debug(
        "parse_multiline_format: using parse_single_line_format for PAGE 1-2 style"
    )
    return parse_single_line_format(lines, invoice_type)


def deduplicate_items(
    items: List[Dict[str, Any]], similarity_threshold: float = 0.95
) -> List[Dict[str, Any]]:
    """
    중복 항목 제거: SN 우선, Description 유사도 기반

    Args:
        items: 파싱된 항목 리스트 (row 딕셔너리 또는 LineItem 변환 후)
        similarity_threshold: 유사도 임계값 (0.95 = 95% 이상 같으면 중복)

    Returns:
        중복 제거된 항목 리스트
    """
    if not items:
        return []

    # 첫 번째 항목은 항상 유지
    deduped = [items[0]]
    seen_descriptions = [items[0].get("description", "")]
    seen_sns = set()

    # 첫 항목의 SN 추출 (row 딕셔너리 형식 또는 NOTES 형식 모두 지원)
    first_item_sn = None
    if "sn" in items[0]:
        first_item_sn = items[0].get("sn")
        if first_item_sn and str(first_item_sn).isdigit():
            seen_sns.add(int(first_item_sn))
    elif "NOTES" in items[0]:
        first_notes = items[0].get("NOTES", "")
        if "sn=" in first_notes:
            try:
                first_item_sn = first_notes.split("sn=")[1].split(";")[0].strip()
                if first_item_sn.isdigit():
                    seen_sns.add(int(first_item_sn))
            except:
                pass

    def similarity(s1: str, s2: str) -> float:
        """간단한 문자열 유사도 계산 (Levenshtein distance 기반)"""
        if not s1 or not s2:
            return 0.0

        # 짧은 문자열 길이 확인
        s1_short = s1[:30].lower().strip()  # 처음 30자만, 소문자, 공백 제거
        s2_short = s2[:30].lower().strip()

        # 완전히 동일한 경우
        if s1_short == s2_short:
            return 1.0

        # 한 문자열이 다른 문자열에 포함되어 있는지 확인
        if len(s1_short) > 10 and len(s2_short) > 10:
            if s1_short in s2_short or s2_short in s1_short:
                return 0.90  # 부분 포함 = 높은 유사도

        # 공통 단어 비율 계산
        words1 = set(s1_short.split())
        words2 = set(s2_short.split())

        if not words1 or not words2:
            return 0.0

        common_words = words1.intersection(words2)
        total_words = words1.union(words2)

        # 80% 이상의 단어가 공통 = 중복
        if len(total_words) > 0:
            jaccard = len(common_words) / len(total_words)
            if jaccard >= 0.80:
                return 0.90

        return 0.0

    for item in items[1:]:
        desc = item.get("description", "")
        is_duplicate = False

        # SN 추출 (row 딕셔너리 형식 또는 NOTES 형식 모두 지원)
        item_sn = None
        if "sn" in item:
            item_sn = item.get("sn")
            if item_sn and str(item_sn).isdigit():
                item_sn = int(item_sn)
            else:
                item_sn = None
        elif "NOTES" in item:
            notes = item.get("NOTES", "")
            if "sn=" in notes:
                try:
                    sn_str = notes.split("sn=")[1].split(";")[0].strip()
                    if sn_str.isdigit():
                        item_sn = int(sn_str)
                except:
                    pass

        # SN이 있고 이미 본 SN이면 중복 (동일 SN 중복)
        if item_sn is not None:
            if item_sn in seen_sns:
                # SN이 중복이면 중복으로 간주
                logger.debug(f"Deduplicating by SN: SN={item_sn} already seen")
                is_duplicate = True
            else:
                # SN이 다르면 다른 항목 (중복 아님) - SN이 다르면 무조건 다른 항목
                seen_sns.add(item_sn)
                # SN이 다르면 description 유사도 검사 생략 (무조건 다른 항목)
                is_duplicate = False

        # SN이 없는 경우에만 description 유사도 검사
        if not is_duplicate and item_sn is None:
            # 기존 항목과 유사도 검사 (SN이 없는 경우만)
            for seen_desc in seen_descriptions:
                sim = similarity(desc, seen_desc)
                if sim >= similarity_threshold:
                    logger.debug(
                        f"Deduplicating: '{desc[:50]}...' vs '{seen_desc[:50]}...' (similarity: {sim:.2f}, SN=None)"
                    )
                    is_duplicate = True
                    break

        if not is_duplicate:
            deduped.append(item)
            seen_descriptions.append(desc)

    logger.info(
        f"De-duplication: {len(items)} items → {len(deduped)} items (removed {len(items) - len(deduped)})"
    )
    return deduped


def parse_table_rows(text: str, invoice_type: str) -> List[Dict[str, Any]]:
    """
    통합 테이블 파서

    자동 감지:
    1. 한 줄 형식 → 기존 정규식 파서 사용
    2. 다중 줄 형식 → 새 상태 머신 파서 사용
    """
    lines = text.splitlines()

    # 형식 감지: 첫 번째 항목의 구조 분석
    format_type = detect_table_format(lines)

    if format_type == "single_line":
        # 기존 정규식 파서
        items = parse_single_line_format(lines, invoice_type)
    else:
        # 새 다중라인 파서
        items = parse_multiline_format(lines, invoice_type)

    # 중복 제거 적용
    items = deduplicate_items(items, similarity_threshold=0.95)

    return items


TAIL_NUMERIC = re.compile(
    r"""
    (?P<tax>\d{1,2}(?:\.\d+)?%)\s*
    (?P<qty>\d+(?:\.\d+)?)\s+
    (?P<rate>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<uom>[A-Za-z]{1,6})\s*
    (?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<vat>\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+
    (?P<total>\d{1,3}(?:,\d{3})*(?:\.\d+)?)
    \s*$
""",
    re.X,
)


def find_subject_lines(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidates = []
    for l in lines:
        if any(
            k in l
            for k in [
                "Agency fee",
                "ADP",
                "SAFEEN",
                "Supply of",
                "Berthing",
                "Pilotage",
                "Man-power",
                "Forklift",
                "Crane",
                "Port Dues",
                "Channel",
                "Gate Pass",
                "Waste",
                "PTW",
                "Storage",
                "MGO",
            ]
        ):
            candidates.append(_norm(l))
    seen, out = set(), []
    for c in candidates:
        lc = c.lower()
        if lc not in seen:
            out.append(c)
            seen.add(lc)
    return out


# V3 JSON 규칙 캐시
_v3_json_rules_cache = None
_v3_json_rules_compiled_cache = None


def load_v3_json_rules(
    json_path: str = "config/subject_cost_center_mapping.json",
) -> List[Dict[str, Any]]:
    """V3 JSON 규칙 로드 및 캐싱"""
    global _v3_json_rules_cache, _v3_json_rules_compiled_cache

    if _v3_json_rules_compiled_cache is not None:
        return _v3_json_rules_compiled_cache

    try:
        # 상대 경로를 절대 경로로 변환
        json_file = Path(json_path)
        if not json_file.is_absolute():
            json_file = Path(__file__).parent / json_file

        if not json_file.exists():
            logger.warning(f"V3 JSON 규칙 파일 없음: {json_file}")
            _v3_json_rules_cache = []
            _v3_json_rules_compiled_cache = []
            return []

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        rules = data.get("rules", [])

        # JSON 규칙을 컴파일된 정규식으로 변환
        compiled_rules = []
        for rule in rules:
            pattern_str = rule.get("pattern", "")
            case_sensitive = rule.get("case_sensitive", False)
            mapping = rule.get("mapping", {})

            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                compiled_pattern = re.compile(pattern_str, flags)
                compiled_rules.append({"pattern": compiled_pattern, "mapping": mapping})
            except re.error as e:
                logger.warning(f"V3 패턴 컴파일 실패: {pattern_str} - {e}")

        _v3_json_rules_cache = rules
        _v3_json_rules_compiled_cache = compiled_rules

        logger.info(f"V3 JSON 규칙 로드 완료: {len(compiled_rules)}개")
        return compiled_rules

    except Exception as e:
        logger.warning(f"V3 JSON 규칙 로드 실패: {e}")
        _v3_json_rules_cache = []
        _v3_json_rules_compiled_cache = []
        return []


def map_cost_centers_from_subject(subject: str) -> Dict[str, Optional[str]]:
    """
    SUBJECT → Cost Center 매핑 (하이브리드: V3 JSON 규칙 우선, 기존 SUBJECT_CC_MAP 보조)

    우선순위:
    1. V3 JSON 규칙 (614개)
    2. 기존 SUBJECT_CC_MAP (33개)
    3. PRICE_CENTER_HEURISTICS (fallback)
    """
    # 1. V3 JSON 규칙 먼저 시도
    v3_rules = load_v3_json_rules()
    for rule in v3_rules:
        if rule["pattern"].search(subject):
            mapping = rule["mapping"]
            return {
                "COST MAIN": mapping.get("COST MAIN"),
                "COST CENTER A": mapping.get("COST CENTER A"),
                "COST CENTER B": mapping.get("COST CENTER B"),
                "PRICE CENTER": mapping.get("PRICE CENTER"),
            }

    # 2. 기존 SUBJECT_CC_MAP 시도
    for pat, mp in SUBJECT_CC_MAP:
        if pat.search(subject):
            return {
                "COST MAIN": mp.get("COST MAIN"),
                "COST CENTER A": mp.get("COST CENTER A"),
                "COST CENTER B": mp.get("COST CENTER B"),
                "PRICE CENTER": mp.get("PRICE CENTER"),
            }

    # 3. PRICE_CENTER_HEURISTICS fallback
    pc = None
    for pat, name in PRICE_CENTER_HEURISTICS:
        if pat.search(subject):
            pc = name
            break
    return {
        "COST MAIN": None,
        "COST CENTER A": None,
        "COST CENTER B": None,
        "PRICE CENTER": pc,
    }


def build_items(rows: List[Dict[str, Any]], invoice_type: str) -> List[LineItem]:
    items = []
    for r in rows:
        subject = r.get("description", "")
        cc = map_cost_centers_from_subject(subject)
        ea_rates = []
        if invoice_type == "OFCO":
            if "qty" in r and "unit_price" in r:
                ea_rates = [(r.get("qty", 1.0), r.get("unit_price", 0.0))]
            else:
                # compact 꼬리: EA×Rate가 명시 없으면 Amount만 검증 대상으로 사용
                ea_rates = []
        elif invoice_type == "ADP":
            # Use unit1 as qty, rate as unit_price (assuming main unit)
            ea_rates = [(r.get("unit1", 1.0), r.get("rate", 0.0))]
        elif invoice_type == "SAFEEN":
            ea_rates = [(1.0, r.get("amount_excl_vat", 0.0))]
        amount = r.get("amount_excl_vat")
        # Tariff Code, sn 등 메타를 Notes에 보존
        notes = "; ".join(
            [
                f"{k}={v}"
                for k, v in r.items()
                if k not in ["description", "amount_excl_vat"]
            ]
        )
        items.append(
            LineItem(
                subject=subject,
                ea_rates=ea_rates,
                amount=amount,
                notes=notes,
                cost_main=cc.get("COST MAIN"),
                cost_center_a=cc.get("COST CENTER A"),
                cost_center_b=cc.get("COST CENTER B"),
                price_center=cc.get("PRICE CENTER"),
            )
        )
    return items


def ea_rate_amount_check(item: LineItem) -> Dict[str, Any]:
    if item.amount is None or not item.ea_rates:
        return {
            "subject": item.subject,
            "status": "SKIP",
            "reason": "missing EA/Rate or Amount",
        }
    total = sum(ea * rate for ea, rate in item.ea_rates)
    dev = abs(total - item.amount)
    ok = (dev <= ABS_EPS) or (item.amount > 0 and dev / item.amount <= REL_TOL)
    return {
        "subject": item.subject,
        "calc": round(total, 2),
        "amount": round(item.amount or 0, 2),
        "dev": round(dev, 2),
        "ok": ok,
    }


def compute_audit(meta: InvoiceMeta, items: List[LineItem]) -> ParseAudit:
    total_items = round(sum(i.amount or 0.0 for i in items), 2)
    if meta.total_excl_vat and meta.total_excl_vat > 0:
        dev_pct = round(
            abs(total_items - meta.total_excl_vat) / meta.total_excl_vat * 100, 2
        )
        within = dev_pct / 100 <= REL_TOL
    else:
        dev_pct = None
        within = True
    checks = [ea_rate_amount_check(i) for i in items]
    return ParseAudit(
        total_amount_from_items=total_items,
        total_deviation_pct=dev_pct,
        within_tolerance=within,
        item_ea_rate_checks=checks,
    )


def payload_to_json_dict(payload: OFCOPayload) -> Dict[str, Any]:
    return {
        "meta": asdict(payload.meta),
        "items": [
            {
                "SUBJECT": it.subject,
                "EA_RATE_PAIRS": [
                    (round(ea, 2), round(rate, 2)) for ea, rate in it.ea_rates
                ],
                "Amount (AED)": round(it.amount, 2) if it.amount is not None else None,
                "COST MAIN": it.cost_main,
                "COST CENTER A": it.cost_center_a,
                "COST CENTER B": it.cost_center_b,
                "PRICE CENTER": it.price_center,
                "NOTES": it.notes,
            }
            for it in payload.items
        ],
        "audit": asdict(payload.audit),
    }


def flatten_payload_to_csv_rows(payload: OFCOPayload) -> List[List[str]]:
    rows = []

    # Header row
    header = [
        "Invoice Number",
        "Date",
        "Samsung Ref",
        "VAT%",
        "Currency",
        "Total Excl VAT",
        "Total VAT",
        "Total Incl VAT",
        "Vessel Name",
        "Rotation No",
        "Voyage No",
        "GRT",
        "DWT",
        "LOA",
        "Customer Reg No",
        "Item#",
        "Subject",
        "EA",
        "Rate",
        "Amount",
        "Cost Main",
        "Cost Center A",
        "Cost Center B",
        "Price Center",
        "Notes",
    ]
    rows.append(header)

    # Extract metadata
    meta = payload.meta

    # Data rows - one per line item
    for idx, item in enumerate(payload.items, 1):
        # Extract EA and Rate (use first pair if multiple)
        ea = item.ea_rates[0][0] if item.ea_rates else ""
        rate = item.ea_rates[0][1] if item.ea_rates else ""

        row = [
            meta.invoice_number or "",
            meta.invoice_date or "",
            meta.samsung_ref or "",
            str(meta.vat_percent) if meta.vat_percent is not None else "",
            meta.currency or "",
            str(meta.total_excl_vat) if meta.total_excl_vat is not None else "",
            str(meta.total_vat) if meta.total_vat is not None else "",
            str(meta.total_incl_vat) if meta.total_incl_vat is not None else "",
            meta.vessel_name or "",
            meta.rotation_no or "",
            meta.voyage_no or "",
            meta.grt or "",
            meta.dwt or "",
            meta.loa or "",
            meta.customer_reg_no or "",
            str(idx),
            item.subject or "",
            str(ea) if ea else "",
            str(rate) if rate else "",
            str(item.amount) if item.amount is not None else "",
            item.cost_main or "",
            item.cost_center_a or "",
            item.cost_center_b or "",
            item.price_center or "",
            item.notes or "",
        ]
        rows.append(row)

    # Add blank row
    rows.append([""] * len(header))

    # Audit summary rows
    audit = payload.audit
    rows.append(["AUDIT SUMMARY:"] + [""] * (len(header) - 1))
    rows.append(
        ["Items Total:", "", "", "", "", str(audit.total_amount_from_items)]
        + [""] * (len(header) - 6)
    )
    rows.append(
        ["Invoice Total Excl VAT:", "", "", "", "", str(meta.total_excl_vat or "")]
        + [""] * (len(header) - 6)
    )
    rows.append(
        [
            "Deviation %:",
            "",
            "",
            "",
            "",
            (
                str(audit.total_deviation_pct)
                if audit.total_deviation_pct is not None
                else "N/A"
            ),
        ]
        + [""] * (len(header) - 6)
    )
    rows.append(
        [
            "Within Tolerance:",
            "",
            "",
            "",
            "",
            "PASS" if audit.within_tolerance else "FAIL",
        ]
        + [""] * (len(header) - 6)
    )

    passed_checks = sum(1 for chk in audit.item_ea_rate_checks if chk.get("ok", False))
    total_checks = len(audit.item_ea_rate_checks)
    rows.append(
        ["EA×Rate Checks Passed:", "", "", "", "", f"{passed_checks}/{total_checks}"]
        + [""] * (len(header) - 6)
    )

    return rows


def write_csv(rows: List[List[str]], output_path: str):
    """Write rows to CSV file"""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"[OK] Wrote CSV: {output_path}")


# Keep other functions as is, but update calls in parse_ofco_invoice


def parse_ofco_invoice(pdf_path: str) -> OFCOPayload:
    text = extract_text_from_pdf(pdf_path)
    invoice_type = detect_invoice_type(text)

    vessel_info = parse_vessel_info(text)

    meta = InvoiceMeta(
        invoice_number=parse_invoice_number(text, invoice_type),
        invoice_date=parse_invoice_date(text, invoice_type),
        customer_name=parse_customer_name(text, invoice_type),
        supplier_name=parse_supplier_name(text, invoice_type),
        samsung_ref=parse_samsung_ref(text, invoice_type),
        vat_percent=parse_vat_percent(text, invoice_type),
        currency=parse_currency(text, invoice_type),
        vessel_name=vessel_info.get("vessel_name"),
        rotation_no=vessel_info.get("rotation_no"),
        voyage_no=vessel_info.get("voyage_no"),
        grt=vessel_info.get("grt"),
        dwt=vessel_info.get("dwt"),
        loa=vessel_info.get("loa"),
        customer_reg_no=vessel_info.get("customer_reg_no"),
    )
    parse_totals(text, meta, invoice_type)
    parse_alt_amounts(text, meta, invoice_type)

    rows: List[Dict[str, Any]] = []
    if _should_use_pymupdf():
        try:
            pym_rows = extract_invoice_items_pymupdf(pdf_path)
            ok, conf, total = _validate_rows(pym_rows)
            if ok:
                logger.info("PyMuPDF extractor accepted (%d rows, conf %.2f) for %s", len(pym_rows), conf, os.path.basename(pdf_path))
                rows = deduplicate_items(pym_rows, similarity_threshold=0.95)
            else:
                logger.warning("PyMuPDF extractor low confidence (%.2f, total %.2f) for %s", conf, total, os.path.basename(pdf_path))
        except Exception as exc:
            logger.warning("PyMuPDF extractor failed for %s: %s", os.path.basename(pdf_path), exc)
            rows = []

    if not rows:
        logger.info("Falling back to text-based parser for %s", os.path.basename(pdf_path))
        rows = parse_table_rows(text, invoice_type)

    items = build_items(rows, invoice_type)
    audit = compute_audit(meta, items)
    return OFCOPayload(meta=meta, items=items, audit=audit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("--out", default=None, help="JSON output file path")
    ap.add_argument("--csv", default=None, help="CSV output file path")
    args = ap.parse_args()
    from pprint import pprint

    payload = parse_ofco_invoice(args.pdf_path)
    out = payload_to_json_dict(payload)

    # JSON output
    if args.out:
        js = json.dumps(out, ensure_ascii=False, indent=2)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"[OK] Wrote JSON: {args.out}")

    # CSV output
    if args.csv:
        csv_rows = flatten_payload_to_csv_rows(payload)
        write_csv(csv_rows, args.csv)

    # If no output specified, print JSON
    if not args.out and not args.csv:
        js = json.dumps(out, ensure_ascii=False, indent=2)
        print(js)


if __name__ == "__main__":
    main()
