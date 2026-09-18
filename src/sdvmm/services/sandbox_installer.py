from __future__ import annotations

import errno
import json
from dataclasses import dataclass, replace
from collections.abc import Callable
from pathlib import Path, PurePosixPath
import shutil
from typing import Any
import uuid

from sdvmm.domain.install_codes import BLOCKED, INSTALL_NEW, OVERWRITE_WITH_ARCHIVE
from sdvmm.domain.models import (
    PackageInspectionResult,
    SandboxInstallPlan,
    SandboxInstallPlanEntry,
    SandboxInstallResult,
)
from sdvmm.domain.unique_id import canonicalize_unique_id
from sdvmm.services.archive_tools import ArchiveToolError
from sdvmm.services.archive_tools import extract_archive_root_to_directory
from sdvmm.services.mod_scanner import scan_mods_directory
from sdvmm.services.package_inspector import inspect_package_archive
from sdvmm.services.app_state_store import write_json_file_atomic
from sdvmm.services.install_integrity import (
    InstallIntegrityError, capture_integrity, snapshot_path, validate_boundaries,
    validate_integrity,
)

_CONFIG_ARTIFACT_NAMES = ("config.json", "config", "configs")


class SandboxInstallError(ValueError):
    """Raised when plan creation or install execution cannot proceed safely."""

    progress: InstallTransactionState | None = None


@dataclass(frozen=True)
class InstallTransactionState:
    outcome_status: str
    installed_targets: tuple[Path, ...]
    archived_targets: tuple[Path, ...]
    journal_path: Path
    failure_message: str | None = None
    installed_target_digests: tuple[tuple[Path, str], ...] = tuple()
    archived_target_digests: tuple[tuple[Path, str], ...] = tuple()


class SandboxFileLockError(SandboxInstallError):
    """Raised when Windows is likely still holding a handle inside the target folder."""

    def __init__(self, message: str, *, technical_detail: str) -> None:
        super().__init__(message)
        self.technical_detail = technical_detail


_LOCK_ERRNOS = {errno.EACCES, errno.EPERM}
_LOCK_WINERRORS = {5, 32, 33}


def build_sandbox_install_plan(
    package_path: Path,
    sandbox_mods_path: Path,
    sandbox_archive_path: Path,
    *,
    allow_overwrite: bool,
    existing_target_paths_by_unique_id: dict[str, Path] | None = None,
) -> SandboxInstallPlan:
    package_snapshot = snapshot_path(package_path)
    inspection = inspect_package_archive(package_path)

    entries: list[SandboxInstallPlanEntry] = []
    overwrite_entries_with_preserved_config = 0

    for mod in inspection.mods:
        source_root = str(PurePosixPath(mod.manifest_path).parent)
        if source_root == "":
            source_root = "."

        target_folder_name = _derive_target_folder_name(source_root, mod.unique_id, mod.name)
        target_path = sandbox_mods_path / target_folder_name
        if existing_target_paths_by_unique_id is not None:
            existing_target_path = existing_target_paths_by_unique_id.get(
                canonicalize_unique_id(mod.unique_id)
            )
            if existing_target_path is not None:
                target_path = existing_target_path

        warnings: list[str] = []
        can_install = True
        action = INSTALL_NEW
        archive_path: Path | None = None

        if source_root == ".":
            warnings.append(
                "Manifest is at package root; install extracts package root files into one target folder."
            )
            if len(inspection.mods) > 1:
                warnings.append(
                    "Package-root manifest with multiple detected mods is unsupported for sandbox install."
                )
                can_install = False

        target_exists = target_path.exists()
        if target_exists:
            if allow_overwrite and can_install:
                action = OVERWRITE_WITH_ARCHIVE
                archive_path = _build_archive_destination(
                    archive_root=sandbox_archive_path,
                    target_folder_name=target_path.name,
                )
                warnings.append(
                    f"Target folder already exists and will be archived to '{archive_path.name}' before overwrite."
                )
                preserved_artifact_names = _config_artifact_names(target_path)
                if preserved_artifact_names:
                    overwrite_entries_with_preserved_config += 1
                    preservation_warning = (
                        "Existing config artifacts will be preserved during replace: "
                        f"{', '.join(preserved_artifact_names)}."
                    )
                    if "config.json" in preserved_artifact_names:
                        preservation_warning += (
                            " When both old and new config.json exist, Cinderleaf adds new default "
                            "settings without changing existing user values."
                        )
                    warnings.append(preservation_warning)
            else:
                warnings.append("Target folder already exists. Overwrite is disabled for this plan.")
                can_install = False

        if not can_install:
            action = BLOCKED
            archive_path = None

        entries.append(
            SandboxInstallPlanEntry(
                name=mod.name,
                unique_id=mod.unique_id,
                version=mod.version,
                source_package_path=package_path,
                source_manifest_path=mod.manifest_path,
                source_root_path=source_root,
                target_path=target_path,
                action=action,
                target_exists=target_exists,
                archive_path=archive_path,
                can_install=can_install,
                warnings=tuple(warnings),
            )
        )

    entries = _mark_duplicate_targets(entries)
    entries.sort(key=lambda item: (item.target_path.name.lower(), item.unique_id.casefold()))

    plan_warnings = _build_plan_warnings(entries, inspection, allow_overwrite=allow_overwrite)
    if overwrite_entries_with_preserved_config > 0:
        target_label = "target" if overwrite_entries_with_preserved_config == 1 else "targets"
        plan_warnings.append(
            "Config preservation is enabled for "
            f"{overwrite_entries_with_preserved_config} overwrite {target_label}; "
            "existing config artifacts will be copied back after replacement."
        )

    plan = SandboxInstallPlan(
        package_path=package_path,
        sandbox_mods_path=sandbox_mods_path,
        sandbox_archive_path=sandbox_archive_path,
        entries=tuple(entries),
        package_findings=inspection.findings,
        package_warnings=inspection.warnings,
        plan_warnings=tuple(plan_warnings),
        dependency_findings=inspection.dependency_findings,
        package_paths=(package_path,),
    )
    if snapshot_path(package_path) != package_snapshot:
        raise SandboxInstallError("Package changed during inspection; rebuild the plan.")
    return replace(plan, integrity=capture_integrity(plan, (package_snapshot,)))


def execute_sandbox_install_plan(
    plan: SandboxInstallPlan,
    *,
    on_progress: Callable[[InstallTransactionState], None] | None = None,
) -> SandboxInstallResult:
    if not plan.sandbox_mods_path.exists() or not plan.sandbox_mods_path.is_dir():
        raise SandboxInstallError(f"Sandbox Mods directory is not accessible: {plan.sandbox_mods_path}")

    installable_entries = [entry for entry in plan.entries if entry.can_install]
    blocked_entries = [entry for entry in plan.entries if not entry.can_install]

    if not installable_entries:
        raise SandboxInstallError("No installable entries in plan. Resolve preflight warnings first.")

    if blocked_entries:
        names = ", ".join(entry.target_path.name for entry in blocked_entries)
        raise SandboxInstallError(
            "Plan has blocked entries and cannot execute conservatively; "
            f"resolve conflicts first: {names}"
        )

    try:
        validate_integrity(plan)
    except (InstallIntegrityError, OSError) as exc:
        raise SandboxInstallError(str(exc)) from exc

    transaction_id = uuid.uuid4().hex
    staging_root = plan.sandbox_mods_path / f".sdvmm-stage-{transaction_id}"
    journal_path = plan.sandbox_archive_path / f".sdvmm-install-{transaction_id}.json"
    installed_targets: list[Path] = []
    archived_targets: list[Path] = []
    attempted: list[SandboxInstallPlanEntry] = []
    installed_digests: dict[Path, str | None] = {}
    archived_digests: dict[Path, str | None] = {}
    staged_identities: dict[Path, tuple[int, int] | None] = {}
    owned_archives: set[Path] = set()
    pinned_roots = None
    cleanup_allowed = False
    commit_decided = False
    writes_started = False

    def publish(status: str, failure: str | None = None) -> InstallTransactionState:
        state = InstallTransactionState(
            status,
            tuple(installed_targets),
            tuple(archived_targets),
            journal_path,
            failure,
            tuple((path, digest) for path, digest in installed_digests.items() if digest is not None),
            tuple((path, digest) for path, digest in archived_digests.items() if digest is not None),
        )
        # Write intent before changing a target. A crash leaves this record and the
        # staged files; it must never be mistaken for a completed operation.
        write_json_file_atomic(journal_path, {
            "version": 1, "status": status, "failure": failure,
            "mods_root": str(plan.sandbox_mods_path), "staging_root": str(staging_root),
            "installed_targets": [str(p) for p in installed_targets],
            "archived_targets": [str(p) for p in archived_targets],
            "attempted_targets": [str(e.target_path) for e in attempted],
            "entries": [{"target": str(e.target_path), "archive": str(e.archive_path) if e.archive_path else None,
                         "action": e.action, "package": str(e.source_package_path)} for e in plan.entries],
        })
        if on_progress is not None:
            on_progress(state)
        return state

    def roots_unchanged() -> None:
        validate_boundaries(plan)
        if pinned_roots != (snapshot_path(plan.sandbox_mods_path, contents=False),
                            snapshot_path(plan.sandbox_archive_path, contents=False)):
            raise InstallIntegrityError("Install roots changed during execution; recovery stopped.")

    try:
        staging_root.mkdir(parents=False, exist_ok=False)

        installable_entries_by_package: dict[Path, list[SandboxInstallPlanEntry]] = {}
        package_order: list[Path] = []
        for entry in installable_entries:
            source_package_path = entry.source_package_path
            if source_package_path not in installable_entries_by_package:
                installable_entries_by_package[source_package_path] = []
                package_order.append(source_package_path)
            installable_entries_by_package[source_package_path].append(entry)

        package_copies = staging_root / ".packages"
        package_copies.mkdir()
        assert plan.integrity is not None
        seals = {item.path: item for item in plan.integrity.packages}
        for index, package_path in enumerate(package_order):
            staged_package = package_copies / f"{index}{package_path.suffix}"
            shutil.copyfile(package_path, staged_package)
            if snapshot_path(staged_package).digest != seals[package_path.absolute()].digest:
                raise InstallIntegrityError("Package changed while staging; rebuild the plan.")
            for entry in installable_entries_by_package[package_path]:
                staged_target = staging_root / entry.target_path.name
                staged_target.mkdir(parents=True, exist_ok=False)
                _extract_mod_root(
                    package_path=staged_package,
                    source_root=entry.source_root_path,
                    destination=staged_target,
                )
                staged_snapshot = snapshot_path(staged_target)
                installed_digests[entry.target_path] = staged_snapshot.digest
                staged_identities[entry.target_path] = staged_snapshot.identity

        # Recheck every target after slow extraction, before the first live write.
        validate_integrity(plan)
        _ensure_archive_root(plan.sandbox_archive_path)
        pinned_roots = (snapshot_path(plan.sandbox_mods_path, contents=False),
                        snapshot_path(plan.sandbox_archive_path, contents=False))
        publish("in_progress")

        for index, entry in enumerate(installable_entries):
            roots_unchanged()
            if snapshot_path(entry.target_path) != plan.integrity.targets[index]:
                raise InstallIntegrityError(f"Target changed during execution: {entry.target_path}")
            attempted.append(entry)
            publish("in_progress")
            roots_unchanged()
            if snapshot_path(entry.target_path) != plan.integrity.targets[index]:
                raise InstallIntegrityError(f"Target changed before writing: {entry.target_path}")
            writes_started = True
            staged_target = staging_root / entry.target_path.name
            if entry.action == INSTALL_NEW:
                _install_new_target(staged_target=staged_target, target_path=entry.target_path)
                installed_targets.append(entry.target_path)
                installed_digests[entry.target_path] = snapshot_path(entry.target_path).digest
                publish("in_progress")
                continue

            if entry.action == OVERWRITE_WITH_ARCHIVE:
                if entry.archive_path is None:
                    raise SandboxInstallError(
                        f"Overwrite entry missing archive path for target: {entry.target_path}"
                    )

                _overwrite_target_with_archive(
                    staged_target=staged_target,
                    target_path=entry.target_path,
                    archive_path=entry.archive_path,
                    on_archived=owned_archives.add,
                )
                installed_targets.append(entry.target_path)
                archived_targets.append(entry.archive_path)
                installed_digests[entry.target_path] = snapshot_path(entry.target_path).digest
                archived_digests[entry.archive_path] = snapshot_path(entry.archive_path).digest
                publish("in_progress")
                continue

            raise SandboxInstallError(
                f"Blocked entry cannot be executed: {entry.target_path}"
            )

        inventory = scan_mods_directory(
            plan.sandbox_mods_path,
            excluded_paths=(plan.sandbox_archive_path, plan.sandbox_mods_path / ".sdvmm-archive", staging_root),
        )
        # Once final recording starts, its failure may be an uncertain write.
        # Do not undo files behind a potentially persisted completed record.
        commit_decided = True
        publish("completed")
        cleanup_allowed = True

    except Exception as exc:
        if pinned_roots is None or not writes_started:
            cleanup_allowed = True
            if pinned_roots is not None:
                try:
                    publish("rolled_back", f"Stopped before any mod write: {exc}")
                except Exception:
                    pass
            if isinstance(exc, SandboxInstallError):
                raise
            raise SandboxInstallError(f"Sandbox install failed before any mod write: {exc}") from exc
        recovery_errors: list[str] = (
            ["Files were applied, but final recording failed. Installed files and archives were retained."]
            if commit_decided else []
        )
        for entry in reversed(attempted if not commit_decided else []):
            try:
                roots_unchanged()
                original = next(s for s in plan.integrity.targets if s.path == entry.target_path.absolute())
                current = snapshot_path(entry.target_path)
                if current == original:
                    continue
                if original.identity is not None:
                    if entry.archive_path not in owned_archives or snapshot_path(entry.archive_path).digest != original.digest:
                        raise InstallIntegrityError(f"Original archive unavailable or changed: {entry.archive_path}")
                if current.identity is not None:
                    if (current.identity != staged_identities.get(entry.target_path)
                            or current.digest != installed_digests.get(entry.target_path)):
                        raise InstallIntegrityError(f"Target changed externally; preserved for manual recovery: {entry.target_path}")
                    # Keep the new files until recovery of the entire batch succeeds.
                    quarantine = staging_root / f".rollback-{len(attempted) - attempted.index(entry)}"
                    _move_path(entry.target_path, quarantine)
                    if snapshot_path(quarantine).digest != installed_digests.get(entry.target_path):
                        if original.identity is not None and not entry.target_path.exists():
                            _move_path(entry.archive_path, entry.target_path)
                        raise InstallIntegrityError(
                            f"Target changed while entering recovery quarantine: {quarantine}"
                        )
                if original.identity is not None:
                    _move_path(entry.archive_path, entry.target_path)
            except Exception as recovery_exc:
                recovery_errors.append(str(recovery_exc))

        # Describe only changes still present. Unknown outcomes remain partial and
        # are never automatically removed by the normal recovery workflow.
        installed_targets[:] = []
        archived_targets[:] = []
        if pinned_roots is not None:
            for entry in attempted:
                try:
                    roots_unchanged()
                    current = snapshot_path(entry.target_path)
                    if (current.identity is not None and current.identity == staged_identities.get(entry.target_path)
                            and current.digest == installed_digests.get(entry.target_path)):
                        installed_targets.append(entry.target_path)
                    if entry.archive_path in owned_archives and entry.archive_path.exists():
                        archived_targets.append(entry.archive_path)
                except Exception as recovery_exc:
                    recovery_errors.append(str(recovery_exc))
        status = "partial" if recovery_errors else "rolled_back"
        detail = str(exc)
        if recovery_errors:
            detail += " Recovery: " + "; ".join(recovery_errors)
        progress = InstallTransactionState(
            status,
            tuple(installed_targets),
            tuple(archived_targets),
            journal_path,
            detail,
            tuple((path, digest) for path, digest in installed_digests.items() if digest is not None),
            tuple((path, digest) for path, digest in archived_digests.items() if digest is not None),
        )
        if pinned_roots is not None:
            try:
                roots_unchanged()
                publish(status, detail)
            except Exception as record_exc:
                detail += f" Recovery record could not be updated: {record_exc}. Journal: {journal_path}"
        progress = replace(progress, failure_message=detail)
        # A failed write attempt keeps its hidden staging/quarantine tree. The
        # journal identifies it for later inspected cleanup; never recursively
        # delete a path that briefly contained a live target.
        cleanup_allowed = False
        error = exc if isinstance(exc, SandboxInstallError) else SandboxInstallError(f"Sandbox install failed: {detail}")
        error.progress = progress
        if isinstance(error, SandboxFileLockError):
            error.technical_detail += f" Journal: {journal_path}"
        raise error from (None if error is exc else exc)
    finally:
        if cleanup_allowed and staging_root.exists():
            # Never recurse through a path that was redirected during execution.
            try:
                if snapshot_path(plan.sandbox_mods_path, contents=False) == plan.integrity.mods_root:
                    snapshot_path(staging_root)
                    shutil.rmtree(staging_root)
            except (OSError, InstallIntegrityError):
                pass  # Staging is disposable; failure does not erase recovery data.
    return SandboxInstallResult(
        plan=plan,
        installed_targets=tuple(sorted(installed_targets, key=lambda path: path.name.lower())),
        archived_targets=tuple(sorted(archived_targets, key=lambda path: path.name.lower())),
        scan_context_path=plan.sandbox_mods_path,
        inventory=inventory,
        destination_kind=plan.destination_kind,
    )


def remove_mod_to_archive(
    *,
    target_mod_path: Path,
    mods_root: Path,
    archive_root: Path,
) -> Path:
    mods_root_resolved = mods_root.resolve()
    target_mod_resolved = target_mod_path.resolve()

    if not mods_root.exists() or not mods_root.is_dir():
        raise SandboxInstallError(f"Mods directory is not accessible: {mods_root}")

    if not target_mod_path.exists() or not target_mod_path.is_dir():
        raise SandboxInstallError(f"Selected mod folder is not accessible: {target_mod_path}")

    if (
        target_mod_resolved == mods_root_resolved
        or not target_mod_resolved.is_relative_to(mods_root_resolved)
    ):
        raise SandboxInstallError(
            "Selected mod folder must be inside the selected Mods destination."
        )

    _ensure_archive_root(archive_root)
    archive_path = _build_archive_destination(
        archive_root=archive_root,
        target_folder_name=target_mod_path.name,
    )
    try:
        _move_path(target_mod_path, archive_path)
    except Exception as exc:
        detail = f"Could not move mod folder to archive: {target_mod_path} -> {archive_path}: {exc}"
        if _is_likely_windows_lock_error(exc):
            raise SandboxFileLockError(
                _sandbox_file_lock_message(),
                technical_detail=detail,
            ) from exc
        raise SandboxInstallError(
            detail
        ) from exc

    return archive_path


def _mark_duplicate_targets(entries: list[SandboxInstallPlanEntry]) -> list[SandboxInstallPlanEntry]:
    buckets: dict[str, list[SandboxInstallPlanEntry]] = {}
    for entry in entries:
        key = entry.target_path.name.casefold()
        buckets.setdefault(key, []).append(entry)

    updated: list[SandboxInstallPlanEntry] = []
    for entry in entries:
        grouped = buckets[entry.target_path.name.casefold()]
        if len(grouped) < 2:
            updated.append(entry)
            continue

        warnings = list(entry.warnings)
        warnings.append("Multiple package mods map to the same target folder.")
        updated.append(
            replace(
                entry,
                action=BLOCKED,
                archive_path=None,
                can_install=False,
                warnings=tuple(warnings),
            )
        )

    return updated


def _build_plan_warnings(
    entries: list[SandboxInstallPlanEntry],
    inspection: PackageInspectionResult,
    *,
    allow_overwrite: bool,
) -> list[str]:
    warnings: list[str] = []

    if not inspection.mods:
        warnings.append("Package inspection found no installable mods.")

    has_existing_targets = any(entry.target_exists for entry in entries)
    has_overwrite_entries = any(entry.action == OVERWRITE_WITH_ARCHIVE for entry in entries)

    if has_existing_targets and not allow_overwrite:
        warnings.append(
            "One or more target folders already exist. Enable overwrite mode and rebuild plan to replace them."
        )

    if has_overwrite_entries:
        warnings.append(
            "Overwrite mode will archive existing target folders before replacement. "
            "An ordinary failure rolls back the whole batch; an interruption or locked "
            "file may still need manual recovery from History."
        )
        warnings.append(
            "Overwrite updates preserve existing config artifacts by default when present. "
            "When both old and new config.json exist, Cinderleaf adds new default settings "
            "without changing existing user values."
        )

    if any(not entry.can_install for entry in entries):
        warnings.append("Plan has blocked entries; execution requires all entries to be installable.")

    return warnings


def _derive_target_folder_name(source_root: str, unique_id: str, name: str) -> str:
    root_path = PurePosixPath(source_root)
    if source_root != "." and root_path.name:
        return root_path.name

    base = _sanitize_name(unique_id) or _sanitize_name(name)
    return base or "installed_mod"


def _sanitize_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("._")


def _build_archive_destination(archive_root: Path, target_folder_name: str) -> Path:
    for idx in range(1, 10_000):
        candidate = archive_root / f"{target_folder_name}__sdvmm_archive_{idx:03d}"
        if not candidate.exists():
            return candidate

    raise SandboxInstallError(
        f"Could not allocate archive path for target '{target_folder_name}' under {archive_root}."
    )


def _ensure_archive_root(archive_root: Path) -> None:
    if archive_root.exists() and not archive_root.is_dir():
        raise SandboxInstallError(f"Sandbox archive path is not a directory: {archive_root}")

    archive_root.mkdir(parents=True, exist_ok=True)


def _install_new_target(staged_target: Path, target_path: Path) -> None:
    if target_path.exists():
        raise SandboxInstallError(
            f"Install plan is stale: target already exists, rebuild plan first: {target_path}"
        )

    _move_path(staged_target, target_path)


def _overwrite_target_with_archive(
    staged_target: Path, target_path: Path, archive_path: Path,
    *, on_archived: Callable[[Path], None] | None = None,
) -> None:
    if not target_path.exists() or not target_path.is_dir():
        raise SandboxInstallError(
            f"Install plan is stale: overwrite target is not an existing directory: {target_path}"
        )

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise SandboxInstallError(f"Archive path already exists; rebuild plan first: {archive_path}")
    staged_snapshot = snapshot_path(staged_target)

    try:
        _move_path(target_path, archive_path)
        if on_archived is not None:
            on_archived(archive_path)
    except Exception as exc:
        detail = (
            f"Could not archive existing target before overwrite: "
            f"{target_path} -> {archive_path}: {exc}"
        )
        if _is_likely_windows_lock_error(exc):
            raise SandboxFileLockError(
                _sandbox_file_lock_message(),
                technical_detail=detail,
            ) from exc
        raise SandboxInstallError(
            detail
        ) from exc

    try:
        _move_path(staged_target, target_path)
        _restore_preserved_config_artifacts(archived_target=archive_path, target_path=target_path)
    except Exception as replace_exc:
        cleanup_errors: list[str] = []

        if target_path.exists():
            try:
                current = snapshot_path(target_path)
                if current.identity != staged_snapshot.identity or current.digest != staged_snapshot.digest:
                    raise InstallIntegrityError("Replacement target changed or is not owned by this attempt; preserved for manual recovery.")
                if staged_target.exists():
                    raise InstallIntegrityError(
                        "Replacement quarantine is occupied; current target was preserved for manual recovery."
                    )
                # Keep the verified replacement in the transaction's retained
                # staging tree. Recovery must not recursively delete a path that
                # was live, even when it still matches our content seal.
                _move_path(target_path, staged_target)
            except Exception as cleanup_exc:
                cleanup_errors.append(f"cleanup failed: {cleanup_exc}")

        recovered = False
        try:
            _move_path(archive_path, target_path)
            recovered = True
        except Exception as restore_exc:
            cleanup_errors.append(f"restore failed: {restore_exc}")

        details = ""
        if cleanup_errors:
            details = " Details: " + "; ".join(cleanup_errors)

        if recovered:
            raise SandboxInstallError(
                "Replacement failed after archive. Best-effort recovery restored original target. "
                f"Replace error: {replace_exc}.{details}"
            ) from replace_exc

        raise SandboxInstallError(
            "Replacement failed after archive and best-effort recovery could not restore original target. "
            f"Replace error: {replace_exc}.{details}"
        ) from replace_exc


def _config_artifact_names(mod_root: Path) -> tuple[str, ...]:
    return tuple(path.name for path in _iter_config_artifacts(mod_root))


def _iter_config_artifacts(mod_root: Path) -> tuple[Path, ...]:
    artifacts: list[Path] = []
    for candidate_name in _CONFIG_ARTIFACT_NAMES:
        candidate_path = mod_root / candidate_name
        if not candidate_path.exists():
            continue
        if candidate_path.is_file() or candidate_path.is_dir():
            artifacts.append(candidate_path)
    return tuple(artifacts)


def _restore_preserved_config_artifacts(*, archived_target: Path, target_path: Path) -> None:
    for artifact in _iter_config_artifacts(archived_target):
        relative_path = artifact.relative_to(archived_target)
        destination_path = target_path / relative_path
        if artifact.is_file():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if destination_path.exists() and destination_path.is_dir():
                _remove_path(destination_path)
            if _try_merge_preserved_config_json(
                archived_config_path=artifact,
                installed_config_path=destination_path,
            ):
                continue
            shutil.copy2(artifact, destination_path)
            continue

        if destination_path.exists() and destination_path.is_file():
            _remove_path(destination_path)
        destination_path.mkdir(parents=True, exist_ok=True)
        for source_file in artifact.rglob("*"):
            if not source_file.is_file():
                continue
            nested_relative_path = source_file.relative_to(artifact)
            nested_destination_path = destination_path / nested_relative_path
            nested_destination_path.parent.mkdir(parents=True, exist_ok=True)
            if nested_destination_path.exists() and nested_destination_path.is_dir():
                _remove_path(nested_destination_path)
            shutil.copy2(source_file, nested_destination_path)


def _try_merge_preserved_config_json(
    *,
    archived_config_path: Path,
    installed_config_path: Path,
) -> bool:
    if archived_config_path.name.casefold() != "config.json":
        return False
    if not installed_config_path.exists() or not installed_config_path.is_file():
        return False

    try:
        preserved_config = json.loads(archived_config_path.read_text(encoding="utf-8"))
        installed_config = json.loads(installed_config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    if not isinstance(preserved_config, dict) or not isinstance(installed_config, dict):
        return False

    merged_config, added_key_count = _merge_json_config_objects(
        preserved_config,
        installed_config,
    )
    if added_key_count <= 0:
        return False

    installed_config_path.write_text(
        json.dumps(merged_config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def _merge_json_config_objects(
    preserved_config: dict[str, Any],
    installed_config: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    merged: dict[str, Any] = {}
    added_key_count = 0

    for key, preserved_value in preserved_config.items():
        installed_value = installed_config.get(key)
        if isinstance(preserved_value, dict) and isinstance(installed_value, dict):
            merged_value, nested_added_key_count = _merge_json_config_objects(
                preserved_value,
                installed_value,
            )
            merged[key] = merged_value
            added_key_count += nested_added_key_count
            continue
        merged[key] = preserved_value

    for key, installed_value in installed_config.items():
        if key in merged:
            continue
        merged[key] = installed_value
        added_key_count += 1

    return merged, added_key_count


def _move_path(source: Path, destination: Path) -> None:
    source.rename(destination)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return

    path.unlink(missing_ok=True)


def _extract_mod_root(package_path: Path, source_root: str, destination: Path) -> None:
    try:
        extract_archive_root_to_directory(
            archive_path=package_path,
            source_root=source_root,
            destination=destination,
        )
    except ArchiveToolError as exc:
        raise SandboxInstallError(str(exc)) from exc
    if not (destination / "manifest.json").exists():
        raise SandboxInstallError(
            f"No usable files extracted for source root '{source_root}'."
        )


def _is_likely_windows_lock_error(exc: BaseException) -> bool:
    queue: list[BaseException] = [exc]
    seen: set[int] = set()
    while queue:
        current = queue.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))

        if isinstance(current, PermissionError):
            return True

        if isinstance(current, OSError):
            if current.errno in _LOCK_ERRNOS:
                return True
            if getattr(current, "winerror", None) in _LOCK_WINERRORS:
                return True
            lowered = str(current).casefold()
            if (
                "being used by another process" in lowered
                or "access is denied" in lowered
                or "permission denied" in lowered
            ):
                return True

        cause = getattr(current, "__cause__", None)
        if isinstance(cause, BaseException):
            queue.append(cause)
        context = getattr(current, "__context__", None)
        if isinstance(context, BaseException):
            queue.append(context)

    return False


def _sandbox_file_lock_message() -> str:
    return (
        "Sandbox write failed because Windows is still using files in the target mod folder. "
        "Close Explorer windows or preview panes for that folder, any editor or terminal using the mod, "
        "and the sandbox game or SMAPI if it is still running, then try again."
    )
