"""Lưu, đọc, xóa và xuất phiên so sánh của GUI.

Phiên GUI nằm riêng trong ``results/gui_sessions/`` để không lẫn với
session của ``src.experiments``.
"""

import base64
import csv
import html
import io
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from src.core.config import PROJECT_ROOT
from src.gui import analytics

SESSIONS_DIR = PROJECT_ROOT / "results" / "gui_sessions"
MAX_HISTORY_POINTS = 600
SAFE_NAME = re.compile(r"[^A-Za-z0-9_-]+")

CSV_HEADERS = (
    "Thuật toán",
    "Profit",
    "Avg",
    "Worst",
    "Std",
    "Gap best (%)",
    "Gap avg (%)",
    "Runtime (s)",
    "Feasible",
    "Status",
    "Chọn",
    "Bộ nhớ đỉnh (MB)",
)


def sanitize_name(name: str) -> str:
    cleaned = SAFE_NAME.sub("_", str(name or "session")).strip("_")
    return cleaned or "session"


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    return value


def _stats_for_store(stats: dict) -> dict:
    cleaned = dict(stats or {})
    cleaned.pop("best_run", None)
    return _jsonable(cleaned)


def cap_history(history, limit: int = MAX_HISTORY_POINTS) -> list:
    history = list(history or [])
    if len(history) <= limit:
        return history
    if limit <= 1:
        return history[-1:]
    step = (len(history) - 1) / (limit - 1)
    indexes = sorted({int(round(index * step)) for index in range(limit)})
    return [history[index] for index in indexes]


def build_session(
    *,
    dataset_file: str,
    problem,
    params: dict,
    records: dict,
    comments_list: list[str],
    created_at: datetime | None = None,
) -> dict:
    created = (created_at or datetime.now()).isoformat(timespec="seconds")
    algorithms = {}
    for algorithm in analytics.ALGORITHMS:
        runs = [dict(run) for run in records.get(algorithm, [])]
        for run in runs:
            run["history"] = cap_history(run.get("history"))
        stats = analytics.summarize_runs(runs)
        algorithms[algorithm] = {
            "runs": _jsonable(runs),
            "stats": _stats_for_store(stats),
        }
    return {
        "version": 1,
        "created_at": created,
        "problem": {
            "file": dataset_file or "",
            "name": getattr(problem, "name", "-"),
            "n": int(getattr(problem, "n", 0)),
            "m": int(getattr(problem, "m", 0)),
            "z_ref": None if getattr(problem, "z_ref", None) is None else float(problem.z_ref),
        },
        "params": {
            "time_limit": float(params.get("time_limit", 0.0)),
            "base_seed": int(params.get("base_seed", 0)),
            "num_seeds": int(params.get("num_seeds", 1)),
            "seeds": [int(seed) for seed in (params.get("seeds") or [])],
        },
        "algorithms": _jsonable(algorithms),
        "comments": [str(line) for line in comments_list],
    }


def records_from_session(session: dict) -> dict:
    records = {}
    for algorithm in analytics.ALGORITHMS:
        block = (session.get("algorithms") or {}).get(algorithm) or {}
        records[algorithm] = list(block.get("runs") or [])
    return records


def rows_from_session(session: dict) -> list[dict]:
    params = session.get("params") or {}
    return analytics.build_rows(
        records_from_session(session), int(params.get("num_seeds", 1))
    )


def new_session_dir(
    problem_name: str,
    base_dir: Path | None = None,
    now: datetime | None = None,
) -> Path:
    base = Path(base_dir) if base_dir is not None else SESSIONS_DIR
    base.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    stem = f"{stamp}_{sanitize_name(problem_name)}"
    candidate = base / stem
    index = 2
    while candidate.exists():
        candidate = base / f"{stem}_{index}"
        index += 1
    candidate.mkdir(parents=True)
    return candidate


def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding=encoding)
    os.replace(temporary, path)


def save_session(
    session: dict,
    base_dir: Path | None = None,
    session_dir: Path | None = None,
    write_chart: bool = True,
) -> Path:
    """Ghi session.json, comparison.csv, nhan_xet.txt và chart.png."""
    if session_dir is None:
        problem_name = (session.get("problem") or {}).get("name", "session")
        session_dir = new_session_dir(problem_name, base_dir=base_dir)
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    _atomic_write_text(
        session_dir / "session.json",
        json.dumps(_jsonable(session), ensure_ascii=False, indent=2),
    )
    export_csv(session, session_dir / "comparison.csv")

    comments_list = session.get("comments") or []
    _atomic_write_text(
        session_dir / "nhan_xet.txt",
        "\n".join(str(line) for line in comments_list) + ("\n" if comments_list else ""),
    )
    if write_chart:
        try:
            export_png(session, session_dir / "chart.png")
        except Exception:  # pragma: no cover - hiếm khi matplotlib lỗi
            _write_placeholder_png(session_dir / "chart.png")
    return session_dir


def _write_placeholder_png(path: Path) -> None:
    figure = Figure(figsize=(6, 3))
    axis = figure.add_subplot(111)
    axis.axis("off")
    axis.text(0.5, 0.5, "Không tạo được biểu đồ", ha="center", va="center")
    figure.savefig(path, dpi=80)


def load_session(path) -> dict:
    path = Path(path)
    if path.is_dir():
        path = path / "session.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions(base_dir: Path | None = None) -> list[dict]:
    base = Path(base_dir) if base_dir is not None else SESSIONS_DIR
    if not base.exists():
        return []
    sessions = []
    for session_file in base.glob("*/session.json"):
        try:
            session = load_session(session_file)
        except (OSError, json.JSONDecodeError):
            continue
        problem = session.get("problem") or {}
        params = session.get("params") or {}
        sessions.append(
            {
                "path": str(session_file.parent),
                "session_file": str(session_file),
                "created_at": session.get("created_at", ""),
                "problem": problem.get("name", "-"),
                "dataset": problem.get("file", ""),
                "time_limit": params.get("time_limit", 0),
                "num_seeds": params.get("num_seeds", 1),
            }
        )
    sessions.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return sessions


def delete_session(path) -> None:
    folder = Path(path)
    if folder.is_dir():
        shutil.rmtree(folder)
    elif folder.exists():
        folder.unlink()


def open_folder(path) -> None:
    folder = Path(path)
    if not folder.exists():
        raise FileNotFoundError(folder)
    os.startfile(str(folder))  # type: ignore[attr-defined]


def _csv_value(value, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def export_csv(session: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = rows_from_session(session)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADERS)
        for row in rows:
            writer.writerow(
                [
                    row["label"],
                    _csv_value(row["profit"], 0),
                    _csv_value(row["avg"], 0),
                    _csv_value(row["worst"], 0),
                    _csv_value(row["std"], 2),
                    _csv_value(None if row["gap_best"] is None else row["gap_best"] * 100, 2),
                    _csv_value(None if row["gap_avg"] is None else row["gap_avg"] * 100, 2),
                    _csv_value(row["runtime"], 3),
                    row["feasible"],
                    row["status"],
                    "-" if row["selected_count"] is None else row["selected_count"],
                    _csv_value(row["peak_memory"], 2),
                ]
            )
    return path


def export_json(session: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        path, json.dumps(_jsonable(session), ensure_ascii=False, indent=2)
    )
    return path


def _session_param_rows(session: dict) -> list[tuple[str, str]]:
    problem = session.get("problem") or {}
    params = session.get("params") or {}
    seeds = ", ".join(str(seed) for seed in (params.get("seeds") or []))
    return [
        ("Dataset", problem.get("file", "-")),
        ("Bài toán", problem.get("name", "-")),
        ("Kích thước", f"n={problem.get('n', '-')}, m={problem.get('m', '-')}"),
        ("Z_ref", "-" if problem.get("z_ref") is None else str(problem.get("z_ref"))),
        ("Time limit", f"{params.get('time_limit', '-')} giây"),
        ("Seed cơ sở", str(params.get("base_seed", "-"))),
        ("Số seed", str(params.get("num_seeds", "-"))),
        ("Danh sách seed", seeds or "-"),
        ("Thời điểm chạy", session.get("created_at", "-")),
    ]


def _display(value, digits: int = 2) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def render_html(session: dict, png_bytes: bytes | None = None) -> str:
    rows = rows_from_session(session)
    param_rows = _session_param_rows(session)
    comments_list = session.get("comments") or []

    param_html = "".join(
        f"<tr><th>{html.escape(name)}</th><td>{html.escape(str(value))}</td></tr>"
        for name, value in param_rows
    )

    header_html = "".join(f"<th>{html.escape(name)}</th>" for name in CSV_HEADERS)
    body_html = []
    for row in rows:
        cells = [
            row["label"],
            _display(row["profit"], 0),
            _display(row["avg"], 0),
            _display(row["worst"], 0),
            _display(row["std"], 2),
            _display(None if row["gap_best"] is None else row["gap_best"] * 100, 2),
            _display(None if row["gap_avg"] is None else row["gap_avg"] * 100, 2),
            _display(row["runtime"], 3),
            row["feasible"],
            row["status"],
            "-" if row["selected_count"] is None else row["selected_count"],
            _display(row["peak_memory"], 2),
        ]
        body_html.append(
            "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>"
        )

    comments_html = "".join(
        f"<li>{html.escape(str(line))}</li>" for line in comments_list
    )

    image_html = ""
    if png_bytes:
        encoded = base64.b64encode(png_bytes).decode("ascii")
        image_html = (
            f'<img alt="Biểu đồ phiên" src="data:image/png;base64,{encoded}" '
            'style="max-width:100%;height:auto;border:1px solid #e2e8f0;border-radius:8px;" />'
        )

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8" />
<title>Báo cáo MKP — {html.escape(str((session.get("problem") or {}).get("name", "-")))}</title>
<style>
body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
h1, h2 {{ color: #0f172a; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; background: #ffffff; }}
th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; font-size: 13px; }}
th {{ background: #e2e8f0; }}
ul {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 28px; }}
</style>
</head>
<body>
<h1>Báo cáo so sánh 4 thuật toán MKP</h1>
<h2>Tham số phiên</h2>
<table>{param_html}</table>
<h2>Nhận xét tự động</h2>
<ul>{comments_html}</ul>
<h2>Bảng kết quả</h2>
<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body_html)}</tbody></table>
<h2>Biểu đồ tổng hợp</h2>
{image_html}
</body>
</html>
"""


def render_png_bytes(session: dict) -> bytes:
    figure = composite_figure(session)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    return buffer.getvalue()


def export_png(session: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = composite_figure(session)
    figure.savefig(path, format="png", dpi=120, bbox_inches="tight")
    return path


def export_html(session: dict, path, png_bytes: bytes | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if png_bytes is None:
        try:
            png_bytes = render_png_bytes(session)
        except Exception:  # pragma: no cover
            png_bytes = None
    _atomic_write_text(path, render_html(session, png_bytes))
    return path


def export_pdf(html_text: str, path) -> Path:
    """Xuất PDF tùy chọn bằng QtPrintSupport (không thêm dependency)."""
    from PySide6.QtCore import QMarginsF
    from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
    from PySide6.QtPrintSupport import QPrinter

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(path))
    printer.setPageLayout(
        QPageLayout(
            QPageSize(QPageSize.A4),
            QPageLayout.Portrait,
            QMarginsF(12, 12, 12, 12),
        )
    )
    document = QTextDocument()
    document.setHtml(html_text)
    document.print_(printer)
    return path


def composite_figure(session: dict) -> Figure:
    rows = rows_from_session(session)
    figure = Figure(figsize=(12, 8))
    axes = figure.subplots(2, 2)

    _bar_axis(
        axes[0][0],
        rows,
        "profit",
        "Profit",
        "Profit",
        value_digits=0,
    )
    _bar_axis(
        axes[0][1],
        rows,
        "gap_best",
        "Gap best (%)",
        "Gap (%)",
        scale=100.0,
        value_digits=2,
    )
    _bar_axis(
        axes[1][0],
        rows,
        "runtime",
        "Runtime",
        "Giây",
        value_digits=3,
    )
    _convergence_axis(axes[1][1], rows)
    figure.tight_layout()
    return figure


def _bar_axis(axis, rows, key, title, ylabel, scale=1.0, value_digits=2):
    labels = [row["label"] for row in rows]
    values = []
    errors = []
    has_error = False
    for row in rows:
        value = row.get(key)
        if key == "gap_best" and row.get("gap_avg") is not None and row.get("stochastic"):
            value = row.get("gap_avg")
        if value is None:
            values.append(0.0)
        else:
            values.append(float(value) * scale)
        std = row.get("std")
        if row.get("stochastic") and std is not None:
            has_error = True
            errors.append(float(std) if key == "profit" else 0.0)
        else:
            errors.append(0.0)
    positions = list(range(len(labels)))
    bars = axis.bar(
        positions,
        values,
        color=["#2563eb", "#0f766e", "#c2410c", "#7c3aed"][: len(labels)],
        yerr=errors if has_error else None,
        capsize=4,
    )
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.set_xticks(positions)
    axis.set_xticklabels(labels)
    axis.grid(axis="y", alpha=0.25)
    top = max(values) if values else 0
    for bar, value in zip(bars, values):
        axis.annotate(
            f"{value:.{value_digits}f}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            fontsize=8,
        )
    if top <= 0:
        axis.set_ylim(0, 1)


def _convergence_axis(axis, rows):
    drew = False
    for row in rows:
        runs = row.get("runs") or []
        if not runs:
            continue
        profits = [
            float(run["profit"]) for run in runs if run.get("profit") is not None
        ]
        best_profit = max(profits) if profits else None
        for run in runs:
            series = analytics.progress_series(run.get("history") or [])
            if not series:
                continue
            xs = [point[0] for point in series]
            ys = [point[1] for point in series]
            is_best = (
                best_profit is not None
                and run.get("profit") is not None
                and abs(float(run["profit"]) - best_profit) < 1e-6
            )
            axis.plot(
                xs,
                ys,
                label=row["label"],
                alpha=0.95 if is_best or len(runs) == 1 else 0.35,
                linewidth=2.0 if is_best or len(runs) == 1 else 1.0,
            )
            drew = True
    axis.set_title("Hội tụ (% tiến trình)")
    axis.set_xlabel("% tiến trình ghi nhận")
    axis.set_ylabel("Profit tốt nhất")
    axis.grid(alpha=0.25)
    if drew:
        axis.legend(fontsize=8)
    else:
        axis.text(0.5, 0.5, "Không có history", ha="center", va="center")
        axis.set_xticks([])
        axis.set_yticks([])
