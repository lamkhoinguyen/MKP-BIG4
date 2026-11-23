# Đánh giá giao diện GUI hiện tại và yêu cầu chỉnh sửa (GĐ7 - bước 1)

Phạm vi: khung cửa sổ chính (sidebar, nội dung, panel Analysis, thanh trạng thái) đang hiển thị trang Comparison. Nội dung trang còn trống là đúng với tiến độ hiện tại nên không tính là nhược điểm.

## 1. Đánh giá

### 1.1. Ưu điểm

- Bố cục đúng thiết kế: Sidebar trái, nội dung giữa, panel Analysis phải, thanh trạng thái dưới cùng.
- Phối màu nhất quán: nền xanh xám nhạt, màu nhấn xanh dương.
- Mục đang chọn (Comparison) nổi bật, dễ nhận ra.
- Tiêu đề trang rõ, tiếng Việt hiển thị đúng dấu.
- Panel phải là thẻ trắng bo góc, nhìn gọn.
- Khu "Bài toán đang chọn" ở góc dưới sidebar cho biết ngay trạng thái `Chưa chọn bài toán`.

### 1.2. Nhược điểm

| # | Nhược điểm | Mức độ |
|---|---|---|
| 1 | **Sidebar khó đọc:** logo "MKP-BIG4" màu trắng trên nền sáng gần như không thấy; các mục Home, Dataset, Algorithm màu xám rất nhạt trên nền sáng, độ tương phản quá thấp. Chỉ mục đang chọn đọc rõ. | Cao |
| 2 | **Thanh trạng thái không đồng bộ với giao diện:** nền trắng, chữ mặc định, trông như phần ngoài ứng dụng. | Trung bình |
| 3 | **Câu giữ chỗ lộ chữ nội bộ:** "hoàn thiện ở bước 6-8" xuất hiện ở cả khu giữa và panel phải. | Trung bình |
| 4 | **Thanh tiêu đề hệ điều hành màu tối,** không hợp với nền sáng của ứng dụng. | Thấp |
| 5 | **Chi tiết nhỏ:** mục chưa chọn không có dấu hiệu bấm được; nhãn "BÀI TOÁN ĐANG CHỌN" nhạt và nhỏ. | Thấp |

Ghi chú nguyên nhân có thể có của nhược điểm 1 (cần kiểm tra trong code, chưa xác nhận): sidebar được thiết kế nền tối với chữ sáng nhưng nền chưa được áp dụng. Với widget tự viết trong Qt, lỗi thường gặp là thiếu `setAttribute(Qt.WA_StyledBackground, True)` hoặc `objectName` chưa khớp với selector trong QSS.

## 2. Yêu cầu chỉnh sửa

Nội dung dưới đây dùng để giao cho người/AI chỉnh code. Chỉ sửa giao diện của khung hiện có, không thêm chức năng mới.

### 2.1. Ràng buộc chung

- Không sửa `src/core/`, `src/algorithms/`, `src/experiments/`, `run_algo.py`, `benchmark_algo.py` và các test cũ.
- Không đổi cấu trúc file đã chốt trong đặc tả GUI. Chỉ sửa trong `src/gui/` (chủ yếu `styles/theme.qss`, `widgets/sidebar.py`, `main_window.py`, các trang giữ chỗ).
- Không thêm thư viện mới.
- Sau khi sửa, 94 test cũ vẫn pass và smoke test GUI vẫn pass.

### 2.2. Yêu cầu 1 - Sidebar đọc rõ (ưu tiên cao)

Làm cho chữ ở sidebar đọc rõ trong mọi trạng thái. Chọn **một** hướng và áp dụng nhất quán:

- **Hướng A (khuyến nghị):** sidebar nền tối (ví dụ xanh navy đậm), chữ sáng. Logo và dòng phụ "Phân tích 4 thuật toán" màu sáng; mục chưa chọn màu sáng dịu; mục đang chọn giữ nền xanh dương, chữ trắng.
- **Hướng B:** giữ sidebar nền sáng, đổi chữ sang màu tối: logo và mục chưa chọn màu xanh đen/xám đậm.

Tiêu chí nghiệm thu:
- Logo "MKP-BIG4", dòng phụ và 3 mục chưa chọn đều đọc rõ bằng mắt thường.
- Tỷ lệ tương phản chữ/nền tối thiểu 4.5:1 (theo chuẩn WCAG AA) cho chữ thường.
- Có trạng thái **hover** cho mục chưa chọn (đổi nền nhẹ) và con trỏ dạng bàn tay.
- Khu "BÀI TOÁN ĐANG CHỌN" ở dưới cùng cũng đọc rõ trên nền sidebar mới.
- Nếu nguyên nhân là nền không được áp dụng thì sửa đúng nguyên nhân (đặt `WA_StyledBackground` / `objectName` khớp QSS), không chồng thêm màu tạm thời.

### 2.3. Yêu cầu 2 - Thanh trạng thái đồng bộ theme

- Dùng chung bảng màu với giao diện: nền xám nhạt hoặc trắng viền trên mảnh, chữ nhỏ hơn và màu xám đậm dễ đọc.
- Nội dung: chia vùng (bài toán hiện tại, trạng thái chạy), có thể để trống từng vùng khi chưa có dữ liệu. Không thêm đồng hồ hay chức năng mới ở bước này.
- Thay chữ "Trang hiện tại: Comparison" bằng nội dung ngắn gọn, nhất quán với vùng hiển thị đã chia.

Tiêu chí nghiệm thu: thanh trạng thái nhìn cùng một hệ giao diện với sidebar và panel phải; chữ đọc rõ.

### 2.4. Yêu cầu 3 - Bỏ chữ nội bộ ở nội dung giữ chỗ

- Xóa mọi cụm như "hoàn thiện ở bước 6-8", "bước N" khỏi giao diện người dùng, ở cả khu giữa và panel Analysis của 4 trang.
- Thay bằng câu hướng dẫn trung tính, ví dụ:
  - Comparison: "Chọn bài toán ở trang Dataset, sau đó chạy phiên so sánh."
  - Algorithm: "Chọn bài toán ở trang Dataset để bắt đầu."
  - Dataset: "Chọn file dataset và bài toán để xem dữ liệu."
  - Home: giữ phần giới thiệu.
- Panel Analysis mỗi trang chỉ mô tả mục đích của trang, không nhắc tiến độ phát triển.

Tiêu chí nghiệm thu: tìm trong `src/gui/` không còn chuỗi "bước" kiểu tiến độ trong văn bản hiển thị cho người dùng.

### 2.5. Yêu cầu 4 - Thanh tiêu đề hệ điều hành (ưu tiên thấp)

- Không bắt buộc sửa. Nếu muốn đồng bộ, có thể giữ khung hệ điều hành và chấp nhận khác màu; chỉ làm khung tự vẽ khi chắc chắn không ảnh hưởng thu nhỏ/phóng to/đóng cửa sổ.
- Mặc định: **bỏ qua yêu cầu này**.

### 2.6. Yêu cầu 5 - Chi tiết nhỏ

- Mục sidebar chưa chọn: có nền hover và vùng bấm rõ (đã gộp ở 2.2).
- Nhãn "BÀI TOÁN ĐANG CHỌN": tăng độ tương phản và cỡ chữ một chút cho đọc được.
- Tooltip cho 4 mục sidebar hiển thị phím tắt (`Ctrl+1` đến `Ctrl+4`), nếu phím tắt đã được cài.

### 2.7. Kiểm tra sau khi sửa

1. Chạy `python -m src.gui.main`: mở cửa sổ, chuyển 4 trang bằng chuột và `Ctrl+1..4`.
2. Chụp ảnh màn hình sidebar ở cả trạng thái bình thường, hover và đang chọn để đối chiếu.
3. Chạy `python -m pytest tests/`: toàn bộ test cũ pass, smoke test GUI pass.
4. Xác nhận không có file ngoài `src/gui/` bị thay đổi (`git status`).
