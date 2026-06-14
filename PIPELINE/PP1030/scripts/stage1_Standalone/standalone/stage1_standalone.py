# -*- coding: utf-8 -*-
"""
Stage 1 Standalone Runner
- Thin wrapper around scripts.tools.data_synchronizer_v30.DataSynchronizerV30
- Safe imports inside frozen (PyInstaller) bundles using sys._MEIPASS
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Dict, Optional, Tuple

def _project_root() -> Path:
    # When frozen by PyInstaller, resources are unpacked to _MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Source mode: this file lives in standalone/, project root is its folder
    return Path(__file__).resolve().parent

def _ensure_path():
    root = _project_root()
    # Add scripts directory to path for imports
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        sys.path.insert(0, str(scripts_dir))
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "scripts" / "core"))

_ensure_path()

def _load_sync_class():
    from scripts.tools.data_synchronizer_v30 import DataSynchronizerV30
    return DataSynchronizerV30

class _Tee:
    def __init__(self, orig, cb=None):
        self.orig = orig
        self.cb = cb

    def write(self, data):
        if self.orig:
            self.orig.write(data)
        if self.cb:
            self.cb(data)

    def flush(self):
        if self.orig:
            self.orig.flush()

def run_sync(
    master: str,
    warehouse: str,
    out: str | None = None,
    header_overrides: Optional[Dict[Tuple[str, str], int]] = None,
    log_cb=None,
):
    DataSynchronizerV30 = _load_sync_class()
    sync = DataSynchronizerV30(header_overrides=header_overrides)
    orig_out, orig_err = sys.stdout, sys.stderr
    sys.stdout = _Tee(orig_out, log_cb)
    sys.stderr = _Tee(orig_err, log_cb)
    try:
        res = sync.synchronize(
            master,
            warehouse,
            out or None,
            header_overrides=header_overrides,
        )
        return bool(res.success), str(res.output_path), dict(res.stats or {})
    finally:
        sys.stdout, sys.stderr = orig_out, orig_err

def main():
    ap = argparse.ArgumentParser(description="Stage 1 Synchronizer (Standalone)")
    ap.add_argument("--master", required=True, help="Path to Master Excel file (.xlsx)")
    ap.add_argument("--warehouse", required=True, help="Path to Warehouse Excel file (.xlsx)")
    ap.add_argument("--out", default="", help="Optional output path (.xlsx)")
    ap.add_argument(
        "--header-override",
        action="append",
        default=[],
        help=(
            "Manual header row override (<file_label>:<sheet>=<row>, '*' allowed). "
            "Repeat flag for multiple overrides."
        ),
    )
    args = ap.parse_args()

    DataSynchronizerV30 = _load_sync_class()
    try:
        overrides = DataSynchronizerV30.parse_header_override_args(args.header_override)
    except ValueError as override_error:
        ap.error(str(override_error))

    ok, out_path, _ = run_sync(
        args.master,
        args.warehouse,
        args.out or None,
        header_overrides=overrides,
    )
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()

