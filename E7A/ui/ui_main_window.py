from adbutils import adb
from adbutils.errors import AdbError
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, pyqtSlot, QRunnable, QObject, QThreadPool, QTimer
)

from E7A.ui.ui_main_window_Qt_generated import Ui_UIMain
from E7A.ui.utils import QTextBrowserHandler
from E7A.common import Logger
from E7A.emulator import MuMuEmulator


class UIMain(QMainWindow, Ui_UIMain):
    def __init__(
            self,
            logger: Logger
    ):
        super().__init__()
        self.setupUi(self)
        self.logger = logger.get_child_logger(self.__class__.__name__)
        text_browser_handler = QTextBrowserHandler(self.log_textBrowser)
        text_browser_handler.setLevel(logger.level)
        text_browser_handler.setFormatter(self.logger.formatter)
        self.logger.addHandler(text_browser_handler)

        self._setup_connections()

    def _setup_connections(self):
        ...

    @pyqtSlot(MuMuEmulator)
    def on_emulator_info_updated(self, emulator: MuMuEmulator):
        # Update available emulator indices.
        self.emulator_index_comboBox.clear()
        for index in emulator.available_emulators:
            self.emulator_index_comboBox.addItem(str(index))
        current_index = self.emulator_index_comboBox.findText(
            str(emulator.target_emulator_index)
        )
        self.emulator_index_comboBox.setCurrentIndex(current_index)

        # Update target emulator info.
        self.emulator_name_label.setText(emulator.target_emulator_info["name"])
        self.emulator_state_label.setText(emulator.target_emulator_state)

        # Update adb info
        target_adb_ip, target_adb_port = emulator.target_emulator_adb_address
        if target_adb_ip and target_adb_port:
            adb_serial = f"{target_adb_ip}:{target_adb_port}"
            adb_device = adb.device(serial=adb_serial)

            try:
                adb_state = adb_device.get_state()
            except AdbError as e:
                adb_state = e

            try:
                adb_name = adb_device.prop.name
            except AdbError as e:
                adb_name = e

            self.adb_address_lineEdit.setText(adb_serial)
            self.adb_ip_label.setText(target_adb_ip)
            self.adb_port_label.setText(f"{target_adb_port}")
            self.adb_device_label.setText(
                f"{adb_name}".replace(f" '{adb_serial}'", "")
            )
            self.adb_state_label.setText(
                f"{adb_state}".replace(f" '{adb_serial}'", "")
            )

        else:
            self.adb_address_lineEdit.setText("")
            self.adb_ip_label.setText("")
            self.adb_port_label.setText("")
            self.adb_device_label.setText("")
            self.adb_state_label.setText("")

    @pyqtSlot(MuMuEmulator)
    def on_apps_info_updated(self, emulator: MuMuEmulator):
        # update app state
        app_info = emulator.target_emulator_apps_info
        previous_selected_app = self.applist_combobox.currentText()
        self.applist_combobox.clear()
        if len(app_info) == 0:
            self.activate_app_label.setText("")
        for pkg, info in app_info.items():
            if pkg == "active":
                if info in app_info.keys():
                    self.activate_app_label.setText(app_info[info]["app_name"])
                else:
                    self.activate_app_label.setText(info)
            else:
                self.applist_combobox.addItem(info["app_name"])
        current_index = self.applist_combobox.findText(previous_selected_app)
        current_index = max(0, current_index)
        self.applist_combobox.setCurrentIndex(current_index)

    def closeEvent(self, event):
        """
        Handle the window close event to quit the application.
        """
        QApplication.closeAllWindows()
        QApplication.quit()
