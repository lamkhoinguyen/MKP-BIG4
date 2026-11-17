"""Benchmark mot thuat toan MKP tren bo de, luu ket qua de so sanh sau nay.

Khac voi run_algo.py (chi in man hinh), script nay chay nhieu bai x nhieu seed,
luu CSV/JSON vao results/<thuat_toan>/ theo cung mot dinh dang cho ca 4 thuat toan.

Vi du (chay tu thu muc goc repo):
    python benchmark_algo.py ga
    python benchmark_algo.py ga -t 30 --seeds 1,2,3
    python benchmark_algo.py sa -t 30 --seeds 1,2,3
    python benchmark_algo.py ga --dataset mknapcb4 -t 5 --seeds 1
    python benchmark_algo.py ga --dataset all -t 30 --seeds 1

Mac dinh: 16 bai trong BENCHMARK_PROBLEMS, seeds 1,2,3, time_limit = config.

File sinh ra trong results/<thuat_toan>/:
    <algo>_runs.csv / .json      : tung luot chay (kem history)
    <algo>_summary.csv / .json   : tong hop theo bai (best/avg/worst/std/gap)
    <algo>_meta.json             : cau hinh cua lan chay
    progress.log                 : tien do
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

from run_algo import normalize_algorithm, resolve_dataset
from src.algorithms import get_solver
from src.core.config import (
    BENCHMARK_PROBLEMS,
    DATA_DIR,
    SEED,
    STATUS_OUT_OF_MEMORY,
    STATUS_TIMEOUT,
    TIME_LIMIT_SECONDS,
)
from src.core.data_loader import get_problem, load_problems


RUN_COLUMNS = [
    "file", "problem", "n", "m", "seed", "z_ref", "profit", "gap_pct",
    "runtime", "peak_memory_mb", "feasible", "status", "selected_count",
    "history_points",
]
SUMMARY_COLUMNS = [
    "file", "problem", "n", "m", "z_ref", "runs", "best_profit", "avg_profit",
    "worst_profit", "std_profit", "avg_gap_pct", "avg_runtime", "feasible_rate",
    "timeout_runs", "oom_runs", "peak_memory_mb",
]


def parse_seeds(text: str) -> list:
    seeds = []
    for token in text.replace(" ", ",").split(","):
        token = token.strip()
        if token:
            seeds.append(int(token))
    if not seeds:
        raise argparse.ArgumentTypeError("--seeds phai co it nhat 1 so")
    return seeds


def collect_problems(dataset):
    if dataset:
        if dataset.strip().lower() in ("all", "*"):
            problems = []
            for path in sorted(DATA_DIR.glob("*.txt")):
                if path.name == "mkcbres.txt":
                    continue
                problems.extend(
                    (path.name, problem) for problem in load_problems(path)
                )
            return problems
        path = resolve_dataset(dataset)
        problems = [
            (path.name, problem) for problem in load_problems(path)
        ]
    else:
        problems = [
            (file_name, get_problem(file_name, number))
            for file_name, number in BENCHMARK_PROBLEMS
        ]
    return problems


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize(runs):
    groups = {}
    for row in runs:
        groups.setdefault((row["file"], row["problem"]), []).append(row)

    summary = []
    for (file_name, problem_name), group in groups.items():
        profits = [r["profit"] for r in group]
        gaps = [r["gap_pct"] for r in group if r["gap_pct"] is not None]
        statuses = [r["status"] for r in group]
        peaks = [r.get("peak_memory_mb") or 0.0 for r in group]
        first = group[0]
        summary.append({
            "file": file_name,
            "problem": problem_name,
            "n": first["n"],
            "m": first["m"],
            "z_ref": first["z_ref"],
            "runs": len(group),
            "best_profit": max(profits),
            "avg_profit": round(float(np.mean(profits)), 2),
            "worst_profit": min(profits),
            "std_profit": round(float(np.std(profits)), 2),
            "avg_gap_pct": round(float(np.mean(gaps)), 3) if gaps else None,
            "avg_runtime": round(float(np.mean([r["runtime"] for r in group])), 2),
            "feasible_rate": round(
                float(np.mean([1.0 if r["feasible"] else 0.0 for r in group])), 3
            ),
            "timeout_runs": sum(1 for s in statuses if s == STATUS_TIMEOUT),
            "oom_runs": sum(1 for s in statuses if s == STATUS_OUT_OF_MEMORY),
            "peak_memory_mb": round(max(peaks), 1),
        })
    return summary


def print_summary(summary):
    header = (
        f"{'problem':<18}{'n':>5}{'m':>4}{'z_ref':>9}"
        f"{'best':>9}{'avg':>9}{'worst':>9}{'std':>8}"
        f"{'gap%':>8}{'time':>7}{'feas':>6}"
    )
    print("\n" + header)
    print("-" * len(header))
    for row in summary:
        gap = "-" if row["avg_gap_pct"] is None else f"{row['avg_gap_pct']:.2f}"
        z_ref = "-" if row["z_ref"] is None else f"{row['z_ref']:.0f}"
        print(
            f"{row['problem']:<18}{row['n']:>5}{row['m']:>4}{z_ref:>9}"
            f"{row['best_profit']:>9.0f}{row['avg_profit']:>9.0f}"
            f"{row['worst_profit']:>9.0f}{row['std_profit']:>8.1f}"
            f"{gap:>8}{row['avg_runtime']:>7.2f}{row['feasible_rate']:>6.2f}"
        )


def save_results(out_dir, alias, runs, summary, meta):
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / f"{alias}_runs.csv", RUN_COLUMNS, runs)
    with open(out_dir / f"{alias}_runs.json", "w", encoding="utf-8") as handle:
        json.dump(runs, handle, ensure_ascii=False)
    write_csv(out_dir / f"{alias}_summary.csv", SUMMARY_COLUMNS, summary)
    with open(out_dir / f"{alias}_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    with open(out_dir / f"{alias}_meta.json", "w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark 1 thuat toan MKP tren bo de, luu results/<algo>/.",
        epilog="Vi du: python benchmark_algo.py ga -t 30 --seeds 1,2,3",
    )
    parser.add_argument("algorithm", help="greedy | dp | ga | sa")
    parser.add_argument("-t", "--time-limit", type=float, default=TIME_LIMIT_SECONDS,
                        help=f"giay moi luot (mac dinh {TIME_LIMIT_SECONDS})")
    parser.add_argument("--seeds", type=parse_seeds, default=list(SEED)[:3],
                        help="danh sach seed, vd 1,2,3 (mac dinh: 3 seed dau)")
    parser.add_argument(
        "--dataset",
        help="chay toan bo 1 file hoac 'all' (tat ca dataset) thay vi 16 bai benchmark",
    )
    parser.add_argument("--out", help="thu muc ket qua (mac dinh results/<algo>)")
    args = parser.parse_args()

    algorithm = normalize_algorithm(args.algorithm)
    alias = args.algorithm.strip().lower()
    try:
        solver = get_solver(algorithm)
    except KeyError as exc:
        raise SystemExit(str(exc))

    problems = collect_problems(args.dataset)
    is_all = bool(args.dataset) and args.dataset.strip().lower() in ("all", "*")
    if args.out:
        out_dir = Path(args.out)
    elif is_all:
        out_dir = Path("results") / f"{alias}_all"
    else:
        out_dir = Path("results") / alias
    total = len(problems) * len(args.seeds)
    estimate = total * max(0.0, args.time_limit)
    print(
        f"{algorithm} | {len(problems)} bai x {len(args.seeds)} seed "
        f"({args.seeds}) x {args.time_limit}s = {total} luot "
        f"(~{estimate / 60:.1f} phut)"
    )
    print(f"Ket qua: {out_dir}")

    (out_dir).mkdir(parents=True, exist_ok=True)
    progress_path = out_dir / "progress.log"
    progress_path.write_text("", encoding="utf-8")

    meta = {
        "algorithm": algorithm,
        "alias": alias,
        "time_limit": args.time_limit,
        "seeds": args.seeds,
        "dataset": args.dataset,
        "problems": [problem.name for _, problem in problems],
        "total_runs": total,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    runs = []
    failed = 0
    started = time.perf_counter()
    index = 0

    for file_name, problem in problems:
        for seed in args.seeds:
            index += 1
            try:
                result = solver(problem, time_limit=args.time_limit, seed=seed)
            except Exception as exc:
                failed += 1
                line = f"[{index:>3}/{total}] FAIL {problem.name} seed={seed}: {exc}"
                print(line, flush=True)
                with open(progress_path, "a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
                continue

            gap_pct = (
                None if result.optimality_gap is None
                else round(result.optimality_gap * 100, 3)
            )
            row = {
                "file": file_name,
                "problem": problem.name,
                "n": problem.n,
                "m": problem.m,
                "seed": seed,
                "z_ref": problem.z_ref,
                "profit": round(float(result.total_profit), 2),
                "gap_pct": gap_pct,
                "runtime": round(float(result.runtime), 3),
                "peak_memory_mb": round(float(result.peak_memory), 1),
                "feasible": bool(result.feasible),
                "status": result.status,
                "selected_count": len(result.selected_items),
                "history_points": len(result.history),
            }
            runs.append({**row, "history": result.history})

            gap_text = "-" if gap_pct is None else f"{gap_pct:.2f}%"
            elapsed = time.perf_counter() - started
            eta = elapsed / index * (total - index)
            line = (
                f"[{index:>3}/{total}] {problem.name:<14} seed={seed} "
                f"profit={row['profit']:.0f} gap={gap_text:<8} "
                f"time={row['runtime']:.2f}s feasible={row['feasible']} "
                f"status={row['status']} eta={eta/60:.1f}min"
            )
            print(line, flush=True)
            with open(progress_path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")

            summary = summarize(runs)
            meta["completed_runs"] = len(runs)
            meta["failed_runs"] = failed
            save_results(out_dir, alias, runs, summary, meta)

    summary = summarize(runs)
    meta["completed_runs"] = len(runs)
    meta["failed_runs"] = failed
    meta["finished_at"] = datetime.now().isoformat(timespec="seconds")
    meta["wall_minutes"] = round((time.perf_counter() - started) / 60, 2)
    save_results(out_dir, alias, runs, summary, meta)

    if summary:
        print_summary(summary)
    print(
        f"\nDONE {len(runs)}/{total} runs, failed={failed}, "
        f"{(time.perf_counter() - started)/60:.1f} min"
    )
    print(f"Saved: {out_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
