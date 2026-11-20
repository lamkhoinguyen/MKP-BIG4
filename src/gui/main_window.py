from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .app_state import AppState
from .pages.algorithm_page import AlgorithmPage
from .pages.comparison_page import ComparisonPage
from .pages.dataset_page import DatasetPage
from .pages.home_page import HomePage
from .widgets.analysis_panel import AnalysisPanel
from .widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    WINDOW_TITLE = "MKP-BIG4 — Phân tích 4 thuật toán MKP"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        self.running = False
        self._page_shortcuts = []
        self.state = AppState(self)

        self._build_ui()
        self._build_shortcuts()
        self._connect_pages()
        self.set_page(0)
        self.pages[3].refresh_history()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        self.analysis = AnalysisPanel()

        self.pages = [
            HomePage(),
            DatasetPage(self.state),
            AlgorithmPage(self.state),
            ComparisonPage(self.state),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.addWidget(self.analysis)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([180, 780, 320])

        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self.sidebar.page_selected.connect(self.set_page)

        bar = self.statusBar()
        self.status_problem = QLabel("Bài toán: chưa chọn")
        self.status_problem.setObjectName("StatusProblem")
        self.status_algorithm = QLabel("Thuật toán: —")
        self.status_algorithm.setObjectName("StatusAlgorithm")
        self.status_elapsed = QLabel("")
        self.status_elapsed.setObjectName("StatusElapsed")
        bar.addPermanentWidget(self.status_problem)
        bar.addPermanentWidget(self.status_algorithm)
        bar.addPermanentWidget(self.status_elapsed)
        bar.showMessage("Sẵn sàng")

    def _build_shortcuts(self) -> None:
        for index in range(4):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{index + 1}"), self)
            shortcut.activated.connect(
                lambda page=index: self.set_page(page)
            )
            self._page_shortcuts.append(shortcut)

        run_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        run_shortcut.activated.connect(self.trigger_primary_action)
        self._page_shortcuts.append(run_shortcut)

        escape = QShortcut(QKeySequence("Esc"), self)
        escape.activated.connect(self._stop_playback)
        self._page_shortcuts.append(escape)

    def _connect_pages(self) -> None:
        for page in self.pages:
            if hasattr(page, "navigate_requested"):
                page.navigate_requested.connect(self.set_page)
            if hasattr(page, "analysis_requested"):
                page.analysis_requested.connect(
                    lambda title, body, sender=page: self._on_analysis_requested(
                        sender, title, body
                    )
                )
            if hasattr(page, "status_message"):
                page.status_message.connect(self.statusBar().showMessage)
            if hasattr(page, "algorithm_text"):
                page.algorithm_text.connect(self.set_algorithm_text)
            if hasattr(page, "running_changed"):
                page.running_changed.connect(self.set_running)

        comparison = self.pages[3]
        comparison.history_list_changed.connect(self.analysis.set_history)
        self.analysis.history_open_requested.connect(comparison.open_session)
        self.analysis.history_delete_requested.connect(comparison.delete_session)
        self.analysis.history_folder_requested.connect(
            comparison.open_sessions_folder
        )

        self.state.problem_changed.connect(
            lambda _problem: self.set_problem_text(self.state.problem_text())
        )

    def _on_analysis_requested(self, sender, title: str, body: str) -> None:
        if self.pages[self.stack.currentIndex()] is sender:
            self.analysis.set_content(title, body)

    def set_page(self, index: int) -> None:
        if not 0 <= index < self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        self.sidebar.set_current(index)
        page = self.pages[index]
        if hasattr(page, "analysis_snapshot"):
            title, body = page.analysis_snapshot()
            self.analysis.set_content(title, body)
        else:
            self.analysis.set_content(page.PAGE_TITLE, page.ANALYSIS_HTML)
        if index == 3:
            self.analysis.history_box.setVisible(True)
            self.pages[3].refresh_history()
        else:
            self.analysis.hide_history()

    def trigger_primary_action(self) -> None:
        if self.running:
            self.statusBar().showMessage("Đang chạy, vui lòng chờ")
            return
        page = self.pages[self.stack.currentIndex()]
        handler = getattr(page, "run_primary_action", None)
        if callable(handler):
            handler()

    def _stop_playback(self) -> None:
        page = self.pages[self.stack.currentIndex()]
        handler = getattr(page, "stop_replay", None)
        if callable(handler):
            handler()

    def set_problem_text(self, text: str) -> None:
        self.sidebar.set_problem_text(text)
        self.status_problem.setText(f"Bài toán: {text}")

    def set_algorithm_text(self, text: str) -> None:
        self.status_algorithm.setText(f"Thuật toán: {text}")

    def set_running(self, running: bool) -> None:
        self.running = running
        self.statusBar().showMessage(
            "Đang chạy thuật toán..." if running else "Sẵn sàng"
        )

    def closeEvent(self, event) -> None:
        if not self.running:
            super().closeEvent(event)
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Đang chạy thuật toán")
        box.setText(
            "Không thể thoát khi thuật toán đang chạy.\n"
            "Bạn có thể thu nhỏ cửa sổ và chờ kết quả."
        )
        minimize_button = box.addButton(
            "Thu nhỏ cửa sổ", QMessageBox.AcceptRole
        )
        wait_button = box.addButton("Tiếp tục chờ", QMessageBox.RejectRole)
        box.setDefaultButton(wait_button)
        box.exec()

        if box.clickedButton() is minimize_button:
            self.showMinimized()
        event.ignore()
