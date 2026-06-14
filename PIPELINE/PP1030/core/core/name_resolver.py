"""
name_resolver.py
- 파일명/시트명/헤더명 공통 별칭 매칭 + 퍼지 유사도 기반 표준화
- 외부 라이브러리 없이 동작(간단한 Levenshtein 거리, 토큰 기반 일치 포함)
- 매칭 순서: exact > 포함/토큰 > 퍼지(편집거리) with 가중치
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# ---------- 0) 표준 키와 별칭 사전 ----------
# 필요시 자유롭게 확장하십시오.
VENDOR_ALIASES: dict[str, Iterable[str]] = {
    "HITACHI": {
        # 기본
        "hitachi",
        "hitachi energy",
        "he",
        "h.e",
        "h-e",
        "히타치",
        "hitachienergy",
        "he local",
        "he-local",
        # 보고서 확장
        "Hitachi",
        "HITACHI ENERGY",
        "H.E",
        "HE-LOCAL",
    },
    "SIEMENS": {
        # 기본
        "siemens",
        "sim",
        "simense",
        "seimens",
        "ril",
        "r.i.l",
        "ril(simense)",
        "지멘스",
        # 보고서 확장
        "Siemens",
        "SIMENSE",
        "RIL(SIMENSE)",
        "RIL(SIEMENS)",
        "R.I.L",
    },
}

# 시트명도 같은 방식으로: (예시는 실제 시트 이름에 맞춰 추가)
SHEET_ALIASES: dict[str, Iterable[str]] = {
    # 일반 Case List
    "CASE LIST": {
        "case list",
        "caselist",
        "case_list",
        "Case List",
        "CaseList",
        "CASE LIST",
    },
    # RIL(SIEMENS) 변형 포함
    "CASE LIST, RIL(SIEMENS)": {
        "case list, ril(simense)",
        "case list ril",
        "ril",
        "ril(simense)",
        "Case List, RIL",
        "Case List RIL",
        "CASE LIST, RIL",
        "Case List, RIL(SIEMENS)",
    },
    # HE Local
    "HE LOCAL": {
        "he local",
        "he-local",
        "hitachi local",
        "히타치 로컬",
        "HE Local",
        "HELocal",
        "HE-LOCAL",
    },
    # Capacitor 시트 (보고서 확장)
    "HE-0214,0252 (CAPACITOR)": {
        "he-0214,0252",
        "he-0214,0252 (capacitor)",
        "capacitor",
        "HE-0214,0252",
        "Capacitor",
    },
    # 리포트 시트(선별) — 필요 시 계속 보강
    "통합_원본데이터_FIXED": {"통합_원본데이터_fixed"},
    "HITACHI_원본데이터_FIXED": {"hitachi_원본데이터_fixed"},
    "SIEMENS_원본데이터_FIXED": {"siemens_원본데이터_fixed"},
    "창고_월별_입출고": {"창고_월별_입출고"},
    "현장_월별_입고재고": {"현장_월별_입고재고"},
    "FLOW_CODE_분석": {"flow_code_분석"},
}

# 헤더(컬럼) 표준화: 프로젝트에서 자주 쓰는 표준 헤더를 좌측에, 우측에 다양한 변형을 나열
HEADER_ALIASES: dict[str, Iterable[str]] = {
    # Case Number
    "CASE NO": {
        "case no",
        "case_no",
        "caseno",
        "case#",
        "case number",
        "Case No",
        "Case No.",
        "CASE NO",
        "Case Number",
        "Case_No",
        "CaseNo",
        "case-no",
        "CASE_NUMBER",
        "케이스번호",
        "케이스 번호",
        "Case",
        "Package No",
        "Package No.",
        "PACKAGE NO",
        "PackageNo",
        "packageno",
        "Package_No",
    },
    # Vendor
    "VENDOR": {
        "vendor",
        "maker",
        "supplier",
        "vend",
        "vendr",
        "Vendor",
        "VENDOR",
        "Source_Vendor",
        "source_vendor",
        "SourceVendor",
        "Source Vendor",
    },
    # Quantity
    "QTY": {
        "qty",
        "quantity",
        "q'ty",
        "수량",
        "QTY",
        "Qty",
        "Quantity",
        "Q'ty",
        "Qty.",
        "QUANTITY",
        "Amount",
        "Count",
        "Pkg",
        "pkg",
        "Pkg_Quantity",
        "pkg_quantity",
    },
    # Material/Description
    "MATERIAL": {
        "material",
        "item desc",
        "description",
        "desc",
        "품명",
        "Material",
        "MATERIAL",
        "Item Desc",
        "Item Description",
        "Description",
        "Desc",
        "DESC",
        "Detail",
        "Details",
        "Name",
        "Item Name",
        "설명",
        "상세",
        "Description/명칭",
    },
    # Date/Time (요약)
    "ETD/ATD": {
        "etd/atd",
        "etd",
        "atd",
        "etd_atd",
        "etd-atd",
        "etd / atd",
        "Estimated Departure",
        "Actual Departure",
        "Departure Date",
        "Departure",
        "출발일",
    },
    "ETA/ATA": {
        "eta/ata",
        "eta",
        "ata",
        "eta_ata",
        "eta-ata",
        "eta / ata",
        "Estimated Arrival",
        "Actual Arrival",
        "Arrival Date",
        "Arrival",
        "도착일",
    },
    # Warehouse/Site
    "DHL WAREHOUSE": {"dhl wh", "dhl warehouse", "DHL WH", "DHL Warehouse"},
    "DSV INDOOR": {"dsv indoor", "DSV Indoor"},
    "DSV AL MARKAZ": {"dsv al markaz", "DSV Al Markaz", "dsv almarkaz"},
    "DSV OUTDOOR": {"dsv outdoor", "DSV Outdoor"},
    "AAA STORAGE": {"aaa storage", "AAA Storage", "AAA_STORAGE"},
    "HAULER INDOOR": {"hauler indoor", "Hauler Indoor", "HAULER_INDOOR"},
    "MOSB": {"mosb", "MOSB"},
    "MIR": {"mir", "MIR", "MIR Site"},
    "SHU": {"shu", "SHU", "SHU Site"},
    "DAS": {"das", "DAS", "DAS Site"},
    "AGI": {"agi", "AGI", "AGI Site"},
    # KPI/측정
    "SQM": {"sqm", "SQM", "Square Meter", "Square Meterage"},
    "STACK_STATUS": {"stack_status", "Stack_Status", "STACK_STATUS"},
}


# ---------- 1) 정규화 유틸 ----------
def normalize(s: str) -> str:
    """소문자, 공백/특수문자 축약, 호환성 정규화."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s).lower().strip()
    # 괄호/구두점 등은 공백으로, 다중 공백은 1칸으로
    s = re.sub(r"[\t\r\n]+", " ", s)
    s = re.sub(r"[^\w\s]+", " ", s)  # 문자/숫자/언더스코어/공백만
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    return normalize(s).split()


# ---------- 2) 간단 Levenshtein 거리/유사도 ----------
def levenshtein(a: str, b: str) -> int:
    a, b = normalize(a), normalize(b)
    if not a:
        return len(b)
    if not b:
        return len(a)
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, cb in enumerate(b, 1):
            cur = dp[j]
            cost = 0 if ca == cb else 1
            dp[j] = min(
                dp[j] + 1, dp[j - 1] + 1, prev + cost  # deletion  # insertion  # substitution
            )
            prev = cur
    return dp[-1]


def sim_ratio(a: str, b: str) -> float:
    """0~1 범위 유사도: 1 - (편집거리 / 최대길이)"""
    a_n, b_n = normalize(a), normalize(b)
    if not a_n and not b_n:
        return 1.0
    dist = levenshtein(a_n, b_n)
    denom = max(len(a_n), len(b_n), 1)
    return 1.0 - dist / denom


# ---------- 3) 점수 계산 ----------
def token_overlap_score(q: str, cand: str) -> float:
    qs, cs = set(tokenize(q)), set(tokenize(cand))
    if not qs or not cs:
        return 0.0
    inter = len(qs & cs)
    return inter / max(len(qs), len(cs))


def contains_score(q: str, cand: str) -> float:
    qn, cn = normalize(q), normalize(cand)
    return 1.0 if qn and (qn in cn or cn in qn) else 0.0


@dataclass
class MatchResult:
    canonical: str
    alias_matched: str
    score: float
    method: str  # 'exact' | 'contains' | 'token' | 'fuzzy'


# ---------- 4) 공통 매칭 엔진 ----------
def _build_alias_table(alias_map: dict[str, Iterable[str]]) -> list[tuple[str, str]]:
    """[(canonical, alias), ...]"""
    rows: list[tuple[str, str]] = []
    for canon, aliases in alias_map.items():
        rows.append((canon, canon))  # canonical 자체도 별칭으로 취급(정확일치 허용)
        for a in aliases:
            rows.append((canon, a))
    return rows


def _score(query: str, alias: str) -> tuple[float, str]:
    # 정확 일치 최우선
    if normalize(query) == normalize(alias):
        return 1.00, "exact"
    # 포함/토큰/퍼지(가중 혼합)
    c = contains_score(query, alias)  # 0 or 1
    t = token_overlap_score(query, alias)  # 0~1
    f = sim_ratio(query, alias)  # 0~1
    # 가중치: 포함 0.50, 토큰 0.75, 퍼지 1.00 (퍼지가 가장 연속적인 신호)
    score = max(0.50 * c, 0.40 * t + 0.60 * f)  # 토큰+퍼지 혼합
    # 메서드 라벨(설명용)
    method = "contains" if c == 1.0 else ("token" if t >= f else "fuzzy")
    return score, method


def resolve_with_aliases(
    query: str, alias_map: dict[str, Iterable[str]], min_score: float = 0.72
) -> MatchResult | None:
    """별칭 테이블에서 최적 canon 반환. min_score 미만이면 None."""
    if not query:
        return None
    best: MatchResult | None = None
    for canon, alias in _build_alias_table(alias_map):
        s, m = _score(query, alias)
        if (best is None) or (s > best.score):
            best = MatchResult(canonical=canon, alias_matched=alias, score=s, method=m)
    if best and best.score >= min_score:
        return best
    return None


# ---------- 5) 공개 API ----------
def resolve_vendor(text: str, *, min_score: float = 0.72) -> MatchResult | None:
    """파일명/시트명/셀 텍스트에서 벤더 추정."""
    return resolve_with_aliases(text, VENDOR_ALIASES, min_score=min_score)


def resolve_sheet(text: str, *, min_score: float = 0.70) -> MatchResult | None:
    return resolve_with_aliases(text, SHEET_ALIASES, min_score=min_score)


def resolve_header(text: str, *, min_score: float = 0.70) -> MatchResult | None:
    return resolve_with_aliases(text, HEADER_ALIASES, min_score=min_score)


# ---------- 6) 파일명/시트명에서 벤더 후보 추출 헬퍼 ----------
_VENDOR_HINT_PAT = re.compile(
    r"\b(he|hitachi(?:\s*energy)?|siemens|simense|seimens|sim|ril)\b", re.I
)


def guess_vendor_from_filename(path: str) -> MatchResult | None:
    """
    파일 경로/파일명에서 벤더 후보 토큰을 먼저 뽑아 점수 가산.
    """
    if not path:
        return None
    toks = _VENDOR_HINT_PAT.findall(path or "")
    # 후보가 없으면 전체 파일명을 그대로 매칭
    candidates = toks or [path]
    best: MatchResult | None = None
    for c in candidates:
        m = resolve_vendor(c)
        if not m:
            # 토큰이 너무 짧으면 전체 파일명으로 재시도
            m = resolve_vendor(path)
        if m and (best is None or m.score > best.score):
            best = m
    return best
