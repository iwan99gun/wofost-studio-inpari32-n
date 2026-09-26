"""Worker thread generik agar simulasi/analisis tidak membekukan UI."""
from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Menjalankan `fn(progress, cancelled, *args, **kwargs)` di thread terpisah.

    `progress(i, n, pesan)` boleh dipanggil dari fn; `cancelled()` mengembalikan True
    bila pengguna menekan Batal.
    """

    progress = Signal(int, int, str)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def is_cancelled(self) -> bool:
        return self._cancel

    def run(self) -> None:  # noqa: D401
        try:
            result = self._fn(self._emit_progress, self.is_cancelled, *self._args, **self._kwargs)
        except InterruptedError as e:
            self.failed.emit(f"Dibatalkan: {e}")
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"{type(e).__name__}: {e}\n\n{traceback.format_exc(limit=6)}")
        else:
            self.finished_ok.emit(result)

    def _emit_progress(self, i: int, n: int, msg: str = "") -> None:
        self.progress.emit(int(i), int(n), str(msg))
