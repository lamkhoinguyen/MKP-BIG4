
"""Genetic Algorithm - Thanh vien 3.

Giai bai toan MKP bang GA nhi phan va Greedy Repair.
"""

import time
import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult


POPULATION_SIZE = 100
MAX_GENERATIONS = 500
CROSSOVER_RATE = 0.85
ELITE_COUNT = 2
TOURNAMENT_SIZE = 3


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    start = time.perf_counter()
    deadline = start + max(0.0, time_limit)
    rng = np.random.default_rng(seed)

    n = problem.n
    profits = problem.profits
    weights = problem.weights
    capacities = problem.capacities

    # Diem uu tien theo loi nhuan / tai nguyen.
    safe_capacities = np.maximum(capacities, 1e-12)
    normalized_weights = weights / safe_capacities[:, None]
    resource_cost = np.sum(normalized_weights, axis=0)
    scores = profits / np.maximum(resource_cost, 1e-12)

    def feasible(x):
        return bool(np.all(weights @ x <= capacities))

    def repair(x):
        """Loai bot hang vi pham, sau do bo sung hang phu hop."""
        x = x.copy()

        # Loai hang co diem uu tien thap truoc.
        for j in np.argsort(scores):
            if feasible(x):
                break
            if x[j] == 1:
                x[j] = 0

        # Bo sung hang co diem uu tien cao truoc.
        for j in np.argsort(-scores):
            if x[j] == 0:
                x[j] = 1
                if not feasible(x):
                    x[j] = 0

        return x

    def fitness(x):
        return float(profits @ x)

    def tournament(population, values):
        ids = rng.integers(
            0, len(population), size=TOURNAMENT_SIZE
        )
        winner = ids[np.argmax(values[ids])]
        return population[winner].copy()

    def crossover(a, b):
        if n < 2 or rng.random() >= CROSSOVER_RATE:
            return a.copy(), b.copy()

        if n == 2:
            left, right = 1, 2
        else:
            left, right = sorted(
                rng.choice(
                    np.arange(1, n + 1),
                    size=2,
                    replace=False
                )
            )

        child1 = a.copy()
        child2 = b.copy()

        child1[left:right] = b[left:right]
        child2[left:right] = a[left:right]

        return child1, child2

    def mutate(x):
        rate = min(0.1, max(0.005, 1.0 / max(n, 1)))
        mask = rng.random(n) < rate
        x[mask] = 1 - x[mask]
        return x

    # Nghiem ban dau an toan.
    best_x = np.zeros(n, dtype=np.int8)
    best_profit = fitness(best_x)
    history = []

    if time.perf_counter() >= deadline:
        return build_result(
            problem,
            best_x,
            runtime=time.perf_counter() - start,
            history=history,
            status=STATUS_TIMEOUT,
        )

    # Tao quan the ban dau.
    population = []
    for i in range(POPULATION_SIZE):
        if time.perf_counter() >= deadline:
            break

        if i == 0:
            x = np.zeros(n, dtype=np.int8)
        else:
            x = rng.integers(0, 2, size=n, dtype=np.int8)

        x = repair(x)
        population.append(x)

        value = fitness(x)
        if value > best_profit:
            best_profit = value
            best_x = x.copy()

    if not population:
        population = [best_x.copy()]

    timed_out = False

    for generation in range(1, MAX_GENERATIONS + 1):
        if time.perf_counter() >= deadline:
            timed_out = True
            break

        values = np.array([fitness(x) for x in population])
        order = np.argsort(-values)

        new_population = [
            population[i].copy()
            for i in order[:ELITE_COUNT]
        ]

        while len(new_population) < POPULATION_SIZE:
            if time.perf_counter() >= deadline:
                timed_out = True
                break

            parent1 = tournament(population, values)
            parent2 = tournament(population, values)

            child1, child2 = crossover(parent1, parent2)

            for child in (child1, child2):
                if time.perf_counter() >= deadline:
                    timed_out = True
                    break

                child = mutate(child)
                child = repair(child)

                value = fitness(child)
                if value > best_profit:
                    best_profit = value
                    best_x = child.copy()

                new_population.append(child)

                if len(new_population) >= POPULATION_SIZE:
                    break

            if timed_out:
                break

        history.append({
            "iteration": generation,
            "profit": float(best_profit),
        })

        if timed_out:
            break

        population = new_population

    runtime = time.perf_counter() - start
    status = STATUS_TIMEOUT if timed_out else STATUS_OK

    return build_result(
        problem,
        best_x,
        runtime=runtime,
        history=history,
        status=status,
    )
