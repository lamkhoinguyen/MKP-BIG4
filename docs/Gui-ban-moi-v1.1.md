# ĐẶC TẢ GUI DESKTOP — GIAI ĐOẠN 7 (phiên bản 1.1)

> Tài liệu này là bản hoàn chỉnh của `docs/Gui-ban-moi.md`, đã xử lý các điểm
> vướng mắc và chốt các quyết định triển khai. Bản gốc được giữ nguyên để đối
> chiếu.
>
> Phạm vi: chỉ đặc tả GUI. Không sửa `src/core/`, `src/algorithms/`,
> `run_algo.py`, `benchmark_algo.py`, `src/experiments/` và test cũ.

---

## 1. Mục tiêu

Xây dựng ứng dụng **desktop** bằng Python + **PySide6** để thực thi, quan sát,
trực quan hóa và đánh giá thực nghiệm 4 thuật toán giải bài toán Multidimensional
Knapsack Problem (MKP):

1. Greedy (tham lam)
2. Dynamic Programming (quy hoạch động)
3. Genetic Algorithm (di truyền)
4. Simulated Annealing (mô phỏng luyện kim)

Cả 4 thuật toán dùng chung một mô hình MKP, một định dạng dữ liệu và bộ dữ liệu
OR-Library có sẵn trong repo. GUI không chỉ để bấm chạy mà còn là công cụ phân
tích: quan sát quá trình chạy, xem kết quả, so sánh trên cùng một bài toán, lưu
và xuất kết quả phục vụ báo cáo/thuyết trình.

## 2. Phạm vi

### 2.1. Có trong GĐ7

- 4 trang: Home, Dataset, Algorithm, Comparison.
- Chạy 1 thuật toán (Run), chạy nhanh cả 4 (Run All), đặt lại (Reset).
- Comparison Session: bảng, biểu đồ, nhận xét tự động, thống kê nhiều seed.
- Lưu tự động mỗi phiên so sánh; xem lại lịch sử; xuất CSV/PNG/JSON/HTML
  (PDF tùy chọn).

### 2.2. Không làm

- **Step / chạy từng bước**: không có; GUI chỉ vẽ đường hội tụ từ `result.history`.
- **Nạp dữ liệu tự sinh hoặc file ngoài OR-Library**: không có; chỉ các file
  trong `data/mknap/` (trừ `mkcbres.txt`).
- **Nút Stop / hủy giữa chừng**: không có, vì 4 thuật toán không hỗ trợ hủy an
  toàn. Người dùng đặt Time Limit ngắn khi thử nghiệm.
- **Chỉnh sửa dữ liệu, thêm/xóa bài toán, đổi mô hình toán học**: không có.

## 3. Quyết định đã chốt (so với bản nháp)

| # | Vấn đề | Quyết định trong v1.1 |
|---|--------|------------------------|
| 1 | Tên file GUI | Dùng bộ skeleton đang có trong `src/gui/`; không tạo bộ tên trùng lặp. Xem mục 7.1. |
| 2 | Thư mục session | GUI lưu riêng trong `results/gui_sessions/`, tách hẳn khỏi `results/sessions/` của `src.experiments`. Xem mục 6.2. |
| 3 | Trục biểu đồ hội tụ | Biểu đồ chồng nhau dùng **% tiến trình history** (0–100%) làm trục x, không dùng `iteration` thô hay chỉ số điểm thô. Biểu đồ 1 thuật toán vẫn dùng `iteration`. Lấy `best_profit` nếu có, fallback `profit`. Xem mục 7.4. |
| 4 | Thanh tiến độ | Không có % tiến độ của thuật toán. Dùng progress bar **indeterminate** + đồng hồ elapsed/remaining; riêng Comparison có tiến độ theo số lượt chạy hoàn thành. |
| 5 | Đóng app khi đang chạy | Không cho thoát; hộp thoại chỉ có "Thu nhỏ cửa sổ" và "Tiếp tục chờ". Không bao giờ gọi `QThread.terminate()`. Xem mục 9. |
| 6 | Multi-seed | Seed cơ sở `s`, chọn N ∈ {1, 3, 5, 10} ⇒ dùng `s, s+1, …, s+N-1`; hiển thị danh sách seed trước khi chạy. Greedy/DP chỉ chạy 1 lần, không hiển thị Std. Xem mục 8.2. |
| 7 | Nhận xét tự động | Tách nhóm "kết thúc sớm" và "dùng hết time limit"; không tuyên bố "nhanh nhất" cho GA/SA. Xem mục 8.4. |
| 8 | Run All vs Run Session | Run All = chạy nhanh, không lưu phiên. Run Session = phiên chính thức, có lưu + multi-seed + nhận xét. Xem mục 5.4.4 và 5.5.1. |
| 9 | Mức tightness | Định nghĩa `tightness_i = b_i / Σ_j r_ij` (bỏ qua ràng buộc có tổng 0), hiển thị trong Dataset. Xem mục 5.3. |
| 10 | Alias thuật toán | GUI dùng tên chuẩn `greedy`, `dynamic_programming`, `genetic_algorithm`, `simulated_annealing`; chỉ hiển thị nhãn ngắn Greedy/DP/GA/SA. |
| 11 | matplotlib | Không import `src.experiments.comparison` (module này ép backend `Agg`). GUI dùng `FigureCanvasQTAgg` trực tiếp. Xem mục 7.4. |
| 12 | Xuất báo cáo | Bắt buộc HTML self-contained; PDF tùy chọn dùng `QtPrintSupport` (có sẵn trong PySide6), không thêm dependency. |
| 13 | Điểm vào | Chính thức: `python -m src.gui.main`. Không tạo thêm điểm vào thứ hai. |
| 14 | Kiểm thử GUI | Tách logic thuần sang `src/gui/analytics.py` để test bằng pytest thường; smoke test Qt chạy offscreen, không cần `pytest-qt`. |
| 15 | Seed mặc định | Thống nhất **0** cho cả Algorithm và Comparison, theo hợp đồng `solve(..., seed=0)` trong README. `config.SEED = 1..10` chỉ là mặc định của benchmark nhiều seed; muốn khớp kết quả benchmark cũ thì nhập seed 1. |
| 16 | Phím tắt `Ctrl+R` | Gọi cùng handler với nút Run / Run Session, gồm kiểm tra bài toán đã chọn và hộp thoại xác nhận khi ước tính > 2 phút; vô hiệu khi đang chạy. |

## 4. Nền tảng desktop

| Hạng mục | Quy định |
|---|---|
| Framework | PySide6 (Qt for Python), chạy cục bộ trên Windows |
| Phiên bản đã kiểm tra | PySide6 6.9.2, matplotlib 3.10.5, Python 3 |
| Điểm chạy | `python -m src.gui.main` (từ thư mục gốc repo) |
| Cửa sổ | Một `QMainWindow`; mặc định 1280×800; tối thiểu 1100×700; cho phóng toàn màn hình |
| Co giãn | `QSplitter` cho 3 khu vực; panel phải thu gọn được bằng nút; kích thước panel được nhớ trong phiên chạy |
| Điều hướng | Sidebar + `QStackedWidget`; không mở cửa sổ rời |
| Phím tắt | `Ctrl+1..4` chuyển trang; `Ctrl+R` gọi **cùng handler** với nút chính của trang (Algorithm: Run; Comparison: Run Session), nên cũng đi qua kiểm tra bài toán và hộp thoại xác nhận khi ước tính > 2 phút; vô hiệu khi đang chạy; `Esc` dừng phát lại biểu đồ |
| Giao diện | Một theme QSS thống nhất; font dễ đọc; cột số dùng font đơn cách |
| Đa luồng | Mọi lần chạy thuật toán nằm trong `QThread`; GUI không treo |
| Đóng ứng dụng | Khi đang chạy: không cho thoát, chỉ thu nhỏ hoặc tiếp tục chờ (mục 9) |

## 5. Bố cục và các trang

### 5.1. Bố cục tổng thể

```
+-----------+--------------------------------------+----------------+
| Sidebar   |           Main Content               |   Analysis     |
| (trái)    |   (nội dung và thao tác chính)       |   (phải)       |
+-----------+--------------------------------------+----------------+
|                     Status bar (dưới cùng)                         |
+--------------------------------------------------------------------+
```

- **Sidebar (~180 px):** 4 nút Home / Dataset / Algorithm / Comparison; hiển thị
  bài toán đang chọn dạng `mknapcb4_01 (n=100, m=10)`.
- **Main Content:** thao tác chính của từng trang.
- **Analysis (~320 px):** nội dung phụ thuộc trang (giải thích, log, nhận xét,
  lịch sử phiên). Có thể thu gọn.
- **Status bar:** bài toán hiện tại, thuật toán/lượt đang chạy, thời gian đã
  trôi, thông báo ngắn.

Trạng thái dùng chung nằm ở `AppState` (mục 6); các trang đọc/ghi qua `AppState`
và tín hiệu Qt, không gọi trực tiếp lẫn nhau.

### 5.2. Trang Home

**Main Content**
- Giới thiệu MKP: `max Σ p_j x_j` với `Σ r_ij x_j ≤ b_i`, `x_j ∈ {0,1}`; ý nghĩa
  bài toán chọn hàng vận chuyển.
- 4 thẻ thuật toán, mỗi thẻ: mô tả một dòng + ưu/nhược điểm chính.
- Thông tin ứng dụng và bộ dữ liệu OR-Library (11 file, 325 bài; n = 6..500,
  m ≤ 30).
- 3 nút điều hướng nhanh: *Chọn dữ liệu*, *Chạy thuật toán*, *So sánh*.

**Analysis:** hướng dẫn ngắn theo luồng Dataset → Algorithm → Comparison.

### 5.3. Trang Dataset

**Main Content**
- Chọn file dataset (ComboBox, 11 file) rồi chọn bài toán (danh sách có ô tìm
  kiếm theo tên, kèm `n`/`m`).
- Thông tin bài: tên, `n`, `m`, `z_ref`, độ chặt tài nguyên.
- 3 bảng dùng `QAbstractTableModel` + `QTableView` (cuộn được, không dựng widget
  cho từng ô):
  - Lợi nhuận `p_j`.
  - Ma trận tài nguyên `r_ij` (m hàng × n cột).
  - Giới hạn tài nguyên `b_i`.
- Nút **Dùng bài toán này**: ghi bài vào `AppState`, chuyển sang trang Algorithm.

**Analysis**
- Giải thích `n`, `m`, `b_i`, `z_ref`.
- Thống kê: tổng lợi nhuận, tổng nhu cầu từng tài nguyên, độ chặt
  `tightness_i = b_i / Σ_j r_ij` (chỉ tính khi mẫu số > 0; nếu không, hiển thị
  `-`).

**Ghi chú kỹ thuật**
- Nạp dữ liệu qua `load_problems` (đã có cache) một lần cho mỗi file.
- Kích thước lớn nhất thực tế: n = 500, m = 30 (15.000 ô) — model/view đủ nhanh.
- Không cho nhập đường dẫn tự do; chỉ chọn từ `DATA_DIR`.
- Nếu `z_ref is None` (một số test giả lập): hiển thị `-`; dữ liệu OR-Library
  hiện tại đều có `z_ref`.

### 5.4. Trang Algorithm

#### 5.4.1. Khu điều khiển
- Chọn 1 trong 4 thuật toán.
- **Time Limit** (giây, mặc định 60).
- **Seed** (mặc định 0). Với Greedy giao diện ghi rõ "không dùng seed" và làm
  mờ ô Seed.
- Nút **Run**, **Run All**, **Reset**.
- Thanh trượt **Tốc độ phát lại** + nút **Phát lại** cho đường hội tụ (mục 5.4.3).
- Khi đang chạy: khóa toàn bộ điều khiển; progress bar indeterminate; đồng hồ
  đếm thời gian đã chạy và thời gian còn lại tối đa.

#### 5.4.2. Khu kết quả
- Profit, Runtime, Gap (%), Feasibility, Status (`ok` / `timeout` /
  `out_of_memory`), số vật phẩm được chọn.
- Mức dùng từng tài nguyên: `used / b_i` và `%`; nếu `b_i == 0` hiển thị `-`.
- `peak_memory`: chỉ hiển thị khi > 0, đơn vị MB.
- Chỉ hiển thị đúng `status` thuật toán trả về. Không có trạng thái "N/A";
  giá trị thiếu hiển thị `-`.
- `timeout` / `out_of_memory`: hiển thị rõ, kèm nghiệm tốt nhất nếu có.
- Lỗi bất ngờ: ghi log, đưa giao diện về trạng thái chờ, cho chạy lại.

#### 5.4.3. Biểu đồ hội tụ và phát lại
- Vẽ `result.history` của lần chạy hiện tại; trục x = `iteration` (ý nghĩa
  iteration của từng thuật toán được ghi trong chú thích).
- Trục y = `best_profit` nếu có, fallback `profit`.
- **Phát lại**: sau khi có history, nút Phát lại vẽ dần các điểm theo QTimer.
  Slider 1×–10×; tốc độ cơ sở 10 điểm/giây; tổng thời gian phát lại giới hạn
  30 giây (tự tăng tốc nếu history quá dài). Slider và nút Phát lại chỉ bật khi
  có history.

#### 5.4.4. Phân biệt Run / Run All / Reset
- **Run**: chạy thuật toán đang chọn, 1 seed, hiển thị kết quả + đường hội tụ.
- **Run All**: chạy lần lượt cả 4 thuật toán trên cùng bài, cùng Time Limit, cùng
  Seed; hiển thị **bảng 4 dòng** + biểu đồ hội tụ chồng nhau (trục x = **% tiến
  trình history**, xem mục 7.4). **Không lưu phiên**. Đây là chế độ xem nhanh;
  muốn lưu và so sánh chính thức thì dùng Run Session ở trang Comparison.
- **Reset**: chỉ bật khi không chạy; xóa kết quả, biểu đồ, log của trang; không
  xóa bài toán đang chọn trong `AppState`.

### 5.5. Trang Comparison

Trang quan trọng nhất cho đánh giá thực nghiệm. Mỗi lần chạy là một
**Comparison Session** mới.

#### 5.5.1. Điều khiển
- Dataset + bài toán: mặc định lấy bài trong `AppState`; nếu chưa có thì yêu cầu
  sang trang Dataset.
- Time Limit, Seed cơ sở (mặc định **0**, thống nhất với hợp đồng
  `solve(..., seed=0)` trong README; nhập 1 nếu muốn khớp benchmark cũ
  `config.SEED = 1..10`).
- Số seed N ∈ {1, 3, 5, 10}, chỉ áp dụng cho GA/SA.
  - Danh sách seed thực dùng: `s, s+1, …, s+N-1`; hiển thị rõ cạnh ô chọn.
  - Greedy/DP luôn chạy 1 lần với seed cơ sở (không ảnh hưởng kết quả).
- Nút **Run Session**; khi chạy khóa điều khiển.
- Ước lượng thời gian trước khi chạy: `T × (2N + 2)` (giây, cận trên); nếu
  > 2 phút thì hỏi xác nhận.
- Phím tắt `Ctrl+R` gọi **cùng handler** với nút Run Session, nên cũng đi qua
  kiểm tra bài toán và hộp thoại xác nhận trên; vô hiệu khi đang chạy.
- Tiến độ tổng: `đã xong / tổng lượt` kèm nhãn (vd `GA seed 2/3 — 5/8`).

#### 5.5.2. Bảng kết quả
Mỗi thuật toán một dòng:

| Cột | Ý nghĩa |
|---|---|
| Thuật toán | Greedy / DP / GA / SA |
| Profit | Best profit (N = 1 thì là profit duy nhất) |
| Avg / Worst / Std | Chỉ với GA/SA khi N > 1; Greedy/DP hiển thị `-` |
| Gap best (%) | `(z_ref - profit) / z_ref`; nếu `z_ref` thiếu hiển thị `-` |
| Gap avg (%) | Như trên, trung bình các seed; Greedy/DP hiển thị `-` |
| Runtime | Trung bình các lượt (N = 1 thì là runtime duy nhất) |
| Feasible | `k/N` |
| Status | `ok` nếu mọi lượt ok; ngược lại `ok ×k, timeout ×m, oom ×j` |
| Chọn | Số vật phẩm được chọn (best run) |
| Bộ nhớ đỉnh | Chỉ hiển thị nếu > 0 (MB) |

Quy ước thống kê:
- `best = max(profit)`, `avg = mean`, `worst = min`, `std = độ lệch chuẩn tổng
  thể (ddof=0)`, làm tròn 2 chữ số.
- Bỏ qua các lượt lỗi khỏi thống kê profit nhưng vẫn đếm trong Status/Feasible.
- Gap thống kê chỉ trên các lượt có gap khác `None`.

#### 5.5.3. Biểu đồ
1. **Profit**: cột theo thuật toán; N > 1 dùng avg + error bar std, chú thích
   best; N = 1 dùng giá trị duy nhất.
2. **Gap**: tương tự Profit.
3. **Runtime**: cột avg.
4. **Hội tụ chồng nhau**: trục x = **% tiến trình history**, chuẩn hóa
   `i / (L - 1) × 100` với `i = 0..L-1` (nếu `L = 1` thì x = 0), để mọi đường
   cùng dài 0–100% dù số điểm khác nhau. Không dùng `iteration` thô hay chỉ số
   điểm thô. Với N > 1: vẽ tất cả seed mờ (alpha 0.35), seed có profit tốt nhất
   vẽ đậm. Giữ dòng chú thích: "Trục x là % tiến trình ghi nhận; đơn vị gốc của
   history khác nhau giữa các thuật toán, nên chỉ so sánh hình dạng hội tụ,
   không so sánh giá trị iteration."
5. **Bộ nhớ đỉnh** (tùy chọn): chỉ vẽ khi có ít nhất một giá trị > 0.

Mỗi biểu đồ nằm trong một tab hoặc vùng riêng; không vẽ quá 5 biểu đồ cùng lúc.
Trạng thái rỗng: khung biểu đồ kèm hướng dẫn "Bấm Run Session để bắt đầu".

#### 5.5.4. Xuất
- Nút **Xuất**: CSV, PNG, JSON, HTML (mục 8.3).
- Nút **Xuất báo cáo**: HTML; PDF tùy chọn.

#### 5.5.5. Analysis (panel phải)
- **Nhận xét tự động** sinh từ số liệu phiên (mục 8.4).
- **Tham số phiên**: dataset, bài, Time Limit, seed cơ sở, danh sách seed, thời
  điểm chạy.
- **Lịch sử phiên**: danh sách trong `results/gui_sessions/`; mỗi dòng gồm thời
  gian, bài toán, time limit, số seed. Bấm để xem lại; có nút **Xóa phiên** và
  **Mở thư mục**.

#### 5.5.6. Nguyên tắc dữ liệu
- Bảng/biểu đồ của phiên mới chỉ dùng kết quả của chính phiên đang chạy.
- Phiên đã lưu chỉ để xem lại, hiển thị banner "Kết quả đã lưu ngày …"; không
  tự khôi phục khi mở app; không thay thế kết quả phiên mới.
- Một thuật toán lỗi/timeout vẫn có dòng riêng với status đúng; không dừng phiên.

## 6. Trạng thái dùng chung và lưu trữ

### 6.1. AppState

Lớp `AppState(QObject)` giữ và phát tín hiệu khi thay đổi:

| Trường | Ý nghĩa |
|---|---|
| `dataset_file` | tên file, vd `mknapcb4.txt` |
| `problem` | `MKPProblem` đang chọn (đã commit) |
| `time_limit` | mặc định 60 |
| `seed` | seed cơ sở, mặc định **0** cho cả Algorithm và Comparison |
| `num_seeds` | 1/3/5/10 (chỉ Comparison) |
| `last_result` | `MKPResult` gần nhất (Algorithm) |
| `last_session` | kết quả phiên gần nhất (Comparison) |
| `running` | đang có tác vụ chạy hay không |
| `viewing_saved_session` | đang xem phiên đã lưu hay không |

Quy ước: chọn bài ở Dataset chỉ **commit** khi bấm "Dùng bài toán này".

### 6.2. Lưu phiên tự động

Mỗi Comparison Session chạy xong được lưu vào:

```
results/gui_sessions/<YYYYMMDD_HHMMSS>_<problem>/
  session.json
  comparison.csv
  chart.png
  nhan_xet.txt
```

- Nếu tên đã tồn tại, thêm hậu tố `_2`, `_3`, …
- `problem` trong tên thư mục được sanitize (chỉ `[A-Za-z0-9_-]`).
- Không dùng chung thư mục với session của `src/experiments`
  (`results/sessions/<tên>/<algo>/`).
- Ghi chú đã kiểm tra code: `comparison --session <tên>` **không quét thư mục
  con**; nó mở đúng `results/sessions/<tên>` và đọc các thư mục con theo tên
  thuật toán (`greedy/dp/ga/sa`). Nếu đặt GUI trong `results/sessions/gui/` thì
  GUI không bị tự động liệt kê, nhưng ai gọi `--session gui` sẽ gặp lỗi
  "không có bài nào đủ 4 thuật toán". Tách sang `results/gui_sessions/` để loại
  bỏ hoàn toàn khả năng nhầm lẫn này.
- `results/gui_sessions/` nằm trong vùng gitignore nhờ `results/*/` (tương tự
  `results/sessions/`); lịch sử chỉ tồn tại trên máy đang chạy.

`session.json` (schema rút gọn):

```json
{
  "version": 1,
  "created_at": "2026-11-19T14:30:00",
  "problem": {
    "file": "mknapcb4.txt",
    "name": "mknapcb4_01",
    "n": 100,
    "m": 10,
    "z_ref": 23064.0
  },
  "params": {
    "time_limit": 60,
    "base_seed": 0,
    "num_seeds": 3,
    "seeds": [0, 1, 2]
  },
  "algorithms": {
    "greedy": {
      "runs": [
        {
          "seed": 0,
          "profit": 22000.0,
          "gap": 0.046,
          "runtime": 0.02,
          "feasible": true,
          "status": "ok",
          "selected_count": 42,
          "peak_memory": 0.0,
          "history": []
        }
      ],
      "stats": null
    },
    "ga": {
      "runs": ["..."],
      "stats": {
        "best": 22800.0,
        "avg": 22650.0,
        "worst": 22500.0,
        "std": 132.4,
        "gap_avg": 0.012,
        "runtime_avg": 60.0,
        "feasible": "3/3",
        "status": "ok ×3"
      }
    }
  }
}
```

Quy tắc ghi:
- Chuyển toàn bộ numpy scalar/array sang kiểu Python trước khi `json.dump`.
- History được giới hạn tối đa 600 điểm/lượt (hiện tại các thuật toán đều
  ≤ ~500 điểm, nên gần như không mất dữ liệu).
- Ghi atomically: ghi file tạm rồi `os.replace` để tránh file hỏng.
- Nếu phiên có lỗi giữa chừng: vẫn lưu các lượt đã xong + status lỗi, không mất
  kết quả.

### 6.3. Lịch sử phiên

- Liệt kê bằng glob `results/gui_sessions/*/session.json`, sắp xếp giảm dần theo
  `created_at`.
- Mỗi dòng: thời gian, bài toán, time limit, số seed.
- Mở lại: đọc `session.json`, dựng lại bảng; hiển thị `chart.png` đã lưu; hiển
  thị `nhan_xet.txt`.
- **Xóa phiên**: hỏi xác nhận, xóa cả thư mục.
- **Mở thư mục**: `os.startfile(folder)` trên Windows, có xử lý ngoại lệ.

### 6.4. Xuất kết quả

- **CSV**: bảng so sánh; mã hóa `utf-8-sig` để mở đúng tiếng Việt trong Excel.
- **JSON**: toàn bộ `session.json` của phiên hiện tại/đang xem.
- **PNG**: biểu đồ tổng hợp 2×2 (Profit, Gap, Runtime, Hội tụ) của phiên.
- **HTML**: một file self-contained gồm tham số phiên, bảng, ảnh PNG nhúng
  base64, nhận xét; mở được bằng trình duyệt.
- **PDF** (tùy chọn): render HTML bằng `QTextDocument` + `QPrinter`
  (`PySide6.QtPrintSupport`); nếu lỗi thì thông báo và giữ HTML.
- Hộp thoại lưu mặc định vào thư mục người dùng chọn; tên file mặc định
  `mknap_<problem>_<timestamp>`.
- Lỗi ghi file: hiển thị hộp thoại lỗi rõ ràng; không làm mất kết quả đang hiển
  thị.

## 7. Kiến trúc triển khai

### 7.1. Cấu trúc file (chốt)

```
src/gui/
  __init__.py
  main.py                    # MỚI: QApplication + MainWindow
  main_window.py             # cửa sổ chính, sidebar, QStackedWidget, status bar
  app_state.py               # MỚI: AppState(QObject)
  analytics.py               # MỚI: logic thuần (thống kê, history, nhận xét) — không import Qt
  session_store.py           # MỚI: lưu/đọc/xóa/xuất phiên
  styles.py                  # loader QSS (đọc styles/theme.qss)
  styles/theme.qss           # MỚI: theme duy nhất
  workers/
    __init__.py
    algorithm_worker.py      # AlgorithmWorker + SessionWorker (QObject + QThread)
  pages/
    __init__.py
    home_page.py
    dataset_page.py
    algorithm_page.py
    comparison_page.py
  widgets/
    __init__.py
    sidebar.py
    analysis_panel.py
    data_table.py            # QAbstractTableModel dùng lại cho 3 bảng dữ liệu
    control_panel.py
    result_panel.py          # bảng kết quả dùng lại ở Algorithm và Comparison
    chart_widget.py          # FigureCanvasQTAgg + các hàm vẽ
```

Không tạo thêm `workers.py`, `widgets/charts.py`, `widgets/result_table.py` để
tránh trùng lặp với skeleton hiện có. Các file rỗng còn lại phải được dùng đúng
mục đích ở trên hoặc xóa nếu không dùng.

### 7.2. Luồng gọi thuật toán

- GUI chỉ dùng API có sẵn: `get_problem`, `load_problems`, `get_solver`,
  `build_result` (gián tiếp), `MKPResult`.
- `get_solver` **chỉ nhận tên chuẩn** (`greedy`, `dynamic_programming`,
  `genetic_algorithm`, `simulated_annealing`); GUI tự map nhãn ngắn.
- `AlgorithmWorker`:
  - Nhận `(algorithm, problem, time_limit, seed)`.
  - Tín hiệu: `started(str)`, `log(str)`, `finished(str, object)`, `failed(str, str)`.
  - Bắt mọi exception của thuật toán, phát `failed`, không làm sập app.
- `SessionWorker`:
  - Nhận danh sách lượt chạy (thuật toán × seed) theo thứ tự.
  - Tín hiệu: `progress(done, total, label)`, `run_done(algo, seed, result)`,
    `log(str)`, `finished(list)`, `failed(str, str)`.
  - Dùng lại cho **Run All** với danh sách 4 lượt, không lưu.
- Worker không chạm vào widget; mọi cập nhật UI thực hiện trong slot ở luồng GUI.
- Sau khi xong: `thread.quit()`, `thread.wait()`, giải phóng worker.

### 7.3. Thống kê và nhận xét

- Toàn bộ logic trong `analytics.py` (thuần Python, không Qt):
  - `seeds_for(base, n)`
  - `summarize_runs(runs) -> stats`
  - `history_series(result) -> list[(x, y)]`
  - `comments(stats, params) -> list[str]`
  - `format_*` cho hiển thị.
- Nhờ vậy test được bằng pytest thường, không cần khởi tạo Qt.

### 7.4. Biểu đồ

- Dùng `matplotlib.figure.Figure` + `FigureCanvasQTAgg`; không dùng `pyplot`.
- **Không import** `src.experiments.comparison` trong bất kỳ file GUI nào, vì
  module đó gọi `matplotlib.use("Agg")` ở cấp module và sẽ ảnh hưởng backend.
- Nếu cần tái dùng hàm vẽ cho báo cáo, tách helper thuần sang module riêng không
  ép backend, hoặc chỉ dùng `Figure.savefig`.
- Quy tắc trục x:
  - Một thuật toán: `iteration` (ý nghĩa iteration ghi trong chú thích).
  - Nhiều thuật toán/seed: **% tiến trình history**:
    `x_i = i / (L - 1) × 100` với `i = 0..L-1`; nếu `L = 1` thì `x = 0`.
    Cách này đưa mọi đường về cùng thang 0–100% dù số điểm khác nhau
    (Greedy ~n, DP ~n+1, GA ≤500, SA ≤~500).
  - Luôn giữ chú thích: đơn vị gốc của history khác nhau, nên chỉ so sánh hình
    dạng hội tụ, không so sánh giá trị iteration.
- Quy tắc trục y: `best_profit` nếu có, fallback `profit`.

### 7.5. Theme

- `styles.py` cung cấp `load_stylesheet()` đọc `src/gui/styles/theme.qss` theo
  đường dẫn tuyệt đối từ `Path(__file__)`, không phụ thuộc cwd.
- Nếu thiếu file QSS, dùng stylesheet mặc định tối thiểu và ghi log.

## 8. Quy tắc nghiệp vụ

### 8.1. Trạng thái và hiển thị

- Chỉ hiển thị `status` thật của thuật toán.
- Giá trị `None`/không có: hiển thị `-`, không bịa số.
- `timeout`/`out_of_memory`: kèm ghi chú "nghiệm tốt nhất tại thời điểm dừng"
  nếu có nghiệm.
- `peak_memory` chỉ hiển thị khi > 0.

### 8.2. Multi-seed (chốt)

- Seed cơ sở mặc định **0**, thống nhất cho Algorithm và Comparison, theo hợp
  đồng `solve(..., seed=0)` trong README. `config.SEED = 1..10` chỉ là mặc định
  của benchmark nhiều seed; muốn tái lập kết quả benchmark cũ thì nhập seed 1
  (khi đó danh sách là 1, 2, …, N).
- N chỉ áp dụng cho GA/SA; Greedy/DP chạy 1 lần.
- Danh sách seed = `s … s+N-1`; hiển thị trước khi chạy.
- Tổng lượt chạy = `2N + 2` (GA, SA mỗi thuật toán N lượt; Greedy, DP mỗi
  thuật toán 1 lượt).
- Bảng: Greedy/DP để `-` ở Avg/Worst/Std và Gap avg; hiển thị giá trị duy nhất
  ở Profit/Gap best.
- Biểu đồ cột dùng avg + std (N > 1) hoặc giá trị duy nhất (N = 1).
- Status tổng hợp dạng `ok ×k, timeout ×m, oom ×j`; Feasible dạng `k/N`.

### 8.3. Xuất

- CSV UTF-8 có BOM.
- PNG là biểu đồ tổng hợp của phiên.
- HTML self-contained (ảnh base64) là định dạng báo cáo bắt buộc.
- Tên file không chứa ký tự cấm Windows (`<>:"/\|?*`).

### 8.4. Nhận xét tự động (quy tắc)

Đầu vào: bảng thống kê + tham số phiên. Không dùng câu cố định; mỗi câu phải
gắn với số liệu. Các bước:

1. **Chia nhóm thời gian**:
   - `early` = thuật toán có `runtime_avg < 0.9 × time_limit` và không timeout.
   - `time_limited` = còn lại.
   - Nếu `early` rỗng: ghi "Cả 4 thuật toán đều dùng hết giới hạn thời gian nên
     không thể so sánh tốc độ tuyệt đối."
2. **Profit tốt nhất**: nêu thuật toán + profit. Nếu chênh lệch giữa các thuật
   toán ≤ 0.5%: ghi là "tương đương" và liệt kê.
3. **Gap**: nêu gap nhỏ nhất; nếu `gap == 0` và có `z_ref`: "đạt giá trị tham
   chiếu Z_ref". Không dùng từ "tối ưu" khi không có `z_ref`.
4. **Tốc độ**: chỉ so sánh trong nhóm `early` (thường Greedy/DP). Không tuyên bố
   GA/SA nhanh/chậm dựa trên runtime ≈ time_limit.
5. **Độ ổn định**: chỉ với GA/SA và N > 1: nêu std thấp/cao, kèm giá trị.
6. **Vấn đề**: liệt kê timeout/out_of_memory và thuật toán tương ứng; nêu
   feasibility nếu < toàn bộ.
7. **Bối cảnh**: luôn kèm "N seed, time limit T giây" để người đọc hiểu mẫu.

Ví dụ cấu trúc (nội dung thay đổi theo số liệu):
- "GA đạt profit cao nhất (22.800), hơn Greedy 3,6%."
- "Greedy và DP kết thúc sớm; GA/SA dùng hết 60 giây."
- "DP trả out_of_memory ở 1/1 lượt; kết quả DP chỉ là nghiệm tốt nhất có kiểm
  soát bộ nhớ."
- "Với 3 seed, GA có std 132,4 — ổn định hơn SA (std 410,2)."

## 9. Trạng thái giao diện cần xử lý

| Tình huống | Hành vi |
|---|---|
| Chưa chọn bài toán | Run/Run Session bị vô hiệu; hiện hướng dẫn sang Dataset |
| Đang chạy | Khóa điều khiển; progress indeterminate + đồng hồ; chặn đóng app |
| Chạy xong | Hiện kết quả, ghi log, lưu phiên (Comparison), cập nhật Analysis |
| Timeout / out_of_memory | Hiện status đúng, kèm nghiệm tốt nhất nếu có |
| Lỗi bất ngờ | Ghi log, giữ app hoạt động, cho chạy lại |
| Lưu/xuất thất bại | Báo lỗi rõ, không mất kết quả đang hiển thị |
| Bài lớn | model/view, không dựng widget từng ô |
| Xem phiên đã lưu | Banner "Kết quả đã lưu ngày …"; không trộn với phiên mới |
| Đóng khi đang chạy | Hộp thoại chỉ có "Thu nhỏ" / "Tiếp tục chờ" |
| History rỗng | Ẩn nút Phát lại, hiển thị "Thuật toán không cung cấp history" |

## 10. Kiểm thử

### 10.1. Test hiện có

```powershell
python -m pytest tests/
```

Bắt buộc giữ nguyên **94 passed** (không sửa test cũ).

### 10.2. Test mới (không cần Qt cho phần lớn)

| File | Nội dung |
|---|---|
| `tests/test_gui_analytics.py` | seeds_for, summarize_runs, history_series, comments (hòa điểm, early/time-limited, OOM, gap None) |
| `tests/test_gui_session_store.py` | lưu/đọc/xóa/xuất CSV/JSON/HTML vào thư mục tạm; JSON chuyển numpy; ghi atomic |
| `tests/test_gui_smoke.py` | Khởi tạo `QApplication` offscreen, tạo `MainWindow`, chuyển 4 trang; skip nếu thiếu PySide6 |

- Smoke test dùng `QT_QPA_PLATFORM=offscreen`; không thêm `pytest-qt`.
- Không đưa logic nghiệp vụ vào widget để tránh phải test Qt.

### 10.3. Kiểm tra thủ công tối thiểu

```powershell
python -m src.gui.main
```

Checklist: mở 4 trang; chọn bài; Run từng thuật toán; Run All; Run Session với
N = 1 và N = 3; mở lại phiên đã lưu; xóa phiên; xuất CSV/PNG/JSON/HTML; thử
timeout (Time Limit = 1 với GA/SA); thử DP trên bài lớn (OOM); đóng app khi đang
chạy.

## 11. Thứ tự triển khai và Definition of Done

| Bước | Việc | DoD |
|---|---|---|
| 1 | Khung cửa sổ, sidebar, QStackedWidget, panel Analysis, status bar, theme, `main.py` | `python -m src.gui.main` mở cửa sổ; chuyển 4 trang trống bằng Ctrl+1..4; smoke test pass |
| 2 | `AppState` + trang Home | Chọn bài từ Dataset cập nhật sidebar; các nút Home điều hướng đúng |
| 3 | Trang Dataset | Chọn file/bài; 3 bảng hiển thị đúng dữ liệu; n=500 mượt; commit bài |
| 4 | `analytics.py` + worker + trang Algorithm (Run) | Chạy 1 thuật toán không treo; kết quả/status đúng; biểu đồ hội tụ; phát lại |
| 5 | Run All | Bảng 4 dòng + hội tụ chồng nhau; không lưu phiên |
| 6 | Trang Comparison (N = 1) | 4 dòng đúng; biểu đồ; nhận xét tự động từ số liệu |
| 7 | Multi-seed GA/SA | Danh sách seed đúng; thống kê best/avg/worst/std; tiến độ theo lượt |
| 8 | `session_store.py` | Tự lưu phiên; lịch sử; mở lại; xóa; xuất CSV/PNG/JSON/HTML; lỗi ghi file được báo |
| 9 | Hoàn thiện | Test GUI pass; 94 test cũ pass; cập nhật README + `docs/HUONG_DAN_TEST.md`; rà trạng thái rỗng/lỗi |

## 12. Rủi ro và giới hạn đã biết

- **Không hủy được thuật toán**: đóng app khi đang chạy bị chặn; phiên nhiều
  seed có thể kéo dài `T × (2N + 2)` giây (Greedy/DP chạy 1 lượt, GA/SA chạy N
  lượt mỗi thuật toán).
- **DP có thể vượt thời gian một chút** ở một tầng trạng thái lớn; GUI hiển thị
  runtime thực tế, không che giấu.
- **Hội tụ giữa các thuật toán không so sánh trực tiếp được**: đã chuẩn hóa
  trục x về % tiến trình để cùng độ dài, nhưng đơn vị gốc của history vẫn khác
  nhau (item, generation, iteration, stage); chỉ so sánh hình dạng hội tụ,
  không so sánh giá trị iteration.
- **SA ghi history thưa** (~≤500 điểm, bước 10.000 iteration) — biểu đồ có thể
  ít điểm.
- **Lịch sử phiên bị gitignore**: chỉ tồn tại trên máy đã chạy; khi demo máy
  khác sẽ không có lịch sử.
- **Session GUI và session experiments độc lập**: không đọc chéo.
- **peak_memory thấp/0** với GA/SA; chỉ hiển thị khi hữu ích.
- **Không thêm dependency mới**: PySide6, matplotlib, numpy là đủ. Nếu cần test
  Qt, dùng offscreen + skip.

## 13. Kết quả mong muốn

Sau khi hoàn thiện, người dùng có thể:

- Tìm hiểu cấu trúc và dữ liệu của bài toán MKP.
- Chạy và quan sát 4 thuật toán trên cùng một bộ dữ liệu.
- Theo dõi kết quả và đường hội tụ của từng thuật toán.
- Đánh giá ưu, nhược điểm và hiệu suất thực tế của từng phương pháp.
- So sánh chất lượng nghiệm, thời gian, độ ổn định và mức dùng tài nguyên.
- Lưu, xem lại và xuất kết quả để phục vụ báo cáo và thuyết trình.

**Định hướng cuối cùng:** GUI là một ứng dụng desktop phân tích, trực quan hóa và
đánh giá thực nghiệm Greedy, Dynamic Programming, Genetic Algorithm và Simulated
Annealing trên cùng bài toán MKP — không chỉ là giao diện để bấm chạy thuật toán.
