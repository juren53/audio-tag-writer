"""
Audio Tag Writer - FileOpsMixin: save, export, import, view-all-tags.
"""

import os
import logging

from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QPushButton, QAbstractItemView,
)
from PyQt6.QtCore import Qt

from .config import config
from .mutagen_utils import open_audio, AudioFileError

logger = logging.getLogger(__name__)

_JSON_FILTER = "JSON Files (*.json);;All Files (*)"


class FileOpsMixin:
    """Mixin for MainWindow: save, export/import JSON, view all tags."""

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def on_save(self):
        if not config.selected_file:
            QMessageBox.warning(self, "No File", "Please open an audio file first.")
            return

        self.metadata_panel.update_manager_from_ui()

        try:
            ok = self.metadata_manager.save_to_file(config.selected_file)
        except AudioFileError as e:
            QMessageBox.critical(self, "Save Error", str(e))
            return
        except Exception as e:
            logger.error(f"Unexpected save error: {e}")
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred:\n{e}")
            return

        if ok:
            filename = os.path.basename(config.selected_file)
            self.set_status(f"Saved  {filename}")

    # ------------------------------------------------------------------
    # Export JSON
    # ------------------------------------------------------------------

    def on_export(self):
        if not config.selected_file:
            QMessageBox.warning(self, "No File", "Please open an audio file first.")
            return

        self.metadata_panel.update_manager_from_ui()

        default_name = os.path.splitext(os.path.basename(config.selected_file))[0] + "_metadata.json"
        start_path = os.path.join(config.last_directory or os.path.expanduser("~"), default_name)

        path, _ = QFileDialog.getSaveFileName(self, "Export Metadata as JSON", start_path, _JSON_FILTER)
        if not path:
            return

        if self.metadata_manager.export_to_json(path):
            self.set_status(f"Exported  {os.path.basename(path)}")
        else:
            QMessageBox.critical(self, "Export Error", "Failed to export metadata.")

    # ------------------------------------------------------------------
    # Import JSON
    # ------------------------------------------------------------------

    def on_import(self):
        if not config.selected_file:
            QMessageBox.warning(self, "No File", "Please open an audio file first.")
            return

        start_dir = config.last_directory or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(self, "Import Metadata from JSON", start_dir, _JSON_FILTER)
        if not path:
            return

        if self.metadata_manager.import_from_json(path):
            self.metadata_panel.update_from_manager()
            self.set_status(f"Imported  {os.path.basename(path)}")
        else:
            QMessageBox.critical(self, "Import Error", "Failed to import metadata.")

    # ------------------------------------------------------------------
    # View All Tags
    # ------------------------------------------------------------------

    def on_view_all_tags(self):
        if not config.selected_file:
            QMessageBox.warning(self, "No File", "Please open an audio file first.")
            return

        try:
            audio = open_audio(config.selected_file)
            tags = audio.tags
        except AudioFileError as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        dlg = AllTagsDialog(config.selected_file, tags, parent=self)
        dlg.exec()


class AllTagsDialog(QDialog):
    """Searchable table of all raw Mutagen frames in the open file."""

    def __init__(self, path, tags, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"All Tags — {os.path.basename(path)}")
        self.resize(720, 500)
        self._all_rows = []
        self._setup_ui(tags)

    def _setup_ui(self, tags):
        layout = QVBoxLayout(self)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type to filter frames…")
        self._search.textChanged.connect(self._apply_filter)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        # Table
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Frame ID", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        self._populate(tags)

    def _populate(self, tags):
        if tags is None:
            return

        for frame_id in sorted(tags.keys()):
            try:
                frame = tags[frame_id]
                # Use text attribute if available, otherwise str representation
                if hasattr(frame, 'text'):
                    value = '; '.join(str(t) for t in frame.text)
                elif hasattr(frame, 'people'):
                    value = '; '.join(f"{p[0]}: {p[1]}" if p[0] else p[1] for p in frame.people)
                elif hasattr(frame, 'data'):
                    value = f"<binary data {len(frame.data)} bytes>"
                else:
                    value = str(frame)
            except Exception:
                value = "<unparseable>"

            self._all_rows.append((str(frame_id), value))

        self._render_rows(self._all_rows)

    def _render_rows(self, rows):
        self._table.setRowCount(len(rows))
        for r, (fid, val) in enumerate(rows):
            self._table.setItem(r, 0, QTableWidgetItem(fid))
            self._table.setItem(r, 1, QTableWidgetItem(val))

    def _apply_filter(self, text):
        text = text.lower()
        if not text:
            filtered = self._all_rows
        else:
            filtered = [
                (fid, val) for fid, val in self._all_rows
                if text in fid.lower() or text in val.lower()
            ]
        self._render_rows(filtered)
