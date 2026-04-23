"""
Audio Tag Writer - FileOpsMixin: save, export, import, view-all-tags.
"""

import os
import logging

import shutil

from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QLabel, QPushButton, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QTimer

from .config import config
from .constants import AUDIO_EXTENSIONS
from .file_utils import backup_file
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
    # Rename File
    # ------------------------------------------------------------------

    def on_rename_file(self):
        """Rename the current audio file in-place with a backup."""
        if not config.selected_file:
            QMessageBox.warning(self, "No File", "Please open an audio file first.")
            return

        current_filename = os.path.basename(config.selected_file)
        current_directory = os.path.dirname(config.selected_file)

        dialog = QDialog(self)
        dialog.setWindowTitle("Rename File")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumWidth(420)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Enter new filename:"))

        line_edit = QLineEdit(current_filename)
        line_edit.selectAll()
        layout.addWidget(line_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Temporarily suspend the app-level event filter so arrow keys work in the line edit
        QApplication.instance().removeEventFilter(self)

        dialog_shown = False
        original_show_event = dialog.showEvent

        def showEvent(event):
            nonlocal dialog_shown
            original_show_event(event)
            if not dialog_shown:
                dialog_shown = True
                QTimer.singleShot(50, lambda: line_edit.setFocus())
                QTimer.singleShot(100, lambda: line_edit.selectAll())

        dialog.showEvent = showEvent

        def keyPressEvent(event):
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right,
                               Qt.Key.Key_Up, Qt.Key.Key_Down):
                line_edit.setFocus()
                line_edit.keyPressEvent(event)
                event.accept()
                return
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                dialog.accept()
                event.accept()
                return
            if event.key() == Qt.Key.Key_Escape:
                dialog.reject()
                event.accept()
                return
            QDialog.keyPressEvent(dialog, event)

        dialog.keyPressEvent = keyPressEvent

        def lineEditEventFilter(watched, event):
            if (event.type() == event.Type.KeyPress and watched == line_edit
                    and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right,
                                        Qt.Key.Key_Up, Qt.Key.Key_Down)):
                line_edit.keyPressEvent(event)
                return True
            return False

        line_edit.installEventFilter(dialog)
        dialog.eventFilter = lineEditEventFilter

        ok = dialog.exec() == QDialog.DialogCode.Accepted
        new_filename = line_edit.text().strip() if ok else ""

        QApplication.instance().installEventFilter(self)

        if not ok or not new_filename or new_filename == current_filename:
            return

        # Strip any path components the user may have typed
        new_filename = os.path.basename(new_filename)
        if not new_filename or new_filename in ('.', '..') or '\x00' in new_filename:
            QMessageBox.warning(self, "Invalid Filename",
                                "The filename is invalid. Please enter a valid filename.")
            return

        # Warn if the extension changes to a non-audio type
        new_ext = os.path.splitext(new_filename)[1].lower()
        if new_ext not in AUDIO_EXTENSIONS:
            reply = QMessageBox.question(
                self, "Extension Changed",
                f'The new extension "{new_ext}" is not a recognised audio format.\n'
                'Rename anyway?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        new_file_path = os.path.join(current_directory, new_filename)

        if os.path.exists(new_file_path):
            reply = QMessageBox.question(
                self, "File Exists",
                f'A file named "{new_filename}" already exists. Overwrite?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            backup_path = backup_file(config.selected_file)
            if not backup_path:
                raise Exception("Failed to create backup file")

            shutil.move(config.selected_file, new_file_path)

            config.selected_file = new_file_path
            if config.directory_audio_files and config.current_file_index >= 0:
                config.directory_audio_files[config.current_file_index] = new_file_path

            self.load_file(new_file_path)
            self.set_status(f"Renamed to  {new_filename}")
            QMessageBox.information(
                self, "File Renamed",
                f"File successfully renamed to '{new_filename}'\n"
                f"A backup was created at '{os.path.basename(backup_path)}'",
            )

        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            QMessageBox.critical(self, "Rename Error", f"Failed to rename file:\n{e}")
            if 'backup_path' in locals() and os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, config.selected_file)
                    self.set_status("Restored from backup after rename error")
                except Exception as restore_err:
                    logger.error(f"Error restoring from backup: {restore_err}")
                    self.set_status("Error during rename — manual restore may be needed")

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


    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def on_switch_mode(self, mode_name: str):
        """Called when the mode combo selection changes."""
        if not mode_name or mode_name == config.get_active_mode():
            return

        if self._has_unsaved_edits():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "There are unsaved edits in the current form.\n"
                "Switch mode and discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                if hasattr(self, 'mode_combo'):
                    self.mode_combo.blockSignals(True)
                    self.mode_combo.setCurrentText(config.get_active_mode())
                    self.mode_combo.blockSignals(False)
                return

        config.set_active_mode(mode_name)
        self.metadata_manager.reload_mode(mode_name)
        self.metadata_panel.rebuild_fields()

        if config.selected_file and os.path.isfile(config.selected_file):
            self.load_file(config.selected_file)
        else:
            self.set_status(f"Mode: {mode_name}")

    def _has_unsaved_edits(self) -> bool:
        """Return True if any form field value differs from the loaded metadata."""
        from PyQt6.QtWidgets import QTextEdit as _QTextEdit
        for spec in self.metadata_manager.get_field_specs():
            label = spec['label']
            widget = self.metadata_panel._field_widgets.get(label)
            if widget is None:
                continue
            ui_val = (widget.toPlainText() if isinstance(widget, _QTextEdit)
                      else widget.text())
            if ui_val != self.metadata_manager.get_field(label):
                return True
        return False

    def on_manage_modes(self):
        """Open the Manage Modes dialog and apply any changes."""
        from .widgets.manage_modes_dialog import ManageModesDialog

        dlg = ManageModesDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_modes, new_active = dlg.get_result()
        config.modes = new_modes
        config.active_mode = new_active
        config.save_config()

        if hasattr(self, 'mode_combo'):
            self.mode_combo.blockSignals(True)
            self.mode_combo.clear()
            self.mode_combo.addItems(list(config.modes.keys()))
            self.mode_combo.setCurrentText(config.get_active_mode())
            self.mode_combo.blockSignals(False)

        self.metadata_manager.reload_mode(config.get_active_mode())
        self.metadata_panel.rebuild_fields()

        if config.selected_file and os.path.isfile(config.selected_file):
            self.load_file(config.selected_file)
        else:
            self.set_status(f"Modes updated  —  Active: {config.get_active_mode()}")


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
