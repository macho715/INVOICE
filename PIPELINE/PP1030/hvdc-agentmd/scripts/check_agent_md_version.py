#!/usr/bin/env python3
"""
check_agent_md_version.py
- 목적: agent.md의 버전 정보와 실제 파이프라인 버전 비교
- 사용: 파이프라인 버전 업데이트 시 agent.md 동기화 필요 여부 확인
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys


def extract_version_from_agent_md(agent_md_path: Path) -> str | None:
    """agent.md에서 버전 정보 추출"""
    if not agent_md_path.exists():
        return None
    
    text = agent_md_path.read_text(encoding="utf-8")
    # "agent.md — HVDC Pipeline v4.0.54" 형식 매칭
    match = re.search(r"v(\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def extract_version_from_pipeline(pipeline_path: Path) -> str | None:
    """run_pipeline.py에서 버전 정보 추출"""
    if not pipeline_path.exists():
        return None
    
    text = pipeline_path.read_text(encoding="utf-8")
    # "v4.0.44" 형식 매칭
    match = re.search(r"v(\d+\.\d+\.\d+)", text)
    return match.group(1) if match else None


def extract_version_from_config(config_path: Path) -> str | None:
    """pipeline_config.yaml에서 버전 정보 추출"""
    if not config_path.exists():
        return None
    
    import yaml
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("pipeline", {}).get("version")
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="agent.md와 파이프라인 버전 비교"
    )
    ap.add_argument("--agent-md", default="agent.md", help="agent.md 경로")
    ap.add_argument("--pipeline", default="run/run_pipeline.py", help="파이프라인 스크립트 경로")
    ap.add_argument("--config", default="config/pipeline_config.yaml", help="설정 파일 경로")
    args = ap.parse_args()

    agent_md_path = Path(args.agent_md)
    pipeline_path = Path(args.pipeline)
    config_path = Path(args.config)

    agent_version = extract_version_from_agent_md(agent_md_path)
    pipeline_version = extract_version_from_pipeline(pipeline_path)
    config_version = extract_version_from_config(config_path)

    print(f"agent.md 버전: {agent_version or 'N/A'}")
    print(f"run_pipeline.py 버전: {pipeline_version or 'N/A'}")
    print(f"pipeline_config.yaml 버전: {config_version or 'N/A'}")

    versions = [v for v in [agent_version, pipeline_version, config_version] if v]
    if not versions:
        print("[WARNING] 버전 정보를 찾을 수 없습니다.")
        return 1

    unique_versions = set(versions)
    if len(unique_versions) == 1:
        print("[OK] 모든 버전이 일치합니다.")
        return 0
    else:
        print(f"[WARNING] 버전 불일치 감지: {unique_versions}")
        print("[ACTION] agent.md를 갱신하는 것을 권장합니다.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
