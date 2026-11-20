from pathlib import Path
import logging

logger = logging.getLogger(__name__)

FALLBACK_STYLESHEET = """
QMainWindow, QWidget { background: #f1f5f9; color: #1f2937; }
QPushButton { padding: 8px 12px; border-radius: 8px; }
"""


def stylesheet_path() -> Path:
    return Path(__file__).resolve().parent / "styles" / "theme.qss"


def load_stylesheet() -> str:
    path = stylesheet_path()
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Khong doc duoc theme QSS %s: %s", path, exc)
        return FALLBACK_STYLESHEET
