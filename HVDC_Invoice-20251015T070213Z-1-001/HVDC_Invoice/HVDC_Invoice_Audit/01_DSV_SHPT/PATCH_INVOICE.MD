# --- add: robust header detection -------------------------------------------
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import re
import unicodedata
import pandas as pd

try:
    # optional but improves accuracy
    from rapidfuzz import fuzz, process
    _USE_FUZZ = True
except Exception:
    _USE_FUZZ = False

_CANONICAL = [
    "sno", "description", "quantity", "uom", "unitprice", "rate", "amount", "total", "hscode"
]

# 동의어/오타/한글 → 정규 키
_SYNONYMS: Dict[str, str] = {
    # 번호
    "s/no": "sno", "s no": "sno", "no": "sno", "순번": "sno", "일련번호": "sno",
    # 품명/설명
    "desc": "description", "item desc": "description", "item description": "description",
    "품명": "description", "규격": "description", "설명": "description",
    # 수량
    "qty": "quantity", "q'ty": "quantity", "quantity": "quantity", "수량": "quantity",
    # 단위
    "uom": "uom", "unit": "uom", "단위": "uom",
    # 단가/요율
    "unit price": "unitprice", "unitprice": "unitprice", "단가": "unitprice", "요율": "rate",
    "rate": "rate", "요금": "rate",
    # 금액/합계
    "amount": "amount", "line total": "amount", "금액": "amount",
    "total": "total", "합계": "total", "총액": "total",
    # HS
    "hs": "hscode", "hs code": "hscode", "hscode": "hscode", "hs코드": "hscode", "세번": "hscode",
}

# 텍스트 정규화
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or "")).strip().lower()
    s = re.sub(r"[^\w\s/.-]+", "", s)  # 기호 정리
    s = re.sub(r"\s+", " ", s)
    return s

def _syn_map(token: str) -> str:
    t = token
    # 정확 동의어 매핑
    if t in _SYNONYMS: 
        return _SYNONYMS[t]
    # 부분 포함형(예: 'hs code', 'item description', 'line total')
    for k, v in _SYNONYMS.items():
        if k in t:
            return v
    # 숫자/기호 혼입 (e.g., "Q’TY", "S.NO")
    t2 = t.replace(".", " ").replace("’", "'").replace("'", "")
    if t2 in _SYNONYMS:
        return _SYNONYMS[t2]
    return t

@dataclass
class HeaderDetectionResult:
    header_row_index: int
    two_row_joined: bool
    mapping: Dict[int, str]     # col_index -> canonical
    coverage: float
    reasons: List[str]          # 로그/근거

class HeaderDetector:
    def __init__(self, min_hit:int=3, fuzz_threshold:int=78, scan_rows:int=25):
        self.min_hit = min_hit
        self.fuzz_threshold = fuzz_threshold
        self.scan_rows = scan_rows

    def detect(self, df: pd.DataFrame) -> HeaderDetectionResult:
        """
        단일행/2행 조합 헤더 후보를 0~scan_rows-1 범위에서 탐색.
        1) 퍼지매칭으로 타깃 헤더 커버리지 계산
        2) 폴백: 데이터형 휴리스틱(숫자/통화/HS 패턴/텍스트 비율)
        """
        n_rows = min(len(df), self.scan_rows)
        best = None  # (score, details)
        reasons = []

        def row_text(r: int) -> List[str]:
            return [ _norm(x) for x in list(df.iloc[r].values) ]

        def join_two_rows(r1: int, r2: int) -> List[str]:
            a = row_text(r1); b = row_text(r2)
            out = []
            L = max(len(a), len(b))
            for i in range(L):
                t1 = a[i] if i < len(a) else ""
                t2 = b[i] if i < len(b) else ""
                j = (t1 + " " + t2).strip()
                out.append(j)
            return out

        def fuzzy_match_token(tok: str) -> Tuple[str, int]:
            tok_syn = _syn_map(tok)
            # 정확 매핑되면 높은 점수
            if tok_syn in _CANONICAL:
                return tok_syn, 100
            if not _USE_FUZZ:
                # 간단 유사도(부분 포함)
                for c in _CANONICAL:
                    if c in tok_syn or tok_syn in c:
                        return c, 85
                return "", 0
            # rapidfuzz
            choice, score, _ = process.extractOne(tok_syn, _CANONICAL, scorer=fuzz.token_set_ratio)
            return (choice if score >= self.fuzz_threshold else ""), score

        def score_row(tokens: List[str]) -> Tuple[float, Dict[int, str], Dict[int, int]]:
            mapping, scores = {}, {}
            seen = set()
            for i, t in enumerate(tokens):
                if not t:
                    continue
                canon, sc = fuzzy_match_token(t)
                if canon and canon not in seen:
                    mapping[i] = canon
                    scores[i] = sc
                    seen.add(canon)
            coverage = len(mapping) / max(1, len(_CANONICAL))
            # 보정: 숫자/날짜만 있는 행은 패널티
            pure_numeric_cols = sum(1 for x in tokens if re.fullmatch(r"[\d,.\-/: ]{1,}$", x or ""))
            penalty = 0.15 if pure_numeric_cols >= max(2, len(tokens)//2) else 0.0
            total_score = coverage * 1.0 - penalty
            return total_score, mapping, scores

        candidates: List[Tuple[float, int, bool, Dict[int,str], Dict[int,int]]] = []

        # 1) 단일행 후보
        for r in range(n_rows):
            toks = row_text(r)
            s, m, scs = score_row(toks)
            candidates.append((s, r, False, m, scs))

        # 2) 2행 결합 후보 (머지/두 줄 헤더)
        for r in range(n_rows-1):
            toks = join_two_rows(r, r+1)
            s, m, scs = score_row(toks)
            # 2행 조합은 소폭 가산
            s += 0.05
            candidates.append((s, r, True, m, scs))

        # 최고 점수 후보 선택 (동점 시 더 위 행 우선, 매핑 더 많은 쪽 우선)
        candidates.sort(key=lambda x: (x[0], len(x[3]) ), reverse=True)
        for s, r, two, m, scs in candidates:
            if len(m) >= self.min_hit:
                best = (s, r, two, m, scs)
                reasons.append(f"[primary] picked row {r}{'+'+str(r+1) if two else ''} "
                               f"with {len(m)} canonical hits (score={s:.3f})")
                break

        # 3) 폴백: 휴리스틱(데이터형)로 유추
        if best is None:
            # 상단 5행 내에서 가장 '텍스트 비율' 높은 행을 헤더로
            textiness = []
            for r in range(min(n_rows, 8)):
                toks = row_text(r)
                text_cnt = sum(1 for t in toks if re.search(r"[A-Za-z가-힣]", t or ""))
                textiness.append((text_cnt / max(1, len(toks)), r))
            textiness.sort(reverse=True)
            r = textiness[0][1] if textiness else 0
            toks = row_text(r)
            # 휴리스틱 매핑
            mapping = {}
            for i, t in enumerate(toks):
                tn = _syn_map(t)
                if tn in _CANONICAL:
                    mapping[i] = tn
                elif re.search(r"hs.?code|^\d{6,12}$", t):
                    mapping[i] = "hscode"
                elif re.search(r"(qty|q.?ty|수량)", t):
                    mapping[i] = "quantity"
                elif re.search(r"(unit.?price|단가|rate|요율)", t):
                    mapping[i] = "unitprice"
                elif re.search(r"(amount|total|합계|총액)", t):
                    mapping[i] = "amount"
                elif re.search(r"(uom|단위)", t):
                    mapping[i] = "uom"
                elif re.search(r"(desc|품명|설명|규격|item)", t):
                    mapping[i] = "description"
            best = (0.33, r, False, mapping, {})
            reasons.append(f"[fallback] heuristic header at row {r} with {len(mapping)} fields")

        score, r, two, mapping, scs = best

        # 근거 로그 보강(상위 매칭 점수 상위 5개)
        top5 = sorted(scs.items(), key=lambda kv: kv[1], reverse=True)[:5]
        for ci, sc in top5:
            reasons.append(f"  - col#{ci} '{_norm(df.iloc[r].values[ci])}' -> {mapping[ci]} ({sc})")

        cov = len(mapping)/len(_CANONICAL)
        return HeaderDetectionResult(
            header_row_index=r,
            two_row_joined=two,
            mapping=mapping,
            coverage=cov,
            reasons=reasons
        )

def apply_header(df: pd.DataFrame, hdr: HeaderDetectionResult) -> pd.DataFrame:
    """헤더 적용: 선택된 행(또는 2행 조합)을 컬럼명으로 만들고, 그 위 행들은 드랍."""
    if hdr.two_row_joined:
        r = hdr.header_row_index
        joined = []
        a = df.iloc[r].astype(str).map(_norm).tolist()
        b = df.iloc[r+1].astype(str).map(_norm).tolist()
        L = max(len(a), len(b))
        for i in range(L):
            t1 = a[i] if i < len(a) else ""
            t2 = b[i] if i < len(b) else ""
            joined.append((t1 + " " + t2).strip())
        new_cols = []
        for i, raw in enumerate(joined):
            if i in hdr.mapping:
                new_cols.append(hdr.mapping[i])
            else:
                new_cols.append(_syn_map(raw))
        out = df.iloc[r+2:].copy()
        out.columns = new_cols[:len(out.columns)]
        return out.reset_index(drop=True)
    else:
        r = hdr.header_row_index
        cols_raw = df.iloc[r].astype(str).map(_norm).tolist()
        new_cols = []
        for i, raw in enumerate(cols_raw):
            if i in hdr.mapping:
                new_cols.append(hdr.mapping[i])
            else:
                new_cols.append(_syn_map(raw))
        out = df.iloc[r+1:].copy()
        out.columns = new_cols[:len(out.columns)]
        return out.reset_index(drop=True)
# --- end add -----------------------------------------------------------------
