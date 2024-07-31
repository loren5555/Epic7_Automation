import logging

import cv2
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QWidget, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from common.logger import Logger
from E7A.emulator.emulator import MuMuEmulator, EmulatorState
from E7A.ui.epic7_automator_main_window import Ui_MainWindow


class QTextBrowserHandler(logging.Handler):
    def __init__(self, text_browser):
        super().__init__()
        self.text_browser = text_browser

    def emit(self, record):
        msg = self.format(record)
        self.text_browser.append(msg)


class BlockingTaskThread(QThread):
    task_completed = pyqtSignal()
    task_not_ready = pyqtSignal()

    def __init__(self, task_func, check_interval=2000):
        super().__init__()
        self.task_func = task_func
        self.check_interval = check_interval

    def run(self):
        print("run")
        while not self.task_func():
            self.task_not_ready.emit()
            print("not_ready_emit")
            self.msleep(self.check_interval)
        self.task_completed.emit()
        print("ready_emit")


class E7AutoMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, emulator: MuMuEmulator, logger: Logger, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.emulator = emulator

        self.logger = logger.get_child_logger("UI_MainWindow")

        # add UI log handler to the Logger
        text_browser_handler = QTextBrowserHandler(self.log_text_browser)
        text_browser_handler.setLevel(logger.level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        text_browser_handler.setFormatter(formatter)
        self.logger.addHandler(text_browser_handler)

        self.setWindowTitle("Epic7 Automation")
        self.setup_connections()
        self.screenshot_scene = QGraphicsScene()

        self.task_thread = None  # 用于锁定操作的线程

    # region base functions
    def setup_connections(self):
        self.start_button.clicked.connect(self.launch_emulator)
        self.get_app_button.clicked.connect(self.populate_app_list)
        self.launch_app_button.clicked.connect(self.launch_app)
        self.shutdown_button.clicked.connect(self.shutdown_emulator)
        self.screenshot_button.clicked.connect(self.take_screenshot)

    def toggle_controls(self, enable: bool):
        # Recursively enable or disable all widgets in the main window
        def set_enabled(widget, enabled: bool):
            widget.setEnabled(enabled)
            if isinstance(widget, QWidget):
                for child in widget.findChildren(QWidget):
                    if isinstance(child, QPushButton):
                        set_enabled(child, enabled)

        set_enabled(self, enable)
        if enable is True:
            self.status_label.setText("")
        else:
            self.status_label.setText("Work in progress...")
    # endregion

    # region Ui functions
    def launch_emulator(self):
        self.logger.info("Emulator launching")
        # 禁用输入
        self.toggle_controls(False)

        def check_emulator_ready():
            print("Checking if emulator is ready...")
            return self.emulator.state == EmulatorState.READY

        self.task_thread = BlockingTaskThread(check_emulator_ready)
        self.task_thread.task_completed.connect(self.on_emulator_ready)
        self.task_thread.task_not_ready.connect(self.on_emulator_not_ready)
        self.task_thread.start()
        self.emulator.launch()

    @pyqtSlot()
    def on_emulator_ready(self):
        self.logger.info("Emulator ready")
        print("Emulator ready")
        self.toggle_controls(True)

    @pyqtSlot()
    def on_emulator_not_ready(self):
        self.logger.info("Emulator not ready yet...")

    def populate_app_list(self):
        if self.emulator.state != EmulatorState.READY:
            self.app_combo_box.clear()
            self.app_combo_box.addItem("Emulator not ready")
            self.logger.error("Emulator not ready")
            return

        self.emulator.update_installed_apps()
        self.app_combo_box.clear()
        self.app_combo_box.addItems(self.emulator.app_list.keys())
        self.logger.info("App list populated")

    def launch_app(self):
        app_name = self.app_combo_box.currentText()
        self.emulator.launch_app(app_name)
        self.logger.info(f"App {app_name} launched")

    def shutdown_emulator(self):
        self.emulator.shutdown()
        self.logger.info("Emulator shutdown")

    def take_screenshot(self):
        image = self.emulator.take_screenshot()
        height, width, channels = image.shape
        bytes_per_line = 3 * width
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        q_image = QPixmap(q_image)

        self.screenshot_scene.clear()
        self.screenshot_scene.addPixmap(q_image)
        self.screenshot_view.setScene(self.screenshot_scene)
        self.screenshot_view.fitInView(self.screenshot_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.logger.info("Screenshot taken")
    # endregion
