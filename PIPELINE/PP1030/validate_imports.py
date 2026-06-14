"""
Post-install import and basic functionality checks.
"""

from __future__ import annotations

import importlib
import sys
from typing import Tuple


LIBRARIES = {
    "pandera": "pandera",
    "prefect": "prefect",
    "structlog": "structlog",
    "rich": "rich",
    "hypothesis": "hypothesis",
    "duckdb": "duckdb",
    "diskcache": "diskcache",
    "joblib": "joblib",
}


def test_import(lib_name: str, import_name: str | None = None) -> Tuple[bool, str]:
    if import_name is None:
        import_name = lib_name

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, str(version)
    except ImportError as exc:
        return False, f"ImportError: {exc}"
    except Exception as exc:
        return False, f"Unexpected error: {exc}"


def main() -> int:
    print("=" * 60)
    print("Library import validation")
    print("=" * 60)

    results: dict[str, bool] = {}
    for lib_name, import_name in LIBRARIES.items():
        success, info = test_import(lib_name, import_name)
        results[lib_name] = success
        status = "OK" if success else "FAIL"
        print(f"{status}: {lib_name} ({info})")

    print("\n" + "=" * 60)
    print("Basic functionality tests")
    print("=" * 60)

    if results.get("pandera"):
        try:
            import pandera as pa

            pa.DataFrameSchema({"col": pa.Column(int)})
            print("OK: pandera schema creation")
        except Exception as exc:
            print(f"FAIL: pandera schema creation: {exc}")

    if results.get("prefect"):
        try:
            from prefect import flow, task

            _ = flow
            _ = task
            print("OK: prefect flow/task import")
        except Exception as exc:
            print(f"FAIL: prefect flow/task import: {exc}")

    if results.get("structlog"):
        try:
            import structlog

            _ = structlog.get_logger()
            print("OK: structlog logger creation")
        except Exception as exc:
            print(f"FAIL: structlog logger creation: {exc}")

    if results.get("rich"):
        try:
            from rich.console import Console

            Console().print("OK: rich console output")
        except Exception as exc:
            print(f"FAIL: rich console output: {exc}")

    if results.get("duckdb"):
        try:
            import duckdb

            conn = duckdb.connect()
            result = conn.execute("SELECT 1").fetchone()
            print(f"OK: duckdb query execution ({result})")
        except Exception as exc:
            print(f"FAIL: duckdb query execution: {exc}")

    if results.get("joblib"):
        try:
            from joblib import Parallel, delayed

            values = Parallel(n_jobs=2)(delayed(lambda x: x * 2)(i) for i in range(3))
            print(f"OK: joblib parallel execution ({values})")
        except Exception as exc:
            print(f"FAIL: joblib parallel execution: {exc}")

    print("\n" + "=" * 60)
    all_pass = all(results.values()) if results else True
    if all_pass:
        print("All libraries imported successfully.")
        return 0

    print("One or more libraries failed to import.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
