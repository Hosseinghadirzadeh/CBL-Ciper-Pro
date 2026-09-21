from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(int)
    finished = Signal()


class Worker(QRunnable):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function, self.args, self.kwargs = function, args, kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            self.kwargs["progress"] = self.signals.progress.emit
            self.signals.result.emit(self.function(*self.args, **self.kwargs))
        except Exception as exc:
            self.signals.error.emit(str(exc) or exc.__class__.__name__)
        finally:
            self.signals.finished.emit()

