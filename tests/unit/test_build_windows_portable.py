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
