"""Fetch the exact Qt/PySide source archives shipped with the Windows release.

The hashes are from Qt's official mirrorlist pages for version 6.11.2. Keep
this list in sync with the binaries in the portable build when upgrading Qt.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import urlopen

from PySide6 import __version__ as pyside_version

QT_VERSION = "6.11.2"
SOURCE_ARCHIVES = (
    (
        "qtbase-everywhere-src-6.11.2.tar.xz",
        "https://download.qt.io/archive/qt/6.11/6.11.2/submodules/qtbase-everywhere-src-6.11.2.tar.xz",
        "5b2e00eccaf5a4d8c14134ffa0ea8dfd0a35ae1ffc7f8d87fa4305a1ed23cf22",
    ),
    (
        "qtsvg-everywhere-src-6.11.2.tar.xz",
        "https://download.qt.io/archive/qt/6.11/6.11.2/submodules/qtsvg-everywhere-src-6.11.2.tar.xz",
        "d594337feca84c26fb67fe87b85e6a5c12fda404b611d905f9d138210c311876",
    ),
    (
        "pyside-setup-everywhere-src-6.11.2.tar.xz",
        "https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/pyside-setup-everywhere-src-6.11.2.tar.xz",
        "cba47efbaad1bedd529725cbc14e21f156c7a19366f07b3edfbb076ffd7afdf8",
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fetch_verified(name: str, url: str, expected_sha256: str, directory: Path) -> Path:
    destination = directory / name
    if destination.is_file() and _sha256(destination) == expected_sha256:
        return destination

    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f"{name}.part"
    try:
        with urlopen(url, timeout=120) as response, temporary.open("wb") as output:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                output.write(chunk)
        actual_sha256 = _sha256(temporary)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"Qt source hash mismatch for {name}: expected {expected_sha256}, got {actual_sha256}"
            )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def main() -> int:
    if pyside_version != QT_VERSION:
        raise RuntimeError(
            f"Qt source list is for {QT_VERSION}, but installed PySide6 is {pyside_version}"
        )
    directory = Path(__file__).resolve().parents[1] / "dist" / "release-sources"
    for name, url, expected_sha256 in SOURCE_ARCHIVES:
        print(_fetch_verified(name, url, expected_sha256, directory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
