#!/usr/bin/env python3
"""
audit_agent_md.py
- 목적: agent.md(또는 AGENTS.md) 최소 품질 게이트
- 검증:
  1) 필수 헤딩 존재
  2) Commands 섹션에 코드블록 존재(최소 1개)
  3) data/raw 수정 금지 문구 존재
- 실패 시 exit code != 0
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


REQUIRED_HEADINGS = [
    r"##\s+0\)\s+에이전트 작업 원칙",
    r"##\s+2\)\s+빠른 실행 명령",
    r"##\s+3\)\s+입력/출력 데이터 계약",
    r"##\s+10\)\s+Git/PR 규칙",  # 실제 agent.md는 10번 섹션
    r"##\s+11\)\s+트러블슈팅",
]

REQUIRED_PHRASES = [
    "data/raw",
    "읽기 전용",
]


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def has_code_fence(md: str) -> bool:
    return bool(re.search(r"\n```[a-zA-Z0-9]*\n", md))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="agent.md", help="감사할 문서 경로(기본: agent.md)")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"[FAIL] file not found: {p}")
        return 2

    md = read_text(p)

    fails: list[str] = []

    for pat in REQUIRED_HEADINGS:
        if not re.search(pat, md):
            fails.append(f"missing heading pattern: {pat}")

    if not has_code_fence(md):
        fails.append("missing any code fence (```...```) in Commands section")

    for ph in REQUIRED_PHRASES:
        if ph not in md:
            fails.append(f"missing required phrase: {ph}")

    if fails:
        print("[FAIL] agent.md audit failed:")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("[OK] agent.md audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
