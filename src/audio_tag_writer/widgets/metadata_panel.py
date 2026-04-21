"""
Audio Tag Writer - MetadataPanel widget (dynamic ID3 form).
"""

import logging
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFormLayout, QScrollArea, QSizePolicy, QMainWindow, QMessageBox
)
from PyQt6.QtCore import Qt

from ..config import config

logger = logging.getLogger(__name__)


class MetadataPanel(QWidget):
    """
    Form panel for displaying and editing ID3 metadata fields.
    Fields are built dynamically from the active mode's field spec.
    """

    def __init__(self, metadata_manager, parent=None):
        super().__init__(parent)
        self.metadata_manager = metadata_manager
        self._field_widgets = {}    # label -> QLineEdit | QTextEdit
        self._char_labels = {}      # label -> QLabel (for text widgets)
        self._all_text_fields = []  # all input widgets (for event filter)
        self._setup_ui()
        self._install_event_filters()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        for spec in self.metadata_manager.get_field_specs():
            label_text = spec['label']
            widget_type = spec.get('widget', 'line')
            max_chars = spec.get('max_chars', 2000)

            if widget_type == 'text':
                container, widget, char_label = self._make_text_widget(label_text, max_chars)
                self._char_labels[label_text] = char_label
                form.addRow(f"{label_text}:", container)
            else:
                widget = QLineEdit()
                form.addRow(f"{label_text}:", widget)

            self._field_widgets[label_text] = widget
            self._all_text_fields.append(widget)

        # Wrap in scroll area
        form_widget = QWidget()
        form_widget.setLayout(form)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        outer.addWidget(scroll, 1)

        # Write Metadata button
        self.write_button = QPushButton("Write Metadata")
        self.write_button.clicked.connect(self._on_write)
        outer.addWidget(self.write_button, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _make_text_widget(self, label, max_chars):
        """Build a QTextEdit with a character-count label below it."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        widget = QTextEdit()
        widget.setMinimumHeight(80)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(widget)

        char_label = QLabel(f"0/{max_chars} characters")
        char_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        char_label.setStyleSheet("font-size: 8pt;")
        layout.addWidget(char_label)

        widget.textChanged.connect(
            lambda lbl=label, mc=max_chars: self._update_char_count(lbl, mc)
        )
        return container, widget, char_label

    def _install_event_filters(self):
        for w in self._all_text_fields:
            w.installEventFilter(self)

    def eventFilter(self, watched, event):
        """Prevent Up/Down arrow keys from propagating to the main window."""
        if (event.type() == event.Type.KeyPress
                and watched in self._all_text_fields
                and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down)):
            event.accept()
            watched.event(event)
            return True
        return super().eventFilter(watched, event)

    # ------------------------------------------------------------------
    # Data sync
    # ------------------------------------------------------------------

    def update_from_manager(self):
        """Populate all form fields from the metadata manager."""
        for spec in self.metadata_manager.get_field_specs():
            label = spec['label']
            widget = self._field_widgets.get(label)
            if widget is None:
                continue
            value = self.metadata_manager.get_field(label)
            if isinstance(widget, QTextEdit):
                widget.blockSignals(True)
                widget.setPlainText(value)
                widget.blockSignals(False)
                self._update_char_count(label, spec.get('max_chars', 2000))
            else:
                widget.setText(value)

    def update_manager_from_ui(self):
        """Push all form field values back into the metadata manager."""
        for spec in self.metadata_manager.get_field_specs():
            label = spec['label']
            widget = self._field_widgets.get(label)
            if widget is None:
                continue
            value = (widget.toPlainText() if isinstance(widget, QTextEdit)
                     else widget.text())
            self.metadata_manager.set_field(label, value)

    def clear_fields(self):
        """Clear all form fields."""
        for widget in self._field_widgets.values():
            if isinstance(widget, QTextEdit):
                widget.clear()
            else:
                widget.clear()
        for label_text, char_label in self._char_labels.items():
            spec = next(
                (s for s in self.metadata_manager.get_field_specs()
                 if s['label'] == label_text), {}
            )
            max_chars = spec.get('max_chars', 2000)
            char_label.setText(f"0/{max_chars} characters")
            char_label.setStyleSheet("font-size: 8pt;")

    # ------------------------------------------------------------------
    # Character counting
    # ------------------------------------------------------------------

    def _update_char_count(self, label, max_chars):
        char_label = self._char_labels.get(label)
        widget = self._field_widgets.get(label)
        if not char_label or not isinstance(widget, QTextEdit):
            return

        text = widget.toPlainText()
        count = len(text)

        if count > max_chars:
            widget.blockSignals(True)
            widget.setPlainText(text[:max_chars])
            widget.blockSignals(False)
            count = max_chars

        char_label.setText(f"{count}/{max_chars} characters")

        if count >= max_chars:
            char_label.setStyleSheet("font-size: 8pt; color: red;")
        elif count > max_chars * 0.8:
            char_label.setStyleSheet("font-size: 8pt; color: #FF9900;")
        else:
            char_label.setStyleSheet("font-size: 8pt;")

    # ------------------------------------------------------------------
    # Write button (save logic added in Phase 3)
    # ------------------------------------------------------------------

    def _on_write(self):
        if not config.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please open an audio file first.")
            return

        self.update_manager_from_ui()

        from ..mutagen_utils import AudioFileError
        try:
            ok = self.metadata_manager.save_to_file(config.selected_file)
        except AudioFileError as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred:\n{e}")
            return

        if ok:
            self._set_main_status(
                f"Metadata saved  —  {os.path.basename(config.selected_file)}"
            )

    def _set_main_status(self, message: str):
        parent = self.parent()
        while parent and not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if parent and hasattr(parent, 'set_status'):
            parent.set_status(message)
