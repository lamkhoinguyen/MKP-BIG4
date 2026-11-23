import json
from datetime import datetime
from types import SimpleNamespace

import numpy as np

from src.gui import analytics, session_store


def make_problem():
    return SimpleNamespace(name="mknap1_01", n=6, m=10, z_ref=3800.0)


def make_records(history_length=10):
    history = [
        {"iteration": index, "profit": float(index)} for index in range(history_length)
    ]
    records = {}
    for index, name in enumerate(analytics.ALGORITHMS):
        records[name] = [
            {
                "seed": 0,
                "profit": np.float64(100.0 + index),
                "gap": np.float64(0.01),
                "runtime": 0.5,
                "feasible": True,
                "status": "ok",
                "selected_count": 4,
                "peak_memory": np.float64(0.0),
                "history": history,
                "error": None,
            }
        ]
    return records


def make_params():
    return {
        "time_limit": 60,
        "base_seed": 0,
        "num_seeds": 1,
        "seeds": [0],
    }


def make_session(history_length=10):
    return session_store.build_session(
        dataset_file="mknap1.txt",
        problem=make_problem(),
        params=make_params(),
        records=make_records(history_length),
        comments_list=["Nhận xét thử nghiệm."],
        created_at=datetime(2026, 11, 19, 10, 30, 0),
    )


def test_sanitize_and_unique_session_dir(tmp_path):
    assert session_store.sanitize_name("mknap 1/abc") == "mknap_1_abc"
    now = datetime(2026, 1, 2, 3, 4, 5)
    first = session_store.new_session_dir("mknap1_01", base_dir=tmp_path, now=now)
    second = session_store.new_session_dir("mknap1_01", base_dir=tmp_path, now=now)
    assert first.name == "20260102_030405_mknap1_01"
    assert second.name == "20260102_030405_mknap1_01_2"


def test_build_session_caps_history_and_converts_numpy():
    session = make_session(history_length=700)
    for algorithm in analytics.ALGORITHMS:
        runs = session["algorithms"][algorithm]["runs"]
        assert len(runs[0]["history"]) <= session_store.MAX_HISTORY_POINTS
        assert isinstance(runs[0]["profit"], float)
    json.dumps(session)


def test_save_and_load_session(tmp_path):
    session = make_session()
    folder = session_store.save_session(session, base_dir=tmp_path)
    files = {path.name for path in folder.iterdir()}
    assert {"session.json", "comparison.csv", "chart.png", "nhan_xet.txt"} <= files
    assert not list(folder.glob("*.tmp"))

    loaded = session_store.load_session(folder)
    assert loaded["version"] == 1
    assert loaded["problem"]["name"] == "mknap1_01"
    assert loaded["params"]["num_seeds"] == 1
    assert "greedy" in loaded["algorithms"]

    entries = session_store.list_sessions(tmp_path)
    assert len(entries) == 1
    assert entries[0]["problem"] == "mknap1_01"
    assert entries[0]["path"] == str(folder)

    rows = session_store.rows_from_session(loaded)
    assert [row["label"] for row in rows] == ["Greedy", "DP", "GA", "SA"]

    session_store.delete_session(folder)
    assert not folder.exists()
    assert session_store.list_sessions(tmp_path) == []


def test_exports(tmp_path):
    session = make_session()
    csv_path = session_store.export_csv(session, tmp_path / "out.csv")
    raw = csv_path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert "Thuật toán" in text
    assert "Greedy" in text

    json_path = session_store.export_json(session, tmp_path / "out.json")
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["problem"]["file"] == "mknap1.txt"

    png_path = session_store.export_png(session, tmp_path / "out.png")
    assert png_path.read_bytes().startswith(b"\x89PNG")

    html_path = session_store.export_html(session, tmp_path / "out.html")
    html_text = html_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html_text
    assert "data:image/png;base64," in html_text
    assert "Nhận xét thử nghiệm." in html_text


def test_save_session_with_partial_error_still_writes(tmp_path):
    session = make_session()
    session["algorithms"]["dynamic_programming"]["runs"] = [
        analytics.error_record("boom", seed=0)
    ]
    folder = session_store.save_session(session, base_dir=tmp_path)
    loaded = session_store.load_session(folder)
    runs = loaded["algorithms"]["dynamic_programming"]["runs"]
    assert runs[0]["status"] == "error"
    assert runs[0]["profit"] is None
