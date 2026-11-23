"""Greedy (tham lam) — Thanh vien 1.

Y tuong (tham lam thich nghi tren NHIEU rang buoc):
- Moi vong lap, voi cac mat hang con vua capacity, tinh diem uu tien
      score_j = profit_j / sum_i ( w_ij / (b_i - used_i) )
  tuc la loi nhuan chia cho muc "ton kem" cua mat hang so voi tai nguyen CON LAI
  cua tung rang buoc (tai nguyen cang can kiet thi cang bi tinh nang).
- Chon mat hang co diem cao nhat, cap nhat tai nguyen da dung, tinh lai diem.
- Lap den khi khong con mat hang nao them vao duoc ma khong vi pham capacity.

Do phuc tap: moi vong O(n*m), toi da n vong => O(n^2 * m); bo nho O(n*m).
Tat dinh (khong dung seed). Luon cho nghiem hop le, khong dam bao toi uu.
"""

import time

import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result, compute_resource_usage
from src.core.model import MKPProblem, MKPResult
from src.core.validator import is_feasible

_EPS = 1e-12


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    start = time.perf_counter()

    n, m = problem.n, problem.m
    profits = np.asarray(problem.profits, dtype=np.float64)
    weights = np.asarray(problem.weights, dtype=np.float64)
    caps = np.asarray(problem.capacities, dtype=np.float64)

    x = np.zeros(n, dtype=int)
    used = np.zeros(m, dtype=np.float64)
    candidate = profits > 0          # mat hang con duoc xet (chua chon, co loi nhuan)
    history: list = []
    status = STATUS_OK
    iteration = 0

    while True:
        if time.perf_counter() - start > time_limit:
            status = STATUS_TIMEOUT
            break

        # Mat hang them vao van khong vuot rang buoc nao
        fits = candidate & np.all(used[:, None] + weights <= caps[:, None], axis=0)
        idx = np.flatnonzero(fits)
        if idx.size == 0:
            break

        # Diem uu tien theo tai nguyen con lai cua tung rang buoc
        remaining = np.maximum(caps - used, _EPS)
        cost = (weights[:, idx] / remaining[:, None]).sum(axis=0)
        score = profits[idx] / np.maximum(cost, _EPS)

        best = int(np.argmax(score))
        j = int(idx[best])
        skipped = int(candidate.sum()) - int(idx.size)

        x[j] = 1
        used += weights[:, j]
        candidate[j] = False

        iteration += 1
        current_profit = float(profits @ x)
        history.append({
            "iteration": iteration,
            "profit": current_profit,
            "best_profit": current_profit,
            "item": j,
            "score": float(score[best]),
            "decision": "select",
            "skipped": skipped,
        })

    # Chot an toan: neu sai so so thuc lam vuot capacity thi bo bot mat hang loi nhuan thap
    while not is_feasible(problem, x):
        chosen = np.flatnonzero(x)
        usage = compute_resource_usage(problem, x)
        if chosen.size == 0 or not np.any(usage > caps):
            break
        x[chosen[np.argmin(profits[chosen])]] = 0

    # Dong bo history voi nghiem cuoi cung (sau buoc chot an toan).
    final_profit = float(profits @ x)
    if history:
        history[-1]["profit"] = final_profit
        history[-1]["best_profit"] = final_profit

    runtime = time.perf_counter() - start
    return build_result(problem, x, runtime=runtime, history=history, status=status)
