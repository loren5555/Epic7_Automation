import sys
import traceback
from datetime import time

import cv2
import scrcpy
import time
from numpy import ndarray
from adbutils import adb
from typing import Optional
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, pyqtSlot, QThreadPool, QRunnable, QObject, \
    pyqtSignal
from PyQt6.QtGui import QPixmap, QImage


from E7A.ui.ui_screenshot_window_Qt_generated import Ui_UIScreenshotWindow
from E7A.emulator import MuMuEmulator
from E7A.common.logger import Logger
from E7A.common.config import Config


class UIScreenshotWindow(QMainWindow, Ui_UIScreenshotWindow):
    on_frame_signal = pyqtSignal(object)  # Signal for updating scrcpy frame.

    def __init__(
            self,
            emulator: MuMuEmulator,
            logger: Logger,
            parent=None
    ):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.logger: Logger = logger.get_child_logger("UIScreenshotWindow")
        self.emulator: MuMuEmulator = emulator
        self.screenshot = None

        self.screenshot_scene = QGraphicsScene()
        self.screenshot_view.setScene(self.screenshot_scene)

        self.screenshot_item = QGraphicsPixmapItem()
        self.screenshot_scene.addItem(self.screenshot_item)

        adb.connect(Config.emulator.adb_address)
        self.scrcpy_client = scrcpy.Client()
        self.scrcpy_client.add_listener(scrcpy.EVENT_FRAME, self.on_frame)

        self.threadpool = QThreadPool()

        self.setup_connections()

    def setup_connections(self):
        """
        Set up signal-slot connections for UI actions.
        """
        self.update_screenshot_action.triggered.connect(self.update_screenshot)
        self.toggle_scrcpy_action.toggled.connect(self.track_screen)
        self.on_frame_signal.connect(self.update_frame)

    @pyqtSlot()
    def update_screenshot(self):
        state, info = self.emulator.get_screenshot_adb(
            file_name=Config.ui.screenshot_file_name,
            save_dir_windows=Config.ui.screenshot_save_dir
        )
        if state != 0:
            self.logger.error(f"Getting screenshot through ADB, failed {info.stdout}")
            return
        else:
            screenshot_path = info

        self.screenshot = cv2.imread(screenshot_path)
        if self.screenshot is None:
            self.logger.error(f"Failed to load screenshot image from {screenshot_path}")
            return

        # Convert to QImage and display
        height, width, channels = self.screenshot.shape
        bytes_per_line = width * 3
        q_image = QImage(
            self.screenshot.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_BGR888
        )
        q_image = QPixmap.fromImage(q_image)
        self.screenshot_item.setPixmap(q_image)
        self.screenshot_view.fitInView(
            self.screenshot_scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.screenshot_view.show()

        self.logger.info("Screenshot taken")

    def on_frame(self, frame):
        """
        Slot for handling new frames from the scrcpy client.
        """
        self.on_frame_signal.emit(frame)

    @pyqtSlot(object)
    def update_frame(self, frame: Optional[ndarray]):
        """
        Update the displayed frame in the UI.

        :param frame: The new frame to be displayed.
        """
        if frame is not None:
            height, width, channels = frame.shape
            bytes_per_line = width * 3
            q_image = QImage(
                frame,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_BGR888
            )
            q_image = QPixmap.fromImage(q_image)
            self.screenshot_item.setPixmap(q_image)
            self.screenshot_view.fitInView(
                self.screenshot_scene.itemsBoundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            self.screenshot_scene.update()

    def track_screen(self):
        """
        Start or stop tracking the screen using scrcpy client.
        """
        if self.scrcpy_client.alive:
            self.scrcpy_client.stop()
        else:
            self.scrcpy_client.start(threaded=True)


class Worker(QRunnable):
    class WorkerSignals(QObject):
        finished_signal = pyqtSignal()
        error_signal = pyqtSignal(str)
        result_signal = pyqtSignal(object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = self.WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error_signal.emit(
                (exctype, value, traceback.format_exc())
            )
        else:
            self.signals.result_signal.emit(
                result
            )
        finally:
            self.signals.finished_signal.emit()