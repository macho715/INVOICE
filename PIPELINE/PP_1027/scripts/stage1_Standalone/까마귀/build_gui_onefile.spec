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
exe = EXE(
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
    onefile=True,
)