from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PUBLIC_DIST_SLUG = "cinderleaf"
PUBLIC_BINARY_NAME = "Cinderleaf"


def _archive_dist_folder(dist_path: Path) -> Path:
    archive_path = dist_path.parent / f"{dist_path.name}.tar.gz"
    if archive_path.exists():
        archive_path.unlink()
    produced = Path(
        shutil.make_archive(
            base_name=str(dist_path),
            format="gztar",
            root_dir=str(dist_path.parent),
            base_dir=dist_path.name,
        )
    )
    return produced


def _write_sha256(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path = Path(f"{path}.sha256")
    checksum_path.write_text(f"{digest} *{path.name}\n", encoding="utf-8")
    return checksum_path


def main() -> int:
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Linux portable builds are only supported on Linux hosts.")

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_path = repo_root / "pyproject.toml"
    spec_path = repo_root / "packaging" / "sdvmm_linux_portable.spec"

    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    version = project["version"]
    dist_path = repo_root / "dist" / f"{PUBLIC_DIST_SLUG}-{version}-linux-portable"
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
    subprocess.run(command, cwd=repo_root, check=True)

    packaged_binary = dist_path / PUBLIC_BINARY_NAME
    platforms_dir_candidates = (
        dist_path / "_internal" / "PySide6" / "plugins" / "platforms",
        dist_path / "_internal" / "PySide6" / "Qt" / "plugins" / "platforms",
    )
    selected_platforms_dir: Path | None = None
    platform_plugins: list[str] = []
    for candidate in platforms_dir_candidates:
        candidate_plugins = sorted(path.name for path in candidate.glob("libq*.so"))
        if candidate_plugins:
            selected_platforms_dir = candidate
            platform_plugins = candidate_plugins
            break

    if not packaged_binary.exists():
        raise RuntimeError(f"Packaged Linux binary was not found: {packaged_binary}")
    if selected_platforms_dir is None:
        searched = ", ".join(str(path) for path in platforms_dir_candidates)
        raise RuntimeError(
            "Qt Linux platform plugins are missing from packaged output. "
            f"Searched: {searched}"
        )

    archive_path = _archive_dist_folder(dist_path)
    checksum_path = _write_sha256(archive_path)

    print(packaged_binary)
    print(selected_platforms_dir)
    print(dist_path)
    print(archive_path)
    print(checksum_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
