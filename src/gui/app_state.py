"""Trạng thái dùng chung giữa các trang GUI."""

from PySide6.QtCore import QObject, Signal

from src.core.config import TIME_LIMIT_SECONDS


class AppState(QObject):
    """Giữ trạng thái chung và phát tín hiệu khi thay đổi.

    Quy ước: trang Dataset chỉ commit bài toán khi người dùng bấm
    "Dùng bài toán này"; lúc đó mới phát ``problem_changed``. Với lựa chọn
    "(tất cả bài trong file)" thì phát thêm ``batch_changed`` với danh sách bài.
    """

    problem_changed = Signal(object)
    batch_changed = Signal(object)
    dataset_changed = Signal(str)
    time_limit_changed = Signal(float)
    seed_changed = Signal(int)
    num_seeds_changed = Signal(int)
    last_result_changed = Signal(object)
    last_session_changed = Signal(object)
    run_all_changed = Signal(object)
    running_changed = Signal(bool)
    viewing_saved_session_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dataset_file = ""
        self._problem = None
        self._problems = []
        self._batch_mode = False
        self._time_limit = float(TIME_LIMIT_SECONDS)
        self._seed = 0
        self._num_seeds = 1
        self._last_result = None
        self._last_session = None
        self._run_all_results = None
        self._running = False
        self._viewing_saved_session = False

    @property
    def dataset_file(self) -> str:
        return self._dataset_file

    @dataset_file.setter
    def dataset_file(self, value: str) -> None:
        value = value or ""
        if value == self._dataset_file:
            return
        self._dataset_file = value
        self.dataset_changed.emit(value)

    @property
    def problem(self):
        return self._problem

    @property
    def problems(self) -> list:
        return list(self._problems)

    @property
    def is_batch(self) -> bool:
        return self._batch_mode

    @property
    def time_limit(self) -> float:
        return self._time_limit

    @time_limit.setter
    def time_limit(self, value: float) -> None:
        value = float(value)
        if value == self._time_limit:
            return
        self._time_limit = value
        self.time_limit_changed.emit(value)

    @property
    def seed(self) -> int:
        return self._seed

    @seed.setter
    def seed(self, value: int) -> None:
        value = int(value)
        if value == self._seed:
            return
        self._seed = value
        self.seed_changed.emit(value)

    @property
    def num_seeds(self) -> int:
        return self._num_seeds

    @num_seeds.setter
    def num_seeds(self, value: int) -> None:
        value = int(value)
        if value == self._num_seeds:
            return
        self._num_seeds = value
        self.num_seeds_changed.emit(value)

    @property
    def last_result(self):
        return self._last_result

    @last_result.setter
    def last_result(self, value) -> None:
        self._last_result = value
        self.last_result_changed.emit(value)

    @property
    def last_session(self):
        return self._last_session

    @last_session.setter
    def last_session(self, value) -> None:
        self._last_session = value
        self.last_session_changed.emit(value)

    @property
    def run_all_results(self):
        """Kết quả Run All gần nhất do trang Algorithm công bố.

        Cấu trúc: ``{batch, dataset_file, problem, problems, records,
        batch_records, time_limit, seed}``. Dùng để trang Comparison nạp lại
        mà không phải chạy lại 4 thuật toán.
        """
        return self._run_all_results

    def set_run_all_results(self, snapshot) -> None:
        self._run_all_results = snapshot
        self.run_all_changed.emit(snapshot)

    @property
    def running(self) -> bool:
        return self._running

    @running.setter
    def running(self, value: bool) -> None:
        value = bool(value)
        if value == self._running:
            return
        self._running = value
        self.running_changed.emit(value)

    @property
    def viewing_saved_session(self) -> bool:
        return self._viewing_saved_session

    @viewing_saved_session.setter
    def viewing_saved_session(self, value: bool) -> None:
        value = bool(value)
        if value == self._viewing_saved_session:
            return
        self._viewing_saved_session = value
        self.viewing_saved_session_changed.emit(value)

    def commit_problem(self, dataset_file: str, problem) -> None:
        """Ghi nhận một bài toán và thoát chế độ chọn tất cả."""
        self._dataset_file = dataset_file or ""
        self._problem = problem
        self._problems = []
        self._batch_mode = False
        self.dataset_changed.emit(self._dataset_file)
        self.problem_changed.emit(problem)
        self.batch_changed.emit(self._problems)

    def commit_problems(self, dataset_file: str, problems) -> None:
        """Ghi nhận mọi bài trong file để chạy batch; vẫn phát problem_changed."""
        items = list(problems)
        self._dataset_file = dataset_file or ""
        self._problem = items[0] if items else None
        self._problems = items
        self._batch_mode = True
        self.dataset_changed.emit(self._dataset_file)
        self.problem_changed.emit(self._problem)
        self.batch_changed.emit(self._problems)

    def clear_problem(self) -> None:
        self.commit_problem("", None)

    def problem_text(self) -> str:
        if self._batch_mode:
            return f"{len(self._problems)} bài trong {self._dataset_file} (tất cả)"
        problem = self._problem
        if problem is None:
            return "Chưa chọn bài toán"
        return f"{problem.name} (n={problem.n}, m={problem.m})"
