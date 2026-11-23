from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class AnalysisPanel(QWidget):
    history_open_requested = Signal(str)
    history_delete_requested = Signal(str)
    history_folder_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AnalysisPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(260)
        self.setMaximumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(8)

        eyebrow = QLabel("PHÂN TÍCH")
        eyebrow.setObjectName("AnalysisEyebrow")

        self.title_label = QLabel("Hướng dẫn")
        self.title_label.setObjectName("AnalysisTitle")
        self.title_label.setWordWrap(True)

        self.body = QTextBrowser()
        self.body.setObjectName("AnalysisBody")
        self.body.setOpenExternalLinks(False)

        layout.addWidget(eyebrow)
        layout.addWidget(self.title_label)
        layout.addWidget(self.body, 1)

        self.history_box = self._build_history_box()
        self.history_box.setVisible(False)
        layout.addWidget(self.history_box)

    def _build_history_box(self) -> QWidget:
        box = QFrame()
        box.setObjectName("HistoryCard")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 8, 10, 10)
        box_layout.setSpacing(6)

        caption = QLabel("Lịch sử phiên")
        caption.setObjectName("CardTitle")
        box_layout.addWidget(caption)

        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setMaximumHeight(150)
        self.history_list.itemActivated.connect(self._open_item)
        self.history_list.itemDoubleClicked.connect(self._open_item)
        box_layout.addWidget(self.history_list)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        open_button = QPushButton("Mở")
        open_button.clicked.connect(self._open_selected)
        delete_button = QPushButton("Xóa")
        delete_button.clicked.connect(self._delete_selected)
        folder_button = QPushButton("Mở thư mục")
        folder_button.clicked.connect(self.history_folder_requested.emit)
        for button in (open_button, delete_button, folder_button):
            button.setObjectName("SmallButton")
            buttons.addWidget(button)
        box_layout.addLayout(buttons)
        return box

    # ------------------------------------------------------------------
    def set_content(self, title: str, html: str) -> None:
        self.title_label.setText(title)
        self.body.setHtml(html)

    def set_history(self, items: list) -> None:
        self.history_list.clear()
        if not items:
            item = QListWidgetItem("(chưa có phiên)")
            item.setFlags(Qt.NoItemFlags)
            self.history_list.addItem(item)
        else:
            for entry in items:
                label = entry.get("label") or entry.get("created_at", "-")
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, entry.get("path", ""))
                item.setToolTip(entry.get("path", ""))
                self.history_list.addItem(item)
        self.history_box.setVisible(True)

    def hide_history(self) -> None:
        self.history_box.setVisible(False)

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            self.history_open_requested.emit(path)

    def _open_selected(self) -> None:
        item = self.history_list.currentItem()
        if item is not None:
            self._open_item(item)

    def _delete_selected(self) -> None:
        item = self.history_list.currentItem()
        if item is None:
            return
        path = item.data(Qt.UserRole)
        if path:
            self.history_delete_requested.emit(path)
