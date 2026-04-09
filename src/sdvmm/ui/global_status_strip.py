from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget


class GlobalStatusStrip(QGroupBox):
    def __init__(self) -> None:
        super().__init__("")
        self.setObjectName("global_status_strip_group")
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setProperty("shellRole", "workflow_status")
        self.setMinimumHeight(58)

        self.current_status_label = QLabel("Waiting for action.")
        self.current_status_label.setObjectName("global_status_current_label")
        self.current_status_label.setWordWrap(True)
        _set_status_label_style(self.current_status_label)

        summary_label = QLabel("Workflow")
        summary_label.setObjectName("global_status_summary_label")
        _set_status_label_style(summary_label, bold=True)
        summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        summary_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        status_strip_layout = QHBoxLayout(self)
        status_strip_layout.setContentsMargins(6, 4, 6, 4)
        status_strip_layout.setSpacing(6)
        status_strip_layout.addWidget(summary_label, 0)
        status_strip_layout.addWidget(
            _build_status_panel("Current", self.current_status_label),
            1,
        )

    def current_status_text(self) -> str:
        text = self.current_status_label.text().strip()
        return text or "Waiting for action."


def _build_status_panel(title: str, value_label: QLabel) -> QWidget:
    panel = QWidget()
    panel.setObjectName("global_status_panel")
    panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.setSpacing(1)
    title_label = QLabel(title)
    title_label.setObjectName("global_status_panel_title")
    _set_status_label_style(title_label, bold=True)
    title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    value_label.setProperty("statusRole", "value")
    value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    value_label.setWordWrap(True)
    value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    layout.addWidget(title_label)
    layout.addWidget(value_label)
    return panel


def _set_status_label_style(label: QLabel, *, bold: bool = False) -> None:
    font = QFont(label.font())
    font.setBold(bold)
    label.setFont(font)

    palette = label.palette()
    palette.setColor(QPalette.ColorRole.WindowText, palette.color(QPalette.ColorRole.WindowText))
    label.setPalette(palette)
