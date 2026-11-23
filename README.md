# MKP-BIG4 — Bài toán chọn hàng vận chuyển đa chiều

Đồ án nhóm giải bài toán **Multidimensional Knapsack Problem (MKP)** bằng **4 thuật toán**
(Greedy, Dynamic Programming, Genetic Algorithm, Simulated Annealing), chạy trên cùng bộ dữ
liệu chuẩn **OR-Library**, sau đó đo và so sánh chất lượng lời giải, thời gian chạy, độ ổn
định. Dự án gồm **CLI** và **giao diện desktop PySide6** để chạy thực nghiệm và trực quan hóa.

- Ngôn ngữ: **Python 3.10+**, thư viện **NumPy**
- Giao diện: **PySide6** + **Matplotlib**
- Dữ liệu: **OR-Library** — 11 file, 325 bài (đã có sẵn trong repo)
- Kiểm thử: **pytest** — **134 passed**

---

## 1. Thông tin dự án

### 1.1. Bài toán

Cho `n` mặt hàng và `m` loại tài nguyên (ràng buộc). Mỗi mặt hàng `j` có:

- lợi nhuận `p_j`,
- lượng tài nguyên `r_ij` tiêu thụ cho ràng buộc `i`,
- giới hạn tài nguyên `b_i`.

Cần chọn tập mặt hàng (biến nhị phân `x_j ∈ {0,1}`) sao cho **tổng lợi nhuận lớn nhất**
mà **không vượt bất kỳ ràng buộc tài nguyên nào**:

```
maximize   Σ p_j · x_j
subject to Σ r_ij · x_j ≤ b_i     (i = 1..m)
           x_j ∈ {0, 1}
```

### 1.2. Mục tiêu

- Cài đặt 4 thuật toán theo **một hợp đồng (contract) chung** để so sánh công bằng.
- Chạy thực nghiệm trên bộ dữ liệu OR-Library, tính **optimality gap** so với `z_ref`.
- So sánh 4 thuật toán theo: chất lượng (profit/gap), hiệu năng (runtime/status) và độ ổn
  định (chỉ GA/SA khi chạy nhiều seed).
- Cung cấp CLI và GUI để tái lập kết quả, xuất báo cáo (CSV/JSON/PNG/HTML).

### 1.3. Kết quả đạt được

| Hạng mục | Trạng thái |
|----------|------------|
| Đọc dữ liệu OR-Library (11 file, 325 bài) | ✅ `src/core/data_loader.py` |
| Mô hình bài toán + kết quả | ✅ `src/core/model.py` |
| Đánh giá lợi nhuận / gap / hợp lệ | ✅ `src/core/evaluator.py`, `validator.py` |
| 4 thuật toán theo contract chung | ✅ `src/algorithms/*.py` |
| Benchmark / so sánh / xuất báo cáo | ✅ `src/experiments/` |
| Giao diện PySide6 (4 trang, session) | ✅ `src/gui/` |
| Test tự kiểm | ✅ **134 passed** |

Benchmark 325 bài (time limit 60s, seed 1), gap trung bình so với `z_ref`:

| Thuật toán | Gap trung bình | Ghi chú |
|------------|----------------|---------|
| Greedy | ~1.05% | Tất định, luôn khả thi, rất nhanh |
| Dynamic Programming | ~1.54% | Chính xác nhưng OOM trên 274/325 bài lớn |
| Genetic Algorithm | ~0.42% | Chất lượng tốt nhất, chạy nhiều seed |
| Simulated Annealing | ~1.11% | Cân bằng, mạnh về thoát cực trị địa phương |

---

## 2. Thông tin dữ liệu (Dataset)

### 2.1. Nguồn

Bộ dữ liệu **OR-Library** (Chu & Beasley), nằm trong `data/mknap/`. Gồm 11 file bài toán
(tổng **325 bài**) và 1 file giá trị tham chiếu `z_ref`.

| File | Số bài | Mô tả |
|------|--------|-------|
| `mknap1.txt` | 7 | Bài nhỏ (`n = 6..10`), có `z_ref` ghi ngay trong file |
| `mknap2.txt` | 48 | Bộ dữ liệu văn học (SENTO, WEING, …) |
| `mknapcb1..cb9.txt` | 270 | Bộ Chu & Beasley, mỗi file 30 bài |
| `mkcbres.txt` | — | Bảng `z_ref` (Best Feasible) cho `mknapcb*` |

Tổng: `7 + 48 + 270 = 325` bài.

### 2.2. Cấu trúc một bài toán

Sau khi nạp, mỗi bài là một `MKPProblem` với:

| Trường | Ý nghĩa | Kiểu |
|--------|---------|------|
| `name` | Tên bài (`mknap1_01`, `SENTO1`, …) | `str` |
| `n` | Số mặt hàng | `int` |
| `m` | Số ràng buộc tài nguyên | `int` |
| `profits` | Lợi nhuận `p_j` | `np.ndarray (n,)` |
| `weights` | Ma trận tài nguyên `r_ij` | `np.ndarray (m, n)` |
| `capacities` | Giới hạn tài nguyên `b_i` | `np.ndarray (m,)` |
| `z_ref` | Giá trị tối ưu tham chiếu (có thể `None`) | `float \| None` |

### 2.3. Định dạng hỗ trợ

- **`mknap1` / `mknapcb*`** (OR-Library chuẩn): `K` rồi lặp `K` block
  `(n m opt) + profits + weights(m×n) + capacities(m)`.
- **`mknap2`** (văn học): nhiều block `problem TEN.DAT`, thứ tự `m n`, profits, caps,
  weights, opt; có comment `//` và dấu `+`.
- `z_ref`: lấy từ trường `opt` nếu `> 0`; nếu file ghi `0` thì tra bảng `mkcbres.txt`.

### 2.4. Đọc dữ liệu

```python
from src.core.data_loader import get_problem

problem = get_problem("mknap1.txt", 1)   # (tên file, số thứ tự bài tính từ 1)
print(problem.name, problem.n, problem.m, problem.z_ref)
```

### 2.5. Optimality gap

`z_ref` là giá trị tối ưu (hoặc tốt nhất đã biết). Gap đo mức kém tối ưu:

```
gap = (z_ref - profit) / z_ref
```

- `gap = 0` → đạt đúng `z_ref`.
- Bài không có `z_ref` → gap để trống (`None`, hiển thị `-`).

### 2.6. Bộ 16 bài benchmark

`config.BENCHMARK_PROBLEMS` chọn 16 bài để so sánh 4 thuật toán:

- `mknap1.txt` — bài 1..7
- `mknapcb1.txt`, `mknapcb3.txt`, `mknapcb4.txt` — bài 1, 11, 21

---

## 3. Bốn thuật toán

Tất cả cài đặt theo cùng một contract (xem mục 4.4), nên dễ so sánh trực tiếp.

| Thuật toán | Loại | Tất định? | Dùng `seed`? | Điểm mạnh chính |
|------------|------|-----------|--------------|-----------------|
| Greedy | Tham lam thích nghi | Có | Không | Rất nhanh, luôn khả thi |
| Dynamic Programming | Quy hoạch động + cắt nhánh | Có | Không | Tối ưu khi bộ nhớ cho phép |
| Genetic Algorithm | Tiến hóa + greedy repair | Không | Có | Chất lượng lời giải cao nhất |
| Simulated Annealing | Luyện kim mô phỏng | Không | Có | Thoát cực trị địa phương tốt |

### 3.1. Greedy (`src/algorithms/greedy.py`)

- **Ý tưởng:** mỗi vòng tính điểm ưu tiên *thích nghi* theo tài nguyên **còn lại**:
  `score_j = p_j / Σ_i ( r_ij / (b_i - used_i) )`, rồi chọn mặt hàng điểm cao nhất còn vừa
  ràng buộc, cập nhật tài nguyên và tính lại điểm. Dừng khi không thêm được mặt hàng nào.
- **Độ phức tạp:** thời gian `O(n²·m)`, bộ nhớ `O(n·m)`.
- **Ưu:** đơn giản, nhanh, luôn trả nghiệm khả thi. **Nhược:** không đảm bảo tối ưu.
- **Tất định** — không phụ thuộc `seed`.

### 3.2. Dynamic Programming (`src/algorithms/dynamic_programming.py`)

- **Ý tưởng:** trạng thái sau khi xét `j` mặt hàng là vector tài nguyên đã dùng
  `R = (r_1..r_m)`, giá trị là lợi nhuận lớn nhất; chuyển trạng thái theo chọn/không chọn
  mặt hàng. Truy vết ngược bằng mảng `parent/took`.
- **Tăng tốc:** nghiệm tham lam + local search làm cận dưới, cắt nhánh theo cận trên
  (fractional bound), loại mặt hàng không bao giờ vừa, gộp trạng thái trùng.
- **Độ phức tạp:** thời gian `O(n·S·(m + log S))`, bộ nhớ `O(S·m)` với `S` là số trạng thái
  không bị chi phối (`S` có thể bùng nổ theo tích các capacity).
- **Giới hạn an toàn:** `DEFAULT_MEMORY_LIMIT_MB = 3000`, `MAX_STATES = 2_000_000`. Vượt
  giới hạn → trả `status = out_of_memory` (kèm nghiệm tốt nhất hiện có), **không** coi là
  lỗi lợi nhuận 0.
- **Tất định** — chính xác khi bộ nhớ/thời gian cho phép.

### 3.3. Genetic Algorithm (`src/algorithms/genetic_algorithm.py`)

- **Ý tưởng:** GA nhị phân (cá thể là vector 0/1) + **greedy repair** đảm bảo khả thi.
  Chọn lọc tournament, lai ghép, đột biến, giữ elite qua các thế hệ.
- **Tham số chính:** `POPULATION_SIZE = 100`, `MAX_GENERATIONS = 500`,
  `CROSSOVER_RATE = 0.85`, `ELITE_COUNT = 2`, `TOURNAMENT_SIZE = 3`.
- **Ngẫu nhiên:** dùng `np.random.default_rng(seed)` → cùng seed + cùng time limit cho kết
  quả tái lập được. Hết giờ → `status = timeout`.

### 3.4. Simulated Annealing (`src/algorithms/simulated_annealing.py`)

- **Ý tưởng:** xuất phát từ nghiệm tham lam khả thi; sinh nghiệm lân cận bằng đảo 1 bit hoặc
  swap 1-0; nhận nghiệm xấu hơn với xác suất `exp(delta / T)`; nhiệt độ giảm theo lịch hình
  học `T ← alpha·T`; restart khi đứng yên quá lâu.
- **Tham số chính:** `MAX_ITERATIONS = 5_000_000`, `COOLING_ITERATIONS = 200_000`,
  `RESTART_AFTER = 20_000`, `T_MIN = 1e-3`.
- **Độ phức tạp:** thời gian `O(MAX_ITERATIONS·m)`, bộ nhớ `O(n + m)`.
- **Ngẫu nhiên:** dùng `seed` để tái lập. Hết giờ → `status = timeout`.

> Greedy/DP tất định nên chỉ chạy 1 lần; GA/SA chạy `N` seed và mới tính được Avg/Worst/Std.

---

## 4. Các tầng của dự án

Dự án tổ chức theo **5 tầng** độc lập, phụ thuộc một chiều từ trên xuống; tầng dưới không
biết tầng trên.

```
MKP-BIG4/
├── data/mknap/           ① TẦNG DỮ LIỆU  — file OR-Library (không sửa)
│
├── src/core/             ② TẦNG LÕI      — mô hình & đánh giá, không phụ thuộc gì phía trên
│   ├── config.py            hằng số: TIME_LIMIT_SECONDS=60, SEED, STATUS_*, BENCHMARK_PROBLEMS
│   ├── model.py             MKPProblem, MKPResult
│   ├── data_loader.py       load_problems(), get_problem(), cache, đọc z_ref
│   ├── evaluator.py         build_result(), compute_profit(), compute_optimality_gap()
│   └── validator.py         is_feasible(), find_violations()
│
├── src/algorithms/       ③ TẦNG THUẬT TOÁN — 4 solver theo cùng contract
│   ├── __init__.py          chữ ký solve(), ALGORITHM_NAMES, get_solver()
│   ├── greedy.py
│   ├── dynamic_programming.py
│   ├── genetic_algorithm.py
│   └── simulated_annealing.py
│
├── src/experiments/      ④ TẦNG THỰC NGHIỆM — chạy hàng loạt & so sánh
│   ├── experiment_runner.py  chạy 1 thuật toán trên dataset, lưu kết quả/session
│   ├── metrics.py            tổng hợp profit/gap/runtime/status
│   └── comparison.py         sinh CSV/PNG/report so sánh 4 thuật toán
│
├── src/gui/              ⑤ TẦNG GIAO DIỆN — PySide6
│   ├── main.py              điểm vào: python -m src.gui.main
│   ├── main_window.py       khung cửa sổ + 4 trang
│   ├── app_state.py         trạng thái chia sẻ giữa các trang
│   ├── analytics.py         thống kê seed, history, nhận xét tự động
│   ├── session_store.py     lưu/đọc/xuất phiên (JSON, CSV, HTML, PNG)
│   ├── pages/               Home, Dataset, Algorithm, Comparison
│   ├── widgets/             sidebar, bảng, biểu đồ, panel kết quả…
│   ├── workers/             chạy thuật toán trong QThread (không treo UI)
│   └── styles/theme.qss     giao diện QSS
│
├── tests/                (kiểm thử) — core, contract, 4 thuật toán, experiments, GUI
├── run_algo.py / run_ga.py / run_sa.py / benchmark_algo.py   CLI tiện dụng ở gốc repo
├── requirements.txt
└── pytest.ini
```

### 4.1. Vai trò từng tầng

| Tầng | Vai trò | Không phụ thuộc vào |
|------|---------|---------------------|
| ① Dữ liệu | Cung cấp file bài toán gốc | — |
| ② Lõi (core) | Nạp dữ liệu, mô hình, tính lợi nhuận/gap/khả thi | algorithms, experiments, gui |
| ③ Thuật toán | Giải bài toán, trả `MKPResult` | experiments, gui |
| ④ Thực nghiệm | Gọi solver hàng loạt, lưu & so sánh kết quả | gui |
| ⑤ Giao diện | Điều khiển, trực quan hóa, xuất báo cáo | — (tầng trên cùng) |

### 4.2. Luồng dữ liệu

```
data_loader ──► MKPProblem ──► solver.solve() ──► MKPResult ──► experiments / GUI
   (①/②)            (②)              (③)              (②)            (④/⑤)
```

### 4.3. Cấu trúc kết quả `MKPResult`

| Trường | Ý nghĩa |
|--------|---------|
| `selected_items` | Danh sách mặt hàng được chọn |
| `total_profit` | Tổng lợi nhuận |
| `resource_usage` | Tài nguyên đã dùng theo từng ràng buộc |
| `feasible` | Nghiệm có hợp lệ không |
| `runtime` | Thời gian chạy (giây) |
| `optimality_gap` | Gap so với `z_ref` (nếu có) |
| `history` | `[{iteration, profit}, …]` để vẽ đường hội tụ |
| `status` | `ok` / `timeout` / `out_of_memory` |
| `peak_memory` | Bộ nhớ đỉnh (MB), hiện chỉ DP báo cáo |

### 4.4. Hợp đồng thuật toán (contract)

Mọi solver có đúng chữ ký sau và **luôn** trả `MKPResult` qua `build_result()`:

```python
def solve(
    problem: MKPProblem,
    *,
    time_limit: float = TIME_LIMIT_SECONDS,
    seed: int = 0,
) -> MKPResult: ...
```

Quy tắc: hết giờ → trả `status=timeout` (không raise); hết bộ nhớ (DP) →
`status=out_of_memory`; nghiệm là vector numpy 0/1 độ dài `problem.n`; `history` phần tử
cuối phải khớp lợi nhuận trả về; không đọc file trong `solve`.

---

## 5. Cài đặt

**Yêu cầu:** Python **3.10+**, pip.

```bash
# 1. Clone repo
git clone <url-repo>
cd MKP-BIG4

# 2. (Khuyến nghị) tạo môi trường ảo
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Cài dependency (PySide6, matplotlib, numpy, pytest)
pip install -r requirements.txt

# 4. Chạy test — phải thấy "134 passed"
python -m pytest tests/
```

Nếu test đỏ → môi trường hoặc code lõi có vấn đề, kiểm tra lại bước cài đặt trước khi demo.

---

## 6. Chạy demo

### 6.1. Giao diện desktop (demo chính)

```bash
python -m src.gui.main
```

Cửa sổ gồm 4 trang (chuyển nhanh bằng `Ctrl+1..4`):

1. **Home** — giới thiệu bài toán và lối tắt đến các trang.
2. **Dataset** — chọn file (vd `mknap1.txt`), chọn bài; xem ma trận `p_j / r_ij / b_i`, hoặc
   chọn *(tất cả bài trong file)* để xem bảng tổng hợp.
3. **Algorithm** — **Run** một thuật toán hoặc **Run All** cả 4; xem bảng kết quả và đường
   hội tụ. Khi Dataset chọn "tất cả", Run All chạy `4 × mọi bài`.
4. **Comparison** — **Run Session** với `N = 1/3/5/10` seed (GA/SA chạy N lần, Greedy/DP 1
   lần); xem bảng so sánh (có cột **Số seed (N)**), biểu đồ và nhận xét tự động. Nút **Dùng
   kết quả Run All** tái sử dụng kết quả đã chạy mà không cần chạy lại.

Xuất kết quả: **CSV / JSON / PNG / HTML** (PDF tùy chọn); phiên được lưu trong
`results/gui_sessions/` (tự tạo khi chạy).

Kịch bản demo 3–5 phút:

1. Mở app → trang **Home** giới thiệu bài toán.
2. **Dataset**: chọn `mknap1.txt`, bài 1 → xem `p_j / r_ij / b_i`.
3. **Algorithm**: **Run All** (Greedy, DP, GA, SA) → xem bảng + đường hội tụ.
4. **Comparison**: chọn `N = 3`, time limit 5–10s → **Run Session**.
5. Chỉ bảng: cột `Số seed (N)`, giải thích ô `-` của Greedy/DP (tất định).
6. Phân tích biểu đồ Profit/Gap/Runtime + nhận xét tự động → xuất báo cáo.

### 6.2. Dòng lệnh (CLI)

Chạy một thuật toán trên một bài hoặc cả dataset:

```bash
# Cú pháp: python run_algo.py <algo> <dataset> <bài|all> [-t giây] [-s seed]
python run_algo.py ga mknapcb4 1
python run_algo.py sa mknapcb4 all -t 10 -s 7
python run_algo.py greedy mknap1 1
python run_algo.py --list          # liệt kê dataset
```

Tên thuật toán: `greedy`, `dp`, `ga`, `sa` (hoặc tên đầy đủ `dynamic_programming`,
`genetic_algorithm`, `simulated_annealing`).

Chạy qua module experiments và lưu kết quả theo session:

```bash
python -m src.experiments ga mknapcb4 all -t 10 -s 1 --session cb4_t10
```

Sinh báo cáo so sánh 4 thuật toán (CSV/PNG/report) từ `results/`:

```bash
python -m src.experiments.comparison
```

### 6.3. Lưu ý khi demo

- **Greedy/DP tất định:** chỉ chạy 1 lần; ô `Avg/Worst/Std/Gap avg` hiển thị `-` kèm tooltip.
- **DP dễ OOM** ở bài lớn: chương trình trả nghiệm tốt nhất + `status=out_of_memory`, không
  sập. Nên chọn bài nhỏ (`mknap1`) khi demo trực tiếp.
- **GA/SA chạm time limit** là bình thường (thuật toán anytime) → `status=timeout` nhưng vẫn
  có nghiệm khả thi.
- Nếu thời gian demo gấp, dùng nút **Dùng kết quả Run All** thay vì chạy lại.
- `results/` không commit (đã gitignore); file cần đính kèm báo cáo thì xuất riêng.
