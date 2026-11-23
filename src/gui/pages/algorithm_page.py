import html
import time

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui import analytics
from src.gui.app_state import AppState
from src.gui.widgets.chart_widget import ChartWidget
from src.gui.widgets.control_panel import ControlPanel
from src.gui.widgets.result_panel import ResultTable, SingleResultDetails
from src.gui.workers.algorithm_worker import AlgorithmWorker, SessionWorker

DESCRIPTIONS = {
    "greedy": (
        "Chọn vật phẩm theo tỷ lệ lợi nhuận trên tài nguyên, cập nhật thích nghi "
        "theo tài nguyên còn lại. Không dùng seed."
    ),
    "dynamic_programming": (
        "Quy hoạch động trên tầng trạng thái tài nguyên; có thể dừng khi vượt "
        "giới hạn bộ nhớ. Không dùng seed."
    ),
    "genetic_algorithm": (
        "Tiến hóa quần thể lời giải qua chọn lọc, lai ghép và đột biến; kết quả "
        "phụ thuộc seed."
    ),
    "simulated_annealing": (
        "Duyệt lời giải lân cận với xác suất chấp nhận giảm dần; kết quả phụ "
        "thuộc seed."
    ),
}


class AlgorithmPage(QWidget):
    PAGE_TITLE = "Algorithm"
    ANALYSIS_HTML = """
    <p><b>Trang thực thi</b></p>
    <p>Chọn thuật toán, đặt Time Limit và Seed, bấm Run để chạy. Kết quả và
    đường hội tụ hiển thị ở khu vực chính.</p>
    """

    analysis_requested = Signal(str, str)
    status_message = Signal(str)
    algorithm_text = Signal(str)
    running_changed = Signal(bool)
    navigate_requested = Signal(int)

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._thread = None
        self._worker = None
        self._run_mode = None
        self._started_at = 0.0
        self._time_limit = float(state.time_limit)
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self._batch_problems = []
        self._batch_index = 0
        self._batch_records = {}
        self._log_lines = []

        self._clock = QTimer(self)
        self._clock.setInterval(200)
        self._clock.timeout.connect(self._update_clock)

        self._build_ui()
        self._on_problem_changed(state.problem)
        state.problem_changed.connect(self._on_problem_changed)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        title = QLabel(self.PAGE_TITLE)
        title.setObjectName("PageTitle")
        hint = QLabel("Chọn bài toán ở trang Dataset để bắt đầu.")
        hint.setObjectName("PageHint")
        hint.setWordWrap(True)
        self.problem_label = QLabel("Bài toán: chưa chọn")
        self.problem_label.setObjectName("ProblemLine")
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.problem_label)

        layout.addWidget(self._build_controls())
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_single_view())
        self.stack.addWidget(self._build_multi_view())
        layout.addWidget(self.stack, 1)

    def _build_controls(self) -> QWidget:
        self.controls = ControlPanel("Điều khiển")
        self.algo_combo = QComboBox()
        for name in analytics.ALGORITHMS:
            self.algo_combo.addItem(analytics.SHORT_LABELS[name], name)
        self.algo_combo.currentIndexChanged.connect(self._on_algorithm_changed)
        self.controls.add_row("Thuật toán", self.algo_combo)

        self.time_spin = QDoubleSpinBox()
        self.time_spin.setRange(0.1, 3600.0)
        self.time_spin.setDecimals(1)
        self.time_spin.setValue(float(self.state.time_limit))
        self.time_spin.setSuffix(" s")
        self.controls.add_row("Time Limit", self.time_spin)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 2_000_000_000)
        self.seed_spin.setValue(int(self.state.seed))
        self.controls.add_row("Seed", self.seed_spin)
        self.seed_note = self.controls.add_note("Greedy không dùng seed.")

        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.clicked.connect(self.run_single)
        self.run_all_button = QPushButton("Run All")
        self.run_all_button.setCursor(Qt.PointingHandCursor)
        self.run_all_button.clicked.connect(self.run_all)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset)
        self.controls.add_buttons(
            self.run_button, self.run_all_button, self.reset_button
        )

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.elapsed_label = QLabel("")
        self.remaining_label = QLabel("")
        clock_row = QHBoxLayout()
        clock_row.setSpacing(12)
        clock_row.addWidget(self.progress, 1)
        clock_row.addWidget(self.elapsed_label)
        clock_row.addWidget(self.remaining_label)
        clock_holder = QWidget()
        clock_holder.setLayout(clock_row)
        self.controls.add_extra(clock_holder)

        replay_row = QHBoxLayout()
        replay_row.setSpacing(8)
        replay_row.addWidget(self._field_label("Tốc độ phát lại"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(1)
        self.speed_label = QLabel("1×")
        self.speed_slider.valueChanged.connect(
            lambda value: self.speed_label.setText(f"{value}×")
        )
        self.replay_button = QPushButton("Phát lại")
        self.replay_button.setEnabled(False)
        self.replay_button.clicked.connect(
            lambda: self.chart_single.start_replay(self.speed_slider.value())
        )
        replay_row.addWidget(self.speed_slider, 1)
        replay_row.addWidget(self.speed_label)
        replay_row.addWidget(self.replay_button)
        replay_holder = QWidget()
        replay_holder.setLayout(replay_row)
        self.controls.add_extra(replay_holder)

        self._on_algorithm_changed(self.algo_combo.currentIndex())
        return self.controls

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _build_single_view(self) -> QWidget:
        holder = QSplitter(Qt.Horizontal)
        holder.setChildrenCollapsible(False)
        self.details = SingleResultDetails()
        details_scroll = QScrollArea()
        details_scroll.setObjectName("DetailsScroll")
        details_scroll.setWidget(self.details)
        details_scroll.setWidgetResizable(True)
        details_scroll.setFrameShape(QFrame.NoFrame)
        details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        details_scroll.viewport().setObjectName("DetailsViewport")
        details_scroll.viewport().setAutoFillBackground(False)
        self.details_scroll = details_scroll
        self.chart_single = ChartWidget()
        self.chart_single.show_placeholder("Bấm Run để xem đường hội tụ")
        holder.addWidget(details_scroll)
        holder.addWidget(self.chart_single)
        holder.setStretchFactor(0, 2)
        holder.setStretchFactor(1, 3)
        holder.setSizes([320, 420])
        return holder

    def _build_multi_view(self) -> QWidget:
        self.multi_tabs = QTabWidget()
        self.result_table = ResultTable(
            "Kết quả Run All (dùng lại được ở trang Comparison)",
            "Chưa có kết quả — bấm Run All để bắt đầu.",
        )
        self.chart_multi = ChartWidget()
        self.chart_multi.show_placeholder("Bấm Run All để so sánh 4 thuật toán")
        self.multi_tabs.addTab(self.result_table, "Bảng kết quả")
        self.multi_tabs.addTab(self.chart_multi, "Hội tụ")
        self.multi_tabs.currentChanged.connect(self._on_multi_tab_changed)
        return self.multi_tabs

    def _on_multi_tab_changed(self, index: int) -> None:
        if self.multi_tabs.widget(index) is self.chart_multi:
            self.chart_multi.canvas.draw_idle()

    # ------------------------------------------------------------------
    def _on_algorithm_changed(self, index: int) -> None:
        algorithm = self.algo_combo.itemData(index)
        is_greedy = algorithm == "greedy"
        self.seed_spin.setEnabled(not is_greedy)
        self.seed_note.setText(
            "Greedy không dùng seed."
            if is_greedy
            else "Greedy/DP không dùng seed; GA/SA dùng seed để tái lập."
        )

    def _on_problem_changed(self, problem) -> None:
        if problem is None:
            self.problem_label.setText("Bài toán: chưa chọn")
            self.run_button.setEnabled(False)
            self.run_all_button.setEnabled(False)
            return
        self.problem_label.setText(f"Bài toán: {self.state.problem_text()}")
        self.run_button.setEnabled(True)
        self.run_all_button.setEnabled(True)

    # ------------------------------------------------------------------
    def _set_running(self, running: bool) -> None:
        self.state.running = running
        self.running_changed.emit(running)
        for widget in (
            self.algo_combo,
            self.time_spin,
            self.seed_spin,
            self.run_button,
            self.run_all_button,
            self.reset_button,
        ):
            widget.setEnabled(not running)
        if not running:
            self._on_algorithm_changed(self.algo_combo.currentIndex())
        self.progress.setVisible(running)
        self.elapsed_label.setVisible(running)
        self.remaining_label.setVisible(running)
        if running:
            self.replay_button.setEnabled(False)

    def _start_clock(self, estimated: float) -> None:
        self._estimated = max(0.0, estimated)
        self._started_at = time.perf_counter()
        self.elapsed_label.setText("Đã chạy 0,0 s")
        self.remaining_label.setText(
            f"Còn tối đa {self._estimated:.0f} s" if self._estimated else ""
        )
        self._clock.start()

    def _stop_clock(self) -> None:
        self._clock.stop()

    def _update_clock(self) -> None:
        elapsed = time.perf_counter() - self._started_at
        self.elapsed_label.setText(f"Đã chạy {elapsed:.1f} s".replace(".", ","))
        if self._estimated:
            remaining = max(0.0, self._estimated - elapsed)
            self.remaining_label.setText(f"Còn tối đa {remaining:.0f} s")
        if self._run_mode == "all" and self._total_runs:
            done = self._records_count()
            self.progress.setValue(min(done, self._total_runs))

    def _records_count(self) -> int:
        return sum(len(runs) for runs in self._records.values())

    # ------------------------------------------------------------------
    def run_single(self) -> None:
        if self.state.problem is None:
            self._ask_for_problem()
            return
        if self.state.running or self._thread is not None:
            return
        algorithm = self.algo_combo.currentData()
        time_limit = float(self.time_spin.value())
        seed = int(self.seed_spin.value())
        problem = self.state.problem
        self._run_problem = problem
        self.state.time_limit = time_limit
        self.state.seed = seed

        self._run_mode = "single"
        self._log_lines = []
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self.details.clear()
        self.chart_single.show_placeholder("Đang chạy…")
        self.chart_single.stop_replay(redraw=False)
        self.replay_button.setEnabled(False)
        self.stack.setCurrentIndex(0)
        self._set_running(True)
        self.progress.setRange(0, 0)
        self._start_clock(time_limit)
        self.algorithm_text.emit(analytics.SHORT_LABELS.get(algorithm, algorithm))
        self.status_message.emit(
            f"Đang chạy {analytics.label_for(algorithm)} trên {problem.name}…"
        )
        self._append_log(
            f"Bắt đầu {analytics.label_for(algorithm)} — "
            f"{problem.name} (T={time_limit:g}s, seed={seed})."
        )

        worker = AlgorithmWorker(algorithm, problem, time_limit, seed)
        worker.started.connect(lambda name: self.algorithm_text.emit(analytics.label_for(name)))
        worker.log.connect(self._append_log)
        worker.finished.connect(self._on_single_finished)
        worker.failed.connect(self._on_failed)
        self._launch(worker)

    def run_all(self) -> None:
        if self.state.problem is None:
            self._ask_for_problem()
            return
        if self.state.running or self._thread is not None:
            return
        time_limit = float(self.time_spin.value())
        seed = int(self.seed_spin.value())
        problems = list(self.state.problems) if self.state.is_batch else [self.state.problem]
        if not problems:
            self._ask_for_problem()
            return
        problem = problems[0]
        self._run_problem = problem
        self.state.time_limit = time_limit
        self.state.seed = seed

        batch = self.state.is_batch
        plan = [(name, seed) for name in analytics.ALGORITHMS]
        self.state.set_run_all_results(None)
        self._run_mode = "batch" if batch else "all"
        self._batch_problems = problems if batch else []
        self._batch_index = 0
        self._batch_records = {}
        self._total_runs = len(problems) * len(plan)
        self._log_lines = []
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self.result_table.clear()
        self.chart_multi.show_placeholder("Đang chạy Run All…")
        self.multi_tabs.setCurrentIndex(0)
        self.stack.setCurrentIndex(1)
        self._set_running(True)
        self.progress.setRange(0, self._total_runs)
        self.progress.setValue(0)
        self._start_clock(time_limit * self._total_runs)
        title = f"Batch ({len(problems)} bài × {len(plan)} thuật toán)" if batch else "Run All"
        self.status_message.emit(f"Đang chạy {title}…")
        self._append_log(f"Bắt đầu {title} trên {problem.name}.")
        self._launch_all_worker(problem, plan, time_limit)

    def _launch_all_worker(self, problem, plan, time_limit: float) -> None:
        worker = SessionWorker(plan, problem, time_limit)
        worker.log.connect(self._append_log)
        worker.progress.connect(self._on_all_progress)
        worker.run_done.connect(self._on_all_run_done)
        worker.finished.connect(self._on_all_finished)
        worker.failed.connect(self._on_failed)
        self._launch(worker)

    def _batch_rows(self) -> list[dict]:
        rows = []
        for problem in self._batch_problems:
            records = self._batch_records.get(problem.name)
            if not records:
                continue
            for row in analytics.build_rows(records, 1):
                rows.append(
                    {
                        **row,
                        "label": f"{problem.name} · {row['label']}",
                        "problem": problem.name,
                    }
                )
        return rows

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
        if self.sender() is self._thread:
            self._thread = None
            self._worker = None

    # ------------------------------------------------------------------
    def _on_single_finished(self, algorithm: str, result) -> None:
        if self._run_mode != "single":
            return
        self._stop_clock()
        self._set_running(False)
        record = analytics.run_record(result, int(self.seed_spin.value()))
        self._records[algorithm] = [record]
        self.state.last_result = result
        self.details.show_result(self._run_problem, result)
        self.chart_single.plot_history(
            result, f"Hội tụ — {analytics.label_for(algorithm)}"
        )
        self.replay_button.setEnabled(self.chart_single.has_history)
        self._append_log(
            f"Hoàn tất: profit={analytics.fmt_number(record['profit'])}, "
            f"gap={analytics.fmt_percent(record['gap'])}, "
            f"status={record['status']}."
        )
        self.status_message.emit(
            f"Xong {analytics.label_for(algorithm)} — "
            f"profit {analytics.fmt_number(record['profit'])}."
        )
        self._emit_analysis(summary="single")
        self._run_mode = None

    def _on_all_progress(self, done: int, total: int, label: str) -> None:
        if self._run_mode == "batch":
            done = self._batch_index * len(analytics.ALGORITHMS) + done
            total = self._total_runs
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(done)
        if done < total:
            self.status_message.emit(f"Run All: {done}/{total} lượt — {label}")

    def _on_all_run_done(self, algorithm: str, seed: int, record: dict) -> None:
        self._records[algorithm].append(record)
        if self._run_mode == "batch":
            problem = self._batch_problems[self._batch_index]
            self._batch_records[problem.name] = self._records
            self.result_table.set_rows(self._batch_rows())
            return
        rows = analytics.build_rows(self._records, 1)
        self.result_table.set_rows(rows)

    def _on_all_finished(self, outcomes) -> None:
        if self._run_mode not in ("all", "batch"):
            return
        if self._run_mode == "batch":
            problem = self._batch_problems[self._batch_index]
            self._batch_records[problem.name] = self._records
            self._batch_index += 1
            if self._batch_index < len(self._batch_problems):
                next_problem = self._batch_problems[self._batch_index]
                self._records = {name: [] for name in analytics.ALGORITHMS}
                self.progress.setValue(self._batch_index * len(analytics.ALGORITHMS))
                self.status_message.emit(
                    f"Batch: {self._batch_index}/{len(self._batch_problems)} bài — "
                    f"{next_problem.name}"
                )
                self._append_log(
                    f"Xong bài {problem.name}; bắt đầu {next_problem.name}."
                )
                plan = [
                    (name, int(self.seed_spin.value())) for name in analytics.ALGORITHMS
                ]
                self._launch_all_worker(
                    next_problem, plan, float(self.time_spin.value())
                )
                return
            title = f"Batch ({len(self._batch_problems)} bài)"
            rows = self._batch_rows()
        else:
            title = "Run All"
            rows = analytics.build_rows(self._records, 1)
        self._stop_clock()
        self.progress.setValue(self._total_runs)
        self._set_running(False)
        self.result_table.set_rows(rows)
        self.chart_multi.plot_convergence(rows)
        self._append_log(f"{title} hoàn tất.")
        self.status_message.emit(f"{title} hoàn tất.")
        self._emit_analysis(summary="all", rows=rows)
        self._publish_run_all()
        self._run_mode = None

    def _publish_run_all(self) -> None:
        """Chia sẻ kết quả Run All để trang Comparison dùng lại."""
        time_limit = float(self.time_spin.value())
        seed = int(self.seed_spin.value())
        if self._run_mode == "batch":
            snapshot = {
                "batch": True,
                "dataset_file": self.state.dataset_file,
                "problem": None,
                "problems": list(self._batch_problems),
                "records": {},
                "batch_records": {
                    name: analytics.copy_records(per_algo)
                    for name, per_algo in self._batch_records.items()
                },
                "time_limit": time_limit,
                "seed": seed,
            }
        else:
            snapshot = {
                "batch": False,
                "dataset_file": self.state.dataset_file,
                "problem": self._run_problem,
                "problems": [],
                "records": analytics.copy_records(self._records),
                "batch_records": {},
                "time_limit": time_limit,
                "seed": seed,
            }
        self.state.set_run_all_results(snapshot)

    def _on_failed(self, algorithm: str, message: str) -> None:
        self._stop_clock()
        self._set_running(False)
        label = analytics.label_for(algorithm)
        self._append_log(f"Lỗi ({label}): {message}")
        self.details.show_error(message)
        self.status_message.emit(f"Lỗi khi chạy {label}: {message}")
        self._emit_analysis(summary="error", error=message)
        self._run_mode = None

    # ------------------------------------------------------------------
    def _append_log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self._log_lines.append(f"[{stamp}] {message}")
        self._log_lines = self._log_lines[-300:]
        self._emit_analysis()

    def _emit_analysis(self, summary: str | None = None, rows=None, error: str | None = None) -> None:
        algorithm = self.algo_combo.currentData()
        body = [f"<p><b>{html.escape(analytics.LONG_LABELS[algorithm])}</b></p>"]
        body.append(f"<p>{html.escape(DESCRIPTIONS[algorithm])}</p>")
        body.append(
            f"<p>Time Limit: {self.time_spin.value():g} giây; "
            f"Seed: {self.seed_spin.value()} (Greedy/DP bỏ qua seed).</p>"
        )
        if rows:
            body.append("<p><b>Tóm tắt Run All</b></p><ul>")
            for row in rows:
                body.append(
                    f"<li>{row['label']}: profit {analytics.fmt_number(row['profit'])}"
                    f" — gap {analytics.fmt_percent(row['gap_best'])}"
                    f" — {row['status']}</li>"
                )
            body.append("</ul>")
        if error:
            body.append(f"<p><b>Lỗi:</b> {html.escape(error)}</p>")
        body.append("<p><b>Nhật ký</b></p><pre>")
        body.append(html.escape("\n".join(self._log_lines[-80:])))
        body.append("</pre>")
        self.analysis_requested.emit(self.PAGE_TITLE, "\n".join(body))

    def analysis_snapshot(self):
        if not self._log_lines:
            return self.PAGE_TITLE, self.ANALYSIS_HTML
        algorithm = self.algo_combo.currentData()
        body = (
            f"<p><b>{html.escape(analytics.LONG_LABELS[algorithm])}</b></p>"
            f"<p>{html.escape(DESCRIPTIONS[algorithm])}</p>"
            "<p><b>Nhật ký</b></p><pre>"
            + html.escape("\n".join(self._log_lines[-80:]))
            + "</pre>"
        )
        return self.PAGE_TITLE, body

    def _ask_for_problem(self) -> None:
        self.status_message.emit("Chưa chọn bài toán — hãy chọn ở trang Dataset.")
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Chưa chọn bài toán")
        box.setText("Hãy chọn bài toán ở trang Dataset trước khi chạy.")
        go_button = box.addButton("Sang trang Dataset", QMessageBox.AcceptRole)
        box.addButton("Đóng", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is go_button:
            self.navigate_requested.emit(1)

    # ------------------------------------------------------------------
    def reset(self) -> None:
        if self.state.running:
            return
        self._stop_clock()
        self._records = {name: [] for name in analytics.ALGORITHMS}
        self._batch_problems = []
        self._batch_index = 0
        self._batch_records = {}
        self._log_lines = []
        self._run_mode = None
        self.state.set_run_all_results(None)
        self.details.clear()
        self.result_table.clear()
        self.chart_single.show_placeholder("Bấm Run để xem đường hội tụ")
        self.chart_multi.show_placeholder("Bấm Run All để so sánh 4 thuật toán")
        self.replay_button.setEnabled(False)
        self.stack.setCurrentIndex(0)
        self.progress.setVisible(False)
        self.elapsed_label.setVisible(False)
        self.remaining_label.setVisible(False)
        self.status_message.emit("Đã đặt lại trang Algorithm.")
        self.analysis_requested.emit(self.PAGE_TITLE, self.ANALYSIS_HTML)

    def stop_replay(self) -> None:
        self.chart_single.stop_replay()

    def run_primary_action(self) -> None:
        self.run_single()
