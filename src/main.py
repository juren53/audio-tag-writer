"""
Audio Tag Writer - Main application entry point.
"""

import os
import pathlib
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# IMM setup at module level so _init_win32() fires before QApplication is created.
_IMM_PATH = os.path.expanduser("~/Projects/Icon_Manager_Module")
if os.path.isdir(_IMM_PATH) and _IMM_PATH not in sys.path:
    sys.path.insert(0, _IMM_PATH)

_app_icons = None
try:
    from icon_loader import IconLoader  # side-effect: _init_win32() on Windows
    _app_icons = IconLoader(
        base_path=pathlib.Path(__file__).resolve().parent.parent / "resources" / "icons"
    )
except Exception:
    pass

from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout,
    QLabel, QSplitter, QStatusBar, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from audio_tag_writer.constants import APP_NAME, APP_VERSION, APP_TIMESTAMP, APP_ORGANIZATION, APP_USER_MODEL_ID, AUDIO_EXTENSIONS
from audio_tag_writer.config import config
from audio_tag_writer.single_instance_guard import SingleInstanceGuard
from audio_tag_writer.mutagen_utils import check_mutagen_available, AudioFileError
from audio_tag_writer.metadata import MetadataManager
from audio_tag_writer.widgets import AudioPanel, MetadataPanel
from audio_tag_writer.file_ops import FileOpsMixin
from audio_tag_writer.navigation import NavigationMixin
from audio_tag_writer.window import WindowMixin
from audio_tag_writer.menu import MenuMixin
from audio_tag_writer.theme import DEFAULT_THEME, is_dark_theme
from audio_tag_writer.theme_mixin import ThemeMixin
from audio_tag_writer.help import HelpMixin


def get_app_icon() -> QIcon:
    if _app_icons is not None:
        return _app_icons.app_icon()
    return QIcon()


class MainWindow(NavigationMixin, FileOpsMixin, MenuMixin, ThemeMixin, HelpMixin, WindowMixin, QMainWindow):
    """
    Main application window — Phase 5.
    Splitter layout: MetadataPanel (left) | AudioPanel (right).
    Mixin chain: NavigationMixin → FileOpsMixin → MenuMixin → ThemeMixin → HelpMixin → WindowMixin → QMainWindow
    """

    def __init__(self):
        super().__init__()
        self._is_closing = False
        self.metadata_manager = MetadataManager()

        # Theme / zoom state — must be set before _setup_ui calls create_menu_bar
        self.current_theme = config.current_theme
        self.dark_mode = is_dark_theme(self.current_theme)
        self.ui_scale_factor = config.ui_zoom_factor
        self._zoom_css = ''

        self._setup_ui()
        QApplication.instance().installEventFilter(self)
        self.restore_window_geometry()

        self.apply_theme()
        if self.ui_scale_factor != 1.0:
            self._apply_ui_zoom()

        self._restore_last_file()
        logger.info("Main window initialised (Phase 5)")

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

        self.setWindowIcon(get_app_icon())

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

        self.audio_panel = AudioPanel(self.metadata_manager)
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
# Application entry point
# ------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)

    app.setWindowIcon(get_app_icon())

    # Handle command-line file argument
    cli_file = None
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if (os.path.isfile(candidate)
                and os.path.splitext(candidate)[1].lower() in AUDIO_EXTENSIONS):
            cli_file = os.path.abspath(candidate)

    guard = SingleInstanceGuard(APP_USER_MODEL_ID)
    payload = cli_file.encode("utf-8") if cli_file else b""
    if not guard.try_acquire(payload):
        return 0
    app.aboutToQuit.connect(guard.release)

    try:
        check_mutagen_available()
        logger.info("Mutagen is available")
    except AudioFileError as e:
        QMessageBox.critical(None, "Missing Dependency", str(e))
        return 1

    window = MainWindow()
    guard.connect_window(window, on_payload=window.load_file)
    window.show()

    if _app_icons is not None:
        _app_icons.set_taskbar_icon(window, APP_USER_MODEL_ID)

    if cli_file:
        window.load_file(cli_file)

    try:
        return app.exec()
    except KeyboardInterrupt:
        app.quit()
        return 0


if __name__ == "__main__":
    sys.exit(main())
