# tools/config_validator.py
# Py 3.11.8
from __future__ import annotations

import argparse
import os
import glob
import json
import sys
import datetime as dt

try:
    import yaml  # pip install pyyaml
except Exception:
    yaml = None


def load_yaml(path: str) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML 미설치: pip install pyyaml 필요")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def norm(p: str) -> str:
    return (p or "").replace("/", os.sep)


def resolve(root: str, p: str) -> str:
    p2 = norm(p)
    if os.path.isabs(p2) or p2.startswith("\\\\"):
        return p2
    return os.path.join(root, p2)


def check_path(root: str, p: str) -> dict:
    if not p:
        return {"ok": True, "type": "EMPTY", "detail": ""}
    rp = resolve(root, p)
    has_glob = any(ch in rp for ch in ["*", "?", "["])
    if has_glob:
        m = glob.glob(rp)
        return {"ok": len(m) > 0, "type": "WILDCARD", "detail": f"{len(m)} matches", "resolved": rp}
    return {"ok": os.path.exists(rp), "type": "FILE", "detail": "exists" if os.path.exists(rp) else "missing", "resolved": rp}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project_root", required=True)
    ap.add_argument("--pipeline_yaml", required=True)
    ap.add_argument("--stage2_yaml", required=True)
    ap.add_argument("--stage4_yaml", required=True)
    ap.add_argument("--out_json", required=True)
    args = ap.parse_args()

    root = os.path.abspath(args.project_root)

    res = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "project_root": root, "checks": []}

    try:
        pipe = load_yaml(args.pipeline_yaml)
        st2 = load_yaml(args.stage2_yaml)
        st4 = load_yaml(args.stage4_yaml)

        # pipeline_config: stage1 + stage3
        stg = (pipe.get("stages") or {})
        st1 = stg.get("stage1") or {}
        st3 = stg.get("stage3") or {}

        st1io = (st1.get("io") or {})
        st3io = (st3.get("io") or {})

        res["checks"].append({"name": "pipeline_yaml_exists", "ok": os.path.exists(args.pipeline_yaml), "path": args.pipeline_yaml})
        res["checks"].append({"name": "stage2_yaml_exists", "ok": os.path.exists(args.stage2_yaml), "path": args.stage2_yaml})
        res["checks"].append({"name": "stage4_yaml_exists", "ok": os.path.exists(args.stage4_yaml), "path": args.stage4_yaml})

        res["checks"].append({"name": "stage1.warehouse_file", **check_path(root, str(st1io.get("warehouse_file", "")))})
        res["checks"].append({"name": "stage1.output_file_dir", **check_path(root, os.path.dirname(str(st1io.get("output_file", ""))))})

        res["checks"].append({"name": "stage2.input.synced_file", **check_path(root, str(st2.get("input", {}).get("synced_file", "")))})
        res["checks"].append({"name": "stage2.output.derived_file_dir", **check_path(root, os.path.dirname(str(st2.get("output", {}).get("derived_file", ""))))})

        res["checks"].append({"name": "stage3.derived_file", **check_path(root, str(st3io.get("derived_file", "")))})
        res["checks"].append({"name": "stage3.report_file_pattern", **check_path(root, str(st3io.get("report_file", "")))})  # wildcard 가능

        st4io = (st4.get("stage4", {}).get("io") or {})
        res["checks"].append({"name": "stage4.input_file", **check_path(root, str(st4io.get("input_file", "")))})
        res["checks"].append({"name": "stage4.excel_output_dir", **check_path(root, os.path.dirname(str(st4io.get("excel_output", ""))))})
        res["checks"].append({"name": "stage4.json_output_dir", **check_path(root, os.path.dirname(str(st4io.get("json_output", ""))))})

        ok_all = all(bool(x.get("ok")) for x in res["checks"])
        res["ok_all"] = ok_all

    except Exception as e:
        res["ok_all"] = False
        res["error"] = str(e)

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    return 0 if res.get("ok_all") else 1


if __name__ == "__main__":
    raise SystemExit(main())

