from __future__ import annotations

from sdvmm.app.i18n import LANGUAGE_PORTUGUESE_BRAZIL
from sdvmm.app.i18n import UiLocalizer
from sdvmm.app.i18n import resolve_effective_language


def test_resolve_effective_language_uses_system_portuguese_when_requested() -> None:
    assert (
        resolve_effective_language("system", system_locale_name="pt-BR")
        == LANGUAGE_PORTUGUESE_BRAZIL
    )


def test_resolve_effective_language_defaults_to_english_for_non_portuguese_system_locale() -> None:
    assert resolve_effective_language("system", system_locale_name="en-US") == "en"


def test_ui_localizer_returns_portuguese_workspace_and_setup_strings() -> None:
    localizer = UiLocalizer.from_preference("pt-BR")

    assert localizer.text("workspace.setup") == "Configuração"
    assert localizer.text("setup.page.title") == "Configuração"
    assert localizer.text("setup.language.option.system") == "Padrão do sistema"
