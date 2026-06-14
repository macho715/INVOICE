#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백업 관리자 (Backup Manager)
============================

파이프라인 개선 단계별 백업을 관리하는 유틸리티입니다.
각 Phase 전에 코드, 의존성, 데이터 파일을 백업합니다.

사용법:
    python scripts/utils/backup_manager.py --phase 1 --description "Polars integration"
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUPS_DIR = PROJECT_ROOT / "backups"
CHECKPOINTS_DIR = BACKUPS_DIR / "checkpoints"
DEPENDENCIES_DIR = BACKUPS_DIR / "dependencies"
DATA_BACKUP_DIR = BACKUPS_DIR / "data"


@dataclass
class CheckpointInfo:
    """체크포인트 정보"""
    phase: int
    timestamp: str
    description: str
    git_commit: Optional[str] = None
    dependencies_snapshot: Optional[str] = None
    data_files: List[str] = None

    def __post_init__(self):
        if self.data_files is None:
            self.data_files = []


class BackupManager:
    """백업 관리자"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.backups_dir = BACKUPS_DIR
        self.checkpoints_dir = CHECKPOINTS_DIR
        self.dependencies_dir = DEPENDENCIES_DIR
        self.data_backup_dir = DATA_BACKUP_DIR

        # 디렉토리 생성
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.dependencies_dir.mkdir(parents=True, exist_ok=True)
        self.data_backup_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self, phase: int, description: str, data_files: Optional[List[Path]] = None
    ) -> CheckpointInfo:
        """
        체크포인트 생성

        Args:
            phase: Phase 번호 (1, 2, 3)
            description: 체크포인트 설명
            data_files: 백업할 데이터 파일 경로 리스트

        Returns:
            CheckpointInfo: 생성된 체크포인트 정보
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_id = f"phase{phase}_{timestamp}"

        # Git 커밋 정보 저장
        git_commit = self._get_git_commit()

        # 의존성 백업
        deps_snapshot = self.backup_dependencies(phase, checkpoint_id)

        # 데이터 파일 백업
        backed_up_files = []
        if data_files:
            backed_up_files = self.backup_data_files(phase, checkpoint_id, data_files)

        # 체크포인트 정보 생성
        checkpoint = CheckpointInfo(
            phase=phase,
            timestamp=timestamp,
            description=description,
            git_commit=git_commit,
            dependencies_snapshot=deps_snapshot,
            data_files=[str(f) for f in backed_up_files],
        )

        # 체크포인트 정보 저장
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(asdict(checkpoint), f, indent=2, ensure_ascii=False)

        print(f"[OK] Checkpoint created: {checkpoint_id}")
        print(f"  - Phase: {phase}")
        print(f"  - Description: {description}")
        print(f"  - Git commit: {git_commit}")
        print(f"  - Dependencies: {deps_snapshot}")
        print(f"  - Data files: {len(backed_up_files)} files")

        return checkpoint

    def backup_dependencies(self, phase: int, checkpoint_id: str) -> str:
        """
        의존성 백업

        Args:
            phase: Phase 번호
            checkpoint_id: 체크포인트 ID

        Returns:
            백업된 의존성 파일 경로
        """
        phase_dir = self.dependencies_dir / f"phase{phase}"
        phase_dir.mkdir(parents=True, exist_ok=True)

        # pyproject.toml 백업
        pyproject_src = self.project_root / "pyproject.toml"
        if pyproject_src.exists():
            pyproject_dst = phase_dir / f"{checkpoint_id}_pyproject.toml"
            shutil.copy2(pyproject_src, pyproject_dst)

        # requirements.txt 백업
        requirements_src = self.project_root / "requirements.txt"
        if requirements_src.exists():
            requirements_dst = phase_dir / f"{checkpoint_id}_requirements.txt"
            shutil.copy2(requirements_src, requirements_dst)

        # pip freeze로 현재 환경 스냅샷
        freeze_file = phase_dir / f"{checkpoint_id}_pip_freeze.txt"
        try:
            result = subprocess.run(
                ["pip", "freeze"],
                capture_output=True,
                text=True,
                check=True,
            )
            with open(freeze_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[WARNING] pip freeze failed, skipping environment snapshot")

        return str(freeze_file)

    def backup_data_files(
        self, phase: int, checkpoint_id: str, file_paths: List[Path]
    ) -> List[Path]:
        """
        데이터 파일 백업

        Args:
            phase: Phase 번호
            checkpoint_id: 체크포인트 ID
            file_paths: 백업할 파일 경로 리스트

        Returns:
            백업된 파일 경로 리스트
        """
        phase_dir = self.data_backup_dir / f"phase{phase}"
        phase_dir.mkdir(parents=True, exist_ok=True)

        backed_up_files = []
        for file_path in file_paths:
            if not file_path.exists():
                print(f"[WARNING] File not found: {file_path}")
                continue

            # 상대 경로 유지
            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                # 절대 경로인 경우 파일명만 사용
                rel_path = Path(file_path.name)

            # 백업 경로 생성 (디렉토리 구조 유지)
            backup_path = phase_dir / checkpoint_id / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # 파일 복사
            if file_path.is_file():
                shutil.copy2(file_path, backup_path)
                backed_up_files.append(backup_path)
            elif file_path.is_dir():
                shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
                backed_up_files.append(backup_path)

        return backed_up_files

    def list_checkpoints(self) -> List[Dict]:
        """
        모든 체크포인트 목록 조회

        Returns:
            체크포인트 정보 리스트
        """
        checkpoints = []
        for checkpoint_file in sorted(self.checkpoints_dir.glob("*.json")):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint_data = json.load(f)
                    checkpoints.append(checkpoint_data)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Failed to read {checkpoint_file}: {e}")

        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)

    def get_checkpoint(self, phase: int, checkpoint_id: Optional[str] = None) -> Optional[CheckpointInfo]:
        """
        특정 체크포인트 조회

        Args:
            phase: Phase 번호
            checkpoint_id: 체크포인트 ID (None이면 최신 것)

        Returns:
            CheckpointInfo 또는 None
        """
        if checkpoint_id:
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"
        else:
            # Phase별 최신 체크포인트 찾기
            phase_checkpoints = [
                f for f in self.checkpoints_dir.glob("*.json")
                if f.stem.startswith(f"phase{phase}_")
            ]
            if not phase_checkpoints:
                return None
            checkpoint_file = max(phase_checkpoints, key=lambda p: p.stat().st_mtime)

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CheckpointInfo(**data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to read checkpoint: {e}")
            return None

    def _get_git_commit(self) -> Optional[str]:
        """현재 Git 커밋 해시 조회"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description="백업 관리자")
    parser.add_argument(
        "--phase",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="Phase 번호 (1, 2, 3)",
    )
    parser.add_argument(
        "--description",
        type=str,
        required=True,
        help="체크포인트 설명",
    )
    parser.add_argument(
        "--data-files",
        type=str,
        nargs="+",
        help="백업할 데이터 파일 경로 (상대 경로 또는 절대 경로)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="체크포인트 목록 조회",
    )

    args = parser.parse_args()

    manager = BackupManager()

    if args.list:
        checkpoints = manager.list_checkpoints()
        print(f"\n[CHECKPOINTS] 총 {len(checkpoints)}개\n")
        for cp in checkpoints:
            print(f"Phase {cp['phase']}: {cp['timestamp']}")
            print(f"  Description: {cp['description']}")
            print(f"  Git commit: {cp.get('git_commit', 'N/A')}")
            print()
        return

    # 데이터 파일 경로 변환
    data_files = None
    if args.data_files:
        data_files = [Path(f) if Path(f).is_absolute() else PROJECT_ROOT / f for f in args.data_files]

    # 체크포인트 생성
    checkpoint = manager.create_checkpoint(
        phase=args.phase,
        description=args.description,
        data_files=data_files,
    )

    print(f"\n[SUCCESS] Checkpoint created successfully")
    print(f"Checkpoint ID: phase{checkpoint.phase}_{checkpoint.timestamp}")


if __name__ == "__main__":
    main()

