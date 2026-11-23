import sys

from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .styles import load_stylesheet


def main(argv=None) -> int:
    app = QApplication.instance() or QApplication(
        argv if argv is not None else sys.argv
    )
    app.setApplicationName("MKP-BIG4")
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
