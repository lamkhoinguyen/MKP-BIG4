"""Dynamic Programming (quy hoach dong) — Thanh vien 2.

Mo hinh:
- Trang thai sau khi xet j mat hang dau (theo thu tu uu tien) la vector tai
  nguyen da dung R = (r_1..r_m); gia tri la loi nhuan lon nhat dat duoc.
- Chuyen trang thai: tu (R, P) sinh (R + w_j, P + p_j) neu khong vuot capacity;
  giu ca phuong an khong chon. Trang thai trung (cung R) chi giu P lon hon.
- Khoi tao (R=0, P=0). Truy vet nguoc bang mang parent/took cua tung tang.
- Cat can: nghiem tham lam + local search lam can duoi; cat nhanh theo can tren
  (fractional bound tren tung rang buoc); loai mat hang khong bao gio vua.

Do phuc tap:
- Thoi gian: O(n * S * (m + log S)) voi S la so trang thai khong bi chi phoi.
- Bo nho: O(S * m) cho tap trang thai + O(n * S) mang truy vet.
- DP chinh xac nhung S co the bung no theo tich cac capacity; vi vay file nay
  gioi han bo nho (DEFAULT_MEMORY_LIMIT_MB) va so trang thai (MAX_STATES).
  Khi vuot gioi han, tra STATUS_TIMEOUT / STATUS_OUT_OF_MEMORY kem nghiem tot
  nhat hien co — KHONG coi la loi nhuan 0.

history: {step, iteration, phase, item, n_states, n_candidates, n_pruned,
best_profit, profit, lower_bound, elapsed}.
"""

import time

import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_OUT_OF_MEMORY, STATUS_TIMEOUT
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult

# Gioi han bo nho cho cac mang cua DP (MB). Vuot -> STATUS_OUT_OF_MEMORY.
DEFAULT_MEMORY_LIMIT_MB = 3000.0

# Tran so trang thai moi tang: chan bung no bo nho va thoi gian.
MAX_STATES = 2_000_000

_MB = 1024.0 * 1024.0
_EPS = 1e-9


def estimate_dense_states(problem: MKPProblem) -> float:
    """So trang thai moi tang cua bang DP dang dac: prod_i (b_i + 1)."""
    caps = np.floor(np.asarray(problem.capacities, dtype=np.float64)) + 1.0
    return float(np.prod(caps))


def _failure_result(problem, *, runtime, history, status, peak_mb, partial_x):
    """Ket qua khi het gio / het bo nho."""
    if partial_x is not None:
        result = build_result(
            problem, partial_x, runtime=runtime, history=history, status=status
        )
    else:
        result = MKPResult(
            selected_items=[],
            total_profit=float("nan"),
            resource_usage=[],
            feasible=False,
            runtime=runtime,
            optimality_gap=None,
            history=history,
            status=status,
        )
    result.peak_memory = peak_mb
    return result


def _local_search(x, profits, w, cap, deadline):
    x = x.copy()
    n_used = len(x)
    usage = w @ x
    improved = True
    while improved and time.perf_counter() < deadline:
        improved = False
        # Them mat hang con vua
        for j in np.flatnonzero((x == 0) & (profits > 0)):
            if np.all(usage + w[:, j] <= cap):
                x[j] = 1
                usage = usage + w[:, j]
                improved = True
        # Doi 1 lay 1: bo i, them j co loi nhuan lon hon
        for i in np.flatnonzero(x == 1):
            if time.perf_counter() >= deadline:
                break
            base = usage - w[:, i]
            ok = (x == 0) & (profits > profits[i]) & np.all(
                base[:, None] + w <= cap[:, None], axis=0
            )
            cand = np.flatnonzero(ok)
            if len(cand):
                j = cand[np.argmax(profits[cand])]
                x[i], x[j] = 0, 1
                usage = base + w[:, j]
                improved = True
    return x


class _BoundTables:

    def __init__(self, profits_pos, weights_pos):
        self.m = weights_pos.shape[0]
        self.profits = profits_pos
        self.weights = weights_pos
        positive = weights_pos > 0
        safe_w = np.where(positive, weights_pos, 1.0)
  
        self.ratio = np.where(positive, profits_pos[None, :] / safe_w, np.inf)
        self.rank = [np.argsort(-self.ratio[i], kind="stable") for i in range(self.m)]
        self.tables = []

    def prepare(self, start: int) -> None:
        self.tables = []
        for i in range(self.m):
            sel = self.rank[i][self.rank[i] >= start]
            cum_w = np.concatenate(([0.0], np.cumsum(self.weights[i, sel])))
            cum_p = np.concatenate(([0.0], np.cumsum(self.profits[sel])))
            self.tables.append((cum_w, cum_p, self.ratio[i, sel]))

    def upper_bound(self, residual: np.ndarray) -> np.ndarray:
    
        residual = residual.astype(np.float64, copy=False)
        bound = np.full(residual.shape[0], np.inf)
        for i, (cum_w, cum_p, ratio) in enumerate(self.tables):
            r = residual[:, i]
            k = np.searchsorted(cum_w, r, side="right") - 1
            value = cum_p[k]
            partial = k < len(ratio)
            if partial.any():
                kk = k[partial]
                value[partial] += (r[partial] - cum_w[kk]) * ratio[kk]
            np.minimum(bound, value, out=bound)
        return bound



def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,  
    record_history: bool = True,
    memory_limit_mb: float = DEFAULT_MEMORY_LIMIT_MB,
    use_bound_pruning: bool = True,
    return_partial_on_failure: bool = True,
) -> MKPResult:

    start = time.perf_counter()
    deadline = start + max(0.0, time_limit)
    memory_limit = memory_limit_mb * _MB

    n, m = problem.n, problem.m
    profits = np.asarray(problem.profits, dtype=np.float64)
    capacities = np.asarray(problem.capacities)
    weights = np.asarray(problem.weights)

    history: list = []
    peak_bytes = 0.0

    def log(entry: dict) -> None:
        if record_history:
            history.append(entry)

    # Mat hang nao da vuot mot gioi han thi khong bao gio chon duoc.
    usable = np.flatnonzero(np.all(weights <= capacities[:, None], axis=0))

    # Thu tu xu ly: diem uu tien giam dan, diem = p / tong(w_ij / b_i)
    safe_caps = np.maximum(capacities.astype(np.float64), 1e-12)
    cost = (weights[:, usable] / safe_caps[:, None]).sum(axis=0)
    score = profits[usable] / np.maximum(cost, 1e-12)
    order = usable[np.argsort(-score, kind="stable")]
    n_used = len(order)


    integer_data = bool(
        np.all(weights == np.round(weights))
        and np.all(capacities == np.round(capacities))
    )
    dtype = np.int64 if integer_data else np.float64
    w_pos = weights[:, order].astype(dtype) 
    p_pos = profits[order]
    cap = capacities.astype(dtype)


    warm_x = np.zeros(n, dtype=np.int8)
    used_res = np.zeros(m, dtype=dtype)
    for pos in range(n_used):
        if p_pos[pos] <= 0:
            continue
        if np.all(used_res + w_pos[:, pos] <= cap):
            used_res = used_res + w_pos[:, pos]
            warm_x[order[pos]] = 1

    ls_deadline = min(deadline, time.perf_counter() + min(2.0, 0.05 * max(time_limit, 0.0)))
    x_pos = _local_search(warm_x[order].copy(), p_pos, w_pos, cap, ls_deadline)
    warm_x = np.zeros(n, dtype=np.int8)
    warm_x[order[x_pos == 1]] = 1
    warm_val = float(profits @ warm_x)
    lower_bound = warm_val
    integer_profits = bool(np.all(profits == np.round(profits)))

    bound_tables = None
    if use_bound_pruning and n_used > 0:
        bound_tables = _BoundTables(np.maximum(p_pos, 0.0), w_pos.astype(np.float64))

    log({
        "step": 0, "iteration": 0, "phase": "init", "item": None,
        "n_states": 1, "n_candidates": 0, "n_pruned": 0,
        "best_profit": lower_bound, "profit": lower_bound,
        "lower_bound": lower_bound,
        "dense_states": estimate_dense_states(problem),
        "memory_limit_mb": memory_limit_mb,
        "max_states": MAX_STATES,
        "elapsed": time.perf_counter() - start,
    })

    #Vong DP theo tung mat hang
    states_u = np.zeros((1, m), dtype=dtype)   
    states_p = np.zeros(1, dtype=np.float64)   
    layers: list = []                          
    stored_bytes = 0.0

    hash_mult = np.random.default_rng(12345).integers(
        1, 2**62, size=m, dtype=np.int64
    ) | 1
    status = STATUS_OK
    exhausted = False
    pending_layer = None

    def traceback(layer_count: int, state_index: int, layer_list=None) -> np.ndarray:

        x = np.zeros(n, dtype=np.int8)
        s = state_index
        source = layers if layer_list is None else layer_list
        for j in range(layer_count - 1, -1, -1):
            parent, took = source[j]
            if took[s]:
                x[order[j]] = 1
            s = int(parent[s])
        return x

    def partial_solution() -> np.ndarray:

        source = layers + ([pending_layer] if pending_layer is not None else [])
        if source and len(states_p):
            idx = int(np.argmax(states_p))
            if states_p[idx] > warm_val:
                return traceback(len(source), idx, source)
        return warm_x

    try:
        for j in range(n_used):
            pending_layer = None
            if time.perf_counter() >= deadline:
                status = STATUS_TIMEOUT
                break

            S = states_u.shape[0]
            
            transient = 11.0 * S * m * states_u.itemsize + 64.0 * S
            if stored_bytes + transient > memory_limit:
                status = STATUS_OUT_OF_MEMORY
                break
            peak_bytes = max(peak_bytes, stored_bytes + transient)

         
            cand_u = states_u + w_pos[:, j]
            feasible_idx = np.flatnonzero(np.all(cand_u <= cap, axis=1))
            cand_u = cand_u[feasible_idx]
            cand_p = states_p[feasible_idx] + p_pos[j]
            K = len(feasible_idx)

            if time.perf_counter() >= deadline:
                status = STATUS_TIMEOUT
                break

            # Chan bung no so trang thai: gioi han ca bo nho lan thoi gian.
            if S + K > MAX_STATES:
                status = STATUS_OUT_OF_MEMORY
                break

       
            all_u = np.concatenate((states_u, cand_u), axis=0)
            all_p = np.concatenate((states_p, cand_p))
            all_parent = np.concatenate(
                (np.arange(S, dtype=np.int32), feasible_idx.astype(np.int32))
            )
            all_took = np.concatenate((np.zeros(S, dtype=bool), np.ones(K, dtype=bool)))

        
            keep = np.ones(S + K, dtype=bool)
            if K > 0:
                bits = np.ascontiguousarray(all_u).view(np.int64)
                key = (bits * hash_mult).sum(axis=1)
                srt = np.argsort(key, kind="stable")  
                same = key[srt[1:]] == key[srt[:-1]]
                a, b = srt[:-1][same], srt[1:][same]
                if len(a):
                    real = np.all(all_u[a] == all_u[b], axis=1)  
                    a, b = a[real], b[real]
      
                    keep[np.where(all_p[b] > all_p[a], a, b)] = False
            kept = np.flatnonzero(keep)
            states_u = all_u[kept]
            states_p = all_p[kept]
            parent = all_parent[kept]
            took = all_took[kept]
            pending_layer = (parent, took)

            if time.perf_counter() >= deadline:
                status = STATUS_TIMEOUT
                break

            lower_bound = max(lower_bound, float(states_p.max()))


            n_pruned = 0
            if bound_tables is not None and j + 1 < n_used:
                bound_tables.prepare(j + 1)
                upper = states_p + bound_tables.upper_bound(cap - states_u)
                if integer_profits:
                    upper = np.floor(upper + _EPS)
                alive = upper >= lower_bound - _EPS
                n_pruned = int((~alive).sum())
                if n_pruned:
                    states_u = states_u[alive]
                    states_p = states_p[alive]
                    parent = parent[alive]
                    took = took[alive]
                    pending_layer = (parent, took)
                    if states_u.shape[0] == 0:
                        exhausted = True
                        break

            if time.perf_counter() >= deadline:
                status = STATUS_TIMEOUT
                break

            layers.append(pending_layer)
            pending_layer = None
            stored_bytes += parent.nbytes + took.nbytes
            peak_bytes = max(
                peak_bytes, stored_bytes + states_u.nbytes + states_p.nbytes
            )

            log({
                "step": j + 1, "iteration": j + 1, "phase": "dp",
                "item": int(order[j]),
                "n_states": int(states_u.shape[0]),
                "n_candidates": int(K),
                "n_pruned": n_pruned,
                "best_profit": float(lower_bound), "profit": float(lower_bound),
                "lower_bound": float(lower_bound),
                "elapsed": time.perf_counter() - start,
            })
    except MemoryError:
        status = STATUS_OUT_OF_MEMORY

    runtime = time.perf_counter() - start
    peak_mb = peak_bytes / _MB

    if exhausted:
        log({
            "step": len(history), "iteration": len(history), "phase": "exhausted",
            "best_profit": float(warm_val), "profit": float(warm_val),
            "lower_bound": float(lower_bound), "elapsed": runtime,
        })
        result = build_result(
            problem, warm_x, runtime=runtime, history=history, status=STATUS_OK
        )
        result.peak_memory = peak_mb
        return result

    if status != STATUS_OK:
        partial_x = partial_solution() if return_partial_on_failure else None
        failed_profit = (
            float(profits @ partial_x)
            if partial_x is not None
            else float(lower_bound)
        )
        log({
            "step": len(history), "iteration": len(history), "phase": "failed",
            "status": status, "best_profit": failed_profit,
            "profit": failed_profit, "lower_bound": float(lower_bound),
            "peak_memory_mb": peak_mb,
            "elapsed": runtime,
        })
        return _failure_result(
            problem, runtime=runtime, history=history, status=status,
            peak_mb=peak_mb, partial_x=partial_x,
        )


    best_x, best_val = warm_x, warm_val
    if states_p.size:
        final_idx = int(np.argmax(states_p))
        if states_p[final_idx] > warm_val + _EPS:
            best_x = traceback(n_used, final_idx)
            best_val = float(states_p[final_idx])

    if record_history:
        step = len(history)
        for pos in range(n_used - 1, -1, -1):
            item = int(order[pos])
            history.append({
                "step": step, "iteration": step, "phase": "traceback",
                "item": item, "selected": bool(best_x[item]),
                "best_profit": best_val, "profit": best_val,
                "elapsed": time.perf_counter() - start,
            })
            step += 1

    result = build_result(
        problem, best_x, runtime=time.perf_counter() - start,
        history=history, status=STATUS_OK,
    )
    result.peak_memory = peak_mb
    return result
