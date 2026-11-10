# MKP-BIG4 — Bài toán chọn hàng vận chuyển (Multidimensional Knapsack Problem)

Đồ án nhóm: xây dựng chương trình giải bài toán MKP bằng **4 thuật toán** (Greedy, Dynamic Programming, Genetic Algorithm, Simulated Annealing), sau đó **đo và so sánh** chất lượng lời giải, thời gian chạy trên cùng một bộ dữ liệu OR-Library.

- Ngôn ngữ: **Python 3** (ưu tiên viết từ scratch)
- Giao diện: **PySide6** (phần sau)
- Dữ liệu: OR-Library — 11 file, đã có sẵn trong repo
- Spec đầy đủ: [`BIG4_spec_clean.txt`](BIG4_spec_clean.txt)

---

## 1. Trạng thái hiện tại

| Hạng mục | Trạng thái | File |
|----------|------------|------|
| Đọc dữ liệu OR-Library (11 file, 325 bài) | ✅ Xong | `src/core/data_loader.py` |
| Mô hình bài toán `MKPProblem` / `MKPResult` | ✅ Xong | `src/core/model.py` |
| Tính lợi nhuận, tài nguyên, kết quả | ✅ Xong | `src/core/evaluator.py` |
| Kiểm tra nghiệm hợp lệ | ✅ Xong | `src/core/validator.py` |
| Hằng số chung (benchmark, seed, status) | ✅ Xong | `src/core/config.py` |
| Quy ước interface 4 thuật toán | ✅ Xong | `src/algorithms/__init__.py` |
| Test tự kiểm (31 test) | ✅ Xong — `31 passed` | `tests/` |
| **4 thuật toán** | ❌ **Chưa code — đợi 4 thành viên** | `src/algorithms/*.py` |
| Chạy benchmark / so sánh | ❌ Chưa code | `src/experiments/` |
| Giao diện PySide6 | ❌ Chưa code | `src/gui/` |
| Điểm vào chương trình | ❌ Chưa code | `main.py` |

**Tóm lại:** phần nền (core + quy ước + test) đã chắc. Việc còn lại là **code 4 thuật toán** (mỗi người 1 file), rồi mới đến experiments và GUI.

---

## 2. Cài đặt & kiểm tra

```bash
# 1. Clone repo
git clone <url-repo>
cd MKP-BIG4

# 2. Cài dependency
pip install -r requirements.txt

# 3. Chạy test — BẮT BUỘC thấy "31 passed" trước khi code gì
python -m pytest tests/
```

Nếu test đỏ → môi trường hoặc code core đang hỏng, báo lại nhóm trước khi bắt đầu.

---

## 3. Cấu trúc chương trình

```
MKP-BIG4/
├── README.md                  ← bạn đang đọc
├── docs/HANDOFF.md            ← trạng thái hiện tại (ghi đè mỗi lần cập nhật)
├── docs/LOG.md                ← lịch sử làm việc (append, không xóa cũ)
├── BIG4_spec_clean.txt        ← spec đồ án (đọc 1 lần)
├── main.py                    ← điểm vào (chưa code)
├── requirements.txt           ← PySide6, matplotlib, pytest
├── pytest.ini                 ← cấu hình test
│
├── data/mknap/                ← DỮ LIỆU (không sửa)
│   ├── mknap1.txt             7 bài nhỏ (n=6..10) — có Z_ref trong file
│   ├── mknap2.txt             48 bài văn học (SENTO, WEING, …)
│   ├── mknapcb1..cb9.txt      270 bài Chu & Beasley (mỗi file 30 bài)
│   └── mkcbres.txt            Z_ref (giá trị tối ưu tham chiếu) cho mknapcb
│
├── src/
│   ├── core/                  ✅ ĐÃ XONG — dùng thoải mái, không sửa
│   │   ├── config.py          hằng số: BENCHMARK, TIME_LIMIT, SEED, STATUS
│   │   ├── model.py           MKPProblem, MKPResult
│   │   ├── data_loader.py     load_problems(), get_problem()
│   │   ├── evaluator.py       build_result(), compute_profit(), …
│   │   └── validator.py       is_feasible(), find_violations()
│   │
│   ├── algorithms/            ❌ MỖI THANH VIÊN 1 FILE — xem mục 5
│   │   ├── __init__.py        contract chung + get_solver()
│   │   ├── greedy.py                    ← Thành viên 1
│   │   ├── dynamic_programming.py       ← Thành viên 2
│   │   ├── genetic_algorithm.py         ← Thành viên 3
│   │   └── simulated_annealing.py       ← Thành viên 4
│   │
│   ├── experiments/           ❌ Chưa code — chạy benchmark, so sánh 4 thuật toán
│   └── gui/                   ❌ Chưa code — PySide6
│
├── tests/                     ✅ Test core + contract (chạy trước & sau khi code)
│   ├── test_core.py           kiểm tra model/evaluator/validator/data_loader
│   └── test_contract.py       bắt đúng chữ ký solve() của 4 thuật toán
│
└── results/                   ← nơi lưu biểu đồ, báo cáo (tự sinh)
```

---

## 4. Thông tin đã có sẵn — dùng như thế nào

### 4.1. Đọc một bài toán

```python
from src.core.data_loader import get_problem

problem = get_problem("mknap1.txt", 1)   # file, số thứ tự bài (tính từ 1)
# problem.name       → "mknap1_01"
# problem.n          → số mặt hàng
# problem.m          → số ràng buộc (tài nguyên)
# problem.profits    → np.array shape (n,)       lợi nhuận p[j]
# problem.weights    → np.array shape (m, n)     lượng tài nguyên tiêu thụ
# problem.capacities → np.array shape (m,)       giới hạn b[i]
# problem.z_ref      → giá trị tối ưu tham chiếu (để tính gap), có thể None
```

Các file benchmark đang dùng (trong `config.BENCHMARK_PROBLEMS`):

- `mknap1.txt` bài 1–7
- `mknapcb1.txt`, `mknapcb3.txt`, `mknapcb4.txt` bài 1, 11, 21

Tổng **16 bài** để so sánh 4 thuật toán.

### 4.2. Trả kết quả — bắt buộc dùng `build_result`

```python
import numpy as np
from src.core.evaluator import build_result
from src.core.config import STATUS_OK, STATUS_TIMEOUT

x = np.zeros(problem.n, dtype=int)   # vector 0/1, x[j]=1 → chọn mặt hàng j
x[0] = 1; x[3] = 1                   # ví dụ chọn 2 mặt hàng

result = build_result(
    problem, x,
    runtime=0.42,                    # giây
    history=[{"iteration": 1, "profit": 1200}],  # tùy chọn, để vẽ đồ thị
    status=STATUS_OK,                # hoặc STATUS_TIMEOUT nếu hết giờ
)
# result.total_profit, result.feasible, result.optimality_gap, result.selected_items, …
```

`build_result` **tự tính** lợi nhuận, tổng tài nguyên, có hợp lệ không, và `optimality_gap = (z_ref − profit) / z_ref`. Bạn **không** tự tính các thứ này.

### 4.3. Hằng số chung (`src/core/config.py`)

| Hằng | Ý nghĩa |
|------|----------|
| `TIME_LIMIT_SECONDS = 60` | giới hạn thời gian mỗi lượt chạy (giây) |
| `SEED` | danh sách seed cho các lần chạy lặp (GA/SA dùng để tái lập kết quả) |
| `BENCHMARK_PROBLEMS` | 16 bài benchmark `(tên_file, số_bài)` |
| `STATUS_OK / STATUS_TIMEOUT / STATUS_OUT_OF_MEMORY` | giá trị cho `result.status` |

### 4.4. Kiểm tra nghiệm

```python
from src.core.validator import is_feasible, find_violations

is_feasible(problem, x)        # True nếu x nhị phân và không vượt capacity
find_violations(problem, x)    # danh sách ràng buộc đang bị vi phạm
```

---

## 5. HỢP ĐỒNG ALGORITHM — bắt buộc cho 4 thành viên

### 5.1. Ai làm file nào

| Thành viên | File cần sửa | Thuật toán |
|------------|--------------|------------|
| **1** | `src/algorithms/greedy.py` | Greedy (tham lam) |
| **2** | `src/algorithms/dynamic_programming.py` | Quy hoạch động |
| **3** | `src/algorithms/genetic_algorithm.py` | Di truyền |
| **4** | `src/algorithms/simulated_annealing.py` | Mô phỏng luyện kim |

> **Chỉ sửa đúng 1 file của mình.** Không sửa `src/core/`, không sửa file của người khác, không đổi tên file.

### 5.2. Chữ ký — KHÔNG ĐƯỢC ĐỔI

Mỗi file đã có sẵn hàm mẫu. Bạn chỉ điền phần thân hàm:

```python
def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    # ... code thuật toán của bạn ...
    return build_result(problem, x, runtime=..., history=..., status=...)
```

| Yêu cầu | Chi tiết |
|---------|----------|
| Tên hàm | `solve` — cố định |
| Tham số | `problem` (vị trí); `time_limit`, `seed` (chỉ nhận keyword: `solve(p, time_limit=5, seed=1)`) |
| Trả về | `MKPResult`, **luôn** qua `build_result(...)` |
| Nghiệm | vector numpy 0/1 độ dài `problem.n` |
| Hết giờ | dừng sớm, trả `status=STATUS_TIMEOUT` — **không raise** |
| Không đọc file | `solve` nhận `problem` đã load sẵn; không mở file data |
| Random | GA/SA **bắt buộc** dùng `seed` (`np.random.default_rng(seed)`) để chạy lại được |
| History | tùy chọn: `list[dict]` dạng `{"iteration": int, "profit": float}` để vẽ đồ thị |

**Sai bất kỳ mục nào → `tests/test_contract.py` đỏ.** Đây là cơ chế chống “mỗi người một kiểu”.

### 5.3. Ví dụ khung hoàn chỉnh (Greedy)

```python
import time
import numpy as np

from src.algorithms import TIME_LIMIT_SECONDS
from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.evaluator import build_result
from src.core.model import MKPProblem, MKPResult


def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult:
    start = time.perf_counter()
    x = np.zeros(problem.n, dtype=int)
    history = []

    # --- thuật toán của bạn ---
    # while True:
    #     if time.perf_counter() - start > time_limit:
    #         return build_result(problem, x, runtime=..., history=history,
    #                            status=STATUS_TIMEOUT)
    #     ... chon mat hang tiep theo ...
    #     history.append({"iteration": k, "profit": current_profit})
    # -------------------------

    runtime = time.perf_counter() - start
    return build_result(problem, x, runtime=runtime, history=history, status=STATUS_OK)
```

Mỗi file stub còn có **gợi ý riêng** trong docstring đầu file (ví dụ Greedy: điểm ưu tiên trên nhiều ràng buộc; DP: cảnh báo bộ nhớ; GA: crossover/mutation; SA: nhiệt độ) — mở file ra đọc trước khi bắt tay vào code.

### 5.4. Quy trình làm việc của từng thành viên

```bash
# 0. Clone + cài + test (1 lần)
pip install -r requirements.txt
python -m pytest tests/          # phải "31 passed"

# 1. Code trong file của mình
#    src/algorithms/greedy.py    (ví dụ thành viên 1)

# 2. Test lại — cả core lẫn contract
python -m pytest tests/

# 3. (Khuyến nghị) test nhanh trên 1 bài nhỏ
python -c "
from src.core.data_loader import get_problem
from src.algorithms import get_solver
p = get_problem('mknap1.txt', 1)
r = get_solver('greedy')(p, time_limit=5, seed=0)
print('profit', r.total_profit, 'z_ref', p.z_ref, 'gap', r.optimality_gap, 'feasible', r.feasible)
"

# 4. Commit chỉ file của mình
git add src/algorithms/greedy.py
git commit -m "greedy: hoan thanh solve"
git push
```

### 5.5. Mẫu test riêng (khuyến nghị)

Tạo `tests/test_greedy.py` (hoặc `test_dp.py`, `test_ga.py`, `test_sa.py` — tên file đã có sẵn, đang rỗng):

```python
import numpy as np
from src.core.data_loader import get_problem
from src.algorithms import get_solver


def test_greedy_mknap1():
    p = get_problem("mknap1.txt", 1)
    r = get_solver("greedy")(p, time_limit=5, seed=0)
    assert r.feasible
    assert r.total_profit > 0
    assert r.total_profit <= p.z_ref * 1.01   # không vượt quá z_ref (hoặc cho phép slightly better)
```

---

## 6. Sau khi có đủ 4 thuật toán (phần chung — ai nhận làm experiments)

1. **`src/experiments/`** — duyệt `BENCHMARK_PROBLEMS`, gọi `get_solver(tên)(problem, …)`, lưu `results/`
2. **`main.py`** — điểm vào chạy CLI/GUI
3. **`src/gui/`** — PySide6: trang chọn dataset, chạy thuật toán, vẽ biểu đồ so sánh

Những phần này **không** thuộc phạm vi 4 thành viên algorithm, chỉ bắt đầu khi 4 file `solve()` đã xong và `pytest` xanh toàn bộ.

---

## 7. Quy ước Git

- Branch feature nếu muốn: `feature/greedy`, `feature/dp`, … rồi PR về `main`
- Commit message ngắn, có tên thuật toán: `greedy: them vong chon`, `dp: trang thai 2D`
- **Không** commit file data, `__pycache__`, kết quả chạy tạm
- Trước khi push: `python -m pytest tests/` phải xanh

---

## 8. Câu hỏi thường gặp

**Q: Tôi được sửa `src/core/` không?**  
A: Không. Core đã test xong. Nếu nghĩ core có bug → báo lại nhóm, không tự sửa song song.

**Q: `solve` được raise Exception không?**  
A: Chỉ raise khi input sai (ví dụ shape `x` sai). Lỗi hết giờ / không tìm được nghiệm → vẫn trả `MKPResult` với `status` phù hợp.

**Q: `seed` dùng cho Greedy/DP?**  
A: Greedy/DP thường xác định — có thể bỏ qua `seed`, nhưng vẫn giữ tham số trong chữ ký cho đồng bộ.

**Q: Kết quả chạy lại có giống nhau không?**  
A: GA/SA với cùng `seed` + cùng `time_limit` phải cho kết quả giống nhau.

---

## 9. Test hiện có

```bash
python -m pytest tests/          # toàn bộ
python -m pytest tests/test_contract.py -v   # chỉ check chữ ký 4 thuật toán
python -m pytest tests/test_core.py -v       # chỉ check core
```

- `tests/test_core.py` — 18 test: model, evaluator, validator, data_loader, benchmark có `z_ref`
- `tests/test_contract.py` — 13 test: 4 file algorithm có `solve()` đúng chữ ký

Sau khi bạn code xong, số test sẽ tăng thêm (test riêng của từng người).
