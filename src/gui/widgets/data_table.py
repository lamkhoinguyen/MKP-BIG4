"""Model/view dùng lại cho các bảng dữ liệu lớn (không dựng widget từng ô)."""

from typing import Optional

import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QAbstractItemView, QTableView


def _format(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, (np.integer,)):
        return str(int(value))
    if isinstance(value, (np.floating,)):
        number = float(value)
        return str(int(number)) if number.is_integer() else f"{number:.2f}"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}"
    return str(value)


class ArrayTableModel(QAbstractTableModel):
    """Bảng hai chiều đọc từ list/numpy array."""

    def __init__(
        self,
        data=None,
        headers: Optional[list[str]] = None,
        row_headers: Optional[list[str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._headers: list[str] = []
        self._row_headers: list[str] = []
        self._data: list[list] = []
        self.set_data(data or [], headers, row_headers)

    def set_data(self, data, headers=None, row_headers=None) -> None:
        self.beginResetModel()
        if isinstance(data, np.ndarray):
            data = data.tolist()
        self._data = [list(row) if isinstance(row, (list, tuple, np.ndarray)) else [row] for row in data]
        columns = max((len(row) for row in self._data), default=0)
        if headers is None:
            headers = [str(index + 1) for index in range(columns)]
        self._headers = [str(name) for name in headers]
        self._row_headers = [str(name) for name in (row_headers or [])]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            try:
                value = self._data[index.row()][index.column()]
            except IndexError:
                return ""
            return _format(value)
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
            return None
        if 0 <= section < len(self._row_headers):
            return self._row_headers[section]
        return str(section + 1)


def make_table_view(model: ArrayTableModel, parent=None) -> QTableView:
    view = QTableView(parent)
    view.setModel(model)
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QAbstractItemView.SelectRows)
    view.setEditTriggers(QAbstractItemView.NoEditTriggers)
    view.verticalHeader().setDefaultSectionSize(24)
    view.horizontalHeader().setDefaultSectionSize(96)
    view.horizontalHeader().setStretchLastSection(True)
    return view
