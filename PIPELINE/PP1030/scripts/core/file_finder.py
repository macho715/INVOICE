# -*- coding: utf-8 -*-
"""
Flexible raw-file finder (SIMENSE/HITACHI alias-aware).
- Token-based, case-insensitive, synonym-unified matching
- Canonical names: simense, hitachi
- Options:
    * enable_siemens_alias: include 'siemens' as SIM group token (default: True)
    * extra_sim_tokens / extra_he_tokens: add custom tokens
    * allowed_suffixes: override excel suffixes set
    * env overrides:
        - HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=0/1
        - HVDC_FILE_FINDER_ALLOWED_SUFFIXES=".xlsx,.xlsm,.xls"
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Dict, Iterable, Optional, Sequence


# -----------------------------
# Canonical vendor dictionary
# -----------------------------
CANONICALS = {
    "SIM": "simense",
    "HE": "hitachi",
}

# Split on common filename separators; keep alnum only per token
_SPLIT = re.compile(r"[ \-_\.,(){}\[\]+]+")

DEFAULT_EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xls"}
_EXCEL_EXT_RE = re.compile(r"\.\s*(xlsx|xlsm|xls)$", re.I)  # 공백 포함 확장자 대응


@dataclass(frozen=True)
class RawFileHit:
    vendor_key: str  # "SIM" or "HE"
    canonical_name: str  # "simense" or "hitachi"
    path: Path
    score: float = 100.0


def _split_keep_alnum(text: str) -> list[str]:
    raw = _SPLIT.split(text)
    cleaned = [re.sub(r"[^0-9a-z]+", "", t.lower()) for t in raw]
    return [t for t in cleaned if t]


def _tokenize_stem(stem: str) -> list[str]:
    return [p for p in _split_keep_alnum(stem) if p]


def _build_token_sets(
    *,
    enable_siemens_alias: bool = True,
    extra_sim_tokens: Optional[Sequence[str]] = None,
    extra_he_tokens: Optional[Sequence[str]] = None,
) -> tuple[set[str], set[str]]:
    # Base tokens from requirements
    sim_tokens = {"sim", "simense"}
    he_tokens = {"hitachi", "he"}  # 'he' allowed only as standalone token via tokenization

    if enable_siemens_alias:
        sim_tokens.add("siemens")  # optional alias

    if extra_sim_tokens:
        sim_tokens |= {t.lower() for t in extra_sim_tokens}
    if extra_he_tokens:
        he_tokens |= {t.lower() for t in extra_he_tokens}

    return sim_tokens, he_tokens


def _matches(tokens: Iterable[str], allowed: set[str]) -> bool:
    return any(t in allowed for t in tokens)


def _match_vendor_from_stem(
    stem: str,
    *,
    enable_siemens_alias: bool = True,
    extra_sim_tokens: Optional[Sequence[str]] = None,
    extra_he_tokens: Optional[Sequence[str]] = None,
) -> Optional[tuple[str, str]]:
    tokens = _tokenize_stem(stem)
    sim_allowed, he_allowed = _build_token_sets(
        enable_siemens_alias=enable_siemens_alias,
        extra_sim_tokens=extra_sim_tokens,
        extra_he_tokens=extra_he_tokens,
    )

    if _matches(tokens, sim_allowed):
        return "SIM", CANONICALS["SIM"]
    if _matches(tokens, he_allowed):
        return "HE", CANONICALS["HE"]
    return None


def _env_flag(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip() not in {"0", "false", "False", ""}


def _env_suffixes(default: set[str]) -> set[str]:
    v = os.getenv("HVDC_FILE_FINDER_ALLOWED_SUFFIXES")
    if not v:
        return default
    parts = [s.strip().lower() for s in v.split(",") if s.strip()]
    return set(parts) if parts else default


def scan_raw_folder(
    raw_dir: Path,
    *,
    enable_siemens_alias: Optional[bool] = None,
    extra_sim_tokens: Optional[Sequence[str]] = None,
    extra_he_tokens: Optional[Sequence[str]] = None,
    allowed_suffixes: Optional[set[str]] = None,
) -> dict[str, list[RawFileHit]]:
    """
    Scan data/raw for SIM/HE excel files.

    Args:
        enable_siemens_alias: include 'siemens' as SIM token (default True, can be overridden by ENV)
        extra_sim_tokens / extra_he_tokens: custom tokens to include
        allowed_suffixes: override excel suffixes set
    """
    # Resolve options with ENV fallbacks
    if enable_siemens_alias is None:
        enable_siemens_alias = _env_flag("HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS", True)
    if allowed_suffixes is None:
        allowed_suffixes = _env_suffixes(DEFAULT_EXCEL_SUFFIXES)

    results: dict[str, list[RawFileHit]] = {"SIM": [], "HE": []}

    for p in raw_dir.rglob("*"):
        if not p.is_file():
            continue
        # 공백 들어간 확장자까지 허용
        name_lc = p.name.lower()
        if not (_EXCEL_EXT_RE.search(name_lc) or p.suffix.lower() in allowed_suffixes):
            continue

        stem = p.stem
        m = _match_vendor_from_stem(
            stem,
            enable_siemens_alias=enable_siemens_alias,
            extra_sim_tokens=extra_sim_tokens,
            extra_he_tokens=extra_he_tokens,
        )
        if not m:
            continue

        vendor_key, canonical = m
        # Prefer shallow depth + shorter stem
        try:
            raw_dir_resolved = raw_dir.resolve()
            rel_path = p.resolve().relative_to(raw_dir_resolved)
            depth = len(rel_path.parts) - 1  # Subtract 1 because file itself doesn't count as depth
        except (ValueError, AttributeError):
            # Fallback if relative_to fails (e.g., different drives on Windows)
            depth = 0
        score = 100.0 - depth * 2 - (len(stem) / 50.0)
        results[vendor_key].append(RawFileHit(vendor_key, canonical, p, score))

    return results


def _pick_best(hits: list[RawFileHit]) -> Optional[RawFileHit]:
    return sorted(hits, key=lambda h: h.score, reverse=True)[0] if hits else None


def find_vendor_files(
    raw_dir: str | Path,
    *,
    enable_siemens_alias: Optional[bool] = None,
    extra_sim_tokens: Optional[Sequence[str]] = None,
    extra_he_tokens: Optional[Sequence[str]] = None,
    allowed_suffixes: Optional[set[str]] = None,
) -> dict[str, Optional[RawFileHit]]:
    """
    Return representative files for each vendor.
    {'SIM': RawFileHit|None, 'HE': RawFileHit|None}
    """
    root = Path(raw_dir)
    hits = scan_raw_folder(
        root,
        enable_siemens_alias=enable_siemens_alias,
        extra_sim_tokens=extra_sim_tokens,
        extra_he_tokens=extra_he_tokens,
        allowed_suffixes=allowed_suffixes,
    )
    return {"SIM": _pick_best(hits["SIM"]), "HE": _pick_best(hits["HE"])}


if __name__ == "__main__":
    base = Path("data/raw")
    found = find_vendor_files(base)
    pretty = {
        k: None if v is None else {"path": str(v.path), "canonical": v.canonical_name}
        for k, v in found.items()
    }
    print("[RAW FILES]", pretty)

