import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from app.main_window import MainWindow
from app.styles.dark_theme import DARK_THEME


def _base_dir() -> str:
    """Works both in dev (script) and PyInstaller one-file mode."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def main():
    # DPI awareness for sharp UI on high-res screens
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("SystemAnalyzer")
    app.setApplicationDisplayName("System Analyzer")
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # App icon (window title bar + taskbar)
    icon_path = os.path.join(_base_dir(), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
