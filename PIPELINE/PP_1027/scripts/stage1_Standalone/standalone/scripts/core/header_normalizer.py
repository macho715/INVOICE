# -*- coding: utf-8 -*-
"""
Minimal HeaderNormalizer for standalone packaging.
Provides normalization helpers used by SemanticMatcher & StandardHeaderOrder.
"""
import re
from typing import List

class HeaderNormalizer:
    def __init__(self):
        # common unicode-wide spaces to collapse
        self._space_re = re.compile(r"[\s\u00A0\u2000-\u200B]+")
        self._punct_re = re.compile(r"[\-_/\\]+")
        self._multi_space = re.compile(r"\s+")

    def normalize(self, name: str) -> str:
        if name is None:
            return ""
        s = str(name)
        # unify width & remove extra spaces/punct
        s = s.strip()
        s = self._space_re.sub(" ", s)
        s = self._punct_re.sub(" ", s)
        # remove duplicate spaces
        s = self._multi_space.sub(" ", s)
        # standardize brackets/punctuations
        s = s.replace("(", " ").replace(")", " ").replace("[", " ").replace("]", " ")
        s = s.replace(".", " ").replace(",", " ").replace(":", " ").replace(";", " ")
        s = self._multi_space.sub(" ", s)
        return s.lower().strip()

    def normalize_with_alternatives(self, name: str) -> List[str]:
        """Return a list of common normalized variants to improve matching."""
        base = self.normalize(name)
        alts = {base}
        # Remove spaces variant
        alts.add(base.replace(" ", ""))
        # Replace spaces with underscore
        alts.add(base.replace(" ", "_"))
        # Common abbreviations
        alts.add(base.replace("warehouse", "wh"))
        alts.add(base.replace("site ", ""))
        return list(alts)