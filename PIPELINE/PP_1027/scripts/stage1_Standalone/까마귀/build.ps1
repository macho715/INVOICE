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

$commonOpts = @(
  "--clean","--noconfirm",
  "--exclude-module","torch","--exclude-module","torchvision","--exclude-module","torchaudio",
  "--exclude-module","matplotlib","--exclude-module","scipy","--exclude-module","sklearn",
  "--exclude-module","IPython","--exclude-module","jupyter","--exclude-module","notebook",
  "--exclude-module","tensorboard","--exclude-module","tensorflow","--exclude-module","keras",
  "--exclude-module","pytest","--exclude-module","hypothesis","--exclude-module","numba"
)

if ($OneFile) {
  pyinstaller @commonOpts "build_gui_onefile.spec"
} else {
  pyinstaller @commonOpts "build_exe_optimized_onedir.spec"
}

Pop-Location