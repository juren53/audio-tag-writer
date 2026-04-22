"""
Audio Tag Writer - Main application entry point.
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout,
    QLabel, QSplitter, QStatusBar, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from audio_tag_writer.constants import APP_NAME, APP_VERSION, APP_TIMESTAMP, APP_ORGANIZATION, AUDIO_EXTENSIONS
from audio_tag_writer.config import config, SingleInstanceChecker
from audio_tag_writer.platform import set_app_user_model_id, set_windows_taskbar_icon
from audio_tag_writer.mutagen_utils import check_mutagen_available, AudioFileError
from audio_tag_writer.metadata import MetadataManager
from audio_tag_writer.widgets import AudioPanel, MetadataPanel
from audio_tag_writer.file_ops import FileOpsMixin
from audio_tag_writer.navigation import NavigationMixin
from audio_tag_writer.window import WindowMixin
from audio_tag_writer.menu import MenuMixin


def _get_icon_path():
    base = (sys._MEIPASS if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for name in ("ICON_atw.ico", "ICON_atw.png"):
        candidate = os.path.join(base, "assets", name)
        if os.path.exists(candidate):
            return candidate
    return None


class MainWindow(NavigationMixin, FileOpsMixin, MenuMixin, WindowMixin, QMainWindow):
    """
    Main application window — Phase 4.
    Splitter layout: MetadataPanel (left) | AudioPanel (right).
    Mixin chain: NavigationMixin → FileOpsMixin → MenuMixin → WindowMixin → QMainWindow
    """

    def __init__(self):
        super().__init__()
        self._is_closing = False
        self.metadata_manager = MetadataManager()
        self._setup_ui()
        self.restore_window_geometry()
        self._restore_last_file()
        logger.info("Main window initialised (Phase 4)")

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1100, 680)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        icon_path = _get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.create_menu_bar()
        self.create_toolbar()
        self._build_central()
        self._build_status_bar()

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.metadata_panel = MetadataPanel(self.metadata_manager)
        splitter.addWidget(self.metadata_panel)

        self.audio_panel = AudioPanel()
        splitter.addWidget(self.audio_panel)

        splitter.setSizes([660, 440])
        layout.addWidget(splitter)

    def _build_status_bar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Ready")
        sb.addWidget(self._status_label, 1)
        sb.addPermanentWidget(QLabel(f"Ver {APP_VERSION}  ({APP_TIMESTAMP})"))

    # ------------------------------------------------------------------
    # Status bar helper (used by all mixins)
    # ------------------------------------------------------------------

    def set_status(self, message: str):
        self._status_label.setText(message)
        self._update_toolbar_label(message)

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def _restore_last_file(self):
        """Re-open the last used file on startup if it still exists."""
        if config.selected_file and os.path.isfile(config.selected_file):
            self.load_file(config.selected_file)

    # ------------------------------------------------------------------
    # Help stubs (Phase 5 will wire these to help.py)
    # ------------------------------------------------------------------

    def on_about(self):
        from audio_tag_writer.constants import APP_VERSION, APP_TIMESTAMP
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<b>{APP_NAME}</b>  v{APP_VERSION}<br>"
            f"<br>"
            f"ID3 metadata editor for audio files.<br>"
            f"Built with PyQt6 + Mutagen.<br>"
            f"<br>"
            f"<small>{APP_TIMESTAMP}</small>"
        )

    def on_changelog(self):
        changelog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "CHANGELOG.md"
        )
        if os.path.isfile(changelog_path):
            from PyQt6.QtWidgets import QDialog, QTextEdit, QPushButton, QVBoxLayout
            dlg = QDialog(self)
            dlg.setWindowTitle("Changelog")
            dlg.resize(700, 500)
            layout = QVBoxLayout(dlg)
            text = QTextEdit()
            text.setReadOnly(True)
            with open(changelog_path, encoding='utf-8') as f:
                text.setPlainText(f.read())
            layout.addWidget(text)
            btn = QPushButton("Close")
            btn.clicked.connect(dlg.accept)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
            dlg.exec()
        else:
            QMessageBox.information(self, "Changelog", "CHANGELOG.md not found.")


# ------------------------------------------------------------------
# Application entry point
# ------------------------------------------------------------------

def main():
    set_app_user_model_id()

    instance_checker = SingleInstanceChecker("audio-tag-writer")
    if instance_checker.is_already_running():
        app = QApplication(sys.argv)
        QMessageBox.warning(
            None,
            "Audio Tag Writer Already Running",
            "Another instance of Audio Tag Writer is already running.\n\n"
            "Please use the existing instance or close it first.",
            QMessageBox.StandardButton.Ok,
        )
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)

    icon_path = _get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    try:
        check_mutagen_available()
        logger.info("Mutagen is available")
    except AudioFileError as e:
        QMessageBox.critical(None, "Missing Dependency", str(e))
        return 1

    set_windows_taskbar_icon()

    # Handle command-line file argument
    cli_file = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if (os.path.isfile(candidate)
                and os.path.splitext(candidate)[1].lower() in AUDIO_EXTENSIONS):
            cli_file = os.path.abspath(candidate)

    window = MainWindow()
    window.show()

    if sys.platform.startswith('win'):
        try:
            set_windows_taskbar_icon(int(window.winId()))
        except Exception as e:
            logger.error(f"Error setting taskbar icon: {e}")

    if cli_file:
        window.load_file(cli_file)

    try:
        exit_code = app.exec()
        instance_checker.release()
        return exit_code
    except KeyboardInterrupt:
        instance_checker.release()
        app.quit()
        return 0
    finally:
        instance_checker.release()


if __name__ == "__main__":
    sys.exit(main())
