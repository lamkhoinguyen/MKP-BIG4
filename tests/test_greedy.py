"""Kiem tra thuat toan Greedy cua Thanh vien 1.

File nay test hanh vi that cua Greedy:
- Nghiem hop le, khong vuot z_ref, gap tinh dung.
- Greedy tat dinh: cung bai + cung seed cho cung ket qua (seed khong doi ket qua).
- Het time_limit phai tra STATUS_TIMEOUT, khong raise, van co nghiem hop le.
- history dung dinh dang de ve do thi (profit khong giam).
- Truong hop bien: mat hang khong vua, trong luong 0, bai khong co z_ref.
"""

import numpy as np
import pytest

from src.algorithms import greedy
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.model import MKPProblem
from src.core.validator import is_feasible


def selected_mask(problem, result):
    """Doi danh sach chi so mat hang thanh vector 0/1 de tai su dung validator."""
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


def synthetic(profits, weights, capacities, z_ref=None):
    weights = np.atleast_2d(np.asarray(weights, dtype=float))
    return MKPProblem(
        name="test_greedy",
        n=len(profits),
        m=weights.shape[0],
        profits=np.asarray(profits, dtype=float),
        weights=weights,
        capacities=np.asarray(capacities, dtype=float),
        z_ref=z_ref,
    )


def test_greedy_mknap1_nghiem_hop_le():
    problem = get_problem("mknap1.txt", 1)
    result = greedy.solve(problem, time_limit=30, seed=1)

    assert result.status == STATUS_OK
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))

    assert result.total_profit > 0
    # Khong duoc tot hon gia tri tham chieu (sai so lam tron).
    assert result.total_profit <= problem.z_ref * 1.01

    assert len(result.resource_usage) == problem.m
    assert len(set(result.selected_items)) == len(result.selected_items)


def test_greedy_tinh_optimality_gap():
    problem = get_problem("mknap1.txt", 1)
    result = greedy.solve(problem, time_limit=30, seed=1)

    expected = (problem.z_ref - result.total_profit) / problem.z_ref
    assert result.optimality_gap == pytest.approx(expected)


def test_greedy_tat_dinh_khong_phu_thuoc_seed():
    problem = get_problem("mknapcb1.txt", 1)

    first = greedy.solve(problem, time_limit=30, seed=0)
    second = greedy.solve(problem, time_limit=30, seed=42)

    assert first.total_profit == second.total_profit
    assert first.selected_items == second.selected_items
    assert first.history == second.history


def test_greedy_het_gio_tra_timeout_khong_raise():
    problem = get_problem("mknap1.txt", 1)

    # time_limit=0: dung ngay, khong raise; van tra nghiem hop le (x co the rong).
    result = greedy.solve(problem, time_limit=0, seed=1)

    assert result.status == STATUS_TIMEOUT
    assert np.isfinite(result.total_profit)
    assert result.total_profit >= 0
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))


def test_greedy_history_dung_dinh_dang():
    problem = get_problem("mknap1.txt", 1)
    result = greedy.solve(problem, time_limit=30, seed=3)

    assert len(result.history) == len(result.selected_items)
    profits = []
    for entry in result.history:
        for key in ("iteration", "profit"):
            assert key in entry
        assert entry["profit"] <= result.total_profit + 1e-9
        profits.append(entry["profit"])

    # Moi vong chon them 1 mat hang co loi nhuan duong -> profit tang dan.
    assert profits == sorted(profits)
    assert result.history[-1]["profit"] == pytest.approx(result.total_profit)


def test_greedy_chon_theo_diem_uu_tien_nhieu_rang_buoc():
    # Mat hang 0: profit cao nhung ton kemnhieu tai nguyen (2 rang buoc deu chat).
    # Mat hang 1: profit thap hon nhung rat re -> phai duoc chon truoc.
    problem = synthetic(
        profits=[100, 40],
        weights=[[9, 1], [9, 1]],
        capacities=[9, 9],
    )
    result = greedy.solve(problem, time_limit=10, seed=1)

    assert result.selected_items == [1]
    assert result.total_profit == pytest.approx(40)


def test_greedy_bo_qua_mat_hang_khong_vua():
    problem = synthetic(
        profits=[10, 10, 10],
        weights=[[5, 5, 5]],
        capacities=[7],
    )
    result = greedy.solve(problem, time_limit=10, seed=1)

    assert result.feasible is True
    assert len(result.selected_items) == 1
    assert result.total_profit == pytest.approx(10)


def test_greedy_mat_hang_trong_luong_0_va_profit_0():
    # Mat hang 0 trong luong 0 -> luon vua; mat hang 1 profit 0 -> khong chon.
    problem = synthetic(
        profits=[5, 0, 3],
        weights=[[0, 1, 1]],
        capacities=[1],
    )
    result = greedy.solve(problem, time_limit=10, seed=1)

    assert result.feasible is True
    assert 0 in result.selected_items
    assert 1 not in result.selected_items
    assert result.total_profit == pytest.approx(8)


def test_greedy_bai_khong_co_z_ref_thi_gap_none():
    problem = synthetic(
        profits=[4, 3, 2],
        weights=[[2, 2, 1]],
        capacities=[3],
        z_ref=None,
    )
    result = greedy.solve(problem, time_limit=10, seed=1)

    assert result.optimality_gap is None
    assert result.feasible is True


def test_greedy_capacity_0_tra_nghiem_rong():
    problem = synthetic(
        profits=[4, 3],
        weights=[[1, 1]],
        capacities=[0],
    )
    result = greedy.solve(problem, time_limit=10, seed=1)

    assert result.selected_items == []
    assert result.total_profit == pytest.approx(0)
    assert result.feasible is True
