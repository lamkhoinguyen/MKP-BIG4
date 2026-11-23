"""Kiem tra thuat toan Simulated Annealing (SA) cua Thanh vien 4.

File nay test hanh vi that cua SA, khong chi kiem tra chu ky ham:
- Nghiem hop le, loi nhuan duong, khong vuot z_ref qua xa.
- Cung seed phai cho cung ket qua.
- Het time_limit phai tra STATUS_TIMEOUT, khong raise.
- history dung dinh dang de ve do thi (profit tot nhat khong giam,
  nhiet do khong tang).
"""

import numpy as np
import pytest

from src.algorithms import simulated_annealing as sa
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.model import MKPProblem
from src.core.validator import is_feasible


@pytest.fixture
def fast_sa(monkeypatch):
    """Giam so vong lap de test chay nhanh.

    SA that chay theo time_limit (toi da MAX_ITERATIONS=5_000_000), mot bai
    nho cung co the mat hang chuc giay. Test chi can kiem tra logic nen giam
    tham so qua monkeypatch, khong sua file simulated_annealing.py.
    """
    monkeypatch.setattr(sa, "MAX_ITERATIONS", 2000)
    return sa


def selected_mask(problem, result):
    """Doi danh sach chi so mat hang thanh vector 0/1 de tai su dung validator."""
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


def test_sa_mknap1_nghiem_hop_le(fast_sa):
    problem = get_problem("mknap1.txt", 1)
    result = fast_sa.solve(problem, time_limit=30, seed=1)

    assert result.status == STATUS_OK
    assert result.feasible is True
    assert is_feasible(problem, selected_mask(problem, result))

    assert result.total_profit > 0
    # Nghiem khong duoc tot hon gia tri tham chieu qua 1% (sai so lam tron).
    assert result.total_profit <= problem.z_ref * 1.01

    assert len(result.resource_usage) == problem.m
    assert len(set(result.selected_items)) == len(result.selected_items)


def test_sa_tinh_optimality_gap(fast_sa):
    problem = get_problem("mknap1.txt", 1)
    result = fast_sa.solve(problem, time_limit=30, seed=1)

    expected = (problem.z_ref - result.total_profit) / problem.z_ref
    assert result.optimality_gap == pytest.approx(expected)


def test_sa_cung_seed_cho_cung_ket_qua(fast_sa):
    problem = get_problem("mknap1.txt", 1)

    first = fast_sa.solve(problem, time_limit=60, seed=42)
    second = fast_sa.solve(problem, time_limit=60, seed=42)

    # Voi cung seed va du thoi gian chay xong, ket qua phai tai lap duoc.
    assert first.status == STATUS_OK
    assert second.status == STATUS_OK
    assert first.total_profit == second.total_profit
    assert first.selected_items == second.selected_items
    assert first.history == second.history


def test_sa_het_gio_tra_timeout_khong_raise(fast_sa):
    problem = get_problem("mknap1.txt", 1)

    # time_limit=0: SA phai dung ngay va tra nghiem rong, khong raise loi.
    result = fast_sa.solve(problem, time_limit=0, seed=1)

    assert result.status == STATUS_TIMEOUT
    assert result.feasible is True  # vector toan 0 luon thoa rang buoc
    assert result.total_profit == 0.0


def test_sa_history_dung_dinh_dang(fast_sa):
    problem = get_problem("mknap1.txt", 7)
    result = fast_sa.solve(problem, time_limit=60, seed=3)

    assert len(result.history) > 0
    profits = []
    temperatures = []

    for entry in result.history:
        for key in ("iteration", "profit", "current_profit", "temperature", "accepted"):
            assert key in entry
        assert isinstance(entry["iteration"], int)
        assert isinstance(entry["profit"], float)
        assert isinstance(entry["current_profit"], float)
        assert isinstance(entry["temperature"], float)
        assert isinstance(entry["accepted"], bool)
        profits.append(entry["profit"])
        temperatures.append(entry["temperature"])

    # profit ghi nhan nghiem tot nhat -> khong giam theo thoi gian.
    assert profits == sorted(profits)
    # Nhiet do chi giam (lich hinh hoc).
    assert temperatures == sorted(temperatures, reverse=True)


def test_sa_history_khop_ket_qua_cuoi(fast_sa):
    problem = get_problem("mknap1.txt", 7)
    result = fast_sa.solve(problem, time_limit=60, seed=5)

    # Sau buoc lap day tham lam cuoi, history phai phan anh dung nghiem tra ve.
    assert result.history[-1]["profit"] == pytest.approx(result.total_profit)


def test_sa_bai_khong_co_z_ref(fast_sa):
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

    result = fast_sa.solve(problem, time_limit=10, seed=1)

    assert result.optimality_gap is None
    assert result.feasible is True
    assert result.total_profit > 0
    assert result.history[-1]["profit"] == pytest.approx(result.total_profit)
