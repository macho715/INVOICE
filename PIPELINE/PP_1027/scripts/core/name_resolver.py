"""헤더/파일/시트명 매칭 도우미 / Flexible resolver for header, file, and sheet names."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

from .header_normalizer import HeaderNormalizer

Kind = str


@dataclass(frozen=True)
class MatchResult:
    """매칭 결과 정보 / Result of a resolved match."""

    value: str
    score: float


class FlexibleNameResolver:
    """헤더/파일/시트명 유연 매칭 / Flexible resolver for header, file, sheet names."""

    def __init__(self, normalizer: Optional[HeaderNormalizer] = None) -> None:
        """정규화 엔진 설정 / Configure optional header normalizer."""

        self._normalizer = normalizer or HeaderNormalizer()

    def normalize(self, value: str, kind: Kind) -> str:
        """값 정규화 / Normalize raw value by kind."""

        text = str(value or "").strip()
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)

        if kind == "header":
            return self._normalizer.normalize(normalized)

        if kind == "file":
            return self._normalize_filename(normalized)

        if kind == "sheet":
            return self._normalize_sheet_name(normalized)

        return self._normalize_generic(normalized)

    def normalize_many(self, values: Iterable[str], kind: Kind) -> list[str]:
        """다중 값 정규화 / Normalize multiple values of the same kind."""

        return [self.normalize(value, kind) for value in values]

    def match_best(
        self,
        target: str,
        candidates: Sequence[str],
        kind: Kind,
        *,
        min_score: float = 0.6,
    ) -> Optional[MatchResult]:
        """최적 후보 찾기 / Find best candidate for the target value."""

        target_key = self.normalize(target, kind)
        if not target_key:
            return None

        best: Optional[Tuple[str, float]] = None
        for candidate in candidates:
            candidate_key = self.normalize(candidate, kind)
            if not candidate_key:
                continue

            if candidate_key == target_key:
                return MatchResult(candidate, 1.0)

            score = SequenceMatcher(None, target_key, candidate_key).ratio()
            if target_key in candidate_key or candidate_key in target_key:
                score = max(score, 0.85)

            if best is None or score > best[1]:
                best = (candidate, score)

        if best is None or best[1] < min_score:
            return None

        return MatchResult(*best)

    def _normalize_filename(self, value: str) -> str:
        """파일명 정규화 / Normalize filename for flexible comparisons."""

        path = Path(value)
        stem = path.stem.replace("_", " ").replace("-", " ")
        normalized_stem = self._normalize_generic(stem)
        suffix = path.suffix.lower().lstrip(".")
        return f"{normalized_stem}.{suffix}" if suffix else normalized_stem

    def _normalize_sheet_name(self, value: str) -> str:
        """시트명 정규화 / Normalize sheet names while keeping word gaps."""

        cleaned = value.replace("_", " ").replace("-", " ")
        filtered = self._filter_letters_numbers_and_space(cleaned, keep_spaces=True)
        return re.sub(r"\s+", " ", filtered).strip().lower()

    def _normalize_generic(self, value: str) -> str:
        """일반 정규화 / Generic normalization for non-specific kinds."""

        filtered = self._filter_letters_numbers_and_space(value, keep_spaces=False)
        return filtered.lower()

    @staticmethod
    def _filter_letters_numbers_and_space(value: str, *, keep_spaces: bool) -> str:
        """문자·숫자·공백 필터 / Filter to letters, numbers, optional spaces."""

        allowed = {"L", "N"}
        result: list[str] = []
        for char in value:
            category = unicodedata.category(char)
            if category and category[0] in allowed:
                result.append(char)
            elif keep_spaces and category == "Zs":
                result.append(" ")
        return "".join(result)
