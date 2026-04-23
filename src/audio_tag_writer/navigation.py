"""
Audio Tag Writer - NavigationMixin: open, prev/next, load_file, recent menus.
"""

import os
import logging

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from .config import config
from .file_utils import get_audio_files
from .constants import APP_NAME, APP_VERSION, AUDIO_EXTENSIONS
from .mutagen_utils import open_audio, detect_mode, AudioFileError
from .audio_utils import get_audio_info

logger = logging.getLogger(__name__)

_AUDIO_FILTER = (
    "Audio Files (*.mp3 *.wav *.ogg *.flac);;"
    "MP3 Files (*.mp3);;"
    "WAV Files (*.wav);;"
    "OGG Files (*.ogg);;"
    "FLAC Files (*.flac);;"
    "All Files (*)"
)


class NavigationMixin:
    """Mixin providing file open, prev/next navigation, and recent file/dir menus."""

    # ------------------------------------------------------------------
    # Open
    # ------------------------------------------------------------------

    def on_open(self):
        """Show open-file dialog and load the selected file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File",
            config.last_directory or os.path.expanduser("~"),
            _AUDIO_FILTER,
        )
        if path:
            self.load_file(path)

    def on_open_directory(self):
        """Prompt for a directory and load the first audio file found in it."""
        directory = QFileDialog.getExistingDirectory(
            self, "Open Directory",
            config.last_directory or os.path.expanduser("~"),
        )
        if directory:
            self.open_directory(directory)

    def open_directory(self, directory: str):
        """Open the first audio file in a directory."""
        if not os.path.isdir(directory):
            QMessageBox.warning(self, "Directory Not Found",
                                f"Directory not found:\n{directory}")
            return
        audio_files = get_audio_files(directory)
        if not audio_files:
            QMessageBox.information(self, "No Audio Files",
                                    f"No audio files found in:\n{directory}")
            return
        self.load_file(audio_files[0])

    # ------------------------------------------------------------------
    # Prev / Next
    # ------------------------------------------------------------------

    def on_previous(self):
        """Navigate to the previous audio file in the directory (with looping)."""
        if not config.directory_audio_files:
            self.set_status("No audio files in directory")
            return
        if config.current_file_index <= 0:
            config.current_file_index = len(config.directory_audio_files) - 1
        else:
            config.current_file_index -= 1
        self.load_file(config.directory_audio_files[config.current_file_index])

    def on_next(self):
        """Navigate to the next audio file in the directory (with looping)."""
        if not config.directory_audio_files:
            self.set_status("No audio files in directory")
            return
        if config.current_file_index >= len(config.directory_audio_files) - 1:
            config.current_file_index = 0
        else:
            config.current_file_index += 1
        self.load_file(config.directory_audio_files[config.current_file_index])

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _auto_detect_mode(self, tags) -> bool:
        """Switch mode based on tag content if auto-detect is enabled. Returns True if switched."""
        if not config.auto_detect_mode:
            return False
        detected = detect_mode(tags, config.mode_detect_frames, config.mode_detect_default)
        if detected == config.get_active_mode() or detected not in config.modes:
            return False
        config.set_active_mode(detected)
        self.metadata_manager.reload_mode(detected)
        self.metadata_panel.rebuild_fields()
        if hasattr(self, 'mode_combo'):
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentText(detected)
            self.mode_combo.blockSignals(False)
        return True

    def load_file(self, path: str):
        """Load an audio file: update config, scan directory, populate panels."""
        if not os.path.isfile(path):
            QMessageBox.warning(self, "File Not Found",
                                f"File not found:\n{path}")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        filename = os.path.basename(path)
        self.set_status(f"Loading  {filename}…")
        QApplication.processEvents()

        try:
            config.selected_file = path
            config.last_directory = os.path.dirname(path)
            config.add_recent_file(path)

            directory = os.path.dirname(path)
            config.directory_audio_files = get_audio_files(directory)
            try:
                config.current_file_index = config.directory_audio_files.index(path)
            except ValueError:
                config.current_file_index = -1

            config.add_recent_directory(directory)
            self.update_recent_directories_menu()
            self.update_recent_menu()

            # Open audio once — reused for mode detection and the audio panel
            try:
                audio = open_audio(path)
                tags = audio.tags
            except AudioFileError:
                audio = None
                tags = None

            # Auto-detect mode before reading metadata so the right field set is loaded
            self._auto_detect_mode(tags)

            # Audio stream info
            info = get_audio_info(path)

            # Metadata
            ok = self.metadata_manager.load_from_file(path)
            self.metadata_panel.update_from_manager()

            # Audio panel (art + info)
            self.audio_panel.display_audio(path, info, tags)

            # Window title
            self.setWindowTitle(f"{APP_NAME}  —  {filename}  v{APP_VERSION}")

            # Status bar: filename · format · file size
            fmt = info.get('format', '')
            size = info.get('file_size', '')
            idx = config.current_file_index
            total = len(config.directory_audio_files)
            pos = f"  [{idx + 1}/{total}]" if idx >= 0 else ""
            status = f"{filename}  ·  {fmt}  ·  {size}{pos}"
            if not ok:
                status += "  (no tags)"
            self.set_status(status)

            logger.info(f"Loaded: {path}")

        finally:
            QApplication.restoreOverrideCursor()

    # ------------------------------------------------------------------
    # Refresh / Clear
    # ------------------------------------------------------------------

    def on_refresh(self):
        """Reload the current file from disk."""
        if config.selected_file and os.path.isfile(config.selected_file):
            self.load_file(config.selected_file)
        else:
            self.set_status("No file to refresh")

    def on_clear(self):
        """Clear all metadata form fields."""
        self.metadata_manager.clear()
        self.metadata_panel.update_from_manager()
        self.set_status("Fields cleared")

    def on_copy_path(self):
        """Copy the fully qualified file path to the clipboard."""
        if config.selected_file:
            QApplication.clipboard().setText(config.selected_file)
            self.set_status(f"Copied to clipboard:  {config.selected_file}")

    # ------------------------------------------------------------------
    # Recent files menu
    # ------------------------------------------------------------------

    def update_recent_menu(self):
        """Rebuild the File > Recent Files submenu."""
        if not hasattr(self, 'recent_menu'):
            return
        self.recent_menu.clear()
        valid = [f for f in config.recent_files if os.path.isfile(f)]
        if not valid:
            act = QAction("No recent files", self)
            act.setEnabled(False)
            self.recent_menu.addAction(act)
            return
        for i, fp in enumerate(valid):
            act = QAction(f"{i + 1}:  {os.path.basename(fp)}", self)
            act.setToolTip(fp)
            act.triggered.connect(lambda checked=False, p=fp: self.load_file(p))
            self.recent_menu.addAction(act)
        self.recent_menu.addSeparator()
        clear_act = QAction("Clear Recent Files", self)
        clear_act.triggered.connect(self.on_clear_recent)
        self.recent_menu.addAction(clear_act)

    def update_recent_directories_menu(self):
        """Rebuild the File > Recent Directories submenu."""
        if not hasattr(self, 'recent_directories_menu'):
            return
        self.recent_directories_menu.clear()
        valid = [d for d in config.recent_directories if os.path.isdir(d)]
        if not valid:
            act = QAction("No recent directories", self)
            act.setEnabled(False)
            self.recent_directories_menu.addAction(act)
            return
        for i, dp in enumerate(valid):
            act = QAction(f"{i + 1}:  {dp}", self)
            act.triggered.connect(lambda checked=False, p=dp: self.open_directory(p))
            self.recent_directories_menu.addAction(act)
        self.recent_directories_menu.addSeparator()
        clear_act = QAction("Clear Recent Directories", self)
        clear_act.triggered.connect(self.on_clear_recent_directories)
        self.recent_directories_menu.addAction(clear_act)

    def on_clear_recent(self):
        config.recent_files = []
        config.save_config()
        self.update_recent_menu()
        self.set_status("Recent files cleared")

    def on_clear_recent_directories(self):
        config.recent_directories = []
        config.save_config()
        self.update_recent_directories_menu()
        self.set_status("Recent directories cleared")
