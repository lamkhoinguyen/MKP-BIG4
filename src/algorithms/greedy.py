"""Greedy (tham lam) — Thanh vien 1.

Huong dan:
- Diem uu ti: mat hang / (tai nguyen da dung + weight moi) tren Nhieu rang buoc
  (KHONG chi profit/1-kieu-tai-nguyen).
- Chon lap lai den khi khong con mat hang de them vao (giu duong tim kiem).
- Bao dam: moi buoc kiem tra them vao co vi phai capacity hay khong.
"""

import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result, compute_resource_usage
from src.core.model import MKPProblem, MKPResult
from src.core.validator import is_feasible


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    raise NotImplementedError("Thanh vien 1: implement greedy o day")
