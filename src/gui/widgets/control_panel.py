"""Khung điều khiển/tham số dùng lại ở trang Algorithm và Comparison."""

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class ControlPanel(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        if title:
            layout.addWidget(self.title_label)

        self.form = QFormLayout()
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setHorizontalSpacing(14)
        self.form.setVerticalSpacing(8)
        layout.addLayout(self.form)

        self._buttons = QHBoxLayout()
        self._buttons.setSpacing(8)
        self._buttons_added = False
        self._layout = layout

    def add_row(self, label: str, widget: QWidget) -> QWidget:
        caption = QLabel(label)
        caption.setObjectName("FieldLabel")
        self.form.addRow(caption, widget)
        return widget

    def add_full(self, widget: QWidget) -> QWidget:
        self.form.addRow(widget)
        return widget

    def add_buttons(self, *buttons: QWidget) -> None:
        if not self._buttons_added:
            self._layout.addLayout(self._buttons)
            self._buttons_added = True
        for button in buttons:
            self._buttons.addWidget(button)

    def add_note(self, text: str) -> QLabel:
        note = QLabel(text)
        note.setObjectName("FieldNote")
        note.setWordWrap(True)
        self._layout.addWidget(note)
        return note

    def add_extra(self, widget: QWidget) -> QWidget:
        self._layout.addWidget(widget)
        return widget
