from __future__ import annotations

import string

from sdvmm.app.i18n import LANGUAGE_ENGLISH
from sdvmm.app.i18n import LANGUAGE_PORTUGUESE_BRAZIL
from sdvmm.app.i18n import UiLocalizer
from sdvmm.app.i18n import _TRANSLATIONS
from sdvmm.app.i18n import resolve_effective_language


def _placeholder_names(template: str) -> set[str]:
    return {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(template)
        if field_name
    }


def test_translation_catalogues_cover_the_same_keys() -> None:
    english_keys = set(_TRANSLATIONS[LANGUAGE_ENGLISH])
    portuguese_keys = set(_TRANSLATIONS[LANGUAGE_PORTUGUESE_BRAZIL])

    # Both languages are shipped, so a key present in only one of them would
    # silently fall back to English for real users.
    assert sorted(english_keys - portuguese_keys) == []
    assert sorted(portuguese_keys - english_keys) == []


def test_translation_placeholders_match_across_languages() -> None:
    mismatches: list[tuple[str, set[str], set[str]]] = []
    for key, english_template in _TRANSLATIONS[LANGUAGE_ENGLISH].items():
        portuguese_template = _TRANSLATIONS[LANGUAGE_PORTUGUESE_BRAZIL].get(key)
        if portuguese_template is None:
            continue
        english_fields = _placeholder_names(english_template)
        portuguese_fields = _placeholder_names(portuguese_template)
        if english_fields != portuguese_fields:
            mismatches.append((key, english_fields, portuguese_fields))

    # A placeholder present in one language and not the other raises KeyError at
    # format() time, which surfaces as a crash only in that language.
    assert mismatches == []


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
    assert localizer.text("setup.managed.placeholder") == "<defina a pasta do jogo primeiro>"
    assert localizer.text("setup.managed.placeholder.invalid") == (
        "<a pasta do jogo ainda não está pronta>"
    )
    assert localizer.text("library.profile.create_sandbox_title") == "Criar perfil sandbox"
    assert localizer.text("library.profile.name_prompt") == "Nome do perfil:"
    assert localizer.text("library.profile.deleting") == "Excluindo..."
    assert localizer.text(
        "library.profile.delete_real_confirmation",
        name="Teste",
    ).startswith("Excluir o perfil de Mods reais 'Teste'?")
    assert localizer.text("library.update.newer_than_latest") == "Pré-lançamento"
