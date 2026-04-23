"""
Audio Tag Writer - ThemeMixin: apply_theme, zoom_ui, dark mode toggle.
"""

import logging

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout,
    QListWidget, QDialogButtonBox, QLabel,
)
from PyQt6.QtCore import Qt

from .config import config

logger = logging.getLogger(__name__)


class ThemeMixin:
    """Mixin providing theme application, UI zoom, and dark mode toggle."""

    def apply_comprehensive_theme(self):
        """Apply the full QSS theme to the application."""
        try:
            stylesheet = self.theme_manager.generate_stylesheet(self.current_theme)
            if config.ui_zoom_factor != 1.0:
                # Preserve any existing zoom CSS appended after the theme
                zoom_css = getattr(self, '_zoom_css', '')
                QApplication.instance().setStyleSheet(stylesheet + zoom_css)
            else:
                QApplication.instance().setStyleSheet(stylesheet)
            self.set_status(f"Theme: {self.current_theme}")
            logger.info(f"Applied theme: {self.current_theme}")
        except Exception as e:
            logger.error(f"Error applying theme: {e}")

    def on_toggle_dark_mode(self):
        """Toggle between Default Light and Dark themes."""
        if self.theme_manager.is_dark_theme(self.current_theme):
            new_theme = 'Default Light'
        else:
            new_theme = 'Dark'

        self.current_theme = new_theme
        self.theme_manager.current_theme = new_theme
        self.dark_mode = self.theme_manager.is_dark_theme(new_theme)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.apply_comprehensive_theme()

        config.current_theme = new_theme
        config.dark_mode = self.dark_mode
        config.save_config()

    def on_select_theme(self):
        """Open an inline theme picker dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Theme")
        dialog.resize(260, 320)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Choose a theme:"))

        lst = QListWidget()
        for name in self.theme_manager.get_theme_names():
            lst.addItem(name)
        matches = lst.findItems(self.current_theme, Qt.MatchFlag.MatchExactly)
        if matches:
            lst.setCurrentItem(matches[0])
        lst.itemDoubleClicked.connect(lambda _: dialog.accept())
        layout.addWidget(lst)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted and lst.currentItem():
            selected = lst.currentItem().text()
            if selected != self.current_theme:
                self.current_theme = selected
                self.theme_manager.current_theme = selected
                self.dark_mode = self.theme_manager.is_dark_theme(selected)
                self.dark_mode_action.setChecked(self.dark_mode)
                self.apply_comprehensive_theme()
                config.current_theme = selected
                config.dark_mode = self.dark_mode
                config.save_config()

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def zoom_ui(self, delta: float):
        """Change UI zoom by delta (e.g. +0.1 or -0.1)."""
        new_zoom = round(self.ui_scale_factor + delta, 1)
        if new_zoom > 1.5:
            self.set_status("Maximum zoom reached (150%)")
            return
        if new_zoom < 0.5:
            self.set_status("Minimum zoom reached (50%)")
            return
        self.ui_scale_factor = new_zoom
        self._apply_ui_zoom()
        config.ui_zoom_factor = new_zoom
        config.save_config()

    def reset_zoom(self):
        """Reset UI zoom to 100%."""
        self.ui_scale_factor = 1.0
        self._apply_ui_zoom()
        config.ui_zoom_factor = 1.0
        config.save_config()

    def _apply_ui_zoom(self):
        """Apply current zoom factor to the application stylesheet."""
        pct = int(self.ui_scale_factor * 100)
        if hasattr(self, 'zoom_label'):
            self.zoom_label.setText(f"  {pct}%")
        self.set_status(f"Zoom: {pct}%")

        base_pt = 9.0
        pt = base_pt * self.ui_scale_factor

        zoom_css = f"""
        /* ZOOM_STYLES_START */
        QWidget {{ font-size: {pt:.1f}pt; }}
        QPushButton {{
            font-size: {pt:.1f}pt;
            padding: {int(6 * self.ui_scale_factor)}px {int(12 * self.ui_scale_factor)}px;
            min-width: {int(80 * self.ui_scale_factor)}px;
        }}
        QLabel {{ font-size: {pt:.1f}pt; }}
        QLineEdit {{ font-size: {pt:.1f}pt; padding: {int(4 * self.ui_scale_factor)}px; }}
        QTextEdit {{ font-size: {pt:.1f}pt; }}
        QComboBox {{
            font-size: {pt:.1f}pt;
            padding: {int(4 * self.ui_scale_factor)}px {int(8 * self.ui_scale_factor)}px;
        }}
        QMenuBar {{ font-size: {pt:.1f}pt; }}
        QMenu {{ font-size: {pt:.1f}pt; }}
        QStatusBar {{ font-size: {pt:.1f}pt; }}
        /* ZOOM_STYLES_END */
        """
        self._zoom_css = zoom_css

        base_stylesheet = self.theme_manager.generate_stylesheet(self.current_theme)
        QApplication.instance().setStyleSheet(base_stylesheet + zoom_css)

        logger.debug(f"Zoom set to {pct}% ({pt:.1f}pt)")
