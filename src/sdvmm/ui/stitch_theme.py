from __future__ import annotations

from string import Template
from pathlib import Path
import sys

# Shared palette, type, radius and control metrics for the desktop UI.
STITCH_TOKENS: dict[str, str] = {
    "surface_canvas": "#0e1211",
    "surface_raised": "#151a18",
    "surface_overlay": "#1b211e",
    "surface_hover": "#222825",
    "surface_active": "#2a312d",
    "surface_sunken": "#0a0d0c",
    "border_solid": "#333b37",
    "border_solid_strong": "#454e49",
    "text_primary": "#e9edea",
    "text_secondary": "#a9b3ad",
    "text_disabled": "#6c756f",
    "brand": "#3d7a54",
    "brand_hover": "#478c61",
    "brand_pressed": "#336847",
    "brand_bg": "#16211b",
    "brand_text": "#f1f7f2",
    "brand_accent_text": "#a8d2b4",
    "attention": "#d9a441",
    "attention_bg": "#241c10",
    "attention_text": "#e8c98a",
    "danger": "#c25a4e",
    "danger_bg": "#2a1a19",
    "danger_text": "#e9b3ac",
    "info": "#5b8fb0",
    "info_text": "#a9c8dc",
    "border_faint": "rgba(233, 237, 234, 0.045)",
    "border_subtle": "rgba(233, 237, 234, 0.10)",
    "border_strong": "rgba(233, 237, 234, 0.18)",
    "brand_border": "rgba(110, 170, 130, 0.45)",
    "brand_border_soft": "rgba(110, 170, 130, 0.22)",
    "brand_fill_soft": "rgba(61, 122, 84, 0.20)",
    "attention_border": "rgba(217, 164, 65, 0.42)",
    "danger_border": "rgba(194, 90, 78, 0.42)",
    "selection_bg": "rgba(61, 122, 84, 0.55)",
    # Controls read as clickable: a visible fill, a boundary at ~3:1 against the
    # surfaces behind them, and a hover step that is obvious at a glance.
    "control_fill": "#2f3833",
    "control_fill_hover": "#414d46",
    "control_fill_pressed": "#262e29",
    "control_border": "#5e6b64",
    "control_border_hover": "#8bb99a",
    "danger_fill": "#3a2422",
    "danger_border_strong": "#a5544a",
    "font_micro": "9pt",
    "font_caption": "9pt",
    "font_body": "10.5pt",
    "font_subtitle": "12pt",
    "font_title": "16pt",
    "control_content": "20px",
    "control_compact_content": "18px",
    "focus_border": "#8bb99a",
    "radius_none": "0px",
    "radius_control": "4px",
    "radius_surface": "6px",
}


def build_stitch_compact_widgets_stylesheet() -> str:
    runtime_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    return Template(_STITCH_STYLESHEET).substitute(
        STITCH_TOKENS,
        dropdown_icon=(runtime_root / "assets" / "chevron-down.svg").as_posix(),
    )


_STITCH_STYLESHEET = """
/* ── Base shell ──────────────────────────────────────────────────────────── */

QWidget#app_shell_root {
    background: $surface_sunken;
}

QMainWindow {
    background: $surface_sunken;
}

QWidget {
    color: $text_primary;
    font-family: "Segoe UI Variable Text", "Segoe UI";
    font-size: $font_body;
}

/* ── Dialogs ─────────────────────────────────────────────────────────────── */

QMessageBox,
QMessageBox QWidget {
    background: $surface_raised;
    color: $text_primary;
}

QMessageBox QLabel {
    background: transparent;
    color: $text_primary;
}

QMessageBox QPushButton {
    min-width: 72px;
}

/* ── Labels (base) ───────────────────────────────────────────────────────── */

QLabel {
    color: $text_primary;
}

/* ── QGroupBox — clean card style, no floating title artifact ────────────── */
/*
   Strategy: push the title text into the top padding using a large
   margin-top + matching padding-top so the ::title subcontrol renders
   inside the card body cleanly, with no border-cut artifact.
   The border stays fully closed (no gap for title text to float through).
*/

QGroupBox {
    background: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
    margin-top: 20px;
    padding-top: 10px;
    padding-left: 1px;
    padding-right: 1px;
    padding-bottom: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    padding: 0px;
    color: $text_secondary;
    font-size: $font_micro;
    font-weight: 700;
}

/* ── Workspace page backgrounds ──────────────────────────────────────────── */

QWidget#workspace_page,
QWidget#mods_workspace_page,
QWidget#discovery_workspace_page,
QWidget#archive_workspace_page,
QWidget#compare_tab,
QWidget#recovery_tab,
QWidget#packages_workspace_page,
QWidget#review_workspace_page,
QWidget#setup_workspace_page {
    background: $surface_canvas;
}

QWidget#history_workspace_page {
    background: $surface_canvas;
}

QWidget#plan_install_tab_content,
QWidget#setup_surface_content_widget,
QWidget#setup_scroll_viewport,
QWidget#plan_install_scroll_viewport {
    background: $surface_canvas;
}

QWidget#setup_surface_workspace_band,
QWidget#setup_surface_main_column,
QWidget#setup_surface_secondary_column,
QWidget#setup_surface_primary_actions,
QWidget#history_workspace_body,
QWidget#history_archive_panel,
QWidget#history_recovery_panel,
QWidget#archive_tab,
QWidget#recovery_tab,
QWidget#packages_top_grid,
QWidget#mods_inventory_source_actions_widget,
QWidget#mods_inventory_launch_actions_widget,
QWidget#mods_smapi_primary_row,
QWidget#mods_smapi_secondary_row,
QWidget#packages_review_actions_widget,
QWidget#packages_review_controls_widget,
QWidget#packages_intake_controls_widget,
QWidget#packages_queue_controls_widget,
QWidget#packages_queue_header_widget,
QWidget#packages_queue_bulk_actions_widget,
QWidget#packages_watcher_runtime_actions_widget,
QWidget#packages_watcher_primary_actions_widget,
QWidget#packages_watcher_secondary_actions_widget {
    background: transparent;
}

/* ── Specific surface panels ─────────────────────────────────────────────── */

QWidget#archive_state_panel {
    background: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
}

QFrame#setup_secondary_panel {
    background: transparent;
    border: none;
    border-radius: $radius_none;
}

QWidget#setup_surface_main_column,
QWidget#setup_surface_secondary_column {
    background: transparent;
}

QWidget#setup_surface_primary_actions QPushButton {
    min-height: 24px;
}

QWidget#setup_actions_widget QPushButton {
    min-height: 25px;
}

/* ── Page header ─────────────────────────────────────────────────────────── */

QFrame#workspace_page_header {
    background: transparent;
    border-radius: $radius_none;
}

QLabel#workspace_page_eyebrow {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel#workspace_page_title {
    color: $text_primary;
    font-family: "Segoe UI Variable Display", "Segoe UI";
    font-size: $font_title;
    font-weight: 600;
}

QLabel#workspace_page_subtitle {
    color: $text_secondary;
    font-size: $font_body;
}

/* ── State / feedback labels ─────────────────────────────────────────────── */

QLabel#mods_inventory_state_label,
QLabel#discovery_results_state_label,
QLabel#packages_workspace_state_label,
QLabel#plan_install_state_label,
QLabel#archive_empty_state_label,
QLabel#archive_state_hint_label,
QLabel#compare_summary_label {
    background: $surface_canvas;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
    padding: 7px 12px;
    color: $text_primary;
    font-size: $font_caption;
}

QLabel#mods_inventory_state_label[feedbackTone="empty"],
QLabel#discovery_results_state_label[feedbackTone="empty"],
QLabel#packages_workspace_state_label[feedbackTone="empty"],
QLabel#plan_install_state_label[feedbackTone="empty"],
QLabel#archive_empty_state_label[feedbackTone="empty"],
QLabel#compare_summary_label[feedbackTone="empty"] {
    background: $surface_canvas;
    border-color: $border_faint;
    color: $text_secondary;
}

QLabel#mods_inventory_state_label[feedbackTone="muted"],
QLabel#discovery_results_state_label[feedbackTone="muted"],
QLabel#packages_workspace_state_label[feedbackTone="muted"],
QLabel#plan_install_state_label[feedbackTone="muted"],
QLabel#archive_state_hint_label[feedbackTone="muted"],
QLabel#compare_summary_label[feedbackTone="muted"] {
    background: $surface_raised;
    border-color: $border_subtle;
    color: $text_secondary;
}

QLabel#mods_inventory_state_label[feedbackTone="ready"],
QLabel#discovery_results_state_label[feedbackTone="ready"],
QLabel#packages_workspace_state_label[feedbackTone="ready"],
QLabel#plan_install_state_label[feedbackTone="ready"],
QLabel#archive_state_hint_label[feedbackTone="ready"],
QLabel#compare_summary_label[feedbackTone="ready"] {
    background: $brand_bg;
    border-color: $brand_border_soft;
    color: $brand_accent_text;
}

QLabel#mods_inventory_state_label[feedbackTone="active"],
QLabel#discovery_results_state_label[feedbackTone="active"],
QLabel#packages_workspace_state_label[feedbackTone="active"],
QLabel#plan_install_state_label[feedbackTone="active"],
QLabel#archive_empty_state_label[feedbackTone="active"],
QLabel#archive_state_hint_label[feedbackTone="active"],
QLabel#compare_summary_label[feedbackTone="active"] {
    background: $attention_bg;
    border-color: $attention_border;
    color: $attention_text;
}

/* ── Top context + status strip group boxes ──────────────────────────────── */

QGroupBox#top_context_surface_group,
QGroupBox#global_status_strip_group {
    background: $surface_sunken;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
    margin-top: 0px;
    padding-top: 0px;
    padding-left: 0px;
    padding-right: 0px;
    padding-bottom: 0px;
}

QGroupBox#top_context_surface_group::title,
QGroupBox#global_status_strip_group::title {
    padding: 0px;
    margin: 0px;
    width: 0px;
    height: 0px;
    color: transparent;
}

/* ── Top context inner panels ────────────────────────────────────────────── */

QWidget#top_context_brand_panel,
QWidget#top_context_operational_panel,
QWidget#top_context_environment_panel,
QWidget#top_context_runtime_panel,
QWidget#top_context_active_context_panel {
    background: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
}

QWidget#top_context_header {
    background: transparent;
    border-bottom: none;
    padding-bottom: 0px;
}

QWidget#top_context_body {
    background: transparent;
}

QPushButton#top_context_toggle_button {
    min-height: 0px;
    padding: 3px 10px;
}

QWidget#global_status_panel {
    background: transparent;
    border: none;
    border-radius: $radius_none;
}

QWidget#top_context_environment_panel[panelVariant="inline"],
QWidget#top_context_runtime_panel[panelVariant="inline"],
QWidget#top_context_active_context_panel[panelVariant="inline"] {
    background: transparent;
    border: none;
    border-radius: $radius_none;
}

/* ── Output group boxes ──────────────────────────────────────────────────── */

QGroupBox#discovery_output_group,
QGroupBox#compare_output_group,
QGroupBox#packages_output_group,
QGroupBox#plan_install_output_group,
QGroupBox#recovery_output_group,
QGroupBox#archive_output_group,
QGroupBox#setup_output_group {
    background: $surface_canvas;
    border: 1px solid $border_subtle;
}

QGroupBox#setup_surface_group,
QGroupBox#setup_advanced_group {
    background: $surface_raised;
}

QGroupBox#setup_backup_restore_group {
    background: $surface_raised;
}

QGroupBox#setup_output_group {
    background: $surface_canvas;
}

QGroupBox#setup_backup_restore_group::title,
QGroupBox#setup_output_group::title {
    color: $text_disabled;
}

/* ── Setup page labels ───────────────────────────────────────────────────── */

QLabel#setup_main_column_intro_label {
    color: $text_secondary;
    font-size: $font_caption;
}

QFrame#setup_quickstart_panel {
    background: $brand_bg;
    border: 1px solid $brand_border_soft;
    border-radius: $radius_surface;
}

QLabel#setup_quickstart_label {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel#setup_quickstart_intro_label {
    color: $text_secondary;
    font-size: $font_caption;
}

QLabel#setup_secondary_section_label {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel#setup_local_setup_intro_label,
QLabel#setup_advanced_intro_label,
QLabel#setup_backup_restore_intro_label,
QLabel#setup_secondary_intro_label {
    color: $text_secondary;
    font-size: $font_caption;
}

QLabel#setup_secondary_intro_label {
    color: $text_secondary;
}

QLabel[setupFieldLabel="true"] {
    color: $text_secondary;
    font-size: $font_micro;
    font-weight: 700;
}

/* ── Brand / top bar labels ──────────────────────────────────────────────── */

QLabel#top_context_scope_label {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QWidget[contextRole="scopeChip"] {
    background: $surface_raised;
    border: none;
    border-radius: $radius_surface;
}

QLabel[contextRole="scopeCaption"] {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel[contextRole="scopeValue"] {
    color: $text_primary;
    font-size: $font_caption;
    font-weight: 600;
}

QLabel#top_context_brand_eyebrow {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel#top_context_brand_title {
    color: $text_primary;
    font-family: "Segoe UI Variable Display", "Segoe UI";
    font-size: $font_subtitle;
    font-weight: 600;
}

QLabel#top_context_brand_subtitle {
    color: $text_secondary;
    font-size: $font_caption;
}

QLabel#global_status_panel_title,
QLabel#top_context_section_title {
    color: $text_secondary;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel#global_status_summary_label {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

QLabel[contextRole="value"] {
    color: $text_primary;
    font-size: $font_caption;
    font-weight: 600;
}

QLabel[contextRole="caption"],
QLabel[statusRole="value"] {
    color: $text_secondary;
    font-size: $font_caption;
}

/* ── Workspace shell / nav rail ──────────────────────────────────────────── */

QFrame#workspace_shell_frame {
    background: transparent;
}

QFrame#workspace_nav_rail {
    background: $surface_sunken;
    border: 1px solid $brand_border_soft;
    border-radius: $radius_surface;
}

QFrame#workspace_nav_brand_panel {
    background: $surface_canvas;
    border: 1px solid $brand_border_soft;
    border-radius: $radius_surface;
}

QFrame#workspace_nav_brand_panel[navCollapsed="true"] {
    background: $surface_canvas;
    border-color: $brand_border_soft;
    border-radius: $radius_surface;
}

QWidget#workspace_nav_brand_header,
QWidget#workspace_nav_brand_text_stack {
    background: transparent;
}

QLabel#workspace_nav_brand_icon {
    background: $surface_canvas;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
}

QFrame#workspace_nav_brand_panel[navCollapsed="true"] QLabel#workspace_nav_brand_icon {
    border-radius: $radius_surface;
    background: $surface_canvas;
}

QLabel#workspace_nav_brand_title {
    color: $text_primary;
    font-family: "Segoe UI Variable Display", "Segoe UI";
    font-size: $font_subtitle;
    font-weight: 700;
}

QLabel#workspace_nav_brand_version,
QLabel#workspace_nav_section_label {
    color: $text_secondary;
    font-size: $font_micro;
}

QLabel#workspace_nav_brand_subtitle {
    color: $text_primary;
    font-size: $font_caption;
    font-weight: 500;
}

QLabel#workspace_nav_brand_version {
    color: $text_secondary;
    font-size: $font_micro;
    font-weight: 700;
}

QPushButton#workspace_nav_toggle_button {
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0px;
    border-radius: $radius_control;
    background: $control_fill;
    border: 1px solid $control_border;
}

QPushButton[buttonRole="nav-toggle"] {
    background: $control_fill;
    color: $text_primary;
    padding: 0px;
    border-radius: $radius_control;
    border: 1px solid $control_border;
}

QPushButton[buttonRole="nav-toggle"]:hover {
    background: $control_fill_hover;
    border-color: $control_border_hover;
}

QPushButton[buttonRole="nav-toggle"]:pressed {
    background: $surface_overlay;
    border-color: $brand_border;
}

QPushButton#workspace_nav_toggle_button:hover {
    background: $surface_overlay;
    border-color: $border_subtle;
}

QPushButton#workspace_nav_toggle_button:pressed {
    background: $surface_overlay;
    border-color: $brand_border;
}

/* Section divider labels in the nav rail */
QLabel#workspace_nav_section_label {
    color: $brand_accent_text;
    font-size: $font_micro;
    font-weight: 700;
}

/* ── Nav rail workspace buttons ──────────────────────────────────────────── */

/* State is fill + weight. The
   left inset that the old 3px accent border occupied is now padding, so
   nothing shifts, and no state rule can bring the stripe back. */

QPushButton[navRole="workspace"] {
    min-height: 20px;
    padding: 6px 10px 6px 12px;
    border: 1px solid transparent;
    border-radius: $radius_control;
    background: transparent;
    color: $text_secondary;
    text-align: left;
    font-size: $font_body;
    font-weight: 400;
}

QPushButton[navRole="workspace"][navCollapsed="true"] {
    padding: 6px;
    text-align: center;
    border-radius: $radius_control;
}

QPushButton[navRole="workspace"]:hover {
    background: $control_fill_hover;
    color: $text_primary;
    border-color: $control_border_hover;
}

QPushButton[navRole="workspace"]:checked {
    background: $surface_active;
    color: $text_primary;
    font-weight: 600;
}

/* ── Workspace tab widget (hidden tab bar) ───────────────────────────────── */

QTabWidget#workspace_nav_tabs::pane {
    border: none;
    background: $surface_canvas;
    left: -1px;
}

QTabBar#workspace_nav_tabbar {
    background: transparent;
    max-width: 0px;
    width: 0px;
    min-width: 0px;
    margin: 0px;
    padding: 0px;
}

QTabBar#workspace_nav_tabbar::tab {
    max-width: 0px;
    width: 0px;
    min-width: 0px;
    min-height: 0px;
    margin: 0px;
    padding: 0px;
    border: none;
    background: transparent;
    color: transparent;
}

QTabBar#workspace_nav_tabbar::tab:selected {
    background: transparent;
}

QTabBar#workspace_nav_tabbar::tab:hover:!selected {
    background: transparent;
}

QTabBar#workspace_nav_tabbar::tab:first {
    margin-top: 0px;
}

/* ── Mods workspace mode tab bar ─────────────────────────────────────────── */

QTabWidget#mods_workspace_mode_tabs::pane {
    border: none;
    background: transparent;
    top: 4px;
}

QTabWidget#history_workspace_tabs::pane {
    border: none;
    background: transparent;
    top: 4px;
}

QTabBar#mods_workspace_mode_tabbar {
    background: transparent;
    margin-bottom: 10px;
}

QTabBar#mods_workspace_mode_tabbar::tab {
    min-height: 28px;
    padding: 5px 13px;
    margin-right: 6px;
    background: $surface_raised;
    color: $text_secondary;
    border: 1px solid $border_subtle;
    border-radius: $radius_control;
    font-size: $font_caption;
    font-weight: 600;
}

QTabBar#mods_workspace_mode_tabbar::tab:hover:!selected {
    background: $surface_hover;
    border-color: $border_subtle;
    color: $text_primary;
}

QTabBar#mods_workspace_mode_tabbar::tab:selected {
    background: $surface_overlay;
    border-color: $brand_border_soft;
    color: $brand_accent_text;
}

/* ── Inventory / SMAPI controls panel ────────────────────────────────────── */

QFrame#mods_inventory_controls_panel,
QFrame#mods_smapi_controls_panel {
    background: transparent;
    border: none;
    border-radius: $radius_none;
}

/* ── Buttons (base) ──────────────────────────────────────────────────────── */

QPushButton {
    min-height: $control_content;
    padding: 5px 12px;
    border: 1px solid $control_border;
    border-radius: $radius_control;
    background: $control_fill;
    color: $text_primary;
}

QPushButton:hover {
    background: $control_fill_hover;
    border-color: $control_border_hover;
}

QPushButton:pressed {
    background: $control_fill_pressed;
    border-color: $control_border_hover;
}

QPushButton:focus {
    border-color: $focus_border;
}

QPushButton:disabled {
    background: $surface_raised;
    color: $text_disabled;
    border-color: $border_subtle;
}

/* ── Primary button ─────────────────────────────────────────────────────── */

QPushButton[buttonRole="primary"] {
    background: $brand;
    color: $text_primary;
    font-weight: 700;
    padding: 5px 15px;
    border-color: $brand_border;
}

QPushButton[buttonRole="primary"]:hover {
    background: $brand_hover;
    border-color: $brand;
}

QPushButton[buttonRole="primary"]:pressed {
    background: $brand_pressed;
    color: $brand_accent_text;
}

QPushButton[buttonRole="primary"]:disabled {
    background: $surface_raised;
    color: $text_disabled;
    border-color: $border_subtle;
}

/* ── Secondary button (sage green) ──────────────────────────────────────── */

QPushButton[buttonRole="secondary"] {
    background: $control_fill;
    color: $text_primary;
    padding: 5px 13px;
    border-color: $control_border;
    font-weight: 600;
}

QPushButton[buttonRole="secondary"]:hover {
    background: $control_fill_hover;
    border-color: $control_border_hover;
}

QPushButton[buttonRole="secondary"]:pressed {
    background: $control_fill_pressed;
    border-color: $control_border_hover;
}

QPushButton[buttonRole="secondary"]:disabled {
    background: $surface_raised;
    color: $text_disabled;
    border-color: $border_subtle;
}

/* ── Utility button ──────────────────────────────────────────────────────── */

QPushButton[buttonRole="utility"] {
    background: $control_fill;
    color: $text_primary;
    padding: 3px 9px;
    font-size: $font_caption;
    border-color: $control_border;
    font-weight: 600;
}

QPushButton[buttonRole="utility"]:hover {
    background: $control_fill_hover;
    border-color: $control_border_hover;
}

QPushButton[buttonRole="utility"]:pressed {
    background: $control_fill_pressed;
    border-color: $control_border_hover;
}

QPushButton[buttonRole="utility"]:disabled {
    background: $surface_raised;
    color: $text_disabled;
    border-color: $border_subtle;
}

/* Role selectors otherwise override the base keyboard-focus border. */
QPushButton[buttonRole]:focus,
QPushButton[navRole="workspace"]:focus,
QPushButton#workspace_nav_toggle_button:focus {
    border: 1px solid $focus_border;
}

/* ── Scroll areas ────────────────────────────────────────────────────────── */

QScrollArea#discovery_workspace_page_scroll_area,
QScrollArea#compare_tab_scroll_area,
QScrollArea#packages_workspace_page_scroll_area,
QScrollArea#history_workspace_page_scroll_area,
QScrollArea#archive_workspace_page_scroll_area,
QScrollArea#recovery_tab_scroll_area {
    border: none;
    background: transparent;
}

QWidget#discovery_workspace_page_scroll_area_viewport,
QWidget#compare_tab_scroll_area_viewport,
QWidget#packages_workspace_page_scroll_area_viewport,
QWidget#history_workspace_page_scroll_area_viewport,
QWidget#archive_workspace_page_scroll_area_viewport,
QWidget#recovery_tab_scroll_area_viewport,
QWidget#discovery_workspace_page_scroll_area_content,
QWidget#compare_tab_scroll_area_content,
QWidget#packages_workspace_page_scroll_area_content,
QWidget#history_workspace_page_scroll_area_content,
QWidget#archive_workspace_page_scroll_area_content,
QWidget#recovery_tab_scroll_area_content {
    background: transparent;
}

/* ── Controls tab button sizing overrides ────────────────────────────────── */

QWidget#mods_inventory_controls_tab QPushButton,
QWidget#mods_smapi_controls_tab QPushButton {
    min-height: $control_compact_content;
    padding: 3px 9px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="primary"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="primary"] {
    min-height: $control_compact_content;
    padding: 4px 11px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="secondary"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="secondary"] {
    min-height: $control_compact_content;
    padding: 3px 9px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="utility"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="utility"] {
    min-height: $control_compact_content;
    padding: 3px 7px;
}

/* ── SMAPI troubleshooting group ─────────────────────────────────────────── */

QGroupBox#mods_smapi_troubleshooting_group {
    margin-top: 20px;
}

QGroupBox#mods_smapi_troubleshooting_group::title {
    subcontrol-origin: margin;
    left: 10px;
    top: 4px;
    padding: 0px;
}

/* ── Selection / action card frames ──────────────────────────────────────── */

QFrame#mods_selection_summary_card,
QGroupBox#mods_selected_actions_group,
QFrame#inventory_update_source_intent_actions,
QFrame#inventory_sandbox_sync_actions,
QFrame#inventory_real_profile_actions,
QFrame#inventory_sandbox_profile_actions,
QGroupBox#mods_smapi_troubleshooting_group {
    background: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
}

QFrame#mods_selection_summary_card QLabel,
QGroupBox#mods_selected_actions_group QLabel,
QFrame#inventory_update_source_intent_actions QLabel,
QFrame#inventory_sandbox_sync_actions QLabel,
QFrame#inventory_real_profile_actions QLabel,
QFrame#inventory_sandbox_profile_actions QLabel {
    background: transparent;
}

QGroupBox#mods_selected_actions_group::title {
    subcontrol-origin: margin;
    left: 10px;
    top: 4px;
    padding: 0px;
}

QFrame#mods_selection_summary_card QLabel#mods_selection_context_intro_label {
    color: $text_primary;
}

/* ── Mods scroll area ────────────────────────────────────────────────────── */

QScrollArea#mods_selection_context_scroll_area {
    border: none;
    background: transparent;
}

QWidget#mods_selection_context_scroll_content {
    background: transparent;
}

/* ── SMAPI dependency selector ───────────────────────────────────────────── */

QComboBox#mods_smapi_dependency_selector,
QPushButton#mods_smapi_dependency_discover_button {
    min-height: 21px;
}

QPlainTextEdit#mods_smapi_troubleshooting_details_box {
    padding: 4px 8px;
}

/* ── Setup surface primary action sizing ─────────────────────────────────── */

QWidget#setup_surface_primary_actions QPushButton[buttonRole="primary"] {
    padding-left: 14px;
    padding-right: 14px;
}

QWidget#setup_surface_primary_actions QPushButton[buttonRole="utility"] {
    padding-left: 11px;
    padding-right: 11px;
}

QWidget#setup_managed_folders_action_row QPushButton[buttonRole="secondary"] {
    min-height: $control_compact_content;
    padding-top: 2px;
    padding-bottom: 2px;
    padding-left: 11px;
    padding-right: 11px;
}

/* ── Danger button ───────────────────────────────────────────────────────── */

QPushButton[buttonRole="danger"] {
    background: $danger_fill;
    color: $danger_text;
    border-color: $danger_border_strong;
    font-weight: 700;
}

QPushButton[buttonRole="danger"]:hover {
    background: $danger;
}

QPushButton[buttonRole="danger"]:pressed {
    background: $danger_bg;
}

QPushButton[buttonRole="danger"]:disabled {
    background: $surface_raised;
    color: $text_disabled;
    border-color: $border_subtle;
}

/* ── Discovery / compare / packages group boxes ──────────────────────────── */

QGroupBox#discovery_search_group,
QGroupBox#discovery_results_group,
QGroupBox#compare_results_group,
QGroupBox#packages_import_group,
QGroupBox#packages_watcher_group,
QGroupBox#packages_review_target_group,
QGroupBox#archive_controls_group,
QGroupBox#archive_results_group,
QGroupBox#plan_install_destination_group,
QGroupBox#plan_install_execute_group,
QGroupBox#plan_install_safety_panel_group,
QGroupBox#plan_install_staged_package_group,
QGroupBox#plan_install_review_summary_group,
QGroupBox#plan_install_facts_group {
    background: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_surface;
}

QGroupBox#packages_review_target_group::title,
QGroupBox#plan_install_execute_group::title,
QGroupBox#plan_install_staged_package_group::title,
QGroupBox#plan_install_safety_panel_group::title,
QGroupBox#mods_selected_actions_group::title {
    left: 10px;
    top: 4px;
    padding: 0px;
}

/* ── Help / hint labels ──────────────────────────────────────────────────── */

QLabel#compact_hint_label,
QLabel#packages_intake_review_flow_label,
QLabel#packages_watcher_scope_label,
QLabel#plan_install_execute_help_label,
QLabel#plan_install_overwrite_help_label,
QLabel#archive_empty_state_label,
QLabel#discovery_intro_label,
QLabel#archive_intro_label {
    color: $text_secondary;
    font-size: $font_caption;
}

/* ── Line edit / combo box / plain text edit ─────────────────────────────── */

QLineEdit,
QComboBox,
QSpinBox {
    background: $surface_sunken;
    border: 1px solid $control_border;
    border-radius: $radius_control;
    padding: 5px 9px;
    min-height: $control_content;
    color: $text_primary;
    selection-background-color: $brand;
    font-size: $font_body;
}

QPlainTextEdit {
    background: $surface_sunken;
    border: 1px solid $border_subtle;
    border-radius: $radius_control;
    padding: 5px 9px;
    color: $text_primary;
    selection-background-color: $brand;
    font-family: "Cascadia Mono", "Consolas";
    font-size: $font_caption;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid $focus_border;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QPlainTextEdit:disabled {
    background: $surface_canvas;
    color: $text_disabled;
    border-color: $border_subtle;
}

QComboBox {
    padding-right: 28px;
}

QComboBox:hover,
QComboBox:on {
    border-color: $control_border_hover;
    background: $control_fill_pressed;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border: none;
}

QComboBox::down-arrow {
    image: url("$dropdown_icon");
    width: 12px;
    height: 8px;
}

/* ── Combo box dropdown ──────────────────────────────────────────────────── */

QComboBox QAbstractItemView {
    background: $surface_overlay;
    color: $text_primary;
    border: 1px solid $border_strong;
    selection-background-color: $brand;
    selection-color: $brand_text;
}

/* ── Table widget ────────────────────────────────────────────────────────── */

QTableView,
QTableWidget {
    background: $surface_canvas;
    alternate-background-color: $surface_raised;
    gridline-color: transparent;
    border: 1px solid $border_subtle;
    border-radius: $radius_control;
    selection-background-color: $brand;
    selection-color: $brand_text;
    outline: 0;
}

QHeaderView {
    background: $surface_overlay;
    border: none;
    /* On the widget, not ::section, so measured and painted labels match. */
    font-size: $font_micro;
    font-weight: 700;
}

QHeaderView::section {
    background: $surface_overlay;
    color: $text_secondary;
    border: none;
    border-bottom: 1px solid $border_subtle;
    border-right: 1px solid $border_subtle;
    /* Right padding keeps room for the sort chevron painted after the label. */
    padding: 8px 24px 8px 10px;
}

/* The header view paints its own chevron beside the label; the platform
   style would otherwise place it above the text or at the section edge. */
QHeaderView::up-arrow,
QHeaderView::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
}

QTableCornerButton::section {
    background: $surface_overlay;
    border: none;
    border-bottom: 1px solid $border_subtle;
    border-right: 1px solid $border_subtle;
}

QTableWidget::item {
    padding: 4px 10px;
    border-bottom: 1px solid $border_faint;
}

QTableWidget::item:hover {
    background: $border_faint;
}

QTableWidget::item:selected {
    background: $brand;
    color: $brand_text;
    border-top: 1px solid $border_faint;
    border-bottom: 1px solid $border_faint;
}

QTableWidget::item:selected:hover {
    background: $brand;
}

QListWidget {
    background: $surface_canvas;
    alternate-background-color: $surface_raised;
    border: 1px solid $border_subtle;
    border-radius: $radius_control;
    color: $text_primary;
    selection-background-color: $brand;
    selection-color: $brand_text;
    outline: 0;
}

QListWidget::item {
    padding: 9px 11px;
    border-bottom: 1px solid $border_subtle;
}

QListWidget::item:hover {
    background: $border_faint;
}

QListWidget::item:selected {
    background: $brand;
    color: $brand_text;
}

QListWidget::item:selected:hover {
    background: $brand;
}

QListWidget#packages_intake_queue_list {
    background: $surface_raised;
    border-radius: $radius_control;
}

/* ── Scroll area (generic) ───────────────────────────────────────────────── */

QScrollArea {
    border: none;
    background: transparent;
}

QAbstractScrollArea::corner {
    background: $surface_overlay;
    border: none;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */

QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 3px;
}

QScrollBar::handle:vertical {
    background: $border_solid;
    min-height: 28px;
    border-radius: $radius_surface;
}

QScrollBar::handle:vertical:hover {
    background: $border_solid_strong;
}

QScrollBar:horizontal {
    background: transparent;
    height: 11px;
    margin: 3px;
}

QScrollBar::handle:horizontal {
    background: $border_solid;
    min-width: 28px;
    border-radius: $radius_surface;
}

QScrollBar::handle:horizontal:hover {
    background: $border_solid_strong;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
    height: 0;
    width: 0;
}

/* ── Checkbox ────────────────────────────────────────────────────────────── */

QCheckBox {
    spacing: 7px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: $radius_control;
    border: 1px solid $control_border;
    background: $surface_sunken;
}

 QCheckBox::indicator:hover {
    border-color: $control_border_hover;
}

QCheckBox::indicator:checked {
    background: $brand_pressed;
    border-color: $brand_accent_text;
}

/* ── Splitter ────────────────────────────────────────────────────────────── */

QSplitter::handle {
    background: transparent;
}

QSplitter#mods_workspace_splitter::handle {
    background: transparent;
}

/* ── Compact hint label ──────────────────────────────────────────────────── */

QLabel#compact_hint_label {
    color: $text_secondary;
    font-size: $font_caption;
}
"""
