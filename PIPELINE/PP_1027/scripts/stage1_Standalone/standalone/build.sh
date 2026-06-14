#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller

pyinstaller build_exe.spec --noconfirm

echo
echo "Build finished. See ./dist/Stage1Sync (GUI) and ./dist/stage1_cli (CLI)."