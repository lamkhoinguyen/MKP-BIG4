from pathlib import Path
"Hang so chung cho bai toan"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "mknap"
RESULTS_DIR = PROJECT_ROOT / "results"

# File chua gia tri tham chieu Z_ref
REFERENCE_FILE = "mkcbres.txt"
TIME_LIMIT_SECONDS = 60
SEED = tuple(range(1, 11))

STATUS_OK = "ok"
STATUS_TIMEOUT = "timeout"
STATUS_OUT_OF_MEMORY = "out_of_memory"

# Chay 16 bai thuc nghiem trong file .txt
BENCHMARK_PROBLEMS = (
    tuple(("mknap1.txt", k) for k in range(1, 8)) + tuple(
        (file_name, k)
        for file_name in ("mknapcb1.txt", "mknapcb3.txt", "mknapcb4.txt")
        for k in (1, 11, 21)
    )
)