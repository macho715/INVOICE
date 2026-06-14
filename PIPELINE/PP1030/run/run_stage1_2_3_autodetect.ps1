# -*- coding: utf-8 -*-
# PowerShell script for running Stage 1, 2, 3 with auto-detection
# 사용법: .\run\run_stage1_2_3_autodetect.ps1

param(
    [switch]$SkipCheck,
    [string]$Stages = "1,2,3"
)

$ErrorActionPreference = "Stop"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "HVDC Pipeline - Stage 1, 2, 3 Execution" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 1. 사전 점검 (선택)
if (-not $SkipCheck) {
    Write-Host "[1/3] Checking auto-detection..." -ForegroundColor Yellow
    python -c @"
from pathlib import Path
from scripts.core.file_registry import FileRegistry

root = Path('.').resolve()
reg = FileRegistry(root)

he_result = reg.get_raw_with_canonical("HE")
sim_result = reg.get_raw_with_canonical("SIM")

if he_result:
    print(f"✓ HE  : {he_result[0]} ({he_result[1]})")
else:
    print("✗ HE  : Not found")
    exit(1)

if sim_result:
    print(f"✓ SIM : {sim_result[0]} ({sim_result[1]})")
else:
    print("⚠ SIM : Not found (optional)")
"@
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Auto-detection failed. Please check data/raw folder." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# 2. 파이프라인 실행
Write-Host "[2/3] Running pipeline stages: $Stages" -ForegroundColor Yellow
python .\run\run_pipeline.py --stage $Stages

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Pipeline execution failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/3] Pipeline execution completed!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan

