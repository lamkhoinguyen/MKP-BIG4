"""Kiem tra tinh dong bo cua 4 thuat toan tren cung mot bai toan MKP.

Muc tieu (spec giai doan 5 + 6):
- Ca 4 thuat toan dung chung mo hinh, validator, evaluator va cau truc ket qua.
- Nghiem tra ve luon kha thi, khong vuot gia tri toi uu, status thuoc tap hop
  {ok, timeout, out_of_memory}.
- history dung dinh dang toi thieu {iteration: int, profit: float} va phan tu
  cuoi cung phan anh dung nghiem tra ve.
- Greedy/DP tat dinh; moi thuat toan ton trong time_limit.
"""

import itertools

import numpy as np
import pytest

from src.algorithms import ALGORITHM_NAMES, dynamic_programming, get_solver
from src.core.config import STATUS_OK, STATUS_OUT_OF_MEMORY, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.model import MKPProblem, MKPResult
from src.core.validator import is_feasible


VALID_STATUS = {STATUS_OK, STATUS_TIMEOUT, STATUS_OUT_OF_MEMORY}


def tiny_problem(z_ref=None):
    """Vi du 4 mat hang, 2 rang buoc; toi uu that = 15."""
    return MKPProblem(
        name="tiny4",
        n=4,
        m=2,
        profits=np.array([10.0, 7.0, 5.0, 3.0]),
        weights=np.array([
            [2.0, 3.0, 1.0, 4.0],
            [1.0, 1.0, 2.0, 1.0],
        ]),
        capacities=np.array([4.0, 3.0]),
        z_ref=z_ref,
    )


def brute_force(problem):
    best = 0.0
    for bits in itertools.product((0, 1), repeat=problem.n):
        x = np.array(bits, dtype=float)
        if np.all(problem.weights @ x <= problem.capacities + 1e-9):
            best = max(best, float(problem.profits @ x))
    return best


def selected_mask(problem, result):
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


@pytest.fixture(scope="module")
def optimum():
    return brute_force(tiny_problem())


@pytest.mark.parametrize("name", ALGORITHM_NAMES)
def test_ket_qua_thong_nhat(name, optimum):
    problem = tiny_problem(z_ref=optimum)
    result = get_solver(name)(problem, time_limit=2, seed=1)

    assert isinstance(result, MKPResult)
    assert result.status in VALID_STATUS
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))

    assert np.isfinite(result.total_profit)
    assert 0.0 <= result.total_profit <= optimum + 1e-9
    assert 1.0 <= result.total_profit  # bai de: moi thuat toan phai chon duoc hang

    assert len(result.resource_usage) == problem.m
    assert len(result.selected_items) == len(set(result.selected_items))
    assert all(0 <= j < problem.n for j in result.selected_items)

    expected_gap = (optimum - result.total_profit) / optimum
    assert result.optimality_gap == pytest.approx(expected_gap)

    assert result.history, f"{name} phai co history de ve do thi"
    for entry in result.history:
        assert isinstance(entry.get("iteration"), int)
        assert isinstance(entry.get("profit"), float)
    assert result.history[-1]["profit"] == pytest.approx(result.total_profit)


def test_dp_va_greedy_dat_toi_uu_tren_bai_4_mat_hang(optimum):
    problem = tiny_problem(z_ref=optimum)

    dp_result = dynamic_programming.solve(problem, time_limit=10, seed=1)
    greedy_result = get_solver("greedy")(problem, time_limit=10, seed=1)

    assert dp_result.total_profit == pytest.approx(optimum)
    assert greedy_result.total_profit == pytest.approx(optimum)


@pytest.mark.parametrize("name", ("greedy", "dynamic_programming"))
def test_thuat_toan_tat_dinh(name, optimum):
    problem = tiny_problem(z_ref=optimum)
    solver = get_solver(name)

    first = solver(problem, time_limit=10, seed=1)
    second = solver(problem, time_limit=10, seed=99)

    assert first.status == STATUS_OK
    assert second.status == STATUS_OK
    assert first.total_profit == second.total_profit
    assert first.selected_items == second.selected_items
    # Greedy khong ghi thoi gian vao history nen history phai giong het.
    if name == "greedy":
        assert first.history == second.history


@pytest.mark.parametrize("name", ALGORITHM_NAMES)
def test_ton_trong_time_limit(name):
    problem = get_problem("mknap2.txt", 1)
    limit = 3.0

    result = get_solver(name)(problem, time_limit=limit, seed=1)

    # Cho phep sai so nho cho buoc truy vet/hoan tat cuoi cung.
    assert result.runtime <= limit + 1.5


def test_dp_ghi_nhan_gioi_han_trang_thai(monkeypatch):
    problem = get_problem("mknap1.txt", 1)
    monkeypatch.setattr(dynamic_programming, "MAX_STATES", 1)

    result = dynamic_programming.solve(problem, time_limit=10, seed=1)

    assert result.status == STATUS_OUT_OF_MEMORY
    assert result.feasible is True
    assert np.isfinite(result.total_profit)
    assert result.peak_memory >= 0.0
    assert result.history[-1]["profit"] == pytest.approx(result.total_profit)
