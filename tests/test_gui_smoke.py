import os
import time
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from src.core.data_loader import get_problem
from src.gui import analytics
from src.gui.main_window import MainWindow
from src.gui.styles import load_stylesheet
from src.gui.workers.algorithm_worker import SessionWorker


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    yield instance


@pytest.fixture
def window(app):
    widget = MainWindow()
    widget.show()
    widget.activateWindow()
    app.processEvents()
    yield widget
    widget.close()
    app.processEvents()


def test_window_has_four_pages(window):
    assert window.stack.count() == 4
    assert window.minimumWidth() == 1100
    assert window.minimumHeight() == 700
    assert window.sidebar.width() == 180
    assert window.sidebar.testAttribute(Qt.WA_StyledBackground)
    assert window.analysis.testAttribute(Qt.WA_StyledBackground)
    assert window.sidebar.buttons[0].toolTip() == "Ctrl+1"
    assert window.sidebar.buttons[3].toolTip() == "Ctrl+4"
    titles = [page.PAGE_TITLE for page in window.pages]
    assert titles == ["Trang chủ", "Dataset", "Algorithm", "Comparison"]


def test_sidebar_navigation(window, app):
    window.sidebar.buttons[2].click()
    app.processEvents()
    assert window.stack.currentIndex() == 2
    assert window.analysis.title_label.text() == "Algorithm"


def test_number_shortcuts_switch_pages(window, app):
    QTest.keyClick(window, Qt.Key_4, Qt.ControlModifier)
    app.processEvents()
    assert window.stack.currentIndex() == 3

    QTest.keyClick(window, Qt.Key_1, Qt.ControlModifier)
    app.processEvents()
    assert window.stack.currentIndex() == 0


def test_analysis_updates_when_page_changes(window):
    window.set_page(1)
    assert window.analysis.title_label.text() == "Dataset"
    assert "dữ liệu" in window.analysis.body.toPlainText().lower()


def test_stylesheet_is_loaded():
    assert "QMainWindow" in load_stylesheet()

def test_home_quick_navigation(window, app):
    home = window.pages[0]
    buttons = home.findChildren(QPushButton)
    assert len(buttons) >= 3
    buttons[0].click()
    app.processEvents()
    assert window.stack.currentIndex() == 1


def test_dataset_page_models_and_commit(window, app):
    page = window.pages[1]
    assert page.tabs.count() == 4
    assert not page.tabs.isTabVisible(3)
    problem = get_problem("mknap1.txt", 1)
    assert page.profits_model.rowCount() == problem.n
    assert page.weights_model.rowCount() == problem.m
    assert page.weights_model.columnCount() == problem.n
    assert page.capacities_model.rowCount() == problem.m

    page._commit()
    app.processEvents()
    assert window.state.problem.name == problem.name
    assert window.state.problem.n == problem.n
    assert window.stack.currentIndex() == 2


def test_dataset_all_problems_commit(window, app):
    page = window.pages[1]
    assert page.problem_list.item(0).text().startswith("(tất cả")
    page.problem_list.setCurrentRow(0)
    page._on_problem_changed(0)
    assert page._all_selected
    expected = len(page._problems)
    assert page.tabs.isTabVisible(3)
    assert page.tabs.currentIndex() == 3
    assert page.summary_model.rowCount() == expected
    assert page.summary_model.index(0, 0).data() == page._problems[0].name
    assert page.profits_model.rowCount() == 0
    assert page.info_values["name"].text().startswith("Tất cả")
    assert page.info_values["n"].text() and page.info_values["n"].text() != "-"

    page._commit()
    app.processEvents()
    assert window.state.is_batch
    assert len(window.state.problems) == expected
    assert "bài" in window.state.problem_text()

    window.state.commit_problem("mknap1.txt", get_problem("mknap1.txt", 1))
    assert not window.state.is_batch
    assert window.state.problems == []

    page.problem_list.setCurrentRow(1)
    page._on_problem_changed(1)
    assert not page.tabs.isTabVisible(3)
    assert page.summary_model.rowCount() == 0
    assert page.info_values["name"].text() == get_problem("mknap1.txt", 1).name


def test_algorithm_batch_rows_prefix_problem_name(window):
    page = window.pages[2]
    first = SimpleNamespace(name="mknapcb2_1")
    second = SimpleNamespace(name="mknapcb2_2")
    page._batch_problems = [first, second]
    page._batch_records = {
        first.name: {name: [] for name in analytics.ALGORITHMS},
        second.name: {name: [] for name in analytics.ALGORITHMS},
    }
    rows = page._batch_rows()
    assert len(rows) == 8
    assert rows[0]["label"].startswith("mknapcb2_1 · ")
    assert rows[4]["label"].startswith("mknapcb2_2 · ")


def test_problem_labels_show_batch_selection(window, app):
    problems = [get_problem("mknap1.txt", 1), get_problem("mknap1.txt", 2)]
    window.state.commit_problems("mknap1.txt", problems)
    app.processEvents()
    assert "tất cả" in window.pages[2].problem_label.text()
    assert "tất cả" in window.pages[3].problem_label.text()


def test_comparison_batch_rows_prefix_problem_name(window):
    page = window.pages[3]
    first = SimpleNamespace(name="mknapcb2_1")
    second = SimpleNamespace(name="mknapcb2_2")
    page._num_seeds = 1
    page._batch_problems = [first, second]
    page._batch_records = {
        first.name: {name: [] for name in analytics.ALGORITHMS},
        second.name: {name: [] for name in analytics.ALGORITHMS},
    }
    rows = page._batch_rows()
    assert len(rows) == 8
    assert rows[0]["label"].startswith("mknapcb2_1 · ")
    assert rows[4]["label"].startswith("mknapcb2_2 · ")


def test_algorithm_page_runs_greedy_in_thread(window, app):
    window.state.commit_problem("mknap1.txt", get_problem("mknap1.txt", 1))
    window.set_page(2)
    page = window.pages[2]
    page.time_spin.setValue(0.5)
    page.algo_combo.setCurrentIndex(0)
    page.run_single()

    deadline = time.time() + 20
    while time.time() < deadline:
        app.processEvents()
        if not page.state.running and page._thread is None:
            break
        time.sleep(0.01)

    assert page.state.running is False
    assert window.state.last_result is not None
    assert window.state.last_result.status == "ok"
    assert page.details.values["profit"][1].text() != "-"
    assert page.chart_single.has_history
    assert page.replay_button.isEnabled()


def test_comparison_seed_label(window):
    page = window.pages[3]
    page.seed_spin.setValue(2)
    page.seeds_combo.setCurrentIndex(1)
    assert "2, 3, 4" in page.seeds_label.text()
    assert "8 lượt" in page.estimate_label.text()


def test_analysis_history_visible_on_comparison(window, app):
    window.set_page(3)
    app.processEvents()
    assert window.analysis.history_box.isVisibleTo(window)


def test_session_worker_single_turn(app):
    worker = SessionWorker(
        [("greedy", 0)],
        get_problem("mknap1.txt", 1),
        0.5,
    )
    outcomes = []
    done = []
    worker.run_done.connect(lambda algorithm, seed, record: done.append(record))
    worker.finished.connect(lambda result: outcomes.extend(result))
    worker.run()
    assert len(done) == 1
    assert done[0]["status"] == "ok"
    assert done[0]["profit"] == 3800.0
    assert len(outcomes) == 1
    assert outcomes[0]["algorithm"] == "greedy"


def _fake_records(seed: int = 7) -> dict:
    values = {
        "greedy": 3800.0,
        "dynamic_programming": 3800.0,
        "genetic_algorithm": 3810.0,
        "simulated_annealing": 3790.0,
    }
    records = {}
    for algorithm in analytics.ALGORITHMS:
        result = SimpleNamespace(
            total_profit=values[algorithm],
            optimality_gap=0.0,
            runtime=0.2,
            feasible=True,
            status="ok",
            selected_items=[1, 2, 3],
            peak_memory=1.5,
            history=[{"iteration": 0, "best_profit": values[algorithm]}],
        )
        records[algorithm] = [analytics.run_record(result, seed)]
    return records


def test_algorithm_publishes_run_all_snapshot(window, app):
    problem = get_problem("mknap1.txt", 1)
    window.state.commit_problem("mknap1.txt", problem)
    page = window.pages[2]
    page._run_problem = problem
    page._records = _fake_records()
    page._run_mode = "all"
    page.time_spin.setValue(2.0)
    page.seed_spin.setValue(11)

    page._publish_run_all()
    app.processEvents()

    snapshot = window.state.run_all_results
    assert snapshot is not None
    assert snapshot["batch"] is False
    assert snapshot["dataset_file"] == "mknap1.txt"
    assert snapshot["problem"] is problem
    assert snapshot["time_limit"] == 2.0
    assert snapshot["seed"] == 11
    assert set(snapshot["records"]) == set(analytics.ALGORITHMS)


def test_comparison_reuses_run_all_results(window, app, monkeypatch, tmp_path):
    import src.gui.pages.comparison_page as comparison_page

    problem = get_problem("mknap1.txt", 1)
    window.state.commit_problem("mknap1.txt", problem)
    window.state.set_run_all_results(
        {
            "batch": False,
            "dataset_file": "mknap1.txt",
            "problem": problem,
            "problems": [],
            "records": _fake_records(seed=5),
            "batch_records": {},
            "time_limit": 1.5,
            "seed": 5,
        }
    )
    app.processEvents()

    page = window.pages[3]
    assert page.reuse_button.isEnabled()

    saved = []
    monkeypatch.setattr(
        comparison_page.session_store,
        "save_session",
        lambda session, *args, **kwargs: saved.append(session) or (tmp_path / "s1"),
    )

    page.load_run_all_results()
    app.processEvents()

    assert len(saved) == 1
    assert page._current_session is not None
    assert len(page._current_rows) == 4
    assert page.result_table.model.rowCount() == 4
    assert page.time_spin.value() == 1.5
    assert page.seed_spin.value() == 5
    assert page._num_seeds == 1
    assert page.banner.isVisibleTo(page)
    assert window.state.last_session is page._current_session


def test_comparison_reuse_disabled_for_other_problem(window, app):
    first = get_problem("mknap1.txt", 1)
    second = get_problem("mknap1.txt", 2)
    window.state.commit_problem("mknap1.txt", first)
    window.state.set_run_all_results(
        {
            "batch": False,
            "dataset_file": "mknap1.txt",
            "problem": first,
            "problems": [],
            "records": _fake_records(),
            "batch_records": {},
            "time_limit": 1.0,
            "seed": 0,
        }
    )
    app.processEvents()
    assert window.pages[3].reuse_button.isEnabled()

    window.state.commit_problem("mknap1.txt", second)
    app.processEvents()
    assert not window.pages[3].reuse_button.isEnabled()


def test_comparison_reuses_run_all_batch(window, app, monkeypatch, tmp_path):
    import src.gui.pages.comparison_page as comparison_page

    problems = [get_problem("mknap1.txt", 1), get_problem("mknap1.txt", 2)]
    window.state.commit_problems("mknap1.txt", problems)
    window.state.set_run_all_results(
        {
            "batch": True,
            "dataset_file": "mknap1.txt",
            "problem": None,
            "problems": problems,
            "records": {},
            "batch_records": {
                problem.name: _fake_records(seed=3) for problem in problems
            },
            "time_limit": 1.0,
            "seed": 3,
        }
    )
    app.processEvents()

    page = window.pages[3]
    assert page.reuse_button.isEnabled()

    saved = []
    monkeypatch.setattr(
        comparison_page.session_store,
        "save_session",
        lambda session, *args, **kwargs: saved.append(session) or (tmp_path / "s"),
    )

    page.load_run_all_results()
    app.processEvents()

    assert len(saved) == 2
    assert len(page._current_rows) == 8
    assert page.result_table.model.rowCount() == 8
    assert page._current_rows[0]["label"].startswith(f"{problems[0].name} · ")
    assert page.banner.isVisibleTo(page)


def _batch_rows_for(problems) -> list[dict]:
    rows = []
    for problem in problems:
        for row in analytics.build_rows(_fake_records(), 1):
            rows.append(
                {
                    **row,
                    "problem": problem.name,
                    "label": f"{problem.name} · {row['label']}",
                }
            )
    return rows


def test_chart_groups_rows_by_problem(window):
    from src.gui.widgets import chart_widget

    problems = [get_problem("mknap1.txt", index) for index in (1, 2)]
    rows = _batch_rows_for(problems)
    groups = chart_widget._group_by_problem(rows)
    assert groups is not None
    assert [problem for problem, _ in groups] == [p.name for p in problems]

    single = analytics.build_rows(_fake_records(), 1)
    assert chart_widget._group_by_problem(single) is None


def test_chart_batch_convergence_uses_grid(window, app):
    from src.gui.widgets.chart_widget import ChartWidget

    problems = [get_problem("mknap1.txt", index) for index in range(1, 8)]
    rows = _batch_rows_for(problems)

    chart = ChartWidget(window)
    chart.plot_bars(rows, "profit", "Profit theo thuật toán")
    app.processEvents()
    assert len(chart.figure.axes) == 1
    assert chart.figure.axes[0].get_legend() is not None

    chart.plot_convergence(rows)
    app.processEvents()
    assert len(chart.figure.axes) == 8
    assert chart.figure.legends


def test_chart_single_problem_convergence_single_axis(window, app):
    from src.gui.widgets.chart_widget import ChartWidget

    chart = ChartWidget(window)
    chart.plot_convergence(analytics.build_rows(_fake_records(), 1))
    app.processEvents()
    assert len(chart.figure.axes) == 1
