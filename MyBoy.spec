# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['MyBoy.py'],
    pathex=[],
    binaries=[],
    datas=[('images/1.gif', '.'), ('images/2.gif', '.'), ('images/3.gif', '.'), ('images/4.gif', '.'), ('images/5.gif', '.'), ('images/dialog.png', '.'), ('configs/items_config.json', '.'),('configs/career_config.json', '.'),('configs/exercise_config.json', '.'),('configs/play_config.json', '.'),('configs/study_config.json', '.'),('configs/work_config.json', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MyBoy',
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
    icon=['images/icon.ico'],
)
