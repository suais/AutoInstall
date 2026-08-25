# -*- mode: python ; coding: utf-8 -*-
"""AutoInstall.spec - PyInstaller 打包配置"""

import os

block_cipher = None

# PyInstaller 标准变量：SPECPATH 是 spec 文件所在目录
# assets 目录在项目根目录
assets_dir = os.path.join(SPECPATH, "assets")
icon_path = os.path.join(assets_dir, "icon.ico")

# 检查图标是否存在
if not os.path.exists(icon_path):
    print(f"警告: 图标文件不存在: {icon_path}")
    icon_path = None

# PyInstaller hidden imports
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "pywinauto",
    "pywinauto.findwindows",
    "pywinauto.controls",
    "pywinauto.application",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
]

a = Analysis(
    [os.path.join(SPECPATH, "src", "main.py")],
    pathex=[SPECPATH],
    binaries=[],
    datas=[
        # 将 assets 文件夹复制到 _MEIPASS/assets
        (assets_dir, "assets"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PyQt5",
        "PyQt6",
    ],
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
    name="AutoInstall",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
