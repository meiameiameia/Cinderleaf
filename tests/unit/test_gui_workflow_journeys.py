"""Connected, headless GUI journeys over disposable synthetic folders.

These tests drive the real window and real services end to end. They never use
live game data, never reach the network, and fail instead of blocking when an
unexpected modal dialog would open.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sys
import time
import zipfile

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QMessageBox

from sdvmm.app.i18n import UiLocalizer
from sdvmm.app.shell_service import AppShellService
from sdvmm.app.shell_service import INSTALL_TARGET_SANDBOX_MODS
from sdvmm.domain.models import AppConfig
from sdvmm.services.app_state_store import save_app_config
from sdvmm.ui.main_window import MainWindow

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="GUI journeys share the Windows-specific GUI regression baseline.",
)

_YES = QMessageBox.StandardButton.Yes
_NO = QMessageBox.StandardButton.No


def _assert_headless(app: QApplication) -> None:
    assert os.environ.get("QT_QPA_PLATFORM", "").casefold() == "offscreen"
    assert app.platformName().casefold() == "offscreen", (
        "GUI journeys refuse to run on a platform that can show windows."
    )


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    _assert_headless(app)
    return app


class DialogScript:
    """Scripted answers for review confirmations, recording what was shown."""

    def __init__(self) -> None:
        self.answers: list[QMessageBox.StandardButton] = []
        self.questions: list[tuple[str, str]] = []
        self.notices: list[tuple[str, str, str]] = []
        self.text_inputs: list[tuple[str, bool]] = []

    def question(self, _window: MainWindow, *, title: str, text: str, **_: object):
        self.questions.append((title, text))
        # Unscripted confirmations take the safe default.
        return self.answers.pop(0) if self.answers else _NO

    def notice(self, kind: str):
        def _record(_parent, title: str, text: str, *_args, **_kwargs):
            self.notices.append((kind, str(title), str(text)))
            return QMessageBox.StandardButton.Ok

        return _record


@pytest.fixture
def dialogs(monkeypatch: pytest.MonkeyPatch) -> DialogScript:
    script = DialogScript()

    def _unexpected_modal(*_args, **_kwargs):
        raise AssertionError("An unscripted modal dialog would block the journey.")

    monkeypatch.setattr(QDialog, "exec", _unexpected_modal)
    monkeypatch.setattr(QMessageBox, "exec", _unexpected_modal)
    monkeypatch.setattr(QInputDialog, "exec", _unexpected_modal)
    for name in ("getExistingDirectory", "getOpenFileName", "getOpenFileNames", "getSaveFileName"):
        monkeypatch.setattr(QFileDialog, name, _unexpected_modal)
    for kind in ("critical", "warning", "information"):
        monkeypatch.setattr(f"sdvmm.ui.main_window.QMessageBox.{kind}", script.notice(kind))
    monkeypatch.setattr(
        MainWindow,
        "_show_localized_question_dialog",
        lambda self, **kwargs: script.question(self, **kwargs),
    )
    monkeypatch.setattr(
        MainWindow,
        "_ask_localized_yes_no",
        lambda self, title, text, **kwargs: script.question(self, title=title, text=text),
    )
    monkeypatch.setattr(
        MainWindow,
        "_show_localized_info_dialog",
        lambda self, *args, **kwargs: script.notices.append(("info", str(args), str(kwargs))),
    )

    def _text_input(self, *, title: str, prompt: str):
        value, accepted = script.text_inputs.pop(0)
        return value, accepted

    monkeypatch.setattr(MainWindow, "_ask_localized_text_input", _text_input)
    return script


@pytest.fixture(autouse=True)
def _isolated_user_folders(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # Services look for SMAPI logs, saves and defaults under these folders; keep
    # every journey away from the owner's real profile.
    profile = tmp_path / "isolated user profile"
    for variable, folder in (
        ("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local"), ("USERPROFILE", "Home"), ("XDG_CONFIG_HOME", "Config"),
    ):
        (profile / folder).mkdir(parents=True)
        monkeypatch.setenv(variable, str(profile / folder))
    return profile


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_args, **_kwargs):
        raise OSError("Network access is disabled in GUI journeys.")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def _write_manifest(folder: Path, *, name: str, unique_id: str, version: str, **extra: object) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {"Name": name, "Author": "Synthetic", "Version": version, "UniqueID": unique_id}
    manifest.update(extra)
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "content.json").write_text(json.dumps({"Format": "2.0.0", "Changes": []}), encoding="utf-8")
    return folder


def _folder_digest(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class SyntheticLibrary:
    LONG_NAME = "Village Conversations Expanded Seasonal Dialogue Collection"

    def __init__(self, root: Path) -> None:
        self.root = root
        self.game = root / "Stardew Valley Synthetic Game"
        self.real_mods = self.game / "Mods"
        self.sandbox_mods = root / "Sandbox Profile With Spaces" / "Mods"
        self.real_archive = root / "Archives" / "Real"
        self.sandbox_archive = root / "Archives" / "Sandbox"
        self.downloads = root / "Downloads"
        self.state_file = root / "state" / "app-state.json"
        for folder in (
            self.real_mods, self.sandbox_mods, self.real_archive, self.sandbox_archive, self.downloads,
        ):
            folder.mkdir(parents=True, exist_ok=True)
        (self.game / "StardewModdingAPI.exe").write_bytes(b"synthetic")

        _write_manifest(self.real_mods / "Garden", name="Seasonal Garden", unique_id="Syn.Garden", version="1.0.0")
        _write_manifest(
            self.real_mods / "VillageExpanded", name=self.LONG_NAME, unique_id="Syn.Village", version="2.0.0",
        )
        # A grouped multi-folder family: one entry in the library and Compare.
        _write_manifest(
            self.real_mods / "[Family] Farm Planner" / "[CP] Farm Planner",
            name="Farm Planner Content", unique_id="Syn.Planner.CP", version="1.2.0",
            ContentPackFor={"UniqueID": "Pathoschild.ContentPatcher"},
        )
        _write_manifest(
            self.real_mods / "[Family] Farm Planner" / "Farm Planner Core",
            name="Farm Planner Core", unique_id="Syn.Planner", version="1.2.0",
        )
        # Missing metadata: no update keys, no author.
        missing = self.real_mods / "Unlabelled"
        missing.mkdir()
        (missing / "manifest.json").write_text(
            json.dumps({"Name": "Unlabelled Mod", "Version": "0.1.0", "UniqueID": "Syn.Unlabelled"}),
            encoding="utf-8",
        )
        # A linked sibling family (shared update key and dependency), the layout
        # Compare sync moves as one logical selection.
        for parent, version in ((self.real_mods, "1.5.3"), (self.sandbox_mods, "1.4.10")):
            _write_manifest(
                parent / "[CC] Weather Wonders", name="[CC] Weather Wonders", unique_id="Kana.WeatherWonders.CC",
                version=version, UpdateKeys=["CurseForge:1016623"],
            )
            _write_manifest(
                parent / "[DLL] Weather Wonders", name="[DLL] Weather Wonders", unique_id="Kana.WeatherWonders.DLL",
                version=version, UpdateKeys=["CurseForge:1016623"],
                Dependencies=[{"UniqueID": "Kana.WeatherWonders.CC", "IsRequired": True}],
            )
        for index in range(18):
            _write_manifest(
                self.real_mods / f"Filler{index:02d}",
                name=f"Filler Mod {index:02d}", unique_id=f"Syn.Filler{index:02d}", version="1.0.0",
            )

        _write_manifest(self.sandbox_mods / "Garden", name="Seasonal Garden", unique_id="Syn.Garden", version="1.0.0")
        _write_manifest(
            self.sandbox_mods / "VillageExpanded", name=self.LONG_NAME, unique_id="Syn.Village", version="2.1.0",
        )
        _write_manifest(
            self.sandbox_mods / "SandboxOnly", name="Sandbox Only Tool", unique_id="Syn.SandboxOnly", version="0.5.0",
        )

        save_app_config(
            self.state_file,
            AppConfig(
                game_path=self.game,
                mods_path=self.real_mods,
                app_data_path=root / "state" / "data",
                sandbox_mods_path=self.sandbox_mods,
                sandbox_archive_path=self.sandbox_archive,
                real_archive_path=self.real_archive,
                watched_downloads_path=self.downloads,
                steam_auto_start_enabled=False,
            ),
        )

    def build_package(self, name: str, *, unique_id: str, version: str, folder: str) -> Path:
        package = self.downloads / f"{name}.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(
                f"{folder}/manifest.json",
                json.dumps({"Name": name, "Author": "Synthetic", "Version": version, "UniqueID": unique_id}),
            )
            archive.writestr(f"{folder}/content.json", json.dumps({"Format": "2.0.0", "Changes": []}))
        return package


@pytest.fixture
def library(tmp_path: Path) -> SyntheticLibrary:
    return SyntheticLibrary(tmp_path / "cinderleaf journeys")


def _open_window(library: SyntheticLibrary, qapp: QApplication, language: str = "en") -> MainWindow:
    window = MainWindow(
        shell_service=AppShellService(state_file=library.state_file),
        localizer=UiLocalizer.from_preference(language),
    )
    # Startup checks may contact remote services; journeys start them explicitly.
    window._startup_checks_scheduled = True
    window._startup_checks_completed = True
    window.resize(1366, 768)
    window.show()
    qapp.processEvents()
    return window


def _wait_until_idle(window: MainWindow, qapp: QApplication, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while True:
        qapp.processEvents()
        if window._active_operation_name is None:
            for _ in range(3):
                qapp.processEvents()
            return
        if time.monotonic() > deadline:
            raise AssertionError(f"{window._active_operation_name} did not finish in {timeout}s")
        time.sleep(0.01)


@pytest.fixture
def window(library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript):
    main_window = _open_window(library, qapp)
    yield main_window
    _wait_until_idle(main_window, qapp)
    main_window.close()
    qapp.processEvents()



def _row_by_name(table, name: str) -> int:
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is not None and item.text() == name:
            return row
    raise AssertionError(f"{name!r} is not in {table.objectName()}")


def _visible_names(table) -> list[str]:
    return [
        table.item(row, 0).text()
        for row in range(table.rowCount())
        if not table.isRowHidden(row)
    ]



def _scan_real(window: MainWindow, qapp: QApplication) -> None:
    window._context_tabs.setCurrentWidget(window._mods_page)
    window._scan_button.click()
    assert window._active_operation_name == "Scan"
    assert window._scan_button.isEnabled() is False
    _wait_until_idle(window, qapp)
    assert window._scan_button.isEnabled() is True


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_library_scan_filter_sort_select_and_profile_membership(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript, language: str,
) -> None:
    from sdvmm.ui.main_window import _ROLE_MOD_IS_ENABLED, _ROLE_MOD_IS_GROUPED, _ROLE_MOD_TOGGLEABLE

    window = _open_window(library, qapp, language)
    try:
        table = window._mods_table
        real_before = _folder_digest(library.real_mods)
        assert table.rowCount() == 0  # empty before the first scan

        _scan_real(window, qapp)
        names = _visible_names(table)
        # 26 manifests; the container family and the sibling family are one entry each.
        assert len(names) == 23
        assert names == sorted(names, key=str.casefold), "library must start A to Z"
        family = table.item(_row_by_name(table, "Farm Planner Core (+1 more)"), 0)
        assert family.data(_ROLE_MOD_IS_GROUPED) is True
        # Default mirrors the canonical library and cannot be edited.
        assert all(table.item(row, 0).data(_ROLE_MOD_TOGGLEABLE) is False for row in range(table.rowCount()))

        window._mods_filter_input.setText("village")
        qapp.processEvents()
        assert _visible_names(table) == [SyntheticLibrary.LONG_NAME]
        table.selectRow(_row_by_name(table, SyntheticLibrary.LONG_NAME))
        qapp.processEvents()
        assert SyntheticLibrary.LONG_NAME in window._inventory_update_guidance_label.text()
        window._mods_filter_input.setText("")
        qapp.processEvents()
        assert len(_visible_names(table)) == 23
        assert table.selectionModel().selectedRows()[0].row() == _row_by_name(table, SyntheticLibrary.LONG_NAME)

        header = table.horizontalHeader()
        header.setSortIndicator(0, Qt.SortOrder.DescendingOrder)
        qapp.processEvents()
        assert _visible_names(table) == sorted(names, key=str.casefold, reverse=True)
        header.setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        qapp.processEvents()

        # A cancelled profile name leaves everything as it was.
        dialogs.text_inputs.append(("", False))
        window._create_real_profile_button.click()
        _wait_until_idle(window, qapp)
        assert window._real_profile_combo.count() == 1

        dialogs.text_inputs.append(("Journey Profile", True))
        window._create_real_profile_button.click()
        _wait_until_idle(window, qapp)
        assert window._real_profile_combo.currentText() == "Journey Profile"
        # Custom profiles start empty.
        assert all(table.item(row, 0).data(_ROLE_MOD_IS_ENABLED) is False for row in range(table.rowCount()))

        def family_item():
            return table.item(_row_by_name(table, "Farm Planner Core (+1 more)"), 0)

        # The family's content pack needs a dependency this library lacks.
        dialogs.answers.append(_NO)
        family_item().setCheckState(Qt.CheckState.Checked)
        _wait_until_idle(window, qapp)
        assert family_item().data(_ROLE_MOD_IS_ENABLED) is False
        assert family_item().checkState() == Qt.CheckState.Unchecked
        assert "Pathoschild.ContentPatcher" in dialogs.questions[-1][1]
        profile_mods = next((library.game / "Cinderleaf" / "Profiles" / "Real Mods").glob("*/Mods"))
        assert list(profile_mods.iterdir()) == []

        dialogs.answers.append(_YES)
        family_item().setCheckState(Qt.CheckState.Checked)
        _wait_until_idle(window, qapp)
        assert family_item().data(_ROLE_MOD_IS_ENABLED) is True
        # One link carries the whole family into the profile.
        assert [path.name for path in profile_mods.iterdir()] == ["[Family] Farm Planner"]
        assert sorted(child.name for child in (profile_mods / "[Family] Farm Planner").iterdir()) == [
            "Farm Planner Core", "[CP] Farm Planner",
        ]

        family_item().setCheckState(Qt.CheckState.Unchecked)
        _wait_until_idle(window, qapp)
        assert family_item().data(_ROLE_MOD_IS_ENABLED) is False
        assert list(profile_mods.iterdir()) == []
        assert _folder_digest(library.real_mods) == real_before
        assert dialogs.notices == []
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()


def _queue_all_downloads_and_open_install(window: MainWindow, qapp: QApplication) -> None:
    window._context_tabs.setCurrentWidget(window._packages_page)
    window._start_watch_button.click()
    _wait_until_idle(window, qapp)
    window._on_watch_tick()
    _wait_until_idle(window, qapp)
    window._on_select_all_visible_package_queue_items()
    qapp.processEvents()
    assert window._plan_selected_intake_button.isEnabled()
    window._plan_selected_intake_button.click()
    _wait_until_idle(window, qapp)
    window._on_stop_watch()
    _wait_until_idle(window, qapp)


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_package_review_install_history_and_reviewed_recovery(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript, language: str,
) -> None:
    library.build_package("Seasonal Garden", unique_id="Syn.Garden", version="1.1.0", folder="Garden")
    library.build_package(
        "Harvest Moonlight Festival Lanterns", unique_id="Syn.Lanterns", version="3.0.0", folder="Lanterns",
    )
    window = _open_window(library, qapp, language)
    tr = window._tr
    try:
        sandbox_before = _folder_digest(library.sandbox_mods)
        real_before = _folder_digest(library.real_mods)
        assert window._package_queue_list.count() == 1  # the empty-queue placeholder
        _queue_all_downloads_and_open_install(window, qapp)
        assert window._context_tabs.currentWidget().objectName() == "review_workspace_page"
        assert window._current_install_target() == INSTALL_TARGET_SANDBOX_MODS

        # Without overwrite, the existing Garden target blocks the whole batch.
        window._plan_install_button.click()
        _wait_until_idle(window, qapp)
        assert window._pending_install_plan is None
        assert window._run_install_button.isEnabled() is False
        assert "Enable overwrite mode" in window._review_output_box.toPlainText()

        window._overwrite_checkbox.setChecked(True)
        window._plan_install_button.click()
        _wait_until_idle(window, qapp)
        plan = window._pending_install_plan
        assert plan is not None
        assert sorted(entry.action for entry in plan.entries) == ["install_new", "overwrite_with_archive"]
        assert "rolls back the whole batch" in window._review_output_box.toPlainText()

        # Review, then decline: nothing is written and the plan stays reviewable.
        dialogs.answers.append(_NO)
        window._run_install_button.click()
        _wait_until_idle(window, qapp)
        title, text = dialogs.questions[-1]
        assert title == tr("install.confirm.title")
        assert str(library.sandbox_mods) in text and str(library.sandbox_archive) in text
        assert tr("install.confirm.entries", count=2) in text
        assert _folder_digest(library.sandbox_mods) == sandbox_before
        assert window._status_strip_label.text() == tr("install.status.cancelled")
        assert window._pending_install_plan is plan

        dialogs.answers.append(_YES)
        window._run_install_button.click()
        # While applying, neither planning nor a second apply is offered.
        assert window._active_operation_name == "Install execution"
        assert window._run_install_button.isEnabled() is False
        assert window._plan_install_button.isEnabled() is False
        _wait_until_idle(window, qapp)
        installed = _folder_digest(library.sandbox_mods)
        assert set(installed) - set(sandbox_before) == {"Lanterns/manifest.json", "Lanterns/content.json"}
        assert b'"1.1.0"' in installed["Garden/manifest.json"]
        archived = next(library.sandbox_archive.glob("Garden__sdvmm_archive_*"))
        assert _folder_digest(archived) == {
            key.split("/", 1)[1]: value for key, value in sandbox_before.items() if key.startswith("Garden/")
        }
        assert _folder_digest(library.real_mods) == real_before
        assert window._pending_install_plan is None
        assert window._run_install_button.isEnabled() is False

        # History selects the new operation; recovery needs its own review.
        window._context_tabs.setCurrentWidget(window._history_page)
        _wait_until_idle(window, qapp)  # opening History refreshes archives first
        assert window._install_history_combo.currentData() is not None
        assert window._run_recovery_button.isEnabled() is False
        assert window._inspect_recovery_button.isEnabled() is True
        window._inspect_recovery_button.click()
        _wait_until_idle(window, qapp)
        assert window._run_recovery_button.isEnabled() is True
        ready = tr("recovery.review.ready.other", count=2)
        assert ready in window._recovery_output_box.toPlainText()

        dialogs.answers.append(_NO)
        window._run_recovery_button.click()
        _wait_until_idle(window, qapp)
        assert ready in dialogs.questions[-1][1]
        assert _folder_digest(library.sandbox_mods) == installed

        dialogs.answers.append(_YES)
        window._run_recovery_button.click()
        _wait_until_idle(window, qapp)
        # Recovery returns the sandbox exactly to its prior contents and keeps
        # the displaced copies as archives rather than deleting them.
        assert _folder_digest(library.sandbox_mods) == sandbox_before
        retained = sorted(path.name.split("__")[0] for path in library.sandbox_archive.glob("*__sdvmm_archive_*"))
        assert retained == ["Garden", "Lanterns"]
        assert window._run_recovery_button.isEnabled() is False
        window._inspect_recovery_button.click()
        _wait_until_idle(window, qapp)
        assert window._run_recovery_button.isEnabled() is False
        if language == "pt-BR":
            for _title, question in dialogs.questions:
                assert "Recovery plan is" not in question
                assert "Execute install now" not in question
        assert [notice for notice in dialogs.notices if notice[0] == "critical"] == []
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()


def test_install_rejects_a_package_changed_after_review(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript,
) -> None:
    package = library.build_package(
        "Harvest Moonlight Festival Lanterns", unique_id="Syn.Lanterns", version="3.0.0", folder="Lanterns",
    )
    window = _open_window(library, qapp)
    try:
        sandbox_before = _folder_digest(library.sandbox_mods)
        _queue_all_downloads_and_open_install(window, qapp)
        window._plan_install_button.click()
        _wait_until_idle(window, qapp)
        assert window._pending_install_plan is not None

        # The reviewed package is replaced on disk before the owner applies it.
        with zipfile.ZipFile(package, "a") as archive:
            archive.writestr("Lanterns/extra.json", "{}")
        dialogs.answers.append(_YES)
        window._run_install_button.click()
        _wait_until_idle(window, qapp)

        assert _folder_digest(library.sandbox_mods) == sandbox_before
        failures = [notice for notice in dialogs.notices if notice[0] == "critical"]
        assert len(failures) == 1
        assert window._pending_install_plan is None
        assert window._run_install_button.isEnabled() is False
        assert window._operation_state_label.text() == window._tr(
            "status.operation_failed", name="Install execution"
        )
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()



def _compare_rows(window: MainWindow) -> dict[str, str]:
    from sdvmm.ui.main_window import _ROLE_COMPARE_STATE

    table = window._compare_results_table
    return {
        table.item(row, 0).text(): table.item(row, 0).data(_ROLE_COMPARE_STATE)
        for row in range(table.rowCount())
        if not table.isRowHidden(row)
    }


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_compare_categories_reviews_and_permitted_sync_paths(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript, language: str,
) -> None:
    window = _open_window(library, qapp, language)
    tr = window._tr
    real_to_sandbox = window._compare_sync_real_to_sandbox_button
    sandbox_to_real = window._compare_sync_sandbox_to_real_button
    try:
        window._context_tabs.setCurrentWidget(window._compare_page)
        assert real_to_sandbox.isEnabled() is False and sandbox_to_real.isEnabled() is False
        window._compare_real_vs_sandbox_button.click()
        _wait_until_idle(window, qapp)

        combo = window._compare_category_filter_combo
        expected_states = [
            {"only_in_real", "only_in_sandbox", "version_mismatch", "ambiguous_match"},
            {"only_in_real"}, {"only_in_sandbox"}, {"version_mismatch"}, {"ambiguous_match"},
            {"same_version"},
        ]
        for index, allowed in enumerate(expected_states):
            combo.setCurrentIndex(index)
            qapp.processEvents()
            assert set(_compare_rows(window).values()) <= allowed, combo.currentText()
        combo.setCurrentIndex(combo.count() - 1)
        qapp.processEvents()
        rows = _compare_rows(window)
        assert rows[SyntheticLibrary.LONG_NAME] == "version_mismatch"
        assert rows["Weather Wonders (+1 more)"] == "version_mismatch"
        assert rows["Sandbox Only Tool"] == "only_in_sandbox"
        assert rows["Seasonal Garden"] == "same_version"

        table = window._compare_results_table
        real_before = _folder_digest(library.real_mods)
        sandbox_before = _folder_digest(library.sandbox_mods)

        def select(name: str) -> None:
            table.selectRow(_row_by_name(table, name))
            qapp.processEvents()

        select("Seasonal Garden")
        assert real_to_sandbox.isEnabled() is False and sandbox_to_real.isEnabled() is False

        # Each direction has its own review; declining both writes nothing.
        select(SyntheticLibrary.LONG_NAME)
        assert real_to_sandbox.isEnabled() and sandbox_to_real.isEnabled()
        dialogs.answers.extend([_NO, _NO])
        real_to_sandbox.click()
        _wait_until_idle(window, qapp)
        sandbox_to_real.click()
        _wait_until_idle(window, qapp)
        (_, to_sandbox_review), (_, to_real_review) = dialogs.questions[-2:]
        assert to_sandbox_review != to_real_review
        for review, source, target, archive in (
            (to_sandbox_review, library.real_mods, library.sandbox_mods, library.sandbox_archive),
            (to_real_review, library.sandbox_mods, library.real_mods, library.real_archive),
        ):
            # The dedicated source and destination lines name each side once.
            path_lines = [line for line in review.splitlines() if line.endswith(("\\Mods", "/Mods"))]
            assert [line.split(": ", 1)[1] for line in path_lines] == [str(source), str(target)]
            assert str(archive) in review
        assert _folder_digest(library.real_mods) == real_before
        assert _folder_digest(library.sandbox_mods) == sandbox_before

        # Permitted path 1: sandbox -> real replaces the real copy with an archive.
        dialogs.answers.append(_YES)
        sandbox_to_real.click()
        _wait_until_idle(window, qapp)
        real_after = _folder_digest(library.real_mods)
        assert real_after["VillageExpanded/manifest.json"] == sandbox_before["VillageExpanded/manifest.json"]
        archived = next(library.real_archive.glob("VillageExpanded__sdvmm_archive_*"))
        assert _folder_digest(archived)["manifest.json"] == real_before["VillageExpanded/manifest.json"]
        assert _compare_rows(window)[SyntheticLibrary.LONG_NAME] == "same_version"

        # Permitted path 2: the linked sibling family moves as one selection.
        select("Weather Wonders (+1 more)")
        dialogs.answers.append(_YES)
        real_to_sandbox.click()
        _wait_until_idle(window, qapp)
        sandbox_after = _folder_digest(library.sandbox_mods)
        for member in ("[CC] Weather Wonders", "[DLL] Weather Wonders"):
            assert sandbox_after[f"{member}/manifest.json"] == real_before[f"{member}/manifest.json"]
        assert sorted(p.name.split("__")[0] for p in library.sandbox_archive.glob("*__sdvmm_archive_*")) == [
            "[CC] Weather Wonders", "[DLL] Weather Wonders",
        ]
        assert _compare_rows(window)["Weather Wonders (+1 more)"] == "same_version"

        # Permitted path 3: a real-only mod is copied into sandbox as a new target.
        select("Unlabelled Mod")
        assert sandbox_to_real.isEnabled() is False
        dialogs.answers.append(_YES)
        real_to_sandbox.click()
        _wait_until_idle(window, qapp)
        assert _folder_digest(library.sandbox_mods / "Unlabelled") == _folder_digest(library.real_mods / "Unlabelled")

        # A container family is shown as one entry but is not offered for sync.
        select("Farm Planner Core (+1 more)")
        assert real_to_sandbox.isEnabled() is False
        assert real_to_sandbox.toolTip() == tr("compare.sync.container_family_unavailable")
        assert not (library.sandbox_mods / "[Family] Farm Planner").exists()
        assert [notice for notice in dialogs.notices if notice[0] == "critical"] == []
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_setup_backup_inspect_plan_cancel_and_reviewed_restore(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript,
    monkeypatch: pytest.MonkeyPatch, language: str,
) -> None:
    import shutil

    from sdvmm.app.shell_service import BackupBundleExportSelection

    window = _open_window(library, qapp, language)
    tr = window._tr
    exports = library.root / "Backups With Spaces"
    exports.mkdir()
    try:
        window._context_tabs.setCurrentWidget(window._setup_page)
        execute = window._execute_restore_import_button
        assert execute.isEnabled() is False

        monkeypatch.setattr(window, "_prompt_for_backup_export_artifacts", lambda: None)
        window._export_backup_button.click()
        assert window._status_strip_label.text() == tr("backup.status.export_cancelled")
        assert list(exports.iterdir()) == []

        monkeypatch.setattr(
            window,
            "_prompt_for_backup_export_artifacts",
            lambda: BackupBundleExportSelection(
                include_manager_state=True, include_managed_mods=True,
                include_archives=False, include_save_files=False,
            ),
        )
        monkeypatch.setattr(window, "_prompt_for_backup_export_target", lambda: (str(exports), "directory"))
        window._export_backup_button.click()
        _wait_until_idle(window, qapp)
        bundle = next(exports.iterdir())
        assert (bundle / "manifest.json").is_file()

        # Cancelling the bundle picker changes nothing.
        monkeypatch.setattr(window, "_prompt_for_backup_bundle_path", lambda: None)
        window._inspect_backup_button.click()
        assert window._status_strip_label.text() == tr("backup.status.inspection_cancelled")
        assert execute.isEnabled() is False

        # A folder that is not a bundle is reported and cannot be restored.
        not_a_bundle = library.root / "Not A Bundle"
        not_a_bundle.mkdir()
        monkeypatch.setattr(window, "_prompt_for_backup_bundle_path", lambda: not_a_bundle)
        window._inspect_backup_button.click()
        _wait_until_idle(window, qapp)
        dialogs.answers.append(_YES)
        execute.click()
        _wait_until_idle(window, qapp)
        assert not any(title == tr("restore.confirm.title") for title, _ in dialogs.questions)

        real_before = _folder_digest(library.real_mods)
        shutil.rmtree(library.real_mods / "Garden")
        dialogs.answers.clear()
        monkeypatch.setattr(window, "_prompt_for_backup_bundle_path", lambda: bundle)
        window._inspect_backup_button.click()
        _wait_until_idle(window, qapp)  # inspection
        _wait_until_idle(window, qapp)  # automatic planning queued after it
        assert execute.isEnabled() is True

        dialogs.answers.append(_NO)
        execute.click()
        _wait_until_idle(window, qapp)
        title, review = dialogs.questions[-1]
        assert title == tr("restore.confirm.title")
        assert tr("restore.confirm.bundle", path=bundle) in review
        assert tr("restore.confirm.write_target", path=library.real_mods / "Garden") in review
        assert tr("restore.confirm.mod_folders", count=1) in review
        assert window._status_strip_label.text() == tr("restore.status.cancelled")
        assert not (library.real_mods / "Garden").exists()

        dialogs.answers.append(_YES)
        execute.click()
        _wait_until_idle(window, qapp)
        assert _folder_digest(library.real_mods) == real_before
        if language == "pt-BR":
            assert "Restore/import will write" not in review
            assert "Mod folders to write" not in review
        assert [notice for notice in dialogs.notices if notice[0] == "critical"] == []
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()


def _discovery_result(query: str, *pairs: tuple[str, str]):
    from sdvmm.domain.discovery_codes import COMPATIBLE, DISCOVERY_SOURCE_NEXUS, SMAPI_COMPATIBILITY_LIST_PROVIDER
    from sdvmm.domain.models import ModDiscoveryEntry, ModDiscoveryResult

    return ModDiscoveryResult(
        query=query,
        provider=SMAPI_COMPATIBILITY_LIST_PROVIDER,
        results=tuple(
            ModDiscoveryEntry(
                name=name, unique_id=unique_id, author="Synthetic",
                provider=SMAPI_COMPATIBILITY_LIST_PROVIDER, source_provider=DISCOVERY_SOURCE_NEXUS,
                source_page_url=f"https://example.invalid/{unique_id}", compatibility_state=COMPATIBLE,
                compatibility_status="Compatible", compatibility_summary="Works with current SMAPI.",
            )
            for name, unique_id in pairs
        ),
    )


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_discover_states_and_smapi_troubleshooting_with_controlled_responses(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript,
    monkeypatch: pytest.MonkeyPatch, _isolated_user_folders: Path, language: str,
) -> None:
    import threading

    from sdvmm.app.shell_service import AppShellError

    window = _open_window(library, qapp, language)
    tr = window._tr
    state = window._discovery_results_state_label
    try:
        _scan_real(window, qapp)
        window._context_tabs.setCurrentWidget(window._discovery_page)
        assert state.text() == tr("discovery.state.optional")

        def unavailable(*, query_text):
            raise AppShellError("Synthetic provider outage.")

        # A first search that fails reports the failure, not an empty query.
        monkeypatch.setattr(window._shell_service, "search_mod_discovery", unavailable)
        window._discovery_query_input.setText("garden")
        window._search_mods_button.click()
        _wait_until_idle(window, qapp)
        assert state.isVisible()
        assert state.text() == tr("discovery.state.failed", message="Synthetic provider outage.")
        assert dialogs.notices[-1][0] == "critical"

        release = threading.Event()

        def slow_search(*, query_text):
            release.wait(5)
            return _discovery_result(query_text, ("Seasonal Garden", "Syn.Garden"), ("Brand New Mod", "Syn.New"))

        monkeypatch.setattr(window._shell_service, "search_mod_discovery", slow_search)
        window._search_mods_button.click()
        qapp.processEvents()
        assert state.text() == tr("discovery.state.searching")
        assert window._search_mods_button.isEnabled() is False
        assert window._discovery_query_input.isEnabled() is False
        release.set()
        _wait_until_idle(window, qapp)
        table = window._discovery_table
        assert _visible_names(table) == ["Brand New Mod", "Seasonal Garden"]
        assert state.text() == tr("discovery.summary_ready", count=2)
        assert window._search_mods_button.isEnabled() is True

        monkeypatch.setattr(window._shell_service, "search_mod_discovery", unavailable)
        window._discovery_query_input.setText("something else")
        window._search_mods_button.click()
        _wait_until_idle(window, qapp)
        assert state.text() == tr("discovery.state.failed_with_previous", message="Synthetic provider outage.")

        monkeypatch.setattr(
            window._shell_service, "search_mod_discovery", lambda *, query_text: _discovery_result(query_text),
        )
        window._search_mods_button.click()
        _wait_until_idle(window, qapp)
        assert table.rowCount() == 0
        assert state.text() == tr("discovery.state.no_results")

        # SMAPI troubleshooting: no log yet, then a log with a missing dependency.
        window._context_tabs.setCurrentWidget(window._mods_page)
        window._check_smapi_log_button.click()
        _wait_until_idle(window, qapp)
        not_found_summary = window._smapi_log_status_label.text()
        assert window._open_smapi_dependency_in_discover_button.isEnabled() is False

        logs = _isolated_user_folders / "Roaming" / "StardewValley" / "ErrorLogs"
        logs.mkdir(parents=True)
        (logs / "SMAPI-latest.txt").write_text(
            "\n".join(
                (
                    "[00:00:01 TRACE SMAPI] SMAPI 4.5.1 with Stardew Valley 1.6.15",
                    "[00:00:03 ERROR SMAPI] Unhandled exception in mod loader.",
                    "[00:00:04 TRACE SMAPI] Skipped mods",
                    "[00:00:05 TRACE SMAPI]    - Farm Planner Content because it needs mods which aren't "
                    "installed (Pathoschild.ContentPatcher)",
                )
            ),
            encoding="utf-8",
        )
        window._check_smapi_log_button.click()
        _wait_until_idle(window, qapp)
        assert window._smapi_log_status_label.text() != not_found_summary
        assert "Pathoschild.ContentPatcher" in window._smapi_log_status_label.toolTip()
        assert window._open_smapi_dependency_in_discover_button.isEnabled() is True

        searched: list[str] = []
        monkeypatch.setattr(
            window._shell_service,
            "search_mod_discovery",
            lambda *, query_text: (searched.append(query_text), _discovery_result(query_text, ("Content Patcher", "Pathoschild.ContentPatcher")))[1],
        )
        window._open_smapi_dependency_in_discover_button.click()
        _wait_until_idle(window, qapp)
        # The handoff prefills Discover; the owner starts the search.
        assert window._context_tabs.currentWidget() is window._discovery_page
        assert window._discovery_query_input.text() == "Pathoschild.ContentPatcher"
        assert searched == []
        window._search_mods_button.click()
        _wait_until_idle(window, qapp)
        assert searched == ["Pathoschild.ContentPatcher"]
        assert _visible_names(window._discovery_table) == ["Content Patcher"]
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()

def test_populated_state_survives_navigation_resize_and_language_change(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript,
) -> None:
    window = _open_window(library, qapp, "en")
    try:
        _scan_real(window, qapp)
        table = window._mods_table
        window._mods_filter_input.setText("filler")
        qapp.processEvents()
        filtered = _visible_names(table)
        assert len(filtered) == 18
        table.selectRow(_row_by_name(table, "Filler Mod 07"))
        header = table.horizontalHeader()
        header.setSortIndicator(0, Qt.SortOrder.DescendingOrder)
        qapp.processEvents()
        window._context_tabs.setCurrentWidget(window._compare_page)
        window._compare_real_vs_sandbox_button.click()
        _wait_until_idle(window, qapp)
        compare_rows_before = _compare_rows(window)

        def selected_name() -> str:
            rows = table.selectionModel().selectedRows()
            assert len(rows) == 1
            return table.item(rows[0].row(), 0).text()

        for step in ("navigate", "resize", "language"):
            if step == "navigate":
                for page in (window._packages_page, window._history_page, window._setup_page, window._mods_page):
                    window._context_tabs.setCurrentWidget(page)
                    qapp.processEvents()
            elif step == "resize":
                for size in ((1100, 720), (1920, 1080), (1366, 768)):
                    window.resize(*size)
                    qapp.processEvents()
            else:
                window._apply_shell_setup_localizer("pt-BR", announce=False)
                qapp.processEvents()
                assert window._scan_button.text() == "Verificar mods"
            window._context_tabs.setCurrentWidget(window._mods_page)
            qapp.processEvents()
            assert window._mods_filter_input.text() == "filler", step
            assert _visible_names(table) == sorted(filtered, key=str.casefold, reverse=True), step
            assert selected_name() == "Filler Mod 07", step
            assert _compare_rows(window) == compare_rows_before, step
        # Actions still work after the language change.
        window._scan_button.click()
        _wait_until_idle(window, qapp)
        assert _visible_names(table) == sorted(filtered, key=str.casefold, reverse=True)
        # Row-based actions must still point at the mod the owner selected.
        assert selected_name() == "Filler Mod 07"
        assert table.item(table.currentRow(), 0).text() == "Filler Mod 07"
        assert dialogs.notices == []
    finally:
        _wait_until_idle(window, qapp)
        window.close()
        qapp.processEvents()



def test_closing_the_window_during_background_work_finishes_cleanly(
    library: SyntheticLibrary, qapp: QApplication, dialogs: DialogScript, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import threading

    from sdvmm.services.app_state_store import load_app_config

    window = _open_window(library, qapp)
    release = threading.Event()
    scan = window._shell_service.scan_with_target
    monkeypatch.setattr(
        window._shell_service, "scan_with_target", lambda **kwargs: (release.wait(5), scan(**kwargs))[1],
    )
    window._scan_button.click()
    assert window._active_operation_name == "Scan"
    window.close()
    qapp.processEvents()
    release.set()
    assert window._thread_pool.waitForDone(5000)
    for _ in range(10):
        qapp.processEvents()
    assert window._active_operation_name is None
    assert dialogs.notices == []
    assert load_app_config(library.state_file) is not None