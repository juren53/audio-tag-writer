"""
Audio Tag Writer - AudioPanel widget (album art + file info).
"""

import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

logger = logging.getLogger(__name__)

_ART_SIZE = 220   # max px for album art display


class AudioPanel(QWidget):
    """
    Right-column panel showing album art (APIC frame) and audio file info.
    Mirrors the ImageViewer panel in tag-writer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
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
        self._update_art(tags)
        self._update_info(info_dict)

    def clear(self):
        """Reset panel to empty/placeholder state."""
        self._show_placeholder_art()
        self._status_label.setText("○  No file loaded")
        self._status_label.setStyleSheet("font-size: 8pt; color: grey;")
        self._info_label.setText(self._build_info_html({}))

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
        else:
            self._show_placeholder_art()
            self._status_label.setText("○  No album art")
            self._status_label.setStyleSheet("font-size: 8pt; color: grey;")

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

        filename = info.get('filename', '--')
        return (
            f"<b>{filename}</b>"
            f"<table style='margin-top:6px; border-spacing:2px 4px;'>"
            + row('Duration',    'duration')
            + row('Bitrate',     'bitrate')
            + row('Sample Rate', 'sample_rate')
            + row('Channels',    'channels')
            + row('Format',      'format')
            + row('File Size',   'file_size')
            + row('Modified',    'modified')
            + "</table>"
        )
