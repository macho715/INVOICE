# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('openpyxl')

datas = []
# Include configs if they exist one directory up from this file
# PyInstaller spec files don't have __file__, use current working directory
# (should be standalone/ folder when running pyinstaller)
BASE = os.path.abspath(os.getcwd())

for fname in [
    'pipeline_config.yaml',
    'project_profile.yaml',
    'stage2_derived_config.yaml',
    'stage4_anomaly.yaml',
]:
    fpath = os.path.abspath(os.path.join(BASE, '..', fname))
    if os.path.exists(fpath):
        # Put at root of bundle
        datas.append((fpath, '.'))

# Include our scripts package tree so relative imports work when frozen
datas += [
    ('scripts/core/__init__.py', 'scripts/core'),
    ('scripts/core/header_registry.py', 'scripts/core'),
    ('scripts/core/semantic_matcher.py', 'scripts/core'),
    ('scripts/core/standard_header_order.py', 'scripts/core'),
    ('scripts/core/header_normalizer.py', 'scripts/core'),
    ('scripts/tools/data_synchronizer_v30.py', 'scripts/tools'),
]

a = Analysis(
    ['stage1_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Stage1Sync',
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # GUI
    disable_windowed_traceback=True,
)

# Optional CLI exe
a_cli = Analysis(
    ['stage1_standalone.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_cli = PYZ(a_cli.pure, a_cli.zipped_data, cipher=block_cipher)
exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    a_cli.binaries,
    a_cli.zipfiles,
    a_cli.datas,
    [],
    name='stage1_cli',
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(exe_gui, exe_cli, name='dist')


