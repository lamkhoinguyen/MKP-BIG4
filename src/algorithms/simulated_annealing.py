"""Simulated Annealing (SA) — Thanh vien 4.

Y tuong:
- Xuat phat tu mot nghiem kha thi, lien tuc sinh nghiem lan can bang cach
  dao 1 bit hoac swap 1 mat hang dang chon lay 1 mat hang chua chon.
- Nghiem tot hon luon duoc nhan; nghiem xau hon van duoc nhan voi xac suat
  exp(delta / T) de thoat khoi cuc bo.
- Nhiet do T giam dan theo lich hinh hoc T <- alpha * T; cang ve sau SA cang
  han che chap nhan nghiem xau (dan chuyen thanh leo doi).

Cac buoc:
1. Khoi tao nghiem tham lam theo diem profit / tong tai nguyen, luon kha thi.
2. Lap den khi het time_limit hoac cham MAX_ITERATIONS:
   a. Sinh nghiem lan can: tat 1 bit, bat 1 bit, hoac swap 1-0.
   b. Tinh delta = profit(moi) - profit(hien tai).
   c. delta >= 0: nhan; nguoc lai nhan neu U(0,1) < exp(delta / T).
   d. Cap nhat nghiem tot nhat, ghi history, giam nhiet.
3. Tra MKPResult qua build_result; het gio -> STATUS_TIMEOUT.

Tham so chinh: MAX_ITERATIONS (so vong toi da), T0 (nhiet do dau, lay theo
loi nhuan trung binh), T_MIN (nhiet do ket thuc), lich giam hinh hoc.

Do phuc tap:
- Thoi gian: O(MAX_ITERATIONS * m) (moi buoc kiem tra m rang buoc).
- Bo nho: O(n + m).

Uu diem: don gian, it tham so, thoat cuc bo tot, la thuat toan anytime.
Nhuoc diem: chat luong phu thuoc lich giam nhiet, ket qua co yeu to ngau nhien.
"""

import time

import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult


MAX_ITERATIONS = 5_000_000
COOLING_ITERATIONS = 200_000
RESTART_AFTER = 20_000
HISTORY_POINTS = 500
T_MIN = 1e-3


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    start = time.perf_counter()
    deadline = start + max(0.0, time_limit)
    rng = np.random.default_rng(seed)

    n = problem.n
    m = problem.m
    profits = problem.profits
    weights = problem.weights
    capacities = problem.capacities

    # Diem uu tien: loi nhuan tren tong tai nguyen da chuan hoa.
    safe_capacities = np.maximum(capacities, 1e-12)
    normalized_weights = weights / safe_capacities[:, None]
    resource_cost = np.sum(normalized_weights, axis=0)
    scores = profits / np.maximum(resource_cost, 1e-12)

    def random_restart(base):
        """Pha nghiem tot nhat roi lap day tham lam theo thu tu ngau nhien."""
        x = base.copy()
        chosen = np.flatnonzero(x)
        if chosen.size:
            drop = chosen[rng.random(chosen.size) < 0.3]
            x[drop] = 0
        used = weights @ x
        profit = float(profits @ x)
        order = np.argsort(-(scores * (0.5 + rng.random(n))))
        for item in order:
            if x[item] == 0 and np.all(
                weights[:, item] <= capacities - used + 1e-9
            ):
                x[item] = 1
                used += weights[:, item]
                profit += profits[item]
        return x, used, profit

    # Nghiem ban dau: tham lam, dam bao kha thi.
    x = np.zeros(n, dtype=np.int8)
    usage = np.zeros(m)
    best_x = x.copy()
    best_profit = 0.0
    history = []

    if time.perf_counter() >= deadline:
        return build_result(
            problem,
            x,
            runtime=time.perf_counter() - start,
            history=history,
            status=STATUS_TIMEOUT,
        )

    for j in np.argsort(-scores):
        if time.perf_counter() >= deadline:
            return build_result(
                problem,
                best_x,
                runtime=time.perf_counter() - start,
                history=history,
                status=STATUS_TIMEOUT,
            )
        if np.all(weights[:, j] <= capacities - usage + 1e-9):
            x[j] = 1
            usage += weights[:, j]

    current_profit = float(profits @ x)
    best_profit = current_profit
    best_x = x.copy()

    # Lich giam nhiet hinh hoc: T0 -> T_MIN sau COOLING_ITERATIONS vong.
    max_iterations = int(MAX_ITERATIONS)
    t0 = max(float(np.mean(profits)), 1.0)
    t_end = max(T_MIN, t0 * 1e-4)
    cooling = (t_end / t0) ** (1.0 / COOLING_ITERATIONS)
    temperature = t0
    history_interval = max(1, max_iterations // HISTORY_POINTS)

    timed_out = False
    stagnation = 0
    last_iteration = 0

    for iteration in range(1, max_iterations + 1):
        if time.perf_counter() >= deadline:
            timed_out = True
            break

        last_iteration = iteration
        j = int(rng.integers(0, n))
        move = None
        delta = 0.0

        if x[j] == 1:
            # Tat 1 bit luon kha thi.
            move = (j, -1)
            delta = -float(profits[j])
        else:
            slack = capacities - usage
            if np.all(weights[:, j] <= slack + 1e-9):
                move = (j, -1)
                delta = float(profits[j])
            else:
                # Swap: bo 1 mat hang dang chon de lay mat hang j.
                selected = np.flatnonzero(x)
                if selected.size:
                    k = int(selected[rng.integers(0, selected.size)])
                    if np.all(weights[:, j] <= slack + weights[:, k] + 1e-9):
                        move = (j, k)
                        delta = float(profits[j] - profits[k])

        accepted = False
        improved = False
        if move is not None:
            if delta >= 0:
                accepted = True
            elif temperature > 0 and delta / temperature > -50:
                accepted = rng.random() < np.exp(delta / temperature)

            if accepted:
                j, k = move
                if k >= 0:
                    x[k] = 0
                    usage -= weights[:, k]
                x[j] = 1 - x[j]
                usage += weights[:, j] if x[j] == 1 else -weights[:, j]
                current_profit += delta

                if current_profit > best_profit:
                    best_profit = current_profit
                    best_x = x.copy()
                    improved = True

        stagnation = 0 if improved else stagnation + 1
        if stagnation >= RESTART_AFTER and iteration < max_iterations:
            # Ket qua da din (khong co cai thien): khoi dong lai tu nghiem tot.
            x, usage, current_profit = random_restart(best_x)
            stagnation = 0

        if iteration % history_interval == 0 or iteration == max_iterations:
            history.append({
                "iteration": iteration,
                "profit": float(best_profit),
                "current_profit": float(current_profit),
                "temperature": float(temperature),
                "accepted": bool(accepted),
                "move": None if move is None else [int(move[0]), int(move[1])],
                "delta": float(delta),
            })

        temperature *= cooling

    # Buoc cuoi: lap day nghiem tot nhat bang tham lam (neu con cho).
    best_usage = weights @ best_x
    for j in np.argsort(-scores):
        if best_x[j] == 0 and np.all(
            weights[:, j] <= capacities - best_usage + 1e-9
        ):
            best_x[j] = 1
            best_usage += weights[:, j]

    # Dong bo history voi nghiem cuoi cung sau khi lap day tham lam.
    best_profit = float(profits @ best_x)
    if history and history[-1]["iteration"] == last_iteration:
        history[-1]["profit"] = best_profit
    else:
        history.append({
            "iteration": last_iteration,
            "profit": best_profit,
            "current_profit": float(current_profit),
            "temperature": float(temperature),
            "accepted": False,
            "move": None,
            "delta": 0.0,
        })

    runtime = time.perf_counter() - start
    status = STATUS_TIMEOUT if timed_out else STATUS_OK

    return build_result(
        problem,
        best_x,
        runtime=runtime,
        history=history,
        status=status,
    )
