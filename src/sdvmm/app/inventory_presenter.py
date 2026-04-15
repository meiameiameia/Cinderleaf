from __future__ import annotations

from sdvmm.app.i18n import get_active_ui_localizer
from sdvmm.app.shell_service import DiscoveryContextCorrelation, IntakeUpdateCorrelation
from sdvmm.domain.dependency_codes import (
    MISSING_REQUIRED_DEPENDENCY,
    OPTIONAL_DEPENDENCY_MISSING,
    SATISFIED,
    UNRESOLVED_DEPENDENCY_CONTEXT,
)
from sdvmm.domain.environment_codes import (
    GAME_PATH_DETECTED,
    INVALID_GAME_PATH,
    MODS_PATH_DETECTED,
    SMAPI_DETECTED,
    SMAPI_NOT_DETECTED,
)
from sdvmm.domain.models import (
    ArchivedModEntry,
    ArchiveCleanupResult,
    ArchiveDeleteResult,
    ArchiveRestoreResult,
    DependencyPreflightFinding,
    DownloadsIntakeResult,
    DownloadsWatchPollResult,
    GameEnvironmentStatus,
    ModDiscoveryEntry,
    ModDiscoveryResult,
    ModRemovalResult,
    ModRollbackPlan,
    ModRollbackResult,
    ModUpdateReport,
    ModsInventory,
    PackageInspectionResult,
    RemoteRequirementGuidance,
    SmapiLogReport,
    SmapiUpdateStatus,
    SandboxInstallPlan,
    SandboxInstallResult,
)
from sdvmm.domain.remote_requirement_codes import (
    NO_REMOTE_LINK_FOR_REQUIREMENTS,
    REQUIREMENTS_ABSENT,
    REQUIREMENTS_PRESENT,
    REQUIREMENTS_UNAVAILABLE,
)
from sdvmm.domain.smapi_codes import (
    SMAPI_DETECTED_VERSION_KNOWN,
    SMAPI_NOT_DETECTED_FOR_UPDATE,
    SMAPI_UNABLE_TO_DETERMINE,
    SMAPI_UP_TO_DATE,
    SMAPI_UPDATE_AVAILABLE,
)
from sdvmm.domain.smapi_log_codes import (
    SMAPI_LOG_ERROR,
    SMAPI_LOG_FAILED_MOD,
    SMAPI_LOG_MISSING_DEPENDENCY,
    SMAPI_LOG_NOT_FOUND,
    SMAPI_LOG_PARSED,
    SMAPI_LOG_RUNTIME_ISSUE,
    SMAPI_LOG_SOURCE_AUTO_DETECTED,
    SMAPI_LOG_SOURCE_MANUAL,
    SMAPI_LOG_SOURCE_NONE,
    SMAPI_LOG_UNABLE_TO_DETERMINE,
    SMAPI_LOG_WARNING,
)


def build_findings_text(inventory: ModsInventory) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Resumo da leitura da biblioteca" if pt_br else "Library Scan Summary")
    lines.append(
        f"- {'Linhas da biblioteca detectadas' if pt_br else 'Library rows detected'}: {len(inventory.mods)}"
    )
    lines.append(
        f"- {'Linhas inativas detectadas' if pt_br else 'Inactive rows detected'}: {len(inventory.disabled_mods)}"
    )
    lines.append(f"- {'Avisos de análise' if pt_br else 'Parse warnings'}: {len(inventory.parse_warnings)}")
    lines.append(
        f"- {'UniqueIDs duplicados' if pt_br else 'Duplicate UniqueIDs'}: {len(inventory.duplicate_unique_ids)}"
    )
    lines.append(
        f"- {'Dependências obrigatórias ausentes' if pt_br else 'Missing required dependencies'}: {len(inventory.missing_required_dependencies)}"
    )
    lines.append("")

    if inventory.scan_entry_findings:
        lines.append("Achados da leitura de pastas:" if pt_br else "Folder scan findings:")
        for finding in inventory.scan_entry_findings:
            kind = _scan_entry_kind_label(finding.kind)
            lines.append(
                f"- {kind}: {finding.entry_path.name}: {finding.message} (code: {finding.kind})"
            )
    else:
        lines.append("Achados da leitura de pastas: nenhum" if pt_br else "Folder scan findings: none")

    lines.append("")

    if inventory.parse_warnings:
        lines.append("Avisos do manifesto:" if pt_br else "Manifest warnings:")
        for warning in inventory.parse_warnings:
            lines.append(
                f"- {_warning_code_label(warning.code)}: {warning.mod_path.name}: "
                f"{warning.message} (code: {warning.code})"
            )
    else:
        lines.append("Avisos do manifesto: nenhum" if pt_br else "Manifest warnings: none")

    if inventory.duplicate_unique_ids:
        lines.append("")
        lines.append("Achados de UniqueID duplicado:" if pt_br else "Duplicate UniqueID findings:")
        for finding in inventory.duplicate_unique_ids:
            folders = ", ".join(path.name for path in finding.folder_paths)
            lines.append(f"- {finding.unique_id} ({folders})")
    else:
        lines.append("")
        lines.append(
            "Achados de UniqueID duplicado: nenhum"
            if pt_br
            else "Duplicate UniqueID findings: none"
        )

    if inventory.missing_required_dependencies:
        lines.append("")
        lines.append("Dependências obrigatórias ausentes:" if pt_br else "Missing required dependencies:")
        for finding in inventory.missing_required_dependencies:
            lines.append(
                "- "
                f"{finding.required_by_unique_id} "
                f"{'requer' if pt_br else 'requires'} {finding.missing_unique_id}"
                f" ({'pasta' if pt_br else 'folder'}: {finding.required_by_folder.name})"
            )
    else:
        lines.append("")
        lines.append(
            "Dependências obrigatórias ausentes: nenhuma"
            if pt_br
            else "Missing required dependencies: none"
        )

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if inventory.missing_required_dependencies:
        lines.append(
            "- Instale primeiro as dependências obrigatórias ausentes e depois faça a leitura de novo."
            if pt_br
            else "- Install missing required dependencies first, then scan again."
        )
    elif inventory.parse_warnings:
        lines.append(
            "- Revise os avisos do manifesto e substitua ou corrija as pastas de mod quebradas."
            if pt_br
            else "- Inspect manifest warnings and replace or fix broken mod folders."
        )
    elif inventory.disabled_mods:
        lines.append(
            "- Revise as linhas inativas na Biblioteca e ative os mods que você quer deixar ativos nesta visualização."
            if pt_br
            else "- Review inactive rows in Library and enable any mods you want active in this view."
        )
    else:
        lines.append(
            "- Execute a verificação de atualizações para ver se há versões mais novas disponíveis."
            if pt_br
            else "- Run update check to see if newer versions are available."
        )

    return "\n".join(lines)


def build_environment_status_text(status: GameEnvironmentStatus) -> str:
    lines: list[str] = []
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines.append("Detecção do ambiente" if pt_br else "Environment Detection")
    lines.append(f"- {'Caminho do jogo selecionado' if pt_br else 'Selected game path'}: {status.game_path}")

    for state in status.state_codes:
        lines.append(f"- {_environment_state_label(state)} (code: {state})")

    if status.mods_path is not None:
        lines.append(f"- {'Caminho Mods detectado' if pt_br else 'Detected Mods path'}: {status.mods_path}")
    else:
        lines.append(f"- {'Caminho Mods detectado' if pt_br else 'Detected Mods path'}: {'<não detectado>' if pt_br else '<not detected>'}")

    if status.smapi_path is not None:
        lines.append(f"- {'Caminho do SMAPI detectado' if pt_br else 'Detected SMAPI path'}: {status.smapi_path}")
    else:
        lines.append(f"- {'Caminho do SMAPI detectado' if pt_br else 'Detected SMAPI path'}: {'<não detectado>' if pt_br else '<not detected>'}")

    for note in status.notes:
        lines.append(f"- {'nota' if pt_br else 'note'}: {note}")

    lines.append("")
    if INVALID_GAME_PATH in status.state_codes:
        lines.append("Resumo do ambiente: caminho do jogo inválido" if pt_br else "Environment summary: invalid game path")
    elif GAME_PATH_DETECTED in status.state_codes:
        parts: list[str] = []
        if MODS_PATH_DETECTED in status.state_codes:
            parts.append("mods detectados" if pt_br else "Mods detected")
        else:
            parts.append("mods não detectados" if pt_br else "Mods not detected")
        if SMAPI_DETECTED in status.state_codes:
            parts.append("SMAPI detectado" if pt_br else "SMAPI detected")
        elif SMAPI_NOT_DETECTED in status.state_codes:
            parts.append("SMAPI não detectado" if pt_br else "SMAPI not detected")
        lines.append(
            f"Resumo do ambiente: {', '.join(parts)}"
            if pt_br
            else f"Environment summary: {', '.join(parts)}"
        )
    else:
        lines.append("Resumo do ambiente: estado de detecção incompleto" if pt_br else "Environment summary: incomplete detection state")

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if INVALID_GAME_PATH in status.state_codes:
        lines.append("- Escolha a pasta de instalação do Stardew Valley (não apenas uma pasta aleatória com Mods)." if pt_br else "- Pick the Stardew Valley install folder (not only a random folder with Mods).")
    elif MODS_PATH_DETECTED not in status.state_codes:
        lines.append("- Crie ou escolha uma pasta Mods válida antes de ler." if pt_br else "- Create or select a valid Mods folder before scanning.")
    elif SMAPI_DETECTED not in status.state_codes:
        lines.append("- SMAPI não detectado. Instale/verifique o SMAPI se seus mods precisarem dele." if pt_br else "- SMAPI not detected. Install/verify SMAPI if your mods require it.")
    else:
        lines.append("- O ambiente parece utilizável. Salve a configuração e execute Ler." if pt_br else "- Environment looks usable. Save config and run Scan.")

    return "\n".join(lines)


def build_smapi_update_status_text(status: SmapiUpdateStatus) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Visão geral da atualização do SMAPI" if pt_br else "SMAPI Update Awareness")
    lines.append(f"- {'Caminho do jogo' if pt_br else 'Game path'}: {status.game_path}")
    lines.append(f"- {'Entrada do SMAPI' if pt_br else 'SMAPI entrypoint'}: {status.smapi_path or ('<não detectado>' if pt_br else '<not detected>')}")
    lines.append(f"- {'Versão instalada do SMAPI' if pt_br else 'Installed SMAPI version'}: {status.installed_version or ('<desconhecida>' if pt_br else '<unknown>')}")
    lines.append(f"- {'Versão mais recente conhecida do SMAPI' if pt_br else 'Latest known SMAPI version'}: {status.latest_version or ('<desconhecida>' if pt_br else '<unknown>')}")
    lines.append(f"- {'Página de atualização' if pt_br else 'Update source page'}: {status.update_page_url}")
    lines.append(f"- Status: {_smapi_update_state_label(status.state)} (code: {status.state})")
    lines.append(f"- {'Mensagem' if pt_br else 'Message'}: {status.message}")

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if status.state == SMAPI_NOT_DETECTED_FOR_UPDATE:
        lines.append("- Instale o SMAPI primeiro se você pretende iniciar com mods do SMAPI." if pt_br else "- Install SMAPI first if you plan to launch with SMAPI mods.")
    elif status.state == SMAPI_UPDATE_AVAILABLE:
        lines.append("- Abra a página do SMAPI e atualize o SMAPI manualmente." if pt_br else "- Open the SMAPI page and update SMAPI manually.")
    elif status.state == SMAPI_UP_TO_DATE:
        lines.append("- O SMAPI está em dia. Continue os fluxos normais de mods." if pt_br else "- SMAPI is current. Continue normal mod workflows.")
    elif status.state == SMAPI_DETECTED_VERSION_KNOWN:
        lines.append("- A versão do SMAPI é conhecida; tente novamente depois para ver a versão remota mais recente." if pt_br else "- SMAPI version is known; retry check later for latest remote version.")
    elif status.state == SMAPI_UNABLE_TO_DETERMINE:
        lines.append("- Corrija a detecção do caminho do jogo/SMAPI e depois execute a checagem do SMAPI novamente." if pt_br else "- Fix game path/SMAPI detection, then run SMAPI check again.")
    else:
        lines.append("- Execute a checagem do SMAPI novamente se o ambiente tiver mudado." if pt_br else "- Re-run SMAPI check if environment changed.")

    return "\n".join(lines)


def build_smapi_log_report_text(report: SmapiLogReport) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Análise do log do SMAPI" if pt_br else "SMAPI Log Troubleshooting")
    lines.append(
        f"- Status: {_smapi_log_state_label(report.state)} (code: {report.state})"
    )
    lines.append(f"- Origem: {_smapi_log_source_label(report.source)}" if pt_br else f"- Source: {_smapi_log_source_label(report.source)}")
    lines.append(f"- Caminho do log: {report.log_path or '<não carregado>'}" if pt_br else f"- Log path: {report.log_path or '<not loaded>'}")
    lines.append(f"- Contexto do caminho do jogo: {report.game_path or '<nenhum>'}" if pt_br else f"- Game path context: {report.game_path or '<none>'}")
    if report.missing_dependency_entry_count > 0:
        lines.append(
            f"- Alvos de dependência ausentes: {report.missing_dependency_target_count}"
            if pt_br
            else f"- Missing dependency targets: {report.missing_dependency_target_count}"
        )
    lines.append(f"- Resumo: {_smapi_log_summary_text(report)}" if pt_br else f"- Summary: {_smapi_log_summary_text(report)}")
    if report.missing_dependencies:
        lines.append("")
        lines.append("Detalhes das dependências ausentes:" if pt_br else "Missing dependency details:")
        for entry in report.missing_dependencies:
            requiring_mod = entry.requiring_mod_name or entry.requiring_mod_unique_id or ("Mod desconhecido" if pt_br else "Unknown mod")
            dependency_target = entry.dependency_target or ("<dependência desconhecida>" if pt_br else "<unknown dependency>")
            detail = f"- {requiring_mod} -> {dependency_target}"
            if entry.required_version:
                detail += f" (requer {entry.required_version})" if pt_br else f" (required {entry.required_version})"
            lines.append(detail)

    lines.append("")
    if report.findings:
        counts = _smapi_log_issue_counts(report)
        lines.append(
            "- Parsed findings: "
            f"errors={counts[SMAPI_LOG_ERROR]}, "
            f"warnings={counts[SMAPI_LOG_WARNING]}, "
            f"failed mods={counts[SMAPI_LOG_FAILED_MOD]}, "
            f"missing dependencies={counts[SMAPI_LOG_MISSING_DEPENDENCY]}, "
            f"runtime issues={counts[SMAPI_LOG_RUNTIME_ISSUE]}"
        )
        lines.append("")
        lines.append("Finding details:")
        for finding in report.findings:
            lines.append(
                f"- linha {finding.line_number} | {_smapi_log_finding_kind_label(finding.kind)}: {finding.message}"
                if pt_br
                else f"- line {finding.line_number} | {_smapi_log_finding_kind_label(finding.kind)}: {finding.message}"
            )
    else:
        lines.append("- Achados analisados: nenhum" if pt_br else "- Parsed findings: none")

    if report.notes:
        lines.append("")
        lines.append("Notas:" if pt_br else "Notes:")
        for note in report.notes:
            lines.append(f"- {note}")

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if report.state == SMAPI_LOG_NOT_FOUND:
        lines.append(
            "- Inicie o jogo com o SMAPI uma vez e depois execute 'Verificar log do SMAPI' de novo ou carregue um log manualmente."
            if pt_br
            else "- Launch the game with SMAPI once, then run 'Check SMAPI log' again or load a log manually."
        )
    elif report.state == SMAPI_LOG_UNABLE_TO_DETERMINE:
        lines.append(
            "- Carregue manualmente um arquivo de log específico do SMAPI e verifique de novo."
            if pt_br
            else "- Load a specific SMAPI log file manually and re-check."
        )
    else:
        counts = _smapi_log_issue_counts(report)
        if report.missing_dependency_entry_count > 0:
            lines.append(
                "- Instale primeiro as dependências ausentes, depois inicie o SMAPI e verifique de novo."
                if pt_br
                else "- Install missing dependencies first, then launch SMAPI and re-check."
            )
            missing_targets = _smapi_missing_dependency_targets(report)
            if missing_targets:
                lines.append(
                    "- Alvos para pesquisar em Descobrir: " + ", ".join(missing_targets)
                    if pt_br
                    else "- Discover search targets: " + ", ".join(missing_targets)
                )
        elif counts[SMAPI_LOG_FAILED_MOD] > 0:
            lines.append(
                "- Revise as entradas de mods com falha e atualize/remova os mods com problema."
                if pt_br
                else "- Review failed-mod entries and update/remove the failing mods."
            )
        elif counts[SMAPI_LOG_ERROR] > 0 or counts[SMAPI_LOG_RUNTIME_ISSUE] > 0:
            lines.append(
                "- Revise as entradas de erro/runtime e confira a compatibilidade dos mods com as versões atuais do jogo e do SMAPI."
                if pt_br
                else "- Review error/runtime entries and verify mod compatibility with current SMAPI/game versions."
            )
        elif counts[SMAPI_LOG_WARNING] > 0:
            lines.append(
                "- Revise os avisos e observe se eles se repetem depois da próxima inicialização."
                if pt_br
                else "- Review warnings and monitor if they repeat after next launch."
            )
        else:
            lines.append(
                "- Nenhum problema óbvio foi encontrado. Verifique de novo depois de reproduzir um problema, se necessário."
                if pt_br
                else "- No obvious issues parsed. Re-check after reproducing a problem if needed."
            )

    return "\n".join(lines)


def _smapi_missing_dependency_targets(report: SmapiLogReport) -> tuple[str, ...]:
    return report.actionable_missing_dependency_targets


def build_dependency_preflight_text(
    *,
    title: str,
    findings: tuple[DependencyPreflightFinding, ...],
) -> str:
    lines: list[str] = [title]
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    if not findings:
        lines.append("- nenhum" if pt_br else "- none")
        return "\n".join(lines)

    grouped: dict[str, list[DependencyPreflightFinding]] = {
        SATISFIED: [],
        MISSING_REQUIRED_DEPENDENCY: [],
        OPTIONAL_DEPENDENCY_MISSING: [],
        UNRESOLVED_DEPENDENCY_CONTEXT: [],
    }
    for finding in findings:
        grouped.setdefault(finding.state, []).append(finding)

    for state in (
        SATISFIED,
        MISSING_REQUIRED_DEPENDENCY,
        OPTIONAL_DEPENDENCY_MISSING,
        UNRESOLVED_DEPENDENCY_CONTEXT,
    ):
        entries = grouped.get(state, [])
        if not entries:
            continue
        lines.append(f"- {_dependency_state_label(state)}: {len(entries)} (code: {state})")
        for entry in entries:
            requirement = (
                "obrigatória"
                if pt_br and entry.required
                else "opcional"
                if pt_br
                else "required"
                if entry.required
                else "optional"
            )
            lines.append(
                "  "
                f"{entry.required_by_name} ({entry.required_by_unique_id}) -> "
                f"{entry.dependency_unique_id} ({requirement})"
            )

    return "\n".join(lines)


def build_package_inspection_text(result: PackageInspectionResult) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Inspeção do pacote" if pt_br else "Package Inspection")
    lines.append(f"- {'Pacote' if pt_br else 'Package'}: {result.package_path.name}")
    lines.append(f"- {'Mods detectados' if pt_br else 'Detected mods'}: {len(result.mods)}")
    lines.append(f"- {'Achados' if pt_br else 'Findings'}: {len(result.findings)}")
    lines.append(f"- {'Avisos' if pt_br else 'Warnings'}: {len(result.warnings)}")

    lines.append("")
    if result.mods:
        lines.append(
            "Mods detectados neste zip:" if pt_br else "Detected mods in this zip:"
        )
        for mod in result.mods:
            lines.append(
                f"- {mod.name} | UniqueID: {mod.unique_id} | "
                f"{'Versão' if pt_br else 'Version'}: {mod.version} | {mod.manifest_path}"
            )
    else:
        lines.append(
            "Mods detectados neste zip: nenhum"
            if pt_br
            else "Detected mods in this zip: none"
        )

    lines.append("")
    if result.findings:
        lines.append("Achados do pacote:" if pt_br else "Package findings:")
        for finding in result.findings:
            lines.append(
                f"- {_package_finding_label(finding.kind)}: {finding.message} "
                f"(code: {finding.kind})"
            )
    else:
        lines.append("Achados do pacote: nenhum" if pt_br else "Package findings: none")

    lines.append("")
    if result.warnings:
        lines.append("Avisos do pacote:" if pt_br else "Package warnings:")
        for warning in result.warnings:
            lines.append(
                f"- {_warning_code_label(warning.code)}: {warning.manifest_path}: "
                f"{warning.message} (code: {warning.code})"
            )
    else:
        lines.append("Avisos do pacote: nenhum" if pt_br else "Package warnings: none")

    lines.append("")
    lines.append(
        build_dependency_preflight_text(
            title=(
                "Pré-checagem de dependências do manifesto (bloqueante/local):"
                if pt_br
                else "Manifest dependency preflight (blocking/local):"
            ),
            findings=result.dependency_findings,
        )
    )
    lines.append("")
    lines.append(
        build_remote_requirement_guidance_text(
            title=(
                "Orientação de requisitos remotos (não bloqueante/declarada na origem):"
                if pt_br
                else "Remote requirement guidance (non-blocking/source-declared):"
            ),
            guidance=result.remote_requirements,
        )
    )
    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if not result.mods:
        lines.append(
            "- O pacote ainda não está pronto para o planejamento da instalação. Escolha outro zip."
            if pt_br
            else "- Package is not ready for install planning. Choose another zip."
        )
    elif any(
        finding.state == MISSING_REQUIRED_DEPENDENCY for finding in result.dependency_findings
    ):
        lines.append(
            "- Dependências obrigatórias ausentes detectadas. Instale as dependências primeiro."
            if pt_br
            else "- Missing required dependencies detected. Install dependencies first."
        )
    else:
        lines.append(
            "- O pacote parece pronto para planejar. Monte um plano de instalação para o destino selecionado."
            if pt_br
            else "- Package looks plannable. Build an install plan for your selected destination."
        )

    return "\n".join(lines)


def build_sandbox_install_plan_text(plan: SandboxInstallPlan) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    blocked_count = sum(1 for entry in plan.entries if not entry.can_install)
    installable_count = sum(1 for entry in plan.entries if entry.can_install)
    source_packages = plan.package_paths if plan.package_paths else (plan.package_path,)
    source_package_names = ", ".join(path.name for path in source_packages)
    destination_label = _install_destination_label(plan.destination_kind)
    lines.append("Plano de instalação" if pt_br else "Install Plan")
    lines.append(f"- Tipo de destino: {destination_label}" if pt_br else f"- Destination type: {destination_label}")
    lines.append(f"- Caminho de destino dos Mods: {plan.sandbox_mods_path}" if pt_br else f"- Destination Mods path: {plan.sandbox_mods_path}")
    lines.append(f"- Caminho do arquivo de destino: {plan.sandbox_archive_path}" if pt_br else f"- Destination archive path: {plan.sandbox_archive_path}")
    lines.append(f"- Pacotes de origem: {source_package_names}" if pt_br else f"- Source packages: {source_package_names}")
    lines.append(
        (
            f"- Status do plano: {'BLOQUEADO' if blocked_count else 'PRONTO'} "
            f"(instaláveis={installable_count}, bloqueados={blocked_count})"
            if pt_br
            else f"- Plan status: {'BLOCKED' if blocked_count else 'READY'} "
            f"(installable={installable_count}, blocked={blocked_count})"
        )
    )
    lines.append("")

    if plan.entries:
        lines.append("Entradas do plano de instalação:" if pt_br else "Install plan entries:")
        for entry in plan.entries:
            status = (
                "novo destino"
                if not entry.target_exists and pt_br
                else "target already exists"
                if entry.target_exists
                else "new target"
            )
            if pt_br and entry.target_exists:
                status = "o destino já existe"
            action = _install_action_label(entry.action)
            executable = "pronto" if entry.can_install and pt_br else "blocked" if not entry.can_install and not pt_br else "bloqueado" if pt_br else "ready"
            lines.append(
                "- "
                f"{entry.name} | UniqueID: {entry.unique_id} | {'Versão' if pt_br else 'Version'}: {entry.version}"
                f" -> {entry.target_path.name} ({status}, action={action}, {executable})"
            )
            if entry.archive_path is not None:
                lines.append(f"  arquivo: {entry.archive_path}" if pt_br else f"  archive: {entry.archive_path}")
            for warning in entry.warnings:
                lines.append(f"  aviso: {warning}" if pt_br else f"  warning: {warning}")
    else:
        lines.append("Entradas do plano de instalação: nenhuma" if pt_br else "Install plan entries: none")

    lines.append("")
    if plan.plan_warnings:
        lines.append("Plan warnings:")
        for warning in plan.plan_warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("Plan warnings: none")

    lines.append("")
    if plan.package_findings:
        lines.append("Package findings:")
        for finding in plan.package_findings:
            lines.append(
                f"- {_package_finding_label(finding.kind)}: {finding.message} "
                f"(code: {finding.kind})"
            )
    else:
        lines.append("Package findings: none")

    lines.append("")
    lines.append(
        build_dependency_preflight_text(
            title="Manifest dependency preflight (blocking/local):",
            findings=plan.dependency_findings,
        )
    )
    lines.append("")
    lines.append(
        build_remote_requirement_guidance_text(
            title="Remote requirement guidance (non-blocking/source-declared):",
            guidance=plan.remote_requirements,
        )
    )
    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if blocked_count:
        lines.append(
            "- O plano está bloqueado. Resolva os avisos, especialmente as dependências obrigatórias ausentes, e monte o plano de novo."
            if pt_br
            else "- Plan is blocked. Resolve warnings (especially missing required dependencies) and rebuild plan."
        )
    else:
        lines.append(
            "- O plano está pronto. Revise as ações de destino/arquivo e depois execute a instalação explicitamente."
            if pt_br
            else "- Plan is ready. Inspect target/archive actions, then run install explicitly."
        )

    return "\n".join(lines)


def build_sandbox_install_result_text(result: SandboxInstallResult) -> str:
    lines: list[str] = []
    destination_label = _install_destination_label(result.destination_kind)
    source_packages = (
        result.plan.package_paths if result.plan.package_paths else (result.plan.package_path,)
    )
    lines.append("Install completed.")
    lines.append(f"- Destination type: {destination_label}")
    lines.append(f"- Scan context: {result.scan_context_path}")
    lines.append(f"- Source packages: {', '.join(path.name for path in source_packages)}")
    lines.append(f"Installed targets: {len(result.installed_targets)}")

    for target in result.installed_targets:
        lines.append(f"- {target}")

    lines.append("")
    lines.append(f"Archived targets: {len(result.archived_targets)}")
    for target in result.archived_targets:
        lines.append(f"- {target}")

    lines.append("")
    lines.append(build_findings_text(result.inventory))
    return "\n".join(lines)


def build_mod_removal_result_text(result: ModRemovalResult) -> str:
    lines: list[str] = []
    destination_label = _install_destination_label(result.destination_kind)
    lines.append("Mod removal completed.")
    lines.append(f"- Destination type: {destination_label}")
    lines.append(f"- Removed from active Mods path: {result.removed_target}")
    lines.append(f"- Archived to: {result.archived_target}")
    if result.included_mod_paths:
        lines.append(f"- Included installed folders: {len(result.included_mod_paths)}")
        for path in result.included_mod_paths:
            lines.append(f"  - {path}")
    lines.append(f"- Scan context: {result.scan_context_path}")
    lines.append("")
    lines.append("Recommended next step:")
    lines.append("- Review scan findings and dependencies after removal.")
    lines.append("")
    lines.append(build_findings_text(result.inventory))
    return "\n".join(lines)


def build_mod_rollback_plan_text(plan: ModRollbackPlan) -> str:
    lines: list[str] = []
    destination_label = _install_destination_label(plan.destination_kind)
    entry = plan.rollback_entry
    lines.append("Rollback Plan")
    lines.append(f"- Destination type: {destination_label}")
    lines.append(f"- Current installed folder: {plan.current_mod_path}")
    lines.append(f"- Current installed version: {plan.current_version}")
    lines.append(
        f"- Current installed UniqueID: {plan.current_unique_id}"
    )
    lines.append(
        "- Archived rollback candidate: "
        f"{entry.mod_name or '<unknown>'} | "
        f"UniqueID: {entry.unique_id or '<unknown>'} | "
        f"Version: {entry.version or '<unknown>'}"
    )
    lines.append(f"- Archived candidate folder: {entry.archived_path}")
    lines.append(f"- Current version will be archived to: {plan.current_archive_path}")
    lines.append("")
    lines.append("Recommended next step:")
    lines.append("- Confirm rollback explicitly to archive current version and restore selected archived version.")
    return "\n".join(lines)


def build_mod_rollback_result_text(result: ModRollbackResult) -> str:
    lines: list[str] = []
    destination_label = _install_destination_label(result.destination_kind)
    lines.append("Mod rollback completed.")
    lines.append(f"- Destination type: {destination_label}")
    lines.append(f"- Previous current version archived to: {result.archived_current_target}")
    lines.append(f"- Restored archived version to active Mods: {result.restored_target}")
    lines.append(f"- Scan context: {result.scan_context_path}")
    lines.append("")
    lines.append("Recommended next step:")
    lines.append("- Review scan findings and dependency warnings after rollback.")
    lines.append("")
    lines.append(build_findings_text(result.inventory))
    return "\n".join(lines)


def build_archive_listing_text(entries: tuple[ArchivedModEntry, ...]) -> str:
    localizer = get_active_ui_localizer()
    lines: list[str] = []
    real_count = sum(1 for entry in entries if entry.source_kind == "real_archive")
    sandbox_count = sum(1 for entry in entries if entry.source_kind == "sandbox_archive")
    retention_keep_limit = next(
        (entry.retention_keep_limit for entry in entries if entry.retention_keep_limit is not None),
        None,
    )
    cleanup_candidate_count = sum(
        1 for entry in entries if entry.retention_cleanup_candidate
    )
    overflow_groups = _archive_retention_overflow_groups(entries)
    lines.append("Navegador do arquivo" if localizer.effective_language == "pt-BR" else "Archive Browser")
    lines.append(
        f"- Entradas arquivadas: {len(entries)}"
        if localizer.effective_language == "pt-BR"
        else f"- Archived entries: {len(entries)}"
    )
    lines.append(
        f"- Entradas do arquivo real: {real_count}"
        if localizer.effective_language == "pt-BR"
        else f"- Real archive entries: {real_count}"
    )
    lines.append(
        f"- Entradas do arquivo sandbox: {sandbox_count}"
        if localizer.effective_language == "pt-BR"
        else f"- Sandbox archive entries: {sandbox_count}"
    )
    if retention_keep_limit is not None:
        lines.append(
            (
                f"- Regra de retenção: manter as {retention_keep_limit} cópias arquivadas mais recentes por mod"
                if localizer.effective_language == "pt-BR"
                else f"- Retention rule: keep latest {retention_keep_limit} archived copies per mod"
            )
        )
        lines.append(
            f"- Candidatos à limpeza: {cleanup_candidate_count}"
            if localizer.effective_language == "pt-BR"
            else f"- Cleanup candidates: {cleanup_candidate_count}"
        )
    lines.append("")

    if not entries:
        lines.append("Nenhuma entrada arquivada encontrada." if localizer.effective_language == "pt-BR" else "No archived entries found.")
    else:
        lines.append("Entradas arquivadas:" if localizer.effective_language == "pt-BR" else "Archived entries:")
        for entry in entries:
            lines.append(
                "- "
                + f"[{_archive_source_label(entry.source_kind)}] "
                + (
                    f"{entry.archived_folder_name} -> destino da restauração '{entry.target_folder_name}'"
                    if localizer.effective_language == "pt-BR"
                    else f"{entry.archived_folder_name} -> restore target '{entry.target_folder_name}'"
                )
            )
            if entry.mod_name or entry.unique_id or entry.version:
                lines.append(
                    "  "
                    f"{'mod' if localizer.effective_language == 'pt-BR' else 'mod'}: {entry.mod_name or ('<desconhecido>' if localizer.effective_language == 'pt-BR' else '<unknown>')} | "
                    f"UniqueID: {entry.unique_id or '<unknown>'} | "
                    f"{'Versão' if localizer.effective_language == 'pt-BR' else 'Version'}: {entry.version or ('<desconhecida>' if localizer.effective_language == 'pt-BR' else '<unknown>')}"
                )
            else:
                lines.append("  mod: <resumo do manifesto indisponível>" if localizer.effective_language == "pt-BR" else "  mod: <manifest summary unavailable>")
            lines.append(f"  caminho: {entry.archived_path}" if localizer.effective_language == "pt-BR" else f"  path: {entry.archived_path}")
            if entry.note:
                lines.append(f"  nota: {entry.note}" if localizer.effective_language == "pt-BR" else f"  note: {entry.note}")
            if entry.retention_keep_limit is not None:
                lines.append(f"  retenção: {_archive_retention_status_label(entry)}" if localizer.effective_language == "pt-BR" else f"  retention: {_archive_retention_status_label(entry)}")

    if overflow_groups:
        lines.append("")
        lines.append("Acúmulo de retenção:" if localizer.effective_language == "pt-BR" else "Retention buildup:")
        for group_text in overflow_groups:
            lines.append(f"- {group_text}")

    lines.append("")
    lines.append("Próximo passo recomendado:" if localizer.effective_language == "pt-BR" else "Recommended next step:")
    if overflow_groups and retention_keep_limit is not None:
        lines.append(
            (
                f"- Use Limpar arquivos antigos para manter as {retention_keep_limit} cópias mais recentes por mod."
                if localizer.effective_language == "pt-BR"
                else f"- Use Cleanup older archives to keep the latest {retention_keep_limit} copies per mod."
            )
        )
    elif entries:
        lines.append(
            "- Selecione uma entrada arquivada, escolha o contexto de destino e depois restaure explicitamente."
            if localizer.effective_language == "pt-BR"
            else "- Select an archived entry, choose destination context, then restore explicitly."
        )
    else:
        lines.append(
            "- Use fluxos de remoção/substituição por atualização para gerar entradas arquivadas primeiro."
            if localizer.effective_language == "pt-BR"
            else "- Use remove/update overwrite flows to generate archived entries first."
        )

    return "\n".join(lines)


def build_archive_restore_result_text(result: ArchiveRestoreResult) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    destination_label = _install_destination_label(result.destination_kind)
    lines.append("Restauração do arquivo concluída." if pt_br else "Archive restore completed.")
    lines.append(f"- {'Tipo de destino' if pt_br else 'Destination type'}: {destination_label}")
    lines.append(f"- {'Restaurado do arquivo' if pt_br else 'Restored from archive'}: {result.plan.entry.archived_path}")
    lines.append(f"- {'Restaurado para Mods ativos' if pt_br else 'Restored to active Mods'}: {result.restored_target}")
    lines.append(f"- {'Contexto de leitura' if pt_br else 'Scan context'}: {result.scan_context_path}")
    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    lines.append(
        "- Revise os achados da leitura e os avisos de dependência depois da restauração."
        if pt_br
        else "- Review scan findings and dependency warnings after restore."
    )
    lines.append("")
    lines.append(build_findings_text(result.inventory))
    return "\n".join(lines)


def build_archive_delete_result_text(result: ArchiveDeleteResult) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Exclusão permanente do arquivo concluída." if pt_br else "Archive permanent delete completed.")
    lines.append(f"- {'Origem do arquivo' if pt_br else 'Archive source'}: {_archive_source_label(result.plan.entry.source_kind)}")
    lines.append(f"- {'Pasta arquivada excluída' if pt_br else 'Deleted archived folder'}: {result.deleted_path}")
    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    lines.append(
        "- Atualize os arquivos e continue o planejamento de restauração/desfazer com as entradas restantes, se precisar."
        if pt_br
        else "- Refresh archives and continue restore/rollback planning with remaining entries if needed."
    )
    return "\n".join(lines)


def build_archive_cleanup_result_text(result: ArchiveCleanupResult) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Limpeza do arquivo concluída." if pt_br else "Archive cleanup completed.")
    lines.append(
        f"- {'Regra de retenção' if pt_br else 'Retention rule'}: "
        + (
            f"mantidas as {result.plan.retention_keep_limit} cópias arquivadas mais recentes por mod"
            if pt_br
            else f"kept latest {result.plan.retention_keep_limit} archived copies per mod"
        )
    )
    lines.append(f"- {'Pastas arquivadas antigas excluídas' if pt_br else 'Older archived folders deleted'}: {len(result.deleted_paths)}")
    lines.append(f"- {'Grupos de mod afetados' if pt_br else 'Affected mod groups'}: {len(result.plan.groups)}")
    if result.plan.groups:
        lines.append("")
        lines.append("Grupos limpos:" if pt_br else "Trimmed groups:")
        for group in result.plan.groups:
            lines.append(
                "- "
                f"[{_archive_source_label(group.source_kind)}] "
                f"{_archive_group_display_name(group.mod_name, group.target_folder_name)} | "
                f"UniqueID: {group.unique_id or '<unknown>'} | "
                f"{'Total' if pt_br else 'Total'}: {group.total_entries} | "
                f"{'Mantidas' if pt_br else 'Kept'}: {group.kept_entry_count} | "
                f"{'Cópias antigas excluídas' if pt_br else 'Deleted older copies'}: {group.cleanup_candidate_count}"
            )
    if result.deleted_paths:
        lines.append("")
        lines.append("Pastas arquivadas excluídas:" if pt_br else "Deleted archived folders:")
        lines.extend(f"- {path}" for path in result.deleted_paths)
    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    lines.append(
        "- Atualize as opções de desfazer ou o planejamento de restauração se você limpou o arquivo primeiro para reduzir a bagunça."
        if pt_br
        else "- Refresh rollback choices or restore planning if you were cleaning up archive clutter first."
    )
    return "\n".join(lines)


def build_update_report_text(report: ModUpdateReport) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Panorama de atualizações" if pt_br else "Update Awareness")
    lines.append(
        "A verificação prévia de dependências do manifesto (bloqueante) é separada da orientação de requisitos remotos (não bloqueante)."
        if pt_br
        else "Manifest dependency preflight (blocking) is separate from remote requirement guidance (non-blocking)."
    )

    if not report.statuses:
        lines.append("- Não há mods instalados no inventário atual." if pt_br else "- No installed mods in current inventory.")
        return "\n".join(lines)

    update_available_count = sum(1 for status in report.statuses if status.state == "update_available")
    up_to_date_count = sum(1 for status in report.statuses if status.state == "up_to_date")
    no_link_count = sum(1 for status in report.statuses if status.state == "no_remote_link")
    unavailable_count = sum(1 for status in report.statuses if status.state == "metadata_unavailable")
    lines.append(
        (
            f"- Resumo: atualização disponível={update_available_count}, atualizado={up_to_date_count}, "
            f"sem link remoto={no_link_count}, metadados indisponíveis={unavailable_count}"
            if pt_br
            else f"- Summary: update available={update_available_count}, up to date={up_to_date_count}, "
            f"no remote link={no_link_count}, metadata unavailable={unavailable_count}"
        )
    )
    lines.append("")

    for status in report.statuses:
        remote_version = status.remote_version or "unknown"
        lines.append(
            "- "
            f"{status.name} | UniqueID: {status.unique_id} | "
            f"{'instalado' if pt_br else 'installed'}={status.installed_version} | {'remoto' if pt_br else 'remote'}={remote_version} | "
            f"state={_update_state_label(status.state)} (code: {status.state})"
        )
        if status.remote_link is not None:
            lines.append(f"  remoto: {status.remote_link.page_url}" if pt_br else f"  remote: {status.remote_link.page_url}")
        if status.message:
            lines.append(f"  nota: {status.message}" if pt_br else f"  note: {status.message}")
        lines.append(
            f"  {'requisitos remotos' if pt_br else 'remote requirements'} [{_remote_requirements_state_label(status.remote_requirements_state)} "
            f"/ code: {status.remote_requirements_state}]: "
            f"{_format_remote_requirements_inline(status.remote_requirements, status.remote_requirements_message)}"
        )

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    if update_available_count:
        lines.append(
            "- Selecione uma linha com 'Atualização disponível' e clique em Abrir página remota. Depois use a entrada de pacotes e o planejamento da instalação."
            if pt_br
            else "- Select an 'Update available' mod row and click Open remote page, then use intake + install planning."
        )
    elif unavailable_count:
        lines.append(
            "- Os metadados estão indisponíveis para alguns mods. Confira a chave de API e a rede e tente Verificar atualizações novamente."
            if pt_br
            else "- Metadata unavailable for some mods. Check API key/network and try Check updates again."
        )
    else:
        lines.append("- Nenhuma ação imediata de atualização é necessária." if pt_br else "- No immediate update action is required.")

    return "\n".join(lines)


def build_discovery_search_text(
    result: ModDiscoveryResult,
    correlations: tuple[DiscoveryContextCorrelation, ...] = tuple(),
) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Descoberta de mods" if pt_br else "Mod Discovery")
    lines.append("- Fonte: índice de compatibilidade do SMAPI" if pt_br else "- Source: SMAPI compatibility index")
    lines.append(f"- Busca: {result.query}" if pt_br else f"- Query: {result.query}")
    lines.append(f"- Resultados: {len(result.results)}" if pt_br else f"- Results: {len(result.results)}")

    if result.notes:
        for note in result.notes:
            lines.append(f"- nota: {note}" if pt_br else f"- note: {note}")

    lines.append("")
    if not result.results:
        lines.append("Nenhum mod correspondente foi encontrado." if pt_br else "No matching mods found.")
        lines.append("")
        lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
        lines.append(
            "- Tente um termo de busca mais amplo, como nome do mod, UniqueID ou autor."
            if pt_br
            else "- Try a broader search term (mod name, UniqueID, or author)."
        )
        return "\n".join(lines)

    lines.append("Resultados da busca:" if pt_br else "Search results:")
    for entry in result.results:
        correlation = _match_discovery_correlation(correlations, entry.unique_id)
        lines.append(
            "- "
            f"{entry.name} | UniqueID: {entry.unique_id} | "
            f"source={_discovery_source_provider_label(entry.source_provider)} | "
            f"compatibility={_discovery_compatibility_label(entry.compatibility_state)} "
            f"(code: {entry.compatibility_state})"
        )
        lines.append(f"  autor: {entry.author}" if pt_br else f"  author: {entry.author}")
        lines.append(f"  contexto da origem: {_discovery_source_context_text(entry)}" if pt_br else f"  source context: {_discovery_source_context_text(entry)}")
        if entry.compatibility_summary:
            lines.append(f"  nota de compatibilidade: {entry.compatibility_summary}" if pt_br else f"  compatibility note: {entry.compatibility_summary}")
        if correlation is not None:
            lines.append(f"  contexto do app: {correlation.context_summary}" if pt_br else f"  app context: {correlation.context_summary}")
            if correlation.provider_relation_note:
                lines.append(f"  relação do provedor: {correlation.provider_relation_note}" if pt_br else f"  provider relation: {correlation.provider_relation_note}")
            lines.append(f"  dica do próximo passo: {correlation.next_step}" if pt_br else f"  next-step hint: {correlation.next_step}")
        if entry.source_page_url:
            lines.append(f"  página: {entry.source_page_url}" if pt_br else f"  page: {entry.source_page_url}")
        else:
            lines.append("  página: <indisponível>" if pt_br else "  page: <not available>")

    lines.append("")
    lines.append("Próximo passo recomendado:" if pt_br else "Recommended next step:")
    lines.append(
        "- Selecione uma linha de resultado da descoberta e clique em Abrir página do mod."
        if pt_br
        else "- Select a discovery result row and click Open discovered page."
    )
    lines.append(
        "- Siga o fluxo manual: abrir a página -> baixar o zip -> o monitor detecta -> revisar a entrada -> planejar/aplicar com segurança."
        if pt_br
        else "- Follow manual flow: open page -> download zip -> watcher detects -> review intake -> plan/apply safely."
    )
    return "\n".join(lines)


def build_downloads_intake_text(result: DownloadsWatchPollResult) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Entrada de downloads" if pt_br else "Downloads Intake")
    lines.append(f"- Caminho de downloads monitorado: {result.watched_path}" if pt_br else f"- Watched downloads path: {result.watched_path}")
    lines.append(f"- Arquivos zip conhecidos: {len(result.known_zip_paths)}" if pt_br else f"- Known zip files: {len(result.known_zip_paths)}")
    lines.append(
        "- A verificação prévia de dependências do manifesto continua bloqueante; requisitos remotos são apenas orientação."
        if pt_br
        else "- Manifest dependency preflight stays blocking; remote requirements are guidance only."
    )
    lines.append("")

    if not result.intakes:
        lines.append("Ainda não foram detectados novos pacotes zip." if pt_br else "No new zip packages detected.")
        lines.append(
            "Próximo passo recomendado: mantenha o monitor ligado e depois adicione novos arquivos zip."
            if pt_br
            else "Recommended next step: keep watcher running, then add new zip files."
        )
        return "\n".join(lines)

    lines.append(
        ("- Resumo da entrada: " if pt_br else "- Intake summary: ")
        + _intake_classification_summary(result.intakes)
    )
    lines.append("")
    lines.append("Resultados da entrada de novos pacotes:" if pt_br else "New package intake results:")
    for intake in result.intakes:
        lines.extend(_format_single_intake(intake))

    return "\n".join(lines)


def _format_single_intake(intake: DownloadsIntakeResult) -> list[str]:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    lines: list[str] = []
    lines.append(
        "- "
        f"{intake.package_path.name} | {'classificação' if pt_br else 'classification'}={_intake_classification_label(intake.classification)} "
        f"(code: {intake.classification})"
    )
    lines.append(f"  {'mensagem' if pt_br else 'message'}: {intake.message}")
    lines.append(f"  {'próximo passo recomendado' if pt_br else 'recommended next step'}: {_intake_next_action(intake.classification)}")

    if intake.mods:
        for mod in intake.mods:
            lines.append(f"  mod: {mod.name} | {mod.unique_id} | {mod.version}")
    else:
        lines.append("  mod: <nenhum>" if pt_br else "  mod: <none>")

    if intake.matched_installed_unique_ids:
        matches = ", ".join(intake.matched_installed_unique_ids)
        lines.append(f"  correspondência instalada: {matches}" if pt_br else f"  installed-match: {matches}")

    for warning in intake.warnings:
        lines.append(
            f"  {'aviso' if pt_br else 'warning'} [{_warning_code_label(warning.code)} / code: {warning.code}]: {warning.message}"
        )

    for finding in intake.findings:
        lines.append(
            f"  {'achado' if pt_br else 'finding'} [{_package_finding_label(finding.kind)} / code: {finding.kind}]: {finding.message}"
        )

    dependency_summary = _dependency_summary(intake.dependency_findings)
    if dependency_summary:
        lines.append(f"  resumo-dependências: {dependency_summary}" if pt_br else f"  dependency-summary: {dependency_summary}")
        for detail in _intake_dependency_details(intake.dependency_findings):
            lines.append(f"  dependência: {detail}" if pt_br else f"  dependency: {detail}")

    remote_summary = _remote_requirements_summary(intake.remote_requirements)
    if remote_summary:
        lines.append(f"  resumo-requisitos-remotos: {remote_summary}" if pt_br else f"  remote-requirements-summary: {remote_summary}")
        for detail in _remote_requirement_details(intake.remote_requirements):
            lines.append(f"  requisito-remoto: {detail}" if pt_br else f"  remote-requirement: {detail}")

    return lines


def _intake_next_action(classification: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    if classification == "unusable_package":
        return (
            "Não acionável. Inspecione/corrija este pacote ou escolha outro zip."
            if pt_br
            else "Not actionable. Inspect/fix this package or choose a different zip."
        )
    if classification == "multi_mod_package":
        return (
            "Acionável. Planeje a instalação e inspecione cada entrada antes de executar."
            if pt_br
            else "Actionable. Plan install and inspect every entry before executing."
        )
    if classification == "update_replace_candidate":
        return (
            "Acionável. Use Abrir como atualização para pré-selecionar a substituição com apoio de arquivo e depois inspecione o plano."
            if pt_br
            else "Actionable. Use Open as update to preselect archive-aware replace, then inspect the plan."
        )
    return (
        "Acionável. Planeje a instalação para o destino selecionado."
        if pt_br
        else "Actionable. Plan install for the selected destination."
    )


def _dependency_summary(findings: tuple[DependencyPreflightFinding, ...]) -> str:
    if not findings:
        return ""
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"

    required_missing = sum(
        1 for finding in findings if finding.state == MISSING_REQUIRED_DEPENDENCY
    )
    optional_missing = sum(
        1 for finding in findings if finding.state == OPTIONAL_DEPENDENCY_MISSING
    )
    unresolved = sum(
        1 for finding in findings if finding.state == UNRESOLVED_DEPENDENCY_CONTEXT
    )
    satisfied = sum(1 for finding in findings if finding.state == SATISFIED)

    return (
        f"satisfeitas={satisfied}, obrigatórias_ausentes={required_missing}, opcionais_ausentes={optional_missing}, não_resolvidas={unresolved}"
        if pt_br
        else f"satisfied={satisfied}, missing_required={required_missing}, optional_missing={optional_missing}, unresolved={unresolved}"
    )


def _intake_dependency_details(
    findings: tuple[DependencyPreflightFinding, ...],
) -> tuple[str, ...]:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    details: list[str] = []
    for finding in findings:
        if finding.state == MISSING_REQUIRED_DEPENDENCY:
            details.append(
                f"{finding.required_by_unique_id} "
                + (
                    f"está sem a dependência obrigatória {finding.dependency_unique_id}; instale a dependência primeiro"
                    if pt_br
                    else f"missing required {finding.dependency_unique_id}; install dependency first"
                )
            )
        elif finding.state == OPTIONAL_DEPENDENCY_MISSING:
            details.append(
                f"{finding.required_by_unique_id} "
                + (
                    f"está sem a dependência opcional {finding.dependency_unique_id}"
                    if pt_br
                    else f"missing optional {finding.dependency_unique_id}"
                )
            )
        elif finding.state == UNRESOLVED_DEPENDENCY_CONTEXT:
            details.append(
                f"{finding.required_by_unique_id} "
                + (
                    f"tem contexto de dependência não resolvido para {finding.dependency_unique_id}"
                    if pt_br
                    else f"unresolved dependency context for {finding.dependency_unique_id}"
                )
            )

    return tuple(details)


def build_remote_requirement_guidance_text(
    *,
    title: str,
    guidance: tuple[RemoteRequirementGuidance, ...],
) -> str:
    lines: list[str] = [title]
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    if not guidance:
        lines.append("- nenhum" if pt_br else "- none")
        return "\n".join(lines)

    for item in guidance:
        provider = item.provider or ("nenhum" if pt_br else "none")
        lines.append(
            "- "
            f"{item.name} ({item.unique_id}) | {'provedor' if pt_br else 'provider'}={provider} | "
            f"{'estado' if pt_br else 'state'}={_remote_requirements_state_label(item.state)} (code: {item.state})"
        )
        if item.requirements:
            joined = "; ".join(item.requirements)
            lines.append(f"  {'requisitos' if pt_br else 'requirements'}: {joined}")
        if item.message:
            lines.append(f"  {'nota' if pt_br else 'note'}: {item.message}")
        if item.remote_link is not None:
            lines.append(f"  {'remoto' if pt_br else 'remote'}: {item.remote_link.page_url}")

    return "\n".join(lines)


def _format_remote_requirements_inline(
    requirements: tuple[str, ...],
    message: str | None,
) -> str:
    if requirements:
        return "; ".join(requirements)
    if message:
        return message
    return "indisponível" if get_active_ui_localizer().effective_language == "pt-BR" else "unavailable"


def _remote_requirements_summary(guidance: tuple[RemoteRequirementGuidance, ...]) -> str:
    if not guidance:
        return ""
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"

    present = sum(1 for item in guidance if item.state == REQUIREMENTS_PRESENT)
    absent = sum(1 for item in guidance if item.state == REQUIREMENTS_ABSENT)
    unavailable = sum(1 for item in guidance if item.state == REQUIREMENTS_UNAVAILABLE)
    no_link = sum(1 for item in guidance if item.state == NO_REMOTE_LINK_FOR_REQUIREMENTS)
    return (
        f"presentes={present}, ausentes={absent}, indisponíveis={unavailable}, sem_link={no_link}"
        if pt_br
        else f"present={present}, absent={absent}, unavailable={unavailable}, no_link={no_link}"
    )


def _remote_requirement_details(
    guidance: tuple[RemoteRequirementGuidance, ...],
) -> tuple[str, ...]:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    details: list[str] = []
    for item in guidance:
        if item.state == REQUIREMENTS_PRESENT:
            details.append(
                f"{item.unique_id} "
                + (
                    f"requisitos remotos: {', '.join(item.requirements)}"
                    if pt_br
                    else f"remote requirements: {', '.join(item.requirements)}"
                )
            )
        elif item.state == REQUIREMENTS_ABSENT:
            details.append(
                f"{item.unique_id} "
                + (
                    "requisitos remotos: nenhum declarado pela origem"
                    if pt_br
                    else "remote requirements: none declared by source"
                )
            )
        elif item.state == NO_REMOTE_LINK_FOR_REQUIREMENTS:
            details.append(
                f"{item.unique_id} "
                + (
                    "requisitos remotos: sem link remoto"
                    if pt_br
                    else "remote requirements: no remote link"
                )
            )
        elif item.state == REQUIREMENTS_UNAVAILABLE:
            details.append(
                f"{item.unique_id} "
                + (
                    f"requisitos remotos indisponíveis: {item.message or 'erro do provedor'}"
                    if pt_br
                    else f"remote requirements unavailable: {item.message or 'provider error'}"
                )
            )

    return tuple(details)


def build_intake_correlation_text(correlations: tuple[IntakeUpdateCorrelation, ...]) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    lines: list[str] = []
    lines.append("Correlação entre entrada e atualização" if pt_br else "Intake and Update Correlation")

    if not correlations:
        lines.append("- nenhuma" if pt_br else "- none")
        return "\n".join(lines)

    for correlation in correlations:
        lines.append(f"- {correlation.intake.package_path.name}: {correlation.summary}")
        lines.append(f"  {'próximo passo' if pt_br else 'next-step'}: {correlation.next_step}")

    return "\n".join(lines)


def _environment_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        GAME_PATH_DETECTED: "Caminho do jogo detectado" if pt_br else "Game installation path detected",
        MODS_PATH_DETECTED: "Pasta Mods detectada" if pt_br else "Mods folder detected",
        SMAPI_DETECTED: "SMAPI detectado" if pt_br else "SMAPI detected",
        SMAPI_NOT_DETECTED: "SMAPI não detectado" if pt_br else "SMAPI not detected",
        INVALID_GAME_PATH: "Caminho do jogo inválido" if pt_br else "Invalid game path",
    }
    return labels.get(state, state.replace("_", " ").title())


def _smapi_update_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        SMAPI_NOT_DETECTED_FOR_UPDATE: "SMAPI não detectado" if pt_br else "SMAPI not detected",
        SMAPI_DETECTED_VERSION_KNOWN: "SMAPI detectado (versão conhecida)" if pt_br else "SMAPI detected (version known)",
        SMAPI_UPDATE_AVAILABLE: "Atualização do SMAPI disponível" if pt_br else "SMAPI update available",
        SMAPI_UP_TO_DATE: "SMAPI atualizado" if pt_br else "SMAPI up to date",
        SMAPI_UNABLE_TO_DETERMINE: "Não foi possível determinar o status do SMAPI" if pt_br else "Unable to determine SMAPI status",
    }
    return labels.get(state, state.replace("_", " ").title())


def _smapi_log_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        SMAPI_LOG_NOT_FOUND: "Log não encontrado" if pt_br else "Log not found",
        SMAPI_LOG_PARSED: "Log analisado" if pt_br else "Log parsed",
        SMAPI_LOG_UNABLE_TO_DETERMINE: "Não foi possível determinar" if pt_br else "Unable to determine",
    }
    return labels.get(state, state.replace("_", " ").title())


def _smapi_log_source_label(source: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        SMAPI_LOG_SOURCE_AUTO_DETECTED: "Caminho do log detectado automaticamente" if pt_br else "Auto-detected log path",
        SMAPI_LOG_SOURCE_MANUAL: "Caminho do log escolhido manualmente" if pt_br else "Manually selected log path",
        SMAPI_LOG_SOURCE_NONE: "Nenhuma origem de log" if pt_br else "No log source",
    }
    return labels.get(source, source.replace("_", " ").title())


def _smapi_log_finding_kind_label(kind: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        SMAPI_LOG_ERROR: "Erro" if pt_br else "Error",
        SMAPI_LOG_WARNING: "Aviso" if pt_br else "Warning",
        SMAPI_LOG_FAILED_MOD: "Mod com falha" if pt_br else "Failed mod",
        SMAPI_LOG_MISSING_DEPENDENCY: "Dependência ausente" if pt_br else "Missing dependency",
        SMAPI_LOG_RUNTIME_ISSUE: "Problema de runtime" if pt_br else "Runtime issue",
    }
    return labels.get(kind, kind.replace("_", " ").title())


def _smapi_log_issue_counts(report: SmapiLogReport) -> dict[str, int]:
    counts = {
        SMAPI_LOG_ERROR: 0,
        SMAPI_LOG_WARNING: 0,
        SMAPI_LOG_FAILED_MOD: 0,
        SMAPI_LOG_MISSING_DEPENDENCY: report.missing_dependency_entry_count,
        SMAPI_LOG_RUNTIME_ISSUE: 0,
    }
    for finding in report.findings:
        if finding.kind == SMAPI_LOG_MISSING_DEPENDENCY:
            continue
        counts[finding.kind] = counts.get(finding.kind, 0) + 1
    return counts


def _smapi_log_summary_text(report: SmapiLogReport) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    counts = _smapi_log_issue_counts(report)
    if pt_br:
        return (
            "Log do SMAPI analisado: "
            f"erros={counts[SMAPI_LOG_ERROR]}, "
            f"avisos={counts[SMAPI_LOG_WARNING]}, "
            f"mods_com_falha={counts[SMAPI_LOG_FAILED_MOD]}, "
            f"dependências_ausentes={counts[SMAPI_LOG_MISSING_DEPENDENCY]}, "
            f"problemas_de_runtime={counts[SMAPI_LOG_RUNTIME_ISSUE]}."
        )
    return (
        "Parsed SMAPI log: "
        f"errors={counts[SMAPI_LOG_ERROR]}, "
        f"warnings={counts[SMAPI_LOG_WARNING]}, "
        f"failed_mods={counts[SMAPI_LOG_FAILED_MOD]}, "
        f"missing_dependencies={counts[SMAPI_LOG_MISSING_DEPENDENCY]}, "
        f"runtime_issues={counts[SMAPI_LOG_RUNTIME_ISSUE]}."
    )


def _scan_entry_kind_label(kind: str) -> str:
    labels = {
        "direct_mod": "Direct mod folder",
        "nested_mod_container": "Nested container with mod",
        "multi_mod_container": "Container with multiple mods",
        "missing_manifest": "No usable manifest found",
        "invalid_manifest": "Invalid manifest",
    }
    return labels.get(kind, kind.replace("_", " ").title())


def _warning_code_label(code: str) -> str:
    labels = {
        "missing_manifest": "Missing manifest",
        "malformed_manifest": "Malformed manifest JSON",
        "invalid_manifest": "Invalid manifest data",
        "manifest_read_error": "Manifest read error",
        "invalid_dependency_entry": "Invalid dependency entry",
    }
    return labels.get(code, code.replace("_", " ").title())


def _package_finding_label(kind: str) -> str:
    labels = {
        "direct_single_mod_package": "Direct single-mod package",
        "nested_single_mod_package": "Nested single-mod package",
        "multi_mod_package": "Multi-mod package",
        "invalid_manifest_package": "Invalid manifest package",
        "no_usable_manifest_found": "No usable manifest found",
        "too_deep_unsupported_package": "Unsupported deep package layout",
    }
    return labels.get(kind, kind.replace("_", " ").title())


def _update_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    labels = {
        "up_to_date": "Atualizado" if localizer.effective_language == "pt-BR" else "Up to date",
        "update_available": "Atualização disponível" if localizer.effective_language == "pt-BR" else "Update available",
        "no_remote_link": "Sem link remoto" if localizer.effective_language == "pt-BR" else "No remote link",
        "metadata_unavailable": "Metadados indisponíveis" if localizer.effective_language == "pt-BR" else "Metadata unavailable",
    }
    return labels.get(state, state.replace("_", " ").title())


def _dependency_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        SATISFIED: "Satisfeita" if pt_br else "Satisfied",
        MISSING_REQUIRED_DEPENDENCY: "Dependência obrigatória ausente" if pt_br else "Missing required dependency",
        OPTIONAL_DEPENDENCY_MISSING: "Dependência opcional ausente" if pt_br else "Optional dependency missing",
        UNRESOLVED_DEPENDENCY_CONTEXT: "Contexto da dependência não resolvido" if pt_br else "Dependency context unresolved",
    }
    return labels.get(state, state.replace("_", " ").title())


def _remote_requirements_state_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        REQUIREMENTS_PRESENT: "Requisitos presentes" if pt_br else "Requirements present",
        REQUIREMENTS_ABSENT: "Nenhum requisito declarado" if pt_br else "No requirements declared",
        REQUIREMENTS_UNAVAILABLE: "Requisitos indisponíveis" if pt_br else "Requirements unavailable",
        NO_REMOTE_LINK_FOR_REQUIREMENTS: "Sem link remoto" if pt_br else "No remote link",
    }
    return labels.get(state, state.replace("_", " ").title())


def _discovery_compatibility_label(state: str) -> str:
    localizer = get_active_ui_localizer()
    labels = {
        "compatible": "Compatível" if localizer.effective_language == "pt-BR" else "Compatible",
        "compatible_with_caveat": "Compatível com ressalva" if localizer.effective_language == "pt-BR" else "Compatible with caveat",
        "unofficial_update": "Usar atualização não oficial" if localizer.effective_language == "pt-BR" else "Use unofficial update",
        "workaround_available": "Usar contorno" if localizer.effective_language == "pt-BR" else "Use workaround",
        "incompatible": "Incompatível" if localizer.effective_language == "pt-BR" else "Incompatible",
        "abandoned": "Abandonado" if localizer.effective_language == "pt-BR" else "Abandoned",
        "obsolete": "Obsoleto" if localizer.effective_language == "pt-BR" else "Obsolete",
        "compatibility_unknown": "Compatibilidade desconhecida" if localizer.effective_language == "pt-BR" else "Compatibility unknown",
    }
    return labels.get(state, state.replace("_", " ").title())


def _discovery_source_provider_label(provider: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        "nexus": "Nexus",
        "github": "GitHub",
        "custom_url": "URL personalizada" if pt_br else "Custom URL",
        "none": "Sem link de origem" if pt_br else "No source link",
    }
    return labels.get(provider, provider.replace("_", " ").title())


def _discovery_source_context_text(entry: ModDiscoveryEntry) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    if entry.source_provider == "nexus":
        return "Listagem do Nexus vinda do índice de compatibilidade" if pt_br else "Nexus listing from compatibility index"
    if entry.source_provider == "github":
        return "Repositório do GitHub vindo do índice de compatibilidade" if pt_br else "GitHub repository from compatibility index"
    if entry.source_provider == "custom_url":
        return "URL de origem personalizada vinda do índice de compatibilidade" if pt_br else "Custom source URL from compatibility index"
    return "Nenhum link de origem listado no índice de compatibilidade" if pt_br else "No source link listed in compatibility index"


def _match_discovery_correlation(
    correlations: tuple[DiscoveryContextCorrelation, ...],
    unique_id: str,
) -> DiscoveryContextCorrelation | None:
    lookup = unique_id.casefold()
    for item in correlations:
        if item.entry.unique_id.casefold() == lookup:
            return item
    return None


def _install_action_label(action: str) -> str:
    pt_br = get_active_ui_localizer().effective_language == "pt-BR"
    labels = {
        "install_new": "instalar novo" if pt_br else "install new",
        "overwrite_with_archive": "substituir (arquivar antes)" if pt_br else "overwrite (archive first)",
        "blocked": "bloqueado" if pt_br else "blocked",
    }
    return labels.get(action, action.replace("_", " "))


def _install_destination_label(destination_kind: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        "configured_real_mods": "Destino Mods do jogo (real)" if pt_br else "Game Mods destination (real)",
        "sandbox_mods": "Destino Mods sandbox" if pt_br else "Sandbox Mods destination",
    }
    return labels.get(destination_kind, destination_kind.replace("_", " ").title())


def _archive_source_label(source_kind: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        "real_archive": "Arquivo real" if pt_br else "Real archive",
        "sandbox_archive": "Arquivo sandbox" if pt_br else "Sandbox archive",
    }
    return labels.get(source_kind, source_kind.replace("_", " ").title())


def _archive_retention_status_label(entry: ArchivedModEntry) -> str:
    localizer = get_active_ui_localizer()
    if entry.retention_keep_limit is None:
        return "Manter" if localizer.effective_language == "pt-BR" else "Keep"
    position_text = f"{entry.retention_position}/{entry.retention_total}"
    if entry.retention_cleanup_candidate:
        return (
            f"Candidato à limpeza ({position_text})"
            if localizer.effective_language == "pt-BR"
            else f"Cleanup candidate ({position_text})"
        )
    if entry.retention_total > entry.retention_keep_limit:
        return (
            f"Manter mais recentes ({position_text})"
            if localizer.effective_language == "pt-BR"
            else f"Keep latest ({position_text})"
        )
    return "Manter" if localizer.effective_language == "pt-BR" else "Keep"


def _archive_retention_overflow_groups(entries: tuple[ArchivedModEntry, ...]) -> tuple[str, ...]:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    grouped_entries: dict[tuple[str, str, str], list[ArchivedModEntry]] = {}
    for entry in entries:
        if not entry.retention_cleanup_candidate:
            continue
        grouped_entries.setdefault(_archive_retention_group_key(entry), []).append(entry)

    summaries: list[str] = []
    for group_entries in grouped_entries.values():
        first_entry = sorted(
            group_entries,
            key=lambda item: item.archived_folder_name.casefold(),
        )[0]
        keep_limit = first_entry.retention_keep_limit or 0
        mod_name = _archive_group_display_name(
            first_entry.mod_name,
            first_entry.target_folder_name,
        )
        summaries.append(
            f"[{_archive_source_label(first_entry.source_kind)}] "
            f"{mod_name} | UniqueID: {first_entry.unique_id or '<unknown>'} | "
            + (
                f"{first_entry.retention_total} cópias arquivadas, "
                f"{len(group_entries)} candidato(s) antigo(s) à limpeza, "
                f"manter as {keep_limit} mais recentes"
                if pt_br
                else f"{first_entry.retention_total} archived copies, "
                f"{len(group_entries)} older cleanup candidate(s), "
                f"keep latest {keep_limit}"
            )
        )

    return tuple(sorted(summaries, key=str.casefold))


def _archive_retention_group_key(entry: ArchivedModEntry) -> tuple[str, str, str]:
    unique_id_key = entry.unique_id.casefold() if entry.unique_id else ""
    return (
        entry.source_kind,
        unique_id_key or f"folder:{entry.target_folder_name.casefold()}",
        entry.target_folder_name.casefold(),
    )


def _archive_group_display_name(mod_name: str | None, target_folder_name: str) -> str:
    if mod_name and mod_name.strip():
        return mod_name
    return target_folder_name


def _intake_classification_label(classification: str) -> str:
    localizer = get_active_ui_localizer()
    pt_br = localizer.effective_language == "pt-BR"
    labels = {
        "new_install_candidate": "Candidata a nova instalação" if pt_br else "New install candidate",
        "update_replace_candidate": "Candidata a atualizar/substituir" if pt_br else "Update/replace candidate",
        "multi_mod_package": "Pacote com vários mods" if pt_br else "Multi-mod package",
        "unusable_package": "Pacote inutilizável" if pt_br else "Unusable package",
    }
    return labels.get(classification, classification.replace("_", " ").title())


def _intake_classification_summary(intakes: tuple[DownloadsIntakeResult, ...]) -> str:
    counts: dict[str, int] = {}
    for intake in intakes:
        counts[intake.classification] = counts.get(intake.classification, 0) + 1

    order = (
        "new_install_candidate",
        "update_replace_candidate",
        "multi_mod_package",
        "unusable_package",
    )
    parts = [
        f"{_intake_classification_label(key)}: {counts[key]}"
        for key in order
        if counts.get(key, 0) > 0
    ]
    return ", ".join(parts) if parts else "none"
