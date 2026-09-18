from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest


# This must be set before pytest imports any test module that imports PySide6.
# Failing closed on the offscreen platform prevents GUI regression tests from
# rapidly opening native windows on a developer's desktop.
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Offscreen Qt has no fonts of its own and substitutes glyphs about twice as
# wide as Segoe UI, and it defaults to the Fusion style. Geometry assertions
# would then describe a layout that never ships. On Windows, give the headless
# platform the real system fonts and the native style without showing windows.
_WINDOWS_FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
if sys.platform == "win32" and _WINDOWS_FONT_DIR.is_dir():
    os.environ.setdefault("QT_QPA_FONTDIR", str(_WINDOWS_FONT_DIR))
    os.environ.setdefault("QT_STYLE_OVERRIDE", "windows11")


@pytest.fixture(autouse=True)
def _pinned_active_localizer():
    """Pin the process-wide localizer to English for every test.

    `get_active_ui_localizer()` is global state whose default follows the host's
    system locale, so service-layer text would otherwise be Portuguese on a
    pt-BR machine and English elsewhere. Tests that exercise Portuguese set the
    localizer themselves; this restores the default afterwards so ordering
    cannot leak one test's language into the next.
    """
    from sdvmm.app.i18n import (
        LANGUAGE_ENGLISH,
        UiLocalizer,
        get_active_ui_localizer,
        set_active_ui_localizer,
    )

    previous = get_active_ui_localizer()
    set_active_ui_localizer(UiLocalizer.from_preference(LANGUAGE_ENGLISH))
    try:
        yield
    finally:
        set_active_ui_localizer(previous)


@pytest.fixture
def fixtures_root() -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "mods_cases"


@pytest.fixture
def mods_case_path(fixtures_root: Path):
    def _resolve(case_name: str) -> Path:
        return fixtures_root / case_name / "Mods"

    return _resolve
