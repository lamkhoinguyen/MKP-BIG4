
"""Genetic Algorithm - Thanh vien 3.

Giai bai toan MKP bang GA nhi phan va Greedy Repair.
"""

import time
import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult


POPULATION_SIZE = 100
MAX_GENERATIONS = 500
CROSSOVER_RATE = 0.85
ELITE_COUNT = 2
TOURNAMENT_SIZE = 3

# Trang thai hien thi khi het gioi han thoi gian.
STATUS_NA = "N/A"


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

    # Sap xep mot lan de tang hieu suat.
    remove_order = np.argsort(scores)
    add_order = np.argsort(-scores)

    def is_timeout():
        return time.perf_counter() >= deadline

    def feasible(x):
        return bool(np.all(weights @ x <= capacities))

    def repair(x):
        """Sua nghiem; tra ve None khi het thoi gian."""
        x = x.copy()

        # Loai cac kien hang co do uu tien thap.
        for j in remove_order:
            if is_timeout():
                return None

            if feasible(x):
                break

            if x[j] == 1:
                x[j] = 0

        # Bo sung cac kien hang co do uu tien cao.
        for j in add_order:
            if is_timeout():
                return None

            if x[j] == 0:
                x[j] = 1

                if not feasible(x):
                    x[j] = 0

        return x

    def fitness(x):
        return float(profits @ x)

    def tournament(population, values):
        ids = rng.integers(
            0,
            len(population),
            size=TOURNAMENT_SIZE
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
        rate = min(
            0.1,
            max(0.005, 1.0 / max(n, 1))
        )

        mask = rng.random(n) < rate
        x[mask] = 1 - x[mask]

        return x

    # Nghiem ban dau an toan.
    best_x = np.zeros(n, dtype=np.int8)
    best_profit = fitness(best_x)
    history = []
    timed_out = False

    if is_timeout():
        return build_result(
            problem,
            best_x,
            runtime=time.perf_counter() - start,
            history=history,
            status=STATUS_NA,
        )

    # Tao quan the ban dau.
    population = []

    for i in range(POPULATION_SIZE):
        if is_timeout():
            timed_out = True
            break

        if i == 0:
            x = np.zeros(n, dtype=np.int8)
        else:
            x = rng.integers(
                0, 2, size=n, dtype=np.int8
            )

        x = repair(x)

        if x is None:
            timed_out = True
            break

        population.append(x)

        value = fitness(x)

        if value > best_profit:
            best_profit = value
            best_x = x.copy()

    if not population:
        population = [best_x.copy()]

    # Vong lap tien hoa.
    if not timed_out:

        for generation in range(
            1, MAX_GENERATIONS + 1
        ):

            if is_timeout():
                timed_out = True
                break

            values = np.array([
                fitness(x) for x in population
            ])

            order = np.argsort(-values)

            new_population = [
                population[i].copy()
                for i in order[:ELITE_COUNT]
            ]

            while len(new_population) < POPULATION_SIZE:

                if is_timeout():
                    timed_out = True
                    break

                parent1 = tournament(
                    population, values
                )
                parent2 = tournament(
                    population, values
                )

                child1, child2 = crossover(
                    parent1, parent2
                )

                for child in (child1, child2):

                    if is_timeout():
                        timed_out = True
                        break

                    child = mutate(child)
                    child = repair(child)

                    if child is None:
                        timed_out = True
                        break

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

    if runtime >= max(0.0, time_limit):
        timed_out = True

    # Het thoi gian -> N/A
    # Hoan thanh binh thuong -> ok
    status = STATUS_NA if timed_out else STATUS_OK

    return build_result(
        problem,
        best_x,
        runtime=runtime,
        history=history,
        status=status,
    )
