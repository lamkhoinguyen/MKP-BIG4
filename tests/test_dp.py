"""Kiem tra thuat toan Dynamic Programming (DP) cua Thanh vien 2.

Test hanh vi that cua DP:
- Nghiem hop le, khong vuot z_ref, gap tinh dung.
- Cung seed cho cung ket qua (DP xac dinh).
- Het gio / het bo nho: tra status phu hop, khong raise, van co nghiem
  tot nhat hien co (partial solution) thay vi nan.
- history dung dinh dang de ve do thi.
"""

import itertools

import numpy as np
import pytest

from src.algorithms import dynamic_programming as dp
from src.core.config import STATUS_OK, STATUS_OUT_OF_MEMORY, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.model import MKPProblem
from src.core.validator import is_feasible


def selected_mask(problem, result):
    """Doi danh sach chi so mat hang thanh vector 0/1 de tai su dung validator."""
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


def brute_force(problem):
    """Gia tri toi uu that cho bai nho (chi dung trong test)."""
    best = 0.0
    for bits in itertools.product((0, 1), repeat=problem.n):
        x = np.array(bits, dtype=float)
        if np.all(problem.weights @ x <= problem.capacities + 1e-9):
            best = max(best, float(problem.profits @ x))
    return best


def test_dp_mknap1_nghiem_hop_le():
    problem = get_problem("mknap1.txt", 1)
    result = dp.solve(problem, time_limit=30, seed=1)

    assert result.status == STATUS_OK
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))

    assert result.total_profit > 0
    # Nghiem khong duoc tot hon gia tri tham chieu qua 1% (sai so lam tron).
    assert result.total_profit <= problem.z_ref * 1.01

    assert len(result.resource_usage) == problem.m
    assert len(set(result.selected_items)) == len(result.selected_items)


def test_dp_tinh_optimality_gap():
    problem = get_problem("mknap1.txt", 1)
    result = dp.solve(problem, time_limit=30, seed=1)

    expected = (problem.z_ref - result.total_profit) / problem.z_ref
    assert result.optimality_gap == pytest.approx(expected)


def test_dp_cung_seed_cho_cung_ket_qua():
    problem = get_problem("mknap1.txt", 1)

    first = dp.solve(problem, time_limit=30, seed=42)
    second = dp.solve(problem, time_limit=30, seed=42)

    assert first.status == STATUS_OK
    assert second.status == STATUS_OK
    assert first.total_profit == second.total_profit
    assert first.selected_items == second.selected_items


def test_dp_het_gio_tra_timeout_khong_raise():
    problem = get_problem("mknap1.txt", 1)

    # time_limit=0: dung ngay, khong raise; van tra nghiem tot nhat hien co.
    result = dp.solve(problem, time_limit=0, seed=1)

    assert result.status == STATUS_TIMEOUT
    assert np.isfinite(result.total_profit)
    assert result.total_profit >= 0
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))


def test_dp_het_bo_nho_tra_out_of_memory():
    problem = get_problem("mknap1.txt", 1)

    result = dp.solve(problem, time_limit=30, seed=1, memory_limit_mb=0)

    assert result.status == STATUS_OUT_OF_MEMORY
    assert np.isfinite(result.total_profit)
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))


def test_dp_bai_nho_khop_brute_force():
    problem = MKPProblem(
        name="khong_z_ref",
        n=4,
        m=2,
        profits=np.array([10.0, 7.0, 5.0, 3.0]),
        weights=np.array([
            [2.0, 3.0, 1.0, 4.0],
            [1.0, 1.0, 2.0, 1.0],
        ]),
        capacities=np.array([4.0, 3.0]),
        z_ref=None,
    )

    expected = brute_force(problem)
    result = dp.solve(problem, time_limit=10, seed=1)

    assert expected == 15.0
    assert result.status == STATUS_OK
    assert result.feasible is True
    assert result.total_profit == pytest.approx(expected)
    assert result.optimality_gap is None

    # Tat bound pruning khong duoc lam thay doi nghiem toi uu.
    no_prune = dp.solve(problem, time_limit=10, seed=1, use_bound_pruning=False)
    assert no_prune.total_profit == pytest.approx(expected)


def test_dp_history_dung_dinh_dang():
    problem = get_problem("mknap1.txt", 1)
    result = dp.solve(problem, time_limit=30, seed=3)

    assert len(result.history) > 0
    profits = []
    for entry in result.history:
        for key in ("step", "iteration", "phase", "best_profit", "profit", "elapsed"):
            assert key in entry
        assert entry["phase"] in ("init", "dp", "traceback", "failed", "exhausted")
        profits.append(entry["best_profit"])

    # best_profit la nghiem tot nhat -> khong giam theo thoi gian.
    assert profits == sorted(profits)
