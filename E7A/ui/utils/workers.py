import traceback

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot, QThread


class ThreadWorker(QThread):
    """
    A worker class to run a task in a separate thread using QThreadPool.
    """
    class WorkerSignals(QObject):
        finished_signal = pyqtSignal()
        error_signal = pyqtSignal(str)
        result_signal = pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._stop_mark = False
        self._signals = self.WorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Run the task and emit signals based on the result.
        """
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            traceback.print_exc()
            self.error_signal.emit(str(e))
        else:
            self.result_signal.emit(result)
        finally:
            self.finished_signal.emit()

    def stop(self):
        self._stop_mark = True

    @property
    def finished_signal(self):
        return self._signals.finished_signal

    @property
    def error_signal(self):
        return self._signals.error_signal

    @property
    def result_signal(self):
        return self._signals.result_signal

    @property
    def stop_mark(self):
        return self._stop_mark


class RunnableWorker(QRunnable):
    """
    A worker class to run a task in a separate thread using QThreadPool.
    """

    class RunnableWorkerSignals(QObject):
        finished_signal = pyqtSignal()
        error_signal = pyqtSignal(str)
        result_signal = pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._is_running = False
        self.signals = self.RunnableWorkerSignals()

    def stop(self):
        self._is_running = False

    @pyqtSlot()
    def run(self):
        """
        Run the task and emit signals based on the result.
        """
        self._is_running = True
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            traceback.print_exc()
            self.signals.error_signal.emit(str(e))
        else:
            self.signals.result_signal.emit(result)
        finally:
            self.signals.finished_signal.emit()

    @property
    def is_running(self):
        return self._is_running
