from pathlib import Path

root = Path(".")

packages = ["src", "src/core", "src/algorithms", "src/experiments",
            "src/gui", "src/gui/pages", "src/gui/widgets", "src/gui/workers"]

keep_dirs = ["data/mknap", "results/individual", "results/comparisons",
             "results/charts", "results/reports", "assets/icons", "assets/images"]

files = [
    "main.py",
    "src/core/model.py", "src/core/data_loader.py",
    "src/core/evaluator.py", "src/core/validator.py",
    "src/algorithms/greedy.py", "src/algorithms/dynamic_programming.py",
    "src/algorithms/genetic_algorithm.py", "src/algorithms/simulated_annealing.py",
    "src/experiments/experiment_runner.py", "src/experiments/comparison.py",
    "src/experiments/metrics.py",
    "src/gui/main_window.py", "src/gui/styles.py",
    "src/gui/pages/home_page.py", "src/gui/pages/dataset_page.py",
    "src/gui/pages/algorithm_page.py", "src/gui/pages/comparison_page.py",
    "src/gui/widgets/sidebar.py", "src/gui/widgets/control_panel.py",
    "src/gui/widgets/result_panel.py", "src/gui/widgets/analysis_panel.py",
    "src/gui/widgets/data_table.py", "src/gui/widgets/chart_widget.py",
    "src/gui/workers/algorithm_worker.py",
    "tests/test_data_loader.py", "tests/test_validator.py",
    "tests/test_greedy.py", "tests/test_dp.py", "tests/test_ga.py",
    "tests/test_sa.py", "tests/test_comparison.py",
]

for p in packages:
    (root / p).mkdir(parents=True, exist_ok=True)
    (root / p / "__init__.py").touch()
for d in keep_dirs:
    (root / d).mkdir(parents=True, exist_ok=True)
    (root / d / ".gitkeep").touch()
for f in files:
    (root / f).parent.mkdir(parents=True, exist_ok=True)
    (root / f).touch()

(root / "requirements.txt").write_text("PySide6\nmatplotlib\npytest\n")
(root / ".gitignore").write_text(
    "__pycache__/\n*.pyc\n.venv/\nvenv/\n.idea/\n.vscode/\n.DS_Store\n*.log\n")
(root / "README.md").write_text("# MKP-BIG4\n\nBai toan chon hang van chuyen (MKP) - so sanh 4 thuat toan: Greedy, DP, GA, SA.\n")