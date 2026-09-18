from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from sdvmm.app import main as app_main
from sdvmm.ui import main_window


def test_resolve_app_version_prefers_runtime_version_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "app-version.txt").write_text("1.1.7\n", encoding="utf-8")

    monkeypatch.setattr(app_main, "_resolve_runtime_root", lambda: runtime_root)
    monkeypatch.setattr(app_main, "version", lambda _name: "0.2.1")

    assert app_main._resolve_app_version() == "1.1.7"


def test_resolve_app_version_prefers_pyproject_for_source_runs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "repo"
    runtime_root.mkdir()
    (runtime_root / "pyproject.toml").write_text(
        """
[project]
name = "stardew-mod-manager"
    version = "1.1.7"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(app_main, "_resolve_runtime_root", lambda: runtime_root)
    monkeypatch.setattr(app_main, "version", lambda _name: "0.2.1")

    assert app_main._resolve_app_version() == "1.1.7"


def test_resolve_runtime_icon_asset_prefers_svg_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    assets_root = runtime_root / "assets"
    assets_root.mkdir(parents=True)
    (assets_root / "cinderleaf-icon.svg").write_text("<svg />", encoding="utf-8")
    (assets_root / "app-icon.png").write_bytes(b"png")
    (assets_root / "cinderleaf.ico").write_bytes(b"ico")

    monkeypatch.setattr(app_main, "_resolve_runtime_root", lambda: runtime_root)

    assert app_main._resolve_runtime_icon_asset_path() == assets_root / "cinderleaf-icon.svg"


def test_single_instance_lock_rejects_second_copy_and_releases_cleanly(tmp_path: Path) -> None:
    state_file = tmp_path / "state" / "app-state.json"
    first = app_main._try_acquire_single_instance_lock(state_file)
    assert first is not None
    try:
        assert app_main._try_acquire_single_instance_lock(state_file) is None
    finally:
        first.unlock()

    replacement = app_main._try_acquire_single_instance_lock(state_file)
    assert replacement is not None
    replacement.unlock()


def test_resolve_ui_app_version_prefers_qapplication_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    original_version = app.applicationVersion()
    app.setApplicationVersion("1.1.7")
    try:
        monkeypatch.setattr(main_window, "package_version", lambda _name: "0.2.1")
        monkeypatch.setattr(
            main_window.Path,
            "resolve",
            lambda self: Path("/no-pyproject-here/src/sdvmm/ui/main_window.py"),
        )
        assert main_window._resolve_ui_app_version() == "1.1.7"
    finally:
        app.setApplicationVersion(original_version)


def test_startup_wires_crash_reporting_to_a_localized_dialog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    from sdvmm.app.i18n import LANGUAGE_PORTUGUESE_BRAZIL, UiLocalizer, set_active_ui_localizer

    shown: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "sdvmm.app.main.QMessageBox.warning",
        lambda _parent, title, text: shown.append((str(title), str(text))),
    )
    original_hook = sys.excepthook
    previous_localizer = None
    try:
        from sdvmm.app.i18n import get_active_ui_localizer

        previous_localizer = get_active_ui_localizer()
        set_active_ui_localizer(UiLocalizer.from_preference(LANGUAGE_PORTUGUESE_BRAZIL))
        state_file = tmp_path / "sdvmm" / "app-state.json"
        app_main._install_crash_reporting(state_file=state_file, app_version="1.6.0")

        try:
            raise RuntimeError("synthetic failure")
        except RuntimeError:
            sys.excepthook(*sys.exc_info())  # type: ignore[arg-type]
    finally:
        sys.excepthook = original_hook
        if previous_localizer is not None:
            set_active_ui_localizer(previous_localizer)

    reports = list((tmp_path / "sdvmm" / "crash-reports").glob("crash-*.txt"))
    assert len(reports) == 1
    assert "RuntimeError: synthetic failure" in reports[0].read_text(encoding="utf-8")
    assert len(shown) == 1
    title, text = shown[0]
    assert title == "Algo deu errado", "the dialog follows the interface language"
    assert str(reports[0]) in text