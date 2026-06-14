# -*- coding: utf-8 -*-
# PowerShell script for checking auto-detection
# 사용법: .\run\check_autodetect.ps1

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "HVDC File Auto-Detection Check" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

python -c @"
from pathlib import Path
from scripts.core.file_registry import FileRegistry

root = Path('.').resolve()
reg = FileRegistry(root)

print("HE  :", reg.get_raw_with_canonical("HE"))
print("SIM :", reg.get_raw_with_canonical("SIM"))
"@

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Check complete!" -ForegroundColor Green

