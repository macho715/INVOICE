#!/usr/bin/env python3
"""
sync_agent_docs.py
- 목적: agent.md(SSOT) ↔ AGENTS.md(mirror) 동기화
- 기본 동작: dry-run (diff만 출력)
- 안전: --write 없이는 파일을 쓰지 않음
"""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path
import sys


def read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def normalize(text: str) -> str:
    # 윈도우/유닉스 개행 차이 최소화
    return text.replace("\r\n", "\n").strip() + "\n"


def unified_diff(a: str, b: str, a_name: str, b_name: str) -> str:
    diff = difflib.unified_diff(
        a.splitlines(keepends=True),
        b.splitlines(keepends=True),
        fromfile=a_name,
        tofile=b_name,
    )
    return "".join(diff)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-path", default="agent.md", help="SSOT 문서 경로(기본: agent.md)")
    ap.add_argument("--to-path", default="AGENTS.md", help="미러 문서 경로(기본: AGENTS.md)")
    ap.add_argument("--write", action="store_true", help="실제로 to-path에 덮어쓰기")
    args = ap.parse_args()

    src = Path(args.from_path)
    dst = Path(args.to_path)

    if not src.exists():
        print(f"[FAIL] source not found: {src}")
        return 2

    src_text = normalize(read_text(src))
    dst_text = normalize(read_text(dst))

    if src_text == dst_text:
        print("[OK] already in sync")
        return 0

    diff = unified_diff(dst_text, src_text, str(dst), str(src))
    print(diff if diff else "[INFO] content differs (diff not available)")

    if not args.write:
        print("[DRY-RUN] add --write to apply changes")
        return 0  # dry-run은 성공으로 처리

    # 안전장치: dst 디렉토리 생성만 허용(파일 삭제/이동 없음)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src_text, encoding="utf-8")
    print(f"[APPLIED] {src} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
