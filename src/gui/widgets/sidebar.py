from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    page_selected = Signal(int)

    PAGE_LABELS = ("Home", "Dataset", "Algorithm", "Comparison")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(6)

        brand = QLabel("MKP-BIG4")
        brand.setObjectName("BrandTitle")
        subtitle = QLabel("Phân tích 4 thuật toán")
        subtitle.setObjectName("BrandSub")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = []

        for index, label in enumerate(self.PAGE_LABELS):
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(f"Ctrl+{index + 1}")
            self.group.addButton(button, index)
            layout.addWidget(button)
            self.buttons.append(button)

        self.group.idClicked.connect(self.page_selected.emit)
        self.buttons[0].setChecked(True)

        layout.addStretch(1)

        badge_title = QLabel("BÀI TOÁN ĐANG CHỌN")
        badge_title.setObjectName("SidebarCaption")
        self.problem_label = QLabel("Chưa chọn bài toán")
        self.problem_label.setObjectName("ProblemBadge")
        self.problem_label.setWordWrap(True)

        layout.addWidget(badge_title)
        layout.addWidget(self.problem_label)

    def set_current(self, index: int) -> None:
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)

    def set_problem_text(self, text: str) -> None:
        self.problem_label.setText(text)
