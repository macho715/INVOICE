# -*- coding: utf-8 -*-
"""
Stage 1 Standalone Runner
- Thin wrapper around scripts.tools.data_synchronizer_v30.DataSynchronizerV30
- Safe imports inside frozen (PyInstaller) bundles using sys._MEIPASS
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

def _project_root() -> Path:
    # When frozen by PyInstaller, resources are unpacked to _MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Source mode: this file lives in standalone/, project root is its folder
    return Path(__file__).resolve().parent

def _ensure_path():
    root = _project_root()
    # Make 'scripts' importable (scripts/core, scripts/tools)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "scripts"))
    sys.path.insert(0, str(root / "scripts" / "tools"))
    sys.path.insert(0, str(root / "scripts" / "core"))

_ensure_path()

def _load_sync_class():
    from scripts.tools.data_synchronizer_v30 import DataSynchronizerV30
    return DataSynchronizerV30

class _Tee:
    def __init__(self, orig, cb=None):
        self.orig = orig
        self.cb = cb
    def write(self, s):
        if self.orig:
            self.orig.write(s)
        if self.cb:
            try: self.cb(s)
            except Exception: pass
    def flush(self):
        if self.orig:
            self.orig.flush()

def run_sync(master: str, warehouse: str, out: str | None = None, log_cb=None):
    DataSynchronizerV30 = _load_sync_class()
    sync = DataSynchronizerV30()
    orig_out, orig_err = sys.stdout, sys.stderr
    sys.stdout = _Tee(orig_out, log_cb)
    sys.stderr = _Tee(orig_err, log_cb)
    try:
        res = sync.synchronize(master, warehouse, out or None)
        return bool(res.success), str(res.output_path), dict(res.stats or {})
    finally:
        sys.stdout, sys.stderr = orig_out, orig_err

def main():
    ap = argparse.ArgumentParser(description="Stage 1 Synchronizer (Standalone)")
    ap.add_argument("--master", required=True, help="Path to Master Excel file (.xlsx)")
    ap.add_argument("--warehouse", required=True, help="Path to Warehouse Excel file (.xlsx)")
    ap.add_argument("--out", default="", help="Optional output path (.xlsx)")
    args = ap.parse_args()
    ok, out_path, _ = run_sync(args.master, args.warehouse, args.out or None)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()