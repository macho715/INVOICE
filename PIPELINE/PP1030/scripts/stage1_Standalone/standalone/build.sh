#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller

pyinstaller --clean --noconfirm build_exe_optimized_onedir.spec

echo
echo "Build finished. See ./dist/"
echo "- GUI  : ./dist/Stage1Sync/Stage1Sync"
echo "- CLI  : ./dist/stage1_cli/stage1_cli"

