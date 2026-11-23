"""Kiem tra 4 file algorithm dung interface chung (truoc khi implement).

Chay truoc khi giao task: phai xanh.
Sau khi member implement: solve() se raise NotImplementedError →
test_nhan_duoc_se_goi_duoc van dung (khong goi solve, chi kiem chu ky).
"""

import inspect

import pytest

from src.algorithms import ALGORITHM_NAMES, get_solver
from src.core.config import TIME_LIMIT_SECONDS
from src.core.model import MKPProblem, MKPResult


@pytest.mark.parametrize("name", ALGORITHM_NAMES)
def test_module_co_solve(name):
    solver = get_solver(name)
    assert callable(solver)


@pytest.mark.parametrize("name", ALGORITHM_NAMES)
def test_chu_ky_solve(name):
    solver = get_solver(name)
    sig = inspect.signature(solver)
    params = list(sig.parameters.values())

    # (problem, *, time_limit=..., seed=...)
    assert params[0].name == "problem"
    assert params[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

    names = [p.name for p in params]
    assert "time_limit" in names and "seed" in names

    for p in params[1:]:
        assert p.kind == inspect.Parameter.KEYWORD_ONLY, (
            f"{name}.{p.name} phai keyword-only"
        )

    assert params[1].default == TIME_LIMIT_SECONDS or params[1].default is inspect.Parameter.empty
    # seed mac dinh 0 neu co default
    seed = sig.parameters.get("seed")
    if seed is not None and seed.default is not inspect.Parameter.empty:
        assert seed.default == 0

    assert sig.return_annotation in (MKPResult, inspect.Signature.empty, "MKPResult")


@pytest.mark.parametrize("name", ALGORITHM_NAMES)
def test_ten_trong_registry(name):
    assert name in ALGORITHM_NAMES
    with pytest.raises(KeyError):
        get_solver("khong_ton_tai")


def test_get_solver_imports():
    # tat ca 4 import duoc, khong crash
    for name in ALGORITHM_NAMES:
        assert callable(get_solver(name))
