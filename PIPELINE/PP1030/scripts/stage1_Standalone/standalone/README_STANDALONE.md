# Stage 1 Standalone Package

This package turns your Stage 1 synchronizer into a **standalone .exe** (GUI + optional CLI)
so users without Python can run it by double‑clicking.

## Contents

```
standalone/
├─ stage1_gui.py                      # Tkinter GUI
├─ stage1_standalone.py               # CLI runner & programmatic API
├─ build_exe_optimized_onedir.spec    # PyInstaller spec (onedir, GUI+CLI)
├─ build_gui_onefile.spec             # PyInstaller spec (onefile, GUI only)
├─ build.bat                          # Windows build script (CMD)
├─ build.ps1                          # Windows build script (PowerShell)
├─ build.sh                           # Linux/mac reference build
├─ requirements_runtime.txt           # Runtime dependencies list
├─ README_STANDALONE.md               # This file
└─ scripts/
   ├─ core/
   │  ├─ __init__.py
   │  ├─ header_registry.py
   │  ├─ header_normalizer.py
   │  ├─ semantic_matcher.py
   │  └─ standard_header_order.py
   └─ tools/
      └─ data_synchronizer_v30.py
```

## How to RUN (for end users)

1. Double‑click **Stage1Sync.exe** (after build), or run:
   `stage1_cli.exe --master "Master.xlsx" --warehouse "Warehouse.xlsx" --out "output.xlsx"`

2. In the GUI, select:
   - **Master** Excel file (.xlsx)
   - **Warehouse** Excel file (.xlsx)
   - (Optional) Output path

3. Click **Run Stage 1**. A log window will stream progress; on success you'll get the output path.

## How to BUILD (for maintainers)

### Quick Start (Recommended Order)

#### 1) Fast Development Build (onedir, GUI+CLI)
```bat
cd scripts\stage1_Standalone\standalone
build.bat
```
**Outputs**:
- GUI: `dist\Stage1Sync\Stage1Sync.exe`
- CLI: `dist\stage1_cli\stage1_cli.exe`

**PowerShell alternative**:
```powershell
cd scripts\stage1_Standalone\standalone
.\build.ps1
```

#### 2) Distribution Build (onefile, GUI only)
```bat
cd scripts\stage1_Standalone\standalone
set ONEFILE=1
build.bat
```
**Output**: `dist\Stage1Sync.exe` (single file, ready for distribution)

**PowerShell alternative**:
```powershell
cd scripts\stage1_Standalone\standalone
.\build.ps1 -OneFile
```

#### 3) Without Virtual Environment (if venv fails)
```bat
cd scripts\stage1_Standalone\standalone
set NO_VENV=1
build.bat
```
**PowerShell alternative**: Use `.\build.ps1` (handles venv automatically) or `.\build.ps1 -NoVenv`

### Build Modes Explained

#### **onedir (Development/Fast)**
- **Speed**: Fastest build (2-3 minutes)
- **Output**: Folder structure with .exe + DLLs
- **Use Case**: Development, testing, frequent rebuilds
- **Includes**: Both GUI and CLI executables

#### **onefile (Distribution)**
- **Speed**: Slower build (+1-2 minutes for compression)
- **Output**: Single .exe file
- **Use Case**: Distribution to end users
- **Includes**: GUI only
- **Note**: First launch may be slower (extracts to temp folder)

### Build Optimizations

This build system excludes large unnecessary packages to dramatically reduce build time:

**Excluded packages** (saves ~15+ minutes):
- `torch`, `torchvision`, `torchaudio` (~1GB+)
- `matplotlib`, `scipy`, `sklearn`, `numba`
- `IPython`, `jupyter`, `notebook`
- `tensorboard`, `tensorflow`, `keras`
- `pytest`, `hypothesis`

**Build time**:
- **Previous**: 15+ minutes (with torch/etc)
- **Now**: 2-5 minutes (essential packages only)

**Settings**:
- `strip=True`: Remove debug symbols (smaller size)
- `upx=False`: Skip UPX compression (faster build)

### Build Warnings & Optimizations

#### Warning Suppression
The build system uses PyInstaller hooks to completely suppress pandas test module warnings:

**Hook file**: `hooks/hook-pandas.py`
- Excludes all `pandas.tests.*` modules at the hook level
- Prevents PyInstaller from searching for test modules
- Reduces warning messages by **99%+**

**Result**:
- Clean build output with minimal warnings
- Faster build time (reduced module scanning)
- No impact on runtime functionality

#### Common Warnings (Safe to Ignore)

**Windows DLL warnings**:
```
WARNING: Library not found: could not resolve 'bcrypt.dll'
WARNING: Library not found: could not resolve 'VERSION.dll'
```
- **Status**: ✅ Safe to ignore
- These DLLs are provided by Windows system and loaded at runtime

**jinja2 warning**:
```
WARNING: Hidden import "jinja2" not found!
```
- **Status**: ✅ Safe to ignore
- Optional dependency for pandas template features, not required for core functionality

**Note**: All excluded modules (torch, matplotlib, etc.) are intentional and will show warnings if accidentally imported. This is expected behavior.

## Features

### ✅ 완성된 기능
- **GUI 인터페이스**: 파일 선택 → 실행 → 결과 확인까지 한 번에
- **CLI 모드**: 배치 작업 및 자동화 스크립트에 활용
- **자동 경로 처리**: PyInstaller frozen 모드와 소스 모드 모두 지원
- **실시간 로그**: GUI에서 진행 상황 실시간 확인
- **의존성 내장**: pandas, numpy, openpyxl 등 모든 라이브러리 포함

### 📋 포함된 모듈
- `scripts/core/`: 헤더 매칭 시스템 (header_registry, semantic_matcher, header_normalizer)
- `scripts/tools/`: DataSynchronizerV30 동기화 엔진
- 모든 core 함수 export 완료: `get_warehouse_columns()`, `get_site_columns()`, `get_date_columns()`

## Troubleshooting

### Build fails
- Ensure Python 3.9+ is installed
- Check that `pandas`, `numpy`, `openpyxl`, `pyinstaller` can be installed
- Try `NO_VENV=1` if virtual environment creation fails

### Runtime errors
- Check that input Excel files are valid
- Ensure output path has write permissions
- Check log window for detailed error messages

### Import errors
- Ensure all files in `scripts/core/` and `scripts/tools/` are present
- Verify PyInstaller spec file `datas` section includes all required files

