import math

from src.gui import analytics


def record(
    profit,
    gap=0.01,
    runtime=1.0,
    status="ok",
    feasible=True,
    seed=0,
    history=None,
):
    return {
        "seed": seed,
        "profit": profit,
        "gap": gap,
        "runtime": runtime,
        "feasible": feasible,
        "status": status,
        "selected_count": 3,
        "peak_memory": 0.0,
        "history": history or [],
        "error": None,
    }


def test_seeds_for_and_estimate():
    assert analytics.seeds_for(0, 3) == [0, 1, 2]
    assert analytics.seeds_for(5, 1) == [5]
    assert analytics.seeds_for(1, 0) == []
    assert analytics.estimate_seconds(60, 3) == 480
    assert analytics.estimate_seconds(60, 1) == 240


def test_build_plan_order_and_total():
    plan = analytics.build_plan(2, 3)
    assert len(plan) == 8
    assert plan[:2] == [("greedy", 2), ("dynamic_programming", 2)]
    assert plan[2:] == [
        ("genetic_algorithm", 2),
        ("genetic_algorithm", 3),
        ("genetic_algorithm", 4),
        ("simulated_annealing", 2),
        ("simulated_annealing", 3),
        ("simulated_annealing", 4),
    ]


def test_summarize_runs_population_std_and_status():
    runs = [
        record(100.0, gap=0.0, runtime=1.0),
        record(120.0, gap=-0.2, runtime=3.0, status="timeout", feasible=False),
        record(80.0, gap=0.2, runtime=2.0),
    ]
    stats = analytics.summarize_runs(runs)
    assert stats["best"] == 120.0
    assert stats["worst"] == 80.0
    assert stats["avg"] == 100.0
    assert stats["std"] == round(math.sqrt((0 + 400 + 400) / 3), 2)
    assert stats["feasible"] == "2/3"
    assert stats["status"] == "ok ×2, timeout ×1"
    assert stats["best_run"]["profit"] == 120.0
    assert stats["selected_count"] == 3


def test_error_runs_ignored_for_profit_but_counted_for_feasible():
    runs = [record(50.0), analytics.error_record("boom", seed=0)]
    stats = analytics.summarize_runs(runs)
    assert stats["best"] == 50.0
    assert stats["feasible"] == "1/2"
    assert "error" in stats["status"]


def test_build_rows_single_seed_hides_statistics():
    records = {
        "greedy": [record(100.0)],
        "dynamic_programming": [record(90.0)],
        "genetic_algorithm": [record(110.0)],
        "simulated_annealing": [record(95.0)],
    }
    rows = analytics.build_rows(records, 1)
    assert [row["label"] for row in rows] == ["Greedy", "DP", "GA", "SA"]
    for row in rows:
        assert row["avg"] is None
        assert row["worst"] is None
        assert row["std"] is None
        assert row["gap_avg"] is None


def test_build_rows_multi_seed_only_stochastic():
    records = {
        "greedy": [record(100.0)],
        "dynamic_programming": [record(90.0)],
        "genetic_algorithm": [record(100.0), record(120.0), record(110.0)],
        "simulated_annealing": [record(95.0), record(96.0), record(94.0)],
    }
    rows = analytics.build_rows(records, 3)
    by_name = {row["algorithm"]: row for row in rows}
    assert by_name["greedy"]["avg"] is None
    assert by_name["genetic_algorithm"]["avg"] == 110.0
    assert by_name["genetic_algorithm"]["worst"] == 100.0
    assert by_name["genetic_algorithm"]["std"] == round(
        math.sqrt(((100 - 110) ** 2 + (120 - 110) ** 2 + 0) / 3), 2
    )
    assert by_name["simulated_annealing"]["gap_avg"] is not None


def test_history_series_and_fallbacks():
    result = {
        "history": [
            {"iteration": 1, "profit": 5.0},
            {"iteration": 2, "profit": 7.0, "best_profit": 9.0},
        ]
    }
    assert analytics.history_series(result) == [(1.0, 5.0), (2.0, 9.0)]

    no_iteration = {"history": [{"profit": 4.0}, {"profit": 8.0}]}
    assert analytics.history_series(no_iteration) == [(0.0, 4.0), (1.0, 8.0)]


def test_progress_series_endpoints():
    result = {"history": [{"profit": 1.0}, {"profit": 2.0}, {"profit": 3.0}]}
    points = analytics.progress_series(result)
    assert points[0][0] == 0.0
    assert points[-1][0] == 100.0
    assert len(points) == 3
    assert analytics.progress_series({"history": [{"profit": 4.0}]}) == [(0.0, 4.0)]
    assert analytics.progress_series({"history": []}) == []


def test_comments_tie_and_context():
    records = {
        name: [record(100.0, gap=0.0, runtime=1.0)]
        for name in analytics.ALGORITHMS
    }
    rows = analytics.build_rows(records, 1)
    lines = analytics.comments(
        rows,
        {
            "time_limit": 60,
            "num_seeds": 1,
            "seeds": [0],
            "problem_name": "demo",
            "z_ref": 100.0,
        },
    )
    text = "\n".join(lines)
    assert "tương đương" in text
    assert "Z_ref" in text
    assert "Bối cảnh: demo" in text


def test_comments_all_time_limited():
    records = {
        name: [record(10.0, runtime=95.0)]
        for name in analytics.ALGORITHMS
    }
    rows = analytics.build_rows(records, 1)
    lines = analytics.comments(
        rows,
        {
            "time_limit": 100,
            "num_seeds": 1,
            "seeds": [0],
            "problem_name": "demo",
            "z_ref": 20.0,
        },
    )
    assert any("không thể so sánh tốc độ tuyệt đối" in line for line in lines)


def test_comments_oom_and_missing_z_ref():
    records = {
        "greedy": [record(10.0, gap=None)],
        "dynamic_programming": [
            record(None, gap=None, status="out_of_memory", feasible=False)
        ],
        "genetic_algorithm": [record(9.0, gap=None)],
        "simulated_annealing": [record(8.0, gap=None)],
    }
    rows = analytics.build_rows(records, 1)
    lines = analytics.comments(
        rows,
        {
            "time_limit": 10,
            "num_seeds": 1,
            "seeds": [0],
            "problem_name": "demo",
            "z_ref": None,
        },
    )
    text = "\n".join(lines)
    assert "out_of_memory" in text
    assert "không có Z_ref" in text


def test_comments_stability_tie():
    records = {
        "greedy": [record(10.0)],
        "dynamic_programming": [record(10.0)],
        "genetic_algorithm": [record(10.0), record(10.0), record(10.0)],
        "simulated_annealing": [record(10.0), record(10.0), record(10.0)],
    }
    rows = analytics.build_rows(records, 3)
    lines = analytics.comments(
        rows,
        {
            "time_limit": 100,
            "num_seeds": 3,
            "seeds": [0, 1, 2],
            "problem_name": "demo",
            "z_ref": 10.0,
        },
    )
    text = "\n".join(lines)
    assert "cùng std thấp nhất" in text

def test_fmt_duration():
    assert analytics.fmt_duration(45) == "45 giây"
    assert analytics.fmt_duration(60) == "1 phút"
    assert analytics.fmt_duration(200) == "3 phút 20 giây"
    assert analytics.fmt_duration(None) == "-"
