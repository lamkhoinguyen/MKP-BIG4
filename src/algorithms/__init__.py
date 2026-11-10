"""Interface chung cho 4 thuat toan — MOI thanh vien phai lam theo day.

Hop dong (contract):

    def solve(problem: MKPProblem, *, time_limit: float, seed: int = 0) -> MKPResult

Quy tac:
- Khong doi ten ham, doi ten file, doi chu ky tham so.
- Nhan keyword-only: time_limit (giay), seed (int, mac dinh 0).
- Tra ve MKPResult — dung build_result() de tinh profit/gap/feasible.
- Neu het time_limit: dung som, status=STATUS_TIMEOUT (tu src.core.config).
- Nghi duong: vector 0/1 do dai problem.n — truyen x vao build_result.
- history (tuy chon): list dict de ve do thuat toan, moi phan tu {"iteration": int, "profit": float}.
- Khong doc file du lieu trong solve — nhan problem da load san.

Chay: python -m pytest tests/  (tu goc repo)
"""

from typing import Callable, Protocol

from src.core.config import TIME_LIMIT_SECONDS
from src.core.model import MKPProblem, MKPResult


class Algorithm(Protocol):
    def solve(
        self,
        problem: MKPProblem,
        *,
        time_limit: float = TIME_LIMIT_SECONDS,
        seed: int = 0,
    ) -> MKPResult: ...


# Ten dung cho experiments/GUI dang ky
ALGORITHM_NAMES = (
    "greedy",
    "dynamic_programming",
    "genetic_algorithm",
    "simulated_annealing",
)


def get_solver(name: str) -> Callable[..., MKPResult]:
    """Lay solve() theo ten; loi neu chua implement hoac ten sai."""
    from src.algorithms import (
        dynamic_programming,
        genetic_algorithm,
        greedy,
        simulated_annealing,
    )

    table = {
        "greedy": greedy.solve,
        "dynamic_programming": dynamic_programming.solve,
        "genetic_algorithm": genetic_algorithm.solve,
        "simulated_annealing": simulated_annealing.solve,
    }
    if name not in table:
        raise KeyError(f"khong co thuat toan '{name}', chon {ALGORITHM_NAMES}")
    return table[name]
