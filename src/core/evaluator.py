"""Tinh loi nhuan va luong tai nguyen da dung"""
from typing import Optional

import numpy as np
from src.core.model import MKPProblem, MKPResult
from src.core.config import STATUS_OK

def as_binary_vector(problem: MKPProblem, x) -> np.ndarray:
    x = np.asarray(x)
    if (x.shape != (problem.n,)):
        raise ValueError(
            f"x phai la vector nhi phan do dai n={problem.n}, "
            f"nhung nhan duoc shape {x.shape}"
        )
    return x 

def compute_profit(problem: MKPProblem, x) -> float:
    """Tong loi nhuan Z = tong profits[j] * x[j]."""
    x = as_binary_vector(problem, x)
    return float(problem.profits @ x)

def compute_resource_usage(problem: MKPProblem, x) -> np.ndarray:
    """Luong tai nguyen da dung R_i = tong weights[i][j] * x[j], moi rang buoc mot gia tri."""
    x = as_binary_vector(problem, x)
    return problem.weights @ x

def compute_optimality_gap(problem: MKPProblem, total_profit: float) -> Optional[float]:
    """(z_ref - z) / z_ref; None neu khong co z_ref."""
    if problem.z_ref is None or problem.z_ref <= 0:
        return None
    return float((problem.z_ref - total_profit) / problem.z_ref)


def build_result(problem, x, *, runtime=0.0, history=None, status=STATUS_OK, optimality_gap=None) -> MKPResult:
    from src.core.validator import is_feasible
    x = as_binary_vector(problem, x)
    total_profit = compute_profit(problem, x)
    if optimality_gap is None:
        optimality_gap = compute_optimality_gap(problem, total_profit)
    return MKPResult(
        selected_items=np.flatnonzero(x).tolist(),
        total_profit=total_profit,
        resource_usage=compute_resource_usage(problem, x).tolist(),
        feasible=is_feasible(problem, x),
        runtime=runtime,
        optimality_gap=optimality_gap,
        history=history if history is not None else [],
        status=status,
    )