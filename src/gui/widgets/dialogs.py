"""Hộp thoại dùng chung, nút tiếng Việt và theo theme của ứng dụng."""

from PySide6.QtWidgets import QMessageBox


def ask_confirm(
    parent,
    title: str,
    text: str,
    *,
    accept: str = "Tiếp tục",
    reject: str = "Hủy",
    icon=QMessageBox.Question,
) -> bool:
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    accept_button = box.addButton(accept, QMessageBox.AcceptRole)
    reject_button = box.addButton(reject, QMessageBox.RejectRole)
    accept_button.setObjectName("PrimaryButton")
    reject_button.setObjectName("SmallButton")
    for button in (accept_button, reject_button):
        button.style().unpolish(button)
        button.style().polish(button)
    box.setDefaultButton(reject_button)
    box.setEscapeButton(reject_button)
    box.exec()
    return box.clickedButton() is accept_button
