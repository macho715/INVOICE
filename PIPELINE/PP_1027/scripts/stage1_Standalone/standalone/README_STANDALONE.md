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
└─ scripts/
   ├─ core/
   │  ├─ __init__.py
   │  ├─ header_registry.py
   │  ├─ header_normalizer.py         # minimal implementation
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
cd standalone
build.bat
```
**Outputs**:
- GUI: `dist\Stage1Sync\Stage1Sync.exe`
- CLI: `dist\stage1_cli\stage1_cli.exe`

**PowerShell alternative**:
```powershell
cd standalone
.\build.ps1
```

#### 2) Distribution Build (onefile, GUI only)
```bat
build.bat ONEFILE=1
```
**Output**: `dist\Stage1Sync.exe` (single file, ready for distribution)

**PowerShell alternative**:
```powershell
.\build.ps1 -OneFile
```

#### 3) Without Virtual Environment (if venv fails)
```bat
build.bat NO_VENV=1
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

## Notes & Troubleshooting

### 일반 문제 해결
- **Import 오류**: `get_warehouse_columns()`, `get_site_columns()` export 확인 완료 ✅
- **경로 오류**: standalone 환경에서 자동 경로 처리 완료 ✅
- **대용량 파일**: `openpyxl`이 큰 파일에서 문제 발생 시 충분한 RAM 확인 및 CLI 모드 사용
- **아이콘 추가**: spec 파일의 `EXE(...)` 블록에 `icon='icon.ico'` 추가, 동일 폴더에 `icon.ico` 배치

### 빌드 관련 문제

#### **Still seeing large hook logs (torch/matplotlib)?**
- Check if any module has static imports like `import torch`
- Use guard clauses:
  ```python
  try:
      import torch  # pragma: no cover
  except Exception:
      torch = None
  ```

#### **PowerShell venv activation fails?**
- Use `.\build.ps1` (uses `Activate.ps1` automatically)
- Or use `build.bat NO_VENV=1` (skips venv)

#### **OneFile startup is slow?**
- Normal behavior (extracts to temp folder on first launch)
- For development, use onedir mode instead

#### **Want to reduce size further?**
- pandas/openpyxl are core dependencies; minimal room for reduction
- Check `requirements_runtime.txt` for minimal dependencies

### 커스터마이징 팁
- **헤더 탐지**: `scripts/core/__init__.py`의 `detect_header_row()` 함수를 프로젝트 고유 로직으로 교체 가능
- **드래그 & 드롭**: 기본 tkinter 사용 (호환성 우선). tkdnd 추가 설치 시 확장 가능

### 빌드 오류 해결
- **PyInstaller 오류**: `pip install --upgrade pyinstaller` 실행
- **의존성 누락**: `hiddenimports`에 필요한 모듈 추가 (spec 파일)
- **Timeout warnings**: Should be gone with optimized excludes; if still present, check system Python environment

## Build Checklist

After build:
1. ✅ **Verify GUI**: Double-click GUI exe → File selection works
2. ✅ **Verify CLI**: Run `stage1_cli.exe --help` → Shows usage
3. ✅ **Test with real files**: Use actual Master/Warehouse files
4. ✅ **Check log output**: No hook-torch/hook-matplotlib/hook-scipy lines
5. ✅ **Test on clean PC** (optional): Copy to PC without Python → Should run

## License

Internal use for HVDC project. Files under `scripts/core` originate from your project modules.
