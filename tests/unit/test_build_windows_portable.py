from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from scripts import build_windows_portable


@pytest.mark.skipif(sys.platform != "win32", reason="Windows build environment")
def test_build_environment_ignores_unrelated_path_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unrelated_tools = tmp_path / "unrelated-tools"
    unrelated_tools.mkdir()
    monkeypatch.setenv("PATH", str(unrelated_tools))

    environment = build_windows_portable._build_environment()

    assert str(unrelated_tools) not in environment["PATH"].split(os.pathsep)
    assert str(Path(sys.executable).parent) == environment["PATH"].split(os.pathsep)[0]
    assert "System32" in environment["PATH"]


def test_copy_license_keeps_required_notice_in_portable_folder(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    dist_path = tmp_path / "portable"
    repo_root.mkdir()
    dist_path.mkdir()
    terms = "Required Notice: Copyright (c) 2026 Cinderleaf contributors\nLicense terms\n"
    (repo_root / "LICENSE").write_text(terms, encoding="utf-8")

    copied = build_windows_portable._copy_license(repo_root, dist_path)

    assert copied == dist_path / "LICENSE.txt"
    assert copied.read_text(encoding="utf-8") == terms


def test_portable_build_rejects_virtual_keyboard_binary(tmp_path: Path) -> None:
    qt_path = tmp_path / "_internal" / "PySide6"
    qt_path.mkdir(parents=True)
    (qt_path / "Qt6VirtualKeyboard.dll").write_bytes(b"test")

    with pytest.raises(RuntimeError, match="Qt Virtual Keyboard"):
        build_windows_portable._check_excluded_qt_components(tmp_path)


def test_copy_third_party_licenses_into_portable_folder(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    packaging = repo_root / "packaging"
    license_sources = packaging / "licenses"
    license_sources.mkdir(parents=True)
    (packaging / "THIRD_PARTY_NOTICES.txt").write_text("Qt notice", encoding="utf-8")
    for name in ("LGPL-3.0.txt", "GPL-3.0.txt"):
        (license_sources / name).write_text(name, encoding="utf-8")
    python_license = tmp_path / "python-license.txt"
    python_license.write_text("Python license", encoding="utf-8")
    pyinstaller_license = tmp_path / "pyinstaller-license.txt"
    pyinstaller_license.write_text("PyInstaller license", encoding="utf-8")
    portable = tmp_path / "portable"
    portable.mkdir()

    notice = build_windows_portable._copy_third_party_licenses(
        repo_root,
        portable,
        python_license=python_license,
        pyinstaller_license=pyinstaller_license,
    )

    assert notice.read_text(encoding="utf-8") == "Qt notice"
    assert (portable / "licenses" / "LGPL-3.0.txt").read_text() == "LGPL-3.0.txt"
    assert (portable / "licenses" / "GPL-3.0.txt").read_text() == "GPL-3.0.txt"
    assert (portable / "licenses" / "PYTHON-LICENSE.txt").read_text() == "Python license"
    assert (portable / "licenses" / "PYINSTALLER-COPYING.txt").read_text() == "PyInstaller license"
