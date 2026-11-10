"""Kiem tra nghiem co thoa moi rang buoc hay khong."""
import numpy as np
from src.core.evaluator import compute_resource_usage
from src.core.model import MKPProblem

def find_violations(problem: MKPProblem, x) -> list:
    usage = compute_resource_usage(problem, x)
    return np.flatnonzero(usage > problem.capacities).tolist()

def is_binary(x) -> bool:
    """ x_j phai thuoc {0, 1}"""
    return bool(np.isin(np.asarray(x), (0, 1)).all())

def is_feasible(problem: MKPProblem, x) -> bool:
    """Nghiem hop le khi moi R_i <= b_i."""
    return is_binary(x) and len(find_violations(problem, x)) == 0