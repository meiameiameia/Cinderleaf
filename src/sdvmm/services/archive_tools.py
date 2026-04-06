from __future__ import annotations

from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

SUPPORTED_PACKAGE_SUFFIXES = (".zip", ".rar")


class ArchiveToolError(ValueError):
    """Raised when a supported package archive cannot be processed safely."""


def is_supported_package_archive(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_PACKAGE_SUFFIXES


def list_supported_package_archives(root: Path) -> list[Path]:
    return [
        item
        for item in sorted(
            root.rglob("*"),
            key=lambda path: str(path.relative_to(root)).lower(),
        )
        if item.is_file() and is_supported_package_archive(item)
    ]


def extract_archive_to_directory(*, archive_path: Path, destination: Path) -> None:
    suffix = archive_path.suffix.lower()
    if suffix == ".zip":
        _extract_zip_archive_to_directory(archive_path=archive_path, destination=destination)
        return
    if suffix == ".rar":
        _extract_rar_archive_to_directory(archive_path=archive_path, destination=destination)
        return
    raise ArchiveToolError(f"Unsupported package archive type: {archive_path.suffix}")


def extract_archive_root_to_directory(
    *,
    archive_path: Path,
    source_root: str,
    destination: Path,
) -> None:
    suffix = archive_path.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as archive:
            _extract_zip_root(archive=archive, source_root=source_root, destination=destination)
        return

    with tempfile.TemporaryDirectory(prefix="sdvmm-archive-") as temp_dir:
        extracted_root = Path(temp_dir)
        extract_archive_to_directory(archive_path=archive_path, destination=extracted_root)
        _copy_extracted_root(
            extracted_root=extracted_root,
            source_root=source_root,
            destination=destination,
        )


def _extract_zip_archive_to_directory(*, archive_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive_path, "r") as archive:
        _extract_zip_root(archive=archive, source_root=".", destination=destination)


def _extract_zip_root(
    *,
    archive: zipfile.ZipFile,
    source_root: str,
    destination: Path,
) -> None:
    root = PurePosixPath(source_root)
    destination_resolved = destination.resolve()
    for info in sorted(archive.infolist(), key=lambda item: item.filename.lower()):
        normalized = _normalize_archive_member(info.filename)
        if normalized is None:
            continue
        if source_root != ".":
            try:
                relative = normalized.relative_to(root)
            except ValueError:
                continue
        else:
            relative = normalized
        if not relative.parts:
            continue
        target_path = destination / Path(*relative.parts)
        target_resolved = target_path.resolve()
        if not target_resolved.is_relative_to(destination_resolved):
            raise ArchiveToolError(f"Unsafe package entry path: {info.filename}")
        if info.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info, "r") as source, target_path.open("wb") as destination_file:
            shutil.copyfileobj(source, destination_file)


def _extract_rar_archive_to_directory(*, archive_path: Path, destination: Path) -> None:
    seven_zip_path = _bundled_7zip_executable()
    if not seven_zip_path.exists():
        raise ArchiveToolError(
            f"Bundled 7-Zip executable is missing for RAR support: {seven_zip_path}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [str(seven_zip_path), "x", str(archive_path), f"-o{destination}", "-y"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown extraction error"
        raise ArchiveToolError(f"Could not extract RAR package: {detail}")


def _copy_extracted_root(
    *,
    extracted_root: Path,
    source_root: str,
    destination: Path,
) -> None:
    root = PurePosixPath(source_root)
    if any(part == ".." for part in root.parts):
        raise ArchiveToolError(f"Unsafe package entry path: {source_root}")
    source_path = extracted_root if source_root == "." else extracted_root.joinpath(*root.parts)
    if not source_path.exists():
        raise ArchiveToolError(f"Package root '{source_root}' was not found after extraction.")
    for child in sorted(source_path.iterdir(), key=lambda item: item.name.lower()):
        target_path = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target_path)
        else:
            shutil.copy2(child, target_path)


def _normalize_archive_member(filename: str) -> PurePosixPath | None:
    normalized = filename.replace("\\", "/").lstrip("/")
    if not normalized:
        return None
    path = PurePosixPath(normalized)
    if any(part == ".." for part in path.parts):
        raise ArchiveToolError(f"Unsafe package entry path: {filename}")
    return path


def _bundled_7zip_executable() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "tools" / "7zip" / "7z.exe"
    return Path(__file__).resolve().parents[3] / "assets" / "tools" / "7zip" / "7z.exe"
