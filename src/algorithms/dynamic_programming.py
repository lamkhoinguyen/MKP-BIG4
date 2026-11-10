"""Dynamic Programming — Thanh vien 2.

Huong dan:
- Trang thai: dp[j] = loi nhuan toi da voi vector tai nguyen da dung j
  (hoac bien the 2D: dp[i][capacity] theo tung rang buoc).
- MKP DP qua lon neu m hoac b(i) lon — neu vuot time_limit/memory
  tra status=STATUS_TIMEOUT / STATUS_OUT_OF_MEMORY, khong raise.
- Track lại danh sach mat hang duoc chon (parent pointer hoac re-trace).
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
    raise NotImplementedError("Thanh vien 2: implement DP o day")
