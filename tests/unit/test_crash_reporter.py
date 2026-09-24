from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sdvmm.app.crash_reporter import (
    crash_report_directory,
    install_crash_reporter,
    summarize_exception,
    write_crash_report,
)


def _raise(message: str = "synthetic failure") -> None:
    raise RuntimeError(message)


def _captured_exception() -> tuple[type[BaseException], BaseException, object]:
    try:
        _raise()
    except RuntimeError:
        return sys.exc_info()  # type: ignore[return-value]
    raise AssertionError("expected the helper to raise")


@pytest.fixture
def restore_excepthook():
    original = sys.excepthook
    yield
    sys.excepthook = original


def test_crash_report_directory_sits_beside_the_app_state(tmp_path: Path) -> None:
    state_file = tmp_path / "sdvmm" / "app-state.json"
    assert crash_report_directory(state_file) == tmp_path / "sdvmm" / "crash-reports"


def test_write_crash_report_records_the_failure_and_its_context(tmp_path: Path) -> None:
    exc_type, exc, exc_traceback = _captured_exception()

    report_path = write_crash_report(
        report_directory=tmp_path / "crash-reports",
        exc_type=exc_type,
        exc=exc,
        exc_traceback=exc_traceback,
        app_version="1.6.0",
    )

    text = report_path.read_text(encoding="utf-8")
    assert report_path.parent == tmp_path / "crash-reports"
    assert "Cinderleaf 1.6.0" in text
    assert "RuntimeError: synthetic failure" in text
    assert "_raise" in text, "the traceback itself must be recorded"
    # The owner may share this file, so it says what it can contain.
    assert "Review it before sharing." in text


def test_crash_reports_with_the_same_timestamp_do_not_overwrite(tmp_path: Path) -> None:
    exc_type, exc, exc_traceback = _captured_exception()
    timestamp = datetime(2026, 9, 24, tzinfo=timezone.utc)
    options = dict(
        report_directory=tmp_path / "crash-reports",
        exc_type=exc_type,
        exc=exc,
        exc_traceback=exc_traceback,
        app_version="1.6.0",
        now=timestamp,
    )

    first = write_crash_report(**options)
    second = write_crash_report(**options)

    assert first != second
    assert first.is_file() and second.is_file()


def test_installed_reporter_records_and_reports_unexpected_failures(
    tmp_path: Path, restore_excepthook: None,
) -> None:
    notices: list[tuple[Path | None, str]] = []
    hook = install_crash_reporter(
        report_directory=tmp_path / "crash-reports",
        app_version="1.6.0",
        notify=lambda path, summary: notices.append((path, summary)),
    )
    assert sys.excepthook is hook

    hook(*_captured_exception())

    assert len(notices) == 1
    report_path, summary = notices[0]
    assert report_path is not None and report_path.is_file()
    assert summary == "RuntimeError: synthetic failure"


def test_repeated_identical_failures_report_once_but_are_all_recorded(
    tmp_path: Path, restore_excepthook: None,
) -> None:
    notices: list[tuple[Path | None, str]] = []
    hook = install_crash_reporter(
        report_directory=tmp_path / "crash-reports",
        app_version="1.6.0",
        notify=lambda path, summary: notices.append((path, summary)),
    )

    for _ in range(3):
        hook(*_captured_exception())

    assert len(notices) == 1, "a repeating failure must not bury the owner in dialogs"
    assert len(list((tmp_path / "crash-reports").glob("crash-*.txt"))) == 3


def test_normal_exits_are_left_alone(tmp_path: Path, restore_excepthook: None) -> None:
    notices: list[object] = []
    forwarded: list[type[BaseException]] = []
    sys.excepthook = lambda exc_type, exc, tb: forwarded.append(exc_type)
    hook = install_crash_reporter(
        report_directory=tmp_path / "crash-reports",
        app_version="1.6.0",
        notify=lambda path, summary: notices.append(summary),
    )

    for exit_type in (SystemExit, KeyboardInterrupt):
        try:
            raise exit_type()
        except BaseException:
            hook(*sys.exc_info())  # type: ignore[arg-type]

    assert notices == []
    assert not (tmp_path / "crash-reports").exists()
    assert forwarded == [SystemExit, KeyboardInterrupt]


def test_reporting_still_happens_when_the_file_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore_excepthook: None,
) -> None:
    notices: list[tuple[Path | None, str]] = []

    def failing_mkdir(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)
    hook = install_crash_reporter(
        report_directory=tmp_path / "crash-reports",
        app_version="1.6.0",
        notify=lambda path, summary: notices.append((path, summary)),
    )

    hook(*_captured_exception())

    assert notices == [(None, "RuntimeError: synthetic failure")]


def test_a_failing_notifier_never_replaces_the_original_failure(
    tmp_path: Path, restore_excepthook: None,
) -> None:
    forwarded: list[type[BaseException]] = []
    sys.excepthook = lambda exc_type, exc, tb: forwarded.append(exc_type)

    def broken_notify(_path: Path | None, _summary: str) -> None:
        raise ValueError("notifier is broken")

    hook = install_crash_reporter(
        report_directory=tmp_path / "crash-reports",
        app_version="1.6.0",
        notify=broken_notify,
    )

    hook(*_captured_exception())

    assert forwarded == [RuntimeError], "the original failure must still reach the previous hook"


def test_summary_handles_an_exception_without_a_message() -> None:
    assert summarize_exception(RuntimeError, RuntimeError()) == "RuntimeError"
    assert summarize_exception(ValueError, ValueError("bad path")) == "ValueError: bad path"
