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

# Ensure the src/ directory is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QVBoxLayout, QStatusBar, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from audio_tag_writer.constants import APP_NAME, APP_VERSION, APP_TIMESTAMP, APP_ORGANIZATION, AUDIO_EXTENSIONS
from audio_tag_writer.config import config, SingleInstanceChecker
from audio_tag_writer.platform import set_app_user_model_id, set_windows_taskbar_icon
from audio_tag_writer.mutagen_utils import check_mutagen_available, AudioFileError


def _get_icon_path():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for name in ("ICON_atw.ico", "ICON_atw.png"):
        candidate = os.path.join(base, "assets", name)
        if os.path.exists(candidate):
            return candidate
    return None


class MainWindow(QMainWindow):
    """
    Main application window — Phase 1 shell.
    Mixins (menu, navigation, file_ops, theme, help, updates) are wired in later phases.
    """

    def __init__(self):
        super().__init__()
        self._setup_ui()
        logger.info("Main window initialised")

    def _setup_ui(self):
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1100, 680)

        icon_path = _get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        placeholder = QLabel("Audio Tag Writer — Phase 1 scaffold\nOpen an audio file to begin.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self._status_label = QLabel("Ready")
        status_bar.addWidget(self._status_label, 1)
        status_bar.addPermanentWidget(QLabel(f"Ver {APP_VERSION}  ({APP_TIMESTAMP})"))

    def set_status(self, message: str):
        self._status_label.setText(message)


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

    # Mutagen pre-flight check
    try:
        check_mutagen_available()
        logger.info("Mutagen is available")
    except AudioFileError as e:
        app_tmp = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Missing Dependency", str(e))
        return 1

    set_windows_taskbar_icon()

    window = MainWindow()
    window.show()
    window.set_status("Mutagen ready — open an audio file to begin")

    if sys.platform.startswith('win'):
        try:
            set_windows_taskbar_icon(int(window.winId()))
        except Exception as e:
            logger.error(f"Error setting taskbar icon: {e}")

    # Re-open last file if present
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        ext = os.path.splitext(candidate)[1].lower()
        if os.path.isfile(candidate) and ext in AUDIO_EXTENSIONS:
            logger.info(f"File from command line: {candidate}")
            # load_file() wired in Phase 2
    elif config.selected_file and os.path.exists(config.selected_file):
        logger.info(f"Restoring last file: {config.selected_file}")
        # load_file() wired in Phase 2

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
