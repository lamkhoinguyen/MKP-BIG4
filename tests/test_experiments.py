"""Tests for experiments framework.
Tests experiment runner, metrics, and configuration.
"""

import pytest
import json
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.algorithms import greedy
from src.core.data_loader import get_problem
from src.experiments.experiment_runner import run_experiment
from src.experiments.metrics import ExperimentMetrics


class TestExperimentMetrics:
    """Test experiment metrics functionality."""

    def test_metrics_creation(self):
        """Test creating metrics from result."""
        # Setup
        problem = get_problem("mknap1.txt", 1)
        result = greedy.solve(problem, time_limit=1, seed=0)

        # Create metrics
        metrics = ExperimentMetrics.from_result(
            "greedy",
            "mknap1.txt",
            problem.name,
            0,
            1,
            result,
            "2026-11-17T00:00:00"
        )

        # Assertions
        assert metrics.algorithm == "greedy"
        assert metrics.dataset == "mknap1.txt"
        assert metrics.profit == result.total_profit
        assert metrics.optimality_gap == result.optimality_gap
        assert metrics.runtime == result.runtime
        assert metrics.status == result.status
        assert metrics.feasible == result.feasible

    def test_metrics_to_dict(self):
        """Test metrics to dictionary conversion."""
        metrics = ExperimentMetrics(
            algorithm="greedy",
            dataset="mknap1.txt",
            problem="mknap1_01",
            seed=0,
            time_limit=1,
            profit=100,
            optimality_gap=0.5,
            runtime=0.1,
            peak_memory_mb=10,
            feasible=True,
            status="ok",
            timestamp="2026-11-17T00:00:00",
            history_points=5
        )

        data = metrics.to_dict()
        assert data["algorithm"] == "greedy"
        assert data["profit"] == 100
        assert data["optimality_gap"] == 0.5
        assert data["status"] == "ok"

    def test_metrics_save_load(self):
        """Test saving and loading metrics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            # Create metrics
            metrics = ExperimentMetrics(
                algorithm="greedy",
                dataset="mknap1.txt",
                problem="mknap1_01",
                seed=0,
                time_limit=1,
                profit=100,
                optimality_gap=0.5,
                runtime=0.1,
                peak_memory_mb=10,
                feasible=True,
                status="ok",
                timestamp="2026-11-17T00:00:00",
                history_points=5
            )

            # Save metrics
            metrics.save_to_json(output_path)

            # Check file exists
            expected_file = output_path / "greedy_mknap1.txt_mknap1_01_seed0.json"
            assert expected_file.exists()

            # Load and verify
            with open(expected_file, "r") as f:
                loaded_data = json.load(f)
            assert loaded_data["algorithm"] == "greedy"
            assert loaded_data["profit"] == 100

    def test_metrics_aggregation(self):
        """Test metrics aggregation."""
        # Create multiple metrics
        metrics_list = []
        for i in range(3):
            metrics_list.append(ExperimentMetrics(
                algorithm="greedy",
                dataset="mknap1.txt",
                problem=f"mknap1_0{i+1}",
                seed=i,
                time_limit=1,
                profit=100 + i * 10,
                optimality_gap=0.5 - i * 0.1,
                runtime=0.1 + i * 0.01,
                peak_memory_mb=10,
                feasible=True,
                status="ok",
                timestamp="2026-11-17T00:00:00",
                history_points=5
            ))

        # Aggregate
        summary = ExperimentMetrics.aggregate_metrics(metrics_list)

        # Assertions
        assert summary["avg_profit"] == 110.0
        assert summary["min_profit"] == 100
        assert summary["max_profit"] == 120
        assert summary["runs"] == 3
        assert summary["feasible_rate"] == 1.0


class TestExperimentRunner:
    """Test experiment runner functionality."""

    def test_problem_resolution(self):
        """Test that problems are resolved correctly."""
        from src.algorithms import get_solver
        from src.core.data_loader import load_problems
        from src.core.config import DATA_DIR

        # Load mknap1.txt
        dataset_path = DATA_DIR / "mknap1.txt"
        problems = load_problems(dataset_path)

        # Check first problem
        assert len(problems) == 7
        assert problems[0].name == "mknap1_01"
        assert problems[0].n == 6
        assert problems[0].z_ref == 3800

    def test_experiment_with_single_problem(self):
        """Test running experiment with single problem."""
        from src.algorithms import get_solver

        solver = get_solver("greedy")
        problem = get_problem("mknap1.txt", 1)

        result = solver(problem, time_limit=1, seed=0)

        assert result.feasible is True
        assert result.status == "ok"
        assert result.total_profit > 0
        assert result.optimality_gap == 0.0

    def test_experiment_timeout(self):
        """Test experiment timeout handling."""
        from src.algorithms import get_solver

        solver = get_solver("greedy")
        problem = get_problem("mknap1.txt", 1)

        result = solver(problem, time_limit=0, seed=0)

        # Should return timeout with empty solution
        assert result.status == "timeout"
        assert result.feasible is True
        assert result.total_profit == 0.0

    def test_experiment_seed_reproducibility(self):
        """Test that same seed produces same result."""
        from src.algorithms import get_solver

        solver = get_solver("greedy")
        problem = get_problem("mknap1.txt", 1)

        result1 = solver(problem, time_limit=1, seed=42)
        result2 = solver(problem, time_limit=1, seed=42)

        # Should produce identical results
        assert result1.total_profit == result2.total_profit
        assert result1.selected_items == result2.selected_items
        assert result1.status == result2.status

    def test_experiment_invalid_dataset(self):
        """Test handling of invalid dataset."""
        from src.experiments.experiment_runner import resolve_dataset

        with pytest.raises(SystemExit):
            resolve_dataset("nonexistent_file.txt")


class TestIntegration:
    """Integration tests for the whole experiment workflow."""

    def test_full_workflow(self):
        """Test complete experiment workflow."""
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)

            # Load problem
            problem = get_problem("mknap1.txt", 1)

            # Run algorithm
            from src.algorithms import get_solver
            solver = get_solver("greedy")
            result = solver(problem, time_limit=1, seed=0)

            # Create metrics
            metrics = ExperimentMetrics.from_result(
                "greedy",
                "mknap1.txt",
                problem.name,
                0,
                1,
                result,
                "2026-11-17T00:00:00"
            )

            # Save metrics
            metrics.save_to_json(output_path)

            # Verify save
            expected_file = output_path / "greedy_mknap1.txt_mknap1_01_seed0.json"
            assert expected_file.exists()

            # Load and verify content
            with open(expected_file, "r") as f:
                loaded = json.load(f)
            assert loaded["algorithm"] == "greedy"
            assert loaded["profit"] == result.total_profit

    def test_multiple_seeds(self):
        """Test running with multiple seeds."""
        from src.algorithms import get_solver

        solver = get_solver("greedy")
        problem = get_problem("mknap1.txt", 1)

        results = []
        for seed in [0, 1, 2]:
            result = solver(problem, time_limit=1, seed=seed)
            results.append(result)

        # All should have same profit (deterministic algorithm)
        assert all(r.total_profit == results[0].total_profit for r in results)
        assert len(results) == 3


class TestCliSaving:
    """Test automatic result saving from CLI."""

    def test_cli_saves_results(self, monkeypatch, capsys):
        """CLI should save per-run JSON and summary when run."""
        from src.experiments.experiment_runner import run_experiment

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "saved"
            monkeypatch.setattr(
                sys,
                "argv",
                [
                    "experiments",
                    "greedy",
                    "mknap1",
                    "1",
                    "-t",
                    "1",
                    "--out",
                    str(out_dir),
                ],
            )

            code = run_experiment()

            assert code == 0
            run_file = out_dir / "greedy_mknap1.txt_mknap1_01_seed0.json"
            summary_file = out_dir / "experiment_summary.json"
            assert run_file.exists()
            assert summary_file.exists()

            with open(run_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["algorithm"] == "greedy"
            assert data["dataset"] == "mknap1.txt"
            assert data["problem"] == "mknap1_01"
            assert data["feasible"] is True

            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
            assert summary["runs"] == 1
            assert summary["algorithm"] == "greedy"

    def test_cli_no_save(self, monkeypatch, capsys):
        """--no-save should not write anything."""
        from src.experiments.experiment_runner import run_experiment

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "not_saved"
            monkeypatch.setattr(
                sys,
                "argv",
                [
                    "experiments",
                    "greedy",
                    "mknap1",
                    "1",
                    "-t",
                    "1",
                    "--out",
                    str(out_dir),
                    "--no-save",
                ],
            )

            code = run_experiment()

            assert code == 0
            assert not out_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])