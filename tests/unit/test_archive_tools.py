from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sdvmm.services import archive_tools


def test_extract_rar_archive_hides_console_window_on_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    seven_zip = tmp_path / "tools" / "7zip" / "7z.exe"
    seven_zip.parent.mkdir(parents=True, exist_ok=True)
    seven_zip.write_text("", encoding="utf-8")

    archive_path = tmp_path / "package.rar"
    archive_path.write_text("rar", encoding="utf-8")
    destination = tmp_path / "out"

    monkeypatch.setattr(archive_tools.os, "name", "nt", raising=False)
    monkeypatch.setattr(
        archive_tools.subprocess,
        "CREATE_NO_WINDOW",
        0x08000000,
        raising=False,
    )
    monkeypatch.setattr(archive_tools.subprocess, "run", _fake_run)
    monkeypatch.setattr(archive_tools, "_bundled_7zip_executable", lambda: seven_zip)

    archive_tools.extract_archive_to_directory(
        archive_path=archive_path,
        destination=destination,
    )

    assert captured["command"] == [
        str(seven_zip),
        "x",
        str(archive_path),
        f"-o{destination}",
        "-y",
    ]
    assert captured["creationflags"] == 0x08000000


def test_extract_rar_archive_uses_system_7zip_on_non_windows_when_bundled_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    archive_path = tmp_path / "package.rar"
    archive_path.write_text("rar", encoding="utf-8")
    destination = tmp_path / "out"

    monkeypatch.setattr(archive_tools.os, "name", "posix", raising=False)
    monkeypatch.setattr(archive_tools.subprocess, "run", _fake_run)
    monkeypatch.setattr(
        archive_tools,
        "_bundled_7zip_executable",
        lambda: tmp_path / "missing-bundled-7zip",
    )
    monkeypatch.setattr(archive_tools.shutil, "which", lambda name: "/usr/bin/7z")

    archive_tools.extract_archive_to_directory(
        archive_path=archive_path,
        destination=destination,
    )

    assert captured["command"] == [
        "/usr/bin/7z",
        "x",
        str(archive_path),
        f"-o{destination}",
        "-y",
    ]
    assert "creationflags" not in captured


def test_extract_rar_archive_raises_when_no_7zip_is_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive_path = tmp_path / "package.rar"
    archive_path.write_text("rar", encoding="utf-8")
    destination = tmp_path / "out"

    monkeypatch.setattr(archive_tools.os, "name", "posix", raising=False)
    monkeypatch.setattr(
        archive_tools,
        "_bundled_7zip_executable",
        lambda: tmp_path / "missing-bundled-7zip",
    )
    monkeypatch.setattr(archive_tools.shutil, "which", lambda name: None)

    with pytest.raises(archive_tools.ArchiveToolError) as exc_info:
        archive_tools.extract_archive_to_directory(
            archive_path=archive_path,
            destination=destination,
        )

    assert "RAR support needs 7-Zip" in str(exc_info.value)
