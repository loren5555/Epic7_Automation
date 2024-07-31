import sys
import time

from PyQt5.QtWidgets import QApplication

from E7A.common.config import Config
from common.logger import Logger
from E7A.emulator.emulator import MuMuEmulator
from E7A.ui.epic7_automator_UI import E7AutoMainWindow


def main():
    Config.load_config(
        r"C:\Users\loren\Projects\Epic7_Automation_Python\config\config.yaml"
    )
    TIMESTAMP = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))
    logger = Logger(
            logger_name=Config.logger.logger_name,
            log_dir=Config.logger.log_dir,
            log_name=Config.logger.log_name.replace("TIMESTAMP", TIMESTAMP)
    )

    emulator = MuMuEmulator(
        vm_index=Config.emulator.vm_index,
        vm_name=Config.emulator.vm_name,
        logger=logger)

    app = QApplication(sys.argv)
    main_window = E7AutoMainWindow(emulator=emulator, logger=logger)

    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
