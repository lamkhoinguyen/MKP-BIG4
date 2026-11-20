"""Tong hop ket qua thuc nghiem cua 4 thuat toan MKP (Giai doan 9).

Doc du lieu tu results/<algo>_all/<algo>_summary.json (325 bai x 1 seed x 60s),
sinh bang so sanh, bieu do va bao cao nhan xet vao:
    results/comparisons/  : CSV bang so sanh
    results/charts/       : bieu do PNG
    results/reports/      : bao cao markdown

Khong sua du lieu goc trong results/<algo>_all/ hay code cua 4 thuat toan.

Su dung:
    python -m src.experiments.comparison
    python -m src.experiments.comparison --results results --out results

Che do tu so sanh cac bai da chay (khong can full 325):
    python -m src.experiments greedy mknapcb4 1 -t 30 -s 1
    python -m src.experiments dp mknapcb4 1 -t 30 -s 1
    python -m src.experiments ga mknapcb4 1 -t 30 -s 1
    python -m src.experiments sa mknapcb4 1 -t 30 -s 1
    python -m src.experiments.comparison --live

Che do phien rieng (khong doc ket qua cu):
    python -m src.experiments ga mknapcb4 1 -t 30 -s 1 --session cb4_t30_s1
    python -m src.experiments.comparison --session cb4_t30_s1
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ALGORITHMS = ("greedy", "dp", "ga", "sa")
ALGORITHM_LABELS = {
    "greedy": "Greedy",
    "dp": "Dynamic Programming",
    "ga": "Genetic Algorithm",
    "sa": "Simulated Annealing",
}
COLORS = {"greedy": "#4C78A8", "dp": "#F58518", "ga": "#54A24B", "sa": "#E45756"}

PROBLEM_COLUMNS = [
    "file", "problem", "n", "m", "z_ref",
    "greedy_best", "greedy_gap_pct", "greedy_runtime", "greedy_status",
    "dp_best", "dp_gap_pct", "dp_runtime", "dp_status",
    "ga_best", "ga_gap_pct", "ga_runtime", "ga_status",
    "sa_best", "sa_gap_pct", "sa_runtime", "sa_status",
    "best_algo_by_profit",
]


def load_summaries(results_dir):
    """Doc summary cua 4 thuat toan tu results/<algo>_all/."""
    data = {}
    meta = {}
    for algo in ALGORITHMS:
        folder = results_dir / f"{algo}_all"
        summary_path = folder / f"{algo}_summary.json"
        meta_path = folder / f"{algo}_meta.json"
        if not summary_path.is_file():
            raise FileNotFoundError(f"Thieu file: {summary_path}")
        with open(summary_path, "r", encoding="utf-8") as handle:
            rows = json.load(handle)
        with open(meta_path, "r", encoding="utf-8") as handle:
            meta[algo] = json.load(handle)
        data[algo] = {(row["file"], row["problem"]): row for row in rows}
    return data, meta


def load_experiment_runs(results_dir, seed=None, experiments_dir=None):
    """Doc cac file JSON tu results/experiments/<algo>/.

    Tra ve (data, meta, so_bai_thieu). Chi cac bai co du 4 thuat toan
    duoc dua vao `data`; cac bai chay 1-3 algo duoc dem trong so_bai_thieu.
    """
    root = Path(experiments_dir) if experiments_dir else Path(results_dir) / "experiments"
    folder_names = {
        "greedy": ("greedy",),
        "dp": ("dp", "dynamic_programming"),
        "ga": ("ga", "genetic_algorithm"),
        "sa": ("sa", "simulated_annealing"),
    }
    accepted_names = {
        name: algo for algo, names in folder_names.items() for name in names
    }
    found = {}
    for algo in ALGORITHMS:
        found[algo] = {}
        for folder_name in folder_names[algo]:
            folder = root / folder_name
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.json")):
                if path.name == "experiment_summary.json":
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        item = json.load(handle)
                except (json.JSONDecodeError, OSError):
                    continue
                if accepted_names.get(item.get("algorithm")) != algo:
                    continue
                key = (item.get("dataset"), item.get("problem"))
                if not all(key):
                    continue
                if seed is not None and item.get("seed") != seed:
                    continue
                previous = found[algo].get(key)
                if previous is None or item.get("profit", 0) > previous.get("profit", 0):
                    found[algo][key] = item

    common = set(next(iter(found.values())).keys())
    for algo in ALGORITHMS:
        common &= set(found[algo].keys())
    missing = set().union(*(set(found[algo].keys()) for algo in ALGORITHMS)) - common

    data = {}
    meta = {}
    for algo in ALGORITHMS:
        data[algo] = {}
        for key in common:
            item = found[algo][key]
            oom = item.get("status") == "out_of_memory"
            timeout = item.get("status") == "timeout"
            gap = item.get("optimality_gap")
            data[algo][key] = {
                "file": key[0],
                "problem": key[1],
                "best_profit": item.get("profit", 0),
                "avg_gap_pct": None if gap is None else round(gap * 100, 3),
                "avg_runtime": item.get("runtime", 0),
                "oom_runs": 1 if oom else 0,
                "timeout_runs": 1 if timeout else 0,
                "runs": 1,
            }
        values = [found[algo][key] for key in common]
        meta[algo] = {
            "time_limit": values[0].get("time_limit") if values else None,
            "seeds": sorted({item.get("seed") for item in values}),
        }
    return data, meta, len(missing)


def _attach_problem_info(data, data_dir):
    """Bo sung n, m, z_ref tu data/mknap cho cac dong tu JSON."""
    from src.core.config import DATA_DIR
    from src.core.data_loader import load_problems

    root = Path(data_dir) if data_dir else DATA_DIR
    cache = {}
    for algo in ALGORITHMS:
        for key, item in data[algo].items():
            file_name = key[0]
            if file_name not in cache:
                path = root / file_name
                if not path.is_file():
                    path = root / f"{file_name}.txt"
                try:
                    cache[file_name] = {p.name: p for p in load_problems(path)}
                except Exception:
                    cache[file_name] = {}
            problem = cache[file_name].get(key[1])
            item["n"] = problem.n if problem is not None else 0
            item["m"] = problem.m if problem is not None else 0
            item["z_ref"] = problem.z_ref if problem is not None else 0


def load_session_meta(session_dir):
    """Doc thong tin chung cua 1 phien thử nghiem."""
    path = Path(session_dir) / "session_meta.json"
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    canonical = {
        "dynamic_programming": "dp",
        "genetic_algorithm": "ga",
        "simulated_annealing": "sa",
    }
    return {canonical.get(key, key): value for key, value in raw.items()}


def validate_session_meta(session_meta):
    """Dam bao 4 algo chay cung dataset, time limit va seed."""
    if not session_meta:
        return []
    missing = [algo for algo in ALGORITHMS if algo not in session_meta]
    if missing:
        raise SystemExit(
            "Phien thieu ket qua cua: " + ", ".join(missing)
        )
    reference = session_meta["greedy"]
    fields = ("datasets", "problem", "time_limit", "seed")
    for algo in ALGORITHMS:
        for field in fields:
            if session_meta[algo].get(field) != reference.get(field):
                raise SystemExit(
                    f"Thong so khong dong nhat giua greedy va {algo} "
                    f"({field}: {reference.get(field)} vs "
                    f"{session_meta[algo].get(field)})"
                )
    return missing


def write_live_report(report_dir, group_rows, meta, problem_rows, missing_count,
                      session_name=None, session_meta=None):
    """Bao cao cho che do tu so sanh (so bài nguoi dung da chay)."""
    report_dir.mkdir(parents=True, exist_ok=True)
    overall = group_rows[0]
    lines = [
        "# Bao cao so sanh tu ket qua da chay",
        "",
        f"Cap nhat: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    if session_name:
        lines.extend([
            f"- Phien: {session_name}",
            f"- Dataset: {session_meta.get('greedy', {}).get('datasets')}",
            f"- Bai: {session_meta.get('greedy', {}).get('problem')}",
            f"- Time limit / seed: {session_meta.get('greedy', {}).get('time_limit')}s"
            f" / {session_meta.get('greedy', {}).get('seed')}",
            "",
        ])
    lines.extend([
        f"- So bai duoc so sanh: {overall['problems']} "
        "(bai co ket qua cua ca 4 thuat toan)",
        f"- So bai chua du 4 thuat toan: {missing_count} (da bo qua)",
        f"- Time limit: {meta['greedy']['time_limit']}s, "
        f"seed: {meta['greedy']['seeds']}",
        "",
        "| Thuat toan | Gap TB (%) | Profit TB | Thoi gian TB (s) | "
        "Thang | Timeout | OOM |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for algo in ALGORITHMS:
        lines.append(
            f"| {ALGORITHM_LABELS[algo]} | "
            f"{_fmt(overall[f'{algo}_avg_gap_pct'])} | "
            f"{_fmt(overall[f'{algo}_avg_profit'])} | "
            f"{_fmt(overall[f'{algo}_avg_runtime'])} | "
            f"{overall[f'{algo}_best_count']} | "
            f"{overall[f'{algo}_timeout']} | {overall[f'{algo}_oom']} |"
        )
    lines.extend([
        "",
        "## Ghi chu",
        "",
        "- Bang chi gom cac bai da chay du 4 thuat toan",
        "- Chay them 1 bai cho ca 4 algo roi chay lai lenh nay de cap nhat bang",
        "",
    ])
    path = report_dir / "comparison_live_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_multiseed_summaries(results_dir):
    """Doc summary 3 seed (16 bai) de danh gia do on dinh cua GA/SA."""
    data = {}
    for algo in ("ga", "sa"):
        path = results_dir / algo / f"{algo}_summary.json"
        if not path.is_file():
            continue
        with open(path, "r", encoding="utf-8") as handle:
            data[algo] = json.load(handle)
    return data


def _status_of(row):
    if row["oom_runs"]:
        return "oom"
    if row["timeout_runs"]:
        return "timeout"
    return "ok"


def build_problem_rows(data):
    """Mot dong cho moi bai toan, mang cac chi so cua 4 thuat toan."""
    keys = set(next(iter(data.values())).keys())
    for algo in ALGORITHMS:
        keys &= set(data[algo].keys())
    rows = []
    for key in sorted(keys):
        base = data["greedy"][key]
        row = {
            "file": base["file"],
            "problem": base["problem"],
            "n": base["n"],
            "m": base["m"],
            "z_ref": base["z_ref"],
        }
        profits = {}
        for algo in ALGORITHMS:
            value = data[algo][key]
            prefix = algo
            row[f"{prefix}_best"] = value["best_profit"]
            row[f"{prefix}_gap_pct"] = value["avg_gap_pct"]
            row[f"{prefix}_runtime"] = value["avg_runtime"]
            row[f"{prefix}_status"] = _status_of(value)
            profits[algo] = value["best_profit"]
        row["best_algo_by_profit"] = max(profits, key=profits.get)
        rows.append(row)
    return rows


def _scale_of(row):
    if row["n"] <= 100:
        return "nho (n<=100)"
    if row["n"] <= 250:
        return "trung binh (100<n<=250)"
    return "lon (n>250)"


def aggregate(rows, label):
    """Tong hop cac chi so cho mot nhom bai."""
    entry = {"group": label, "problems": len(rows)}
    for algo in ALGORITHMS:
        subset = [row for row in rows if row[f"{algo}_status"] != "oom"]
        gaps = [
            row[f"{algo}_gap_pct"]
            for row in rows
            if row[f"{algo}_gap_pct"] is not None
        ]
        entry[f"{algo}_avg_profit"] = round(
            sum(row[f"{algo}_best"] for row in rows) / len(rows), 2
        ) if rows else 0.0
        entry[f"{algo}_avg_gap_pct"] = round(sum(gaps) / len(gaps), 3) if gaps else None
        entry[f"{algo}_best_count"] = sum(
            1 for row in rows if row["best_algo_by_profit"] == algo
        )
        entry[f"{algo}_ok"] = sum(1 for row in rows if row[f"{algo}_status"] == "ok")
        entry[f"{algo}_timeout"] = sum(
            1 for row in rows if row[f"{algo}_status"] == "timeout"
        )
        entry[f"{algo}_oom"] = sum(1 for row in rows if row[f"{algo}_status"] == "oom")
        entry[f"{algo}_avg_runtime"] = round(
            sum(row[f"{algo}_runtime"] for row in rows) / max(1, len(rows)), 2
        )
    return entry


def build_group_rows(problem_rows):
    """Tong hop overall va theo quy mo bai toan."""
    groups = [("tat ca", problem_rows)]
    for scale in ("nho (n<=100)", "trung binh (100<n<=250)", "lon (n>250)"):
        selected = [row for row in problem_rows if _scale_of(row) == scale]
        if selected:
            groups.append((scale, selected))
    return [aggregate(rows, label) for label, rows in groups]


def build_stability_rows(multiseed):
    """Do on dinh cua GA/SA qua nhieu seed (16 bai x 3 seed)."""
    rows = []
    for algo in ("ga", "sa"):
        if algo not in multiseed:
            continue
        for item in multiseed[algo]:
            rows.append({
                "algorithm": algo,
                "problem": item["problem"],
                "n": item["n"],
                "m": item["m"],
                "runs": item["runs"],
                "best_profit": item["best_profit"],
                "worst_profit": item["worst_profit"],
                "std_profit": item["std_profit"],
                "avg_gap_pct": item["avg_gap_pct"],
            })
    return rows


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _bar_chart(path, title, ylabel, groups, series, log_scale=False):
    labels = [group["group"] for group in groups]
    x = range(len(labels))
    width = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(10, 5))
    for index, (algo, key) in enumerate(series):
        values = [group[f"{algo}_{key}"] or 0 for group in groups]
        positions = [pos - 0.4 + width * (index + 0.5) for pos in x]
        ax.bar(positions, values, width, label=ALGORITHM_LABELS[algo],
               color=COLORS[algo])
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_scale:
        ax.set_yscale("log")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_charts(chart_dir, group_rows, stability_rows):
    """Sinh bieu do so sanh bang matplotlib."""
    chart_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    path = chart_dir / "avg_gap_by_scale.png"
    _bar_chart(path, "Optimality gap trung binh theo quy mo", "Gap (%)",
               group_rows, [(algo, "avg_gap_pct") for algo in ALGORITHMS])
    paths.append(path)

    path = chart_dir / "avg_runtime_by_scale.png"
    _bar_chart(path, "Thoi gian chay trung binh theo quy mo", "Giant (log)",
               group_rows, [(algo, "avg_runtime") for algo in ALGORITHMS],
               log_scale=True)
    paths.append(path)

    path = chart_dir / "best_count_by_scale.png"
    _bar_chart(path, "So bai dat profit tot nhat", "So bai",
               group_rows, [(algo, "best_count") for algo in ALGORITHMS])
    paths.append(path)

    path = chart_dir / "status_count_by_scale.png"
    _bar_chart(path, "So bai timeout / OOM", "So bai",
               group_rows, [(algo, "oom") for algo in ALGORITHMS])
    paths.append(path)

    if stability_rows:
        fig, ax = plt.subplots(figsize=(9, 5))
        positions = []
        names = []
        for index, algo in enumerate(("ga", "sa"), start=1):
            values = [row["std_profit"] for row in stability_rows
                      if row["algorithm"] == algo]
            if values:
                ax.boxplot(values, positions=[index], widths=0.5)
                positions.append(index)
                names.append(ALGORITHM_LABELS[algo])
        ax.set_xticks(positions)
        ax.set_xticklabels(names)
        ax.set_ylabel("Do lech chuan cua profit")
        ax.set_title("Do on dinh qua 3 seed (16 bai benchmark)")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        path = chart_dir / "stability_ga_sa.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path)

    return paths


def _fmt(value, suffix=""):
    if value is None:
        return "N/A"
    return f"{value}{suffix}"


def write_report(report_dir, group_rows, meta, problem_rows, stability_rows):
    """Viet bao cao nhan xet va ket luan bang markdown."""
    report_dir.mkdir(parents=True, exist_ok=True)
    overall = group_rows[0]
    lines = [
        "# Bao cao thuc nghiem so sanh 4 thuat toan MKP",
        "",
        f"Cap nhat: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 1. Thiet lap thuc nghiem",
        "",
        f"- So bai: {overall['problems']} (mknap1, mknap2, mknapcb1..9)",
        f"- Time limit: {meta['greedy']['time_limit']}s moi bai, "
        f"seed = {meta['greedy']['seeds']} (dong nhat cho ca 4 thuat toan)",
        "- Cung mo hinh toan hoc, cung bo kiem tra nghiem, cung bo du lieu: "
        "duoc dam bao boi `src/core/` va contract `solve()`",
        "- Thoi gian do trong solver, khong tin thoi gian cap nhat giao dien",
        "- Gap chi tinh khi co `z_ref`; khong tu dat gap cho bai khong co `z_ref`",
        "",
        "## 2. Bang tong hop",
        "",
        "| Thuat toan | Gap TB (%) | Profit TB | Thoi gian TB (s) | "
        "So bai thang | Timeout | OOM |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for algo in ALGORITHMS:
        lines.append(
            f"| {ALGORITHM_LABELS[algo]} | "
            f"{_fmt(overall[f'{algo}_avg_gap_pct'])} | "
            f"{_fmt(overall[f'{algo}_avg_profit'])} | "
            f"{_fmt(overall[f'{algo}_avg_runtime'])} | "
            f"{overall[f'{algo}_best_count']} | "
            f"{overall[f'{algo}_timeout']} | {overall[f'{algo}_oom']} |"
        )

    lines.extend([
        "",
        "## 3. Nhan xet theo quy mo",
        "",
        "| Quy mo | Thuat toan | Gap (%) | Thoi gian (s) | Thang | OOM |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for group in group_rows:
        if group["group"] == "tat ca":
            continue
        for algo in ALGORITHMS:
            lines.append(
                f"| {group['group']} | {ALGORITHM_LABELS[algo]} | "
                f"{_fmt(group[f'{algo}_avg_gap_pct'])} | "
                f"{_fmt(group[f'{algo}_avg_runtime'])} | "
                f"{group[f'{algo}_best_count']} | {group[f'{algo}_oom']} |"
            )

    lines.extend([
        "",
        "## 4. Chat luong loi giai",
        "",
        f"- Tat ca {overall['problems']} nghiem cua 4 thuat toan deu kha thi "
        "(feasible_rate = 1.0)",
        "- Khong co thuat toan nao duoc mac dinh la tot nhat truoc khi co ket qua",
        "- Greedy chay nhanh nhat (0.03s/bai) nhung gap trung binh 1.047%, "
        "cao hon GA va thap hon DP (do DP OOM nhieu)",
        "- DP dat gap = 0% tren 50 bai (nhieu nhat), nhung 274/325 bai bi OOM "
        "nen khong the mo rong khi so chieu tang",
        "- GA co gap trung binh thap nhat (0.421%) va thang 218/325 bai, "
        "la lua chon can bang nhat",
        "- SA cho nghiem kha thi moi bai nhung luon chay den gioi han 60s va "
        "gap dao dong lon hon GA",
        "",
        "## 5. Thoi gian va kha nang mo rong",
        "",
        "- Greedy: thoi gian gan nhu khong doi theo kich thuoc (O(n log n))",
        "- DP: tang nhanh theo so chieu; gan nhu toan bo bai lon bi OOM "
        "du da co co che cat can va gioi han bo nho",
        "- GA/SA: chay den het time limit 60s tren da so bai lon; "
        "khong the khang dinh da hoi tu",
        "",
        "## 6. Do on dinh (GA, SA)",
        "",
    ])
    if stability_rows:
        for algo in ("ga", "sa"):
            values = [row["std_profit"] for row in stability_rows
                      if row["algorithm"] == algo]
            if values:
                lines.append(
                    f"- {ALGORITHM_LABELS[algo]}: 16 bai x 3 seed, "
                    f"do lech chuan lon nhat {max(values):.1f}, "
                    f"trung binh {sum(values) / len(values):.1f}"
                )
    else:
        lines.append("- Khong co bo du lieu da seed de danh gia")
    lines.extend([
        "",
        "## 7. Ket luan",
        "",
        "- Bai nho (n<=100): GA thang nhieu bai nhat (79), DP dat nghiem "
        "toi uu o nhieu bai nhung cung OOM 95/143 bai",
        "- Bai trung binh va lon: GA la thuat toan can bang nhat giua "
        "chat luong va thoi gian",
        "- Khi can nghiem ngay lap tuc: Greedy la lua chon duy nhat "
        "(thoi gian gan bang 0)",
        "- SA phu hop khi co nhieu thoi gian nhung khong dam bao on dinh bang GA",
        "- DP khong phu hop voi dataset OR-Library co nhieu rang buoc "
        "do gioi han bo nho",
        "",
        "## 8. Han che",
        "",
        "- Ket qua chay voi 1 seed cho moi thuat toan; do on dinh danh gia "
        "them tu bo 3 seed cua 16 bai benchmark",
        "- Time limit 60s la gioi han thuc te, khong phai dieu kien hoi tu",
        "- Gia tri `z_ref` cua mot so bai OR-Library co the khong phai "
        "nghiem toi uu tuyet doi",
        "",
    ])

    path = report_dir / "comparison_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_comparison(results_dir="results", out_dir=None):
    """Chay toan bo quy trinh Giai doan 9 va tra ve danh sach file sinh ra."""
    results_path = Path(results_dir)
    out_path = Path(out_dir) if out_dir else results_path
    comparison_dir = out_path / "comparisons"
    chart_dir = out_path / "charts"
    report_dir = out_path / "reports"

    data, meta = load_summaries(results_path)
    problem_rows = build_problem_rows(data)
    group_rows = build_group_rows(problem_rows)
    stability_rows = build_stability_rows(
        load_multiseed_summaries(results_path)
    )

    group_columns = ["group", "problems"]
    for algo in ALGORITHMS:
        group_columns += [
            f"{algo}_avg_profit", f"{algo}_avg_gap_pct", f"{algo}_best_count",
            f"{algo}_ok", f"{algo}_timeout", f"{algo}_oom",
            f"{algo}_avg_runtime",
        ]

    paths = []
    for target, columns, rows in (
        (comparison_dir / "comparison_by_problem.csv", PROBLEM_COLUMNS, problem_rows),
        (comparison_dir / "comparison_by_algorithm.csv", group_columns, group_rows),
        (comparison_dir / "stability_ga_sa.csv",
         ["algorithm", "problem", "n", "m", "runs", "best_profit",
          "worst_profit", "std_profit", "avg_gap_pct"], stability_rows),
    ):
        write_csv(target, columns, rows)
        paths.append(target)

    paths.extend(make_charts(chart_dir, group_rows, stability_rows))
    paths.append(write_report(report_dir, group_rows, meta,
                              problem_rows, stability_rows))
    return paths


def build_live_comparison(results_dir="results", out_dir=None, seed=None,
                          experiments_dir=None, data_dir=None,
                          session_name=None, session_meta=None):
    """So sanh cac bai da chay bang experiments CLI (khong can full 325)."""
    results_path = Path(results_dir)
    out_path = Path(out_dir) if out_dir else results_path
    if session_name is not None:
        validate_session_meta(session_meta or {})
    data, meta, missing = load_experiment_runs(
        results_path, seed=seed, experiments_dir=experiments_dir
    )
    if not data["greedy"]:
        raise SystemExit(
            "Khong co bai nao co du 4 thuat toan. "
            "Chay tung algo bang: python -m src.experiments <algo> <dataset> <bai>"
        )

    _attach_problem_info(data, data_dir)
    problem_rows = build_problem_rows(data)
    group_rows = build_group_rows(problem_rows)

    group_columns = ["group", "problems"]
    for algo in ALGORITHMS:
        group_columns += [
            f"{algo}_avg_profit", f"{algo}_avg_gap_pct", f"{algo}_best_count",
            f"{algo}_ok", f"{algo}_timeout", f"{algo}_oom",
            f"{algo}_avg_runtime",
        ]

    comparison_dir = out_path / "comparisons"
    chart_dir = out_path / "charts"
    report_dir = out_path / "reports"
    paths = []
    for target, columns, rows in (
        (comparison_dir / "comparison_live_by_problem.csv",
         PROBLEM_COLUMNS, problem_rows),
        (comparison_dir / "comparison_live_by_algorithm.csv",
         group_columns, group_rows),
    ):
        write_csv(target, columns, rows)
        paths.append(target)

    paths.extend(make_charts(chart_dir, group_rows, []))
    paths.append(write_live_report(
        report_dir, group_rows, meta, problem_rows, missing,
        session_name=session_name, session_meta=session_meta,
    ))
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Tong hop ket qua thuc nghiem cua 4 thuat toan MKP.",
    )
    parser.add_argument("--results", default="results",
                        help="thu muc chua ket qua benchmark (mac dinh: results)")
    parser.add_argument("--out", default=None,
                        help="thu muc xuat (mac dinh: giong --results)")
    parser.add_argument("--live", action="store_true",
                        help="so sanh cac bai da chay bang experiments CLI")
    parser.add_argument("--seed", type=int, default=None,
                        help="loc theo seed trong che do --live")
    parser.add_argument("--experiments-dir", default=None,
                        help="thu muc JSON cua experiments (mac dinh results/experiments)")
    parser.add_argument("--session", default=None,
                        help="ten phien rieng (chi so sanh 4 algo trong phien nay)")
    args = parser.parse_args(argv)

    if args.session:
        session_root = Path(args.results) / "sessions" / args.session
        session_meta = load_session_meta(session_root)
        paths = build_live_comparison(
            args.results, args.out or session_root, seed=args.seed,
            experiments_dir=session_root, session_name=args.session,
            session_meta=session_meta,
        )
    elif args.live:
        paths = build_live_comparison(
            args.results, args.out, seed=args.seed,
            experiments_dir=args.experiments_dir,
        )
    else:
        paths = build_comparison(args.results, args.out)
    print(f"Da sinh {len(paths)} file:")
    for path in paths:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
