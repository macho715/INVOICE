#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
롤백 관리자 (Rollback Manager)
==============================

파이프라인 개선 단계별 롤백을 관리하는 유틸리티입니다.
백업된 체크포인트로 코드, 의존성, 데이터 파일을 복구합니다.

사용법:
    python scripts/utils/rollback_manager.py --phase 1
    python scripts/utils/rollback_manager.py --phase 1 --checkpoint-id phase1_20251117_123456
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from backup_manager import BackupManager, CheckpointInfo, PROJECT_ROOT, BACKUPS_DIR


class RollbackManager:
    """롤백 관리자"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.backup_manager = BackupManager(project_root)

    def rollback_phase(
        self, phase: int, checkpoint_id: Optional[str] = None, dry_run: bool = False
    ) -> bool:
        """
        특정 Phase 롤백

        Args:
            phase: Phase 번호 (1, 2, 3)
            checkpoint_id: 체크포인트 ID (None이면 최신 것)
            dry_run: 실제 롤백 없이 시뮬레이션만

        Returns:
            성공 여부
        """
        # 체크포인트 조회
        checkpoint = self.backup_manager.get_checkpoint(phase, checkpoint_id)
        if not checkpoint:
            print(f"[ERROR] Checkpoint not found for phase {phase}")
            return False

        print(f"[INFO] Rolling back to checkpoint:")
        print(f"  Phase: {checkpoint.phase}")
        print(f"  Timestamp: {checkpoint.timestamp}")
        print(f"  Description: {checkpoint.description}")
        print(f"  Git commit: {checkpoint.git_commit}")

        if dry_run:
            print("\n[DRY RUN] Would perform the following actions:")
            print("  1. Restore code from Git commit")
            print("  2. Restore dependencies")
            print("  3. Restore data files")
            return True

        # 1. 코드 복구 (Git)
        if checkpoint.git_commit:
            if not self._restore_from_git(checkpoint.git_commit):
                print("[ERROR] Failed to restore code from Git")
                return False

        # 2. 의존성 복구
        if checkpoint.dependencies_snapshot:
            if not self.restore_dependencies(phase, checkpoint.timestamp):
                print("[WARNING] Failed to restore dependencies, but continuing...")

        # 3. 데이터 파일 복구
        if checkpoint.data_files:
            if not self.restore_data_files(phase, checkpoint.timestamp):
                print("[WARNING] Failed to restore data files, but continuing...")

        print("\n[SUCCESS] Rollback completed")
        return True

    def restore_dependencies(self, phase: int, timestamp: str) -> bool:
        """
        의존성 복구

        Args:
            phase: Phase 번호
            timestamp: 체크포인트 타임스탬프

        Returns:
            성공 여부
        """
        phase_dir = BACKUPS_DIR / "dependencies" / f"phase{phase}"
        checkpoint_id = f"phase{phase}_{timestamp}"

        # pyproject.toml 복구
        pyproject_backup = phase_dir / f"{checkpoint_id}_pyproject.toml"
        if pyproject_backup.exists():
            pyproject_target = self.project_root / "pyproject.toml"
            shutil.copy2(pyproject_backup, pyproject_target)
            print(f"[OK] Restored pyproject.toml")

        # requirements.txt 복구
        requirements_backup = phase_dir / f"{checkpoint_id}_requirements.txt"
        if requirements_backup.exists():
            requirements_target = self.project_root / "requirements.txt"
            shutil.copy2(requirements_backup, requirements_target)
            print(f"[OK] Restored requirements.txt")

        # pip freeze 복구 (참고용)
        freeze_backup = phase_dir / f"{checkpoint_id}_pip_freeze.txt"
        if freeze_backup.exists():
            print(f"[INFO] Environment snapshot available at: {freeze_backup}")
            print("[INFO] To restore environment, run:")
            print(f"  pip install -r {freeze_backup}")

        return True

    def restore_data_files(self, phase: int, timestamp: str) -> bool:
        """
        데이터 파일 복구

        Args:
            phase: Phase 번호
            timestamp: 체크포인트 타임스탬프

        Returns:
            성공 여부
        """
        checkpoint_id = f"phase{phase}_{timestamp}"
        backup_dir = BACKUPS_DIR / "data" / f"phase{phase}" / checkpoint_id

        if not backup_dir.exists():
            print(f"[WARNING] Data backup directory not found: {backup_dir}")
            return False

        # 백업된 파일들을 원래 위치로 복구
        restored_count = 0
        for backup_file in backup_dir.rglob("*"):
            if backup_file.is_file():
                # 원본 경로 계산
                rel_path = backup_file.relative_to(backup_dir)
                target_path = self.project_root / rel_path

                # 디렉토리 생성
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # 파일 복사
                shutil.copy2(backup_file, target_path)
                restored_count += 1

        print(f"[OK] Restored {restored_count} data files")
        return True

    def verify_rollback(self, phase: int, checkpoint_id: Optional[str] = None) -> bool:
        """
        롤백 검증

        Args:
            phase: Phase 번호
            checkpoint_id: 체크포인트 ID

        Returns:
            검증 성공 여부
        """
        checkpoint = self.backup_manager.get_checkpoint(phase, checkpoint_id)
        if not checkpoint:
            print(f"[ERROR] Checkpoint not found")
            return False

        # Git 커밋 확인
        current_commit = self._get_git_commit()
        if checkpoint.git_commit and current_commit != checkpoint.git_commit:
            print(f"[WARNING] Git commit mismatch:")
            print(f"  Expected: {checkpoint.git_commit}")
            print(f"  Current: {current_commit}")
            return False

        # 의존성 파일 확인
        deps_backup = BACKUPS_DIR / "dependencies" / f"phase{phase}" / f"{checkpoint_id}_pyproject.toml"
        if deps_backup.exists():
            # 간단한 파일 크기 비교
            current_pyproject = self.project_root / "pyproject.toml"
            if current_pyproject.exists():
                if current_pyproject.stat().st_size != deps_backup.stat().st_size:
                    print("[WARNING] pyproject.toml size mismatch")
                    return False

        print("[OK] Rollback verification passed")
        return True

    def _restore_from_git(self, commit_hash: str) -> bool:
        """
        Git 커밋으로 코드 복구

        Args:
            commit_hash: Git 커밋 해시

        Returns:
            성공 여부
        """
        try:
            # Git 저장소 확인
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[WARNING] Not a Git repository, skipping Git rollback")
            return True  # Git이 없어도 계속 진행

        try:
            # 커밋 존재 확인
            subprocess.run(
                ["git", "cat-file", "-e", commit_hash],
                check=True,
                cwd=self.project_root,
                capture_output=True,
            )

            # 작업 디렉토리 상태 확인
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )

            if result.stdout.strip():
                print("[WARNING] Working directory has uncommitted changes")
                response = input("Continue with rollback? (y/N): ")
                if response.lower() != "y":
                    return False

            # 특정 커밋으로 체크아웃 (detached HEAD)
            subprocess.run(
                ["git", "checkout", commit_hash],
                check=True,
                cwd=self.project_root,
            )

            print(f"[OK] Restored code from Git commit: {commit_hash[:8]}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Git rollback failed: {e}")
            return False

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
    parser = argparse.ArgumentParser(description="롤백 관리자")
    parser.add_argument(
        "--phase",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="Phase 번호 (1, 2, 3)",
    )
    parser.add_argument(
        "--checkpoint-id",
        type=str,
        help="체크포인트 ID (None이면 최신 것)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 롤백 없이 시뮬레이션만",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="롤백 검증만 수행",
    )

    args = parser.parse_args()

    manager = RollbackManager()

    if args.verify:
        success = manager.verify_rollback(args.phase, args.checkpoint_id)
        sys.exit(0 if success else 1)

    success = manager.rollback_phase(
        phase=args.phase,
        checkpoint_id=args.checkpoint_id,
        dry_run=args.dry_run,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

