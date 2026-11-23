import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from src.algorithms import ALGORITHM_NAMES, get_solver
from src.core.config import DATA_DIR, TIME_LIMIT_SECONDS
from src.core.data_loader import load_problems

from .metrics import ExperimentMetrics


ALIASES = {
    "greedy": "greedy",
    "dp": "dynamic_programming",
    "dynamic_programming": "dynamic_programming",
    "ga": "genetic_algorithm",
    "genetic_algorithm": "genetic_algorithm",
    "sa": "simulated_annealing",
    "simulated_annealing": "simulated_annealing",
}

CANONICAL_NAMES = {
    "greedy": "greedy",
    "dynamic_programming": "dp",
    "genetic_algorithm": "ga",
    "simulated_annealing": "sa",
}


def normalize_algorithm(name: str) -> str:
    key = name.strip().lower()
    if key not in ALIASES:
        raise SystemExit(
            f"Khong co thuat toan '{name}'. Chon: {', '.join(ALGORITHM_NAMES)}"
        )
    return ALIASES[key]


def resolve_dataset(name: str) -> Path:
    """Nhan 'mknapcb4', 'mknapcb4.txt' hoac duong dan day du."""
    path = Path(name)
    for candidate in (path, DATA_DIR / name, DATA_DIR / f"{name}.txt"):
        if candidate.is_file():
            return candidate
    raise SystemExit(
        f"Khong tim thay dataset '{name}'. Chay 'python run_algo.py --list' de xem."
    )


def gap_text(result) -> str:
    if result.optimality_gap is None:
        return "-"
    return f"{result.optimality_gap * 100:.2f}%"


def print_one(problem, result, show_items: bool) -> None:
    z_ref = "-" if problem.z_ref is None else f"{problem.z_ref:.0f}"
    print(
        f"{problem.name}: n={problem.n} m={problem.m} z_ref={z_ref} | "
        f"profit={result.total_profit:.0f} gap={gap_text(result)} "
        f"time={result.runtime:.2f}s feasible={result.feasible} "
        f"status={result.status}"
    )
    if show_items:
        print(f"  items ({len(result.selected_items)}): {result.selected_items}")


def print_table(rows) -> None:
    header = (
        f"{'problem':<16}{'n':>5}{'m':>4}{'z_ref':>9}"
        f"{'profit':>9}{'gap':>8}{'time':>7}{'feasible':>9}{'status':>14}"
    )
    print("\n" + header)
    print("-" * len(header))
    for problem, result, gap in rows:
        z_ref = "-" if problem.z_ref is None else f"{problem.z_ref:.0f}"
        print(
            f"{problem.name:<16}{problem.n:>5}{problem.m:>4}{z_ref:>9}"
            f"{result.total_profit:>9.0f}{gap:>8}{result.runtime:>7.2f}"
            f"{str(result.feasible):>9}{result.status:>14}"
        )


def list_datasets() -> None:
    print(f"{'file':<18}{'so bai':>7}")
    print("-" * 25)
    for path in sorted(DATA_DIR.glob("*.txt")):
        if path.name == "mkcbres.txt":
            continue
        try:
            count = len(load_problems(path))
        except Exception as exc:
            print(f"{path.name:<18}{'LOI':>7}  ({exc})")
            continue
        print(f"{path.name:<18}{count:>7}")


def build_parser(default_algorithm=None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chay thuat toan MKP tren dataset va luu ket qua.",
        epilog="Vi du: python -m src.experiments ga mknapcb4 all -t 10 -s 1",
    )
    if default_algorithm is None:
        parser.add_argument("algorithm", nargs="?", help="greedy | dp | ga | sa")
    parser.add_argument(
        "dataset", nargs="?",
        help="vd: mknapcb4, mknapcb4.txt hoac 'all' (tat ca dataset)",
    )
    parser.add_argument(
        "problem",
        nargs="?",
        default="1",
        help="so bai (tinh tu 1) hoac 'all' (mac dinh: 1)",
    )
    parser.add_argument(
        "-t", "--time-limit", type=float, default=TIME_LIMIT_SECONDS,
        help=f"giay chay moi bai (mac dinh {TIME_LIMIT_SECONDS})",
    )
    parser.add_argument("-s", "--seed", type=int, default=0, help="seed (mac dinh 0)")
    parser.add_argument("-l", "--list", action="store_true", help="liet ke dataset")
    parser.add_argument("--no-items", action="store_true",
                        help="khong in danh sach mat hang")
    parser.add_argument(
        "--out",
        help="thu muc luu ket qua (mac dinh results/experiments/<algo>)",
    )
    parser.add_argument("--no-save", action="store_true",
                        help="chi in man hinh, khong luu ket qua")
    parser.add_argument("--session",
                        help="ten phien thử nghiem rieng (vd cb4_t30_s1)")
    return parser


def run_experiment(default_algorithm=None) -> int:
    """Run a single experiment with given parameters."""
    parser = build_parser(default_algorithm)
    args = parser.parse_args()

    if args.list:
        list_datasets()
        return 0
    if not args.dataset:
        parser.print_help()
        return 1
    if default_algorithm is None and not args.algorithm:
        parser.error("thieu ten thuat toan (greedy | dp | ga | sa)")

    algorithm = (
        normalize_algorithm(default_algorithm)
        if default_algorithm is not None
        else normalize_algorithm(args.algorithm)
    )
    solver = get_solver(algorithm)
    if args.dataset.strip().lower() in ("all", "*"):
        datasets = [
            path for path in sorted(DATA_DIR.glob("*.txt"))
            if path.name != "mkcbres.txt"
        ]
    else:
        datasets = [resolve_dataset(args.dataset)]

    session_dir = (
        Path("results") / "sessions" / args.session if args.session else None
    )
    if session_dir is not None:
        output_dir = session_dir / algorithm
    elif args.out:
        output_dir = Path(args.out)
    else:
        output_dir = Path("results") / "experiments" / algorithm
    save_enabled = not args.no_save
    if save_enabled:
        print(f"Ket qua se duoc luu vao: {output_dir}")

    rows = []
    metrics_list = []
    started = time.perf_counter()
    for dataset in datasets:
        problems = load_problems(dataset)

        if args.problem.lower() in ("all", "*"):
            numbers = None
        else:
            try:
                number = int(args.problem)
            except ValueError:
                parser.error("problem phai la so hoac 'all'")
            if not 1 <= number <= len(problems):
                if len(datasets) == 1:
                    raise SystemExit(
                        f"{dataset.name} co {len(problems)} bai, "
                        f"khong co bai {number}."
                    )
                continue
            numbers = [number - 1]

        selected = problems if numbers is None else [problems[i] for i in numbers]
        estimate = len(selected) * max(0.0, args.time_limit)
        print(
            f"\n{algorithm} | {dataset.name}: chay {len(selected)} bai, "
            f"time_limit={args.time_limit}s, seed={args.seed} "
            f"(~{estimate / 60:.1f} phut)"
        )

        for index, problem in enumerate(selected, start=1):
            print(f"[{index}/{len(selected)}] ", end="", flush=True)
            try:
                result = solver(problem, time_limit=args.time_limit, seed=args.seed)
            except NotImplementedError as exc:
                print(f"{problem.name}: CHUA CAI DAT ({exc})")
                continue
            except Exception as exc:
                print(f"{problem.name}: LOI ({exc})")
                continue
            print_one(problem, result, not args.no_items)
            rows.append((problem, result, gap_text(result)))

            if save_enabled:
                metrics = ExperimentMetrics.from_result(
                    algorithm,
                    dataset.name,
                    problem.name,
                    args.seed,
                    args.time_limit,
                    result,
                    datetime.now().isoformat(timespec="seconds"),
                )
                metrics_list.append(metrics)
                metrics.save_to_json(output_dir)
                ExperimentMetrics.save_summary(metrics_list, output_dir)

    if session_dir is not None and save_enabled:
        session_dir.mkdir(parents=True, exist_ok=True)
        meta_path = session_dir / "session_meta.json"
        meta = {}
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                meta = {}
        canonical = CANONICAL_NAMES[algorithm]
        meta.pop(algorithm, None)
        meta[canonical] = {
            "datasets": [dataset.name for dataset in datasets],
            "problem": args.problem,
            "time_limit": args.time_limit,
            "seed": args.seed,
            "updated": datetime.now().isoformat(timespec="seconds"),
        }
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if len(rows) > 1:
        print_table(rows)
    print(f"Tong thoi gian: {(time.perf_counter() - started) / 60:.2f} phut")
    if save_enabled and metrics_list:
        print(f"Da luu {len(metrics_list)} ket qua vao: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(run_experiment())