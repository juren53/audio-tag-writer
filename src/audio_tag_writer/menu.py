"""
Audio Tag Writer - MenuMixin: create_menu_bar() and create_toolbar().
"""

from PyQt6.QtWidgets import QToolBar, QLabel, QComboBox
from PyQt6.QtGui import QAction, QKeySequence

from .config import config


class MenuMixin:
    """Mixin providing the full menu bar and toolbar."""

    def create_menu_bar(self):
        """Build the application menu bar."""
        mb = self.menuBar()

        # ── File ──────────────────────────────────────────────────────
        file_menu = mb.addMenu("&File")

        open_act = QAction("&Open…", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self.on_open)
        file_menu.addAction(open_act)

        open_dir_act = QAction("Open &Directory…", self)
        open_dir_act.triggered.connect(self.on_open_directory)
        file_menu.addAction(open_dir_act)

        file_menu.addSeparator()

        self.recent_menu = file_menu.addMenu("Recent &Files")
        self.recent_directories_menu = file_menu.addMenu("Recent &Directories")
        self.update_recent_menu()
        self.update_recent_directories_menu()

        file_menu.addSeparator()

        save_act = QAction("&Save Metadata", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self.on_save)
        file_menu.addAction(save_act)

        file_menu.addSeparator()

        export_act = QAction("&Export Metadata to JSON…", self)
        export_act.triggered.connect(self.on_export)
        file_menu.addAction(export_act)

        import_act = QAction("&Import Metadata from JSON…", self)
        import_act.triggered.connect(self.on_import)
        file_menu.addAction(import_act)

        file_menu.addSeparator()

        quit_act = QAction("&Quit", self)
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # ── Edit ──────────────────────────────────────────────────────
        edit_menu = mb.addMenu("&Edit")

        clear_act = QAction("&Clear Fields", self)
        clear_act.setShortcut("Ctrl+L")
        clear_act.triggered.connect(self.on_clear)
        edit_menu.addAction(clear_act)

        edit_menu.addSeparator()

        rename_act = QAction("&Rename File…", self)
        rename_act.setShortcut("F2")
        rename_act.triggered.connect(self.on_rename_file)
        edit_menu.addAction(rename_act)

        edit_menu.addSeparator()

        copy_path_act = QAction("Copy &Path to Clipboard", self)
        copy_path_act.setShortcut("Ctrl+Shift+C")
        copy_path_act.triggered.connect(self.on_copy_path)
        edit_menu.addAction(copy_path_act)

        # ── View ──────────────────────────────────────────────────────
        view_menu = mb.addMenu("&View")

        refresh_act = QAction("&Refresh", self)
        refresh_act.setShortcut("F5")
        refresh_act.triggered.connect(self.on_refresh)
        view_menu.addAction(refresh_act)

        view_menu.addSeparator()

        tags_act = QAction("&View All Tags…", self)
        tags_act.setShortcut("Ctrl+T")
        tags_act.triggered.connect(self.on_view_all_tags)
        view_menu.addAction(tags_act)

        view_menu.addSeparator()

        self.dark_mode_action = QAction("Toggle &Dark Mode", self)
        self.dark_mode_action.setShortcut("Ctrl+D")
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(getattr(self, 'dark_mode', False))
        self.dark_mode_action.triggered.connect(self.on_toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

        theme_act = QAction("Select &Theme…", self)
        theme_act.triggered.connect(self.on_select_theme)
        view_menu.addAction(theme_act)

        view_menu.addSeparator()

        zoom_in_act = QAction("Zoom &In", self)
        zoom_in_act.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_act.triggered.connect(lambda: self.zoom_ui(0.1))
        view_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("Zoom &Out", self)
        zoom_out_act.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_act.triggered.connect(lambda: self.zoom_ui(-0.1))
        view_menu.addAction(zoom_out_act)

        zoom_reset_act = QAction("&Reset Zoom", self)
        zoom_reset_act.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_act.triggered.connect(self.reset_zoom)
        view_menu.addAction(zoom_reset_act)

        view_menu.addSeparator()

        self.auto_detect_action = QAction("&Auto-detect Mode on Load", self)
        self.auto_detect_action.setCheckable(True)
        self.auto_detect_action.setChecked(config.auto_detect_mode)
        self.auto_detect_action.setToolTip(
            "Automatically switch the metadata mode when opening a file"
        )
        self.auto_detect_action.triggered.connect(self.on_toggle_auto_detect)
        view_menu.addAction(self.auto_detect_action)

        # ── Tools ─────────────────────────────────────────────────────
        tools_menu = mb.addMenu("&Tools")

        manage_modes_act = QAction("&Manage Modes…", self)
        manage_modes_act.setToolTip("Add, rename, reorder or delete metadata modes")
        manage_modes_act.triggered.connect(self.on_manage_modes)
        tools_menu.addAction(manage_modes_act)

        # ── Help ──────────────────────────────────────────────────────
        help_menu = mb.addMenu("&Help")

        readme_act = QAction("&README…", self)
        readme_act.triggered.connect(self.on_readme)
        help_menu.addAction(readme_act)

        changelog_act = QAction("&Changelog…", self)
        changelog_act.triggered.connect(self.on_changelog)
        help_menu.addAction(changelog_act)

        issue_log_act = QAction("&Issue Log…", self)
        issue_log_act.setToolTip("Open the GitHub issue tracker in your browser")
        issue_log_act.triggered.connect(self.on_issue_log)
        help_menu.addAction(issue_log_act)

        help_menu.addSeparator()

        about_act = QAction("&About…", self)
        about_act.triggered.connect(self.on_about)
        help_menu.addAction(about_act)

    def create_toolbar(self):
        """Build the application toolbar."""
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        prev_act = QAction("◀  Prev", self)
        prev_act.setToolTip("Previous file in directory  (↑)")
        prev_act.triggered.connect(self.on_previous)
        tb.addAction(prev_act)

        open_act = QAction("Open", self)
        open_act.setToolTip("Open audio file  (Ctrl+O)")
        open_act.triggered.connect(self.on_open)
        tb.addAction(open_act)

        next_act = QAction("Next  ▶", self)
        next_act.setToolTip("Next file in directory  (↓)")
        next_act.triggered.connect(self.on_next)
        tb.addAction(next_act)

        tb.addSeparator()

        save_act = QAction("Save", self)
        save_act.setToolTip("Save metadata to file  (Ctrl+S)")
        save_act.triggered.connect(self.on_save)
        tb.addAction(save_act)

        tb.addSeparator()

        export_act = QAction("Export JSON", self)
        export_act.setToolTip("Export metadata to JSON")
        export_act.triggered.connect(self.on_export)
        tb.addAction(export_act)

        import_act = QAction("Import JSON", self)
        import_act.setToolTip("Import metadata from JSON")
        import_act.triggered.connect(self.on_import)
        tb.addAction(import_act)

        tb.addSeparator()

        tags_act = QAction("View Tags", self)
        tags_act.setToolTip("View all raw ID3 tags  (Ctrl+T)")
        tags_act.triggered.connect(self.on_view_all_tags)
        tb.addAction(tags_act)

        tb.addSeparator()

        tb.addWidget(QLabel("  Mode: "))
        self.mode_combo = QComboBox()
        self.mode_combo.setToolTip("Switch metadata field set")
        self.mode_combo.setMinimumWidth(160)
        self.mode_combo.addItems(list(config.modes.keys()))
        self.mode_combo.setCurrentText(config.get_active_mode())
        self.mode_combo.currentTextChanged.connect(self.on_switch_mode)
        tb.addWidget(self.mode_combo)

        tb.addSeparator()

        zoom_out_btn = QAction("−", self)
        zoom_out_btn.setToolTip("Zoom out  (Ctrl+−)")
        zoom_out_btn.triggered.connect(lambda: self.zoom_ui(-0.1))
        tb.addAction(zoom_out_btn)

        self.zoom_label = QLabel("  100%")
        self.zoom_label.setMinimumWidth(44)
        tb.addWidget(self.zoom_label)

        zoom_in_btn = QAction("+", self)
        zoom_in_btn.setToolTip("Zoom in  (Ctrl++)")
        zoom_in_btn.triggered.connect(lambda: self.zoom_ui(0.1))
        tb.addAction(zoom_in_btn)

        tb.addSeparator()

        self._toolbar_file_label = QLabel("  No file loaded")
        tb.addWidget(self._toolbar_file_label)

    def _update_toolbar_label(self, text: str):
        """Update the filename label in the toolbar."""
        if hasattr(self, '_toolbar_file_label'):
            self._toolbar_file_label.setText(f"  {text}")
