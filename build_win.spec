# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec - Windows 可执行文件
参照喜报项目：显式打包 VC++ 运行时 DLL，避免 failed to load python dll
"""

import glob
import os
import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

img2pdf_datas, img2pdf_binaries, img2pdf_hidden = collect_all("img2pdf")

vc_runtime_binaries = []
python_dir = os.path.dirname(sys.executable)
for dll_name in [
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140.dll",
    "concrt140.dll",
    "vccorlib140.dll",
    "ucrtbase.dll",
]:
    for search_dir in [python_dir, os.path.join(python_dir, "DLLs"), r"C:\Windows\System32"]:
        dll_path = os.path.join(search_dir, dll_name)
        if os.path.exists(dll_path):
            vc_runtime_binaries.append((dll_path, "."))
            print(f"[FOUND] {dll_name} -> {dll_path}")
            break

for search_dir in [python_dir, os.path.join(python_dir, "DLLs")]:
    for pattern in ["api-ms-win-crt-*.dll", "api-ms-win-core-*.dll"]:
        for dll in glob.glob(os.path.join(search_dir, pattern)):
            vc_runtime_binaries.append((dll, "."))
            print(f"[FOUND] {os.path.basename(dll)}")

a = Analysis(
    ["convert.py"],
    pathex=[],
    binaries=vc_runtime_binaries + img2pdf_binaries,
    datas=img2pdf_datas,
    hiddenimports=[
        "img2pdf",
        "processor",
        "encodings.utf_8",
        "encodings.gbk",
        "encodings.mbcs",
    ]
    + img2pdf_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="ImageToPDF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",
)
