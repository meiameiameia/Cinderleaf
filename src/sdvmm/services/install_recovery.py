"""Content-sealed, archive-first recovery for completed install operations."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
import os
from pathlib import Path
import uuid

from sdvmm.domain.models import InstallRecoveryExecutionReviewEntry, ModsInventory
from sdvmm.services.app_state_store import write_json_file_atomic
from sdvmm.services.install_integrity import (
    InstallIntegrityError,
    paths_overlap,
    snapshot_path,
)
from sdvmm.services.mod_scanner import scan_mods_directory


@dataclass(frozen=True, slots=True)
class RecoveryTransactionState:
    outcome_status: str
    removed_target_paths: tuple[Path, ...]
    restored_target_paths: tuple[Path, ...]
    retained_archive_paths: tuple[Path, ...]
    journal_path: Path
    failure_message: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryTransactionResult:
    removed_target_paths: tuple[Path, ...]
    restored_target_paths: tuple[Path, ...]
    retained_archive_paths: tuple[Path, ...]
    journal_path: Path
    inventory: ModsInventory


@dataclass(frozen=True, slots=True)
class _AppliedRecovery:
    action: str
    target_path: Path
    source_archive_path: Path | None
    retained_archive_path: Path
    expected_target_digest: str
    expected_archive_digest: str | None
    phase: str


class InstallRecoveryTransactionError(ValueError):
    progress: RecoveryTransactionState | None = None


def execute_install_recovery_transaction(
    *,
    entries: tuple[InstallRecoveryExecutionReviewEntry, ...],
    mods_root: Path,
    archive_root: Path,
    on_progress: Callable[[RecoveryTransactionState], None] | None = None,
) -> RecoveryTransactionResult:
    if not entries or any(not entry.executable for entry in entries):
        raise InstallRecoveryTransactionError("Recovery review is not executable.")
    if not mods_root.is_dir() or not archive_root.is_dir():
        raise InstallRecoveryTransactionError("Recovery roots are not accessible directories.")
    if paths_overlap(mods_root, archive_root):
        raise InstallRecoveryTransactionError("Recovery archive and Mods roots must not overlap.")

    try:
        root_seals = (
            snapshot_path(mods_root, contents=False),
            snapshot_path(archive_root, contents=False),
        )
        reserved: set[Path] = set()
        retention_paths: dict[Path, Path] = {}
        for reviewed in entries:
            plan_entry = reviewed.plan_entry
            _validate_reviewed_entry(reviewed, mods_root=mods_root, archive_root=archive_root)
            retention_paths[plan_entry.target_path] = _allocate_retention_path(
                archive_root,
                plan_entry.target_path.name,
                reserved,
            )
    except (OSError, InstallIntegrityError) as exc:
        raise InstallRecoveryTransactionError(str(exc)) from exc

    transaction_id = uuid.uuid4().hex
    journal_path = archive_root / f".sdvmm-recovery-{transaction_id}.json"
    applied: list[_AppliedRecovery] = []
    removed: list[Path] = []
    restored: list[Path] = []
    commit_decided = False
    writes_started = False

    def roots_unchanged() -> None:
        if (
            snapshot_path(mods_root, contents=False),
            snapshot_path(archive_root, contents=False),
        ) != root_seals:
            raise InstallIntegrityError("Recovery roots changed during execution.")

    def retained_paths() -> tuple[Path, ...]:
        return tuple(item.retained_archive_path for item in applied if os.path.lexists(item.retained_archive_path))

    def publish(status: str, failure: str | None = None, current_index: int | None = None) -> RecoveryTransactionState:
        state = RecoveryTransactionState(
            status,
            tuple(removed),
            tuple(restored),
            retained_paths(),
            journal_path,
            failure,
        )
        write_json_file_atomic(journal_path, {
            "version": 1,
            "status": status,
            "failure": failure,
            "mods_root": str(mods_root),
            "archive_root": str(archive_root),
            "current_index": current_index,
            "removed_target_paths": [str(path) for path in removed],
            "restored_target_paths": [str(path) for path in restored],
            "retained_archive_paths": [str(path) for path in state.retained_archive_paths],
            "entries": [
                {
                    "action": reviewed.plan_entry.action,
                    "target": str(reviewed.plan_entry.target_path),
                    "source_archive": (
                        str(reviewed.plan_entry.archive_path)
                        if reviewed.plan_entry.archive_path is not None
                        else None
                    ),
                    "retained_archive": str(retention_paths[reviewed.plan_entry.target_path]),
                    "expected_target_digest": reviewed.plan_entry.expected_target_digest,
                    "expected_archive_digest": reviewed.plan_entry.expected_archive_digest,
                }
                for reviewed in entries
            ],
        })
        if on_progress is not None:
            on_progress(state)
        return state

    try:
        publish("in_progress")
        for index, reviewed in enumerate(entries):
            roots_unchanged()
            _validate_reviewed_entry(reviewed, mods_root=mods_root, archive_root=archive_root)
            publish("in_progress", current_index=index)
            roots_unchanged()
            _validate_reviewed_entry(reviewed, mods_root=mods_root, archive_root=archive_root)

            plan_entry = reviewed.plan_entry
            expected_target_digest = plan_entry.expected_target_digest
            if expected_target_digest is None:
                raise InstallIntegrityError("Recovery target has no recorded content seal.")
            retained = retention_paths[plan_entry.target_path]
            writes_started = True
            plan_entry.target_path.rename(retained)
            applied.append(_AppliedRecovery(
                action=plan_entry.action,
                target_path=plan_entry.target_path,
                source_archive_path=plan_entry.archive_path,
                retained_archive_path=retained,
                expected_target_digest=expected_target_digest,
                expected_archive_digest=plan_entry.expected_archive_digest,
                phase="retained",
            ))
            if snapshot_path(retained).digest != expected_target_digest:
                raise InstallIntegrityError("Recovery target changed while being archived; recovery stopped.")

            if plan_entry.action == "remove_installed_target":
                removed.append(plan_entry.target_path)
                publish("in_progress", current_index=index)
                continue

            if plan_entry.action != "restore_from_archive" or plan_entry.archive_path is None:
                raise InstallRecoveryTransactionError(f"Unsupported recovery action: {plan_entry.action}")
            plan_entry.archive_path.rename(plan_entry.target_path)
            applied[-1] = replace(applied[-1], phase="completed")
            if snapshot_path(plan_entry.target_path).digest != plan_entry.expected_archive_digest:
                raise InstallIntegrityError("Restored archive changed while being moved; recovery stopped.")
            restored.append(plan_entry.target_path)
            publish("in_progress", current_index=index)

        inventory = scan_mods_directory(
            mods_root,
            excluded_paths=(archive_root, mods_root / ".sdvmm-archive"),
        )
        commit_decided = True
        publish("completed")
        return RecoveryTransactionResult(
            tuple(removed),
            tuple(restored),
            retained_paths(),
            journal_path,
            inventory,
        )
    except Exception as exc:
        if not writes_started:
            detail = f"Recovery stopped before changing any Mods: {exc}"
            try:
                publish("failed", detail)
            except Exception:
                pass
            raise InstallRecoveryTransactionError(detail) from exc

        recovery_errors = (
            ["Recovery files were applied, but final recording failed; files were retained."]
            if commit_decided
            else []
        )
        if not commit_decided:
            for item in reversed(applied):
                try:
                    roots_unchanged()
                    if item.phase == "completed":
                        if item.source_archive_path is None or item.expected_archive_digest is None:
                            raise InstallIntegrityError("Original archive destination is unavailable.")
                        if snapshot_path(item.target_path).digest != item.expected_archive_digest:
                            raise InstallIntegrityError(f"Restored target changed externally: {item.target_path}")
                        if os.path.lexists(item.source_archive_path):
                            raise InstallIntegrityError(f"Original archive destination is occupied: {item.source_archive_path}")
                        item.target_path.rename(item.source_archive_path)
                    if snapshot_path(item.retained_archive_path).digest != item.expected_target_digest:
                        raise InstallIntegrityError(
                            f"Retained replacement changed externally: {item.retained_archive_path}"
                        )
                    if os.path.lexists(item.target_path):
                        raise InstallIntegrityError(f"Recovery target is occupied: {item.target_path}")
                    item.retained_archive_path.rename(item.target_path)
                except Exception as recovery_exc:
                    recovery_errors.append(str(recovery_exc))

        removed.clear()
        restored.clear()
        if recovery_errors:
            for item in applied:
                try:
                    if item.action == "remove_installed_target" and not os.path.lexists(item.target_path):
                        removed.append(item.target_path)
                    elif (
                        item.action == "restore_from_archive"
                        and os.path.lexists(item.target_path)
                        and snapshot_path(item.target_path).digest == item.expected_archive_digest
                    ):
                        restored.append(item.target_path)
                except (OSError, InstallIntegrityError):
                    pass
        status = "partial" if recovery_errors else "rolled_back"
        detail = str(exc)
        if recovery_errors:
            detail += " Recovery: " + "; ".join(recovery_errors)
        progress = RecoveryTransactionState(
            status,
            tuple(removed),
            tuple(restored),
            retained_paths(),
            journal_path,
            detail,
        )
        try:
            roots_unchanged()
            publish(status, detail)
        except Exception as record_exc:
            detail += f" Recovery record could not be updated: {record_exc}. Journal: {journal_path}"
            progress = replace(progress, failure_message=detail)
        error = InstallRecoveryTransactionError(detail)
        error.progress = progress
        raise error from exc


def _validate_reviewed_entry(
    reviewed: InstallRecoveryExecutionReviewEntry,
    *,
    mods_root: Path,
    archive_root: Path,
) -> None:
    entry = reviewed.plan_entry
    target = entry.target_path.resolve()
    if target.parent != mods_root.resolve():
        raise InstallIntegrityError(f"Recovery target is outside the Mods root: {entry.target_path}")
    if reviewed.target_snapshot is None or snapshot_path(entry.target_path) != reviewed.target_snapshot:
        raise InstallIntegrityError(f"Recovery target changed after review: {entry.target_path}")
    if entry.expected_target_digest is None or reviewed.target_snapshot.digest != entry.expected_target_digest:
        raise InstallIntegrityError(f"Recovery target does not match its install record: {entry.target_path}")
    if entry.action == "restore_from_archive":
        if entry.archive_path is None or entry.archive_path.resolve().parent != archive_root.resolve():
            raise InstallIntegrityError("Recovery archive is outside the recorded archive root.")
        if reviewed.archive_snapshot is None or snapshot_path(entry.archive_path) != reviewed.archive_snapshot:
            raise InstallIntegrityError(f"Recovery archive changed after review: {entry.archive_path}")
        if entry.expected_archive_digest is None or reviewed.archive_snapshot.digest != entry.expected_archive_digest:
            raise InstallIntegrityError(f"Recovery archive does not match its install record: {entry.archive_path}")


def _allocate_retention_path(archive_root: Path, folder_name: str, reserved: set[Path]) -> Path:
    for index in range(1, 10_000):
        candidate = archive_root / f"{folder_name}__sdvmm_archive_{index:03d}"
        if candidate not in reserved and not os.path.lexists(candidate):
            reserved.add(candidate)
            return candidate
    raise InstallRecoveryTransactionError(f"Could not allocate recovery archive for {folder_name}.")
