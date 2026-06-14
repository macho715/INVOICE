"""
Pre-install checks for Python compatibility and dependency conflicts.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


LIBRARIES_TO_VALIDATE = {
    "pandera": {
        "min_version": "0.18.0",
        "python_min": (3, 8),
        "note": "Verify Python 3.13 support.",
    },
    "prefect": {
        "min_version": "2.14.0",
        "python_min": (3, 8),
        "note": "Verify Python 3.13 support.",
    },
    "structlog": {
        "min_version": "24.1.0",
        "python_min": (3, 8),
        "note": "Expected to support Python 3.13.",
    },
    "rich": {
        "min_version": "13.7.0",
        "python_min": (3, 8),
        "note": "Expected to support Python 3.13.",
    },
    "hypothesis": {
        "min_version": "6.92.0",
        "python_min": (3, 8),
        "note": "Verify Python 3.13 support.",
    },
    "duckdb": {
        "min_version": "0.10.0",
        "python_min": (3, 8),
        "note": "Verify Python 3.13 support.",
    },
    "diskcache": {
        "min_version": "5.6.0",
        "python_min": (3, 8),
        "note": "Expected to support Python 3.13.",
    },
    "joblib": {
        "min_version": "1.3.0",
        "python_min": (3, 8),
        "note": "Expected to support Python 3.13.",
    },
}


def format_version(version_tuple: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version_tuple)


def run_pip_dry_run(args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--dry-run", "--disable-pip-version-check", *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return False, f"pip dry-run failed: {exc}"

    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def check_library(lib_name: str, config: dict, python_version: tuple[int, int, int]) -> bool:
    print(f"\n[{lib_name}]")
    print(f"  min version: {config['min_version']}")
    print(f"  python min: {format_version(config['python_min'])}")
    print(f"  note: {config['note']}")

    if python_version < config["python_min"]:
        print("  FAIL: Python version is below the minimum.")
        return False

    requirement = f"{lib_name}>={config['min_version']}"
    ok, _ = run_pip_dry_run([requirement])
    if ok:
        print("  OK: installable via pip dry-run.")
        return True

    print("  FAIL: pip dry-run could not resolve this requirement.")
    return False


def check_requirements_file(requirements_path: Path) -> bool:
    if not requirements_path.exists():
        print(f"\nRequirements file not found: {requirements_path}")
        return False

    print(f"\n[requirements] {requirements_path}")
    ok, output = run_pip_dry_run(["-r", str(requirements_path)])
    if ok:
        print("  OK: pip dry-run resolved requirements.")
        return True

    print("  FAIL: pip dry-run could not resolve requirements.")
    if output:
        preview = "\n".join(output.splitlines()[:15])
        print("  pip output (first 15 lines):")
        print(preview)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Python 3.13 compatibility and pip resolution.")
    parser.add_argument(
        "--requirements",
        default="requirements.txt",
        help="Path to requirements file to validate with pip dry-run.",
    )
    parser.add_argument(
        "--skip-extras",
        action="store_true",
        help="Skip validation of extra libraries listed in this script.",
    )
    args = parser.parse_args()

    python_version = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    print(f"Python version: {format_version(python_version)}")
    if python_version < (3, 13, 0):
        print("WARNING: Python 3.13+ recommended for this validation.")
    else:
        print("OK: Python 3.13+ detected.")

    results: dict[str, bool] = {}
    if not args.skip_extras:
        print("\n" + "=" * 60)
        print("Extra library validation")
        print("=" * 60)
        for lib_name, config in LIBRARIES_TO_VALIDATE.items():
            results[lib_name] = check_library(lib_name, config, python_version)

    print("\n" + "=" * 60)
    print("Requirements file validation")
    print("=" * 60)
    requirements_ok = check_requirements_file(Path(args.requirements))

    if results:
        all_extras_ok = all(results.values())
    else:
        all_extras_ok = True

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    if results:
        for lib_name, ok in results.items():
            status = "OK" if ok else "FAIL"
            print(f"{status}: {lib_name}")
    print(f"{'OK' if requirements_ok else 'FAIL'}: requirements file")

    if all_extras_ok and requirements_ok:
        print("\nAll checks passed.")
        return 0

    print("\nSome checks failed. Consider adjusting versions or using Python 3.12.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
