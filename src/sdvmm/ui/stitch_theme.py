from __future__ import annotations


def build_stitch_compact_widgets_stylesheet() -> str:
    return """
/* ── Base shell ──────────────────────────────────────────────────────────── */

QWidget#app_shell_root {
    background: #111315;
}

QMainWindow {
    background: #111315;
}

QWidget {
    color: #ede8e0;
    font-family: "Segoe UI Variable Text", "Segoe UI", "Trebuchet MS";
    font-size: 10.5pt;
}

/* ── Dialogs ─────────────────────────────────────────────────────────────── */

QMessageBox,
QMessageBox QWidget {
    background: #15181c;
    color: #ede8e0;
}

QMessageBox QLabel {
    background: transparent;
    color: #ede8e0;
}

QMessageBox QPushButton {
    min-width: 72px;
}

/* ── Labels (base) ───────────────────────────────────────────────────────── */

QLabel {
    color: #ede8e0;
}

/* ── QGroupBox — clean card style, no floating title artifact ────────────── */
/*
   Strategy: push the title text into the top padding using a large
   margin-top + matching padding-top so the ::title subcontrol renders
   inside the card body cleanly, with no border-cut artifact.
   The border stays fully closed (no gap for title text to float through).
*/

QGroupBox {
    background: #1a1e22;
    border: 1px solid rgba(220, 212, 200, 0.08);
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 10px;
    padding-left: 1px;
    padding-right: 1px;
    padding-bottom: 1px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 13px;
    top: 4px;
    padding: 0px;
    color: #a89483;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
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
    background: #15181c;
}

QWidget#history_workspace_page {
    background: #15181c;
}

QWidget#plan_install_tab_content,
QWidget#setup_surface_content_widget,
QWidget#setup_scroll_viewport,
QWidget#plan_install_scroll_viewport {
    background: #15181c;
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
    background: #161a1e;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 10px;
}

QFrame#setup_secondary_panel {
    background: #131619;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 12px;
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
    border-radius: 0px;
}

QLabel#workspace_page_eyebrow {
    color: #8ebb80;
    font-size: 7pt;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

QLabel#workspace_page_title {
    color: #f6f2eb;
    font-family: "Georgia", "Segoe UI Variable Display", "Segoe UI";
    font-size: 18.5pt;
    font-weight: 700;
}

QLabel#workspace_page_subtitle {
    color: #c0b4a8;
    font-size: 9.75pt;
}

/* ── State / feedback labels ─────────────────────────────────────────────── */

QLabel#mods_inventory_state_label,
QLabel#discovery_results_state_label,
QLabel#packages_workspace_state_label,
QLabel#plan_install_state_label,
QLabel#archive_empty_state_label,
QLabel#archive_state_hint_label,
QLabel#compare_summary_label {
    background: #161a1e;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 8px;
    padding: 7px 11px;
    color: #c8bdb1;
    font-size: 8.8pt;
}

QLabel#mods_inventory_state_label[feedbackTone="empty"],
QLabel#discovery_results_state_label[feedbackTone="empty"],
QLabel#packages_workspace_state_label[feedbackTone="empty"],
QLabel#plan_install_state_label[feedbackTone="empty"],
QLabel#archive_empty_state_label[feedbackTone="empty"],
QLabel#compare_summary_label[feedbackTone="empty"] {
    background: #161a1e;
    border-color: rgba(220, 212, 200, 0.06);
    color: #c2b5a7;
}

QLabel#mods_inventory_state_label[feedbackTone="muted"],
QLabel#discovery_results_state_label[feedbackTone="muted"],
QLabel#packages_workspace_state_label[feedbackTone="muted"],
QLabel#plan_install_state_label[feedbackTone="muted"],
QLabel#archive_state_hint_label[feedbackTone="muted"],
QLabel#compare_summary_label[feedbackTone="muted"] {
    background: #191d21;
    border-color: rgba(220, 212, 200, 0.08);
    color: #cfc3b7;
}

QLabel#mods_inventory_state_label[feedbackTone="ready"],
QLabel#discovery_results_state_label[feedbackTone="ready"],
QLabel#packages_workspace_state_label[feedbackTone="ready"],
QLabel#plan_install_state_label[feedbackTone="ready"],
QLabel#archive_state_hint_label[feedbackTone="ready"],
QLabel#compare_summary_label[feedbackTone="ready"] {
    background: #192219;
    border-color: rgba(142, 187, 128, 0.18);
    color: #dae7d3;
}

QLabel#mods_inventory_state_label[feedbackTone="active"],
QLabel#discovery_results_state_label[feedbackTone="active"],
QLabel#packages_workspace_state_label[feedbackTone="active"],
QLabel#plan_install_state_label[feedbackTone="active"],
QLabel#archive_empty_state_label[feedbackTone="active"],
QLabel#archive_state_hint_label[feedbackTone="active"],
QLabel#compare_summary_label[feedbackTone="active"] {
    background: #231f12;
    border-color: rgba(241, 187, 57, 0.16);
    color: #f0dfb6;
}

/* ── Top context + status strip group boxes ──────────────────────────────── */

QGroupBox#top_context_surface_group,
QGroupBox#global_status_strip_group {
    background: #121518;
    border: 1px solid rgba(220, 212, 200, 0.07);
    border-radius: 10px;
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
    background: #181c20;
    border-radius: 9px;
}

QWidget#top_context_header {
    background: transparent;
    border-bottom: 1px solid rgba(220, 212, 200, 0.06);
    padding-bottom: 2px;
}

QWidget#top_context_body {
    background: transparent;
}

QPushButton#top_context_toggle_button {
    min-height: 0px;
    padding: 2px 10px;
}

QWidget#global_status_panel {
    background: #161a1e;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 7px;
}

QWidget#top_context_environment_panel[panelVariant="inline"],
QWidget#top_context_runtime_panel[panelVariant="inline"],
QWidget#top_context_active_context_panel[panelVariant="inline"] {
    background: transparent;
    border-radius: 0px;
}

/* ── Output group boxes ──────────────────────────────────────────────────── */

QGroupBox#discovery_output_group,
QGroupBox#compare_output_group,
QGroupBox#packages_output_group,
QGroupBox#plan_install_output_group,
QGroupBox#recovery_output_group,
QGroupBox#archive_output_group,
QGroupBox#setup_output_group {
    background: #181c20;
    border: 1px solid rgba(220, 212, 200, 0.06);
}

QGroupBox#setup_surface_group,
QGroupBox#setup_advanced_group {
    background: #1d2227;
}

QGroupBox#setup_backup_restore_group {
    background: #171b1f;
}

QGroupBox#setup_output_group {
    background: #151819;
}

QGroupBox#setup_backup_restore_group::title,
QGroupBox#setup_output_group::title {
    color: #a08978;
}

/* ── Setup page labels ───────────────────────────────────────────────────── */

QLabel#setup_main_column_intro_label {
    color: #c8bcb0;
    font-size: 9.15pt;
}

QFrame#setup_quickstart_panel {
    background: rgba(142, 187, 128, 0.07);
    border: 1px solid rgba(142, 187, 128, 0.2);
    border-radius: 10px;
}

QLabel#setup_quickstart_label {
    color: #8ebb80;
    font-size: 7.25pt;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

QLabel#setup_quickstart_intro_label {
    color: #c4b7aa;
    font-size: 8.5pt;
}

QLabel#setup_secondary_section_label {
    color: #8ebb80;
    font-size: 7.1pt;
    font-weight: 700;
    letter-spacing: 0.17em;
    text-transform: uppercase;
}

QLabel#setup_local_setup_intro_label,
QLabel#setup_advanced_intro_label,
QLabel#setup_backup_restore_intro_label,
QLabel#setup_secondary_intro_label {
    color: #b2a69a;
    font-size: 8.6pt;
}

QLabel#setup_secondary_intro_label {
    color: #a4998c;
}

QLabel[setupFieldLabel="true"] {
    color: #c8b6a4;
    font-size: 7.75pt;
    font-weight: 700;
}

/* ── Brand / top bar labels ──────────────────────────────────────────────── */

QLabel#top_context_brand_eyebrow {
    color: #8ebb80;
    font-size: 7.5pt;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

QLabel#top_context_brand_title {
    color: #f5f0e8;
    font-family: "Georgia", "Segoe UI Variable Display", "Segoe UI";
    font-size: 12.5pt;
    font-weight: 700;
}

QLabel#top_context_brand_subtitle {
    color: #ccbeb1;
    font-size: 9pt;
}

QLabel#global_status_panel_title,
QLabel#top_context_section_title {
    color: #b8a491;
    font-size: 8.2pt;
    font-weight: 700;
    letter-spacing: 0.06em;
}

QLabel#global_status_summary_label {
    color: #87a47c;
    font-size: 7.75pt;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

QLabel[contextRole="value"] {
    color: #f3efe8;
    font-size: 9.35pt;
    font-weight: 600;
}

QLabel[contextRole="caption"],
QLabel[statusRole="value"] {
    color: #cac0b4;
    font-size: 8.85pt;
}

/* ── Workspace shell / nav rail ──────────────────────────────────────────── */

QFrame#workspace_shell_frame {
    background: transparent;
}

QFrame#workspace_nav_rail {
    background: #131619;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 15px;
}

QFrame#workspace_nav_brand_panel {
    background: #1a1e22;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 11px;
}

QFrame#workspace_nav_brand_panel[navCollapsed="true"] {
    background: #171b1f;
    border-color: rgba(142, 187, 128, 0.1);
    border-radius: 12px;
}

QWidget#workspace_nav_brand_header,
QWidget#workspace_nav_brand_text_stack {
    background: transparent;
}

QLabel#workspace_nav_brand_icon {
    background: #161a1e;
    border: 1px solid rgba(142, 187, 128, 0.16);
    border-radius: 13px;
}

QFrame#workspace_nav_brand_panel[navCollapsed="true"] QLabel#workspace_nav_brand_icon {
    border-radius: 11px;
    background: #14181b;
}

QLabel#workspace_nav_brand_title {
    color: #f5f2ec;
    font-family: "Georgia", "Segoe UI Variable Display", "Segoe UI";
    font-size: 13.5pt;
    font-weight: 700;
}

QLabel#workspace_nav_brand_version,
QLabel#workspace_nav_section_label {
    color: #b8aa9d;
    font-size: 7.8pt;
}

QLabel#workspace_nav_brand_subtitle {
    color: #d7ccc1;
    font-size: 8.8pt;
    font-weight: 500;
}

QLabel#workspace_nav_brand_version {
    color: #d4c5b6;
    font-size: 8pt;
    font-weight: 600;
}

QPushButton#workspace_nav_toggle_button {
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0px;
    border-radius: 12px;
    background: #171c20;
    border: 1px solid rgba(142, 187, 128, 0.18);
}

QPushButton[buttonRole="nav-toggle"] {
    background: #171c20;
    color: #f1e6d6;
    padding: 0px;
    border-radius: 12px;
    border: 1px solid rgba(142, 187, 128, 0.18);
}

QPushButton[buttonRole="nav-toggle"]:hover {
    background: #1d2529;
    border-color: rgba(214, 171, 83, 0.28);
}

QPushButton[buttonRole="nav-toggle"]:pressed {
    background: #222b24;
    border-color: rgba(142, 187, 128, 0.32);
}

QPushButton#workspace_nav_toggle_button:hover {
    background: #1d2529;
    border-color: rgba(214, 171, 83, 0.28);
}

QPushButton#workspace_nav_toggle_button:pressed {
    background: #222b24;
    border-color: rgba(142, 187, 128, 0.32);
}

/* Section divider labels in the nav rail */
QLabel#workspace_nav_section_label {
    color: #6e6660;
    font-size: 6.8pt;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

/* ── Nav rail workspace buttons ──────────────────────────────────────────── */

QPushButton[navRole="workspace"] {
    min-height: 0px;
    padding: 6px 11px;
    border: 1px solid transparent;
    border-left: 2px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: #c4b3a3;
    text-align: left;
    font-size: 9pt;
    font-weight: 600;
}

QPushButton[navRole="workspace"][navCollapsed="true"] {
    padding: 5px;
    border-left-width: 1px;
    text-align: center;
    border-radius: 10px;
}

QPushButton[navRole="workspace"]:hover {
    background: #1a2025;
    border-color: rgba(142, 187, 128, 0.14);
    border-left-color: rgba(142, 187, 128, 0.3);
    color: #ede3d6;
}

QPushButton[navRole="workspace"]:checked {
    background: #1e3028;
    border-color: rgba(142, 187, 128, 0.22);
    border-left-color: #8ebb80;
    color: #ecf5e8;
    font-weight: 700;
}

/* ── Workspace tab widget (hidden tab bar) ───────────────────────────────── */

QTabWidget#workspace_nav_tabs::pane {
    border: none;
    background: #161819;
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
    min-height: 26px;
    padding: 4px 12px;
    margin-right: 5px;
    background: #1b2025;
    color: #c4af99;
    border: 1px solid rgba(220, 212, 200, 0.07);
    border-radius: 8px;
    font-size: 9pt;
    font-weight: 600;
}

QTabBar#mods_workspace_mode_tabbar::tab:hover:!selected {
    background: #222830;
    border-color: rgba(220, 212, 200, 0.11);
    color: #e4d8cb;
}

QTabBar#mods_workspace_mode_tabbar::tab:selected {
    background: #1e3428;
    border-color: rgba(142, 187, 128, 0.24);
    color: #eef5e8;
}

/* ── Inventory / SMAPI controls panel ────────────────────────────────────── */

QFrame#mods_inventory_controls_panel,
QFrame#mods_smapi_controls_panel {
    background: rgba(21, 26, 30, 0.94);
    border: 1px solid rgba(220, 212, 200, 0.08);
    border-radius: 12px;
}

/* ── Buttons (base) ──────────────────────────────────────────────────────── */

QPushButton {
    min-height: 0px;
    padding: 4px 11px;
    border: 1px solid rgba(220, 212, 200, 0.1);
    border-radius: 8px;
    background: #23292f;
    color: #efe9e1;
}

QPushButton:hover {
    background: #2b333a;
    border-color: rgba(220, 212, 200, 0.18);
}

QPushButton:pressed {
    background: #191d21;
    border-color: rgba(220, 212, 200, 0.18);
}

QPushButton:focus {
    border-color: rgba(241, 187, 57, 0.44);
}

QPushButton:disabled {
    background: #181c1f;
    color: #5e5952;
    border-color: rgba(220, 212, 200, 0.03);
}

/* ── Primary button (gold) ───────────────────────────────────────────────── */

QPushButton[buttonRole="primary"] {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #f6cb5c,
        stop: 1 #e8ae28
    );
    color: #2f1e00;
    font-weight: 700;
    padding: 4px 13px;
    border-color: rgba(255, 240, 195, 0.24);
}

QPushButton[buttonRole="primary"]:hover {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #f9d168,
        stop: 1 #ecb835
    );
}

QPushButton[buttonRole="primary"]:pressed {
    background: #d9a220;
    color: #2a1a00;
}

QPushButton[buttonRole="primary"]:disabled {
    background: #23231e;
    color: #78705e;
    border-color: rgba(220, 212, 200, 0.03);
}

/* ── Secondary button (sage green) ──────────────────────────────────────── */

QPushButton[buttonRole="secondary"] {
    background: #3c4d43;
    color: #f4f7f0;
    padding: 4px 11px;
    border-color: rgba(165, 205, 152, 0.46);
    font-weight: 600;
}

QPushButton[buttonRole="secondary"]:hover {
    background: #475749;
    border-color: rgba(188, 225, 172, 0.56);
}

QPushButton[buttonRole="secondary"]:pressed {
    background: #2d3830;
}

QPushButton[buttonRole="secondary"]:disabled {
    background: #232924;
    color: #96a08f;
    border-color: rgba(220, 212, 200, 0.06);
}

/* ── Utility button ──────────────────────────────────────────────────────── */

QPushButton[buttonRole="utility"] {
    background: #3b454e;
    color: #f5efe6;
    padding: 3px 8px;
    font-size: 8.5pt;
    border-color: rgba(220, 212, 200, 0.28);
    font-weight: 600;
}

QPushButton[buttonRole="utility"]:hover {
    background: #424e57;
    border-color: rgba(235, 225, 210, 0.32);
}

QPushButton[buttonRole="utility"]:pressed {
    background: #282f35;
}

QPushButton[buttonRole="utility"]:disabled {
    background: #1e2226;
    color: #91908a;
    border-color: rgba(220, 212, 200, 0.05);
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
    min-height: 0px;
    padding: 3px 9px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="primary"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="primary"] {
    min-height: 0px;
    padding: 4px 11px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="secondary"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="secondary"] {
    min-height: 0px;
    padding: 3px 9px;
}

QWidget#mods_inventory_controls_tab QPushButton[buttonRole="utility"],
QWidget#mods_smapi_controls_tab QPushButton[buttonRole="utility"] {
    min-height: 0px;
    padding: 2px 7px;
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
    background: #161a1e;
    border: 1px solid rgba(220, 212, 200, 0.06);
    border-radius: 10px;
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
    color: #d4cbc1;
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
    min-height: 22px;
    max-height: 26px;
    padding-top: 2px;
    padding-bottom: 2px;
    padding-left: 11px;
    padding-right: 11px;
}

/* ── Danger button ───────────────────────────────────────────────────────── */

QPushButton[buttonRole="danger"] {
    background: #5c2b2e;
    color: #fdd8d8;
    font-weight: 700;
}

QPushButton[buttonRole="danger"]:hover {
    background: #71363a;
}

QPushButton[buttonRole="danger"]:pressed {
    background: #4e2427;
}

QPushButton[buttonRole="danger"]:disabled {
    background: #231f20;
    color: #8a7474;
    border-color: rgba(220, 212, 200, 0.03);
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
    background: #1a1e22;
    border: 1px solid rgba(220, 212, 200, 0.07);
    border-radius: 12px;
}

QGroupBox#packages_review_target_group,
QGroupBox#plan_install_execute_group,
QGroupBox#plan_install_staged_package_group {
    background: #192022;
    border-color: rgba(142, 187, 128, 0.1);
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
    color: #c8bdb1;
    font-size: 9.25pt;
}

/* ── Line edit / combo box / plain text edit ─────────────────────────────── */

QLineEdit,
QComboBox {
    background: #0c0f11;
    border: 1px solid rgba(220, 212, 200, 0.14);
    border-radius: 8px;
    padding: 5px 9px;
    color: #ede8e1;
    selection-background-color: #3b6030;
    font-size: 10.1pt;
}

QPlainTextEdit {
    background: #0c0f11;
    border: 1px solid rgba(220, 212, 200, 0.14);
    border-radius: 8px;
    padding: 5px 9px;
    color: #ede8e1;
    selection-background-color: #3b6030;
    font-family: "Cascadia Mono", "Consolas";
    font-size: 9.15pt;
}

QLineEdit:focus,
QComboBox:focus,
QPlainTextEdit:focus {
    border: 1px solid rgba(246, 190, 57, 0.52);
}

QLineEdit:disabled,
QComboBox:disabled,
QPlainTextEdit:disabled {
    background: #141618;
    color: #858078;
    border-color: rgba(220, 212, 200, 0.06);
}

/* ── Combo box dropdown ──────────────────────────────────────────────────── */

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QComboBox QAbstractItemView {
    background: #1c1e21;
    color: #ede8e1;
    border: 1px solid rgba(155, 142, 134, 0.16);
    selection-background-color: #3b6030;
}

/* ── Table widget ────────────────────────────────────────────────────────── */

QTableView,
QTableWidget {
    background: #161b1f;
    alternate-background-color: #1a1f24;
    gridline-color: transparent;
    border: 1px solid rgba(220, 212, 200, 0.07);
    border-radius: 11px;
    selection-background-color: rgba(80, 120, 65, 0.76);
    selection-color: #f8f4ec;
    outline: 0;
}

QHeaderView {
    background: #1f252b;
    border: none;
}

QHeaderView::section {
    background: #1f252b;
    color: #c2af9d;
    border: none;
    border-bottom: 1px solid rgba(220, 212, 200, 0.1);
    border-right: 1px solid rgba(220, 212, 200, 0.04);
    padding: 7px 10px;
    font-size: 8.15pt;
    font-weight: 700;
    letter-spacing: 0.04em;
}

QTableCornerButton::section {
    background: #1f252b;
    border: none;
    border-bottom: 1px solid rgba(220, 212, 200, 0.1);
    border-right: 1px solid rgba(220, 212, 200, 0.04);
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(220, 212, 200, 0.046);
}

QTableWidget::item:hover {
    background: rgba(255, 255, 255, 0.04);
}

QTableWidget::item:selected {
    background: rgba(80, 120, 65, 0.8);
    color: #f8f4ec;
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

QTableWidget::item:selected:hover {
    background: rgba(92, 135, 76, 0.86);
}

QListWidget {
    background: #161b1f;
    alternate-background-color: #1a1f24;
    border: 1px solid rgba(220, 212, 200, 0.07);
    border-radius: 11px;
    color: #ede8e0;
    selection-background-color: rgba(80, 120, 65, 0.76);
    selection-color: #f8f4ec;
    outline: 0;
}

QListWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(220, 212, 200, 0.046);
}

QListWidget::item:hover {
    background: rgba(255, 255, 255, 0.04);
}

QListWidget::item:selected {
    background: rgba(80, 120, 65, 0.8);
    color: #f8f4ec;
}

QListWidget::item:selected:hover {
    background: rgba(92, 135, 76, 0.86);
}

QListWidget#packages_intake_queue_list {
    background: #151a1e;
    border-radius: 12px;
}

/* ── Scroll area (generic) ───────────────────────────────────────────────── */

QScrollArea {
    border: none;
    background: transparent;
}

QAbstractScrollArea::corner {
    background: #1f252b;
    border: none;
}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */

QScrollBar:vertical {
    background: transparent;
    width: 11px;
    margin: 3px;
}

QScrollBar::handle:vertical {
    background: #363c40;
    min-height: 28px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #44494d;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar:horizontal,
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
    border-radius: 4px;
    border: 1px solid rgba(155, 142, 134, 0.32);
    background: #0e1012;
}

QCheckBox::indicator:checked {
    background: #2d4e26;
    border-color: #8ebb80;
}

/* ── Splitter ────────────────────────────────────────────────────────────── */

QSplitter::handle {
    background: #171a1e;
}

/* ── Compact hint label ──────────────────────────────────────────────────── */

QLabel#compact_hint_label {
    color: #b9ada1;
    font-size: 9pt;
}
"""
