from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import shutil
from zipfile import ZipFile

import pytest

from sdvmm.app.shell_service import AppShellError, AppShellService
from sdvmm.app.i18n import UiLocalizer, set_active_ui_localizer
from sdvmm.services import sandbox_installer as installer
from sdvmm.services import app_state_store
from sdvmm.services.install_integrity import snapshot_path


def package(path: Path, names: tuple[str, ...] = ("Alpha",), version: str = "2.0.0") -> Path:
    with ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(f"{name}/manifest.json", json.dumps({"Name": name, "UniqueID": f"Audit.{name}", "Version": version}))
            archive.writestr(f"{name}/payload.txt", version)
    return path


def setup(tmp_path: Path, *, names=("Alpha",), overwrite=False):
    mods, archive = tmp_path / "Mods", tmp_path / "Archive"
    mods.mkdir()
    archive.mkdir()
    if overwrite:
        for name in names:
            target = mods / name
            target.mkdir()
            (target / "manifest.json").write_text(json.dumps({"Name": name, "UniqueID": f"Audit.{name}", "Version": "1.0.0"}), encoding="utf-8")
            (target / "config.json").write_text('{"keep":true}', encoding="utf-8")
    source = package(tmp_path / "mods.zip", names)
    service = AppShellService(state_file=tmp_path / "state" / "app-state.json")
    plan = service.build_sandbox_install_plan(str(source), str(mods), str(archive), allow_overwrite=overwrite)
    return service, plan


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_replaced_archive_rejected_even_when_size_and_mtime_are_preserved(tmp_path, language):
    service, plan = setup(tmp_path)
    set_active_ui_localizer(UiLocalizer.from_preference(language))
    before = plan.package_path.stat()
    package(plan.package_path, version="9.0.0")
    assert plan.package_path.stat().st_size == before.st_size
    os.utime(plan.package_path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(AppShellError) as caught:
        service.execute_sandbox_install_plan(plan)
    assert str(caught.value) == UiLocalizer.from_preference(language).text("install.integrity.changed")
    assert not (plan.sandbox_mods_path / "Alpha").exists()
    assert not list(plan.sandbox_archive_path.iterdir())
    assert service.load_install_operation_history().operations == ()


@pytest.mark.parametrize("change", ["config", "target", "root", "archive"])
def test_changed_destination_rejected_before_any_mod_write(tmp_path, change):
    service, plan = setup(tmp_path, overwrite=True)
    if change == "config":
        (plan.entries[0].target_path / "config.json").write_text('{"keep":false}', encoding="utf-8")
    elif change == "target":
        plan.entries[0].target_path.rename(plan.sandbox_mods_path / "MovedAlpha")
    elif change == "root":
        plan.sandbox_mods_path.rename(tmp_path / "PreviousMods")
        plan.sandbox_mods_path.mkdir()
    else:
        plan.entries[0].archive_path.mkdir()
    before_targets = {
        name: snapshot_path(plan.sandbox_mods_path / name)
        for name in ("Alpha", "Beta")
        if (plan.sandbox_mods_path / name).exists()
    }
    with pytest.raises(AppShellError, match="reviewed files or destination changed"):
        service.execute_sandbox_install_plan(plan)
    for name in ("Alpha", "Beta"):
        target = plan.sandbox_mods_path / name
        if name in before_targets:
            assert snapshot_path(target) == before_targets[name]
        else:
            assert not target.exists()
    assert service.load_install_operation_history().operations == ()


def test_unsealed_plan_cannot_bypass_review(tmp_path):
    service, plan = setup(tmp_path)
    with pytest.raises(AppShellError, match="Create a new install plan"):
        service.execute_sandbox_install_plan(replace(plan, integrity=None))
    assert list(plan.sandbox_mods_path.iterdir()) == []


def test_second_target_created_while_extracting_prevents_first_install(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, names=("Alpha", "Beta"))
    original = installer._extract_mod_root
    def extract(**kwargs):
        original(**kwargs)
        if kwargs["source_root"] == "Beta":
            (plan.sandbox_mods_path / "Beta").mkdir()
    monkeypatch.setattr(installer, "_extract_mod_root", extract)
    with pytest.raises(AppShellError):
        service.execute_sandbox_install_plan(plan)
    assert not (plan.sandbox_mods_path / "Alpha").exists()
    assert (plan.sandbox_mods_path / "Beta").exists()


@pytest.mark.parametrize("overwrite", [False, True])
def test_second_entry_failure_rolls_back_entire_batch_and_records_outcome(tmp_path, monkeypatch, overwrite):
    service, plan = setup(tmp_path, names=("Alpha", "Beta"), overwrite=overwrite)
    before_targets = {
        name: snapshot_path(plan.sandbox_mods_path / name)
        for name in ("Alpha", "Beta")
        if (plan.sandbox_mods_path / name).exists()
    }
    original = installer._move_path
    def move(source, destination):
        if destination == plan.sandbox_mods_path / "Beta" and source.parent.name.startswith(".sdvmm-stage-"):
            raise OSError("Synthetic second-target failure")
        original(source, destination)
    monkeypatch.setattr(installer, "_move_path", move)
    with pytest.raises(AppShellError, match="No mod changes from this attempt were kept"):
        service.execute_sandbox_install_plan(plan)
    for name in ("Alpha", "Beta"):
        target = plan.sandbox_mods_path / name
        if name in before_targets:
            assert snapshot_path(target) == before_targets[name]
        else:
            assert not target.exists()
    assert list(plan.sandbox_mods_path.glob(".sdvmm-stage-*"))
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "rolled_back"
    assert record.installed_targets == record.archived_targets == ()
    assert json.loads(record.journal_path.read_text())["status"] == "rolled_back"
    assert not any(e.recoverable for e in service.derive_install_operation_recovery_plan(record).entries)


def test_failed_rollback_preserves_files_and_records_partial_not_success(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, names=("Alpha", "Beta"), overwrite=True)
    original = installer._move_path
    def move(source, destination):
        if destination == plan.sandbox_mods_path / "Beta" and source.parent.name.startswith(".sdvmm-stage-"):
            raise OSError("Synthetic install failure")
        if destination == plan.sandbox_mods_path / "Alpha" and source.parent == plan.sandbox_archive_path:
            raise OSError("Synthetic rollback failure")
        original(source, destination)
    monkeypatch.setattr(installer, "_move_path", move)
    with pytest.raises(AppShellError, match="recovery is incomplete"):
        service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "partial"
    assert record.archived_targets == (plan.entries[0].archive_path,)
    assert (plan.entries[0].archive_path / "config.json").read_text() == '{"keep":true}'
    assert list(plan.sandbox_mods_path.glob(".sdvmm-stage-*"))
    assert json.loads(record.journal_path.read_text())["status"] == "partial"
    assert not any(e.recoverable for e in service.derive_install_operation_recovery_plan(record).entries)


def test_history_completion_failure_preserves_files_and_marks_partial(tmp_path, monkeypatch):
    service, plan = setup(tmp_path)
    original = app_state_store.save_install_operation_history
    def save(path, history):
        if history.operations[-1].outcome_status == "completed":
            raise OSError("Synthetic full disk at completion")
        original(path, history)
    monkeypatch.setattr("sdvmm.app.shell_service.save_install_operation_history", save)
    with pytest.raises(AppShellError):
        service.execute_sandbox_install_plan(plan)
    assert (plan.entries[0].target_path / "payload.txt").read_text() == "2.0.0"
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "partial"


def test_interruption_leaves_durable_unfinished_record_not_automatic_recovery(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, names=("Alpha", "Beta"))
    original = installer._move_path
    def move(source, destination):
        if destination == plan.sandbox_mods_path / "Beta":
            raise KeyboardInterrupt("Synthetic process interruption")
        original(source, destination)
    monkeypatch.setattr(installer, "_move_path", move)
    with pytest.raises(KeyboardInterrupt):
        service.execute_sandbox_install_plan(plan)
    # Reopen the history through a new service, as after an application restart.
    reopened = AppShellService(state_file=tmp_path / "state" / "app-state.json")
    record, = reopened.load_install_operation_history().operations
    assert record.outcome_status == "in_progress"
    assert record.installed_targets == (plan.sandbox_mods_path / "Alpha",)
    assert json.loads(record.journal_path.read_text())["attempted_targets"] == [str(e.target_path) for e in plan.entries]
    assert not any(e.recoverable for e in reopened.derive_install_operation_recovery_plan(record).entries)


@pytest.mark.parametrize("relationship", ["same", "inside", "contains"])
def test_sandbox_overlap_is_rejected_in_both_directions(tmp_path, relationship):
    common = tmp_path / "ModTrees"
    common.mkdir()
    real = common / "Real"
    real.mkdir()
    sandbox = {"same": real, "inside": real / "TestMods", "contains": common}[relationship]
    sandbox.mkdir(exist_ok=True)
    source = package(tmp_path / "one.zip")
    service = AppShellService(state_file=tmp_path / "state.json")
    with pytest.raises(AppShellError, match="neither may contain the other"):
        service.build_sandbox_install_plan(str(source), str(sandbox), str(tmp_path / "Archive"), allow_overwrite=False, configured_real_mods_path=real)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction boundary")
def test_target_parent_replaced_by_junction_is_rejected(tmp_path):
    service, plan = setup(tmp_path)
    outside = tmp_path / "Outside"
    outside.mkdir()
    plan.sandbox_mods_path.rename(tmp_path / "OriginalMods")
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(plan.sandbox_mods_path), str(outside)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with pytest.raises(AppShellError):
        service.execute_sandbox_install_plan(plan)
    assert list(outside.iterdir()) == []


def test_staged_package_copy_is_verified_before_extraction(tmp_path, monkeypatch):
    service, plan = setup(tmp_path)
    original = shutil.copyfile
    def copy(source, destination, *args, **kwargs):
        original(source, destination, *args, **kwargs)
        package(Path(destination), version="9.0.0")
    monkeypatch.setattr(installer.shutil, "copyfile", copy)
    with pytest.raises(AppShellError) as caught:
        service.execute_sandbox_install_plan(plan)
    assert "History" not in str(caught.value)
    assert "journal" not in str(caught.value).casefold()
    assert not plan.entries[0].target_path.exists()
    assert service.load_install_operation_history().operations == ()


def test_completed_install_records_content_seal_and_blocks_changed_mod_recovery(tmp_path):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    assert record.entries[0].installed_target_digest == snapshot_path(plan.entries[0].target_path).digest

    (plan.entries[0].target_path / "payload.txt").write_text("player changed this", encoding="utf-8")
    recovery_plan = service.derive_install_operation_recovery_plan(record)
    review = service.review_install_recovery_execution(recovery_plan)
    assert not review.allowed
    assert review.entries[0].decision_code == "removal_target_changed"
    assert (plan.entries[0].target_path / "payload.txt").read_text() == "player changed this"


def test_completed_overwrite_recovery_archives_current_and_restores_original(tmp_path):
    service, plan = setup(tmp_path, overwrite=True)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    entry = record.entries[0]
    assert entry.installed_target_digest == snapshot_path(entry.target_path).digest
    assert entry.archived_target_digest == snapshot_path(entry.archive_path).digest

    review = service.review_install_recovery_execution(
        service.derive_install_operation_recovery_plan(record)
    )
    assert review.allowed
    result = service.execute_install_recovery_review(review)
    restored = json.loads((entry.target_path / "manifest.json").read_text(encoding="utf-8"))
    assert restored["Version"] == "1.0.0"
    assert not entry.archive_path.exists()
    assert len(result.retained_archive_paths) == 1
    assert (result.retained_archive_paths[0] / "payload.txt").read_text() == "2.0.0"
    assert result.journal_path is not None and result.journal_path.exists()


def test_changed_original_archive_blocks_overwrite_recovery(tmp_path):
    service, plan = setup(tmp_path, overwrite=True)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    archived = record.entries[0].archive_path
    (archived / "config.json").write_text('{"changed":true}', encoding="utf-8")

    review = service.review_install_recovery_execution(
        service.derive_install_operation_recovery_plan(record)
    )
    assert not review.allowed
    assert review.entries[0].decision_code == "restore_archive_changed"
    assert record.entries[0].target_path.exists()


def test_recovery_review_is_revalidated_before_archive_write(tmp_path):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    review = service.review_install_recovery_execution(
        service.derive_install_operation_recovery_plan(record)
    )
    assert review.allowed
    (record.entries[0].target_path / "payload.txt").write_text("changed after review", encoding="utf-8")

    with pytest.raises(AppShellError, match="Recovery stopped before changing any Mods"):
        service.execute_install_recovery_review(review)
    assert (record.entries[0].target_path / "payload.txt").read_text() == "changed after review"
    recovery_record, = service.load_recovery_execution_history().operations
    assert recovery_record.outcome_status == "failed"


def test_recovery_interruption_keeps_archives_and_durable_in_progress_record(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, names=("Alpha", "Beta"))
    service.execute_sandbox_install_plan(plan)
    install_record, = service.load_install_operation_history().operations
    review = service.review_install_recovery_execution(
        service.derive_install_operation_recovery_plan(install_record)
    )
    assert review.allowed
    original_rename = Path.rename

    def interrupt_second_target(path, destination):
        if path == plan.sandbox_mods_path / "Beta":
            raise KeyboardInterrupt("synthetic recovery interruption")
        return original_rename(path, destination)

    monkeypatch.setattr(Path, "rename", interrupt_second_target)
    with pytest.raises(KeyboardInterrupt):
        service.execute_install_recovery_review(review)

    assert not (plan.sandbox_mods_path / "Alpha").exists()
    assert (plan.sandbox_mods_path / "Beta").exists()
    record, = service.load_recovery_execution_history().operations
    assert record.outcome_status == "in_progress"
    assert len(record.retained_archive_paths) == 1
    assert record.retained_archive_paths[0].exists()
    assert record.journal_path is not None and record.journal_path.exists()
    reopened = AppShellService(state_file=service.state_file)
    blocked = reopened.review_install_recovery_execution(
        reopened.derive_install_operation_recovery_plan(install_record)
    )
    assert not blocked.allowed


def test_rollback_never_undoes_another_install_with_identical_contents(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, overwrite=True)
    original = installer._overwrite_target_with_archive
    external_identity = None
    def overwrite(staged_target, target_path, archive_path, **kwargs):
        nonlocal external_identity
        # Another process finishes after our last preflight but before the move.
        target_path.rename(archive_path)
        shutil.copytree(staged_target, target_path)
        external_identity = snapshot_path(target_path).identity
        original(staged_target, target_path, archive_path, **kwargs)
    monkeypatch.setattr(installer, "_overwrite_target_with_archive", overwrite)
    with pytest.raises(AppShellError, match="recovery is incomplete"):
        service.execute_sandbox_install_plan(plan)
    assert snapshot_path(plan.entries[0].target_path).identity == external_identity
    assert (plan.entries[0].archive_path / "config.json").exists()
    record, = service.load_install_operation_history().operations
    assert record.installed_targets == record.archived_targets == ()


def test_new_target_from_another_process_is_not_deleted_during_rollback(tmp_path, monkeypatch):
    service, plan = setup(tmp_path)
    external_identity = None
    def install(staged_target, target_path):
        nonlocal external_identity
        shutil.copytree(staged_target, target_path)
        external_identity = snapshot_path(target_path).identity
        raise OSError("Another process created the target")
    monkeypatch.setattr(installer, "_install_new_target", install)
    with pytest.raises(AppShellError, match="recovery is incomplete"):
        service.execute_sandbox_install_plan(plan)
    assert snapshot_path(plan.entries[0].target_path).identity == external_identity


def test_changed_replacement_is_preserved_if_config_restoration_fails(tmp_path, monkeypatch):
    service, plan = setup(tmp_path, overwrite=True)

    def restore(*, archived_target, target_path):
        (target_path / "payload.txt").write_text("Changed after replacement", encoding="utf-8")
        raise OSError("Synthetic failure after a target changed")

    monkeypatch.setattr(installer, "_restore_preserved_config_artifacts", restore)
    with pytest.raises(AppShellError, match="recovery is incomplete"):
        service.execute_sandbox_install_plan(plan)
    assert (plan.entries[0].target_path / "payload.txt").read_text() == "Changed after replacement"
    assert (plan.entries[0].archive_path / "config.json").read_text() == '{"keep":true}'
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "partial"


def test_verified_replacement_is_quarantined_not_deleted_when_config_restore_fails(
    tmp_path,
    monkeypatch,
):
    service, plan = setup(tmp_path, overwrite=True)

    def restore(*, archived_target, target_path):
        raise OSError("Synthetic failure before changing the replacement")

    monkeypatch.setattr(installer, "_restore_preserved_config_artifacts", restore)
    with pytest.raises(AppShellError, match="No mod changes from this attempt were kept"):
        service.execute_sandbox_install_plan(plan)

    assert (plan.entries[0].target_path / "config.json").read_text() == '{"keep":true}'
    assert not plan.entries[0].archive_path.exists()
    staging_roots = list(plan.sandbox_mods_path.glob(".sdvmm-stage-*"))
    assert len(staging_roots) == 1
    assert (staging_roots[0] / plan.entries[0].target_path.name / "payload.txt").read_text() == "2.0.0"
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "rolled_back"


def test_legacy_history_loads_but_new_outcomes_use_fail_closed_version(tmp_path):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    history_file = app_state_store.install_operation_history_file(tmp_path / "state" / "app-state.json")
    payload = json.loads(history_file.read_text())
    assert payload["version"] == 2
    payload["version"] = 1
    for field in ("outcome_status", "failure_message", "journal_path"):
        payload["operations"][0].pop(field)
    payload["operations"][0]["entries"][0].pop("installed_target_digest")
    payload["operations"][0]["entries"][0].pop("archived_target_digest")
    history_file.write_text(json.dumps(payload), encoding="utf-8")
    record, = service.load_install_operation_history().operations
    assert record.outcome_status == "completed"
    assert record.journal_path is None
    assert not any(
        entry.recoverable
        for entry in service.derive_install_operation_recovery_plan(record).entries
    )
    app_state_store.save_install_operation_history(history_file, service.load_install_operation_history())
    assert json.loads(history_file.read_text())["version"] == 2


def test_missing_archive_root_is_created_only_after_validating_review(tmp_path):
    service, plan = setup(tmp_path)
    plan.sandbox_archive_path.rmdir()
    plan = service.build_sandbox_install_plan(str(plan.package_path), str(plan.sandbox_mods_path), str(plan.sandbox_archive_path), allow_overwrite=False)
    service.execute_sandbox_install_plan(plan)
    assert plan.entries[0].target_path.exists()


def test_replaced_parent_of_missing_target_invalidates_plan(tmp_path):
    service, plan = setup(tmp_path)
    original = plan.sandbox_archive_path
    original.rmdir()
    parent = tmp_path / "ArchiveParent"
    parent.mkdir()
    plan = service.build_sandbox_install_plan(str(plan.package_path), str(plan.sandbox_mods_path), str(parent / "Archive"), allow_overwrite=False)
    parent.rename(tmp_path / "PreviousArchiveParent")
    parent.mkdir()
    with pytest.raises(AppShellError, match="reviewed files or destination changed"):
        service.execute_sandbox_install_plan(plan)
    assert not plan.entries[0].target_path.exists()


def test_config_save_rejects_nested_sandbox_without_writing_state(tmp_path):
    game = tmp_path / "Game"
    real = game / "Mods"
    sandbox = real / "Test"
    sandbox.mkdir(parents=True)
    state_file = tmp_path / "state.json"
    service = AppShellService(state_file=state_file)
    with pytest.raises(AppShellError, match="neither may contain the other"):
        service.save_operational_config(game_path_text=str(game), mods_dir_text=str(real),
            sandbox_mods_path_text=str(sandbox), sandbox_archive_path_text="",
            watched_downloads_path_text="", scan_target="configured_real_mods", existing_config=None)
    assert not state_file.exists()


def test_changed_dependency_manifest_invalidates_review(tmp_path):
    service, plan = setup(tmp_path, names=("Dependency",), overwrite=True)
    source = package(tmp_path / "new.zip", names=("NewMod",))
    plan = service.build_sandbox_install_plan(str(source), str(plan.sandbox_mods_path), str(plan.sandbox_archive_path), allow_overwrite=False)
    dependency_manifest = plan.sandbox_mods_path / "Dependency" / "manifest.json"
    dependency_manifest.write_text('{"Name":"Dependency","UniqueID":"Audit.Dependency","Version":"0.0.1"}', encoding="utf-8")
    with pytest.raises(AppShellError, match="Create a new install plan"):
        service.execute_sandbox_install_plan(plan)
    assert not (plan.sandbox_mods_path / "NewMod").exists()


def test_initial_install_history_failure_reports_no_mod_write_without_false_recovery_guidance(
    tmp_path,
    monkeypatch,
):
    service, plan = setup(tmp_path)

    def fail_history(*args, **kwargs):
        raise OSError("Synthetic history write failure")

    monkeypatch.setattr(
        "sdvmm.app.shell_service.append_install_operation_record",
        fail_history,
    )
    with pytest.raises(AppShellError) as caught:
        service.execute_sandbox_install_plan(plan)

    assert str(caught.value) == UiLocalizer.from_preference("en").text(
        "install.integrity.prewrite_failed"
    )
    assert "History" not in str(caught.value)
    assert "journal" not in str(caught.value).casefold()
    assert not plan.entries[0].target_path.exists()
    assert not list(plan.sandbox_mods_path.glob(".sdvmm-stage-*"))
    assert service.load_install_operation_history().operations == tuple()


def test_initial_recovery_history_failure_reports_no_mod_write_and_preserves_target(
    tmp_path,
    monkeypatch,
):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    recovery_plan = service.derive_install_operation_recovery_plan(
        service.load_install_operation_history().operations[0]
    )
    review = service.review_install_recovery_execution(recovery_plan)
    before = snapshot_path(plan.entries[0].target_path)

    def fail_history(*args, **kwargs):
        raise OSError("Synthetic recovery history write failure")

    monkeypatch.setattr(
        "sdvmm.app.shell_service.append_recovery_execution_record",
        fail_history,
    )
    with pytest.raises(AppShellError) as caught:
        service.execute_install_recovery_review(review)

    assert str(caught.value) == UiLocalizer.from_preference("en").text(
        "recovery.integrity.prewrite_failed"
    )
    assert "History" not in str(caught.value)
    assert "journal" not in str(caught.value).casefold()
    assert snapshot_path(plan.entries[0].target_path) == before
    assert service.load_recovery_execution_history().operations == tuple()


@pytest.mark.parametrize("outcome", ["in_progress", "partial", "rolled_back"])
def test_incomplete_history_round_trip(tmp_path, outcome):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    history = app_state_store.InstallOperationHistory(operations=(replace(record,
        outcome_status=outcome, failure_message="Synthetic failure"),))
    path = app_state_store.install_operation_history_file(tmp_path / "state" / "app-state.json")
    app_state_store.save_install_operation_history(path, history)
    assert app_state_store.load_install_operation_history(path) == history


def test_new_history_without_outcome_cannot_be_treated_as_completed(tmp_path):
    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    path = app_state_store.install_operation_history_file(tmp_path / "state" / "app-state.json")
    payload = json.loads(path.read_text())
    del payload["operations"][0]["outcome_status"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(app_state_store.AppStateStoreError, match="outcome_status is required"):
        app_state_store.load_install_operation_history(path)


@pytest.mark.parametrize("language", ["en", "pt-BR"])
@pytest.mark.parametrize("outcome", ["completed", "in_progress", "partial", "rolled_back"])
def test_history_outcome_and_journal_are_present_in_both_languages(tmp_path, language, outcome):
    from sdvmm.ui.main_window import (
        _build_install_operation_summary_text,
        _install_operation_selector_text,
    )

    service, plan = setup(tmp_path)
    service.execute_sandbox_install_plan(plan)
    record, = service.load_install_operation_history().operations
    record = replace(record, outcome_status=outcome)
    localizer = UiLocalizer.from_preference(language)
    set_active_ui_localizer(localizer)
    label = localizer.text(f"install.outcome.{outcome}")
    assert label in _install_operation_selector_text(record)
    summary = _build_install_operation_summary_text(record)
    assert localizer.text("install.outcome.summary", outcome=label) in summary
    assert localizer.text("install.outcome.journal", path=record.journal_path) in summary
