"""
Audio Tag Writer - ManageModesDialog: edit mode definitions.
"""

import copy
import logging

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QWidget, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QLabel, QInputDialog, QMessageBox, QDialogButtonBox,
    QComboBox, QStyledItemDelegate,
)
from PyQt6.QtCore import Qt

from ..config import config
from ..constants import DEFAULT_MODES

logger = logging.getLogger(__name__)

_WIDGET_TYPES = ["line", "text"]


class _ComboDelegate(QStyledItemDelegate):
    """Inline QComboBox editor for the Widget Type column."""

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(_WIDGET_TYPES)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.DisplayRole) or "line"
        idx = _WIDGET_TYPES.index(value) if value in _WIDGET_TYPES else 0
        editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class ManageModesDialog(QDialog):
    """
    Dialog for viewing and editing mode definitions.

    Left panel: list of mode names with Add / Rename / Delete / Reset controls.
    Right panel: editable field table for the selected mode.
    OK writes to config; Cancel discards all changes.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Modes")
        self.resize(860, 520)
        self._modes = copy.deepcopy(config.modes)
        self._active_mode = config.get_active_mode()
        self._current_mode = None
        self._setup_ui()
        self._populate_mode_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QVBoxLayout(self)

        content = QHBoxLayout()
        root.addLayout(content, 1)

        # ── Left: mode list ───────────────────────────────────────────
        left_widget = QWidget()
        left_widget.setFixedWidth(210)
        left = QVBoxLayout(left_widget)
        left.setContentsMargins(0, 0, 8, 0)
        left.addWidget(QLabel("Modes"))

        self._mode_list = QListWidget()
        self._mode_list.currentTextChanged.connect(self._on_mode_selected)
        left.addWidget(self._mode_list, 1)

        mode_btns = QHBoxLayout()
        self._btn_add_mode = QPushButton("Add")
        self._btn_add_mode.setToolTip("Create a new empty mode")
        self._btn_add_mode.clicked.connect(self._on_add_mode)
        self._btn_rename_mode = QPushButton("Rename")
        self._btn_rename_mode.clicked.connect(self._on_rename_mode)
        self._btn_delete_mode = QPushButton("Delete")
        self._btn_delete_mode.clicked.connect(self._on_delete_mode)
        self._btn_reset_mode = QPushButton("Reset")
        self._btn_reset_mode.setToolTip("Reset built-in mode to its defaults")
        self._btn_reset_mode.clicked.connect(self._on_reset_mode)
        for btn in (self._btn_add_mode, self._btn_rename_mode,
                    self._btn_delete_mode, self._btn_reset_mode):
            mode_btns.addWidget(btn)
        left.addLayout(mode_btns)

        content.addWidget(left_widget)

        # ── Right: field table ────────────────────────────────────────
        right = QVBoxLayout()
        self._fields_label = QLabel("Fields")
        right.addWidget(self._fields_label)

        self._field_table = QTableWidget(0, 4)
        self._field_table.setHorizontalHeaderLabels(
            ["Label", "Frame ID", "Widget", "Max Chars"]
        )
        hdr = self._field_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._field_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._field_table.setItemDelegateForColumn(2, _ComboDelegate(self._field_table))
        right.addWidget(self._field_table, 1)

        field_btns = QHBoxLayout()
        self._btn_add_field = QPushButton("Add Field")
        self._btn_add_field.clicked.connect(self._on_add_field)
        self._btn_remove_field = QPushButton("Remove")
        self._btn_remove_field.clicked.connect(self._on_remove_field)
        self._btn_field_up = QPushButton("↑ Up")
        self._btn_field_up.clicked.connect(self._on_field_up)
        self._btn_field_down = QPushButton("↓ Down")
        self._btn_field_down.clicked.connect(self._on_field_down)
        for btn in (self._btn_add_field, self._btn_remove_field,
                    self._btn_field_up, self._btn_field_down):
            field_btns.addWidget(btn)
        field_btns.addStretch()
        right.addLayout(field_btns)

        content.addLayout(right, 1)

        # ── OK / Cancel ───────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    # ------------------------------------------------------------------
    # Mode list
    # ------------------------------------------------------------------

    def _populate_mode_list(self):
        self._mode_list.blockSignals(True)
        self._mode_list.clear()
        for name in self._modes:
            self._mode_list.addItem(name)
        self._mode_list.blockSignals(False)

        target = self._active_mode
        items = self._mode_list.findItems(target, Qt.MatchFlag.MatchExactly)
        if items:
            self._mode_list.setCurrentItem(items[0])
        elif self._mode_list.count() > 0:
            self._mode_list.setCurrentRow(0)

    def _on_mode_selected(self, mode_name: str):
        self._save_current_fields()
        self._current_mode = mode_name
        self._fields_label.setText(f"Fields for: {mode_name}")
        self._load_fields(mode_name)
        self._update_mode_buttons()

    def _update_mode_buttons(self):
        mode = self._current_mode
        self._btn_delete_mode.setEnabled(len(self._modes) > 1)
        self._btn_reset_mode.setEnabled(bool(mode and mode in DEFAULT_MODES))
        has_mode = bool(mode)
        self._btn_rename_mode.setEnabled(has_mode)
        self._btn_add_field.setEnabled(has_mode)
        self._btn_remove_field.setEnabled(has_mode)
        self._btn_field_up.setEnabled(has_mode)
        self._btn_field_down.setEnabled(has_mode)

    # ------------------------------------------------------------------
    # Field table
    # ------------------------------------------------------------------

    def _load_fields(self, mode_name: str):
        self._field_table.blockSignals(True)
        self._field_table.setRowCount(0)
        for spec in self._modes.get(mode_name, []):
            self._append_row(spec)
        self._field_table.blockSignals(False)

    def _append_row(self, spec: dict):
        row = self._field_table.rowCount()
        self._field_table.insertRow(row)
        self._field_table.setItem(row, 0, QTableWidgetItem(spec.get('label', '')))
        self._field_table.setItem(row, 1, QTableWidgetItem(spec.get('frame_id', '')))
        self._field_table.setItem(row, 2, QTableWidgetItem(spec.get('widget', 'line')))
        self._field_table.setItem(row, 3, QTableWidgetItem(str(spec.get('max_chars', 2000))))

    def _save_current_fields(self):
        """Flush table contents back into _modes for the current mode."""
        if self._current_mode is None:
            return
        specs = []
        for row in range(self._field_table.rowCount()):
            def _cell(col):
                item = self._field_table.item(row, col)
                return item.text().strip() if item else ''
            label = _cell(0)
            frame_id = _cell(1)
            widget_type = _cell(2)
            max_chars_text = _cell(3)
            if not label or not frame_id:
                continue
            try:
                max_chars = int(max_chars_text)
            except ValueError:
                max_chars = 2000
            specs.append({
                'label': label,
                'frame_id': frame_id,
                'widget': widget_type if widget_type in _WIDGET_TYPES else 'line',
                'max_chars': max_chars,
            })
        self._modes[self._current_mode] = specs

    # ------------------------------------------------------------------
    # Mode button handlers
    # ------------------------------------------------------------------

    def _on_add_mode(self):
        name, ok = QInputDialog.getText(self, "Add Mode", "Mode name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._modes:
            QMessageBox.warning(self, "Duplicate Name",
                                f'A mode named "{name}" already exists.')
            return
        self._modes[name] = []
        self._populate_mode_list()
        items = self._mode_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self._mode_list.setCurrentItem(items[0])

    def _on_rename_mode(self):
        if not self._current_mode:
            return
        old = self._current_mode
        new, ok = QInputDialog.getText(self, "Rename Mode", "New name:", text=old)
        if not ok or not new.strip() or new.strip() == old:
            return
        new = new.strip()
        if new in self._modes:
            QMessageBox.warning(self, "Duplicate Name",
                                f'A mode named "{new}" already exists.')
            return
        self._save_current_fields()
        rebuilt = {(new if k == old else k): v for k, v in self._modes.items()}
        self._modes = rebuilt
        if self._active_mode == old:
            self._active_mode = new
        self._current_mode = new
        self._populate_mode_list()

    def _on_delete_mode(self):
        if not self._current_mode or len(self._modes) <= 1:
            return
        reply = QMessageBox.question(
            self, "Delete Mode",
            f'Delete mode "{self._current_mode}"?\nThis cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        deleted = self._current_mode
        del self._modes[deleted]
        if self._active_mode == deleted:
            self._active_mode = next(iter(self._modes))
        self._current_mode = None
        self._populate_mode_list()

    def _on_reset_mode(self):
        if not self._current_mode or self._current_mode not in DEFAULT_MODES:
            return
        reply = QMessageBox.question(
            self, "Reset Mode",
            f'Reset "{self._current_mode}" to its built-in defaults?\n'
            'Any customisations will be lost.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._modes[self._current_mode] = copy.deepcopy(DEFAULT_MODES[self._current_mode])
        self._load_fields(self._current_mode)

    # ------------------------------------------------------------------
    # Field button handlers
    # ------------------------------------------------------------------

    def _on_add_field(self):
        if not self._current_mode:
            return
        row = self._field_table.rowCount()
        self._field_table.insertRow(row)
        self._field_table.setItem(row, 0, QTableWidgetItem("New Field"))
        self._field_table.setItem(row, 1, QTableWidgetItem("TXXX:NewField"))
        self._field_table.setItem(row, 2, QTableWidgetItem("line"))
        self._field_table.setItem(row, 3, QTableWidgetItem("2000"))
        self._field_table.scrollToBottom()
        self._field_table.setCurrentCell(row, 0)
        self._field_table.editItem(self._field_table.item(row, 0))

    def _on_remove_field(self):
        row = self._field_table.currentRow()
        if row >= 0:
            self._field_table.removeRow(row)

    def _on_field_up(self):
        row = self._field_table.currentRow()
        if row <= 0:
            return
        self._swap_rows(row, row - 1)
        self._field_table.setCurrentCell(row - 1, self._field_table.currentColumn())

    def _on_field_down(self):
        row = self._field_table.currentRow()
        if row < 0 or row >= self._field_table.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self._field_table.setCurrentCell(row + 1, self._field_table.currentColumn())

    def _swap_rows(self, r1: int, r2: int):
        for col in range(self._field_table.columnCount()):
            item1 = self._field_table.takeItem(r1, col)
            item2 = self._field_table.takeItem(r2, col)
            self._field_table.setItem(r1, col, item2)
            self._field_table.setItem(r2, col, item1)

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------

    def _on_ok(self):
        self._save_current_fields()
        for name, fields in self._modes.items():
            if not fields:
                QMessageBox.warning(
                    self, "Empty Mode",
                    f'Mode "{name}" has no fields.\n'
                    'Add at least one field before saving.',
                )
                items = self._mode_list.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    self._mode_list.setCurrentItem(items[0])
                return
        self.accept()

    def get_result(self):
        """Return (modes_dict, active_mode_name) after the dialog is accepted."""
        return self._modes, self._active_mode
