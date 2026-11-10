"""Simulated Annealing — Thanh vien 4.

Huong dan:
- Nghieman ban dau: 0/1 vector (random bang seed hoac greedy don gian).
- Lân can: dao 1 bit (hoac swap 0<->1) de van giu tinh feasibility.
- T(nhap) = T0 * alpha^n; danh accept theo delta fitness.
- Dung theo time_limit; history = [{"iteration", "profit"}, ...].
"""

import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    raise NotImplementedError("Thanh vien 4: implement SA o day")
