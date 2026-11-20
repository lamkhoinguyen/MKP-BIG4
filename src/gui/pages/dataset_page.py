import html

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.config import DATA_DIR
from src.core.data_loader import load_problems
from src.gui.app_state import AppState
from src.gui.widgets.data_table import ArrayTableModel, make_table_view

ALL_PROBLEMS_LABEL = "(tất cả bài trong file)"
SUMMARY_HEADERS = [
    "Bài toán",
    "n",
    "m",
    "Z_ref",
    "Tổng lợi nhuận",
    "Độ chặt (min–max)",
]


class DatasetPage(QWidget):
    PAGE_TITLE = "Dataset"
    ANALYSIS_HTML = """
    <p><b>Trang dữ liệu</b></p>
    <p>Chọn file OR-Library, chọn bài toán, xem lợi nhuận, ma trận tài nguyên
    và giới hạn tài nguyên.</p>
    <p><b>n</b> là số vật phẩm, <b>m</b> là số tài nguyên. <b>z_ref</b> là giá trị
    tham chiếu để tính gap. Độ chặt tài nguyên i là b_i / Σ_j r_ij.</p>
    <p>Bấm <b>Dùng bài toán này</b> để chuyển sang trang Algorithm.</p>
    """

    analysis_requested = Signal(str, str)
    navigate_requested = Signal(int)

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._problems = []
        self._current_file = ""
        self._current_problem = None
        self._all_selected = False
        self._file_cache = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        title = QLabel(self.PAGE_TITLE)
        title.setObjectName("PageTitle")
        hint = QLabel("Chọn file dataset và bài toán để xem dữ liệu.")
        hint.setObjectName("PageHint")
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_chooser())
        splitter.addWidget(self._build_info())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 320])
        layout.addWidget(splitter)

        self.tabs = QTabWidget()
        self.profits_model = ArrayTableModel()
        self.weights_model = ArrayTableModel()
        self.capacities_model = ArrayTableModel()
        self.summary_model = ArrayTableModel()
        self.tabs.addTab(make_table_view(self.profits_model), "Lợi nhuận p_j")
        self.tabs.addTab(make_table_view(self.weights_model), "Ma trận r_ij")
        self.tabs.addTab(make_table_view(self.capacities_model), "Giới hạn b_i")
        self.tabs.addTab(make_table_view(self.summary_model), "Tổng hợp bài")
        self.tabs.setTabVisible(3, False)
        layout.addWidget(self.tabs, 1)

        self._load_files()

    # ------------------------------------------------------------------
    def _build_chooser(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        caption = QLabel("Chọn dữ liệu")
        caption.setObjectName("CardTitle")
        card_layout.addWidget(caption)

        form = QFormLayout()
        form.setSpacing(8)
        self.file_combo = QComboBox()
        self.file_combo.currentTextChanged.connect(self._on_file_changed)
        form.addRow(self._field_label("File dataset"), self.file_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Tìm theo tên bài…")
        self.search_edit.textChanged.connect(self._apply_filter)
        form.addRow(self._field_label("Tìm bài"), self.search_edit)
        card_layout.addLayout(form)

        self.problem_list = QListWidget()
        self.problem_list.setAlternatingRowColors(True)
        self.problem_list.currentRowChanged.connect(self._on_problem_changed)
        card_layout.addWidget(self.problem_list, 1)

        self.commit_button = QPushButton("Dùng bài toán này")
        self.commit_button.setObjectName("PrimaryButton")
        self.commit_button.setCursor(Qt.PointingHandCursor)
        self.commit_button.clicked.connect(self._commit)
        card_layout.addWidget(self.commit_button)
        return card

    def _build_info(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        caption = QLabel("Thông tin bài toán")
        caption.setObjectName("CardTitle")
        card_layout.addWidget(caption)

        form = QFormLayout()
        form.setSpacing(8)
        self.info_values = {}
        for key, text in (
            ("name", "Tên bài"),
            ("n", "Số vật phẩm n"),
            ("m", "Số tài nguyên m"),
            ("z_ref", "Z_ref"),
            ("tightness", "Độ chặt"),
        ):
            label = QLabel("-")
            label.setObjectName("FieldValue")
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            form.addRow(self._field_label(text), label)
            self.info_values[key] = label
        card_layout.addLayout(form)
        card_layout.addStretch(1)
        return card

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    # ------------------------------------------------------------------
    def _load_files(self) -> None:
        files = sorted(
            path.name
            for path in DATA_DIR.glob("*.txt")
            if path.name != "mkcbres.txt"
        )
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        self.file_combo.addItems(files)
        self.file_combo.blockSignals(False)
        if files:
            self.file_combo.setCurrentIndex(0)
            self._on_file_changed(files[0])

    def _on_file_changed(self, file_name: str) -> None:
        if not file_name:
            return
        self._current_file = file_name
        try:
            if file_name not in self._file_cache:
                self._file_cache[file_name] = load_problems(DATA_DIR / file_name)
            self._problems = self._file_cache[file_name]
        except Exception as exc:  # noqa: BLE001 - hiển thị lỗi cho người dùng
            self._problems = []
            self._current_problem = None
            self._all_selected = False
            self.info_values["name"].setText(f"Lỗi đọc file: {exc}")
            self.problem_list.clear()
            return

        self.problem_list.blockSignals(True)
        self.problem_list.clear()
        self.problem_list.addItem(ALL_PROBLEMS_LABEL)
        for problem in self._problems:
            item = QListWidgetItem(f"{problem.name}  (n={problem.n}, m={problem.m})")
            self.problem_list.addItem(item)
        self.problem_list.blockSignals(False)

        self.search_edit.clear()
        if self._problems:
            self.problem_list.setCurrentRow(1)
            self._on_problem_changed(1)
        else:
            self._current_problem = None
            self._all_selected = False
            self._clear_tables()

    def _on_problem_changed(self, row: int) -> None:
        if row == 0:
            self._all_selected = bool(self._problems)
            self._current_problem = None
            self._show_all_summary()
            return

        self._all_selected = False
        self.summary_model.set_data([], headers=SUMMARY_HEADERS)
        self.tabs.setTabVisible(3, False)
        self.tabs.setCurrentIndex(0)
        index = row - 1
        if not 0 <= index < len(self._problems):
            self._current_problem = None
            self._clear_tables()
            return
        self._current_problem = self._problems[index]
        self._update_problem(self._current_problem)

    def _apply_filter(self, text: str) -> None:
        query = text.strip().lower()
        for index in range(1, self.problem_list.count()):
            item = self.problem_list.item(index)
            item.setHidden(bool(query) and query not in item.text().lower())

    def _clear_tables(self) -> None:
        self.profits_model.set_data([], headers=["Vật phẩm", "Lợi nhuận p_j"])
        self.weights_model.set_data([], headers=["Vật phẩm"])
        self.capacities_model.set_data([], headers=["Tài nguyên", "Giới hạn b_i"])
        self.summary_model.set_data([], headers=SUMMARY_HEADERS)
        self.tabs.setTabVisible(3, False)
        for label in self.info_values.values():
            label.setText("-")

    def _show_all_summary(self) -> None:
        self.profits_model.set_data([], headers=["Vật phẩm", "Lợi nhuận p_j"])
        self.weights_model.set_data([], headers=["Vật phẩm"])
        self.capacities_model.set_data([], headers=["Tài nguyên", "Giới hạn b_i"])
        self.summary_model.set_data(self._all_summary_rows(), headers=SUMMARY_HEADERS)
        self.tabs.setTabVisible(3, bool(self._problems))
        if self._problems:
            self.tabs.setCurrentIndex(3)
            ns = [problem.n for problem in self._problems]
            ms = [problem.m for problem in self._problems]
            self.info_values["name"].setText(
                f"Tất cả {len(self._problems)} bài trong {self._current_file}"
            )
            self.info_values["n"].setText(self._range_text(ns))
            self.info_values["m"].setText(self._range_text(ms))
            self.info_values["z_ref"].setText("-")
            self.info_values["tightness"].setText(
                "Xem tab Tổng hợp bài (mỗi bài có độ chặt riêng)"
            )
        else:
            self.tabs.setCurrentIndex(0)
            self.info_values["name"].setText(ALL_PROBLEMS_LABEL)
            for key in ("n", "m", "z_ref", "tightness"):
                self.info_values[key].setText("-")
        self._emit_all_analysis()

    @staticmethod
    def _range_text(values) -> str:
        smallest, largest = min(values), max(values)
        return str(smallest) if smallest == largest else f"{smallest}–{largest}"

    def _all_summary_rows(self) -> list[list]:
        rows = []
        for problem in self._problems:
            tightness = [
                value for value in self._tightness(problem) if value is not None
            ]
            if tightness:
                tightness_text = (
                    f"{min(tightness):.2f}"
                    if min(tightness) == max(tightness)
                    else f"{min(tightness):.2f}–{max(tightness):.2f}"
                )
            else:
                tightness_text = "-"
            z_ref = (
                "-"
                if problem.z_ref is None
                else self._format_int(problem.z_ref)
            )
            rows.append(
                [
                    problem.name,
                    problem.n,
                    problem.m,
                    z_ref,
                    self._format_int(problem.profits.sum()),
                    tightness_text,
                ]
            )
        return rows

    def _emit_all_analysis(self) -> None:
        self.analysis_requested.emit(
            self.PAGE_TITLE,
            self._all_analysis_html(self._current_file, self._problems),
        )

    @classmethod
    def _all_analysis_html(cls, file_name: str, problems) -> str:
        if not problems:
            return cls.ANALYSIS_HTML
        ns = [problem.n for problem in problems]
        ms = [problem.m for problem in problems]
        rows = "".join(
            f"<tr><td>{html.escape(problem.name)}</td><td>{problem.n}</td>"
            f"<td>{problem.m}</td>"
            f"<td>{'—' if problem.z_ref is None else cls._format_int(problem.z_ref)}</td>"
            f"<td>{cls._format_int(problem.profits.sum())}</td></tr>"
            for problem in problems[:20]
        )
        more = (
            f"<p>… và {len(problems) - 20} bài khác trong {html.escape(file_name)}.</p>"
            if len(problems) > 20
            else ""
        )
        return f"""
        <p><b>Tất cả {len(problems)} bài trong {html.escape(file_name)}</b></p>
        <p>Số vật phẩm n: {cls._format_int(min(ns))}–{cls._format_int(max(ns))};
        số tài nguyên m: {cls._format_int(min(ms))}–{cls._format_int(max(ms))}.</p>
        <p>Mỗi bài có lợi nhuận, ma trận và giới hạn riêng; chọn một bài để xem
        chi tiết. Khi chạy batch, chương trình dùng đúng dữ liệu của từng bài.</p>
        <table border="0" cellspacing="2" cellpadding="2">
          <tr><th>Bài</th><th>n</th><th>m</th><th>Z_ref</th><th>Tổng lợi nhuận</th></tr>
          {rows}
        </table>
        {more}
        """

    def _update_problem(self, problem) -> None:
        self.info_values["name"].setText(problem.name)
        self.info_values["n"].setText(str(problem.n))
        self.info_values["m"].setText(str(problem.m))
        self.info_values["z_ref"].setText(
            "-" if problem.z_ref is None else str(int(problem.z_ref))
        )

        profits = [
            [index + 1, float(problem.profits[index])]
            for index in range(problem.n)
        ]
        self.profits_model.set_data(
            profits,
            headers=["Vật phẩm", "Lợi nhuận p_j"],
        )

        weights = problem.weights.tolist()
        self.weights_model.set_data(
            weights,
            headers=[f"j={index + 1}" for index in range(problem.n)],
            row_headers=[f"R{index + 1}" for index in range(problem.m)],
        )

        capacities = [
            [index + 1, float(problem.capacities[index])]
            for index in range(problem.m)
        ]
        self.capacities_model.set_data(
            capacities,
            headers=["Tài nguyên", "Giới hạn b_i"],
        )

        tightness = self._tightness(problem)
        summary = ", ".join(
            f"R{index + 1}={'—' if value is None else f'{value:.2f}'}"
            for index, value in enumerate(tightness)
        )
        self.info_values["tightness"].setText(summary or "-")
        self._emit_analysis(problem, tightness)

    @staticmethod
    def _tightness(problem) -> list:
        result = []
        for index in range(problem.m):
            demand = float(problem.weights[index].sum())
            capacity = float(problem.capacities[index])
            result.append(None if demand == 0 else capacity / demand)
        return result

    def _emit_analysis(self, problem, tightness) -> None:
        self.analysis_requested.emit(
            self.PAGE_TITLE, self._analysis_html(problem, tightness)
        )

    @staticmethod
    def _format_int(value) -> str:
        return f"{float(value):,.0f}".replace(",", ".")

    @classmethod
    def _analysis_html(cls, problem, tightness) -> str:
        rows = "".join(
            f"<tr><td>R{index + 1}</td>"
            f"<td>{cls._format_int(problem.capacities[index])}</td>"
            f"<td>{cls._format_int(problem.weights[index].sum())}</td>"
            f"<td>{'—' if value is None else f'{value:.3f}'}</td></tr>"
            for index, value in enumerate(tightness)
        )
        z_ref = (
            "—" if problem.z_ref is None else cls._format_int(problem.z_ref)
        )
        return f"""
        <p><b>Dữ liệu bài {html.escape(problem.name)}</b></p>
        <p>n = {problem.n}, m = {problem.m}, Z_ref = {z_ref}</p>
        <p>Tổng lợi nhuận: {cls._format_int(problem.profits.sum())}</p>
        <table border="0" cellspacing="2" cellpadding="2">
          <tr><th>Tài nguyên</th><th>b_i</th><th>Σ r_ij</th><th>Chặt</th></tr>
          {rows}
        </table>
        <p>Độ chặt = b_i / Σ_j r_ij; dấu — nghĩa là tổng nhu cầu bằng 0.</p>
        """

    def _commit(self) -> None:
        if self._all_selected:
            if not self._problems:
                return
            self.state.commit_problems(self._current_file, self._problems)
        else:
            if self._current_problem is None:
                return
            self.state.commit_problem(self._current_file, self._current_problem)
        self.navigate_requested.emit(2)

    # ------------------------------------------------------------------
    def analysis_snapshot(self):
        if self._all_selected:
            title, html_text = self._all_analysis_html(
                self._current_file, self._problems
            )
            return title, html_text
        if self._current_problem is None:
            return self.PAGE_TITLE, self.ANALYSIS_HTML
        tightness = self._tightness(self._current_problem)
        return self.PAGE_TITLE, self._analysis_html(self._current_problem, tightness)

    def run_primary_action(self) -> None:
        self._commit()
