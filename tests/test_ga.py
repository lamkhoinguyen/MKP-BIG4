"""Kiem tra thuat toan Genetic Algorithm (GA) cua Thanh vien 3.

File nay test hanh vi that cua GA, khong chi kiem tra chu ky ham:
- Nghiem hop le, loi nhuan duong, khong vuot z_ref qua xa.
- Cung seed phai cho cung ket qua.
- Het time_limit phai tra STATUS_TIMEOUT, khong raise.
- history dung dinh dang de ve do thi.
"""

import numpy as np
import pytest

from src.algorithms import genetic_algorithm as ga
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.validator import is_feasible


@pytest.fixture
def fast_ga(monkeypatch):
    """Thu nho so the he/quan the de test chay nhanh.

    GA that dung MAX_GENERATIONS=500 nen mot bai nho cung mat khoang 30 giay.
    Test chi can kiem tra logic, nen giam tham so qua monkeypatch.
    Khong sua file genetic_algorithm.py cua Thanh vien 3.
    """
    monkeypatch.setattr(ga, "MAX_GENERATIONS", 10)
    monkeypatch.setattr(ga, "POPULATION_SIZE", 20)
    return ga


def selected_mask(problem, result):
    """Doi danh sach chi so mat hang thanh vector 0/1 de tai su dung validator."""
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


def test_ga_mknap1_nghiem_hop_le(fast_ga):
    problem = get_problem("mknap1.txt", 1)
    result = fast_ga.solve(problem, time_limit=30, seed=1)

    assert result.status == STATUS_OK
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))

    assert result.total_profit > 0
    # Nghiem cua GA khong duoc tot hon gia tri tham chieu qua 1% (sai so lam tron).
    assert result.total_profit <= problem.z_ref * 1.01

    assert len(result.resource_usage) == problem.m
    assert len(set(result.selected_items)) == len(result.selected_items)


def test_ga_tinh_optimality_gap(fast_ga):
    problem = get_problem("mknap1.txt", 1)
    result = fast_ga.solve(problem, time_limit=30, seed=1)

    expected = (problem.z_ref - result.total_profit) / problem.z_ref
    assert result.optimality_gap == pytest.approx(expected)


def test_ga_cung_seed_cho_cung_ket_qua(fast_ga):
    problem = get_problem("mknap1.txt", 1)

    first = fast_ga.solve(problem, time_limit=60, seed=42)
    second = fast_ga.solve(problem, time_limit=60, seed=42)

    # Voi cung seed va du thoi gian de chay xong, ket qua phai tai lap duoc.
    assert first.status == STATUS_OK
    assert second.status == STATUS_OK
    assert first.total_profit == second.total_profit
    assert first.selected_items == second.selected_items
    assert first.history == second.history


def test_ga_het_gio_tra_timeout_khong_raise(fast_ga):
    problem = get_problem("mknap1.txt", 1)

    # time_limit=0: GA phai dung ngay va tra ve nghiem rong, khong raise loi.
    result = fast_ga.solve(problem, time_limit=0, seed=1)

    assert result.status == STATUS_TIMEOUT
    assert result.feasible is True  # vector toan 0 luon thoa rang buoc
    assert result.total_profit == 0.0


def test_ga_history_dung_dinh_dang(fast_ga):
    problem = get_problem("mknap1.txt", 7)
    result = fast_ga.solve(problem, time_limit=60, seed=3)

    assert len(result.history) > 0
    profits = []
    for entry in result.history:
        assert "iteration" in entry
        assert "profit" in entry
        assert isinstance(entry["iteration"], int)
        profits.append(entry["profit"])

    # GA chi cap nhat best_profit khi tim duoc nghiem tot hon,
    # nen day loi nhuan tot nhat theo thoi gian phai khong giam.
    assert profits == sorted(profits)
