import time

from adbutils import adb
from PyQt6.QtCore import (
    pyqtSignal, pyqtSlot, QObject, QThreadPool, QTimer
)

from E7A.common import Config, Logger
from E7A.emulator import MuMuEmulator
from E7A.ui.ui_main_window import UIMain
from E7A.ui.utils import ThreadWorker, RunnableWorker


class Epic7Automator(QObject):
    emulators_info_updated = pyqtSignal(MuMuEmulator)
    apps_info_updated = pyqtSignal(MuMuEmulator)

    def __init__(self):
        super().__init__()

        # Initialize logger
        TIMESTAMP = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
        self.logger = Logger(
            logger_name=Config.logger.logger_name,
            log_dir=Config.logger.log_dir,
            log_name=Config.logger.log_name.replace("TIMESTAMP", TIMESTAMP),
            fmt=Config.logger.fmt
        )
        # Initialize Ui windows.
        self.main_window: UIMain = UIMain(self.logger)


        # Initialize emulator
        self._emulator = MuMuEmulator(self.logger)

        # ADB connection to target emulator.
        # TODO Autor the adb device through input.
        # self.adb_device = None

        # Thread pool for tasks
        self._thread_pool = QThreadPool()

        # timer for periodic tasks
        self._periodic_task_count: int = 0
        self._periodic_task_timer = QTimer()

        self._setup_connections()
        self._initialize_automator()

    def _setup_connections(self) -> None:
        # periodic_task
        self._periodic_task_timer.timeout.connect(self._on_periodic_timer_timeout)
        # emulator info update
        self.emulators_info_updated.connect(self.main_window.on_emulator_info_updated)
        self.apps_info_updated.connect(self.main_window.on_apps_info_updated)

        # main window
        self.main_window.emulator_launch_button.pressed.connect(self._launch_target_emulator)
        self.main_window.emulator_stop_button.pressed.connect(self._shutdown_target_emulator)
        self.main_window.app_launch_button.pressed.connect(self._launch_target_app)
        self.main_window.app_stop_button.pressed.connect(self._close_active_app)
        self.main_window.adb_connect_button.pressed.connect(self._connect_target_adb)
        self.main_window.adb_stop_button.pressed.connect(self._disconnect_target_adb)
        self.main_window.emulator_index_comboBox.activated.connect(
            self._on_target_assigned
        )

    def _initialize_automator(self):
        # self._periodic_task_timer.start(3000)
        self.emulators_info_updated.emit(self._emulator)
        self.apps_info_updated.emit(self._emulator)

    @pyqtSlot()
    def _on_periodic_timer_timeout(self) -> None:
        """
        periodic tasks including updating the emulator state, frames, etc.
        """
        worker = RunnableWorker(self._periodic_tasks)
        self._thread_pool.start(worker)

    def _periodic_tasks(self):
        self._periodic_task_count += 1
        # Update emulators and app info
        previous_emulator_info = self._emulator.get_emulator_info()
        previous_apps_info = self._emulator.get_app_info()
        self._emulator.update()
        if previous_emulator_info != self._emulator.get_emulator_info():
            self.emulators_info_updated.emit(self._emulator)
        if previous_apps_info != self._emulator.get_app_info():
            self.apps_info_updated.emit(self._emulator)
        self.logger.debug(f"periodic_task_count: {self._periodic_task_count}")

    @pyqtSlot()
    def _on_target_assigned(self):
        # Target emulator index is changed through UI.
        if new_index := self.main_window.emulator_index_comboBox.currentText():
            self._emulator.target_emulator_index = new_index
            self._emulator.update()
            self.emulators_info_updated.emit(self._emulator)
            self.apps_info_updated.emit(self._emulator)

    @pyqtSlot()
    def _launch_target_emulator(self):
        self._emulator.launch_target_emulator()
        self.main_window.logger.info(f"Emulator {self._emulator.target_emulator_index} starting...")

    @pyqtSlot()
    def _shutdown_target_emulator(self):
        self._emulator.shutdown_target_emulator()
        self.main_window.logger.info(f"Emulator {self._emulator.target_emulator_index} stopping...")
        QTimer.singleShot(500, self._emulator.update)
        QTimer.singleShot(600, lambda: self.emulators_info_updated.emit(self._emulator))

    @pyqtSlot()
    def _launch_target_app(self):
        app_name = self.main_window.applist_combobox.currentText()
        reverse_dict = self._emulator.app_name2pkg_dict(
            self._emulator.target_emulator_apps_info
        )
        pkg_name = reverse_dict[app_name]
        self._emulator.launch_app_on_target_emulator(pkg_name)
        self.main_window.logger.info(f"App {app_name} launched")
        self._emulator.update()
        self.apps_info_updated.emit(self._emulator)

    @pyqtSlot()
    def _close_active_app(self):
        active_app_pkg = self._emulator.target_emulator_apps_info["active"]
        self._emulator.close_app_on_target_emulator(active_app_pkg)
        self.main_window.logger.info(f"App {active_app_pkg} closed")
        self._emulator.update()
        self.apps_info_updated.emit(self._emulator)

    @pyqtSlot()
    def _connect_target_adb(self):
        adb_serial = self.main_window.adb_address_lineEdit.text()
        if adb_serial:
            adb.connect(adb_serial)
            self.main_window.logger.info(f"Connected to {adb_serial}")
        else:
            self.main_window.logger.error(f"Failed to connect adb. Adb address is empty")
        self._emulator.update()
        self.emulators_info_updated.emit(self._emulator)

    @pyqtSlot()
    def _disconnect_target_adb(self):
        adb_serial = self.main_window.adb_address_lineEdit.text()
        if adb_serial:
            adb.disconnect(adb_serial)
            self.main_window.logger.info(f"Disconnected from {adb_serial}")
        else:
            self.main_window.logger.error(f"Failed to disconnect adb. Adb address is empty")
        self._emulator.update()
        self.emulators_info_updated.emit(self._emulator)
