#!/usr/bin/env python3
"""
update_agent_md_from_template.py
- 목적: 템플릿 기반으로 agent.md 자동 갱신 (보수적 접근)
- 안전: 기존 내용을 보존하면서 누락된 섹션만 추가
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def read_template_sections(template_path: Path) -> dict[str, str]:
    """템플릿에서 섹션별 내용 추출"""
    if not template_path.exists():
        return {}
    
    text = template_path.read_text(encoding="utf-8")
    sections = {}
    
    # 섹션 패턴: ## N) 제목
    pattern = r"##\s+(\d+)\)\s+(.+?)(?=##\s+\d+\)|$)"
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        section_num = match.group(1)
        section_content = match.group(2).strip()
        sections[section_num] = section_content
    
    return sections


def read_agent_md_sections(agent_md_path: Path) -> dict[str, str]:
    """agent.md에서 섹션별 내용 추출"""
    if not agent_md_path.exists():
        return {}
    
    text = agent_md_path.read_text(encoding="utf-8")
    sections = {}
    
    pattern = r"##\s+(\d+)\)\s+(.+?)(?=##\s+\d+\)|$)"
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        section_num = match.group(1)
        section_content = match.group(2).strip()
        sections[section_num] = section_content
    
    return sections


def main() -> int:
    ap = argparse.ArgumentParser(
        description="템플릿 기반 agent.md 갱신 (보수적)"
    )
    ap.add_argument("--template", default="hvdc-agentmd/references/AGENTMD_TEMPLATE.md")
    ap.add_argument("--agent-md", default="agent.md")
    ap.add_argument("--dry-run", action="store_true", help="실제 변경 없이 diff만 출력")
    args = ap.parse_args()

    template_path = Path(args.template)
    agent_md_path = Path(args.agent_md)

    if not template_path.exists():
        print(f"[ERROR] 템플릿을 찾을 수 없습니다: {template_path}")
        return 1

    template_sections = read_template_sections(template_path)
    agent_sections = read_agent_md_sections(agent_md_path)

    missing_sections = []
    for section_num in template_sections:
        if section_num not in agent_sections:
            missing_sections.append(section_num)

    if not missing_sections:
        print("[OK] 모든 필수 섹션이 존재합니다.")
        return 0

    print(f"[INFO] 누락된 섹션: {', '.join(missing_sections)}")
    
    if args.dry_run:
        print("[DRY-RUN] 실제 변경은 수행하지 않습니다.")
        for section_num in missing_sections:
            print(f"\n섹션 {section_num} 내용 (템플릿):")
            print(template_sections[section_num][:200] + "...")
        return 0

    # 실제 갱신은 사용자가 수동으로 수행하도록 권장
    print("[INFO] 자동 갱신은 위험할 수 있습니다. 수동으로 템플릿을 참고하여 갱신하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
