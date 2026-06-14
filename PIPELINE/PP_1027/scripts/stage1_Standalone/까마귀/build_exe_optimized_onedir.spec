# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('openpyxl')

excludes = [
    'torch', 'torchvision', 'torchaudio',
    'matplotlib', 'scipy', 'sklearn', 'numba',
    'IPython', 'jupyter', 'notebook', 'nbformat', 'nbconvert',
    'tensorboard', 'tensorflow', 'keras', 'protobuf',
    'pytest', 'hypothesis', 'pluggy', 'py',
]

datas = [
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
    excludes=excludes,
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
    strip=True,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
)

a_cli = Analysis(
    ['stage1_standalone.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
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
    strip=True,
    upx=False,
    console=True,
)

coll = COLLECT(exe_gui, exe_cli, name='dist')