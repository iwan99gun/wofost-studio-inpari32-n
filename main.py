"""Entry point WOFOST Studio.

Jalankan:  python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# pastikan paket dapat diimpor walau dijalankan dari folder lain
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("WOFOST Studio")
    app.setStyle("Fusion")
    from wofost_app.ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
