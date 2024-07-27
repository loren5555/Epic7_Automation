import logging
import sys

from PyQt5.QtWidgets import QApplication

from E7A.utils.logger import Logger
from E7A.emulator.emulator import MuMuEmulator
from E7A.ui.epic7_automator_UI import E7AutoMainWindow


def main():
    logger = Logger("Epic7_Automation", log_level=logging.DEBUG)
    emulator = MuMuEmulator(logger=logger)
    app = QApplication(sys.argv)
    main_window = E7AutoMainWindow(emulator=emulator, logger=logger)

    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
