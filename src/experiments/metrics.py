"""Metrics tracking for MKP experiments.
Contains functions to calculate and store experiment metrics.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ExperimentMetrics:
    """Container for experiment metrics."""
    algorithm: str
    dataset: str
    problem: str
    seed: int
    time_limit: float
    profit: float
    optimality_gap: Optional[float]
    runtime: float
    peak_memory_mb: float
    feasible: bool
    status: str
    timestamp: str
    history_points: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "algorithm": self.algorithm,
            "dataset": self.dataset,
            "problem": self.problem,
            "seed": self.seed,
            "time_limit": self.time_limit,
            "profit": self.profit,
            "optimality_gap": self.optimality_gap,
            "runtime": self.runtime,
            "peak_memory_mb": self.peak_memory_mb,
            "feasible": self.feasible,
            "status": self.status,
            "timestamp": self.timestamp,
            "history_points": self.history_points,
        }

    @classmethod
    def from_result(
        cls,
        algorithm: str,
        dataset: str,
        problem: str,
        seed: int,
        time_limit: float,
        result: Any,
        timestamp: str,
    ) -> "ExperimentMetrics":
        """Create metrics from algorithm result."""
        return cls(
            algorithm=algorithm,
            dataset=dataset,
            problem=problem,
            seed=seed,
            time_limit=time_limit,
            profit=result.total_profit,
            optimality_gap=result.optimality_gap,
            runtime=result.runtime,
            peak_memory_mb=result.peak_memory,
            feasible=result.feasible,
            status=result.status,
            timestamp=timestamp,
            history_points=len(result.history),
        )

    def save_to_json(self, output_dir: Path) -> None:
        """Save metrics to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{self.algorithm}_{self.dataset}_{self.problem}_seed{self.seed}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def aggregate_metrics(metrics: List["ExperimentMetrics"]) -> Dict[str, Any]:
        """Calculate aggregate metrics across multiple runs."""
        if not metrics:
            return {}

        profits = [m.profit for m in metrics]
        gaps = [m.optimality_gap for m in metrics if m.optimality_gap is not None]
        runtimes = [m.runtime for m in metrics]
        feasible_rates = [
            1.0 if m.feasible else 0.0 for m in metrics
        ]
        mean_profit = sum(profits) / len(profits)
        std_profit = (
            sum((p - mean_profit) ** 2 for p in profits) / len(profits)
        ) ** 0.5 if len(profits) > 1 else 0.0

        return {
            "algorithm": metrics[0].algorithm,
            "dataset": metrics[0].dataset,
            "runs": len(metrics),
            "avg_profit": mean_profit,
            "std_profit": std_profit,
            "min_profit": min(profits),
            "max_profit": max(profits),
            "avg_gap": sum(gaps) / len(gaps) if gaps else None,
            "avg_runtime": sum(runtimes) / len(runtimes),
            "feasible_rate": sum(feasible_rates) / len(feasible_rates),
            "status_counts": {
                status: sum(1 for m in metrics if m.status == status)
                for status in {m.status for m in metrics}
            },
        }

    @staticmethod
    def save_summary(metrics: List["ExperimentMetrics"], output_dir: Path) -> None:
        """Save aggregated metrics summary."""
        summary = ExperimentMetrics.aggregate_metrics(metrics)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "experiment_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)


def calculate_experiment_metrics(algorithm: str, dataset: str, problem: str, seed: int, time_limit: float, result: Any) -> ExperimentMetrics:
    """Helper function to create metrics from algorithm result."""
    import datetime
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    return ExperimentMetrics.from_result(
        algorithm, dataset, problem, seed, time_limit, result, timestamp
    )