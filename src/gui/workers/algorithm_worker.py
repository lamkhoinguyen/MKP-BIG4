"""Worker chạy thuật toán trong QThread, không chạm vào widget."""

from PySide6.QtCore import QObject, Signal, Slot

from src.algorithms import get_solver
from src.gui import analytics


def _error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


class AlgorithmWorker(QObject):
    """Chạy một thuật toán cho một bài toán."""

    started = Signal(str)
    log = Signal(str)
    finished = Signal(str, object)
    failed = Signal(str, str)

    def __init__(self, algorithm: str, problem, time_limit: float, seed: int = 0):
        super().__init__()
        self.algorithm = algorithm
        self.problem = problem
        self.time_limit = float(time_limit)
        self.seed = int(seed)

    @Slot()
    def run(self) -> None:
        self.started.emit(self.algorithm)
        self.log.emit(
            f"Bắt đầu {analytics.LONG_LABELS.get(self.algorithm, self.algorithm)} "
            f"trên {getattr(self.problem, 'name', '-')} "
            f"(time_limit={self.time_limit:g}s, seed={self.seed})."
        )
        try:
            solver = get_solver(self.algorithm)
            result = solver(
                self.problem,
                time_limit=self.time_limit,
                seed=self.seed,
            )
        except Exception as exc:  # noqa: BLE001 - báo lỗi về GUI
            message = _error_text(exc)
            self.log.emit(f"Lỗi: {message}")
            self.failed.emit(self.algorithm, message)
            return
        self.log.emit(
            f"Xong: profit={getattr(result, 'total_profit', None)}, "
            f"status={getattr(result, 'status', None)}, "
            f"runtime={getattr(result, 'runtime', 0.0):.2f}s."
        )
        self.finished.emit(self.algorithm, result)


class SessionWorker(QObject):
    """Chạy tuần tự danh sách (thuật toán, seed); lỗi một lượt không dừng phiên."""

    progress = Signal(int, int, str)
    run_done = Signal(str, int, object)
    log = Signal(str)
    finished = Signal(list)
    failed = Signal(str, str)

    def __init__(self, plan, problem, time_limit: float):
        super().__init__()
        self.plan = list(plan)
        self.problem = problem
        self.time_limit = float(time_limit)

    @Slot()
    def run(self) -> None:
        total = len(self.plan)
        outcomes = []
        try:
            for done, (algorithm, seed) in enumerate(self.plan):
                label = analytics.label_for(algorithm)
                if algorithm in analytics.STOCHASTIC:
                    label = f"{label} seed {seed}"
                self.progress.emit(done, total, label)
                self.log.emit(f"Bắt đầu {label} ({done + 1}/{total}).")
                try:
                    solver = get_solver(algorithm)
                    result = solver(
                        self.problem,
                        time_limit=self.time_limit,
                        seed=int(seed),
                    )
                    record = analytics.run_record(result, int(seed))
                    self.log.emit(
                        f"Xong {label}: profit={record['profit']}, "
                        f"status={record['status']}, "
                        f"runtime={record['runtime']:.2f}s."
                    )
                except Exception as exc:  # noqa: BLE001 - giữ phiên chạy tiếp
                    message = _error_text(exc)
                    record = analytics.error_record(message, int(seed))
                    self.log.emit(f"Lỗi {label}: {message}")
                self.run_done.emit(algorithm, int(seed), record)
                outcomes.append(
                    {
                        "algorithm": algorithm,
                        "seed": int(seed),
                        "record": record,
                    }
                )
            self.progress.emit(total, total, "Hoàn tất")
            self.finished.emit(outcomes)
        except Exception as exc:  # noqa: BLE001 - lỗi ngoài vòng lặp
            self.failed.emit("session", _error_text(exc))
