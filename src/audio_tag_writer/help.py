"""
Audio Tag Writer - HelpMixin: About and Changelog dialogs.
"""

import os
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt

from .constants import APP_NAME, APP_VERSION, APP_TIMESTAMP

logger = logging.getLogger(__name__)


def _project_root():
    # From src/audio_tag_writer/ go up two levels
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


class HelpMixin:
    """Mixin providing About and Changelog dialogs."""

    def on_about(self):
        """Show About dialog, preferring pyqt_app_info if available."""
        try:
            import mutagen
            mutagen_ver = getattr(mutagen, 'version_string', str(mutagen.version))
        except Exception:
            mutagen_ver = 'unknown'

        try:
            from pyqt_app_info import AppIdentity, gather_info
            from pyqt_app_info.qt import AboutDialog

            identity = AppIdentity(
                name=APP_NAME,
                version=APP_VERSION,
                commit_date=APP_TIMESTAMP,
                description=(
                    "ID3 metadata editor for MP3, WAV, OGG, and FLAC files.\n"
                    f"Mutagen {mutagen_ver}"
                ),
            )
            info = gather_info(identity, caller_file=__file__)
            AboutDialog(info, parent=self).exec()
        except Exception as e:
            logger.debug(f"pyqt_app_info unavailable ({e}), falling back to QMessageBox")
            QMessageBox.about(
                self,
                f"About {APP_NAME}",
                f"<b>{APP_NAME}</b>&nbsp; v{APP_VERSION}<br><br>"
                f"ID3 metadata editor for MP3, WAV, OGG, and FLAC files.<br>"
                f"Built with <b>PyQt6</b> + <b>Mutagen {mutagen_ver}</b>.<br><br>"
                f"<small>{APP_TIMESTAMP}</small>",
            )

    def on_changelog(self):
        """Show CHANGELOG.md in a resizable dialog."""
        changelog_path = os.path.join(_project_root(), "CHANGELOG.md")
        if not os.path.isfile(changelog_path):
            QMessageBox.information(self, "Changelog", "CHANGELOG.md not found.")
            return

        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Changelog")
            dialog.resize(740, 560)
            dialog.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowMinimizeButtonHint |
                Qt.WindowType.WindowMaximizeButtonHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            layout = QVBoxLayout(dialog)

            text = QTextEdit()
            text.setReadOnly(True)
            with open(changelog_path, encoding='utf-8') as f:
                text.setPlainText(f.read())
            layout.addWidget(text)

            btn = QPushButton("Close")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)

            dialog.exec()
        except Exception as e:
            logger.error(f"Error showing changelog: {e}")
            QMessageBox.warning(self, "Changelog", f"Could not open changelog:\n{e}")
