"""Last-resort reporting for unexpected failures.

Known failures already surface as reviewed dialogs with technical details. An
unexpected one is different: the packaged app is windowed, so a traceback goes
nowhere and the action simply appears to do nothing. This records what happened
and points the owner at the file, without ever raising on its own.
"""

from __future__ import annotations

import platform
import sys
import traceback
from datetime import datetime, timezone
from itertools import count
from pathlib import Path
from types import TracebackType
from typing import Callable

CRASH_REPORT_DIRECTORY_NAME = "crash-reports"

CrashNotifier = Callable[[Path | None, str], None]


def crash_report_directory(state_file: Path) -> Path:
    return state_file.parent / CRASH_REPORT_DIRECTORY_NAME


def summarize_exception(exc_type: type[BaseException], exc: BaseException) -> str:
    text = str(exc).strip()
    return f"{exc_type.__name__}: {text}" if text else exc_type.__name__


def write_crash_report(
    *,
    report_directory: Path,
    exc_type: type[BaseException],
    exc: BaseException,
    exc_traceback: TracebackType | None,
    app_version: str,
    now: datetime | None = None,
) -> Path:
    """Write one report and return its path. Raises only if the write fails."""
    moment = now or datetime.now(timezone.utc)
    report_directory.mkdir(parents=True, exist_ok=True)
    details = "".join(traceback.format_exception(exc_type, exc, exc_traceback))
    report_text = "\n".join(
        (
            f"Cinderleaf {app_version}",
            f"Recorded: {moment.isoformat()}",
            f"Python: {sys.version.split()[0]}",
            f"Platform: {platform.platform()}",
            f"Packaged build: {'yes' if getattr(sys, 'frozen', False) else 'no'}",
            "",
            "This file may contain folder paths from this computer.",
            "Review it before sharing.",
            "",
            details,
        )
    )
    stem = f"crash-{moment.strftime('%Y%m%d-%H%M%S-%f')}"
    for attempt in count():
        suffix = f"-{attempt}" if attempt else ""
        report_path = report_directory / f"{stem}{suffix}.txt"
        try:
            with report_path.open("x", encoding="utf-8") as report:
                report.write(report_text)
        except FileExistsError:
            continue
        return report_path


def install_crash_reporter(
    *,
    report_directory: Path,
    app_version: str,
    notify: CrashNotifier,
) -> Callable[..., None]:
    """Record unexpected failures and report each distinct one once."""
    previous_hook = sys.excepthook
    reported_signatures: set[str] = set()

    def hook(
        exc_type: type[BaseException],
        exc: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            previous_hook(exc_type, exc, exc_traceback)
            return

        report_path: Path | None = None
        try:
            report_path = write_crash_report(
                report_directory=report_directory,
                exc_type=exc_type,
                exc=exc,
                exc_traceback=exc_traceback,
                app_version=app_version,
            )
        except Exception:
            # A reporter that raises would hide the original failure.
            report_path = None

        try:
            last_frame = traceback.extract_tb(exc_traceback)[-1] if exc_traceback else None
            signature = "|".join(
                (
                    exc_type.__name__,
                    last_frame.filename if last_frame else "",
                    str(last_frame.lineno) if last_frame else "",
                )
            )
            if signature not in reported_signatures:
                reported_signatures.add(signature)
                notify(report_path, summarize_exception(exc_type, exc))
        except Exception:
            pass

        # Keep the previous behaviour too: a source run still prints to stderr.
        previous_hook(exc_type, exc, exc_traceback)

    sys.excepthook = hook
    return hook
