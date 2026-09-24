from __future__ import annotations

import hashlib
import importlib.metadata
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PUBLIC_DIST_SLUG = "cinderleaf"
PUBLIC_EXE_NAME = "Cinderleaf.exe"
BUNDLED_QT_VERSION = "6.11.2"


def _build_environment() -> dict[str, str]:
    """Keep unrelated tools on the caller's PATH out of PyInstaller's DLL scan."""
    environment = os.environ.copy()
    if sys.platform != "win32":
        return environment

    windows_root = Path(environment.get("SystemRoot", r"C:\Windows"))
    search_roots = (
        Path(sys.executable).parent,
        Path(sys.base_prefix),
        windows_root / "System32",
        windows_root,
    )
    environment["PATH"] = os.pathsep.join(
        str(path) for path in dict.fromkeys(search_roots) if path.is_dir()
    )
    return environment


def _archive_dist_folder(dist_path: Path) -> Path:
    zip_path = dist_path.parent / f"{dist_path.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(
        base_name=str(dist_path),
        format="zip",
        root_dir=str(dist_path.parent),
        base_dir=dist_path.name,
    )
    return zip_path


def _write_sha256(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path = Path(f"{path}.sha256")
    checksum_path.write_text(f"{digest} *{path.name}\n", encoding="utf-8")
    return checksum_path


def _copy_license(repo_root: Path, dist_path: Path) -> Path:
    """Include the required license terms and notice with the portable app."""
    destination = dist_path / "LICENSE.txt"
    shutil.copyfile(repo_root / "LICENSE", destination)
    return destination


def _pyinstaller_license() -> Path:
    distribution = importlib.metadata.distribution("pyinstaller")
    for package_path in distribution.files or ():
        if str(package_path).replace("\\", "/").endswith("licenses/COPYING.txt"):
            return Path(distribution.locate_file(package_path))
    raise RuntimeError("PyInstaller bootloader license was not found")


def _copy_third_party_licenses(
    repo_root: Path,
    dist_path: Path,
    *,
    python_license: Path | None = None,
    pyinstaller_license: Path | None = None,
) -> Path:
    notice = dist_path / "THIRD_PARTY_NOTICES.txt"
    shutil.copyfile(repo_root / "packaging" / "THIRD_PARTY_NOTICES.txt", notice)
    license_dir = dist_path / "licenses"
    license_dir.mkdir(exist_ok=True)
    for name in ("LGPL-3.0.txt", "GPL-3.0.txt"):
        shutil.copyfile(repo_root / "packaging" / "licenses" / name, license_dir / name)
    shutil.copyfile(
        python_license or Path(sys.base_prefix) / "LICENSE.txt",
        license_dir / "PYTHON-LICENSE.txt",
    )
    shutil.copyfile(
        pyinstaller_license or _pyinstaller_license(),
        license_dir / "PYINSTALLER-COPYING.txt",
    )
    return notice


def _check_excluded_qt_components(dist_path: Path) -> None:
    """Fail rather than publish unused GPL-only Qt Virtual Keyboard binaries."""
    forbidden = {"qt6virtualkeyboard.dll", "qtvirtualkeyboardplugin.dll"}
    found = [
        path for path in dist_path.rglob("*.dll") if path.name.lower() in forbidden
    ]
    if found:
        raise RuntimeError(f"Unused Qt Virtual Keyboard binary in portable build: {found[0]}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject_path = repo_root / "pyproject.toml"
    spec_path = repo_root / "packaging" / "sdvmm_windows_portable.spec"

    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    bundled_qt_version = importlib.metadata.version("PySide6")
    if bundled_qt_version != BUNDLED_QT_VERSION:
        raise RuntimeError(
            f"Portable notices/sources cover Qt {BUNDLED_QT_VERSION}, "
            f"but installed PySide6 is {bundled_qt_version}"
        )
    version = project["version"]
    dist_path = repo_root / "dist" / f"{PUBLIC_DIST_SLUG}-{version}-windows-portable"
    work_path = repo_root / "build" / "pyinstaller"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        f"--distpath={repo_root / 'dist'}",
        f"--workpath={work_path}",
        str(spec_path),
    ]
    subprocess.run(command, cwd=repo_root, env=_build_environment(), check=True)
    packaged_exe = dist_path / PUBLIC_EXE_NAME
    qwindows_plugin = (
        dist_path
        / "_internal"
        / "PySide6"
        / "plugins"
        / "platforms"
        / "qwindows.dll"
    )
    if not packaged_exe.exists():
        raise RuntimeError(f"Packaged executable not found: {packaged_exe}")
    if not qwindows_plugin.exists():
        raise RuntimeError(
            "Qt Windows platform plugin is missing from packaged output: "
            f"{qwindows_plugin}"
        )

    _check_excluded_qt_components(dist_path)

    license_path = _copy_license(repo_root, dist_path)
    third_party_notice = _copy_third_party_licenses(repo_root, dist_path)

    # Authenticode signing belongs here, after the EXE exists and before the
    # portable folder is zipped and hashed for release distribution.
    zip_path = _archive_dist_folder(dist_path)
    checksum_path = _write_sha256(zip_path)

    print(packaged_exe)
    print(qwindows_plugin)
    print(license_path)
    print(third_party_notice)
    print(dist_path)
    print(zip_path)
    print(checksum_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
