@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set ONEFILE=%ONEFILE%
if "%ONEFILE%"=="" set ONEFILE=0
set NO_VENV=%NO_VENV%
if "%NO_VENV%"=="" set NO_VENV=0

if "%NO_VENV%"=="0" (
  if not exist .venv (
    python -m venv .venv || exit /b 1
  )
  call .venv\Scripts\activate.bat || exit /b 1
)

python -m pip install --upgrade pip wheel setuptools || exit /b 1
python -m pip install pandas numpy openpyxl pyinstaller || exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Note: --exclude-module options are not valid with .spec files
REM Excludes are already defined in the spec files
set EXC=--clean --noconfirm

if "%ONEFILE%"=="1" (
  pyinstaller %EXC% build_gui_onefile.spec || exit /b 1
) else (
  pyinstaller %EXC% build_exe_optimized_onedir.spec || exit /b 1
)

echo.
echo Build finished. See .\dist\
if "%ONEFILE%"=="1" (
  echo - GUI (onefile): .\dist\Stage1Sync.exe
) else (
  echo - GUI  : .\dist\Stage1Sync\Stage1Sync.exe
  echo - CLI  : .\dist\stage1_cli\stage1_cli.exe
)
exit /b 0

