from __future__ import annotations

from pathlib import Path

from sdvmm.app.shell_service import DiscoveryContextCorrelation
from sdvmm.app.inventory_presenter import (
    build_archive_restore_result_text,
    build_findings_text,
    build_mod_rollback_result_text,
    build_mod_removal_result_text,
    build_discovery_search_text,
    build_downloads_intake_text,
    build_environment_status_text,
    build_package_inspection_text,
    build_sandbox_install_plan_text,
    build_smapi_log_report_text,
    build_smapi_update_status_text,
    build_update_report_text,
)
from sdvmm.domain.models import (
    ArchiveRestorePlan,
    ArchiveRestoreResult,
    ArchivedModEntry,
    DownloadsIntakeResult,
    DownloadsWatchPollResult,
    GameEnvironmentStatus,
    ModDiscoveryEntry,
    ModDiscoveryResult,
    InstalledMod,
    ModRemovalPlan,
    ModRemovalResult,
    ModsInventory,
    ModUpdateReport,
    ModUpdateStatus,
    ModRollbackPlan,
    ModRollbackResult,
    PackageFinding,
    PackageInspectionResult,
    PackageModEntry,
    PackageWarning,
    SmapiLogFinding,
    SmapiMissingDependency,
    SmapiLogReport,
    SmapiUpdateStatus,
    SandboxInstallPlan,
    SandboxInstallPlanEntry,
)


def _assert_contains_any_casefold(text: str, *candidates: str) -> None:
    lowered = text.casefold()
    assert any(candidate.casefold() in lowered for candidate in candidates), (
        f"Expected one of {candidates!r} in text:\n{text}"
    )


def test_update_report_text_is_human_readable_and_includes_next_step() -> None:
    report = ModUpdateReport(
        statuses=(
            ModUpdateStatus(
                unique_id="Sample.Mod",
                name="Sample Mod",
                folder_path=Path("/tmp/SampleMod"),
                installed_version="1.0.0",
                remote_version="1.1.0",
                state="update_available",
                remote_link=None,
                message="Remote version is newer than installed version.",
            ),
        )
    )

    text = build_update_report_text(report)

    _assert_contains_any_casefold(text, "Update Awareness", "Panorama de atualizações")
    _assert_contains_any_casefold(text, "Update available", "Atualização disponível")
    _assert_contains_any_casefold(text, "Recommended next step", "Próximo passo recomendado")
    _assert_contains_any_casefold(text, "Open remote page", "Abrir página remota")


def test_findings_text_uses_inactive_rows_language() -> None:
    inventory = ModsInventory(
        mods=tuple(),
        parse_warnings=tuple(),
        duplicate_unique_ids=tuple(),
        missing_required_dependencies=tuple(),
        scan_entry_findings=tuple(),
        ignored_entries=tuple(),
        disabled_mods=(
            InstalledMod(
                unique_id="Sample.Inactive",
                name="Inactive Mod",
                version="1.0.0",
                folder_path=Path("/tmp/Mods/InactiveMod"),
                manifest_path=Path("/tmp/Mods/InactiveMod/manifest.json"),
                dependencies=tuple(),
            ),
        ),
    )

    text = build_findings_text(inventory)

    _assert_contains_any_casefold(text, "Inactive rows detected: 1", "Linhas inativas detectadas: 1")
    assert "Disabled rows detected" not in text
    _assert_contains_any_casefold(
        text,
        "Review inactive rows in Library and enable any mods you want active in this view.",
        "Revise as linhas inativas na Biblioteca e ative os mods que você quer deixar ativos nesta visualização.",
    )


def test_mod_removal_result_text_lists_grouped_included_folders() -> None:
    root = Path("/tmp/Mods")
    container = root / "PackFolder"
    result = ModRemovalResult(
        plan=ModRemovalPlan(
            destination_kind="configured_real_mods",
            mods_path=root,
            archive_path=Path("/tmp/Archive"),
            target_mod_path=container,
            included_mod_paths=(
                container / "ComponentA",
                container / "ComponentB",
            ),
        ),
        removed_target=container,
        archived_target=Path("/tmp/Archive/PackFolder__sdvmm_archive_001"),
        scan_context_path=root,
        inventory=ModsInventory(
            mods=tuple(),
            parse_warnings=tuple(),
            duplicate_unique_ids=tuple(),
            missing_required_dependencies=tuple(),
            scan_entry_findings=tuple(),
            ignored_entries=tuple(),
        ),
        included_mod_paths=(
            container / "ComponentA",
            container / "ComponentB",
        ),
        destination_kind="configured_real_mods",
    )

    text = build_mod_removal_result_text(result)

    assert "Included installed folders: 2" in text
    assert str(container / "ComponentA") in text
    assert str(container / "ComponentB") in text


def test_environment_text_clarifies_invalid_path_next_step() -> None:
    status = GameEnvironmentStatus(
        game_path=Path("/tmp/not-game"),
        mods_path=Path("/tmp/not-game/Mods"),
        smapi_path=None,
        state_codes=("invalid_game_path", "mods_path_detected"),
        notes=tuple(),
    )

    text = build_environment_status_text(status)

    _assert_contains_any_casefold(text, "Environment Detection", "Detecção do ambiente")
    _assert_contains_any_casefold(text, "Invalid game path", "Caminho do jogo inválido")
    _assert_contains_any_casefold(text, "Recommended next step", "Próximo passo recomendado")
    _assert_contains_any_casefold(text, "Pick the Stardew Valley install folder", "Escolha a pasta de instalação do Stardew Valley")


def test_smapi_update_text_highlights_manual_update_guidance() -> None:
    status = SmapiUpdateStatus(
        state="update_available",
        game_path=Path("/tmp/game"),
        smapi_path=Path("/tmp/game/StardewModdingAPI"),
        installed_version="4.4.0",
        latest_version="4.5.1",
        update_page_url="https://github.com/Pathoschild/SMAPI/releases/tag/4.5.1",
        message="SMAPI update available: installed 4.4.0, latest 4.5.1.",
    )

    text = build_smapi_update_status_text(status)

    _assert_contains_any_casefold(text, "SMAPI Update Awareness", "Visão geral da atualização do SMAPI")
    _assert_contains_any_casefold(text, "Status: SMAPI update available", "Status: Atualização do SMAPI disponível")
    _assert_contains_any_casefold(text, "Recommended next step", "Próximo passo recomendado")
    _assert_contains_any_casefold(text, "Open the SMAPI page and update SMAPI manually", "Abra a página do SMAPI e atualize o SMAPI manualmente")


def test_smapi_log_report_text_highlights_missing_dependencies_guidance() -> None:
    report = SmapiLogReport(
        state="parsed",
        source="auto_detected",
        log_path=Path("/tmp/SMAPI-latest.txt"),
        game_path=Path("/tmp/Game"),
        findings=(
            SmapiLogFinding(
                kind="missing_dependency",
                line_number=120,
                message="Fancy Pack because it needs mods which aren't installed (Pathoschild.ContentPatcher)",
            ),
        ),
        missing_dependencies=(
            SmapiMissingDependency(
                requiring_mod_name="Fancy Pack",
                dependency_unique_id="Pathoschild.ContentPatcher",
            ),
        ),
        message="Parsed SMAPI log: errors=0, warnings=0, failed_mods=0, missing_dependencies=1, runtime_issues=0.",
    )

    text = build_smapi_log_report_text(report)

    _assert_contains_any_casefold(text, "SMAPI Log Troubleshooting", "Análise do log do SMAPI")
    _assert_contains_any_casefold(text, "Log parsed", "Log analisado")
    _assert_contains_any_casefold(text, "missing dependencies=1", "dependências ausentes=1", "missing_dependencies=1")
    _assert_contains_any_casefold(text, "Install missing dependencies first", "Instale primeiro as dependências ausentes")


def test_downloads_intake_text_shows_classification_summary_and_action() -> None:
    intake = DownloadsIntakeResult(
        package_path=Path("/tmp/broken.zip"),
        classification="unusable_package",
        message="Package has no usable manifests in supported depth.",
        mods=tuple(),
        matched_installed_unique_ids=tuple(),
        warnings=tuple(),
        findings=tuple(),
    )
    result = DownloadsWatchPollResult(
        watched_path=Path("/tmp/Downloads"),
        known_zip_paths=(Path("/tmp/Downloads/broken.zip"),),
        intakes=(intake,),
    )

    text = build_downloads_intake_text(result)

    _assert_contains_any_casefold(text, "Downloads Intake", "Entrada de downloads")
    _assert_contains_any_casefold(text, "Intake summary", "Resumo da entrada")
    _assert_contains_any_casefold(text, "Unusable package: 1", "Pacote não utilizável: 1", "Pacote inutilizável: 1")
    _assert_contains_any_casefold(text, "recommended next step", "próximo passo recomendado")
    _assert_contains_any_casefold(text, "Not actionable", "Não acionável")


def test_discovery_search_text_shows_compatibility_and_next_step() -> None:
    result = ModDiscoveryResult(
        query="spacecore",
        provider="smapi_compatibility_list",
        results=(
            ModDiscoveryEntry(
                name="SpaceCore",
                unique_id="spacechase0.SpaceCore",
                author="spacechase0",
                provider="smapi_compatibility_list",
                source_provider="nexus",
                source_page_url="https://www.nexusmods.com/stardewvalley/mods/1348",
                compatibility_state="compatible",
                compatibility_status="ok",
                compatibility_summary="Compatible on latest SMAPI.",
            ),
        ),
    )

    correlation = DiscoveryContextCorrelation(
        entry=result.results[0],
        installed_match_unique_id="spacechase0.SpaceCore",
        update_state="update_available",
        provider_relation="provider_aligned",
        provider_relation_note="Discovery source matches tracked update provider (Nexus).",
        context_summary="Already installed (spacechase0.SpaceCore); update is available in current metadata report",
        next_step="Open source page, download manually, let watcher detect the zip, then plan a safe update/replace.",
    )

    text = build_discovery_search_text(result, (correlation,))

    _assert_contains_any_casefold(text, "Mod Discovery", "Descoberta de mods")
    _assert_contains_any_casefold(text, "SMAPI compatibility index", "índice de compatibilidade do SMAPI")
    assert "SpaceCore" in text
    assert "Compatible" in text
    _assert_contains_any_casefold(text, "source context", "contexto da origem")
    _assert_contains_any_casefold(text, "provider relation", "relação do provedor")
    _assert_contains_any_casefold(text, "app context", "contexto do app")
    _assert_contains_any_casefold(text, "Open discovered page", "Abrir página descoberta", "Abrir página do mod", "Open source page")


def test_package_inspection_text_separates_blocking_and_non_blocking_guidance() -> None:
    inspection = PackageInspectionResult(
        package_path=Path("/tmp/mod.zip"),
        mods=(
            PackageModEntry(
                name="Mod A",
                unique_id="Sample.ModA",
                version="1.0.0",
                manifest_path="ModA/manifest.json",
            ),
        ),
        warnings=(
            PackageWarning(
                code="invalid_manifest",
                message="UniqueID missing",
                manifest_path="ModB/manifest.json",
            ),
        ),
        findings=(
            PackageFinding(
                kind="direct_single_mod_package",
                message="Single mod found at package root layout.",
                related_paths=("ModA/manifest.json",),
            ),
        ),
    )

    text = build_package_inspection_text(inspection)

    _assert_contains_any_casefold(
        text,
        "Manifest dependency preflight (blocking/local)",
        "prévia de dependências do manifesto (bloqueante/local)",
        "pré-checagem de dependências do manifesto (bloqueante/local)",
    )
    _assert_contains_any_casefold(
        text,
        "Remote requirement guidance (non-blocking/source-declared)",
        "orientação de requisitos remotos (não bloqueante/declarado na origem)",
        "orientação de requisitos remotos (não bloqueante/declarada na origem)",
    )
    _assert_contains_any_casefold(text, "Recommended next step", "Próximo passo recomendado")


def test_sandbox_plan_text_highlights_blocked_plan() -> None:
    plan = SandboxInstallPlan(
        package_path=Path("/tmp/mod.zip"),
        sandbox_mods_path=Path("/tmp/SandboxMods"),
        sandbox_archive_path=Path("/tmp/SandboxArchive"),
        entries=(
            SandboxInstallPlanEntry(
                name="Mod A",
                unique_id="Sample.ModA",
                version="1.0.0",
                source_package_path=Path("/tmp/mod.zip"),
                source_manifest_path="ModA/manifest.json",
                source_root_path="ModA",
                target_path=Path("/tmp/SandboxMods/ModA"),
                action="blocked",
                target_exists=False,
                archive_path=None,
                can_install=False,
                warnings=("Missing required dependencies: Sample.Required",),
            ),
        ),
        package_findings=tuple(),
        package_warnings=tuple(),
        plan_warnings=("Plan has blocked entries.",),
    )

    text = build_sandbox_install_plan_text(plan)

    _assert_contains_any_casefold(text, "Install Plan", "Plano de instalação")
    _assert_contains_any_casefold(text, "Sandbox Mods destination", "Destino Mods sandbox")
    _assert_contains_any_casefold(text, "Plan status: BLOCKED", "Status do plano: BLOQUEADO")
    _assert_contains_any_casefold(text, "Recommended next step", "Próximo passo recomendado")
    _assert_contains_any_casefold(text, "Resolve warnings", "Resolva os avisos")


def test_real_destination_plan_text_is_explicit() -> None:
    plan = SandboxInstallPlan(
        package_path=Path("/tmp/mod.zip"),
        sandbox_mods_path=Path("/tmp/RealMods"),
        sandbox_archive_path=Path("/tmp/RealMods/.sdvmm-archive"),
        entries=tuple(),
        package_findings=tuple(),
        package_warnings=tuple(),
        plan_warnings=tuple(),
        destination_kind="configured_real_mods",
    )

    text = build_sandbox_install_plan_text(plan)

    _assert_contains_any_casefold(text, "Game Mods destination (real)", "Destino Mods do jogo (real)")


def test_archive_restore_result_text_shows_destination_and_target_path() -> None:
    restored_mods = ModsInventory(
        mods=tuple(),
        parse_warnings=tuple(),
        duplicate_unique_ids=tuple(),
        missing_required_dependencies=tuple(),
        scan_entry_findings=tuple(),
        ignored_entries=tuple(),
    )
    result = ArchiveRestoreResult(
        plan=ArchiveRestorePlan(
            entry=ArchivedModEntry(
                source_kind="real_archive",
                archive_root=Path("/tmp/RealArchive"),
                archived_path=Path("/tmp/RealArchive/RestoreReal__sdvmm_archive_001"),
                archived_folder_name="RestoreReal__sdvmm_archive_001",
                target_folder_name="RestoreReal",
                mod_name="Restore Real",
                unique_id="Sample.RestoreReal",
                version="3.0.0",
            ),
            destination_kind="configured_real_mods",
            destination_mods_path=Path("/tmp/RealMods"),
            destination_target_path=Path("/tmp/RealMods/RestoreReal"),
        ),
        restored_target=Path("/tmp/RealMods/RestoreReal"),
        scan_context_path=Path("/tmp/RealMods"),
        inventory=restored_mods,
        destination_kind="configured_real_mods",
    )

    text = build_archive_restore_result_text(result)

    _assert_contains_any_casefold(text, "Archive restore completed", "Restauração do arquivo concluída")
    _assert_contains_any_casefold(text, "Game Mods destination (real)", "Destino Mods do jogo (real)")
    assert str(result.restored_target) in text


def test_mod_rollback_result_text_shows_destination_and_paths() -> None:
    inventory = ModsInventory(
        mods=tuple(),
        parse_warnings=tuple(),
        duplicate_unique_ids=tuple(),
        missing_required_dependencies=tuple(),
        scan_entry_findings=tuple(),
        ignored_entries=tuple(),
    )
    result = ModRollbackResult(
        plan=ModRollbackPlan(
            destination_kind="sandbox_mods",
            mods_path=Path("/tmp/SandboxMods"),
            archive_path=Path("/tmp/SandboxArchive"),
            current_mod_path=Path("/tmp/SandboxMods/SampleMod"),
            current_unique_id="Sample.Mod",
            current_version="2.0.0",
            rollback_entry=ArchivedModEntry(
                source_kind="sandbox_archive",
                archive_root=Path("/tmp/SandboxArchive"),
                archived_path=Path("/tmp/SandboxArchive/SampleMod__sdvmm_archive_001"),
                archived_folder_name="SampleMod__sdvmm_archive_001",
                target_folder_name="SampleMod",
                mod_name="Sample Mod",
                unique_id="Sample.Mod",
                version="1.0.0",
            ),
            current_archive_path=Path("/tmp/SandboxArchive/SampleMod__sdvmm_archive_002"),
        ),
        archived_current_target=Path("/tmp/SandboxArchive/SampleMod__sdvmm_archive_002"),
        restored_target=Path("/tmp/SandboxMods/SampleMod"),
        scan_context_path=Path("/tmp/SandboxMods"),
        inventory=inventory,
        destination_kind="sandbox_mods",
    )

    text = build_mod_rollback_result_text(result)

    _assert_contains_any_casefold(text, "Mod rollback completed.", "Mod rollback completed.")
    _assert_contains_any_casefold(text, "Sandbox Mods destination", "Destino Mods sandbox")
    assert str(result.archived_current_target) in text
    assert str(result.restored_target) in text
