# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for SystemAnalyzer
# Build with: pyinstaller build.spec

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'psutil',
        'wmi',
        'win32api',
        'win32con',
        'win32gui',
        'pywintypes',
        'send2trash',
        'concurrent.futures',
        'hashlib',
        'ctypes',
        'socket',
        'platform',
        'datetime',
        'string',
        'pathlib',
        'shutil',
        'urllib.request',
        'urllib.error',
        'packaging',
        'packaging.version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name='SystemAnalyzer',
    version='version_file.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
