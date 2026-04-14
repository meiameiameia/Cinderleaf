from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QLocale

DEFAULT_LANGUAGE_PREFERENCE = "system"
LANGUAGE_ENGLISH = "en"
LANGUAGE_PORTUGUESE_BRAZIL = "pt-BR"
SUPPORTED_LANGUAGE_PREFERENCES = (
    DEFAULT_LANGUAGE_PREFERENCE,
    LANGUAGE_ENGLISH,
    LANGUAGE_PORTUGUESE_BRAZIL,
)

_TRANSLATIONS: dict[str, dict[str, str]] = {
    LANGUAGE_ENGLISH: {
        "shell.version": "Version {version}",
        "shell.release_check_available": "Release check available in Setup",
        "shell.workspaces": "Workspaces",
        "workspace.library": "Library",
        "workspace.setup": "Setup",
        "workspace.packages": "Packages",
        "workspace.install": "Install",
        "workspace.discover": "Discover",
        "workspace.compare": "Compare",
        "workspace.history": "History",
        "setup.page.eyebrow": "Folders and tools",
        "setup.page.title": "Setup",
        "setup.page.subtitle": "Set your folders. Tools stay on the right.",
        "setup.main_intro": "Set folders once, then use Packages, Compare, and Mods.",
        "setup.quickstart": "Quick start",
        "setup.quickstart.readiness": "Quick start: set Game folder, Real Mods folder, and Sandbox Mods folder.",
        "setup.quickstart.intro": "Game folder, Real Mods folder, Sandbox Mods folder.",
        "setup.folders": "Folders",
        "setup.folders.intro": "Save setup remembers these paths. Detect game folders only reads the installed environment.",
        "setup.extras": "Extras",
        "setup.extras.intro": "Archive folders, Nexus, and Steam options are optional.",
        "setup.backup": "Backup",
        "setup.backup.intro": "Export creates a bundle. Inspect is read-only. Execute restore writes only into the configured folders.",
        "setup.managed": "Managed folders",
        "setup.details": "Details",
        "setup.support": "Support",
        "setup.support.intro": "Backup tools first, managed folders below.",
        "setup.language": "App language",
        "setup.language.option.system": "System default",
        "setup.language.option.en": "English",
        "setup.language.option.pt-BR": "Portuguese (Brazil)",
        "setup.game_folder": "Game folder (live install)",
        "setup.real_mods_folder": "Real Mods folder",
        "setup.sandbox_mods_folder": "Sandbox Mods folder",
        "setup.sandbox_archive_folder": "Sandbox archive folder",
        "setup.real_archive_folder": "Real Mods archive folder",
        "setup.nexus_api_key": "Nexus API key",
        "setup.release": "Cinderleaf release",
        "setup.managed_sandbox_mods": "Managed Sandbox Mods",
        "setup.managed_sandbox_archive": "Managed Sandbox Archive",
        "setup.managed_real_archive": "Managed Real Mods Archive",
        "setup.managed_real_logs": "Managed Logs / Real",
        "setup.managed_sandbox_logs": "Managed Logs / Sandbox",
        "setup.managed.placeholder": "<set the game folder first>",
        "setup.managed.placeholder.invalid": "<game folder is not ready>",
        "setup.save": "Save setup",
        "setup.detect": "Detect game folders",
        "setup.choose_game": "Choose game folder",
        "setup.choose_real_mods": "Choose real Mods",
        "setup.open_real_mods": "Open real Mods",
        "setup.choose_sandbox_mods": "Choose sandbox Mods",
        "setup.open_sandbox_mods": "Open sandbox Mods",
        "setup.choose_sandbox_archive": "Choose sandbox archive",
        "setup.open_sandbox_archive": "Open sandbox archive",
        "setup.choose_real_archive": "Choose real archive",
        "setup.open_real_archive": "Open real archive",
        "setup.open_folder": "Open folder",
        "setup.migrate_managed": "Migrate configured folders",
        "setup.migrate_managed_tooltip": "Move the configured Sandbox Mods and archive folders into the Cinderleaf-managed paths under the game folder.",
        "setup.check_nexus": "Check Nexus connection",
        "setup.check_updates": "Check for app updates",
        "setup.open_release_page": "Open release page",
        "setup.export_backup": "Export backup",
        "setup.inspect_backup": "Inspect backup",
        "setup.execute_restore": "Execute restore",
        "setup.steam_auto_start": "Try to start Steam before game launch when Steam is not already running",
        "setup.steam_auto_start_tooltip": "Best-effort Steam launch assistance for Vanilla, SMAPI, and Sandbox dev launch.",
        "setup.app_update_status": "Check for app updates to compare this install with the latest Cinderleaf release.",
        "setup.managed_summary": "Derived from the game folder. Migrate only when you want Cinderleaf-managed paths.",
        "setup.managed_summary.no_game": "Set the game folder to see the Cinderleaf-managed paths. Existing paths keep working until you choose migration.",
        "setup.managed_summary.invalid_game": "The game folder must point to an accessible Stardew Valley install before managed folders can be derived.",
        "setup.language.saved_restart": "Language saved. Restart Cinderleaf to apply the new app language everywhere.",
        "setup.language.saved_restart_short": "Saved setup. Restart Cinderleaf to apply the new app language.",
        "setup.language.applied": "App language updated for the visible shell. Save setup to keep it next time.",
        "setup.saved_status": "Saved config to {path}",
        "setup.loaded_status": "Loaded saved config from {path}",
        "setup.core.game_short": "Game folder",
        "setup.core.real_mods_short": "Real Mods folder",
        "setup.core.sandbox_mods_short": "Sandbox Mods folder",
        "setup.readiness.ready": "Ready to go. Save setup if you want to keep these paths, then inspect a package in Packages.",
        "setup.readiness.empty": "Quick start: set Game folder, Real Mods folder, and Sandbox Mods folder.",
        "setup.readiness.partial": "{count}/3 core paths set. Add {missing} to get started in Packages, Compare, and Mods.",
        "setup.first_run.ready": "Ready to go. You can inspect a package now, and save setup when you want to keep these paths.",
        "setup.first_run.empty": "Quick start is empty. Set Game folder, Real Mods folder, and Sandbox Mods folder to get started.",
        "setup.first_run.partial_prefix": "Setup is almost ready.",
        "setup.first_run.partial": "Setup is almost ready. Add {missing} to get started, then save setup when you want to keep these paths.",
        "setup.summary.saved": "Config saved.",
        "setup.summary.state_file": "State file: {path}",
        "setup.summary.game": "Game directory: {path}",
        "setup.summary.real_mods": "Real Mods path: {path}",
        "setup.summary.sandbox_mods": "Sandbox Mods path: {path}",
        "setup.summary.sandbox_archive": "Sandbox archive path: {path}",
        "setup.summary.real_archive": "Real archive path: {path}",
        "setup.summary.watched_1": "Watched downloads path 1: {path}",
        "setup.summary.watched_2": "Watched downloads path 2: {path}",
        "setup.summary.language": "App language: {language}",
        "setup.summary.steam_enabled": "Steam auto-start before launch: Enabled",
        "setup.summary.steam_disabled": "Steam auto-start before launch: Disabled",
    },
    LANGUAGE_PORTUGUESE_BRAZIL: {
        "shell.version": "Versão {version}",
        "shell.release_check_available": "Verificação de versão disponível em Configuração",
        "shell.workspaces": "Áreas",
        "workspace.library": "Biblioteca",
        "workspace.setup": "Configuração",
        "workspace.packages": "Pacotes",
        "workspace.install": "Instalar",
        "workspace.discover": "Descobrir",
        "workspace.compare": "Comparar",
        "workspace.history": "Histórico",
        "setup.page.eyebrow": "Pastas e ferramentas",
        "setup.page.title": "Configuração",
        "setup.page.subtitle": "Defina suas pastas. As ferramentas ficam à direita.",
        "setup.main_intro": "Defina as pastas uma vez e depois use Pacotes, Comparar e Biblioteca.",
        "setup.quickstart": "Começo rápido",
        "setup.quickstart.readiness": "Começo rápido: defina a pasta do jogo, a pasta Mods real e a pasta Mods sandbox.",
        "setup.quickstart.intro": "Pasta do jogo, pasta Mods real, pasta Mods sandbox.",
        "setup.folders": "Pastas",
        "setup.folders.intro": "Salvar configuração guarda estes caminhos. Detectar pastas do jogo só lê o ambiente instalado.",
        "setup.extras": "Extras",
        "setup.extras.intro": "Pastas de arquivo, Nexus e opções da Steam são opcionais.",
        "setup.backup": "Backup",
        "setup.backup.intro": "Exportar cria um pacote. Inspecionar é só leitura. Executar restauração grava apenas nas pastas configuradas.",
        "setup.managed": "Pastas gerenciadas",
        "setup.details": "Detalhes",
        "setup.support": "Suporte",
        "setup.support.intro": "Ferramentas de backup primeiro, pastas gerenciadas abaixo.",
        "setup.language": "Idioma do app",
        "setup.language.option.system": "Padrão do sistema",
        "setup.language.option.en": "Inglês",
        "setup.language.option.pt-BR": "Português (Brasil)",
        "setup.game_folder": "Pasta do jogo (instalação real)",
        "setup.real_mods_folder": "Pasta Mods real",
        "setup.sandbox_mods_folder": "Pasta Mods sandbox",
        "setup.sandbox_archive_folder": "Pasta de arquivo do sandbox",
        "setup.real_archive_folder": "Pasta de arquivo dos Mods reais",
        "setup.nexus_api_key": "Chave de API do Nexus",
        "setup.release": "Versão do Cinderleaf",
        "setup.managed_sandbox_mods": "Mods sandbox gerenciados",
        "setup.managed_sandbox_archive": "Arquivo sandbox gerenciado",
        "setup.managed_real_archive": "Arquivo de Mods reais gerenciado",
        "setup.managed_real_logs": "Logs gerenciados / Real",
        "setup.managed_sandbox_logs": "Logs gerenciados / Sandbox",
        "setup.managed.placeholder": "<defina a pasta do jogo primeiro>",
        "setup.managed.placeholder.invalid": "<a pasta do jogo ainda não está pronta>",
        "setup.save": "Salvar configuração",
        "setup.detect": "Detectar pastas do jogo",
        "setup.choose_game": "Escolher pasta do jogo",
        "setup.choose_real_mods": "Escolher Mods reais",
        "setup.open_real_mods": "Abrir Mods reais",
        "setup.choose_sandbox_mods": "Escolher Mods sandbox",
        "setup.open_sandbox_mods": "Abrir Mods sandbox",
        "setup.choose_sandbox_archive": "Escolher arquivo sandbox",
        "setup.open_sandbox_archive": "Abrir arquivo sandbox",
        "setup.choose_real_archive": "Escolher arquivo real",
        "setup.open_real_archive": "Abrir arquivo real",
        "setup.open_folder": "Abrir pasta",
        "setup.migrate_managed": "Migrar pastas configuradas",
        "setup.migrate_managed_tooltip": "Move as pastas configuradas de Mods sandbox e de arquivo para os caminhos gerenciados pelo Cinderleaf dentro da pasta do jogo.",
        "setup.check_nexus": "Verificar conexão com Nexus",
        "setup.check_updates": "Verificar atualizações do app",
        "setup.open_release_page": "Abrir página da versão",
        "setup.export_backup": "Exportar backup",
        "setup.inspect_backup": "Inspecionar backup",
        "setup.execute_restore": "Executar restauração",
        "setup.steam_auto_start": "Tentar iniciar a Steam antes de abrir o jogo quando ela ainda não estiver em execução",
        "setup.steam_auto_start_tooltip": "Ajuda de início da Steam por tentativa para lançamentos Vanilla, SMAPI e sandbox.",
        "setup.app_update_status": "Verifique atualizações do app para comparar esta instalação com a versão mais recente do Cinderleaf.",
        "setup.managed_summary": "Derivado da pasta do jogo. Migre só quando quiser usar caminhos gerenciados pelo Cinderleaf.",
        "setup.managed_summary.no_game": "Defina a pasta do jogo para ver os caminhos gerenciados pelo Cinderleaf. Os caminhos atuais continuam funcionando até você escolher migrar.",
        "setup.managed_summary.invalid_game": "A pasta do jogo precisa apontar para uma instalação acessível do Stardew Valley antes que as pastas gerenciadas possam ser derivadas.",
        "setup.language.saved_restart": "Idioma salvo. Reinicie o Cinderleaf para aplicar o novo idioma do app em tudo.",
        "setup.language.saved_restart_short": "Configuração salva. Reinicie o Cinderleaf para aplicar o novo idioma do app.",
        "setup.language.applied": "Idioma do app atualizado na interface visível. Salve a configuração para manter isso da próxima vez.",
        "setup.saved_status": "Configuração salva em {path}",
        "setup.loaded_status": "Configuração salva carregada de {path}",
        "setup.core.game_short": "Pasta do jogo",
        "setup.core.real_mods_short": "Pasta Mods real",
        "setup.core.sandbox_mods_short": "Pasta Mods sandbox",
        "setup.readiness.ready": "Tudo pronto. Salve a configuração se quiser manter estes caminhos e depois inspecione um pacote em Pacotes.",
        "setup.readiness.empty": "Começo rápido: defina a pasta do jogo, a pasta Mods real e a pasta Mods sandbox.",
        "setup.readiness.partial": "{count}/3 caminhos principais definidos. Adicione {missing} para começar em Pacotes, Comparar e Biblioteca.",
        "setup.first_run.ready": "Tudo pronto. Você já pode inspecionar um pacote e salvar a configuração quando quiser manter estes caminhos.",
        "setup.first_run.empty": "O começo rápido está vazio. Defina a pasta do jogo, a pasta Mods real e a pasta Mods sandbox para começar.",
        "setup.first_run.partial_prefix": "A configuração está quase pronta.",
        "setup.first_run.partial": "A configuração está quase pronta. Adicione {missing} para começar e depois salve a configuração quando quiser manter estes caminhos.",
        "setup.summary.saved": "Configuração salva.",
        "setup.summary.state_file": "Arquivo de estado: {path}",
        "setup.summary.game": "Pasta do jogo: {path}",
        "setup.summary.real_mods": "Pasta Mods real: {path}",
        "setup.summary.sandbox_mods": "Pasta Mods sandbox: {path}",
        "setup.summary.sandbox_archive": "Pasta de arquivo do sandbox: {path}",
        "setup.summary.real_archive": "Pasta de arquivo real: {path}",
        "setup.summary.watched_1": "Pasta monitorada 1: {path}",
        "setup.summary.watched_2": "Pasta monitorada 2: {path}",
        "setup.summary.language": "Idioma do app: {language}",
        "setup.summary.steam_enabled": "Início automático da Steam antes do jogo: Ativado",
        "setup.summary.steam_disabled": "Início automático da Steam antes do jogo: Desativado",
    },
}


def normalize_language_preference(preference: str | None) -> str:
    if preference in SUPPORTED_LANGUAGE_PREFERENCES:
        return preference
    return DEFAULT_LANGUAGE_PREFERENCE


def resolve_effective_language(
    preference: str | None,
    *,
    system_locale_name: str | None = None,
) -> str:
    normalized_preference = normalize_language_preference(preference)
    if normalized_preference != DEFAULT_LANGUAGE_PREFERENCE:
        return normalized_preference

    locale_name = (system_locale_name or QLocale.system().bcp47Name()).replace("_", "-")
    if locale_name.casefold().startswith("pt"):
        return LANGUAGE_PORTUGUESE_BRAZIL
    return LANGUAGE_ENGLISH


@dataclass(frozen=True, slots=True)
class UiLocalizer:
    preference: str
    effective_language: str

    @classmethod
    def from_preference(
        cls,
        preference: str | None,
        *,
        system_locale_name: str | None = None,
    ) -> UiLocalizer:
        normalized_preference = normalize_language_preference(preference)
        return cls(
            preference=normalized_preference,
            effective_language=resolve_effective_language(
                normalized_preference,
                system_locale_name=system_locale_name,
            ),
        )

    def text(self, key: str, **kwargs: object) -> str:
        template = _TRANSLATIONS[self.effective_language].get(
            key,
            _TRANSLATIONS[LANGUAGE_ENGLISH].get(key, key),
        )
        return template.format(**kwargs)

    def language_options(self) -> tuple[tuple[str, str], ...]:
        return (
            (
                DEFAULT_LANGUAGE_PREFERENCE,
                self.text("setup.language.option.system"),
            ),
            (LANGUAGE_ENGLISH, self.text("setup.language.option.en")),
            (
                LANGUAGE_PORTUGUESE_BRAZIL,
                self.text("setup.language.option.pt-BR"),
            ),
        )
