"""Logic thuần cho GUI: thống kê, chuỗi hội tụ và nhận xét tự động.

Module này không import Qt để có thể test bằng pytest thường.
"""

import math
from typing import Any, Iterable, Optional

ALGORITHMS = (
    "greedy",
    "dynamic_programming",
    "genetic_algorithm",
    "simulated_annealing",
)

SHORT_LABELS = {
    "greedy": "Greedy",
    "dynamic_programming": "DP",
    "genetic_algorithm": "GA",
    "simulated_annealing": "SA",
}

LONG_LABELS = {
    "greedy": "Greedy (tham lam)",
    "dynamic_programming": "Dynamic Programming (quy hoạch động)",
    "genetic_algorithm": "Genetic Algorithm (di truyền)",
    "simulated_annealing": "Simulated Annealing (mô phỏng luyện kim)",
}

STOCHASTIC = ("genetic_algorithm", "simulated_annealing")

STATUS_SHORT = {
    "ok": "ok",
    "timeout": "timeout",
    "out_of_memory": "oom",
    "error": "error",
}


def label_for(algorithm: str) -> str:
    return SHORT_LABELS.get(algorithm, algorithm)


def seeds_for(base_seed: int, count: int) -> list[int]:
    """Danh sách seed s, s+1, ..., s+count-1."""
    return [int(base_seed) + offset for offset in range(max(0, int(count)))]


def estimate_seconds(time_limit: float, num_seeds: int) -> float:
    """Cận trên thời gian phiên: T × (2N + 2)."""
    return max(0.0, float(time_limit)) * (2 * int(num_seeds) + 2)


def build_plan(base_seed: int, num_seeds: int) -> list[tuple[str, int]]:
    """Danh sách lượt chạy theo thứ tự: Greedy, DP, GA × N, SA × N."""
    seeds = seeds_for(base_seed, num_seeds)
    plan: list[tuple[str, int]] = [
        ("greedy", int(base_seed)),
        ("dynamic_programming", int(base_seed)),
    ]
    for algorithm in ("genetic_algorithm", "simulated_annealing"):
        for seed in seeds:
            plan.append((algorithm, seed))
    return plan


def _num(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _history_value(entry: dict) -> Optional[float]:
    if "best_profit" in entry and entry["best_profit"] is not None:
        return _num(entry["best_profit"])
    return _num(entry.get("profit"))


def error_record(message: str, seed: int = 0) -> dict:
    return {
        "seed": int(seed),
        "profit": None,
        "gap": None,
        "runtime": 0.0,
        "feasible": False,
        "status": "error",
        "selected_count": 0,
        "peak_memory": 0.0,
        "history": [],
        "error": str(message),
    }


def run_record(result, seed: int) -> dict:
    """Chuyển MKPResult thành bản ghi thuần Python."""
    history = [dict(entry) for entry in (getattr(result, "history", None) or [])]
    return {
        "seed": int(seed),
        "profit": _num(getattr(result, "total_profit", None)),
        "gap": _num(getattr(result, "optimality_gap", None)),
        "runtime": _num(getattr(result, "runtime", None)) or 0.0,
        "feasible": bool(getattr(result, "feasible", False)),
        "status": str(getattr(result, "status", "ok")),
        "selected_count": len(getattr(result, "selected_items", None) or []),
        "peak_memory": _num(getattr(result, "peak_memory", 0.0)) or 0.0,
        "history": history,
        "error": None,
    }


def record_from_result(result, seed: int) -> dict:
    """Alias dễ đọc cho ``run_record``."""
    return run_record(result, seed)


def status_summary(runs: Iterable[dict]) -> str:
    runs = list(runs)
    if not runs:
        return "-"
    counts: dict[str, int] = {}
    for run in runs:
        status = STATUS_SHORT.get(str(run.get("status", "ok")), str(run.get("status", "ok")))
        counts[status] = counts.get(status, 0) + 1
    if len(counts) == 1:
        status, count = next(iter(counts.items()))
        return status if count == len(runs) else f"{status} ×{count}"
    order = ["ok", "timeout", "oom", "error"]
    parts = []
    for status in order:
        if status in counts:
            parts.append(f"{status} ×{counts[status]}")
    for status, count in counts.items():
        if status not in order:
            parts.append(f"{status} ×{count}")
    return ", ".join(parts)


def summarize_runs(runs: Iterable[dict]) -> dict:
    runs = list(runs)
    if not runs:
        return {
            "count": 0,
            "best": None,
            "avg": None,
            "worst": None,
            "std": None,
            "gap_best": None,
            "gap_avg": None,
            "runtime_avg": None,
            "feasible": "0/0",
            "status": "-",
            "selected_count": None,
            "peak_memory": 0.0,
            "best_run": None,
        }

    valid = [run for run in runs if run.get("profit") is not None]
    profits = [float(run["profit"]) for run in valid]
    if profits:
        best_value = max(profits)
        avg_value = sum(profits) / len(profits)
        worst_value = min(profits)
        std_value = math.sqrt(
            sum((value - avg_value) ** 2 for value in profits) / len(profits)
        )
        best_run = max(valid, key=lambda run: float(run["profit"]))
        gap_best = _num(best_run.get("gap"))
    else:
        best_value = avg_value = worst_value = std_value = None
        best_run = None
        gap_best = None

    gaps = [_num(run.get("gap")) for run in runs]
    gaps = [gap for gap in gaps if gap is not None]
    gap_avg = sum(gaps) / len(gaps) if gaps else None

    runtimes = [_num(run.get("runtime")) for run in runs]
    runtimes = [runtime for runtime in runtimes if runtime is not None]
    runtime_avg = sum(runtimes) / len(runtimes) if runtimes else None

    feasible_count = sum(1 for run in runs if run.get("feasible"))

    peak_memory = max((_num(run.get("peak_memory")) or 0.0) for run in runs)

    return {
        "count": len(runs),
        "best": None if best_value is None else round(best_value, 2),
        "avg": None if avg_value is None else round(avg_value, 2),
        "worst": None if worst_value is None else round(worst_value, 2),
        "std": None if std_value is None else round(std_value, 2),
        "gap_best": gap_best,
        "gap_avg": None if gap_avg is None else round(gap_avg, 6),
        "runtime_avg": None if runtime_avg is None else round(runtime_avg, 4),
        "feasible": f"{feasible_count}/{len(runs)}",
        "status": status_summary(runs),
        "selected_count": None
        if best_run is None
        else int(best_run.get("selected_count") or 0),
        "peak_memory": round(peak_memory, 4),
        "best_run": best_run,
    }


def copy_records(records: dict) -> dict:
    """Sao chép nông từng bản ghi để tránh chia sẻ danh sách giữa các trang."""
    return {
        algorithm: [dict(run) for run in (records.get(algorithm) or [])]
        for algorithm in ALGORITHMS
    }


def build_rows(records: dict[str, list[dict]], num_seeds: int) -> list[dict]:
    """Tạo 4 dòng bảng kết quả từ bản ghi theo thuật toán."""
    rows = []
    for algorithm in ALGORITHMS:
        runs = list(records.get(algorithm, []))
        stats = summarize_runs(runs)
        stochastic = algorithm in STOCHASTIC and int(num_seeds) > 1
        rows.append(
            {
                "algorithm": algorithm,
                "label": label_for(algorithm),
                "profit": stats["best"],
                "avg": stats["avg"] if stochastic else None,
                "worst": stats["worst"] if stochastic else None,
                "std": stats["std"] if stochastic else None,
                "gap_best": stats["gap_best"],
                "gap_avg": stats["gap_avg"] if stochastic else None,
                "runtime": stats["runtime_avg"],
                "feasible": stats["feasible"],
                "status": stats["status"],
                "selected_count": stats["selected_count"],
                "peak_memory": stats["peak_memory"] if stats["peak_memory"] > 0 else None,
                "count": stats["count"],
                "runs": runs,
                "stats": stats,
                "best_run": stats["best_run"],
                "stochastic": stochastic,
            }
        )
    return rows


def _extract_history(result):
    history = getattr(result, "history", None)
    if history is None and isinstance(result, dict):
        history = result.get("history")
    if history is None and isinstance(result, (list, tuple)):
        history = result
    return history or []


def history_series(result) -> list[tuple[float, float]]:
    """Chuỗi (iteration, best_profit) từ result.history."""
    history = _extract_history(result)
    points = []
    for index, entry in enumerate(history):
        if not isinstance(entry, dict):
            continue
        value = _history_value(entry)
        if value is None:
            continue
        x = _num(entry.get("iteration"))
        if x is None:
            x = float(index)
        points.append((float(x), value))
    return points


def progress_series(result_or_history) -> list[tuple[float, float]]:
    """Chuỗi (% tiến trình, best_profit) với x = i/(L-1)×100."""
    history = _extract_history(result_or_history)
    values = []
    for entry in history:
        if not isinstance(entry, dict):
            continue
        value = _history_value(entry)
        if value is not None:
            values.append(value)
    length = len(values)
    if length == 0:
        return []
    if length == 1:
        return [(0.0, values[0])]
    return [
        (index / (length - 1) * 100.0, value)
        for index, value in enumerate(values)
    ]


def fmt_number(value, digits: int = 0, missing: str = "-") -> str:
    if value is None:
        return missing
    try:
        number = float(value)
    except (TypeError, ValueError):
        return missing
    text = f"{number:,.{digits}f}"
    return text.replace(",", ".")


def fmt_percent(value, digits: int = 2, missing: str = "-") -> str:
    if value is None:
        return missing
    try:
        return f"{float(value) * 100:.{digits}f}%".replace(".", ",")
    except (TypeError, ValueError):
        return missing


def fmt_seconds(value, missing: str = "-") -> str:
    if value is None:
        return missing
    try:
        return f"{float(value):.2f} s".replace(".", ",")
    except (TypeError, ValueError):
        return missing


def fmt_duration(seconds, missing: str = "-") -> str:
    """Định dạng thời lượng: '45 giây', '2 phút', '3 phút 20 giây'."""
    if seconds is None:
        return missing
    try:
        total = int(round(float(seconds)))
    except (TypeError, ValueError):
        return missing
    if total < 60:
        return f"{total} giây"
    minutes, secs = divmod(total, 60)
    return f"{minutes} phút" + (f" {secs} giây" if secs else "")


def fmt_compact(value, missing: str = "-") -> str:
    """Số gọn cho tham số (giữ 0,2 thay vì làm tròn thành 0)."""
    if value is None:
        return missing
    try:
        return f"{float(value):g}".replace(".", ",")
    except (TypeError, ValueError):
        return missing


def comments(rows: list[dict], params: dict) -> list[str]:
    """Sinh nhận xét tự động dựa trên số liệu (mục 8.4 đặc tả)."""
    time_limit = float(params.get("time_limit") or 0.0)
    num_seeds = int(params.get("num_seeds") or 1)
    seeds = list(params.get("seeds") or [])
    problem_name = params.get("problem_name") or "-"
    z_ref = params.get("z_ref")

    available = [row for row in rows if row.get("profit") is not None]
    if not available:
        return [
            "Chưa có kết quả hợp lệ trong phiên.",
            f"Bối cảnh: {problem_name}, N = {num_seeds} seed, "
            f"time limit {fmt_compact(time_limit)} giây.",
        ]

    result: list[str] = []

    early = [
        row
        for row in available
        if row.get("runtime") is not None
        and time_limit > 0
        and float(row["runtime"]) < 0.9 * time_limit
        and "timeout" not in str(row.get("status", ""))
    ]
    limited = [row for row in available if row not in early]

    if not early:
        result.append(
            "Cả 4 thuật toán đều dùng hết hoặc gần hết giới hạn thời gian nên "
            "không thể so sánh tốc độ tuyệt đối."
        )
    else:
        early_text = ", ".join(
            f"{row['label']} ({fmt_seconds(row['runtime'])})" for row in early
        )
        result.append(f"Kết thúc sớm (dưới 90% time limit): {early_text}.")
        if limited:
            limited_text = ", ".join(row["label"] for row in limited)
            result.append(
                f"Nhóm dùng gần hết thời gian: {limited_text}; không tuyên bố "
                "nhanh/chậm dựa trên runtime của nhóm này."
            )

    if any(row["algorithm"] not in STOCHASTIC for row in available):
        result.append(
            "Greedy/DP tất định nên chỉ chạy 1 lần; so sánh chất lượng dựa trên "
            "Profit và Gap best, còn Avg/Worst/Std/Gap avg chỉ áp dụng cho "
            "GA/SA khi N > 1."
        )

    profits = [(row, float(row["profit"])) for row in available]
    profits.sort(key=lambda item: item[1], reverse=True)
    best_row, best_profit = profits[0]
    lowest = min(value for _, value in profits)
    if best_profit > 0 and (best_profit - lowest) / best_profit <= 0.005:
        names = ", ".join(row["label"] for row, _ in profits)
        result.append(
            f"Profit giữa các thuật toán chênh lệch không quá 0,5% "
            f"({names} tương đương)."
        )
    else:
        tolerance = max(1e-9, abs(best_profit) * 1e-9)
        best_group = [
            row for row, value in profits if abs(value - best_profit) <= tolerance
        ]
        lower = [
            (row, value)
            for row, value in profits
            if value < best_profit - tolerance
        ]
        if len(best_group) > 1:
            names = ", ".join(row["label"] for row in best_group)
            text = (
                f"{names} cùng đạt profit cao nhất "
                f"({fmt_number(best_profit)})."
            )
            if lower and lower[0][1] > 0:
                margin = (best_profit - lower[0][1]) / lower[0][1] * 100
                text += (
                    f" Cao hơn {lower[0][0]['label']} "
                    f"{fmt_number(margin, 1)}%."
                )
        else:
            text = (
                f"{best_row['label']} đạt profit cao nhất "
                f"({fmt_number(best_profit)})."
            )
            if lower and lower[0][1] > 0:
                margin = (best_profit - lower[0][1]) / lower[0][1] * 100
                text += (
                    f" Cao hơn {lower[0][0]['label']} "
                    f"{fmt_number(margin, 1)}%."
                )
        result.append(text)

    gaps = [
        (row, row["gap_best"])
        for row in available
        if row.get("gap_best") is not None
    ]
    if gaps:
        gap_row, gap_value = min(gaps, key=lambda item: item[1])
        if abs(float(gap_value)) < 1e-12 and z_ref is not None:
            result.append(
                f"{gap_row['label']} đạt giá trị tham chiếu Z_ref "
                f"(gap 0%)."
            )
        else:
            result.append(
                f"Gap nhỏ nhất: {gap_row['label']} "
                f"({fmt_percent(gap_value)})."
            )
    else:
        result.append("Bài toán không có Z_ref nên không tính được gap.")

    if early:
        fastest = min(early, key=lambda row: float(row["runtime"]))
        result.append(
            f"Trong nhóm kết thúc sớm, {fastest['label']} nhanh nhất "
            f"({fmt_seconds(fastest['runtime'])})."
        )

    if num_seeds > 1:
        stability = []
        for row in rows:
            if row["algorithm"] not in STOCHASTIC:
                continue
            if row.get("std") is None:
                continue
            stability.append(row)
        if stability:
            stability.sort(key=lambda row: float(row["std"]))
            text = "; ".join(
                f"{row['label']} std {fmt_number(row['std'], 1)}"
                for row in stability
            )
            text += f" (N = {num_seeds} seed)."
            if len(stability) > 1:
                lowest_std = float(stability[0]["std"])
                ties = [
                    row
                    for row in stability
                    if abs(float(row["std"]) - lowest_std) <= 1e-9
                ]
                if len(ties) > 1:
                    names = ", ".join(row["label"] for row in ties)
                    text += f" {names} có cùng std thấp nhất."
                else:
                    text += f" {stability[0]['label']} ổn định hơn."
            result.append(text)

    problems = []
    for row in rows:
        runs = row.get("runs") or []
        if not runs:
            problems.append(f"{row['label']} không có lượt chạy nào.")
            continue
        count = len(runs)
        timeouts = sum(1 for run in runs if run.get("status") == "timeout")
        ooms = sum(1 for run in runs if run.get("status") == "out_of_memory")
        errors = sum(1 for run in runs if run.get("status") == "error")
        feasible_count = sum(1 for run in runs if run.get("feasible"))
        if timeouts:
            problems.append(f"{row['label']} timeout ở {timeouts}/{count} lượt.")
        if ooms:
            problems.append(
                f"{row['label']} trả out_of_memory ở {ooms}/{count} lượt; "
                "kết quả chỉ là nghiệm tốt nhất có kiểm soát bộ nhớ."
            )
        if errors:
            problems.append(f"{row['label']} lỗi ở {errors}/{count} lượt.")
        if feasible_count < count:
            problems.append(
                f"{row['label']} chỉ có {feasible_count}/{count} lượt khả thi."
            )
    if problems:
        result.extend(problems)

    seeds_text = ", ".join(str(seed) for seed in seeds) if seeds else "-"
    result.append(
        f"Bối cảnh: {problem_name}, N = {num_seeds} seed ({seeds_text}), "
        f"time limit {fmt_compact(time_limit)} giây."
    )
    return result
