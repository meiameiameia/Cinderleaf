from __future__ import annotations

from PySide6.QtWidgets import QGroupBox
from PySide6.QtWidgets import QGridLayout
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QLineEdit
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QTableWidget
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from sdvmm.app.i18n import UiLocalizer


class DiscoveryTabSurface(QWidget):
    def __init__(
        self,
        *,
        localizer: UiLocalizer,
        discovery_query_input: QLineEdit,
        discovery_filter_input: QLineEdit,
        discovery_filter_stats_label: QLabel,
        discovery_results_state_label: QLabel,
        discovery_table: QTableWidget,
        discovery_search_button: QPushButton,
        open_discovered_button: QPushButton,
    ) -> None:
        super().__init__()
        self._localizer = localizer
        self.setObjectName("discovery_tab")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        intro_label = QLabel(
            localizer.text("discovery.intro")
        )
        intro_label.setObjectName("discovery_intro_label")
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        discovery_search_group = QGroupBox(localizer.text("discovery.search_group"))
        discovery_search_group.setObjectName("discovery_search_group")
        discovery_search_group.setFlat(True)
        discovery_search_group.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        discovery_search_layout = QGridLayout(discovery_search_group)
        discovery_search_layout.setContentsMargins(10, 10, 10, 10)
        discovery_search_layout.setHorizontalSpacing(10)
        discovery_search_layout.setVerticalSpacing(6)
        search_query_label = QLabel(localizer.text("discovery.search_query"))
        discovery_search_layout.addWidget(search_query_label, 0, 0)
        discovery_search_layout.addWidget(discovery_query_input, 0, 1, 1, 2)
        discovery_search_layout.addWidget(discovery_search_button, 0, 3)
        discovery_search_layout.addWidget(open_discovered_button, 1, 3)
        discovery_search_layout.setColumnStretch(1, 1)
        layout.addWidget(discovery_search_group)

        discovery_results_group = QGroupBox(localizer.text("discovery.results_group"))
        discovery_results_group.setObjectName("discovery_results_group")
        discovery_results_group.setFlat(True)
        discovery_results_layout = QVBoxLayout(discovery_results_group)
        discovery_results_layout.setContentsMargins(10, 10, 10, 10)
        discovery_results_layout.setSpacing(8)
        discovery_results_layout.addWidget(discovery_results_state_label)
        discovery_filter_layout = QHBoxLayout()
        discovery_filter_layout.setSpacing(8)
        filter_label = QLabel(localizer.text("discovery.filter"))
        discovery_filter_layout.addWidget(filter_label)
        discovery_filter_layout.addWidget(discovery_filter_input, 1)
        discovery_filter_layout.addWidget(discovery_filter_stats_label)
        discovery_results_layout.addLayout(discovery_filter_layout)
        discovery_results_layout.addWidget(discovery_table)
        layout.addWidget(discovery_results_group)
        layout.setStretch(1, 1)

        self.search_group = discovery_search_group
        self.results_group = discovery_results_group
        self.intro_label = intro_label
        self.results_state_label = discovery_results_state_label
        self.search_query_label = search_query_label
        self.filter_label = filter_label

    def retranslate(self, localizer: UiLocalizer) -> None:
        self._localizer = localizer
        self.intro_label.setText(localizer.text("discovery.intro"))
        self.search_group.setTitle(localizer.text("discovery.search_group"))
        self.results_group.setTitle(localizer.text("discovery.results_group"))
        self.search_query_label.setText(localizer.text("discovery.search_query"))
        self.filter_label.setText(localizer.text("discovery.filter"))
