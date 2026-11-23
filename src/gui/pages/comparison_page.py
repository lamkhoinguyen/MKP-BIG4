import html
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui import analytics, session_store
from src.gui.app_state import AppState
from src.gui.widgets.chart_widget import ChartWidget
from src.gui.widgets.control_panel import ControlPanel
from src.gui.widgets.dialogs import ask_confirm
from src.gui.widgets.result_panel import ResultTable
from src.gui.workers.algorithm_worker import SessionWorker


class ComparisonPage(QWidget):
    PAGE_TITLE = "Comparison"
    ANALYSIS_HTML = """
    <p><b>Trang so sánh</b></p>
    <p>Chạy cả 4 thuật toán trong cùng một phiên, cùng bài toán và cùng
    Time Limit; xem bảng, biểu đồ và nhận xét tự động.</p>
    <p>Nếu đã chạy Run All ở trang Algorithm cho cùng bài, bấm
    "Dùng kết quả Run All" để so sánh mà không chạy lại.</p>
    <p>Chọn bài toán ở trang Dataset, sau đó bấm Run Session.</p>
    """

    analysis_requested = Signal(str, str)
    status_message = Signal(str)
    running_changed = Signal(bool)
    history_list_changed = Signal(list)
    navigate_requested = Signal(int)
    REUSE_TOOLTIP = (
        "Nạp kết quả 4 thuật toán vừa chạy ở trang Algorithm cho đúng bài đang "
        "chọn, để so sánh mà không phải chạy lại."
    )

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._thread = None
        self._worker = None
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self._batch_problems = []
        self._batch_index = 0
        self._batch_records = {}
        self._batch_paths = []
        self._batch_comments = []
        self._current_rows = []
        self._current_session = None
        self._saved_path = None
        self._run_problem = None
        self._run_dataset = ""
        self._base_seed = 0
        self._num_seeds = 1
        self._total_runs = 0
        self._started_at = 0.0
        self._last_directory = str(Path.home())
        self._log_lines = []

        self._clock = QTimer(self)
        self._clock.setInterval(500)
        self._clock.timeout.connect(self._update_clock)

        self._build_ui()
        self._on_problem_changed(state.problem)
        state.problem_changed.connect(self._on_problem_changed)
        state.batch_changed.connect(self._refresh_reuse_state)
        state.dataset_changed.connect(self._refresh_reuse_state)
        state.run_all_changed.connect(self._refresh_reuse_state)
        state.running_changed.connect(self._refresh_reuse_state)
        self._update_seed_label()
        self._refresh_reuse_state()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        title = QLabel(self.PAGE_TITLE)
        title.setObjectName("PageTitle")
        hint = QLabel("Chạy phiên so sánh chính thức: lưu kết quả, nhiều seed, nhận xét.")
        hint.setObjectName("PageHint")
        hint.setWordWrap(True)
        self.problem_label = QLabel("Bài toán: chưa chọn")
        self.problem_label.setObjectName("ProblemLine")
        self.banner = QLabel("")
        self.banner.setObjectName("SavedBanner")
        self.banner.setWordWrap(True)
        self.banner.setVisible(False)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.problem_label)
        layout.addWidget(self.banner)
        layout.addWidget(self._build_controls())

        self.result_table = ResultTable(
            "Bảng so sánh",
            "Chưa có kết quả — bấm Run Session để bắt đầu.",
        )
        self.content_tabs = QTabWidget()
        self.content_tabs.addTab(self.result_table, "Bảng kết quả")

        self.chart_profit = ChartWidget()
        self.chart_gap = ChartWidget()
        self.chart_runtime = ChartWidget()
        self.chart_convergence = ChartWidget()
        self.chart_memory = ChartWidget()
        for widget, name in (
            (self.chart_profit, "Profit"),
            (self.chart_gap, "Gap"),
            (self.chart_runtime, "Runtime"),
            (self.chart_convergence, "Hội tụ"),
            (self.chart_memory, "Bộ nhớ đỉnh"),
        ):
            widget.show_placeholder("Bấm Run Session để bắt đầu")
            self.content_tabs.addTab(widget, name)
        self.content_tabs.setTabVisible(5, False)
        self.content_tabs.currentChanged.connect(self._on_content_tab_changed)
        layout.addWidget(self.content_tabs, 1)

    def _on_content_tab_changed(self, index: int) -> None:
        widget = self.content_tabs.widget(index)
        if isinstance(widget, ChartWidget):
            widget.canvas.draw_idle()

    def _build_controls(self) -> QWidget:
        self.controls = ControlPanel("Tham số phiên")
        self.time_spin = QDoubleSpinBox()
        self.time_spin.setRange(0.1, 3600.0)
        self.time_spin.setDecimals(1)
        self.time_spin.setSuffix(" s")
        self.time_spin.setValue(float(self.state.time_limit))
        self.time_spin.valueChanged.connect(self._update_estimate)
        self.controls.add_row("Time Limit", self.time_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2_000_000_000)
        self.seed_spin.setValue(int(self.state.seed))
        self.seed_spin.valueChanged.connect(self._update_seed_label)
        self.controls.add_row("Seed cơ sở", self.seed_spin)

        self.seeds_combo = QComboBox()
        for count in (1, 3, 5, 10):
            self.seeds_combo.addItem(str(count), count)
        self.seeds_combo.currentIndexChanged.connect(self._update_seed_label)
        self.controls.add_row("Số seed N (GA/SA)", self.seeds_combo)

        self.seeds_label = QLabel("")
        self.seeds_label.setObjectName("FieldNote")
        self.seeds_label.setWordWrap(True)
        self.controls.add_extra(self.seeds_label)

        self.estimate_label = QLabel("")
        self.estimate_label.setObjectName("FieldNote")
        self.controls.add_extra(self.estimate_label)

        self.run_button = QPushButton("Run Session")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.clicked.connect(self.run_session)
        self.reuse_button = QPushButton("Dùng kết quả Run All")
        self.reuse_button.setCursor(Qt.PointingHandCursor)
        self.reuse_button.setToolTip(self.REUSE_TOOLTIP)
        self.reuse_button.setEnabled(False)
        self.reuse_button.clicked.connect(self.load_run_all_results)
        self.export_button = QPushButton("Xuất")
        self.export_button.setMenu(self._build_export_menu())
        self.report_button = QPushButton("Xuất báo cáo")
        self.report_button.setMenu(self._build_report_menu())
        self.controls.add_buttons(
            self.run_button,
            self.reuse_button,
            self.export_button,
            self.report_button,
        )

        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress_label = QLabel("")
        self.elapsed_label = QLabel("")
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.elapsed_label)
        holder = QWidget()
        holder.setLayout(progress_row)
        self.controls.add_extra(holder)

        self._update_estimate()
        return self.controls

    def _build_export_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.addAction("CSV", lambda: self.export("csv"))
        menu.addAction("JSON", lambda: self.export("json"))
        menu.addAction("PNG", lambda: self.export("png"))
        menu.addAction("HTML", lambda: self.export("html"))
        return menu

    def _build_report_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.addAction("HTML (bắt buộc)", lambda: self.export("report_html"))
        menu.addAction("PDF (tùy chọn)", lambda: self.export("pdf"))
        return menu

    # ------------------------------------------------------------------
    def _on_problem_changed(self, problem) -> None:
        if problem is None:
            self.problem_label.setText("Bài toán: chưa chọn")
            self.run_button.setEnabled(False)
            self._refresh_reuse_state()
            return
        self.problem_label.setText(f"Bài toán: {self.state.problem_text()}")
        self.run_button.setEnabled(True)
        self._refresh_reuse_state()

    # ------------------------------------------------------------------
    # Dùng lại kết quả Run All từ trang Algorithm
    # ------------------------------------------------------------------
    def _run_all_matches_selection(self) -> bool:
        """Kết quả Run All có đúng bài/dataset đang chọn không."""
        snapshot = self.state.run_all_results
        if not snapshot:
            return False
        if (snapshot.get("dataset_file") or "") != (self.state.dataset_file or ""):
            return False
        if snapshot.get("batch"):
            if not self.state.is_batch:
                return False
            current = [problem.name for problem in self.state.problems]
            stored = [
                problem.name for problem in (snapshot.get("problems") or [])
            ]
            return bool(current) and current == stored
        if self.state.is_batch or self.state.problem is None:
            return False
        stored = snapshot.get("problem")
        return stored is not None and stored.name == self.state.problem.name

    def _refresh_reuse_state(self, *args) -> None:
        available = not self.state.running and self._run_all_matches_selection()
        self.reuse_button.setEnabled(available)
        if available:
            self.reuse_button.setToolTip(self.REUSE_TOOLTIP)
        elif self.state.running:
            self.reuse_button.setToolTip("Đang chạy, chưa thể nạp kết quả.")
        else:
            self.reuse_button.setToolTip(
                "Chạy Run All ở trang Algorithm cho bài đang chọn để bật nút này."
            )

    def _select_num_seeds(self, count: int) -> None:
        index = self.seeds_combo.findData(count)
        if index >= 0:
            self.seeds_combo.setCurrentIndex(index)

    def load_run_all_results(self) -> None:
        """Nạp kết quả Run All gần nhất vào trang so sánh, không chạy lại."""
        if self.state.running or self._thread is not None:
            return
        snapshot = self.state.run_all_results
        if not snapshot or not self._run_all_matches_selection():
            QMessageBox.information(
                self,
                "Chưa có kết quả Run All",
                "Hãy chạy Run All ở trang Algorithm cho đúng bài đang chọn trước.",
            )
            return

        time_limit = float(snapshot.get("time_limit") or self.state.time_limit)
        base_seed = int(snapshot.get("seed") or 0)
        self._run_dataset = snapshot.get("dataset_file", "")
        self._base_seed = base_seed
        self._num_seeds = 1
        self._saved_path = None
        self._current_session = None
        self._batch_problems = []
        self._batch_records = {}
        self._batch_index = 0
        self._batch_paths = []
        self._batch_comments = []
        self._records = {}
        self._current_rows = []
        self._log_lines = []
        self.state.time_limit = time_limit
        self.state.seed = base_seed
        self.state.num_seeds = 1
        self.state.viewing_saved_session = False

        self.time_spin.setValue(time_limit)
        self.seed_spin.setValue(base_seed)
        self._select_num_seeds(1)
        self.content_tabs.setTabVisible(5, False)
        self.content_tabs.setCurrentIndex(0)

        if snapshot.get("batch"):
            self._load_reused_batch(snapshot)
        else:
            self._load_reused_single(snapshot)
        self._refresh_reuse_state()

    def _load_reused_single(self, snapshot) -> None:
        problem = snapshot.get("problem")
        self._run_problem = problem
        self._records = analytics.copy_records(snapshot.get("records") or {})
        rows = analytics.build_rows(self._records, 1)
        self._current_rows = rows
        self.result_table.set_rows(rows)
        self._update_charts(rows)

        session, comments_list = self._build_reused_session(problem, self._records)
        self._current_session = session
        self.state.last_session = session
        self._saved_path = self._save_reused_session(session)
        if self._saved_path:
            self.banner.setText(
                "Đang dùng kết quả Run All gần nhất (GA/SA 1 seed, không chạy lại). "
                f"Đã lưu phiên so sánh tại {self._saved_path}."
            )
        else:
            self.banner.setText(
                "Đang dùng kết quả Run All gần nhất (không chạy lại); "
                "chưa lưu được phiên so sánh."
            )
        self.banner.setVisible(True)
        self._emit_analysis(session, comments_list)
        self.refresh_history()
        self.status_message.emit("Đã nạp kết quả Run All vào trang so sánh.")

    def _load_reused_batch(self, snapshot) -> None:
        problems = list(snapshot.get("problems") or [])
        self._batch_problems = problems
        self._batch_records = {
            name: analytics.copy_records(records)
            for name, records in (snapshot.get("batch_records") or {}).items()
        }
        self._batch_index = len(problems)
        combined = self._batch_rows()
        self._current_rows = combined
        self.result_table.set_rows(combined)
        self._update_charts(combined)

        last_session = None
        failures = 0
        for problem in problems:
            records = self._batch_records.get(problem.name) or {}
            session, comments_list = self._build_reused_session(problem, records)
            self._batch_comments.extend(
                f"{problem.name}: {line}" for line in comments_list
            )
            last_session = session
            path = self._save_reused_session(session)
            if path:
                self._batch_paths.append(path)
            else:
                failures += 1

        self._current_session = last_session
        if last_session is not None:
            self.state.last_session = last_session
        text = (
            f"Đang dùng kết quả Run All cho {len(problems)} bài (không chạy lại); "
            f"đã lưu {len(self._batch_paths)} phiên."
        )
        if failures:
            text += f" {failures} phiên lưu lỗi."
        self.banner.setText(text)
        self.banner.setVisible(True)
        if last_session is not None:
            self._emit_analysis(last_session, self._batch_comments)
        self.refresh_history()
        self.status_message.emit(
            f"Đã nạp kết quả Run All cho {len(problems)} bài vào trang so sánh."
        )

    def _build_reused_session(self, problem, records: dict):
        params = self._session_params(problem)
        rows = analytics.build_rows(records, self._num_seeds)
        comments_list = analytics.comments(rows, params)
        session = session_store.build_session(
            dataset_file=self._run_dataset,
            problem=problem,
            params=params,
            records=records,
            comments_list=comments_list,
        )
        return session, comments_list

    def _save_reused_session(self, session: dict):
        try:
            return str(session_store.save_session(session))
        except Exception as exc:  # noqa: BLE001 - vẫn hiển thị kết quả
            self._append_log(f"Không lưu được phiên: {exc}")
            return None

    def _selected_num_seeds(self) -> int:
        return int(self.seeds_combo.currentData())

    def _update_seed_label(self, *args) -> None:
        base = int(self.seed_spin.value())
        count = self._selected_num_seeds()
        seeds = analytics.seeds_for(base, count)
        self.seeds_label.setText(
            "Seed dùng cho GA/SA: " + ", ".join(str(seed) for seed in seeds)
        )
        self._update_estimate()

    def _update_estimate(self, *args) -> None:
        count = self._selected_num_seeds()
        seconds = analytics.estimate_seconds(self.time_spin.value(), count)
        text = (
            f"Ước tính tối đa: {analytics.fmt_duration(seconds)} "
            f"= T × (2N + 2), tổng {2 * count + 2} lượt."
        )
        if seconds > 120:
            text += " Sẽ hỏi xác nhận trước khi chạy."
        self.estimate_label.setText(text)

    # ------------------------------------------------------------------
    def _set_running(self, running: bool) -> None:
        self.state.running = running
        self.running_changed.emit(running)
        for widget in (
            self.time_spin,
            self.seed_spin,
            self.seeds_combo,
            self.run_button,
            self.reuse_button,
            self.export_button,
            self.report_button,
        ):
            widget.setEnabled(not running)
        if not running:
            self._refresh_reuse_state()
        self.progress.setVisible(running)
        self.progress_label.setVisible(running)
        self.elapsed_label.setVisible(running)

    def _update_clock(self) -> None:
        elapsed = time.perf_counter() - self._started_at
        self.elapsed_label.setText(f"Đã chạy {elapsed:.0f} s")

    # ------------------------------------------------------------------
    def run_session(self) -> None:
        if self.state.running or self._thread is not None:
            return
        if self.state.problem is None:
            self._ask_for_problem()
            return

        count = self._selected_num_seeds()
        time_limit = float(self.time_spin.value())
        base_seed = int(self.seed_spin.value())
        batch = self.state.is_batch
        problems = list(self.state.problems) if batch else [self.state.problem]
        plan = analytics.build_plan(base_seed, count)
        seconds = analytics.estimate_seconds(time_limit, count) * len(problems)
        detail = f" cho {len(problems)} bài" if batch else ""
        if seconds > 120:
            confirmed = ask_confirm(
                self,
                "Phiên chạy dài",
                f"Ước tính tối đa {analytics.fmt_duration(seconds)}{detail}. "
                "Tiếp tục chạy?",
                accept="Tiếp tục",
                reject="Hủy",
            )
            if not confirmed:
                return

        self._run_problem = problems[0]
        self._run_dataset = self.state.dataset_file
        self._base_seed = base_seed
        self._num_seeds = count
        self._total_runs = len(plan) * len(problems)
        self._batch_problems = problems if batch else []
        self._batch_index = 0
        self._batch_records = {}
        self._batch_paths = []
        self._batch_comments = []
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self._current_rows = []
        self._current_session = None
        self._saved_path = None
        self._log_lines = []
        self.banner.setVisible(False)
        self.state.viewing_saved_session = False
        self.state.time_limit = time_limit
        self.state.seed = base_seed
        self.state.num_seeds = count

        self.result_table.clear()
        for chart in self._charts():
            chart.show_placeholder("Đang chạy phiên…")
        self.content_tabs.setTabVisible(5, False)
        self.content_tabs.setCurrentIndex(0)
        self._set_running(True)
        self.progress.setRange(0, self._total_runs)
        self.progress.setValue(0)
        self.progress_label.setText(f"0/{self._total_runs}")
        self._started_at = time.perf_counter()
        self._clock.start()
        title = f"Batch {len(problems)} bài" if batch else self._run_problem.name
        self.status_message.emit(
            f"Bắt đầu phiên ({title}): N={count}, T={time_limit:g}s."
        )
        self._launch_session_worker(self._run_problem, plan, time_limit)

    def _launch_session_worker(self, problem, plan, time_limit: float) -> None:
        worker = SessionWorker(plan, problem, time_limit)
        worker.progress.connect(self._on_progress)
        worker.run_done.connect(self._on_run_done)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.log.connect(self._append_log)
        self._launch(worker)

    def _batch_rows(self) -> list[dict]:
        rows = []
        for problem in self._batch_problems:
            records = self._batch_records.get(problem.name)
            if not records:
                continue
            for row in analytics.build_rows(records, self._num_seeds):
                rows.append(
                    {
                        **row,
                        "label": f"{problem.name} · {row['label']}",
                        "problem": problem.name,
                    }
                )
        return rows

    def _runs_per_problem(self) -> int:
        return len(analytics.build_plan(self._base_seed, self._num_seeds))

    def _launch(self, worker) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_thread_finished(self) -> None:
        if self.sender() is not self._thread:
            return
        self._thread = None
        self._worker = None

    def _on_progress(self, done: int, total: int, label: str) -> None:
        if self._batch_problems:
            done = self._batch_index * self._runs_per_problem() + done
            total = self._total_runs
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        self.progress_label.setText(f"{done}/{total} — {label}")
        if done < total:
            self.status_message.emit(f"Phiên: {done}/{total} lượt — {label}")

    def _on_run_done(self, algorithm: str, seed: int, record: dict) -> None:
        self._records[algorithm].append(record)
        if self._batch_problems:
            problem = self._batch_problems[self._batch_index]
            self._batch_records[problem.name] = self._records
            rows = self._batch_rows()
            done = self._batch_index * self._runs_per_problem() + sum(
                len(runs) for runs in self._records.values()
            )
        else:
            rows = analytics.build_rows(self._records, self._num_seeds)
            done = sum(len(runs) for runs in self._records.values())
        self._current_rows = rows
        self.result_table.set_rows(rows)
        self.progress.setRange(0, max(1, self._total_runs))
        self.progress.setValue(done)
        self.progress_label.setText(f"{done}/{self._total_runs}")

    def _on_finished(self, outcomes) -> None:
        if self._batch_problems:
            self._finish_batch_problem()
            return
        self._clock.stop()
        self.progress.setValue(self._total_runs)
        self._set_running(False)
        rows = analytics.build_rows(self._records, self._num_seeds)
        self._current_rows = rows
        self.result_table.set_rows(rows)
        self._update_charts(rows)

        params = self._session_params()
        comments_list = analytics.comments(rows, params)
        session = session_store.build_session(
            dataset_file=self._run_dataset,
            problem=self._run_problem,
            params=params,
            records=self._records,
            comments_list=comments_list,
        )
        self._current_session = session
        self.state.last_session = session
        self.state.viewing_saved_session = False

        try:
            self._saved_path = str(session_store.save_session(session))
            self.status_message.emit(f"Đã lưu phiên vào {self._saved_path}.")
        except Exception as exc:  # noqa: BLE001 - báo lỗi, giữ kết quả
            self._saved_path = None
            QMessageBox.critical(
                self,
                "Không lưu được phiên",
                f"Kết quả vẫn hiển thị nhưng không ghi được phiên:\n{exc}",
            )
            self.status_message.emit("Phiên chạy xong nhưng lưu thất bại.")

        self.banner.setVisible(False)
        self._emit_analysis(session, comments_list)
        self.refresh_history()
        self.status_message.emit("Phiên so sánh hoàn tất.")

    def _finish_batch_problem(self) -> None:
        problem = self._batch_problems[self._batch_index]
        self._batch_records[problem.name] = self._records
        rows = analytics.build_rows(self._records, self._num_seeds)
        self._current_rows = rows
        self.result_table.set_rows(rows)
        self._update_charts(rows)

        params = self._session_params()
        comments = analytics.comments(rows, params)
        self._batch_comments.extend(f"{problem.name}: {c}" for c in comments)
        session = session_store.build_session(
            dataset_file=self._run_dataset,
            problem=problem,
            params=params,
            records=self._records,
            comments_list=comments,
        )
        self._current_session = session
        self.state.last_session = session
        self.state.viewing_saved_session = False
        try:
            self._batch_paths.append(str(session_store.save_session(session)))
        except Exception as exc:  # noqa: BLE001 - báo lỗi, giữ kết quả
            QMessageBox.critical(
                self,
                "Không lưu được phiên",
                f"Không ghi được phiên của {problem.name}:\n{exc}",
            )

        self._batch_index += 1
        if self._batch_index < len(self._batch_problems):
            next_problem = self._batch_problems[self._batch_index]
            self._run_problem = next_problem
            self._records = {name: [] for name in analytics.ALGORITHMS}
            self.result_table.clear()
            for chart in self._charts():
                chart.show_placeholder("Đang chạy phiên…")
            self.content_tabs.setTabVisible(5, False)
            self.content_tabs.setCurrentIndex(0)
            self.progress.setValue(self._batch_index * self._runs_per_problem())
            self.status_message.emit(
                f"Batch: {self._batch_index}/{len(self._batch_problems)} bài — "
                f"{next_problem.name}."
            )
            plan = analytics.build_plan(self._base_seed, self._num_seeds)
            self._launch_session_worker(
                next_problem, plan, float(self.state.time_limit)
            )
            return

        self._clock.stop()
        self.progress.setValue(self._total_runs)
        self._set_running(False)
        combined = self._batch_rows()
        self._current_rows = combined
        self.result_table.set_rows(combined)
        self._update_charts(combined)
        self.banner.setText(
            f"Đã lưu {len(self._batch_paths)} phiên cho "
            f"{len(self._batch_problems)} bài."
        )
        self.banner.setVisible(True)
        self._emit_analysis(session, self._batch_comments)
        self.refresh_history()
        self.status_message.emit(
            f"Phiên so sánh batch hoàn tất: {len(self._batch_problems)} bài."
        )

    def _on_failed(self, name: str, message: str) -> None:
        self._clock.stop()
        self._set_running(False)
        self._append_log(f"Lỗi phiên: {message}")
        QMessageBox.critical(self, "Lỗi phiên", message)
        self.status_message.emit(f"Lỗi phiên: {message}")

    def _append_log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self._log_lines.append(f"[{stamp}] {message}")
        self._log_lines = self._log_lines[-200:]

    # ------------------------------------------------------------------
    def _charts(self):
        return (
            self.chart_profit,
            self.chart_gap,
            self.chart_runtime,
            self.chart_convergence,
            self.chart_memory,
        )

    def _update_charts(self, rows) -> None:
        self.chart_profit.plot_bars(rows, "profit", "Profit theo thuật toán")
        self.chart_gap.plot_bars(rows, "gap", "Gap (%)")
        self.chart_runtime.plot_bars(rows, "runtime", "Runtime trung bình", "Giây")
        self.chart_convergence.plot_convergence(rows)
        has_memory = any(row.get("peak_memory") for row in rows)
        self.content_tabs.setTabVisible(5, has_memory)
        if has_memory:
            self.chart_memory.plot_bars(rows, "memory", "Bộ nhớ đỉnh", "MB")
        else:
            self.chart_memory.show_placeholder("Không có dữ liệu bộ nhớ")

    def _session_params(self, problem=None) -> dict:
        problem = problem if problem is not None else self._run_problem
        return {
            "time_limit": float(self.time_spin.value()),
            "base_seed": int(self._base_seed),
            "num_seeds": int(self._num_seeds),
            "seeds": analytics.seeds_for(self._base_seed, self._num_seeds),
            "problem_name": getattr(problem, "name", "-"),
            "z_ref": getattr(problem, "z_ref", None),
        }

    def _emit_analysis(self, session: dict, comments_list: list[str]) -> None:
        problem = session.get("problem") or {}
        params = session.get("params") or {}
        seeds = ", ".join(str(seed) for seed in (params.get("seeds") or []))
        body = [
            "<p><b>Nhận xét tự động</b></p><ul>",
        ]
        for line in comments_list:
            body.append(f"<li>{html.escape(line)}</li>")
        body.append("</ul>")
        body.append("<p><b>Tham số phiên</b></p><ul>")
        body.append(f"<li>Dataset: {html.escape(str(problem.get('file', '-')))}</li>")
        body.append(f"<li>Bài toán: {html.escape(str(problem.get('name', '-')))}</li>")
        body.append(f"<li>Time limit: {params.get('time_limit', '-')} giây</li>")
        body.append(f"<li>Seed cơ sở: {params.get('base_seed', '-')}</li>")
        body.append(f"<li>Số seed: {params.get('num_seeds', '-')} ({seeds})</li>")
        body.append(f"<li>Thời điểm: {html.escape(str(session.get('created_at', '-')))}</li>")
        body.append("</ul>")
        if self._saved_path:
            body.append(
                f"<p>Đã lưu vào: <code>{html.escape(self._saved_path)}</code></p>"
            )
        self.analysis_requested.emit(self.PAGE_TITLE, "\n".join(body))

    def analysis_snapshot(self):
        if self._current_session is None:
            return self.PAGE_TITLE, self.ANALYSIS_HTML
        comments_list = self._current_session.get("comments") or []
        return self.PAGE_TITLE, self._analysis_html(self._current_session, comments_list)

    @staticmethod
    def _analysis_html(session: dict, comments_list: list[str]) -> str:
        problem = session.get("problem") or {}
        params = session.get("params") or {}
        seeds = ", ".join(str(seed) for seed in (params.get("seeds") or []))
        body = ["<p><b>Nhận xét tự động</b></p><ul>"]
        for line in comments_list:
            body.append(f"<li>{html.escape(str(line))}</li>")
        body.append("</ul><p><b>Tham số phiên</b></p><ul>")
        body.append(f"<li>Dataset: {html.escape(str(problem.get('file', '-')))}</li>")
        body.append(f"<li>Bài toán: {html.escape(str(problem.get('name', '-')))}</li>")
        body.append(f"<li>Time limit: {params.get('time_limit', '-')} giây</li>")
        body.append(f"<li>Seed cơ sở: {params.get('base_seed', '-')}</li>")
        body.append(f"<li>Số seed: {params.get('num_seeds', '-')} ({seeds})</li>")
        body.append(f"<li>Thời điểm: {html.escape(str(session.get('created_at', '-')))}</li>")
        body.append("</ul>")
        return "\n".join(body)

    # ------------------------------------------------------------------
    def refresh_history(self) -> None:
        items = []
        for entry in session_store.list_sessions():
            created = entry.get("created_at", "").replace("T", " ")
            items.append(
                {
                    **entry,
                    "label": (
                        f"{created} — {entry.get('problem', '-')} — "
                        f"T={entry.get('time_limit', '-')}s — "
                        f"N={entry.get('num_seeds', '-')}"
                    ),
                }
            )
        self.history_list_changed.emit(items)

    def open_session(self, path: str) -> None:
        if self.state.running:
            return
        try:
            session = session_store.load_session(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Không mở được phiên", str(exc))
            return
        self._current_session = session
        self._saved_path = str(Path(path))
        self.state.last_session = session
        self.state.viewing_saved_session = True
        params = session.get("params") or {}
        self._base_seed = int(params.get("base_seed", 0))
        self._num_seeds = int(params.get("num_seeds", 1))
        self.time_spin.setValue(float(params.get("time_limit", 60)))
        self.seed_spin.setValue(self._base_seed)
        index = self.seeds_combo.findData(self._num_seeds)
        if index >= 0:
            self.seeds_combo.setCurrentIndex(index)
        self._records = session_store.records_from_session(session)
        rows = session_store.rows_from_session(session)
        self._current_rows = rows
        self.result_table.set_rows(rows)
        self._update_charts(rows)
        comments_list = session.get("comments") or analytics.comments(
            rows,
            {
                "time_limit": params.get("time_limit", 0),
                "num_seeds": params.get("num_seeds", 1),
                "seeds": params.get("seeds", []),
                "problem_name": (session.get("problem") or {}).get("name", "-"),
                "z_ref": (session.get("problem") or {}).get("z_ref"),
            },
        )
        created = str(session.get("created_at", "")).replace("T", " ")
        self.banner.setText(
            f"Kết quả đã lưu ngày {created}. Đang xem lại phiên cũ; "
            "không trộn với phiên mới."
        )
        self.banner.setVisible(True)
        self._emit_analysis(session, comments_list)
        self.status_message.emit(f"Đang xem lại phiên đã lưu: {Path(path).parent.name}")

    def delete_session(self, path: str) -> None:
        confirmed = ask_confirm(
            self,
            "Xóa phiên",
            "Xóa toàn bộ thư mục phiên này?",
            accept="Xóa",
            reject="Hủy",
            icon=QMessageBox.Warning,
        )
        if not confirmed:
            return
        try:
            session_store.delete_session(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Không xóa được", str(exc))
            return
        if self._saved_path and Path(self._saved_path) == Path(path):
            self._saved_path = None
            self.banner.setVisible(False)
            self.state.viewing_saved_session = False
        self.refresh_history()
        self.status_message.emit("Đã xóa phiên.")

    def open_sessions_folder(self) -> None:
        try:
            session_store.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            session_store.open_folder(session_store.SESSIONS_DIR)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Không mở được thư mục", str(exc))

    # ------------------------------------------------------------------
    def export(self, kind: str) -> None:
        if self._current_session is None:
            QMessageBox.information(
                self, "Chưa có phiên", "Hãy chạy Run Session hoặc mở một phiên đã lưu."
            )
            return
        problem_name = (self._current_session.get("problem") or {}).get("name", "mknap")
        stem = f"mknap_{problem_name}_{datetime.now():%Y%m%d_%H%M%S}"
        filters = {
            "csv": ("CSV (*.csv)", ".csv"),
            "json": ("JSON (*.json)", ".json"),
            "png": ("PNG (*.png)", ".png"),
            "html": ("HTML (*.html)", ".html"),
            "report_html": ("HTML (*.html)", ".html"),
            "pdf": ("PDF (*.pdf)", ".pdf"),
        }
        caption, suffix = filters[kind]
        target, _ = QFileDialog.getSaveFileName(
            self, "Xuất kết quả", str(Path(self._last_directory) / (stem + suffix)), caption
        )
        if not target:
            return
        self._last_directory = str(Path(target).parent)
        try:
            if kind == "csv":
                session_store.export_csv(self._current_session, target)
            elif kind == "json":
                session_store.export_json(self._current_session, target)
            elif kind == "png":
                session_store.export_png(self._current_session, target)
            elif kind in ("html", "report_html"):
                session_store.export_html(self._current_session, target)
            elif kind == "pdf":
                png_bytes = None
                try:
                    png_bytes = session_store.render_png_bytes(self._current_session)
                except Exception:  # noqa: BLE001
                    png_bytes = None
                html_text = session_store.render_html(self._current_session, png_bytes)
                session_store.export_pdf(html_text, target)
            self.status_message.emit(f"Đã xuất {kind.upper()}: {target}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Xuất thất bại", str(exc))
            self.status_message.emit(f"Xuất {kind.upper()} thất bại.")

    # ------------------------------------------------------------------
    def _ask_for_problem(self) -> None:
        self.status_message.emit("Chưa chọn bài toán — hãy chọn ở trang Dataset.")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Chưa chọn bài toán")
        box.setText("Hãy chọn bài toán ở trang Dataset trước khi chạy phiên.")
        go_button = box.addButton("Sang trang Dataset", QMessageBox.AcceptRole)
        box.addButton("Đóng", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is go_button:
            self.navigate_requested.emit(1)

    def run_primary_action(self) -> None:
        self.run_session()

    def stop_replay(self) -> None:
        for chart in self._charts():
            chart.stop_replay()
