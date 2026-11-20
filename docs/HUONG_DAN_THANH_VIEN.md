# Hướng dẫn thành viên triển khai thuật toán MKP

Tài liệu này dành cho **TV1 (Greedy)** và **TV2 (Dynamic Programming)**, hoặc bất kỳ
ai muốn hiểu cách một thuật toán được cài đặt, kiểm thử và benchmark trong dự án.

Mục tiêu: sau khi đọc và làm theo, bạn tự triển khai được file thuật toán của mình,
viết test, chạy benchmark — mà không cần sửa core hay file của người khác.

---

## 0. Bạn cần biết trước

Đọc nhanh 3 phần trong `README.md`:

- Mục 4: dữ liệu, `MKPProblem`, `build_result`.
- Mục 5: hợp đồng `solve()` — **bắt buộc**.
- Docstring đầu file stub của bạn: `src/algorithms/greedy.py` hoặc
  `src/algorithms/dynamic_programming.py`.

Quy tắc bất di bất dịch:

- Chỉ sửa **đúng file của bạn** và file test tương ứng.
- Không sửa `src/core/`, không sửa file thuật toán của người khác.
- Không đổi chữ ký `solve(problem, *, time_limit, seed)`.
- Luôn trả kết quả qua `build_result(...)`.
- Hết giờ thì trả `STATUS_TIMEOUT`, **không raise**.

---

## 1. Chuẩn bị môi trường (10 phút)

```powershell
pip install -r requirements.txt
python -m pytest tests/
# Ky vong: 43 passed
```

Chạy thử 2 thuật toán đã có để thấy output chuẩn:

```powershell
python run_sa.py mknap1 1 -t 1
python run_ga.py mknap1 1 -t 5
```

Xem nhanh một bài dữ liệu:

```powershell
python -c "from src.core.data_loader import get_problem; p=get_problem('mknap1.txt',1); print(p.name, p.n, p.m, p.z_ref); print(p.weights.shape, p.capacities)"
```

---

## 2. Hiểu dữ liệu và kết quả (20 phút)

`MKPProblem` (trong `src/core/model.py`):

| Thuộc tính | Ý nghĩa |
|---|---|
| `n` | số mặt hàng |
| `m` | số ràng buộc tài nguyên |
| `profits` | mảng `(n,)`, lợi nhuận `p[j]` |
| `weights` | ma trận `(m, n)`, `weights[i][j]` là tài nguyên `i` mà hàng `j` dùng |
| `capacities` | mảng `(m,)`, giới hạn `b[i]` |
| `z_ref` | giá trị tối ưu tham chiếu (có thể `None`) |

Nghiệm là vector `x` gồm 0/1, dài `n`:

```python
usage = problem.weights @ x          # tài nguyên đã dùng, shape (m,)
profit = problem.profits @ x         # tổng lợi nhuận
feasible = all(usage <= problem.capacities)
```

**Không tự tính** profit/gap/feasible khi trả kết quả — dùng:

```python
from src.core.evaluator import build_result
result = build_result(problem, x, runtime=..., history=..., status=...)
```

`build_result` tự tính `total_profit`, `resource_usage`, `feasible`,
`optimality_gap = (z_ref - profit) / z_ref` (hoặc `None` nếu không có `z_ref`).

---

## 3. Quy trình code một thuật toán

### 3.1. Khung bắt buộc

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
    deadline = start + max(0.0, time_limit)

    x = np.zeros(problem.n, dtype=np.int8)
    history = []

    # ... thuat toan ...

    return build_result(
        problem,
        x,
        runtime=time.perf_counter() - start,
        history=history,
        status=STATUS_OK,  # hoac STATUS_TIMEOUT neu het gio
    )
```

Checklist khi code:

- [ ] Kiểm tra `time.perf_counter() >= deadline` ở chỗ có thể chạy lâu.
- [ ] `time_limit=0` phải trả nghiệm rỗng, `STATUS_TIMEOUT`, không raise.
- [ ] Nếu thuật toán ngẫu nhiên: `rng = np.random.default_rng(seed)`.
- [ ] `history` (nếu có): mỗi phần tử `{"iteration": int, "profit": float}`.
- [ ] Không đọc file trong `solve`.

---

### 3.2. Greedy (TV1) — các bước gợi ý

Bài toán nhiều ràng buộc nên **không** dùng `profit / weight` của một ràng buộc.
Điểm ưu tiên hợp lý:

```text
score[j] = profits[j] / sum_i( weights[i][j] / capacities[i] )
```

Tức là lợi nhuận trên tổng tài nguyên đã chuẩn hóa theo từng ràng buộc.

Các bước:

1. Tính `score` cho mọi mặt hàng.
2. Sắp xếp giảm dần theo `score`.
3. Duyệt từng mặt hàng `j`:
   - nếu `weights[:, j] <= capacities - usage` thì chọn `x[j] = 1`,
     cộng `usage += weights[:, j]`;
   - nếu không đủ tài nguyên thì bỏ qua.
4. Ghi `history` sau mỗi lần chọn (tùy chọn): `{"iteration": k, "profit": current}`.
5. Kiểm tra deadline trong vòng lặp; hết giờ → `STATUS_TIMEOUT`.
6. Trả `build_result(...)`.

Gợi ý kiểm tra bằng tay:

- Bài 1 ràng buộc: Greedy theo `profit/weight` thường đạt gap 0–5%.
- Bài nhiều ràng buộc: thử so sánh với GA/SA để thấy chênh lệch.

Câu hỏi tự kiểm: nếu hai mặt hàng cùng `score` thì chọn cách nào? Ghi lại lựa chọn
trong code/docstring để người đọc hiểu.

---

### 3.3. Dynamic Programming (TV2) — các bước gợi ý

DP chính xác cho MKP có trạng thái là **vector tài nguyên còn lại**:

```text
state = (c1, c2, ..., cm)   # tai nguyen con lai
value = loi nhuan lon nhat dat duoc voi state do
```

Với `m = 1`, dùng mảng 1 chiều `dp[c]` kích thước `b[0] + 1` — cổ điển, dễ nhất.

Với `m > 1`, số trạng thái là `prod(b[i] + 1)`, thường **quá lớn** với OR-Library.
Cách khả thi hơn: DP thưa (sparse) bằng dict + loại trạng thái bị chi phối:

```text
states = { (0, 0, ..., 0): (profit=0, chosen=0) }   # key: tai nguyen da dung
for j in items:
    new_states = copy(states)                       # bo qua hang j
    for used, (profit, chosen) in states:
        if used + weights[:, j] <= capacities:
            new_used = used + weights[:, j]
            new_profit = profit + profits[j]
            new_chosen = chosen | (1 << j)
            # chi giu neu khong bi trang thai khac chi phoi
            ...
    states = prune_dominated(new_states)
    if time.perf_counter() >= deadline:
        return build_result(..., status=STATUS_TIMEOUT)
```

Nguyên tắc loại trạng thái bị chi phối: trạng thái A chi phối B nếu
`used_A <= used_B` theo mọi ràng buộc **và** `profit_A >= profit_B`.
Giữ lại biên Pareto (Pareto frontier).

Lưu ý quan trọng:

- `chosen` có thể dùng bitmask Python int (`1 << j`) vì `n <= 500`.
- Kiểm tra deadline **trong** vòng lặp, không chỉ sau mỗi mặt hàng.
- Bắt `MemoryError` → `STATUS_OUT_OF_MEMORY` (không raise).
- Nếu hết thời gian: trả nghiệm tốt nhất đã tìm được, `STATUS_TIMEOUT`.
- DP lớn có thể không đạt nghiệm tốt bằng GA/SA trên bộ dữ liệu lớn — điều đó
  bình thường, miễn là đúng hợp đồng và giải thích được trong báo cáo.

---

## 4. Viết test riêng (30 phút)

Tạo/nuôi file `tests/test_greedy.py` hoặc `tests/test_dp.py`. Mẫu:

```python
import numpy as np
import pytest

from src.core.config import STATUS_OK, STATUS_TIMEOUT
from src.core.data_loader import get_problem
from src.core.validator import is_feasible
from src.algorithms import greedy  # doi thanh dynamic_programming neu DP


def selected_mask(problem, result):
    x = np.zeros(problem.n, dtype=int)
    x[result.selected_items] = 1
    return x


def test_greedy_nghiem_hop_le():
    p = get_problem("mknap1.txt", 1)
    r = greedy.solve(p, time_limit=5, seed=0)

    assert r.feasible is True
    assert is_feasible(p, selected_mask(p, r))
    assert r.total_profit > 0
    assert r.total_profit <= p.z_ref * 1.01
    assert len(r.resource_usage) == p.m


def test_greedy_gap_dung_cong_thuc():
    p = get_problem("mknap1.txt", 1)
    r = greedy.solve(p, time_limit=5, seed=0)

    expected = (p.z_ref - r.total_profit) / p.z_ref
    assert r.optimality_gap == pytest.approx(expected)


def test_greedy_het_gio_khong_raise():
    p = get_problem("mknap1.txt", 1)
    r = greedy.solve(p, time_limit=0, seed=0)

    assert r.status == STATUS_TIMEOUT
    assert r.feasible is True
    assert r.total_profit == 0.0
```

Chạy:

```powershell
python -m pytest tests/test_greedy.py -v
python -m pytest tests/ -q
```

Với DP, thêm test cho trường hợp bộ nhớ/thời gian nếu code của bạn có nhánh đó.

---

## 5. Chạy và benchmark

Chạy nhanh 1 bài:

```powershell
python run_algo.py greedy mknap1 1 -t 5 -s 1
python run_algo.py dp mknap1 1 -t 5 -s 1
```

Benchmark 1 seed để kiểm tra (16 bài × 5s ≈ 80 giây):

```powershell
python benchmark_algo.py greedy -t 5 --seeds 1
python benchmark_algo.py dp -t 5 --seeds 1
```

Kết quả vào `results/greedy/`, `results/dp/`:

- `*_runs.csv/json`: từng lượt (JSON có `history`).
- `*_summary.csv/json`: tổng hợp theo bài.
- `*_meta.json`: cấu hình lần chạy.
- `progress.log`: tiến độ.

**Chưa chạy full 60s × 10 seed** — để cuối, khi đủ 4 thuật toán, chạy một lần
cho công bằng.

---

## 6. Commit và push

Chỉ commit file của bạn + test:

```powershell
python -m pytest tests/ -q
git add src/algorithms/greedy.py tests/test_greedy.py
git commit -m "greedy: hoan thanh solve + test"
git push origin feature
```

Quy ước:

- Không commit `results/`, `__pycache__/`, file tạm.
- Commit message ngắn, có tên thuật toán.
- Trước khi push: toàn bộ test phải xanh.

---

## 7. Definition of Done

Một thuật toán được coi là xong khi:

- [ ] `solve()` giữ đúng chữ ký, dùng `build_result`.
- [ ] Trả nghiệm 0/1 hợp lệ, `feasible=True` trên ít nhất các bài nhỏ.
- [ ] `time_limit=0` trả `STATUS_TIMEOUT`, không raise.
- [ ] Không đọc file dữ liệu trong `solve`.
- [ ] Có test riêng, tất cả test pass.
- [ ] Chạy được `run_algo.py` và benchmark 1 seed.
- [ ] Không sửa core/file người khác.
- [ ] Commit đúng file, message rõ ràng.

---

## 8. Lỗi thường gặp

| Lỗi | Cách tránh |
|---|---|
| Quên `best_x = x.copy()` | Lưu bản sao mỗi khi tìm được nghiệm tốt hơn |
| So sánh tài nguyên bằng `<=` với số thực | Dùng dung sai `+ 1e-9` |
| Trả `selected_items` thay vì vector `x` | `build_result` cần vector 0/1 dài `n` |
| Raise khi hết giờ | Trả `STATUS_TIMEOUT` |
| Đọc file trong `solve` | Nhận `problem` đã load sẵn |
| Sửa `src/core/` | Báo nhóm nếu nghi core có bug |
| Chạy full benchmark quá sớm | Chỉ chạy 1 seed × 5s để kiểm tra |

---

## 9. Lộ trình 2 buổi

**Buổi 1 — Greedy (TV1)**
1. Đọc README mục 4–5 + docstring stub.
2. Chạy SA/GA để xem output.
3. Code Greedy theo mục 3.2.
4. Viết test theo mục 4.
5. Chạy `run_algo.py greedy` + benchmark 1 seed.

**Buổi 2 — DP (TV2)**
1. Làm DP cho `m = 1` trước (mảng 1 chiều).
2. Mở rộng sang `m > 1` bằng dict + Pareto pruning.
3. Thêm kiểm tra deadline và `MemoryError`.
4. Viết test, chạy benchmark 1 seed.
5. Ghi lại nhận xét: DP dừng vì thời gian/bộ nhớ ở bài nào, gap bao nhiêu.

---

## 10. Câu hỏi tự kiểm tra

1. `optimality_gap` được tính ở đâu, khi nào là `None`?
2. Vì sao phải giữ `x` là vector 0/1 thay vì danh sách chỉ số?
3. Khi `time_limit=0`, thuật toán của bạn trả gì?
4. Vì sao Greedy/DP không bắt buộc dùng `seed`, nhưng vẫn phải giữ tham số?
5. Vì sao không nên chạy full 60s × 10 seed trước khi đủ 4 thuật toán?

Nếu trả lời được 5 câu trên và checklist mục 7 đều tick, bạn đã sẵn sàng.
