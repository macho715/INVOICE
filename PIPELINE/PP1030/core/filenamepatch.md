---

## `scripts/core/file_finder.py` (전체 파일)

```python
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


@dataclass(frozen=True)
class RawFileHit:
    vendor_key: str             # "SIM" or "HE"
    canonical_name: str         # "simense" or "hitachi"
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
        if p.suffix.lower() not in allowed_suffixes:
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
        depth = len(p.resolve().relative_to(p.anchor).parts)
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
```

---

## `file_registry.py` (전체 파일)

```python
# -*- coding: utf-8 -*-
"""
FileRegistry with flexible raw vendor detection.
- Auto-detect SIM/HE raw files in data/raw via file_finder
- Exposes both path-only and (path, canonical) helpers
- Options passthrough to control SIEMENS alias and custom tokens
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Tuple

# Import tolerant to package layout (scripts/ vs module)
try:
    from scripts.core.file_finder import (
        find_vendor_files,
        RawFileHit,
    )
except Exception:  # pragma: no cover
    from .core.file_finder import (  # type: ignore
        find_vendor_files,
        RawFileHit,
    )


class FileRegistry:
    def __init__(
        self,
        project_root: Path,
        *,
        enable_siemens_alias: Optional[bool] = None,
        extra_sim_tokens: Optional[list[str]] = None,
        extra_he_tokens: Optional[list[str]] = None,
        allowed_suffixes: Optional[set[str]] = None,
    ) -> None:
        self.project_root = project_root
        self.raw_dir = self.project_root / "data" / "raw"
        self.processed_dir = self.project_root / "data" / "processed"
        self.config_dir = self.project_root / "config"

        # finder options
        self._finder_opts = dict(
            enable_siemens_alias=enable_siemens_alias,
            extra_sim_tokens=extra_sim_tokens,
            extra_he_tokens=extra_he_tokens,
            allowed_suffixes=allowed_suffixes,
        )

        # cache: {'SIM': RawFileHit|None, 'HE': RawFileHit|None}
        self._auto_raw_cache: Optional[Dict[str, Optional[RawFileHit]]] = None

    # ---------- core ----------
    def _ensure_auto_scan(self) -> None:
        if self._auto_raw_cache is None:
            self._auto_raw_cache = find_vendor_files(self.raw_dir, **self._finder_opts)

    def resolve(self, *parts: str) -> Path:
        return (self.project_root.joinpath(*parts)).resolve()

    # ---------- public helpers ----------
    def get_raw_vendor(self, vendor: str) -> Optional[Path]:
        """
        Get best-matched raw file path for vendor ('SIM' or 'HE').
        - SIM group: SIM, sim, simense, SIMENSE (+ optional 'siemens')
        - HE  group: HITACHI, hitachi, HE, he, (HE)
        """
        self._ensure_auto_scan()
        vendor = vendor.upper()
        if vendor not in {"SIM", "HE"}:
            raise ValueError(f"Unknown vendor: {vendor}")
        hit = (self._auto_raw_cache or {}).get(vendor)
        return hit.path if hit else None

    def get_raw_with_canonical(self, vendor: str) -> Optional[Tuple[Path, str]]:
        """
        Return (path, canonical_name) where canonical_name in {'simense','hitachi'}.
        """
        self._ensure_auto_scan()
        vendor = vendor.upper()
        hit = (self._auto_raw_cache or {}).get(vendor)
        if not hit:
            return None
        return hit.path, hit.canonical_name

    # Convenience
    def get_raw_sim(self) -> Optional[Path]:
        return self.get_raw_vendor("SIM")

    def get_raw_he(self) -> Optional[Path]:
        return self.get_raw_vendor("HE")
```

---

### 어떻게 쓰면 되나 (예시)

```python
# run_pipeline.py (발췌)
from pathlib import Path
from file_registry import FileRegistry

registry = FileRegistry(
    Path(__file__).resolve().parents[1],
    enable_siemens_alias=True,          # 기본 True (ENV로도 제어 가능)
    extra_sim_tokens=[],                # 필요 시 ["simx"] 같이 추가
    extra_he_tokens=[],                 # 필요 시 ["hitachi-ltd"] 같이 추가
    allowed_suffixes=None,              # 필요 시 {".xlsx",".xlsm"}로 제한
)

he_path, he_name = registry.get_raw_with_canonical("HE") or (None, None)
sim_path, sim_name = registry.get_raw_with_canonical("SIM") or (None, None)
```

* **ENV 제어(선택)**

  * `HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=0` → `SIEMENS` 토큰 비활성
  * `HVDC_FILE_FINDER_ALLOWED_SUFFIXES=".xlsx,.xlsm"` → 확장자 제한

---

### 빠른 테스트 스니펫

```python
from scripts.core.file_finder import _match_vendor_from_stem

# SIEMENS alias ON (기본값)
assert _match_vendor_from_stem("Case List(SIM_20251030)") == ("SIM", "simense")
assert _match_vendor_from_stem("HVDC WAREHOUSE_SIMENSE(SIM)") == ("SIM", "simense")
assert _match_vendor_from_stem("HVDC WAREHOUSE_SIEMENS") == ("SIM", "simense")   # 신규 허용
assert _match_vendor_from_stem("HVDC WAREHOUSE_HITACHI(HE)") == ("HE", "hitachi")
assert _match_vendor_from_stem("Case List(HE)") == ("HE", "hitachi")
assert _match_vendor_from_stem("the-file") is None  # 'he' 부분문자열 오검출 방지
```

---

필요하면 `SIEMENS`를 **기본 OFF**로 바꾸고 싶을 때는 `FileRegistry(..., enable_siemens_alias=False)` 또는 ENV `HVDC_FILE_FINDER_ENABLE_SIEMENS_ALIAS=0`로 끄면 돼.
이 정도면 네 폴더 구조에서 바로 꽂혀서 동작한다.
