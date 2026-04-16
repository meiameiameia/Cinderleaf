# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import tomllib


ROOT = Path(SPECPATH).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
PROJECT = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
VERSION = PROJECT["version"]
DIST_NAME = f"cinderleaf-{VERSION}-linux-portable"
APP_ICON_SVG = ROOT / "assets" / "cinderleaf-icon.svg"
APP_ICON_PNG = ROOT / "assets" / "app-icon.png"
APP_VERSION_FILE = ROOT / "build" / "app-version.txt"

APP_VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
APP_VERSION_FILE.write_text(f"{VERSION}\n", encoding="utf-8")

datas = [
    (str(APP_ICON_SVG), "assets"),
    (str(APP_ICON_PNG), "assets"),
    (str(APP_VERSION_FILE), "."),
]

a = Analysis(
    [str(ROOT / "src" / "sdvmm" / "app" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "packaging" / "pyi_rth_qt_paths.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Cinderleaf",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=DIST_NAME,
    contents_directory="_internal",
)
