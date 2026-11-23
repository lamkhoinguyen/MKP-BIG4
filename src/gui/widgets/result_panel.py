"""Bảng kết quả dùng lại ở trang Algorithm và Comparison."""

from typing import Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHeaderView,
    QLabel,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.gui import analytics
from src.gui.widgets.data_table import ArrayTableModel, make_table_view


RESULT_HEADERS = (
    "Thuật toán",
    "Số seed (N)",
    "Profit",
    "Avg",
    "Worst",
    "Std",
    "Gap best (%)",
    "Gap avg (%)",
    "Runtime (s)",
    "Feasible",
    "Status",
    "Số vật phẩm",
    "Bộ nhớ đỉnh (MB)",
)

COL_COUNT = 1
COL_AVG = 3
COL_WORST = 4
COL_STD = 5
COL_GAP_AVG = 7
COL_MEMORY = 12
STABILITY_COLUMNS = {COL_AVG, COL_WORST, COL_STD, COL_GAP_AVG}

HEADER_TOOLTIPS = {
    COL_COUNT: "Số lần chạy thật: Greedy/DP = 1 (tất định), GA/SA = N seed đã chọn.",
    COL_AVG: "Chỉ áp dụng cho GA/SA khi N > 1; Greedy/DP tất định nên không có.",
    COL_WORST: "Chỉ áp dụng cho GA/SA khi N > 1; Greedy/DP tất định nên không có.",
    COL_STD: "Độ lệch chuẩn giữa các seed; chỉ GA/SA khi N > 1.",
    COL_GAP_AVG: "Gap trung bình giữa các seed; chỉ GA/SA khi N > 1.",
    COL_MEMORY: "Chỉ DP báo cáo bộ nhớ đỉnh; thuật toán khác không đo.",
}

TABLE_HINT = (
    "Chất lượng & hiệu năng (cả 4 thuật toán): Profit, Gap best, Runtime, "
    "Feasible, Status. Độ ổn định (chỉ GA/SA khi N > 1): Avg, Worst, Std, "
    "Gap avg. Greedy/DP tất định nên chỉ chạy 1 lần — ô “-” không phải thiếu kết quả."
)


def _gap_percent(value) -> str:
    return analytics.fmt_percent(value)


def _display_row(row: dict) -> list[str]:
    return [
        row.get("label", "-"),
        "-" if row.get("count") is None else str(row["count"]),
        analytics.fmt_number(row.get("profit"), 0),
        analytics.fmt_number(row.get("avg"), 0),
        analytics.fmt_number(row.get("worst"), 0),
        analytics.fmt_number(row.get("std"), 2),
        _gap_percent(row.get("gap_best")),
        _gap_percent(row.get("gap_avg")),
        analytics.fmt_number(row.get("runtime"), 3),
        row.get("feasible", "-"),
        row.get("status", "-"),
        "-" if row.get("selected_count") is None else str(row["selected_count"]),
        analytics.fmt_number(row.get("peak_memory"), 2),
    ]


class ResultTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[list[dict]] = None, parent=None):
        super().__init__(parent)
        self._rows = list(rows or [])
        self._display = [_display_row(row) for row in self._rows]

    def set_rows(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self._rows = list(rows or [])
        self._display = [_display_row(row) for row in self._rows]
        self.endResetModel()

    def clear(self) -> None:
        self.set_rows([])

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(RESULT_HEADERS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._display[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)
        if role == Qt.ToolTipRole:
            row = self._rows[index.row()]
            column = index.column()
            if column in STABILITY_COLUMNS and not row.get("stochastic"):
                return (
                    "Greedy/DP là thuật toán tất định: chỉ chạy 1 lần nên "
                    "không có Avg/Worst/Std/Gap avg."
                )
            if column == COL_MEMORY and row.get("peak_memory") is None:
                return "Chỉ DP báo cáo bộ nhớ đỉnh; thuật toán này không đo."
            if column == COL_COUNT:
                return HEADER_TOOLTIPS[COL_COUNT]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Horizontal and section in HEADER_TOOLTIPS:
            if role == Qt.ToolTipRole:
                return HEADER_TOOLTIPS[section]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(RESULT_HEADERS):
            return RESULT_HEADERS[section]
        return None


class ResultTable(QWidget):
    def __init__(
        self,
        title: str = "Kết quả",
        empty_text: str = "Chưa có kết quả.",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        if title:
            caption = QLabel(title)
            caption.setObjectName("CardTitle")
            layout.addWidget(caption)

        self.hint = QLabel(TABLE_HINT)
        self.hint.setObjectName("FieldNote")
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        self.model = ResultTableModel()
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.view.horizontalHeader().setStretchLastSection(True)

        self.empty_label = QLabel(empty_text)
        self.empty_label.setObjectName("EmptyState")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.empty_label)
        self.stack.addWidget(self.view)
        layout.addWidget(self.stack, 1)
        self.stack.setCurrentWidget(self.empty_label)

    def set_rows(self, rows: list[dict]) -> None:
        self.model.set_rows(rows)
        has_memory = any(row.get("peak_memory") is not None for row in rows)
        self.view.setColumnHidden(COL_MEMORY, not has_memory)
        self.stack.setCurrentWidget(self.view if rows else self.empty_label)

    def clear(self) -> None:
        self.model.clear()
        self.stack.setCurrentWidget(self.empty_label)


class SingleResultDetails(QWidget):
    """Chi tiết một lần chạy cho trang Algorithm."""

    FIELDS = (
        ("profit", "Profit"),
        ("runtime", "Runtime"),
        ("gap", "Gap (%)"),
        ("feasible", "Feasible"),
        ("status", "Status"),
        ("selected", "Số vật phẩm chọn"),
        ("peak", "Bộ nhớ đỉnh"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailsPanel")
        self._problem = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(4)

        title = QLabel("Chi tiết lần chạy")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(4)
        self.values = {}
        for key, caption_text in self.FIELDS:
            caption = QLabel(caption_text)
            caption.setObjectName("FieldLabel")
            value = QLabel("-")
            value.setObjectName("FieldValue")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            form.addRow(caption, value)
            self.values[key] = (caption, value)
        layout.addLayout(form)

        self.note = QLabel("")
        self.note.setObjectName("FieldNote")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        resource_title = QLabel("Mức dùng tài nguyên")
        resource_title.setObjectName("FieldLabel")
        layout.addWidget(resource_title)

        self.resource_model = ArrayTableModel(
            [["-", "-", "-"]],
            headers=["Đã dùng", "Giới hạn", "% sử dụng"],
        )
        self.resource_view = make_table_view(self.resource_model)
        self.resource_view.setMinimumHeight(150)
        self.resource_view.verticalHeader().setFixedWidth(48)
        self.resource_view.verticalHeader().setDefaultSectionSize(22)
        self.resource_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.resource_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.resource_view, 1)

        self.clear()

    def clear(self) -> None:
        self._problem = None
        for _, value in self.values.values():
            value.setText("-")
        self._show_peak(False)
        self.note.setText("")
        self.resource_model.set_data(
            [[], []],
            headers=["Đã dùng", "Giới hạn", "% sử dụng"],
            row_headers=[],
        )

    def _show_peak(self, visible: bool) -> None:
        caption, value = self.values["peak"]
        caption.setVisible(visible)
        value.setVisible(visible)

    def show_result(self, problem, result) -> None:
        self._problem = problem
        gap = getattr(result, "optimality_gap", None)
        selected = len(getattr(result, "selected_items", None) or [])
        peak = float(getattr(result, "peak_memory", 0.0) or 0.0)

        self.values["profit"][1].setText(
            analytics.fmt_number(getattr(result, "total_profit", None), 0)
        )
        self.values["runtime"][1].setText(
            analytics.fmt_seconds(getattr(result, "runtime", None))
        )
        self.values["gap"][1].setText(analytics.fmt_percent(gap))
        self.values["feasible"][1].setText(
            "Có" if getattr(result, "feasible", False) else "Không"
        )
        self.values["status"][1].setText(str(getattr(result, "status", "-")))
        self.values["selected"][1].setText(str(selected))
        self.values["peak"][1].setText(f"{peak:.2f} MB")
        self._show_peak(peak > 0)

        status = str(getattr(result, "status", "ok"))
        if status == "timeout":
            self.note.setText(
                "Dừng do hết thời gian; kết quả là nghiệm tốt nhất tại thời "
                "điểm dừng."
            )
        elif status == "out_of_memory":
            self.note.setText(
                "Dừng do giới hạn bộ nhớ; kết quả là nghiệm tốt nhất có kiểm soát."
            )
        else:
            self.note.setText("")

        self._fill_resources(problem, result)

    def _fill_resources(self, problem, result) -> None:
        usage = list(getattr(result, "resource_usage", None) or [])
        capacities = [float(value) for value in getattr(problem, "capacities", [])]
        rows = []
        row_headers = []
        for index, capacity in enumerate(capacities):
            used = float(usage[index]) if index < len(usage) else 0.0
            if capacity == 0:
                percent = "-"
            else:
                percent = analytics.fmt_percent(used / capacity)
            rows.append([analytics.fmt_number(used, 2), analytics.fmt_number(capacity, 2), percent])
            row_headers.append(f"R{index + 1}")
        self.resource_model.set_data(
            rows,
            headers=["Đã dùng", "Giới hạn", "% sử dụng"],
            row_headers=row_headers,
        )

    def show_error(self, message: str) -> None:
        self.clear()
        self.note.setText(f"Lỗi: {message}")
