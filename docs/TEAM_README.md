# TEAM README — MKP-BIG4 (Thuat toan 4)

## Mục tiêu
Mỗi thanh viên tự triển khai thuật toán được chỉ định (Greedy, DP, GA, SA) trên cùng bộ dataset OR-Library, tuân theo contract chung, cấu trúc lịch sử chuẩn, và báo cáo benchmark để so sánh.

## Contract chung
- Chữ ký: `solve(problem: MKPProblem, *, time_limit: float = 60, seed: int = 0) -> MKPResult`
- Status: `ok` / `timeout` / `out_of_memory`
- Kết quả qua `build_result(problem, x, runtime=..., history=..., status=...)`
- `history`: bắt buộc `{"iteration": int, "profit": float}`; mỗi thuật toán có thêm trường riêng (xem chi tiết bên dưới).
- **Không** đọc file; chỉ sử dụng `MKPProblem` từ `src.core.model`.
- Không thay đổi tên hàm/file, seed chỉ là tham số.

## Các thuật toán

### Greedy (TV1) – tham lam thích nghi nhiều ràng buộc
- Ưu tiên: profit / sum(weight_i / (capacity_i - used_i))
- Lặp cho đến khi không có mặt hàng nào vừa capacity.
- History: `{"iteration", "profit", "item", "score", "decision", "skipped"}`
- Tất định (seed không ảnh hưởng). Tất cả 16 bài phải **ok**, avg gap ~1.24%, worst `mknap1_02` ~4.24%.
- Run: `python run_algo.py greedy mknapcb4 all -t 5 --no-items`

### Dynamic Programming (TV2) – DP thưa, cat can, OOM có kiểm soát
- State: vector tài nguyên đã dùng + profit tốt nhất.
- Trao đổi state trên mỗi mặt hàng, sử dụng bound pruning.
- Giới hạn bộ nhớ: `MAX_STATES = 2_000_000`, `DEFAULT_MEMORY_LIMIT_MB = 3000`.
- History: `{"step", "iteration", "phase", "item", "n_states", "n_candidates", "n_pruned", "best_profit", "profit", "lower_bound", "elapsed"}`
- Đối với bài nhỏ: chính xác (gap 0). Đối với bài lớn: 5/16 ok, 10/16 OOM, 1 timeout.
- Run: `python run_algo.py dp mknapcb1 1 -t 60`

### Genetic Algorithm (TV3) – GA nhị phân + Repair
- Representation: nhị phân string độ dài n.
- Selection: tournament, crossover (kiểm tra), mutation (khó bị ảnh hưởng), repair.
- History: `{"iteration", "profit", "best_profit"}` (chỉ ghi thế hệ)
- Average gap ~0.33% khi 10s, `timeout` ở 60s.
- Run: `python run_algo.py ga mknapcb3 1 -t 60 --seeds 1,2,3`

### Simulated Annealing (TV4) – SA với random_restart
- Khởi tạo bằng Greedy, move: flip 1 bit hoặc swap 1-0, acceptance exp(Δ/T).
- Lịch giảm T hình học, random_restart khi không tiến triển.
- History: `{"iteration", "profit", "current_profit", "temperature", "accepted", "move", "delta"}`
- Gap trung bình ~0.65% (phụ thuộc vào time‑limit). `timeout` ở 60s.
- Run: `python run_algo.py sa mknapcb4 1 -t 60 --seeds 1,2,3`

## Kiểm tra (test) – `python -m pytest tests/`
- Phải **72 passed**.
- Mọi thuật toán phải có file test riêng:
  - `tests/test_greedy.py` (10 test) — khẳng định tất định, từng mặt hàng, edge cases.
  - `tests/test_dp.py` (7 test) — gap chính xác, OOM, timeout, tất định.
  - `tests/test_ga.py` (5 test) — OK, deterministic, timeout, history.
  - `tests/test_sa.py` (7 test) — OK, deterministic, timeout, history, restart.
  - `tests/test_comparison.py` (1 test) — 4 thuật toán trên bài 4 mặt hàng, khẳng định chung.

## Benchmark (chuẩn spec 9.2–9.3)
Benchmark thực hiện trên **cùng một máy** (cùng seed, cùng time_limit).

### Giả sử (mẫu) – 16 bài × 10s (chỉ để chứng minh):
```bash
python benchmark_algo.py greedy -t 10 --seeds 1 --out results/_tmp/greedy
python benchmark_algo.py dp     -t 10 --seeds 1 --out results/_tmp/dp
set results/_tmp/ga/results_ga_summary.csv
python benchmark_algo.py ga     -t 10 --seeds 1 --out results/_tmp/ga
python benchmark_algo.py sa     -t 10 --seeds 1 --out results/_tmp/sa
```
Tạm thời trung bình (máy này):
- Greedy: 16/16 OK, gap TB = 1.24%
- DP: 5 OK, 10 OOM, 1 timeout, gap TB = 1.28%
- GA: 16/16 timeout, gap TB = 0.33%
- SA: 16/16 timeout, gap TB = 0.65%

### Chính thức (yêu cầu spec) – 16 bài × 60s (GA/SA × 3 seed):
```bash
python benchmark_algo.py greedy -t 60 --seeds 1 --out results/final/greedy
python benchmark_algo.py dp     -t 60 --seeds 1 --out results/final/dp
python benchmark_algo.py ga     -t 60 --seeds 1,2,3 --out results/final/ga
python benchmark_algo.py sa     -t 60 --seeds 1,2,3 --out results/final/sa
```
Dự kiến:
- Greedy/DP: ~2 phút mỗi cái.
- GA/SA: ~48 phút mỗi cái (x3 seeds).
- Đầu ra: CSV và JSON trong `results/final/<algo>/` (runs, summary, meta).

## Các file thay đổi (commit `0ae0b2b`)
1. src/algorithms/greedy.py – history, deterministic.
2. src/algorithms/dynamic_programming.py – giới hạn bộ nhớ, OOM.
3. src/algorithms/genetic_algorithm.py – history, đồng bộ profit cuối.
4. src/algorithms/simulated_annealing.py – history, move/delta.
5. src/algorithms/__init__.py – contract chuẩn.
6. src/core/model.py – thêm `peak_memory` vào `to_dict`.
7. benchmark_algo.py – cột `peak_memory_mb`, `timeout_runs`, `oom_runs`.
8. run_algo.py – bảng in cột `status`.
9. tests/test_comparison.py – test chéo 4 thuật toán.
10. tests/test_greedy.py – 10 test.

## Các bước tiếp theo
1. Pull branch `feature` (nếu bạn đã push) hoặc sao chép từ repo.
2. Chạy `python -m pytest tests/` để xác nhận 72 passed.
3. Chạy benchmarks (bước 2) trên máy bạn.
4. Soạn báo cáo từ CSV (`runs`, `summary`) + biên bản (tạm dịch lại) cho nhóm.
5. experiments/GUI (tương lai) – tích hợp với worker thread, history realtime, hiển thị so sánh.

**Lưu ý:** remote hiện vẫn ở `99195e3`. Branch đã commit local `0ae0b2b`. Bạn có thể commit này hoặc đợi push sau.

Mọi thắc mắc về test, benchmark, hoặc mở rộng, hỏi thoải mái.