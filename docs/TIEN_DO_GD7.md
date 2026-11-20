
# THEO DÕI TIẾN ĐỘ — GIAI ĐOẠN 7 (GUI DESKTOP)

Cập nhật lần cuối: 2026-11-19
Tài liệu gốc: `docs/Gui-ban-moi-v1.1.md`
Trạng thái tổng: **Hoàn thành bước 0–9** (còn kiểm tra hình ảnh trên màn hình thật và xuất PDF)

---

## 1. Cách dùng file này

- Đây là file **theo dõi tiến độ**, không phải đặc tả. Đặc tả nằm ở
  `docs/Gui-ban-moi-v1.1.md`.
- Mỗi bước có: mục tiêu, checklist việc cần làm, file dự kiến, DoD và mục
  **"Đã làm / Đã chỉnh"**.
- Khi làm xong việc nào: đánh `[x]`, đổi trạng thái ở bảng tổng quan, ghi thêm
  một dòng vào **"Đã làm / Đã chỉnh"** kèm ngày.
- Không xóa ghi chú cũ; chỉ thêm mới (giống `docs/LOG.md`).
- Quy ước trạng thái: `Chưa bắt đầu` → `Đang làm` → `Hoàn thành` (hoặc `Tạm dừng`
  nếu bị chặn).
- Các mục 6–9 dùng để ghi nhật ký phiên, vấn đề, trạng thái file và kết quả
  kiểm thử; mục 10 là checklist nghiệm thu; mục 11 là mẫu ghi.

---

## 2. Bối cảnh dự án

| Giai đoạn    | Nội dung                                                   | Trạng thái                                           |
| -------------- | ----------------------------------------------------------- | ------------------------------------------------------ |
| GĐ1–6        | Core, data loader, contract, 4 thuật toán, CLI, benchmark | Hoàn thành (theo `HANDOFF.md`, `LOG.md`)         |
| GĐ9           | Experiments + comparison + cơ chế session                 | Hoàn thành                                           |
| **GĐ7** | **GUI desktop PySide6**                               | **Đang thực hiện — bước 1/9 hoàn thành** |
| GĐ8           | Tích hợp GUI + hiển thị lịch sử                       | Chưa bắt đầu (phần lớn nằm trong GĐ7)          |
| GĐ10          | Rà soát báo cáo/slide                                   | Chưa bắt đầu                                       |

---

## 3. Bảng tổng quan các bước GĐ7

| Bước | Tên                                        | Phụ thuộc | Trạng thái           | File chính                                                                    |
| ------ | ------------------------------------------- | ----------- | ---------------------- | ------------------------------------------------------------------------------ |
| 0      | Đặc tả GUI v1.1                          | —          | **Hoàn thành** | `docs/Gui-ban-moi-v1.1.md`                                                   |
| 1      | Khung cửa sổ, theme, `main.py`          | Bước 0    | **Hoàn thành** | `main_window.py`, `main.py`, `styles.py`                                 |
| 2      | `AppState` + trang Home                   | Bước 1    | **Hoàn thành**       | `app_state.py`, `pages/home_page.py`                                       |
| 3      | Trang Dataset                               | Bước 2    | **Hoàn thành**       | `pages/dataset_page.py`, `widgets/data_table.py`                           |
| 4      | `analytics.py` + worker + Algorithm (Run) | Bước 3    | **Hoàn thành**       | `analytics.py`, `workers/algorithm_worker.py`, `pages/algorithm_page.py` |
| 5      | Run All                                     | Bước 4    | **Hoàn thành**       | `pages/algorithm_page.py`                                                    |
| 6      | Comparison (N = 1)                          | Bước 4    | **Hoàn thành**       | `pages/comparison_page.py`, `widgets/chart_widget.py`                      |
| 7      | Multi-seed GA/SA                            | Bước 6    | **Hoàn thành**       | `analytics.py`, `comparison_page.py`                                       |
| 8      | `session_store.py` + lịch sử + xuất    | Bước 6–7 | **Hoàn thành**       | `session_store.py`                                                           |
| 9      | Hoàn thiện, test, cập nhật tài liệu   | Bước 1–8 | **Hoàn thành**       | `tests/test_gui_*`, `README.md`                                            |

---

## 4. Chi tiết từng bước

### Bước 0 — Đặc tả GUI (Hoàn thành)

**Đã làm**

- Đọc `docs/Gui-ban-moi.md`, đối chiếu với code hiện tại (core, algorithms,
  experiments, skeleton `src/gui/`).
- Review và chỉ ra các điểm cần chốt: cấu trúc file, session, biểu đồ hội tụ,
  tiến độ, đóng app, multi-seed, nhận xét tự động, Run All vs Run Session.
- Tạo `docs/Gui-ban-moi-v1.1.md` với 16 quyết định đã chốt.

**Đã chỉnh sau góp ý**

- 2026-11-18: chuyển thư mục session GUI từ `results/sessions/gui/` sang
  `results/gui_sessions/`; ghi rõ `comparison --session` không quét thư mục con.
- 2026-11-18: đổi trục x biểu đồ hội tụ chồng từ chỉ số điểm sang **% tiến
  trình** `i/(L-1)×100`.
- 2026-11-18: sửa công thức thời gian phiên `4×N×T` → `T×(2N+2)`.
- 2026-11-18: sửa toàn bộ tham chiếu mục trong bảng quyết định.
- 2026-11-18: thống nhất seed mặc định **0** cho Algorithm và Comparison; ghi
  rõ `config.SEED=1..10` là mặc định benchmark.
- 2026-11-18: ghi rõ `Ctrl+R` dùng chung handler, đi qua xác nhận > 2 phút.
- 2026-11-18: tạo file theo dõi tiến độ này.

**DoD:** đặc tả không còn mâu thuẫn, tham chiếu đúng, sẵn sàng triển khai.
**Kết quả:** đạt.

---

### Bước 1 — Khung cửa sổ, theme, `main.py` (Hoàn thành)

**Mục tiêu:** mở được ứng dụng với bố cục 3 khu vực và 4 trang rỗng.

**Checklist**

- [X] `src/gui/main.py`: tạo `QApplication`, nạp theme, mở `MainWindow`
- [X] `main_window.py`: `QSplitter` 3 vùng (sidebar / nội dung / Analysis)
- [X] `widgets/sidebar.py`: 4 nút Home, Dataset, Algorithm, Comparison + nhãn bài toán
- [X] `QStackedWidget` chứa 4 trang rỗng
- [X] `status bar`: bài toán, thuật toán/lượt, thời gian, thông báo
- [X] `styles/theme.qss` + `styles.py` loader theo `Path(__file__)`
- [X] phím tắt `Ctrl+1..4`; `Ctrl+R` nối vào handler của trang
- [X] `closeEvent`: chính sách chặn thoát khi đang chạy (để placeholder đến bước 4)
- [X] `tests/test_gui_smoke.py`: mở `MainWindow` offscreen, chuyển 4 trang

**File:** `src/gui/main.py`, `main_window.py`, `styles.py`,
`src/gui/styles/theme.qss`, `widgets/sidebar.py`, `widgets/analysis_panel.py`,
4 file trong `pages/`.

**DoD:** `python -m src.gui.main` mở cửa sổ; chuyển 4 trang trống bằng
`Ctrl+1..4`; smoke test pass.

**Đã làm / Đã chỉnh**

- 2026-11-18: tạo `src/gui/main.py` (QApplication + theme + MainWindow).
- 2026-11-18: viết `main_window.py`: QSplitter 3 vùng, QStackedWidget 4 trang,
  status bar, menu phím tắt, `set_page`, `set_running`, `closeEvent` chặn thoát.
- 2026-11-18: viết `widgets/sidebar.py` (4 nút + nhãn bài toán) và
  `widgets/analysis_panel.py` (tiêu đề + nội dung HTML theo trang).
- 2026-11-18: tạo 4 trang placeholder trong `pages/`; chưa làm nội dung chi tiết
  (để đúng bước 2–8).
- 2026-11-18: tạo `styles/theme.qss` + `styles.py` với fallback khi thiếu file.
- 2026-11-18: tạo `tests/test_gui_smoke.py` (5 test, offscreen).
- Test: `python -m pytest tests/test_gui_smoke.py -v` → 5 passed.
- Test: `python -m pytest tests/` → 99 passed (94 cũ + 5 mới).
- 2026-11-18: rà soát `docs/Danh-gia-GUI.md`:
  - bật `WA_StyledBackground` cho Sidebar và AnalysisPanel (nguyên nhân nền
    sidebar không được vẽ); kiểm tra pixel: sidebar `#0f172a`, panel `#f8fafc`.
  - status bar: chuyển nhãn bài toán/thuật toán sang `addPermanentWidget`,
    bỏ dòng "Trang hiện tại", thêm style chữ nhỏ + viền trên.
  - bỏ toàn bộ cụm "bước N" khỏi hint/Analysis của 4 trang; thay bằng câu
    hướng dẫn trung tính.
  - thêm tooltip `Ctrl+1..4` cho nút sidebar; tăng cỡ/tương phản nhãn
    "BÀI TOÁN ĐANG CHỌN".
  - bỏ qua yêu cầu đổi thanh tiêu đề hệ điều hành (đúng khuyến nghị trong file).
  - thêm assert `WA_StyledBackground` + tooltip vào smoke test; vẫn 5 test.
- Test lại: `pytest tests/` → 99 passed.

---

### Bước 2 — `AppState` + trang Home (Hoàn thành)

**Mục tiêu:** có trạng thái dùng chung và trang giới thiệu điều hướng được.

**Checklist**

- [X] `app_state.py`: các trường ở mục 6.1 của đặc tả + tín hiệu thay đổi
- [X] quy ước chỉ commit bài khi bấm "Dùng bài toán này"
- [X] `pages/home_page.py`: giới thiệu MKP, 4 thẻ thuật toán, thông tin dữ liệu
- [X] 3 nút điều hướng nhanh: Chọn dữ liệu / Chạy thuật toán / So sánh
- [X] sidebar cập nhật bài toán đang chọn từ `AppState`
- [X] Analysis trang Home: hướng dẫn luồng Dataset → Algorithm → Comparison

**File:** `src/gui/app_state.py`, `pages/home_page.py`, `widgets/sidebar.py`.

**DoD:** chọn bài (giả lập) cập nhật sidebar; các nút Home chuyển đúng trang.

**Đã làm / Đã chỉnh**

- 2026-11-19: tạo `src/gui/app_state.py`: `AppState(QObject)` với signal problem/dataset/
  time_limit/seed/num_seeds/last_result/last_session/running/viewing; `commit_problem`,
  `clear_problem`, `problem_text`.
- 2026-11-19: `HomePage`: giới thiệu MKP + công thức, 4 thẻ thuật toán, 3 nút điều hướng
  phát `navigate_requested`; Analysis hướng dẫn luồng Dataset → Algorithm → Comparison.
- 2026-11-19: sidebar cập nhật nhãn bài toán từ `AppState`; smoke test bấm nút Home.
- Test: `pytest tests/test_gui_smoke.py` → pass; tổng suite 122 passed.

---

### Bước 3 — Trang Dataset (Hoàn thành)

**Mục tiêu:** chọn và xem dữ liệu OR-Library.

**Checklist**

- [X] ComboBox 11 file dataset (loại `mkcbres.txt`)
- [X] danh sách bài + ô tìm kiếm, hiển thị `n`/`m`
- [X] thông tin bài: tên, n, m, z_ref, tightness
- [X] `widgets/data_table.py`: `QAbstractTableModel` cho 3 bảng
  (profits, weights, capacities)
- [X] n = 500, m = 30 hiển thị mượt (không dựng widget từng ô)
- [X] nút "Dùng bài toán này": ghi `AppState` + chuyển trang Algorithm
- [X] item "(tất cả bài trong file)": commit mọi bài, chuyển sang chế độ batch
- [X] tab "Tổng hợp bài" (chỉ hiện ở chế độ batch): tên, n, m, z_ref, tổng lợi nhuận,
  độ chặt min–max của từng bài; thông tin n/m hiện khoảng giá trị
- [X] Analysis: giải thích n/m/b_i/z_ref + thống kê + tightness; batch có bảng tóm tắt
- [X] xử lý `z_ref is None` → hiển thị `-`

**File:** `pages/dataset_page.py`, `widgets/data_table.py`.

**DoD:** chọn đúng file/bài; 3 bảng đúng dữ liệu; n=500 mượt; commit bài đúng.

**Đã làm / Đã chỉnh**

- 2026-11-19: `DatasetPage`: combo 11 file (bỏ `mkcbres.txt`), ô tìm bài, danh sách
  n/m, thẻ thông tin, 3 tab bảng, tightness; hiển thị `-` khi `z_ref is None`.
- 2026-11-19: `widgets/data_table.py`: `ArrayTableModel` chỉ dựng ô đang hiển thị;
  n=500 mượt, không tạo widget từng ô.
- 2026-11-19: cache dữ liệu theo file; nút "Dùng bài toán này" ghi `AppState` rồi
  chuyển trang Algorithm; Analysis giải thích n/m/b_i/z_ref.
- 2026-11-19: thêm item "(tất cả bài trong file)" (luôn hiện khi lọc); `AppState`
  có `commit_problems()`/`problems`/`is_batch`, `problem_text()` báo "N bài (tất cả)".
- 2026-11-19: khi chọn tất cả, ẩn 3 tab ma trận (vì mỗi bài có dữ liệu riêng) và mở tab
  `Tổng hợp bài`; thẻ thông tin hiện `n=6–50`, `m=5–10`, còn `z_ref` để `-` vì khác nhau.
- Test: smoke kiểm tra 3 bảng mknap1 (6 cột, 10 ràng buộc) + commit bài + bảng tổng hợp.

---

### Bước 4 — `analytics.py` + worker + Algorithm (Run) (Hoàn thành)

**Mục tiêu:** chạy 1 thuật toán trong luồng riêng và hiển thị kết quả.

**Checklist**

- [X] `analytics.py` (thuần Python, không Qt): `seeds_for`, `summarize_runs`,
  `history_series`, `comments`, các hàm format
- [X] `workers/algorithm_worker.py`: `AlgorithmWorker` (started/log/finished/failed)
- [X] map nhãn ngắn ↔ tên chuẩn `get_solver` (không dùng alias trực tiếp)
- [X] `pages/algorithm_page.py`: chọn algo, Time Limit, Seed, Run, Reset
- [X] khóa điều khiển khi chạy; progress indeterminate + đồng hồ elapsed/remaining
- [X] `widgets/result_panel.py`: profit, runtime, gap, feasible, status, chọn,
  tài nguyên, peak_memory (> 0)
- [X] `widgets/chart_widget.py`: vẽ history (trục `iteration`, y `best_profit`
  fallback `profit`) + phát lại với slider 1×–10×
- [X] Analysis: log realtime + mô tả thuật toán
- [X] `closeEvent`: chặn thoát khi đang chạy (Thu nhỏ / Tiếp tục chờ)
- [X] xử lý timeout/out_of_memory/lỗi bất ngờ đúng đặc tả

**File:** `analytics.py`, `workers/algorithm_worker.py`,
`pages/algorithm_page.py`, `widgets/result_panel.py`, `widgets/chart_widget.py`.

**DoD:** chạy 1 thuật toán không treo; kết quả/status đúng; biểu đồ + phát lại;
`timeout` với Time Limit = 1 (GA/SA) hiển thị đúng.

**Đã làm / Đã chỉnh**

- 2026-11-19: `analytics.py` thuần Python: `ALGORITHMS`, `seeds_for`, `estimate_seconds`,
  `build_plan`, `summarize_runs`, `history_series`, `progress_series`, `comments`, format.
- 2026-11-19: `AlgorithmWorker` (QThread) signal started/log/finished/failed; map nhãn
  ngắn ↔ tên chuẩn của `get_solver`, không dùng alias.
- 2026-11-19: `AlgorithmPage`: chọn algo/Time Limit/Seed, Run/Reset, khóa điều khiển,
  progress indeterminate + elapsed, `ResultTable`/`SingleResultDetails`, `ChartWidget`
  (matplotlib Qt) + phát lại 1×–10×, log realtime.
- 2026-11-19: xử lý timeout/out_of_memory/lỗi; chặn đóng cửa sổ khi đang chạy; giữ
  bài tại thời điểm bắt đầu chạy.
- Kiểm tra tay greedy `mknap1_01`: profit 3800, status `ok`, replay bật.

---

### Bước 5 — Run All (Hoàn thành)

**Mục tiêu:** chạy nhanh 4 thuật toán, không lưu phiên.

**Checklist**

- [X] chạy tuần tự 4 thuật toán cùng bài/time/seed
- [X] chế độ batch: 4 thuật toán × mọi bài đã chọn "(tất cả)", mỗi bài một worker
- [X] bảng 4 dòng dùng lại `result_panel`; batch hiển thị `Tên bài · Thuật toán`
- [X] biểu đồ hội tụ chồng nhau, trục x = **% tiến trình** `i/(L-1)×100`
- [X] giữ chú thích về đơn vị history khác nhau
- [X] không lưu phiên; phân biệt rõ với Run Session
- [X] `Ctrl+R` trên trang Algorithm gọi Run All? (chốt: `Ctrl+R` = Run; Run All
  chỉ qua nút — ghi chú khi triển khai)

**File:** `pages/algorithm_page.py`, `widgets/chart_widget.py`.

**DoD:** bảng 4 dòng + hội tụ chồng nhau đúng; không sinh thư mục phiên.

**Đã làm / Đã chỉnh**

- 2026-11-19: Run All chạy tuần tự 4 thuật toán cùng bài/time/seed; bảng 4 dòng dùng
  lại `ResultTable`; `ChartWidget.plot_convergence` vẽ chồng với trục x % tiến trình
  `i/(L-1)×100` + chú thích đơn vị history.
- 2026-11-19: không lưu phiên; phân biệt với Run Session. `Ctrl+R` = Run (không phải
  Run All) theo chốt trong đặc tả.
- 2026-11-19: gom bảng và biểu đồ Run All thành 2 tab (`multi_tabs`); mỗi tab dùng
  toàn bộ chiều cao, không còn cảnh bảng 4 dòng bị ép trên màn hình thấp.
- 2026-11-19: Run All đọc `state.is_batch`/`problems`, chạy tuần tự từng bài bằng
  `SessionWorker`, progress toàn cục `bài×4`, gom dòng dạng `Tên bài · Thuật toán`;
  `_on_thread_finished` chỉ dọn thread hiện tại để không mất tham chiếu lúc chuyển bài.
- Kiểm tra tay `mknap1`: 4 dòng Greedy/DP/GA/SA, đều profit 3800, có gap/status.

---

### Bước 6 — Trang Comparison (N = 1) (Hoàn thành)

**Mục tiêu:** phiên so sánh 4 thuật toán, có nhận xét tự động.

**Checklist**

- [X] `comparison_page.py`: chọn bài (mặc định `AppState`), Time Limit, Seed
- [X] `SessionWorker`: progress theo lượt, run_done, finished
- [X] bảng kết quả 4 dòng đúng cột (mục 5.5.2)
- [X] biểu đồ Profit, Gap, Runtime (N = 1) + hội tụ % tiến trình
- [X] `analytics.py`: nhận xét tự động theo quy tắc mục 8.4
- [X] Analysis: tham số phiên + nhận xét + trạng thái rỗng
- [X] tiến độ tổng `đã xong / tổng lượt`
- [X] lỗi/timeout của 1 thuật toán không dừng phiên
- [X] khi Dataset chọn "(tất cả bài trong file)": Run Session chạy từng bài, lưu từng phiên
- [X] bảng batch gắn tên bài vào nhãn (`Tên bài · Thuật toán`)

**File:** `pages/comparison_page.py`, `workers/algorithm_worker.py`,
`widgets/chart_widget.py`, `analytics.py`.

**DoD:** 4 dòng đúng; biểu đồ đúng; nhận xét dựa trên số liệu, không câu cố định.

**Đã làm / Đã chỉnh**

- 2026-11-19: `ComparisonPage` + `SessionWorker`: Time Limit, base seed, N, ước lượng
  `T×(2N+2)` và xác nhận khi > 120 giây; tiến độ `đã xong / tổng lượt`.
- 2026-11-19: bảng kết quả 4 dòng đúng cột; 5 tab biểu đồ (Profit, Gap, Runtime,
  % tiến trình, Hội tụ); `analytics.comments` sinh nhận xét theo số liệu.
- 2026-11-19: Analysis hiển thị tham số phiên + nhận xét + trạng thái rỗng; lỗi/timeout
  của một lượt không dừng phiên.
- 2026-11-19: đổi vùng kết quả thành một `QTabWidget` gồm `Bảng kết quả` + 5 tab biểu
  đồ; bảng luôn đủ 4 dòng, biểu đồ rộng hơn và chữ to hơn; tự chọn tab bảng lúc bắt
  đầu chạy và `draw_idle()` khi chuyển tab.
- 2026-11-19: nhãn bài của Algorithm/Comparison dùng `AppState.problem_text()` nên hiện
  rõ `N bài ... (tất cả)` thay vì chỉ bài đầu.
- 2026-11-19: `run_session` đọc `state.is_batch`/`problems`, chain `SessionWorker` qua
  từng bài, progress `bài×(2Nseed+2)`, lưu mỗi bài một phiên và gom bảng/biểu đồ cuối.
- Kiểm tra tay N=1: bảng/biểu đồ/nhận xét đúng; phiên tự lưu. Thử batch 2 bài: 8 dòng,
  progress 8/8, 2 phiên, banner báo số phiên.

---

### Bước 7 — Multi-seed GA/SA (Hoàn thành)

**Mục tiêu:** đánh giá độ ổn định của GA/SA.

**Checklist**

- [X] chọn N ∈ {1, 3, 5, 10}; danh sách seed = `s..s+N-1`, hiển thị trước chạy
- [X] Greedy/DP chỉ 1 lượt; hiển thị `-` ở Avg/Worst/Std/Gap avg
- [X] tổng lượt = `2N + 2`; ước lượng thời gian `T×(2N+2)`; xác nhận > 2 phút
- [X] thống kê best/avg/worst/std (ddof=0, làm tròn 2)
- [X] Status tổng hợp `ok ×k, timeout ×m, oom ×j`; Feasible `k/N`
- [X] biểu đồ cột avg + error bar std (N > 1)
- [X] hội tụ nhiều seed: seed tốt nhất đậm, còn lại alpha 0.35
- [X] `Ctrl+R` gọi cùng handler Run Session (qua xác nhận), vô hiệu khi chạy

**File:** `analytics.py`, `pages/comparison_page.py`, `widgets/chart_widget.py`.

**DoD:** chạy N = 3 cho GA/SA ra thống kê đúng; tổng lượt và tiến độ khớp.

**Đã làm / Đã chỉnh**

- 2026-11-19: N ∈ {1,3,5,10}; seed hiển thị trước khi chạy dạng `s..s+N-1`;
  Greedy/DP chạy 1 lượt, thống kê phụ hiển thị `-`.
- 2026-11-19: tổng lượt `2N+2`; thống kê best/avg/worst/std (ddof=0, làm tròn 2);
  status tổng hợp `ok ×k, timeout ×m, oom ×j`; Feasible `k/N`.
- 2026-11-19: biểu đồ cột avg + error bar std khi N > 1; hội tụ nhiều seed (seed tốt
  nhất đậm, còn lại alpha 0.35); `Ctrl+R` gọi cùng handler Run Session.
- Kiểm tra tay N=3: 8 lượt, GA/SA có avg/std/gap_avg, tiến độ 8/8.

---

### Bước 8 — `session_store.py` + lịch sử + xuất (Hoàn thành)

**Mục tiêu:** lưu/xem lại/xuất phiên so sánh.

**Checklist**

- [X] lưu tự động vào `results/gui_sessions/<YYYYMMDD_HHMMSS>_<problem>/`
- [X] `session.json` đúng schema mục 6.2; chuyển numpy → Python; ghi atomic
- [X] history giới hạn ≤ 600 điểm/lượt
- [X] lưu cả phiên lỗi một phần (không mất lượt đã xong)
- [X] `comparison.csv` UTF-8 có BOM
- [X] `chart.png` biểu đồ tổng hợp 2×2
- [X] `nhan_xet.txt`
- [X] lịch sử: glob `results/gui_sessions/*/session.json`, sắp xếp theo thời gian
- [X] mở lại phiên: banner "Kết quả đã lưu ngày …", không trộn với phiên mới
- [X] xóa phiên (xác nhận) + mở thư mục (`os.startfile`)
- [X] xuất CSV/JSON/PNG/HTML; HTML self-contained; PDF tùy chọn
- [X] lỗi ghi file: báo rõ, không mất kết quả đang hiển thị

**File:** `session_store.py`, `pages/comparison_page.py`,
`widgets/analysis_panel.py`.

**DoD:** chạy phiên → tự lưu đủ 4 file; mở lại/xóa/xuất hoạt động; JSON đọc lại
không lỗi.

**Đã làm / Đã chỉnh**

- 2026-11-19: `session_store.py`: lưu tự động `results/gui_sessions/<YYYYMMDD_HHMMSS>_<problem>/`;
  `session.json` (version, created_at, problem, params, algorithms, comments), chuyển
  numpy → Python, ghi atomic; history cap 600 điểm/lượt; lưu cả phiên lỗi một phần.
- 2026-11-19: `comparison.csv` UTF-8 BOM; `chart.png` tổng hợp 2×2; `nhan_xet.txt`.
- 2026-11-19: lịch sử glob `*/session.json`, sắp xếp mới nhất; mở lại có banner
  "Kết quả đã lưu ngày …"; xóa có xác nhận; mở thư mục bằng `os.startfile`.
- 2026-11-19: xuất CSV/JSON/PNG/HTML self-contained; PDF tùy chọn qua `QtPrintSupport`;
  lỗi ghi file báo rõ, không mất kết quả đang hiển thị.
- Kiểm tra tay: phiên `20261119_094923_mknap1_01` đủ 4 file; mở lại/xóa OK.

---

### Bước 9 — Hoàn thiện, test, tài liệu (Hoàn thành)

**Mục tiêu:** chốt GĐ7, không phá test cũ.

**Checklist**

- [X] `tests/test_gui_analytics.py`: seeds, stats, history, comments (hòa điểm,
  early/time-limited, OOM, z_ref None)
- [X] `tests/test_gui_session_store.py`: lưu/đọc/xóa/xuất, temp dir, atomic
- [X] `tests/test_gui_smoke.py`: offscreen, 4 trang
- [X] `python -m pytest tests/` → 94 test cũ vẫn pass
- [X] kiểm tra thủ công checklist mục 10.3
- [X] cập nhật `README.md` (trạng thái GUI, cách chạy)
- [X] cập nhật `docs/HUONG_DAN_TEST.md` (điểm vào GUI, test mới)
- [X] rà trạng thái rỗng/lỗi theo mục 9
- [X] cập nhật `docs/HANDOFF.md` (ghi đè) và `docs/LOG.md` (append)

**DoD:** test xanh, app chạy ổn, tài liệu khớp thực tế.

**Đã làm / Đã chỉnh**

- 2026-11-19: thêm `tests/test_gui_analytics.py` (12), `tests/test_gui_session_store.py`
  (5); mở rộng `tests/test_gui_smoke.py` lên 11 test (Home, Dataset, thread Run,
  seed label, history panel, `SessionWorker`).
- 2026-11-19: sửa `history_series`/`progress_series` nhận cả dict; cache file Dataset;
  sửa công thức std trong test.
- 2026-11-19: `pytest tests/` → **122 passed**; 94 test cũ vẫn pass.
- 2026-11-19: cập nhật `README.md`, `docs/HUONG_DAN_TEST.md`, `docs/HANDOFF.md`,
  `docs/LOG.md`, file này; theme QSS bổ sung đầy đủ.
- Đã kiểm tra tay: Run đơn, Run All, N=1, N=3, lưu/mở phiên. Còn kiểm tra trên màn
  hình thật, xuất PDF và các mục 10.1–10.3 còn lại.

---

## 5. Nhật ký thay đổi tài liệu

| Ngày      | Việc                                                                                            | File                         |
| ---------- | ------------------------------------------------------------------------------------------------ | ---------------------------- |
| 2026-11-17 | HANDOFF ghi GĐ7 là bước tiếp theo                                                           | `docs/HANDOFF.md`          |
| 2026-11-18 | Tạo đặc tả GUI v1.1 từ bản nháp                                                           | `docs/Gui-ban-moi-v1.1.md` |
| 2026-11-18 | Sửa 5 điểm theo góp ý (session, trục %, công thức thời gian, tham chiếu, seed, Ctrl+R) | `docs/Gui-ban-moi-v1.1.md` |
| 2026-11-18 | Tạo file theo dõi tiến độ GĐ7                                                              | `docs/TIEN_DO_GD7.md`      |
| 2026-11-19 | Đánh dấu bước 2–9 hoàn thành; cập nhật file, test và nghiệm thu                        | `docs/TIEN_DO_GD7.md`      |

---

## 6. Nhật ký phiên làm việc

Ghi mỗi phiên một dòng (append, không xóa). Dùng cột `Test` để ghi lệnh/kết quả
kiểm thử chính của phiên.

| Ngày      | Bước     | Việc đã làm                                                                                                                        | File thay đổi                                                                                                                                                                     | Test                           | Kết quả                |
| ---------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------ |
| 2026-11-17 | Chuẩn bị | Xác định GĐ7 là bước tiếp theo sau GĐ9                                                                                        | `docs/HANDOFF.md`                                                                                                                                                                 | —                             | Ghi nhận                |
| 2026-11-18 | 0          | Đọc bản nháp, đối chiếu code, review 8 nhóm vấn đề                                                                          | `docs/Gui-ban-moi.md`                                                                                                                                                             | —                             | Có danh sách vấn đề |
| 2026-11-18 | 0          | Tạo đặc tả v1.1 với 16 quyết định                                                                                              | `docs/Gui-ban-moi-v1.1.md`                                                                                                                                                        | —                             | Hoàn thành             |
| 2026-11-18 | 0          | Áp dụng 5 góp ý + bổ sung Ctrl+R                                                                                                  | `docs/Gui-ban-moi-v1.1.md`                                                                                                                                                        | —                             | Hoàn thành             |
| 2026-11-18 | 0          | Tạo file theo dõi tiến độ                                                                                                         | `docs/TIEN_DO_GD7.md`                                                                                                                                                             | —                             | Hoàn thành             |
| 2026-11-18 | 0          | Bổ sung nhật ký, vấn đề, bảng file, test, nghiệm thu                                                                           | `docs/TIEN_DO_GD7.md`                                                                                                                                                             | —                             | Hoàn thành             |
| 2026-11-18 | 1          | Dựng khung cửa sổ, sidebar, panel Analysis, status bar, theme, 4 trang rỗng                                                        | `src/gui/main.py`, `main_window.py`, `styles.py`, `styles/theme.qss`, `widgets/sidebar.py`, `widgets/analysis_panel.py`, 4 file `pages/`, `tests/test_gui_smoke.py` | `pytest tests/` → 99 passed | Hoàn thành             |
| 2026-11-18 | 1          | Rà soát góp ý `Danh-gia-GUI.md`: sửa nền sidebar/panel, status bar dùng widget cố định, bỏ chữ tiến độ, thêm tooltip | `styles/theme.qss`, `widgets/sidebar.py`, `widgets/analysis_panel.py`, `main_window.py`, 4 file `pages/`, `tests/test_gui_smoke.py`                                     | `pytest tests/` → 99 passed | Hoàn thành             |
| 2026-11-19 | 2–5        | `AppState`, Home, Dataset, analytics, worker, Run/Run All, chart + replay                                                    | `src/gui/app_state.py`, `analytics.py`, `workers/`, `pages/`, `widgets/`                                                                                                      | `pytest tests/` → 122 passed | Hoàn thành             |
| 2026-11-19 | 6–7        | Comparison N=1, multi-seed N=3, 5 tab biểu đồ, nhận xét, ước lượng + xác nhận                                            | `pages/comparison_page.py`, `analytics.py`, `widgets/chart_widget.py`                                                                                                          | Thử tay N=1/N=3            | Hoàn thành             |
| 2026-11-19 | 8–9        | `session_store`, lịch sử, xuất CSV/JSON/PNG/HTML/PDF, test GUI, cập nhật tài liệu                                       | `session_store.py`, `widgets/analysis_panel.py`, `tests/test_gui_*`, `README.md`, `docs/*`                                                                                   | `pytest tests/` → 122 passed | Hoàn thành             |
| 2026-11-19 | 5–7        | Sửa bố cục kết quả: tab toàn chiều cao cho bảng/biểu đồ, tăng font chart, dialog sáng                                 | `pages/algorithm_page.py`, `pages/comparison_page.py`, `widgets/chart_widget.py`, `widgets/dialogs.py`, `styles/theme.qss`                                                     | `pytest tests/` → 123 passed | Hoàn thành             |
| 2026-11-19 | 3, 5, 6    | Chọn "(tất cả bài trong file)": Run All batch + Run Session lưu từng phiên                                          | `app_state.py`, `pages/dataset_page.py`, `pages/algorithm_page.py`, `pages/comparison_page.py`, `tests/test_gui_smoke.py`                                                          | `pytest tests/` → 127 passed | Hoàn thành             |

---

## 7. Vấn đề, blocker và quyết định

Các vấn đề đã phát hiện trong quá trình đặc tả đều đã được xử lý trong v1.1.
Nếu gặp vấn đề mới khi code, thêm dòng mới với ID tiếp theo.

| ID     | Ngày      | Vấn đề                                                                       | Ảnh hưởng                                                    | Cách xử lý / quyết định                                                                | Trạng thái                        |
| ------ | ---------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------- |
| GD7-01 | 2026-11-18 | Thư mục `results/sessions/gui/` nằm trong session của `src.experiments` | Có thể gây nhầm khi dùng `--session`                     | Chuyển sang `results/gui_sessions/`; ghi rõ `--session` không quét thư mục con     | Đã xử lý                        |
| GD7-02 | 2026-11-18 | Import `src.experiments.comparison` ép `matplotlib.use("Agg")`             | Phá canvas nhúng Qt                                           | Cấm import module này trong GUI; dùng `FigureCanvasQTAgg` trực tiếp                   | Đã xử lý                        |
| GD7-03 | 2026-11-18 | History 4 thuật toán khác schema và thang iteration                         | Biểu đồ chồng nhau dễ gây hiểu sai                       | Chuẩn hóa trục x về % tiến trình `i/(L-1)×100`; giữ chú thích                    | Đã xử lý                        |
| GD7-04 | 2026-11-18 | Thuật toán không có callback tiến độ                                     | Không thể hiển thị % tiến độ                             | Progress indeterminate + đồng hồ elapsed/remaining; Comparison tiến độ theo lượt     | Đã xử lý                        |
| GD7-05 | 2026-11-18 | `QThread` không hủy an toàn, không có nút Stop                          | Đóng app khi chạy có thể treo/mất dữ liệu               | Chặn thoát khi đang chạy; chỉ "Thu nhỏ" / "Tiếp tục chờ"; không `terminate()`    | Đã xử lý                        |
| GD7-06 | 2026-11-18 | `get_solver` không nhận alias `dp/ga/sa`                                  | Dễ gọi sai tên                                               | GUI map nhãn ngắn ↔ tên chuẩn; chỉ `get_solver` với tên chuẩn                     | Đã xử lý                        |
| GD7-07 | 2026-11-18 | Seed mặc định lệch (Algorithm 0, Comparison 1)                              | Kết quả khó tái lập, tài liệu mâu thuẫn                | Thống nhất 0; `config.SEED = 1..10` chỉ là mặc định benchmark                       | Đã xử lý                        |
| GD7-08 | 2026-11-18 | PDF cần thêm dependency                                                       | Tăng phạm vi cài đặt                                       | HTML bắt buộc; PDF tùy chọn bằng `QtPrintSupport` có sẵn                            | Đã xử lý                        |
| GD7-09 | 2026-11-18 | Chưa có test GUI, chưa có `pytest-qt`                                     | Khó kiểm chứng tự động                                    | Tách logic thuần vào `analytics.py`; smoke test offscreen, không thêm dependency      | Đã xử lý                        |
| GD7-10 | 2026-11-18 | DP có thể OOM hoặc vượt thời gian một chút                              | Số liệu so sánh có thể gây hiểu nhầm                    | Hiển thị đúng status/runtime thực tế, kèm nghiệm tốt nhất nếu có                 | Chấp nhận (giới hạn đã biết) |
| GD7-11 | 2026-11-18 | `QWidget` tự viết không vẽ nền QSS (thiếu `WA_StyledBackground`)      | Sidebar nền sáng + chữ sáng, gần như không đọc được | Bật `WA_StyledBackground` cho `Sidebar`/`AnalysisPanel`; thêm assert vào smoke test | Đã xử lý                        |
| GD7-12 | 2026-11-19 | Splitter dọc ép bảng kết quả chỉ còn vài dòng, biểu đồ hẹp/chữ mờ | Không đọc được 4 dòng so sánh, khó nhìn biểu đồ | Gom bảng + biểu đồ vào tab chiều cao đầy; bỏ min 220 của canvas, tăng font trục/tiêu đề | Đã xử lý                        |
| GD7-13 | 2026-11-19 | Nút phụ (Xuất/Xuất báo cáo/Run All/Reset) dùng style mặc định, nền tối lấn chữ | Khó đọc nhãn nút | Thêm rule `QPushButton` chung trong QSS: nền sáng/chữ tối/viền; sửa luôn màu chữ khi disabled | Đã xử lý                        |
| GD7-14 | 2026-11-19 | GUI chỉ commit từng bài, muốn chạy mọi bài trong dataset phải dùng CLI | Không tiện khi cần quét cả file | Thêm item "(tất cả bài trong file)"; Run All chạy batch, Run Session lưu từng phiên; nhãn bài hiện rõ chế độ batch | Đã xử lý                        |
| GD7-15 | 2026-11-19 | Chọn tất cả thì bảng lợi nhuận/ma trận/giới hạn để trống | Dễ tưởng dữ liệu bị mất | Thêm tab "Tổng hợp bài" + Analysis tóm tắt; giải thích mỗi bài có ma trận riêng | Đã xử lý                        |
|        |            |                                                                                 |                                                                 |                                                                                              |                                     |

**Blocker hiện tại:** không có.

---

## 8. Trạng thái file theo bước

Bảng dưới phản ánh trạng thái sau khi hoàn thành bước 9.

### 8.1. Điểm vào và khung ứng dụng

| File                         | Hiện tại      | Hành động                                    | Bước | Trạng thái |
| ---------------------------- | --------------- | ----------------------------------------------- | ------ | ------------ |
| `src/gui/main.py`          | Đã tạo       | QApplication + theme + MainWindow               | 1      | Hoàn thành |
| `src/gui/main_window.py`   | Đã viết      | 3 vùng, sidebar, stack, status bar, closeEvent | 1      | Hoàn thành |
| `src/gui/styles.py`        | Đã viết      | Loader QSS theo `Path(__file__)` + fallback   | 1      | Hoàn thành |
| `src/gui/styles/theme.qss` | Đã tạo       | Theme duy nhất                                 | 1      | Hoàn thành |
| `src/gui/app_state.py`     | Đã tạo       | `AppState(QObject)` + signal + commit bài   | 2      | Hoàn thành |

### 8.2. Trang

| File                                 | Hiện tại  | Hành động                                         | Bước | Trạng thái |
| ------------------------------------ | ----------- | ---------------------------------------------------- | ------ | ------------ |
| `src/gui/pages/home_page.py`       | Đã viết     | Giới thiệu, 4 thẻ, nút điều hướng            | 2      | Hoàn thành |
| `src/gui/pages/dataset_page.py`    | Đã viết     | Chọn file/bài, 3 bảng, commit bài                | 3      | Hoàn thành |
| `src/gui/pages/algorithm_page.py`  | Đã viết     | Run, Run All, Reset, kết quả, hội tụ, phát lại | 4–5   | Hoàn thành |
| `src/gui/pages/comparison_page.py` | Đã viết     | Session, bảng, biểu đồ, nhận xét, lịch sử    | 6–8   | Hoàn thành |

### 8.3. Widget và worker

| File                                    | Hiện tại | Hành động                            | Bước | Trạng thái |
| --------------------------------------- | ---------- | --------------------------------------- | ------ | ------------ |
| `src/gui/widgets/sidebar.py`          | Đã viết | 4 nút + nhãn bài toán               | 1      | Hoàn thành |
| `src/gui/widgets/analysis_panel.py`   | Đã viết    | Panel phải: log, nhận xét, lịch sử | 1–8   | Hoàn thành |
| `src/gui/widgets/data_table.py`       | Đã viết    | `ArrayTableModel` + view dùng lại   | 3      | Hoàn thành |
| `src/gui/widgets/control_panel.py`    | Đã viết    | Điều khiển chạy/tham số            | 4      | Hoàn thành |
| `src/gui/widgets/result_panel.py`     | Đã viết    | Bảng kết quả + chi tiết 1 lượt     | 4–6   | Hoàn thành |
| `src/gui/widgets/chart_widget.py`     | Đã viết    | `FigureCanvasQTAgg`, bars/overlay/replay | 4–7   | Hoàn thành |
| `src/gui/workers/algorithm_worker.py` | Đã viết    | `AlgorithmWorker` + `SessionWorker` | 4–6   | Hoàn thành |

### 8.4. Logic thuần, lưu trữ, test, tài liệu

| File                                | Hiện tại            | Hành động                                | Bước | Trạng thái |
| ----------------------------------- | --------------------- | ------------------------------------------- | ------ | ------------ |
| `src/gui/analytics.py`            | Đã tạo             | Thống kê, history, nhận xét (không Qt) | 4–7   | Hoàn thành |
| `src/gui/session_store.py`        | Đã tạo             | Lưu/đọc/xóa/xuất phiên                | 8      | Hoàn thành |
| `tests/test_gui_analytics.py`     | Đã tạo (12)        | Test logic thuần                           | 9      | Hoàn thành |
| `tests/test_gui_session_store.py` | Đã tạo (5)         | Test lưu/đọc/xuất                       | 9      | Hoàn thành |
| `tests/test_gui_smoke.py`         | Đã tạo (15)        | Smoke test Qt offscreen + batch Algorithm/Comparison | 1, 9   | Hoàn thành |
| `README.md`                       | Đã cập nhật       | Trạng thái + cách chạy GUI             | 9      | Hoàn thành |
| `docs/HUONG_DAN_TEST.md`          | Đã cập nhật       | Điểm vào GUI + test mới                | 9      | Hoàn thành |
| `docs/HANDOFF.md`                 | Đã cập nhật       | Ghi đè trạng thái cuối GĐ7            | 9      | Hoàn thành |
| `docs/LOG.md`                     | Đã cập nhật       | Append nhật ký GĐ7                       | 9      | Hoàn thành |

**Quy ước:** không sửa `src/core/`, `src/algorithms/`, `run_algo.py`,
`benchmark_algo.py`, `src/experiments/` và test cũ.

---

## 9. Kết quả kiểm thử theo mốc

### 9.1. Baseline trước GĐ7

| Ngày      | Lệnh                       | Kết quả                | Ghi chú                                                              |
| ---------- | --------------------------- | ------------------------ | --------------------------------------------------------------------- |
| 2026-11-17 | `python -m pytest tests/` | 94 passed (theo HANDOFF) | Xác nhận gián tiếp: sau khi thêm 5 test GUI, tổng là 99 passed |

### 9.2. Log kiểm thử trong GĐ7

| Ngày      | Bước | Lệnh / nội dung                               | Kết quả | Ghi chú                          |
| ---------- | ------ | ----------------------------------------------- | --------- | --------------------------------- |
| 2026-11-18 | 1      | `python -m pytest tests/test_gui_smoke.py -v` | 5 passed  | Offscreen, không cần màn hình |
| 2026-11-18 | 1      | `python -m pytest tests/`                     | 99 passed | 94 test cũ + 5 test GUI mới     |
| 2026-11-19 | 2–9    | `pytest tests/test_gui_analytics.py`          | 13 passed | Logic thuần, không cần Qt        |
| 2026-11-19 | 8      | `pytest tests/test_gui_session_store.py`      | 5 passed  | Lưu/đọc/xóa/xuất, atomic         |
| 2026-11-19 | 2–9    | `pytest tests/test_gui_smoke.py`              | 15 passed | Offscreen: 4 trang + batch Algorithm/Comparison + thread Run |
| 2026-11-19 | 2–9    | `python -m pytest tests/`                     | 127 passed | 94 cũ + 5 GUI + 28 GUI mới      |

### 9.3. Lệnh kiểm thử sẽ dùng

```powershell
# Test toàn bộ (bắt buộc sau mỗi bước)
python -m pytest tests/

# Test riêng phần GUI
python -m pytest tests/test_gui_analytics.py -v
python -m pytest tests/test_gui_session_store.py -v
python -m pytest tests/test_gui_smoke.py -v

# Smoke test Qt không cần màn hình
$env:QT_QPA_PLATFORM="offscreen"; python -m pytest tests/test_gui_smoke.py -v

# Chạy ứng dụng
python -m src.gui.main
```

### 9.4. Kiểm tra thủ công (điền kết quả vào bảng)

| #  | Nội dung                  | Kỳ vọng                                                                  | Kết quả       |
| -- | -------------------------- | -------------------------------------------------------------------------- | --------------- |
| 1  | Mở app                    | Cửa sổ 1280×800, 4 trang                                                | Đạt (offscreen) |
| 2  | Ctrl+1..4                  | Chuyển đúng trang                                                       | Chưa kiểm tra |
| 3  | Dataset n=500              | Cuộn mượt, đúng dữ liệu                                             | Đạt (model)   |
| 4  | Run từng thuật toán     | Có kết quả, không treo                                                 | Đạt (greedy)  |
| 5  | Time Limit = 1 với GA/SA  | Status `timeout`, có nghiệm tốt nhất                                 | Đạt (0.3s)    |
| 6  | DP bài lớn               | Status `out_of_memory` hoặc `ok`, không crash                        | Chưa kiểm tra |
| 7  | Run All                    | Bảng 4 dòng + hội tụ chồng nhau, không lưu phiên                   | Đạt           |
| 8  | Run Session N=1            | Bảng/biểu đồ/nhận xét đúng                                         | Đạt           |
| 9  | Run Session N=3            | Thống kê best/avg/worst/std, tổng lượt đúng                         | Đạt           |
| 10 | Lưu phiên                | Đủ `session.json`, `comparison.csv`, `chart.png`, `nhan_xet.txt` | Đạt           |
| 11 | Mở lại phiên            | Banner "đã lưu ngày…", không trộn phiên mới                       | Chưa kiểm tra |
| 12 | Xóa phiên                | Xác nhận rồi xóa thư mục                                             | Chưa kiểm tra |
| 13 | Xuất CSV/JSON/PNG/HTML    | Mở được, tiếng Việt đúng                                           | Đạt (test)    |
| 14 | Đóng app khi đang chạy | Không thoát; chỉ thu nhỏ/tiếp tục chờ                               | Chưa kiểm tra |
| 15 | Lỗi ghi file              | Báo lỗi, kết quả vẫn hiển thị                                       | Chưa kiểm tra |

---

## 10. Checklist nghiệm thu GĐ7

Chỉ đánh dấu GĐ7 hoàn thành khi tất cả mục dưới đây đạt.

### 10.1. Chức năng

- [X] Mở app bằng `python -m src.gui.main`, bố cục 3 khu vực, theme thống nhất
- [X] Chuyển 4 trang bằng sidebar và `Ctrl+1..4`
- [X] Dataset: chọn file/bài, xem 3 bảng, tightness, commit bài hoặc "(tất cả bài trong file)"
- [X] Algorithm: Run 1 thuật toán, kết quả đầy đủ, hội tụ + phát lại
- [X] Run All: bảng 4 dòng + hội tụ chồng nhau, không lưu phiên; batch 4 × mọi bài
- [X] Comparison: Run Session N=1 và N=3, bảng/biểu đồ/nhận xét; batch lưu từng phiên
- [X] Lịch sử: lưu tự động, mở lại, xóa, mở thư mục
- [X] Xuất CSV/JSON/PNG/HTML (PDF tùy chọn)

### 10.2. Đúng đặc tả

- [X] Chỉ hiển thị status thật; thiếu dữ liệu dùng `-`
- [X] Không đọc chéo session của experiments; lưu ở `results/gui_sessions/`
- [X] Biểu đồ chồng dùng trục % tiến trình + chú thích đơn vị history
- [X] Multi-seed đúng `s..s+N-1`; Greedy/DP 1 lượt, `-` ở thống kê
- [X] Nhận xét tự động dựa trên số liệu, tách early/time-limited
- [X] Ctrl+R đi qua xác nhận > 2 phút
- [X] Không đóng app khi đang chạy

### 10.3. Kỹ thuật

- [X] `python -m pytest tests/` xanh, 94 test cũ không đổi
- [X] Test GUI mới pass
- [X] Smoke test offscreen pass
- [X] Không sửa core/algorithms/experiments/CLI/test cũ
- [X] Không thêm dependency ngoài PySide6/matplotlib/numpy
- [X] Không import `src.experiments.comparison` trong GUI

### 10.4. Tài liệu

- [X] `README.md` cập nhật trạng thái + cách chạy GUI
- [X] `docs/HUONG_DAN_TEST.md` có lệnh GUI
- [X] `docs/HANDOFF.md` và `docs/LOG.md` cập nhật
- [X] File này: tất cả bước 1–9 = Hoàn thành, nhật ký đầy đủ

---

## 11. Mẫu ghi khi hoàn thành một bước

```
### Bước N — <tên> (Hoàn thành)

**Đã làm / Đã chỉnh**
- YYYY-MM-DD: <việc đã làm, file đã sửa, quyết định thay đổi so với đặc tả>
- YYYY-MM-DD: <lỗi gặp phải và cách xử lý>
- Test: `python -m pytest tests/` → <kết quả>
```

Nếu phải lệch khỏi đặc tả: ghi rõ lý do tại đây **và** cập nhật
`docs/Gui-ban-moi-v1.1.md` để hai tài liệu không mâu thuẫn.
