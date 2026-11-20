"""Tests for Giai doan 9: comparison module.
Khong sua du lieu goc trong results/ va khong sua test cu.
"""

import csv
import json
from pathlib import Path

import pytest

from src.experiments.comparison import (
    ALGORITHMS,
    PROBLEM_COLUMNS,
    build_comparison,
    build_group_rows,
    build_live_comparison,
    build_problem_rows,
    load_experiment_runs,
    load_session_meta,
    load_summaries,
    validate_session_meta,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def test_load_summaries_all_algorithms():
    data, meta = load_summaries(RESULTS)
    assert set(data) == set(ALGORITHMS)
    for algo in ALGORITHMS:
        assert len(data[algo]) == 325
        assert meta[algo]["time_limit"] == 60.0
        assert meta[algo]["seeds"] == [1]


def test_build_problem_rows():
    data, _ = load_summaries(RESULTS)
    rows = build_problem_rows(data)
    assert len(rows) == 325
    assert set(PROBLEM_COLUMNS).issubset(rows[0].keys())
    for row in rows:
        assert row["best_algo_by_profit"] in ALGORITHMS
        assert row["greedy_best"] > 0
        assert row["sa_best"] > 0


def test_build_group_rows():
    data, _ = load_summaries(RESULTS)
    groups = build_group_rows(build_problem_rows(data))
    assert [group["group"] for group in groups] == [
        "tat ca",
        "nho (n<=100)",
        "trung binh (100<n<=250)",
        "lon (n>250)",
    ]
    overall = groups[0]
    assert overall["problems"] == 325
    assert overall["dp_oom"] == 274
    assert overall["ga_best_count"] > overall["greedy_best_count"]
    assert overall["ga_avg_gap_pct"] < overall["sa_avg_gap_pct"]


def test_build_comparison_outputs(tmp_path):
    paths = build_comparison(RESULTS, tmp_path)
    names = {path.name for path in paths}
    assert "comparison_by_problem.csv" in names
    assert "comparison_by_algorithm.csv" in names
    assert "stability_ga_sa.csv" in names
    assert "comparison_report.md" in names
    assert sum(1 for name in names if name.endswith(".png")) == 5

    with open(tmp_path / "comparisons" / "comparison_by_problem.csv",
              "r", encoding="utf-8-sig") as handle:
        problem_rows = list(csv.DictReader(handle))
    assert len(problem_rows) == 325

    with open(tmp_path / "reports" / "comparison_report.md",
              "r", encoding="utf-8") as handle:
        report = handle.read()
    assert "325" in report
    assert "Genetic Algorithm" in report
    assert "Giai doan" not in report or "Ket luan" in report


def _write_experiment_json(folder, algo, dataset, problem, seed, profit,
                           gap, runtime, status="ok"):
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "algorithm": algo,
        "dataset": dataset,
        "problem": problem,
        "seed": seed,
        "time_limit": 30.0,
        "profit": profit,
        "optimality_gap": gap,
        "runtime": runtime,
        "peak_memory_mb": 10.0,
        "feasible": True,
        "status": status,
        "timestamp": "2026-01-01T00:00:00",
        "history_points": 5,
    }
    path = folder / f"{algo}_{dataset}_{problem}_seed{seed}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_live_mode_takes_intersection_of_four_algorithms(tmp_path):
    root = tmp_path / "experiments"
    for algo in ("greedy", "dp", "ga", "sa"):
        _write_experiment_json(root / algo, algo, "mknapcb4.txt",
                               "mknapcb4_01", 1, 23064, 0.0, 0.1)
    _write_experiment_json(root / "greedy", "greedy", "mknapcb4.txt",
                           "mknapcb4_02", 1, 22000, 0.05, 0.1)

    _write_experiment_json(root / "dynamic_programming",
                           "dynamic_programming", "mknapcb4.txt",
                           "mknapcb4_01", 1, 23064, 0.0, 0.1)

    data, meta, missing = load_experiment_runs(
        tmp_path, experiments_dir=root
    )
    assert len(data["greedy"]) == 1
    assert ("mknapcb4.txt", "mknapcb4_01") in data["sa"]
    assert ("mknapcb4.txt", "mknapcb4_02") not in data["greedy"]
    assert missing == 1
    assert meta["ga"]["seeds"] == [1]


def test_live_mode_generates_outputs_for_one_problem(tmp_path):
    root = tmp_path / "experiments"
    for algo in ("greedy", "dp", "ga", "sa"):
        _write_experiment_json(
            root / algo, algo, "mknapcb4.txt", "mknapcb4_01", 1,
            22000 + {"greedy": 0, "dp": 500, "ga": 1000, "sa": 200}[algo],
            0.05, 0.2,
        )

    out = tmp_path / "out"
    paths = build_live_comparison(
        tmp_path, out, experiments_dir=root,
        data_dir=ROOT / "data" / "mknap",
    )
    names = {path.name for path in paths}
    assert "comparison_live_by_problem.csv" in names
    assert "comparison_live_by_algorithm.csv" in names
    assert "comparison_live_report.md" in names

    with open(out / "comparisons" / "comparison_live_by_problem.csv",
              "r", encoding="utf-8-sig") as handle:
        assert len(list(csv.DictReader(handle))) == 1
    report = (out / "reports" / "comparison_live_report.md").read_text(
        encoding="utf-8"
    )
    assert "So bai duoc so sanh: 1" in report


def _session_meta(seed=1):
    return {
        algo: {
            "datasets": ["mknapcb4.txt"],
            "problem": "1",
            "time_limit": 5.0,
            "seed": seed,
        }
        for algo in ("greedy", "dp", "ga", "sa")
    }


def test_session_mode_uses_only_that_session(tmp_path):
    root = tmp_path / "sessions" / "demo"
    for algo in ("greedy", "dp", "ga", "sa"):
        _write_experiment_json(root / algo, algo, "mknapcb4.txt",
                               "mknapcb4_01", 1, 23000, 0.01, 0.2)
    (root / "session_meta.json").write_text(
        json.dumps(_session_meta()), encoding="utf-8"
    )
    meta = load_session_meta(root)
    validate_session_meta(meta)

    out = tmp_path / "out"
    paths = build_live_comparison(
        tmp_path, out, experiments_dir=root, session_name="demo",
        session_meta=meta, data_dir=ROOT / "data" / "mknap",
    )
    assert any(path.name == "comparison_live_report.md" for path in paths)
    report = (out / "reports" / "comparison_live_report.md").read_text(
        encoding="utf-8"
    )
    assert "Phien: demo" in report
    assert "So bai duoc so sanh: 1" in report
    with open(out / "comparisons" / "comparison_live_by_problem.csv",
              "r", encoding="utf-8-sig") as handle:
        assert len(list(csv.DictReader(handle))) == 1


def test_session_meta_rejects_mixed_parameters():
    meta = _session_meta()
    meta["sa"]["seed"] = 2
    with pytest.raises(SystemExit, match="khong dong nhat"):
        validate_session_meta(meta)


def test_report_uses_computed_values(tmp_path):
    build_comparison(RESULTS, tmp_path)
    report = (tmp_path / "reports" / "comparison_report.md").read_text(
        encoding="utf-8"
    )
    assert "791" not in report
    assert "0.421" in report
