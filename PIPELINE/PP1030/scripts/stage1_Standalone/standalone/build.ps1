param(
  [switch]$OneFile = $false,
  [ValidateSet("Both","GUI","CLI")]
  [string]$Target = "Both",
  [switch]$NoVenv = $false
)

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot

if (-not $NoVenv) {
  if (-not (Test-Path ".venv")) { python -m venv .venv }
  & ".\.venv\Scripts\Activate.ps1"
}

python -m pip install --upgrade pip wheel setuptools
python -m pip install pandas numpy openpyxl pyinstaller

Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue

# Note: --exclude-module options are not valid with .spec files
# Excludes are already defined in the spec files
$commonOpts = @("--clean", "--noconfirm")

if ($OneFile) {
  pyinstaller @commonOpts "build_gui_onefile.spec"
} else {
  pyinstaller @commonOpts "build_exe_optimized_onedir.spec"
}

Pop-Location

Write-Host ""
Write-Host "Build finished. See .\dist\"
if ($OneFile) {
  Write-Host "- GUI (onefile): .\dist\Stage1Sync.exe"
} else {
  Write-Host "- GUI  : .\dist\Stage1Sync\Stage1Sync.exe"
  Write-Host "- CLI  : .\dist\stage1_cli\stage1_cli.exe"
}

