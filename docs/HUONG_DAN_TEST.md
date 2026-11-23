# HƯỚNG DẪN CHẠY TEST & CHẠY THUẬT TOÁN VỚI DATASET

Tài liệu này liệt kê **tất cả câu lệnh** để kiểm thử chương trình và chạy 4 thuật
toán (Greedy, DP, GA, SA) trên bộ dữ liệu OR-Library.

> Mọi lệnh đều chạy **từ thư mục gốc repo** (`MKP-BIG4/`).

---

## 0. Chuẩn bị môi trường (1 lần)

```powershell
pip install -r requirements.txt
python --version          # cần Python 3
```

---

## 1. Test tự động (pytest)

### 1.1. Chạy toàn bộ test

```powershell
python -m pytest tests/
```

Kết quả mong đợi hiện tại: **127 passed**.

### 1.2. Chạy test theo từng nhóm

| Lệnh                                               | Số test | Nội dung                                                |
| -------------------------------------------------- | ------: | ------------------------------------------------------- |
| `python -m pytest tests/test_core.py`              |      18 | model, evaluator, validator, data_loader, benchmark     |
| `python -m pytest tests/test_contract.py`          |      13 | chữ ký `solve()` của 4 thuật toán                       |
| `python -m pytest tests/test_data_loader.py`       |       — | đọc đúng 2 format OR-Library, z_ref, cache              |
| `python -m pytest tests/test_validator.py`         |       — | kiểm tra nghiệm hợp lệ / vi phạm                        |
| `python -m pytest tests/test_greedy.py`            |      10 | Greedy: hợp lệ, gap, tất định, timeout, history         |
| `python -m pytest tests/test_dp.py`                |       7 | DP: hợp lệ, gap, OOM, timeout, khớp brute-force         |
| `python -m pytest tests/test_ga.py`                |       5 | GA: hợp lệ, gap, tái lập theo seed, timeout, history    |
| `python -m pytest tests/test_sa.py`                |       7 | SA: hợp lệ, gap, tái lập, timeout, history khớp kết quả |
| `python -m pytest tests/test_comparison.py`        |      12 | ghép kết quả 4 thuật toán, xếp hạng                     |
| `python -m pytest tests/test_experiments.py`       |      13 | runner, metrics, lưu JSON/summary                       |
| `python -m pytest tests/test_phase9_comparison.py` |       9 | sinh CSV/PNG/report của GĐ9                             |
| `python -m pytest tests/test_gui_analytics.py`     |      12 | thống kê, seeds, history, nhận xét (không cần Qt)       |
| `python -m pytest tests/test_gui_session_store.py` |       5 | lưu/đọc/xóa/xuất phiên GUI, JSON, atomic                |
| `python -m pytest tests/test_gui_smoke.py`         |      15 | Qt offscreen: 4 trang, Dataset, batch, thread Run, worker |

### 1.3. Chạy 1 file / 1 test cụ thể

```powershell
python -m pytest tests/test_ga.py -v
python -m pytest tests/test_ga.py::test_ga_cung_seed_cho_cung_ket_qua -v
python -m pytest tests/test_greedy.py -k "timeout or history" -v
```

### 1.4. Các tùy chọn hữu ích

```powershell
python -m pytest tests/ -x                 # dừng ngay khi test đầu tiên fail
python -m pytest tests/ -v                 # in tên từng test
python -m pytest tests/ -q                 # gọn (mặc định theo pytest.ini)
python -m pytest tests/ --durations=10     # test chậm nhất
```

---

## 2. Test nhanh 1 thuật toán (không cần file test)

Chạy trực tiếp trên 1 bài nhỏ (`mknap1`, bài 1 — n=6):

```powershell
python -c "from src.core.data_loader import get_problem; from src.algorithms import get_solver; p=get_problem('mknap1.txt',1); r=get_solver('greedy')(p,time_limit=5,seed=0); print('profit',r.total_profit,'z_ref',p.z_ref,'gap',r.optimality_gap,'feasible',r.feasible,'status',r.status)"
```

Đổi `'greedy'` thành `'dp'`, `'ga'`, `'sa'` để test thuật toán khác.

---

## 3. Chạy 1 thuật toán trên dataset (`run_algo.py`)

Cú pháp:

```powershell
python run_algo.py <algorithm> <dataset> <problem> [-t giay] [-s seed] [--no-items]
```

- `<algorithm>`: `greedy` | `dp` | `ga` | `sa` (hoặc tên đầy đủ)
- `<dataset>`: `mknap1`, `mknap2`, `mknapcb1`…`mknapcb9` (hoặc `all`)
- `<problem>`: số bài tính từ 1, hoặc `all`, mặc định `1`
- `-t`: giới hạn thời gian mỗi bài (giây), mặc định 60
- `-s`: seed (dùng cho GA/SA để tái lập), mặc định 0
- `--no-items`: không in danh sách mặt hàng được chọn

### 3.1. Xem danh sách dataset

```powershell
python run_algo.py --list
```

| File                |      Số bài |
| ------------------- | ----------: |
| `mknap1.txt`        |           7 |
| `mknap2.txt`        |          48 |
| `mknapcb1..cb9.txt` | 30 mỗi file |
| **Tổng**            |     **325** |

### 3.2. Ví dụ cơ bản

```powershell
python run_algo.py greedy mknap1 1
python run_algo.py dp     mknap1 1 -t 30
python run_algo.py ga     mknapcb4 1 -t 30 -s 1
python run_algo.py sa     mknapcb4 1 -t 30 -s 7
```

### 3.3. Chạy cả một file dữ liệu

```powershell
python run_algo.py greedy mknap1 all -t 5
python run_algo.py ga     mknapcb1 all -t 30 -s 1,2,3
```

### 3.4. Chạy tất cả dataset

```powershell
python run_algo.py greedy all -t 5
```

> Cẩn thận: `all` = 325 bài × time_limit. Ví dụ `-t 30` mất khoảng 2.7 giờ.

### 3.5. Lưu ý khi chọn thời gian

| Thuật toán | Hành vi                                                   | Gợi ý                       |
| ---------- | --------------------------------------------------------- | --------------------------- |
| Greedy     | Tất định, chạy rất nhanh                                  | `-t 1` là đủ                |
| DP         | Đúng tối ưu nhưng tốn bộ nhớ; bài lớn trả `out_of_memory` | `-t 30`, xem cột `status`   |
| GA         | Chạy đến hết `time_limit`; kết quả phụ thuộc seed         | `-t 30 -s 1`, so nhiều seed |
| SA         | Chạy đến hết `time_limit`; phụ thuộc seed                 | `-t 30 -s 7`                |

---

## 4. Benchmark nhiều bài × nhiều seed (`benchmark_algo.py`)

Khác `run_algo.py` (chỉ in màn hình), script này **lưu CSV/JSON** để so sánh sau.

```powershell
python benchmark_algo.py <algorithm> [-t giay] [--seeds 1,2,3] [--dataset ...] [--out ...]
```

Mặc định chạy **16 bài** trong `BENCHMARK_PROBLEMS` × 3 seed.

```powershell
python benchmark_algo.py greedy
python benchmark_algo.py dp    -t 30 --seeds 1
python benchmark_algo.py ga    -t 30 --seeds 1,2,3
python benchmark_algo.py sa    -t 30 --seeds 1,2,3
python benchmark_algo.py ga --dataset mknapcb4 -t 5 --seeds 1
python benchmark_algo.py ga --dataset all -t 30 --seeds 1
python benchmark_algo.py sa --out results/sa_test -t 10 --seeds 1
```

Kết quả trong `results/<algo>/` (hoặc `results/<algo>_all/` khi `--dataset all`):

```
<algo>_runs.csv / .json       từng lượt chạy (kèm history)
<algo>_summary.csv / .json    tổng hợp theo bài (best/avg/worst/std/gap)
<algo>_meta.json              cấu hình lần chạy
progress.log                  tiến độ
```

Ước lượng thời gian: `số_bài × số_seed × time_limit`.

---

## 5. Chạy thí nghiệm có lưu kết quả (`src.experiments`)

```powershell
python -m src.experiments <algorithm> <dataset> <problem> -t 30 -s 1
```

Ví dụ:

```powershell
python -m src.experiments greedy mknapcb4 1 -t 30 -s 1
python -m src.experiments ga     mknapcb4 all -t 30 -s 1
```

Kết quả mặc định lưu ở `results/experiments/<algo>/`.

Các tùy chọn riêng:

```powershell
python -m src.experiments dp mknap1 1 -t 10 --no-save     # chỉ in, không lưu
python -m src.experiments ga mknap1 1 -t 10 --out results/tmp
```

### 5.1. Cơ chế session (khuyến nghị khi so sánh 4 thuật toán)

Chạy cả 4 thuật toán với **cùng** dataset / time / seed và **cùng tên session**:

```powershell
python -m src.experiments greedy mknapcb4 1 -t 30 -s 1 --session cb4_t30_s1
python -m src.experiments dp     mknapcb4 1 -t 30 -s 1 --session cb4_t30_s1
python -m src.experiments ga     mknapcb4 1 -t 30 -s 1 --session cb4_t30_s1
python -m src.experiments sa     mknapcb4 1 -t 30 -s 1 --session cb4_t30_s1
```

Kết quả nằm trong `results/sessions/cb4_t30_s1/<algo>/`; mỗi lần chạy kiểm tra
cùng dataset/time/seed và **không đọc kết quả cũ**.

### 5.2. So sánh kết quả

```powershell
# So sánh theo session (khuyến nghị)
python -m src.experiments.comparison --session cb4_t30_s1

# So sánh các bài vừa chạy ở results/experiments/ (cùng seed)
python -m src.experiments.comparison --live

# So sánh toàn bộ kết quả 325 bài trong results/<algo>_all/
python -m src.experiments.comparison
```

Sinh ra:

```
results/comparisons/   bảng so sánh CSV
results/charts/        biểu đồ PNG
results/reports/       báo cáo markdown
results/sessions/<ten>/reports/comparison_live_report.md   (khi dùng --session/--live)
```

---

## 6. Chạy GUI desktop (PySide6)

```powershell
python -m src.gui.main
```

Bốn trang: **Home / Dataset / Algorithm / Comparison**.

- **Dataset**: chọn file (11 file, 325 bài), tìm bài, xem 3 bảng dữ liệu và độ chặt,
  bấm **Dùng bài này** để đưa bài sang Algorithm; hoặc chọn dòng đầu
  **"(tất cả bài trong file)"** rồi bấm **Dùng bài toán này** để commit mọi bài; lúc này
  tab **Tổng hợp bài** hiện tên/`n`/`m`/`z_ref`/tổng lợi nhuận/độ chặt của từng bài
  (thay vì để trống vì không có một ma trận chung).
- **Algorithm**: chọn thuật toán, thời gian, seed → **Run**; hoặc **Run All** để chạy
  cả 4 thuật toán (4 × mọi bài nếu đang chọn "tất cả") và xem biểu đồ hội tụ chồng nhau. **Reset** xóa kết quả.
- **Comparison**: chọn time limit, base seed, N = 1/3/5/10 (GA/SA chạy N seed) →
  **Run Session**. Khi đang chọn "tất cả", chương trình chạy lần lượt từng bài, lưu
  mỗi bài một phiên và gom bảng dạng `Tên bài · Thuật toán`. Xem bảng tổng hợp,
  5 tab biểu đồ, nhận xét tự động. Phiên tự lưu vào `results/gui_sessions/`;
  có thể mở lại, xóa hoặc mở thư mục.
- **Xuất**: CSV / JSON / PNG / HTML; PDF tùy chọn (nếu Qt hỗ trợ).
- Phím tắt: `Ctrl+1..4` chuyển trang, `Ctrl+R` chạy thao tác chính, `Esc` dừng
  phát lại biểu đồ. Không đóng cửa sổ khi đang chạy.

Chạy test GUI ở chế độ không cần màn hình:

```powershell
$env:QT_QPA_PLATFORM="offscreen"
python -m pytest tests/test_gui_analytics.py tests/test_gui_session_store.py tests/test_gui_smoke.py -v
```

---

## 7. Chạy nhanh toàn bộ quy trình kiểm thử (checklist)

```powershell
# 1. Test toàn bộ
python -m pytest tests/

# 2. Smoke test 1 bài mỗi thuật toán (nhanh, ~5 giây/bài)
python run_algo.py greedy mknap1 1 -t 5 --no-items
python run_algo.py dp     mknap1 1 -t 5 --no-items
python run_algo.py ga     mknap1 1 -t 5 -s 1 --no-items
python run_algo.py sa     mknap1 1 -t 5 -s 1 --no-items

# 3. Session so sánh 1 bài
python -m src.experiments greedy mknap1 1 -t 5 -s 1 --session demo
python -m src.experiments dp     mknap1 1 -t 5 -s 1 --session demo
python -m src.experiments ga     mknap1 1 -t 5 -s 1 --session demo
python -m src.experiments sa     mknap1 1 -t 5 -s 1 --session demo
python -m src.experiments.comparison --session demo

# 4. GUI (mở cửa sổ thật)
python -m src.gui.main
```

---

## 8. Lưu ý

- GUI PySide6 chạy bằng `python -m src.gui.main`; `main.py` ở thư mục gốc để trống.
- Không sửa `src/core/` và test cũ; chạy `python -m pytest tests/` trước khi commit.
- DP trên bài lớn (mknapcb) có thể trả `out_of_memory` — đây là hành vi đúng, không phải lỗi.
- GA/SA chạy đủ `time_limit`; muốn kết quả lặp lại được phải giữ nguyên `seed` và `time_limit`.
