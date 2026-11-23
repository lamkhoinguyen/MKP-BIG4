from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    PAGE_TITLE = "Trang chủ"
    ANALYSIS_HTML = """
    <p><b>Luồng sử dụng</b></p>
    <ol>
      <li>Chọn dữ liệu ở trang <b>Dataset</b>.</li>
      <li>Chạy thuật toán ở trang <b>Algorithm</b>.</li>
      <li>So sánh 4 thuật toán ở trang <b>Comparison</b>.</li>
    </ol>
    <p>Trang chủ giới thiệu bài toán MKP và 4 thuật toán.</p>
    """

    navigate_requested = Signal(int)

    ALGORITHM_CARDS = (
        (
            "Greedy",
            "Chọn hàng theo tỷ lệ lợi nhuận/tài nguyên, thích nghi theo tài "
            "nguyên còn lại.",
            "Nhanh, đơn giản · Chất lượng phụ thuộc thứ tự chọn.",
        ),
        (
            "Dynamic Programming",
            "Quy hoạch động theo tầng trạng thái tài nguyên.",
            "Nghiệm tốt, tất định · Tốn bộ nhớ với bài lớn.",
        ),
        (
            "Genetic Algorithm",
            "Tiến hóa quần thể lời giải qua chọn lọc, lai ghép, đột biến.",
            "Chất lượng cao · Phụ thuộc seed, dùng hết thời gian.",
        ),
        (
            "Simulated Annealing",
            "Duyệt lời giải lân cận với xác suất chấp nhận giảm dần.",
            "Cân bằng khám phá/khai thác · Phụ thuộc seed.",
        ),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel(self.PAGE_TITLE)
        title.setObjectName("PageTitle")
        hint = QLabel(
            "Bài toán chọn hàng vận chuyển (Multidimensional Knapsack Problem): "
            "chọn tập vật phẩm tối đa hóa lợi nhuận dưới nhiều giới hạn tài nguyên."
        )
        hint.setObjectName("PageHint")
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)

        formula = QFrame()
        formula.setObjectName("Card")
        formula_layout = QVBoxLayout(formula)
        formula_layout.setContentsMargins(16, 12, 16, 12)
        formula_layout.setSpacing(4)
        formula_title = QLabel("Mô hình toán học")
        formula_title.setObjectName("CardTitle")
        formula_text = QLabel(
            "max  Σ p_j · x_j\n"
            "với  Σ r_ij · x_j ≤ b_i  (mọi tài nguyên i)   và   x_j ∈ {0, 1}"
        )
        formula_text.setObjectName("Formula")
        formula_layout.addWidget(formula_title)
        formula_layout.addWidget(formula_text)
        layout.addWidget(formula)

        cards_title = QLabel("4 thuật toán")
        cards_title.setObjectName("SectionTitle")
        layout.addWidget(cards_title)

        grid = QGridLayout()
        grid.setSpacing(10)
        for index, (name, description, tradeoff) in enumerate(self.ALGORITHM_CARDS):
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)
            card_title = QLabel(name)
            card_title.setObjectName("CardTitle")
            card_description = QLabel(description)
            card_description.setObjectName("CardText")
            card_description.setWordWrap(True)
            card_tradeoff = QLabel(tradeoff)
            card_tradeoff.setObjectName("CardMuted")
            card_tradeoff.setWordWrap(True)
            card_layout.addWidget(card_title)
            card_layout.addWidget(card_description)
            card_layout.addWidget(card_tradeoff)
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)

        data_info = QLabel(
            "Bộ dữ liệu OR-Library có sẵn: 11 file, 325 bài; n = 6..500, m ≤ 30. "
            "Toàn bộ 4 thuật toán dùng chung một mô hình và một định dạng dữ liệu."
        )
        data_info.setObjectName("PageHint")
        data_info.setWordWrap(True)
        layout.addWidget(data_info)
        layout.addStretch(1)

        buttons = QGridLayout()
        buttons.setSpacing(8)
        for column, (text, page) in enumerate(
            (
                ("1. Chọn dữ liệu", 1),
                ("2. Chạy thuật toán", 2),
                ("3. So sánh", 3),
            )
        ):
            button = QPushButton(text)
            button.setObjectName("PrimaryButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(
                lambda _=False, target=page: self.navigate_requested.emit(target)
            )
            buttons.addWidget(button, 0, column)
        layout.addLayout(buttons)

    def run_primary_action(self) -> None:
        self.navigate_requested.emit(1)
