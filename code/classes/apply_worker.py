from PyQt5.QtCore import QThread, pyqtSignal


class ApplyWorker(QThread):
    """Runs WorldManager.apply_changes() off the main thread.

    Connect ``finished`` and ``errored`` before calling ``start()``.
    The caller must keep a reference to the worker (e.g. ``self._worker``)
    until the signal is received; otherwise Python may GC it mid-run.
    """

    finished = pyqtSignal(list)   # list of (name, error_msg) tuples
    errored  = pyqtSignal(str)    # exception message

    def __init__(self, world_manager, parent=None):
        super().__init__(parent)
        self.world_manager = world_manager

    def run(self):
        try:
            errors = self.world_manager.apply_changes()
            self.finished.emit(errors)
        except Exception as exc:
            self.errored.emit(str(exc))
