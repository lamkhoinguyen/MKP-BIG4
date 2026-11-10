"""Genetic Algorithm — Thanh vien 3.

Huong dan:
- Chromosome: vector 0/1 do dai n.
- Fitness = total_profit; xu ly vi phai rang buoc (penalty hoac repair).
- Crossover + mutation; dung seed de random (np.random.default_rng(seed)).
- Dung theo time_limit hoac so the he; history = [{"iteration", "profit"}, ...].
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
    raise NotImplementedError("Thanh vien 3: implement GA o day")
