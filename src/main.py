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
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSplitter, QStatusBar, QMessageBox, QFileDialog,
    QToolBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction

from audio_tag_writer.constants import APP_NAME, APP_VERSION, APP_TIMESTAMP, APP_ORGANIZATION, AUDIO_EXTENSIONS
from audio_tag_writer.config import config, SingleInstanceChecker
from audio_tag_writer.platform import set_app_user_model_id, set_windows_taskbar_icon
from audio_tag_writer.mutagen_utils import check_mutagen_available, AudioFileError
from audio_tag_writer.metadata import MetadataManager
from audio_tag_writer.audio_utils import get_audio_info
from audio_tag_writer.widgets import AudioPanel, MetadataPanel


def _get_icon_path():
    base = (sys._MEIPASS if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for name in ("ICON_atw.ico", "ICON_atw.png"):
        candidate = os.path.join(base, "assets", name)
        if os.path.exists(candidate):
            return candidate
    return None


_AUDIO_FILTER = (
    "Audio Files (*.mp3 *.wav *.ogg *.flac);;"
    "MP3 Files (*.mp3);;"
    "WAV Files (*.wav);;"
    "OGG Files (*.ogg);;"
    "FLAC Files (*.flac);;"
    "All Files (*)"
)


class MainWindow(QMainWindow):
    """
    Main application window — Phase 2.
    Splitter layout: MetadataPanel (left) | AudioPanel (right).
    Mixins (navigation, file_ops, theme, help, updates) wired in later phases.
    """

    def __init__(self):
        super().__init__()
        self.metadata_manager = MetadataManager()
        self._setup_ui()
        self._restore_last_file()
        logger.info("Main window initialised")

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

        self._build_menu_bar()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

    def _build_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        open_action = QAction("Open", self)
        open_action.setToolTip("Open an audio file  (Ctrl+O)")
        open_action.triggered.connect(self.on_open_file)
        tb.addAction(open_action)

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
    # File operations
    # ------------------------------------------------------------------

    def on_open_file(self):
        """Show open-file dialog and load the selected file."""
        start_dir = config.last_directory or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", start_dir, _AUDIO_FILTER
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        """Load audio info and metadata for the given file path."""
        if not os.path.isfile(path):
            logger.error(f"load_file: not a file: {path}")
            return

        config.selected_file = path
        config.last_directory = os.path.dirname(path)
        config.add_recent_file(path)

        filename = os.path.basename(path)
        self.set_status(f"Loading {filename}…")
        self.setWindowTitle(f"{APP_NAME}  —  {filename}  v{APP_VERSION}")

        # Audio stream info
        info = get_audio_info(path)

        # Metadata
        ok = self.metadata_manager.load_from_file(path)
        self.metadata_panel.update_from_manager()

        # Right panel (art + info)
        try:
            from audio_tag_writer.mutagen_utils import open_audio
            audio = open_audio(path)
            tags = audio.tags
        except AudioFileError:
            tags = None

        self.audio_panel.display_audio(path, info, tags)

        if ok:
            self.set_status(f"Loaded  {filename}")
        else:
            self.set_status(f"Loaded  {filename}  (no metadata tags found)")

        logger.info(f"Loaded file: {path}")

    def _restore_last_file(self):
        """Re-open the last used file on startup if it still exists."""
        if config.selected_file and os.path.exists(config.selected_file):
            self.load_file(config.selected_file)

    # ------------------------------------------------------------------
    # Status bar helper
    # ------------------------------------------------------------------

    def set_status(self, message: str):
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Arrow-key navigation (wired to prev/next in Phase 4)
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            if hasattr(self, 'on_previous'):
                self.on_previous()
        elif event.key() == Qt.Key.Key_Right:
            if hasattr(self, 'on_next'):
                self.on_next()
        else:
            super().keyPressEvent(event)


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
