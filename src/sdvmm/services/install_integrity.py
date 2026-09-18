"""Read-only seals for reviewed archive installs; never follow links in mod trees."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

from sdvmm.domain.models import InstallPathSnapshot, InstallPlanIntegrity, SandboxInstallPlan


class InstallIntegrityError(ValueError):
    pass


def paths_overlap(left: Path, right: Path) -> bool:
    left, right = left.resolve(), right.resolve()
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _reject_link(path: Path) -> None:
    if path.is_symlink() or path.is_junction():
        raise InstallIntegrityError(f"Linked install path is not supported: {path}")


def _check_ancestors(path: Path) -> None:
    for parent in (path, *path.parents):
        _reject_link(parent)


def snapshot_path(path: Path, *, contents: bool = True) -> InstallPathSnapshot:
    path = path.absolute()
    _check_ancestors(path)
    resolved = path.resolve()
    ancestors = tuple((parent, info.st_dev, info.st_ino)
                      for parent in path.parents if parent.exists()
                      for info in (parent.stat(),))
    if not path.exists():
        return InstallPathSnapshot(path, resolved, None, None, ancestors)
    info = path.stat()
    identity = (info.st_dev, info.st_ino)
    if not contents:
        if not path.is_dir():
            raise InstallIntegrityError(f"Install root is not a directory: {path}")
        return InstallPathSnapshot(path, resolved, identity, None, ancestors)
    digest = hashlib.sha256()

    def visit(current: Path) -> None:
        _reject_link(current)
        before = current.stat()
        digest.update(current.relative_to(path).as_posix().encode("utf-8") + b"\0")
        if stat.S_ISDIR(before.st_mode):
            digest.update(b"directory\0")
            for child in sorted(current.iterdir(), key=lambda p: p.name):
                visit(child)
        elif stat.S_ISREG(before.st_mode):
            digest.update(b"file\0")
            digest.update(before.st_size.to_bytes(8, "big"))
            with current.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            after = current.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns
            ):
                raise InstallIntegrityError(f"File changed while checking install plan: {current}")
        else:
            raise InstallIntegrityError(f"Unsupported install file: {current}")

    visit(path)
    return InstallPathSnapshot(path, resolved, identity, digest.hexdigest(), ancestors)


def validate_boundaries(plan: SandboxInstallPlan) -> None:
    root = plan.sandbox_mods_path.resolve()
    archive = plan.sandbox_archive_path.resolve()
    _check_ancestors(plan.sandbox_mods_path.absolute())
    _check_ancestors(plan.sandbox_archive_path.absolute())
    if archive == root or root.is_relative_to(archive):
        raise InstallIntegrityError("The archive cannot contain or equal the Mods root.")
    if plan.protected_mods_path is not None:
        if paths_overlap(plan.sandbox_mods_path, plan.protected_mods_path):
            raise InstallIntegrityError("Sandbox and real Mods folders overlap.")
        if paths_overlap(plan.sandbox_archive_path, plan.protected_mods_path):
            raise InstallIntegrityError("Sandbox archive and real Mods folders overlap.")
    targets: list[Path] = []
    archives: set[Path] = set()
    for entry in plan.entries:
        target = entry.target_path.resolve()
        _check_ancestors(entry.target_path.absolute())
        if target == root or not target.is_relative_to(root) or paths_overlap(target, archive):
            raise InstallIntegrityError(f"Target escapes or overlaps an install boundary: {entry.target_path}")
        if any(paths_overlap(target, prior) for prior in targets):
            raise InstallIntegrityError(f"Install targets overlap: {entry.target_path}")
        targets.append(target)
        if entry.archive_path is not None:
            _check_ancestors(entry.archive_path.absolute())
            candidate = entry.archive_path.resolve()
            if candidate.parent != archive or candidate in archives:
                raise InstallIntegrityError(f"Archive target is outside its reviewed root or duplicated: {candidate}")
            archives.add(candidate)


def capture_integrity(plan: SandboxInstallPlan, packages: tuple[InstallPathSnapshot, ...]) -> InstallPlanIntegrity:
    # Blocked plans remain displayable, but can never execute.
    if all(entry.can_install for entry in plan.entries):
        validate_boundaries(plan)
    return InstallPlanIntegrity(
        packages=packages,
        targets=tuple(snapshot_path(entry.target_path) for entry in plan.entries),
        mods_root=snapshot_path(plan.sandbox_mods_path, contents=False),
        archive_root=snapshot_path(plan.sandbox_archive_path, contents=False),
        manifests=snapshot_manifest_context(plan.sandbox_mods_path, plan.sandbox_archive_path),
    )


def snapshot_manifest_context(root: Path, archive: Path) -> tuple[InstallPathSnapshot, ...]:
    """Seal the dependency/target-discovery inputs, not every unrelated asset."""
    found: list[InstallPathSnapshot] = []
    def visit(directory: Path) -> None:
        _reject_link(directory)
        for child in sorted(directory.iterdir(), key=lambda p: p.name):
            if child.name.startswith(".") or child.resolve() == archive.resolve():
                continue
            _reject_link(child)
            if child.is_dir():
                visit(child)
            elif child.name.casefold() == "manifest.json":
                found.append(snapshot_path(child))
    visit(root)
    return tuple(found)


def validate_integrity(plan: SandboxInstallPlan) -> None:
    seal = plan.integrity
    if seal is None:
        raise InstallIntegrityError("Install plan has no review seal; rebuild it first.")
    validate_boundaries(plan)
    expected_packages = {entry.source_package_path.absolute() for entry in plan.entries}
    if expected_packages != {item.path for item in seal.packages}:
        raise InstallIntegrityError("Install package selection changed; rebuild the plan.")
    if tuple(entry.target_path.absolute() for entry in plan.entries) != tuple(item.path for item in seal.targets):
        raise InstallIntegrityError("Install targets changed; rebuild the plan.")
    for expected in (seal.mods_root, seal.archive_root):
        if snapshot_path(expected.path, contents=False) != expected:
            raise InstallIntegrityError(f"Install root changed; rebuild the plan: {expected.path}")
    if plan.sandbox_mods_path.absolute() != seal.mods_root.path or plan.sandbox_archive_path.absolute() != seal.archive_root.path:
        raise InstallIntegrityError("Install roots changed; rebuild the plan.")
    for expected in (*seal.packages, *seal.targets):
        if snapshot_path(expected.path) != expected:
            raise InstallIntegrityError(f"Install plan is stale; reviewed files changed: {expected.path}")
    if snapshot_manifest_context(plan.sandbox_mods_path, plan.sandbox_archive_path) != seal.manifests:
        raise InstallIntegrityError("Installed mod manifests changed; rebuild the dependency review.")
    for entry in plan.entries:
        if entry.archive_path is not None and os.path.lexists(entry.archive_path):
            raise InstallIntegrityError(f"Archive path now exists; rebuild the plan: {entry.archive_path}")
