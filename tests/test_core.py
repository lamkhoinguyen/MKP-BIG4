"""Kiem tra core: model, evaluator, validator, data_loader, config."""

import numpy as np
import pytest

from src.core.config import BENCHMARK_PROBLEMS, STATUS_OK, STATUS_TIMEOUT
from src.core.data_loader import get_problem, load_problems
from src.core.evaluator import (
    build_result,
    compute_optimality_gap,
    compute_profit,
    compute_resource_usage,
)
from src.core.model import MKPProblem, MKPResult
from src.core.validator import find_violations, is_binary, is_feasible


@pytest.fixture
def tiny_problem() -> MKPProblem:
    """2 hang, 1 rang buoc — de tinh tay."""
    return MKPProblem(
        name="tiny",
        n=2,
        m=1,
        profits=np.array([10.0, 20.0]),
        weights=np.array([[5.0, 6.0]]),
        capacities=np.array([10.0]),
        z_ref=20.0,
    )


class TestModel:
    def test_shapes_ok(self, tiny_problem):
        assert tiny_problem.profits.shape == (2,)
        assert tiny_problem.weights.shape == (1, 2)
        assert tiny_problem.capacities.shape == (1,)

    def test_bad_shape_raises(self):
        with pytest.raises(ValueError):
            MKPProblem(
                name="bad",
                n=3,
                m=1,
                profits=np.array([1.0, 2.0]),
                weights=np.array([[1.0, 1.0]]),
                capacities=np.array([1.0]),
            )


class TestEvaluator:
    def test_profit(self, tiny_problem):
        x = np.array([1, 1])
        assert compute_profit(tiny_problem, x) == 30.0

    def test_usage(self, tiny_problem):
        x = np.array([1, 0])
        assert compute_resource_usage(tiny_problem, x).tolist() == [5.0]

    def test_gap_auto(self, tiny_problem):
        gap = compute_optimality_gap(tiny_problem, 10.0)
        assert gap == pytest.approx((20.0 - 10.0) / 20.0)

    def test_build_result_fills_gap(self, tiny_problem):
        r = build_result(tiny_problem, np.array([1, 1]), runtime=0.1)
        assert r.total_profit == 30.0
        assert r.optimality_gap == pytest.approx(-0.5)
        assert r.feasible is False  # 5+6=11 > 10
        assert r.status == STATUS_OK

    def test_build_result_ok_vector(self, tiny_problem):
        r = build_result(tiny_problem, np.array([1, 0]))
        assert r.feasible is True
        assert r.selected_items == [0]
        assert r.optimality_gap == pytest.approx(0.5)

    def test_wrong_length_raises(self, tiny_problem):
        with pytest.raises(ValueError):
            build_result(tiny_problem, np.array([1, 1, 1]))


class TestValidator:
    def test_binary(self):
        assert is_binary(np.array([0, 1, 1]))
        assert not is_binary(np.array([0, 2]))

    def test_violations(self, tiny_problem):
        x = np.array([1, 1])  # usage 11 > 10
        assert find_violations(tiny_problem, x) == [0]
        assert not is_feasible(tiny_problem, x)
        assert is_feasible(tiny_problem, np.array([1, 0]))


class TestDataLoader:
    def test_mknap1_first(self):
        p = get_problem("mknap1.txt", 1)
        assert p.n == 6 and p.m == 10
        assert p.z_ref == 3800.0

    def test_mknap2_literature(self):
        problems = load_problems("data/mknap/mknap2.txt")
        assert len(problems) == 48
        assert problems[0].name == "SENTO1"

    def test_mknapcb_z_ref_from_reference_file(self):
        p = get_problem("mknapcb1.txt", 1)
        assert p.z_ref == 24381.0

    def test_benchmark_all_have_z_ref(self):
        for file_name, k in BENCHMARK_PROBLEMS:
            p = get_problem(file_name, k)
            assert p.z_ref is not None, f"{file_name}#{k}"

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            get_problem("mknap1.txt", 99)

    def test_cache_returns_same_object(self):
        a = get_problem("mknap1.txt", 1)
        b = get_problem("mknap1.txt", 1)
        assert a is b


class TestContractTypes:
    def test_result_is_dataclass(self, tiny_problem):
        r = build_result(tiny_problem, np.array([1, 0]))
        assert isinstance(r, MKPResult)
        d = r.to_dict()
        assert set(d) >= {
            "selected_items",
            "total_profit",
            "resource_usage",
            "feasible",
            "runtime",
            "optimality_gap",
            "history",
            "status",
        }

    def test_status_constants(self):
        assert STATUS_OK == "ok"
        assert STATUS_TIMEOUT == "timeout"
