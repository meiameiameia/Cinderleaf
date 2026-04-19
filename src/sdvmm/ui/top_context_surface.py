from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from sdvmm.app.i18n import UiLocalizer


class TopContextSurface(QGroupBox):
    def __init__(
        self,
        *,
        localizer: UiLocalizer,
        environment_status_label: QLabel,
        smapi_update_status_label: QLabel,
        smapi_log_status_label: QLabel,
        nexus_status_label: QLabel,
        watch_status_label: QLabel,
        operation_state_label: QLabel,
        sandbox_launch_status_label: QLabel,
        scan_context_label: QLabel,
        install_context_label: QLabel,
        collapse_toggle_button: QPushButton,
    ) -> None:
        super().__init__("")
        self._localizer = localizer
        self.setObjectName("top_context_surface_group")
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(0)
        self.setProperty("shellRole", "session_context")

        for value_label in (
            environment_status_label,
            smapi_update_status_label,
            smapi_log_status_label,
            nexus_status_label,
            watch_status_label,
            operation_state_label,
            sandbox_launch_status_label,
            scan_context_label,
            install_context_label,
        ):
            _prepare_context_value_label(value_label)

        context_layout = QVBoxLayout(self)
        context_layout.setContentsMargins(8, 8, 8, 8)
        context_layout.setSpacing(8)

        header_panel = QWidget()
        header_panel.setObjectName("top_context_header")
        header_layout = QHBoxLayout(header_panel)
        header_layout.setContentsMargins(2, 0, 2, 0)
        header_layout.setSpacing(10)

        header_text_stack = QWidget()
        header_text_stack.setObjectName("top_context_header_text_stack")
        header_text_layout = QVBoxLayout(header_text_stack)
        header_text_layout.setContentsMargins(0, 0, 0, 0)
        header_text_layout.setSpacing(2)

        brand_eyebrow = QLabel(localizer.text("top_context.eyebrow"))
        brand_eyebrow.setObjectName("top_context_brand_eyebrow")
        brand_title = QLabel(localizer.text("top_context.title"))
        brand_title.setObjectName("top_context_brand_title")
        brand_title.setWordWrap(True)
        header_text_layout.addWidget(brand_eyebrow)
        header_text_layout.addWidget(brand_title)
        header_layout.addWidget(header_text_stack, 1)
        header_layout.addWidget(
            collapse_toggle_button,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        body_panel = QWidget()
        body_panel.setObjectName("top_context_body")
        body_layout = QHBoxLayout(body_panel)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        brand_panel = QWidget()
        brand_panel.setObjectName("top_context_brand_panel")
        brand_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        brand_layout = QVBoxLayout(brand_panel)
        brand_layout.setContentsMargins(12, 10, 12, 10)
        brand_layout.setSpacing(4)

        brand_subtitle = QLabel(
            localizer.text("top_context.subtitle")
        )
        brand_subtitle.setObjectName("top_context_brand_subtitle")
        brand_subtitle.setWordWrap(True)

        active_context_group = QWidget()
        active_context_group.setObjectName("top_context_active_context_panel")
        active_context_group.setProperty("panelVariant", "inline")
        active_context_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        active_context_container_layout = QVBoxLayout(active_context_group)
        active_context_container_layout.setContentsMargins(0, 1, 0, 0)
        active_context_container_layout.setSpacing(4)
        active_context_section_label = _section_label(localizer.text("top_context.active_context"))
        active_context_section_label.setProperty(
            "translationKey",
            "top_context.active_context",
        )
        active_context_container_layout.addWidget(active_context_section_label)
        active_context_layout = QGridLayout()
        active_context_layout.setContentsMargins(0, 0, 0, 0)
        active_context_layout.setHorizontalSpacing(8)
        active_context_layout.setVerticalSpacing(4)
        active_context_layout.addWidget(
            _context_caption(
                localizer.text("top_context.scan_source"),
                translation_key="top_context.scan_source",
            ),
            0,
            0,
        )
        active_context_layout.addWidget(scan_context_label, 0, 1)
        active_context_layout.addWidget(
            _context_caption(
                localizer.text("top_context.install_target"),
                translation_key="top_context.install_target",
            ),
            1,
            0,
        )
        active_context_layout.addWidget(install_context_label, 1, 1)
        active_context_layout.setColumnMinimumWidth(0, 84)
        active_context_layout.setColumnStretch(1, 1)
        active_context_container_layout.addLayout(active_context_layout)

        brand_layout.addWidget(brand_subtitle)
        brand_layout.addWidget(active_context_group)
        brand_layout.addStretch(1)

        operations_group = QWidget()
        operations_group.setObjectName("top_context_operational_panel")
        operations_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        operations_container_layout = QVBoxLayout(operations_group)
        operations_container_layout.setContentsMargins(12, 10, 12, 10)
        operations_container_layout.setSpacing(5)
        operations_section_label = _section_label(localizer.text("top_context.operational"))
        operations_section_label.setProperty("translationKey", "top_context.operational")
        operations_container_layout.addWidget(operations_section_label)

        environment_group = QWidget()
        environment_group.setObjectName("top_context_environment_panel")
        environment_group.setProperty("panelVariant", "inline")
        environment_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        environment_container_layout = QVBoxLayout(environment_group)
        environment_container_layout.setContentsMargins(0, 0, 0, 0)
        environment_container_layout.setSpacing(4)
        environment_section_label = _section_label(localizer.text("top_context.environment"))
        environment_section_label.setProperty("translationKey", "top_context.environment")
        environment_container_layout.addWidget(environment_section_label)
        environment_layout = QGridLayout()
        environment_layout.setContentsMargins(0, 0, 0, 0)
        environment_layout.setHorizontalSpacing(8)
        environment_layout.setVerticalSpacing(4)
        environment_layout.addWidget(
            _context_caption(localizer.text("top_context.game"), translation_key="top_context.game"),
            0,
            0,
        )
        environment_layout.addWidget(environment_status_label, 0, 1)
        environment_layout.addWidget(
            _context_caption(
                localizer.text("top_context.smapi_update"),
                translation_key="top_context.smapi_update",
            ),
            1,
            0,
        )
        environment_layout.addWidget(smapi_update_status_label, 1, 1)
        environment_layout.addWidget(
            _context_caption(
                localizer.text("top_context.smapi_log"),
                translation_key="top_context.smapi_log",
            ),
            2,
            0,
        )
        environment_layout.addWidget(smapi_log_status_label, 2, 1)
        environment_layout.setColumnMinimumWidth(0, 76)
        environment_layout.setColumnStretch(1, 1)
        environment_container_layout.addLayout(environment_layout)

        runtime_group = QWidget()
        runtime_group.setObjectName("top_context_runtime_panel")
        runtime_group.setProperty("panelVariant", "inline")
        runtime_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        runtime_container_layout = QVBoxLayout(runtime_group)
        runtime_container_layout.setContentsMargins(0, 0, 0, 0)
        runtime_container_layout.setSpacing(4)
        runtime_section_label = _section_label(localizer.text("top_context.runtime"))
        runtime_section_label.setProperty("translationKey", "top_context.runtime")
        runtime_container_layout.addWidget(runtime_section_label)
        runtime_layout = QGridLayout()
        runtime_layout.setContentsMargins(0, 0, 0, 0)
        runtime_layout.setHorizontalSpacing(8)
        runtime_layout.setVerticalSpacing(4)
        runtime_layout.addWidget(
            _context_caption(localizer.text("top_context.nexus"), translation_key="top_context.nexus"),
            0,
            0,
        )
        runtime_layout.addWidget(nexus_status_label, 0, 1)
        runtime_layout.addWidget(
            _context_caption(
                localizer.text("top_context.watcher"),
                translation_key="top_context.watcher",
            ),
            1,
            0,
        )
        runtime_layout.addWidget(watch_status_label, 1, 1)
        runtime_layout.addWidget(
            _context_caption(
                localizer.text("top_context.operation"),
                translation_key="top_context.operation",
            ),
            2,
            0,
        )
        runtime_layout.addWidget(operation_state_label, 2, 1)
        runtime_layout.addWidget(
            _context_caption(
                localizer.text("top_context.sandbox_run"),
                translation_key="top_context.sandbox_run",
            ),
            3,
            0,
        )
        runtime_layout.addWidget(sandbox_launch_status_label, 3, 1)
        runtime_layout.setColumnMinimumWidth(0, 82)
        runtime_layout.setColumnStretch(1, 1)
        runtime_container_layout.addLayout(runtime_layout)

        operations_columns_layout = QHBoxLayout()
        operations_columns_layout.setContentsMargins(0, 0, 0, 0)
        operations_columns_layout.setSpacing(10)
        operations_columns_layout.addWidget(environment_group, 1)
        operations_columns_layout.addWidget(runtime_group, 1)
        operations_container_layout.addLayout(operations_columns_layout)

        body_layout.addWidget(brand_panel, 11)
        body_layout.addWidget(operations_group, 12)
        context_layout.addWidget(header_panel)
        context_layout.addWidget(body_panel)

        self.header_panel = header_panel
        self.body_panel = body_panel
        self.brand_panel = brand_panel
        self.operations_group = operations_group
        self.environment_group = environment_group
        self.runtime_group = runtime_group
        self.active_context_group = active_context_group
        self.brand_eyebrow = brand_eyebrow
        self.brand_title = brand_title
        self.brand_subtitle = brand_subtitle
        self.context_layout = context_layout
        self.header_layout = header_layout
        self.header_text_layout = header_text_layout
        self.body_layout = body_layout
        self.brand_layout = brand_layout
        self.active_context_container_layout = active_context_container_layout
        self.active_context_layout = active_context_layout
        self.operations_container_layout = operations_container_layout
        self.environment_container_layout = environment_container_layout
        self.environment_layout = environment_layout
        self.runtime_container_layout = runtime_container_layout
        self.runtime_layout = runtime_layout
        self.operations_columns_layout = operations_columns_layout

    def set_compact_mode(self, compact: bool) -> None:
        self.context_layout.setContentsMargins(
            4 if compact else 8,
            4 if compact else 8,
            4 if compact else 8,
            4 if compact else 8,
        )
        self.context_layout.setSpacing(4 if compact else 8)
        self.header_layout.setContentsMargins(0 if compact else 2, 0, 0 if compact else 2, 0)
        self.header_layout.setSpacing(6 if compact else 10)
        self.header_text_layout.setSpacing(1 if compact else 2)
        self.body_layout.setSpacing(6 if compact else 10)
        self.brand_layout.setContentsMargins(
            8 if compact else 12,
            6 if compact else 10,
            8 if compact else 12,
            6 if compact else 10,
        )
        self.brand_layout.setSpacing(2 if compact else 4)
        self.active_context_container_layout.setSpacing(2 if compact else 4)
        self.active_context_layout.setHorizontalSpacing(4 if compact else 8)
        self.active_context_layout.setVerticalSpacing(2 if compact else 4)
        self.active_context_layout.setColumnMinimumWidth(0, 64 if compact else 84)
        self.operations_container_layout.setContentsMargins(
            8 if compact else 12,
            6 if compact else 10,
            8 if compact else 12,
            6 if compact else 10,
        )
        self.operations_container_layout.setSpacing(3 if compact else 5)
        self.environment_container_layout.setSpacing(2 if compact else 4)
        self.environment_layout.setHorizontalSpacing(4 if compact else 8)
        self.environment_layout.setVerticalSpacing(2 if compact else 4)
        self.environment_layout.setColumnMinimumWidth(0, 60 if compact else 76)
        self.runtime_container_layout.setSpacing(2 if compact else 4)
        self.runtime_layout.setHorizontalSpacing(4 if compact else 8)
        self.runtime_layout.setVerticalSpacing(2 if compact else 4)
        self.runtime_layout.setColumnMinimumWidth(0, 60 if compact else 82)
        self.operations_columns_layout.setSpacing(6 if compact else 10)

    def set_details_expanded(self, expanded: bool) -> None:
        self.body_panel.setVisible(expanded)

    def retranslate(self, localizer: UiLocalizer) -> None:
        self._localizer = localizer
        self.brand_eyebrow.setText(localizer.text("top_context.eyebrow"))
        self.brand_title.setText(localizer.text("top_context.title"))
        self.brand_subtitle.setText(localizer.text("top_context.subtitle"))
        for label in self.findChildren(QLabel):
            translation_key = label.property("translationKey")
            if isinstance(translation_key, str) and translation_key:
                label.setText(localizer.text(translation_key))


def _context_caption(text: str, *, translation_key: str | None = None) -> QLabel:
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    label.setProperty("contextRole", "caption")
    if translation_key is not None:
        label.setProperty("translationKey", translation_key)
    label.setWordWrap(True)
    _set_auxiliary_label_style(label)
    return label


def _section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("top_context_section_title")
    _set_section_label_style(label)
    return label


def _set_label_font_weight(label: QLabel, *, bold: bool = False) -> None:
    font = QFont(label.font())
    font.setBold(bold)
    label.setFont(font)


def _apply_label_palette_role(label: QLabel, role: QPalette.ColorRole) -> None:
    palette = label.palette()
    palette.setColor(QPalette.ColorRole.WindowText, palette.color(role))
    label.setPalette(palette)


def _set_auxiliary_label_style(label: QLabel, *, bold: bool = False) -> None:
    _set_label_font_weight(label, bold=bold)
    _apply_label_palette_role(label, QPalette.ColorRole.WindowText)


def _set_section_label_style(label: QLabel) -> None:
    _set_label_font_weight(label, bold=True)
    _apply_label_palette_role(label, QPalette.ColorRole.WindowText)


def _prepare_context_value_label(label: QLabel) -> None:
    label.setProperty("contextRole", "value")
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
