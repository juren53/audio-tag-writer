"""
Audio Tag Writer - AudioPanel widget (album art + file info).
"""

import logging
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy,
    QPushButton, QMessageBox, QFileDialog, QMainWindow,
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices

logger = logging.getLogger(__name__)

_ART_SIZE = 220   # max px for album art display

_IMAGE_MIME = {
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png':  'image/png',
    '.gif':  'image/gif',
    '.bmp':  'image/bmp',
    '.webp': 'image/webp',
}


class AudioPanel(QWidget):
    """
    Right-column panel showing album art (APIC frame) and audio file info.
    Mirrors the ImageViewer panel in tag-writer.
    """

    def __init__(self, metadata_manager=None, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._current_path = None
        self._metadata_manager = metadata_manager
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Album art frame
        art_frame = QFrame()
        art_frame.setFrameShape(QFrame.Shape.StyledPanel)
        art_frame.setFrameShadow(QFrame.Shadow.Sunken)
        art_frame.setFixedSize(_ART_SIZE + 4, _ART_SIZE + 4)
        art_layout = QVBoxLayout(art_frame)
        art_layout.setContentsMargins(2, 2, 2, 2)

        self._art_label = QLabel()
        self._art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._art_label.setFixedSize(_ART_SIZE, _ART_SIZE)
        art_layout.addWidget(self._art_label)

        layout.addWidget(art_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Art edit buttons
        art_btn_row = QHBoxLayout()
        art_btn_row.setSpacing(4)

        self._set_art_button = QPushButton("Set Art…")
        self._set_art_button.setToolTip("Load an image file as album art")
        self._set_art_button.setEnabled(False)
        self._set_art_button.clicked.connect(self._on_set_art)
        art_btn_row.addWidget(self._set_art_button)

        self._remove_art_button = QPushButton("Remove Art")
        self._remove_art_button.setToolTip("Remove album art from this file")
        self._remove_art_button.setEnabled(False)
        self._remove_art_button.clicked.connect(self._on_remove_art)
        art_btn_row.addWidget(self._remove_art_button)

        layout.addLayout(art_btn_row)

        # Play button
        self._play_button = QPushButton("▶  Play")
        self._play_button.setToolTip("Open in system audio player")
        self._play_button.setEnabled(False)
        self._play_button.clicked.connect(self._on_play)
        layout.addWidget(self._play_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Status indicator
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 8pt;")
        layout.addWidget(self._status_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # File info — scrollable table
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(4, 4, 4, 4)
        info_layout.setSpacing(2)

        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._info_label.setTextFormat(Qt.TextFormat.RichText)
        info_layout.addWidget(self._info_label)
        info_layout.addStretch()

        scroll.setWidget(info_widget)
        layout.addWidget(scroll, 1)

        self.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_audio(self, path: str, info_dict: dict, tags):
        """Update panel with album art and file info for the loaded file."""
        self._current_path = path
        self._play_button.setEnabled(True)
        self._set_art_button.setEnabled(True)
        self._update_art(tags)
        self._update_info(info_dict)

    def clear(self):
        """Reset panel to empty/placeholder state."""
        self._current_path = None
        self._play_button.setEnabled(False)
        self._set_art_button.setEnabled(False)
        self._remove_art_button.setEnabled(False)
        self._show_placeholder_art()
        self._status_label.setText("○  No file loaded")
        self._status_label.setStyleSheet("font-size: 8pt; color: grey;")
        self._info_label.setText(self._build_info_html({}))

    def _on_play(self):
        """Open the current file in the system default audio player."""
        if not self._current_path or not os.path.isfile(self._current_path):
            return
        url = QUrl.fromLocalFile(self._current_path)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self, "Playback Error",
                f"Could not open the file with the system player:\n{self._current_path}"
            )

    # ------------------------------------------------------------------
    # Album art
    # ------------------------------------------------------------------

    def _update_art(self, tags):
        """Extract APIC frame from tags and display it; fall back to placeholder."""
        pixmap = self._extract_apic(tags)
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                _ART_SIZE, _ART_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._art_label.setPixmap(scaled)
            self._status_label.setText("●  Art embedded")
            self._status_label.setStyleSheet("font-size: 8pt; color: green;")
            self._remove_art_button.setEnabled(True)
        else:
            self._show_placeholder_art()
            self._status_label.setText("○  No album art")
            self._status_label.setStyleSheet("font-size: 8pt; color: grey;")
            self._remove_art_button.setEnabled(False)

    def _extract_apic(self, tags):
        """Return QPixmap from the first APIC frame, or None."""
        if tags is None:
            return None
        try:
            frames = tags.getall('APIC')
            if frames:
                pixmap = QPixmap()
                if pixmap.loadFromData(frames[0].data):
                    return pixmap
        except Exception as e:
            logger.debug(f"APIC extraction failed: {e}")
        return None

    def _show_placeholder_art(self):
        """Show a music-note placeholder when no art is available."""
        self._art_label.clear()
        self._art_label.setText("♪")
        self._art_label.setStyleSheet(
            "font-size: 72pt; color: #aaaaaa; background: #f0f0f0;"
        )

    # ------------------------------------------------------------------
    # Album art edit actions
    # ------------------------------------------------------------------

    def _on_set_art(self):
        if not self._current_path:
            return

        start_dir = os.path.dirname(self._current_path)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Album Art", start_dir,
            "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;All Files (*)"
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        mime_type = _IMAGE_MIME.get(ext, 'image/jpeg')

        try:
            with open(path, 'rb') as f:
                image_data = f.read()
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Could not read image file:\n{e}")
            return

        if self._metadata_manager is None:
            QMessageBox.critical(self, "Error", "No metadata manager available.")
            return

        from ..mutagen_utils import AudioFileError
        try:
            self._metadata_manager.save_apic_to_file(self._current_path, image_data, mime_type)
        except AudioFileError as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred:\n{e}")
            return

        self._refresh_art()
        self._set_main_status(f"Album art updated  —  {os.path.basename(self._current_path)}")

    def _on_remove_art(self):
        if not self._current_path:
            return

        if self._metadata_manager is None:
            QMessageBox.critical(self, "Error", "No metadata manager available.")
            return

        from ..mutagen_utils import AudioFileError
        try:
            self._metadata_manager.remove_apic_from_file(self._current_path)
        except AudioFileError as e:
            QMessageBox.critical(self, "Remove Error", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Remove Error", f"An unexpected error occurred:\n{e}")
            return

        self._refresh_art()
        self._set_main_status(f"Album art removed  —  {os.path.basename(self._current_path)}")

    def _refresh_art(self):
        """Reload tags from the current file and refresh the art display."""
        try:
            from ..mutagen_utils import open_audio
            audio = open_audio(self._current_path)
            self._update_art(audio.tags)
        except Exception:
            self._show_placeholder_art()
            self._remove_art_button.setEnabled(False)

    def _set_main_status(self, message: str):
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if parent and hasattr(parent, 'set_status'):
            parent.set_status(message)

    # ------------------------------------------------------------------
    # File info
    # ------------------------------------------------------------------

    def _update_info(self, info: dict):
        self._info_label.setText(self._build_info_html(info))

    def _build_info_html(self, info: dict) -> str:
        def row(label, key):
            val = info.get(key, '--')
            return (
                f"<tr>"
                f"<td style='font-weight:bold; padding-right:8px; white-space:nowrap;'>{label}:</td>"
                f"<td>{val}</td>"
                f"</tr>"
            )

        def row_if(label, key):
            val = info.get(key, '--')
            if val == '--':
                return ''
            return (
                f"<tr>"
                f"<td style='font-weight:bold; padding-right:8px; white-space:nowrap;'>{label}:</td>"
                f"<td>{val}</td>"
                f"</tr>"
            )

        filename = info.get('filename', '--')
        return (
            f"<b>{filename}</b>"
            f"<table style='margin-top:6px; border-spacing:2px 4px;'>"
            + row('Duration',     'duration')
            + row('Bitrate',      'bitrate')
            + row_if('Bitrate Mode', 'bitrate_mode')
            + row('Sample Rate',  'sample_rate')
            + row('Channels',     'channels')
            + row_if('Stereo Mode',  'stereo_mode')
            + row_if('MPEG Version', 'mpeg_version')
            + row('Format',       'format')
            + row_if('Compression',  'compression')
            + row('File Size',    'file_size')
            + row('Modified',     'modified')
            + "</table>"
        )
