"""Biểu đồ nhúng Qt (không dùng pyplot, không ép backend Agg)."""

import math

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.gui import analytics

COLORS = {
    "greedy": "#2563eb",
    "dynamic_programming": "#0f766e",
    "genetic_algorithm": "#c2410c",
    "simulated_annealing": "#7c3aed",
}

BAR_COLORS = ("#2563eb", "#0f766e", "#c2410c", "#7c3aed")

HISTORY_NOTE = (
    "Trục x là % tiến trình ghi nhận; đơn vị gốc của history khác nhau giữa "
    "các thuật toán, nên chỉ so sánh hình dạng hội tụ, không so sánh giá trị "
    "iteration."
)


def _row_problem(row: dict):
    """Tên bài của một dòng, lấy từ khóa ``problem`` hoặc tách nhãn batch."""
    problem = row.get("problem")
    if problem:
        return str(problem)
    label = str(row.get("label") or "")
    if " · " in label:
        return label.split(" · ", 1)[0]
    return None


def _group_by_problem(rows):
    """Gom rows theo bài; trả ``None`` nếu chỉ có một bài/không có tên bài."""
    problems = []
    grouped = {}
    for row in rows:
        problem = _row_problem(row)
        if not problem:
            return None
        if problem not in grouped:
            grouped[problem] = []
            problems.append(problem)
        grouped[problem].append(row)
    if len(problems) <= 1:
        return None
    return [(problem, grouped[problem]) for problem in problems]


def _short_problem_labels(problems):
    """Bỏ tiền tố chung (vd ``mknap1_``) để nhãn trục X không dính nhau."""
    if not problems:
        return list(problems)
    first = problems[0]
    cut = first.rfind("_")
    prefix = first[: cut + 1] if cut > 0 else ""
    if prefix and all(problem.startswith(prefix) for problem in problems):
        return [problem[len(prefix):] or problem for problem in problems]
    return list(problems)


class ChartWidget(QWidget):
    """Canvas matplotlib kèm phát lại đường hội tụ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3.2))
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas.setMinimumHeight(160)
        layout.addWidget(self.canvas)

        self._replay_points: list[tuple[float, float]] = []
        self._replay_index = 0
        self._replay_step = 1
        self._replay_title = "Hội tụ"
        self._replay_speed = 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self.show_placeholder("Chưa có dữ liệu")

    # ------------------------------------------------------------------
    # Trạng thái
    # ------------------------------------------------------------------
    @property
    def has_history(self) -> bool:
        return bool(self._replay_points)

    @property
    def is_replaying(self) -> bool:
        return self._timer.isActive()

    def _new_axis(self):
        self.figure.clf()
        axis = self.figure.add_subplot(111)
        return axis

    def _finish(self) -> None:
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def show_placeholder(self, text: str) -> None:
        self.stop_replay(redraw=False)
        self._replay_points = []
        axis = self._new_axis()
        axis.axis("off")
        axis.text(0.5, 0.5, text, ha="center", va="center", color="#64748b", fontsize=12)
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.show_placeholder("Chưa có dữ liệu")

    # ------------------------------------------------------------------
    # Đường hội tụ một thuật toán
    # ------------------------------------------------------------------
    def plot_history(self, result, title: str = "Đường hội tụ") -> None:
        points = analytics.history_series(result)
        if not points:
            self.show_placeholder("Thuật toán không cung cấp history")
            return
        self._replay_points = points
        self._replay_title = title
        self._replay_speed = 1
        self._draw_history(points, title)
        self._configure_replay()

    def _configure_replay(self) -> None:
        length = len(self._replay_points)
        base_duration = min(30.0, length / 10.0) if length else 0.0
        duration = base_duration / max(1, self._replay_speed)
        ticks = max(1.0, duration / 0.05)
        self._replay_step = max(1, math.ceil(length / ticks))

    def _draw_history(self, points, title: str) -> None:
        axis = self._new_axis()
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        axis.plot(xs, ys, color="#2563eb", linewidth=2)
        axis.set_title(title, fontsize=13)
        axis.set_xlabel("iteration", fontsize=10)
        axis.set_ylabel("Profit tốt nhất", fontsize=10)
        axis.tick_params(labelsize=9)
        axis.grid(alpha=0.25)
        self._finish()

    def start_replay(self, speed: int = 1) -> None:
        if not self._replay_points:
            return
        self.stop_replay(redraw=False)
        self._replay_speed = max(1, int(speed))
        self._configure_replay()
        self._replay_index = min(self._replay_step, len(self._replay_points))
        self._draw_history(
            self._replay_points[: self._replay_index], self._replay_title
        )
        self._timer.start(50)

    def stop_replay(self, redraw: bool = True) -> None:
        if self._timer.isActive():
            self._timer.stop()
        if redraw and self._replay_points:
            self._draw_history(self._replay_points, self._replay_title)

    def _tick(self) -> None:
        if not self._replay_points:
            self._timer.stop()
            return
        self._replay_index += self._replay_step
        if self._replay_index >= len(self._replay_points):
            self._replay_index = len(self._replay_points)
            self._timer.stop()
        self._draw_history(
            self._replay_points[: self._replay_index], self._replay_title
        )

    # ------------------------------------------------------------------
    # Biểu đồ cột
    # ------------------------------------------------------------------
    def plot_bars(self, rows, key: str, title: str, ylabel: str = "") -> None:
        groups = _group_by_problem(rows)
        if groups is not None:
            self._plot_grouped_bars(groups, key, title, ylabel)
            return

        values = []
        errors = []
        labels = []
        colors = []
        for index, row in enumerate(rows):
            value, error = _row_value(row, key)
            labels.append(row.get("label", "-"))
            values.append(0.0 if value is None else value)
            errors.append(error)
            colors.append(BAR_COLORS[index % len(BAR_COLORS)])

        if not any(value for value in values) and not any(errors):
            self.show_placeholder("Chưa có dữ liệu để vẽ")
            return

        axis = self._new_axis()
        positions = list(range(len(labels)))
        bars = axis.bar(
            positions,
            values,
            color=colors,
            yerr=errors if any(errors) else None,
            capsize=4,
        )
        axis.set_title(title, fontsize=13)
        axis.set_ylabel(ylabel, fontsize=10)
        axis.set_xticks(positions)
        axis.set_xticklabels(labels, fontsize=10)
        axis.tick_params(axis="y", labelsize=9)
        axis.grid(axis="y", alpha=0.25)
        top = max(values) if values else 0
        if top > 0:
            axis.set_ylim(0, top * 1.18)
        for bar, value in zip(bars, values):
            axis.annotate(
                analytics.fmt_number(value, 2 if key == "gap" else 0),
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                fontsize=9,
            )
        if top <= 0:
            axis.set_ylim(0, 1)
        self._finish()

    def _plot_grouped_bars(self, groups, key: str, title: str, ylabel: str) -> None:
        """Cột gom theo bài, 4 màu theo thuật toán (chế độ batch)."""
        algorithms = []
        for _, group in groups:
            for row in group:
                algorithm = row.get("algorithm")
                if algorithm not in algorithms:
                    algorithms.append(algorithm)
        if not algorithms:
            self.show_placeholder("Chưa có dữ liệu để vẽ")
            return

        values = {algorithm: [] for algorithm in algorithms}
        errors = {algorithm: [] for algorithm in algorithms}
        for _, group in groups:
            by_algorithm = {row.get("algorithm"): row for row in group}
            for algorithm in algorithms:
                row = by_algorithm.get(algorithm)
                value, error = (None, 0.0) if row is None else _row_value(row, key)
                values[algorithm].append(0.0 if value is None else value)
                errors[algorithm].append(error)

        flat_values = [value for series in values.values() for value in series]
        flat_errors = [error for series in errors.values() for error in series]
        if not any(flat_values) and not any(flat_errors):
            self.show_placeholder("Chưa có dữ liệu để vẽ")
            return

        axis = self._new_axis()
        positions = list(range(len(groups)))
        group_width = 0.82
        bar_width = group_width / len(algorithms)
        for index, algorithm in enumerate(algorithms):
            offsets = [
                position - group_width / 2 + bar_width * (index + 0.5)
                for position in positions
            ]
            bars = axis.bar(
                offsets,
                values[algorithm],
                width=bar_width,
                color=COLORS.get(algorithm, BAR_COLORS[index % len(BAR_COLORS)]),
                label=analytics.label_for(algorithm),
            )
            self._annotate_grouped(axis, bars, values[algorithm], key)

        axis.set_title(title, fontsize=13)
        axis.set_ylabel(ylabel, fontsize=10)
        axis.set_xticks(positions)
        axis.set_xticklabels(
            _short_problem_labels([problem for problem, _ in groups]), fontsize=8
        )
        axis.tick_params(axis="y", labelsize=9)
        axis.grid(axis="y", alpha=0.25)
        top = max(flat_values) if flat_values else 0
        if top > 0:
            axis.set_ylim(0, top * 1.25)
        else:
            axis.set_ylim(0, 1)
        axis.legend(
            fontsize=8,
            ncol=len(algorithms),
            loc="upper left",
            framealpha=0.9,
        )
        self._finish()

    @staticmethod
    def _annotate_grouped(axis, bars, values, key: str) -> None:
        if key == "profit":
            return
        digits = {"gap": 2, "runtime": 1, "memory": 0}.get(key, 0)
        threshold = 0.5 * (10 ** -digits)
        for bar, value in zip(bars, values):
            if not value or abs(value) < threshold:
                continue
            axis.annotate(
                analytics.fmt_number(value, digits),
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                textcoords="offset points",
                xytext=(0, 3),
                ha="center",
                va="bottom",
                rotation=90,
                fontsize=7,
            )

    # ------------------------------------------------------------------
    # Hội tụ chồng nhau
    # ------------------------------------------------------------------
    def plot_convergence(self, rows) -> None:
        groups = _group_by_problem(rows)
        if groups is not None:
            self._plot_grouped_convergence(groups)
            return

        axis = self._new_axis()
        drew = False
        for row in rows:
            drew = self._plot_row_series(axis, row) or drew
        axis.set_title("Hội tụ (% tiến trình)", fontsize=13)
        axis.set_xlabel("% tiến trình ghi nhận", fontsize=10)
        axis.set_ylabel("Profit tốt nhất", fontsize=10)
        axis.tick_params(labelsize=9)
        axis.grid(alpha=0.25)
        if drew:
            axis.legend(fontsize=9)
            self.figure.text(
                0.5,
                0.005,
                HISTORY_NOTE,
                ha="center",
                va="bottom",
                fontsize=7.5,
                color="#64748b",
                wrap=True,
            )
            self.figure.subplots_adjust(bottom=0.28)
        else:
            axis.text(0.5, 0.5, "Chưa có history", ha="center", va="center", color="#64748b", fontsize=12)
            axis.set_xticks([])
            axis.set_yticks([])
        self.canvas.draw_idle()

    def _plot_row_series(self, axis, row, with_label: bool = True) -> bool:
        runs = row.get("runs") or []
        if not runs:
            return False
        profits = [
            float(run["profit"]) for run in runs if run.get("profit") is not None
        ]
        best_profit = max(profits) if profits else None
        color = COLORS.get(row.get("algorithm"), "#2563eb")
        multiple = len(runs) > 1
        drew = False
        for run in runs:
            series = analytics.progress_series(run.get("history") or [])
            if not series:
                continue
            xs = [point[0] for point in series]
            ys = [point[1] for point in series]
            is_best = (
                best_profit is not None
                and run.get("profit") is not None
                and abs(float(run["profit"]) - best_profit) < 1e-6
            )
            label = None
            if with_label and (not multiple or is_best):
                label = row.get("label")
            axis.plot(
                xs,
                ys,
                color=color,
                label=label,
                alpha=0.95 if (is_best or not multiple) else 0.35,
                linewidth=2.0 if (is_best or not multiple) else 1.0,
            )
            drew = True
        return drew

    def _plot_grouped_convergence(self, groups) -> None:
        """Lưới nhỏ mỗi bài một ô, mỗi thuật toán một màu (chế độ batch)."""
        self.figure.clf()
        count = len(groups)
        columns = min(4, count)
        grid_rows = math.ceil(count / columns)
        axes = self.figure.subplots(grid_rows, columns, squeeze=False)

        handles = {}
        drew_any = False
        for index, (problem, group) in enumerate(groups):
            axis = axes[index // columns][index % columns]
            drew = False
            for row in group:
                drew = self._plot_row_series(axis, row, with_label=False) or drew
                algorithm = row.get("algorithm")
                if algorithm and algorithm not in handles:
                    handles[algorithm] = Line2D(
                        [],
                        [],
                        color=COLORS.get(algorithm, "#2563eb"),
                        linewidth=2,
                        label=analytics.label_for(algorithm),
                    )
            axis.set_title(problem, fontsize=9)
            axis.tick_params(labelsize=7)
            axis.grid(alpha=0.2)
            if index // columns == grid_rows - 1:
                axis.set_xlabel("% tiến trình", fontsize=7)
            if index % columns == 0:
                axis.set_ylabel("Profit tốt nhất", fontsize=7)
            if not drew:
                axis.text(
                    0.5,
                    0.5,
                    "Không có history",
                    ha="center",
                    va="center",
                    color="#64748b",
                    fontsize=8,
                )
                axis.set_xticks([])
                axis.set_yticks([])
            drew_any = drew_any or drew

        for index in range(count, grid_rows * columns):
            axes[index // columns][index % columns].axis("off")

        if drew_any:
            self.figure.legend(
                handles=list(handles.values()),
                loc="upper center",
                ncol=max(1, len(handles)),
                fontsize=8,
                frameon=False,
            )
            self.figure.tight_layout(rect=(0, 0.02, 1, 0.93))
        else:
            self.figure.tight_layout()
        self.canvas.draw_idle()


def _row_value(row: dict, key: str):
    stochastic = bool(row.get("stochastic"))
    if key == "profit":
        value = row.get("profit")
        error = row.get("std") if stochastic else 0.0
    elif key == "gap":
        value = row.get("gap_avg") if stochastic else row.get("gap_best")
        if value is None:
            value = row.get("gap_best")
        error = 0.0
        if value is not None:
            value = float(value) * 100.0
        runs = row.get("runs") or []
        if stochastic and value is not None:
            gaps = [
                float(run["gap"]) * 100.0
                for run in runs
                if run.get("gap") is not None
            ]
            if len(gaps) > 1:
                mean = sum(gaps) / len(gaps)
                error = math.sqrt(
                    sum((gap - mean) ** 2 for gap in gaps) / len(gaps)
                )
    elif key == "runtime":
        value = row.get("runtime")
        value = None if value is None else float(value)
        error = 0.0
    elif key == "memory":
        value = row.get("peak_memory")
        value = None if value is None else float(value)
        error = 0.0
    else:
        value = row.get(key)
        error = 0.0
    return value, float(error or 0.0)
