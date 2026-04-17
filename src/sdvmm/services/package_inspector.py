from __future__ import annotations

from pathlib import Path, PurePosixPath
import tempfile
import zipfile

from sdvmm.domain.models import (
    PackageFinding,
    PackageInspectionResult,
    PackageModEntry,
    PackageWarning,
)
from sdvmm.domain.package_codes import (
    DIRECT_SINGLE_MOD_PACKAGE,
    INVALID_MANIFEST_PACKAGE,
    MULTI_MOD_PACKAGE,
    NESTED_SINGLE_MOD_PACKAGE,
    NO_USABLE_MANIFEST_FOUND,
    TOO_DEEP_UNSUPPORTED_PACKAGE,
)
from sdvmm.domain.unique_id import canonicalize_unique_id
from sdvmm.services.archive_tools import extract_archive_to_directory
from sdvmm.services.archive_tools import is_supported_package_archive
from sdvmm.services.dependency_preflight import evaluate_package_dependencies
from sdvmm.services.manifest_parser import parse_manifest_text

MAX_PACKAGE_MANIFEST_DEPTH = 3
_MANIFEST_FILE_NAME = "manifest.json"


def inspect_package_archive(package_path: Path) -> PackageInspectionResult:
    if not is_supported_package_archive(package_path):
        raise ValueError(f"Unsupported package archive type: {package_path.suffix}")
    if package_path.suffix.lower() == ".zip":
        return _inspect_zip_package(package_path)
    return _inspect_extracted_package(package_path)


def inspect_zip_package(package_path: Path) -> PackageInspectionResult:
    return inspect_package_archive(package_path)


def _inspect_zip_package(package_path: Path) -> PackageInspectionResult:
    with zipfile.ZipFile(package_path, "r") as archive:
        manifest_entries = _find_zip_manifest_entries(archive)
        allowed_entries, too_deep_entries = _split_manifest_depth(manifest_entries)

        mods: list[PackageModEntry] = []
        warnings: list[PackageWarning] = []

        for manifest_entry in allowed_entries:
            parsed_mod, parsed_warnings = _parse_zip_manifest_entry(archive, manifest_entry)
            warnings.extend(parsed_warnings)
            if parsed_mod is not None:
                mods.append(parsed_mod)

    return _build_package_inspection_result(
        package_path=package_path,
        mods=mods,
        warnings=warnings,
        too_deep_entries=too_deep_entries,
    )


def _inspect_extracted_package(package_path: Path) -> PackageInspectionResult:
    with tempfile.TemporaryDirectory(prefix="sdvmm-package-inspection-") as temp_dir:
        extracted_root = Path(temp_dir)
        extract_archive_to_directory(archive_path=package_path, destination=extracted_root)

        manifest_entries = _find_extracted_manifest_entries(extracted_root)
        allowed_entries, too_deep_entries = _split_manifest_depth(manifest_entries)

        mods: list[PackageModEntry] = []
        warnings: list[PackageWarning] = []

        for manifest_entry in allowed_entries:
            parsed_mod, parsed_warnings = _parse_extracted_manifest_entry(
                extracted_root,
                manifest_entry,
            )
            warnings.extend(parsed_warnings)
            if parsed_mod is not None:
                mods.append(parsed_mod)

    return _build_package_inspection_result(
        package_path=package_path,
        mods=mods,
        warnings=warnings,
        too_deep_entries=too_deep_entries,
    )


def _build_package_inspection_result(
    *,
    package_path: Path,
    mods: list[PackageModEntry],
    warnings: list[PackageWarning],
    too_deep_entries: list[str],
) -> PackageInspectionResult:
    mods.sort(key=lambda mod: (canonicalize_unique_id(mod.unique_id), mod.manifest_path.lower()))
    warnings.sort(key=lambda warning: (warning.code, warning.manifest_path.lower()))

    findings = _build_findings(
        mods=mods,
        warnings=warnings,
        too_deep_entries=too_deep_entries,
    )
    dependency_findings = evaluate_package_dependencies(
        package_mods=tuple(mods),
        installed_mods=None,
        source="package_inspection",
    )

    return PackageInspectionResult(
        package_path=package_path,
        mods=tuple(mods),
        warnings=tuple(warnings),
        findings=findings,
        dependency_findings=dependency_findings,
    )


def _find_zip_manifest_entries(archive: zipfile.ZipFile) -> list[str]:
    entries: set[str] = set()
    for info in archive.infolist():
        if info.is_dir():
            continue
        normalized_filename = info.filename.replace("\\", "/").strip().lstrip("/")
        lowered = normalized_filename.casefold()
        if lowered != _MANIFEST_FILE_NAME and not lowered.endswith(f"/{_MANIFEST_FILE_NAME}"):
            continue
        entries.add(normalized_filename)
    return sorted(entries, key=lambda value: value.lower())


def _find_extracted_manifest_entries(extracted_root: Path) -> list[str]:
    entries = [
        str(path.relative_to(extracted_root).as_posix())
        for path in extracted_root.rglob("*")
        if path.is_file() and path.name.casefold() == _MANIFEST_FILE_NAME
    ]
    entries.sort(key=lambda value: value.lower())
    return entries


def _split_manifest_depth(entries: list[str]) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    too_deep: list[str] = []

    for manifest_entry in entries:
        depth = _manifest_depth(manifest_entry)
        if depth <= MAX_PACKAGE_MANIFEST_DEPTH:
            allowed.append(manifest_entry)
        else:
            too_deep.append(manifest_entry)

    return allowed, too_deep


def _manifest_depth(manifest_entry: str) -> int:
    return max(len(PurePosixPath(manifest_entry).parts) - 1, 0)


def _parse_zip_manifest_entry(
    archive: zipfile.ZipFile,
    manifest_entry: str,
) -> tuple[PackageModEntry | None, list[PackageWarning]]:
    try:
        raw_bytes = _read_zip_entry_bytes(archive=archive, manifest_entry=manifest_entry)
    except KeyError:
        warning = PackageWarning(
            code="manifest_read_error",
            message="manifest.json entry disappeared while reading package archive",
            manifest_path=manifest_entry,
        )
        return None, [warning]
    except OSError as exc:
        warning = PackageWarning(
            code="manifest_read_error",
            message=f"Could not read manifest entry: {exc}",
            manifest_path=manifest_entry,
        )
        return None, [warning]

    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        warning = PackageWarning(
            code="malformed_manifest",
            message=f"manifest.json is not valid UTF-8 text: {exc}",
            manifest_path=manifest_entry,
        )
        return None, [warning]

    return _parse_manifest_text_entry(raw_text=raw_text, manifest_entry=manifest_entry)


def _read_zip_entry_bytes(*, archive: zipfile.ZipFile, manifest_entry: str) -> bytes:
    try:
        return archive.read(manifest_entry)
    except KeyError:
        normalized_target = manifest_entry.replace("\\", "/").lstrip("/")
        candidates = []
        backslash_variant = normalized_target.replace("/", "\\")
        if backslash_variant != normalized_target:
            candidates.append(backslash_variant)
        candidates.extend(
            info.filename
            for info in archive.infolist()
            if not info.is_dir()
            and info.filename.replace("\\", "/").lstrip("/") == normalized_target
        )

        seen: set[str] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                return archive.read(candidate)
            except KeyError:
                continue
        raise


def _parse_extracted_manifest_entry(
    extracted_root: Path,
    manifest_entry: str,
) -> tuple[PackageModEntry | None, list[PackageWarning]]:
    manifest_path = extracted_root / Path(*PurePosixPath(manifest_entry).parts)
    try:
        raw_text = manifest_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        warning = PackageWarning(
            code="malformed_manifest",
            message=f"manifest.json is not valid UTF-8 text: {exc}",
            manifest_path=manifest_entry,
        )
        return None, [warning]
    except OSError as exc:
        warning = PackageWarning(
            code="manifest_read_error",
            message=f"Could not read manifest entry: {exc}",
            manifest_path=manifest_entry,
        )
        return None, [warning]

    return _parse_manifest_text_entry(raw_text=raw_text, manifest_entry=manifest_entry)


def _parse_manifest_text_entry(
    *,
    raw_text: str,
    manifest_entry: str,
) -> tuple[PackageModEntry | None, list[PackageWarning]]:
    manifest_path = Path(manifest_entry)
    parse_result = parse_manifest_text(
        raw_text=raw_text,
        mod_dir=manifest_path.parent,
        manifest_path=manifest_path,
    )

    warnings = [
        PackageWarning(
            code=warning.code,
            message=warning.message,
            manifest_path=manifest_entry,
        )
        for warning in parse_result.warnings
    ]

    if parse_result.manifest is None:
        return None, warnings

    manifest = parse_result.manifest
    mod_entry = PackageModEntry(
        name=manifest.name,
        unique_id=manifest.unique_id,
        version=manifest.version,
        manifest_path=manifest_entry,
        dependencies=manifest.dependencies,
        update_keys=manifest.update_keys,
    )
    return mod_entry, warnings


def _build_findings(
    mods: list[PackageModEntry],
    warnings: list[PackageWarning],
    too_deep_entries: list[str],
) -> tuple[PackageFinding, ...]:
    findings: list[PackageFinding] = []

    if mods:
        if len(mods) == 1:
            depth = _manifest_depth(mods[0].manifest_path)
            kind = DIRECT_SINGLE_MOD_PACKAGE if depth <= 1 else NESTED_SINGLE_MOD_PACKAGE
            message = (
                "Single mod found at package root layout."
                if kind == DIRECT_SINGLE_MOD_PACKAGE
                else "Single mod found in nested package layout."
            )
            findings.append(
                PackageFinding(
                    kind=kind,
                    message=message,
                    related_paths=(mods[0].manifest_path,),
                )
            )
        else:
            findings.append(
                PackageFinding(
                    kind=MULTI_MOD_PACKAGE,
                    message=f"Package contains {len(mods)} detectable mods.",
                    related_paths=tuple(mod.manifest_path for mod in mods),
                )
            )

        invalid_warning_paths = tuple(
            warning.manifest_path for warning in warnings if warning.code in _INVALID_WARNING_CODES
        )
        if invalid_warning_paths:
            findings.append(
                PackageFinding(
                    kind=INVALID_MANIFEST_PACKAGE,
                    message="Some manifests in package are invalid and were skipped.",
                    related_paths=invalid_warning_paths,
                )
            )

        if too_deep_entries:
            findings.append(
                PackageFinding(
                    kind=TOO_DEEP_UNSUPPORTED_PACKAGE,
                    message="Some manifests are deeper than supported package inspection depth.",
                    related_paths=tuple(too_deep_entries),
                )
            )

        return tuple(findings)

    if any(warning.code in _INVALID_WARNING_CODES for warning in warnings):
        findings.append(
            PackageFinding(
                kind=INVALID_MANIFEST_PACKAGE,
                message="Package has manifest files but none parsed successfully.",
                related_paths=tuple(warning.manifest_path for warning in warnings),
            )
        )
    elif too_deep_entries:
        findings.append(
            PackageFinding(
                kind=TOO_DEEP_UNSUPPORTED_PACKAGE,
                message="Manifest files exist only in unsupported deep paths.",
                related_paths=tuple(too_deep_entries),
            )
        )
    else:
        findings.append(
            PackageFinding(
                kind=NO_USABLE_MANIFEST_FOUND,
                message="No usable manifest.json found in supported package depth.",
                related_paths=tuple(),
            )
        )

    return tuple(findings)


_INVALID_WARNING_CODES = {
    "invalid_manifest",
    "malformed_manifest",
    "manifest_read_error",
}
