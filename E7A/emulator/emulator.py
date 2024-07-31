import os
import re
import ast
import subprocess
import json
import time
import threading

from shutil import copyfile
from enum import Enum
from typing import Optional

import cv2

from common.logger import Logger
from E7A.common.error_handler import ErrorHandlingMixin


# class EmulatorState(Enum):
#     # Emulator states
#     UNINITIALIZED = "uninitialized"
#     STOPPED = "stopped"
#     BOOTING = "booting"
#     READY = "ready"


# class AppState(Enum):
#     # App states
#     RUNNING = "running"
#     STOPPED = "stopped"
#     OTHER = "other_state"
#     INEXISTENCE = "inexistence"


# class MumuReturnCode(Enum):
#     # Err code from MuMu API
#     PLAYER_NOT_RUNNING = 4294967096
#     ADB_FAIL = 4294967295    # may be adb fail


class MuMuEmulator(ErrorHandlingMixin):
    """
    A Class for controlling the mu-mu emulator through MuMuManager.
    For MuMuManager API, see "doc/MuMuManager.html"
    """
    def __init__(
            self,
            vm_index: int = 0,
            vm_name: str = None,
            logger: Logger = None
    ):
        """
        Bind to a certain emulator in MuMU Emulator.

        :param vm_index: The index in mumu manager.
                         If vm_name provided, this parameter is ignored.
        :param vm_name: the nmme in mumu manager
        :param logger: logger
        """
        super().__init__(logger)
        self.index: str = str(vm_index)
        self.name: Optional[str] = vm_name
        # 用于传给Mumumanager的模拟器标识
        self.identifier: str = self.index if self.name is None else self.name
        # 用于存放获取到的应用列表
        self.app_list: dict = {"App list not initialized": None}
        self.state_info: dict = {}

        if logger is not None:
            self.logger = logger.get_child_logger("MuMuEmulator")
        else:
            self.logger = Logger("MuMuEmulator")

        self.logger.info("Initializing MuMiEmulator.")
        self.update_player_state()

    def execute_command(self, command: str) -> subprocess.CompletedProcess:
        """
        Run command and return process.

        :param command: A CMD command in string format.
        :return: Process output.
        """
        self.logger.debug("Command received: $ " + command)
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process

    # region mumu api command
    def update_player_state(self) -> subprocess.CompletedProcess:
        if self.state_info =={}:
            self.logger.info("Initializing player state.")
        else:
            self.logger.info("Updating player state.")
        # 检查状态
        process = self.execute_command(
            f"mumumanager info -v {self.identifier}"
        )
        # API 输出
        state_info = json.loads(process.stdout.decode("utf-8").strip())
        self.state_info = state_info
        if process.returncode != 0:
            self.logger.error(
                f"Failed to update MuMu emulator state. Errcode: "
                f"{self.state_info['errcode']}, "
                f"Errmsg: {state_info['errmsg']}. "
                f"This can be caused that the index of name doesn't exist."
            )
            self.state_info["error_code"] = self.state_info["errcode"]
        self.logger.info(f"Player state updated.")
        return process

    def launch(self) -> subprocess.CompletedProcess:
        # launch emulator
        process = self.execute_command(
            f"mumumanager control -v {self.identifier} launch"
        )
        self.logger.info("Emulator starting.")
        return process

    def shutdown(self) -> subprocess.CompletedProcess:
        # shutdown emulator
        process = self.execute_command(
            f"mumumanager control -v {self.identifier} shutdown"
        )
        self.logger.info("Emulator shutting down.")
        return process

    def update_installed_apps(self) -> None:
        """
        get installed apps info including packageName, appName and version.
        """
        # 检测模拟器状态
        self.update_player_state()
        # 模拟器错误
        if self.state_info["error_code"] != 0:
            self.logger.error(
                f"Failed to update installed APPs info. "
                f"Maby the emulator index or name doesn't exist."
            )
            self.app_list = {"Apps info update failed.": None}
            return

        process = self.execute_command(
            f"mumumanager control -v {self.identifier} app info -i"
        )
        app_info = json.loads(process.stdout.decode("utf-8").strip())
        # 获取信息错误
        if process.returncode != 0:
            self.logger.error(
                f"Failed to update installed APPs info. Errcode: "
                f"{app_info['errcode']}, "
                f"Errmsg: {app_info['errmsg']}. "
                f"Maby the emulator is not running."
            )
            self.app_list = {"The emulator is not ready": None}
            return

        self.app_list = json.loads(process.stdout.decode("utf-8").strip())
        self.logger.info("Apps info updated.")

    def get_app_state(self, app_pkg_name: str) -> str:
        # 模拟器错误
        if self.state_info["error_code"] != 0:
            self.logger.error(
                f"Failed to get APP state. "
                f"Maby the emulator index or name doesn't exist."
            )
            return "error"

        process = self.execute_command(
            f"mumumanager control -v {self.identifier} app info -pkg {app_pkg_name}"
        )
        state_info = json.loads(process.stdout.decode("utf-8").strip())
        # 获取信息错误
        if process.returncode != 0:
            self.logger.error(
                f"Failed to get APP state. "
                f"{state_info['errcode']}, "
                f"Errmsg: {state_info['errmsg']}. "
                f"Maby the emulator is not running."
            )
            return "error"

        return state_info["state"]

    def launch_app(self, app_pkg_name: str) -> None:
        self.update_installed_apps()
        app_state = self.get_app_state(app_pkg_name)
        app_name = self.app_list.get(
            app_pkg_name, {"app_name": "inexistence"})["app_name"]
        match app_state:
            case "running":
                self.logger.info(f"App [{app_name}] already running.")
            case "stopped":
                self.logger.info(f"Starting app [{app_name}].")
                self.execute_command(
                    f"mumumanager control -v {self.identifier} app launch -pkg {app_pkg_name}"
                )
            case "not_installed":
                self.logger.info(f"Pkg name  [{app_pkg_name}] does not exist.")
            case "error":
                self.logger.error(f"App state error, pkg name {app_pkg_name}")

    def close_app(self, app_pkg_name: str):
        process = self.execute_command(
            f"mumumanager control -v {self.identifier} app close -pkg {app_pkg_name}"
        )
        return process

    def take_screenshot(
            self,
            move_screenshot: bool = True,
            file_name: str = "E7Automation_screenshot.png",
            save_dir: str = "C:/Users/loren/Projects/Epic7_Automation_Python/temp",
            mumu_share_path: str = "C:/Users/loren/Documents/MuMu共享文件夹/Screenshots",
            delete_after_save: bool = True,
            wait_time: int = 5,
            check_interval: float = 0.5,
    ):
        """
        Take a screenshot of the emulator using adb method.

        :param move_screenshot: If is True, move the screenshot to save dir.
        :param file_name: The name of the screenshot png.
        :param save_dir: the path to save the screenshot.
        :param mumu_share_path:  the path to the png stored in windows.
        :param delete_after_save:  Whether to delete the origin screenshot in
                    mumu_share_path.
        :param wait_time: Max wait time in seconds.
        :param check_interval: Interval in seconds between checking the screenshot.
        """
        # 模拟器错误
        if self.state_info["error_code"] != 0:
            self.logger.error(
                f"Failed to take screenshot. "
                f"Maby the emulator index or name doesn't exist."
            )
            return

        # 记录截图前文件状态.
        initial_files = set(os.listdir(mumu_share_path))

        process = self.execute_command(
            f"mumumanager control -v {self.identifier} tool func -n screenshot"
        )
        task_info = json.loads(process.stdout.decode("utf-8").strip())
        # 截图错误
        if process.returncode != 0:
            self.logger.error(
                f"Failed to take screenshot. "
                f"{task_info['errcode']}, "
                f"Errmsg: {task_info['errmsg']}. "
                f"Maby the emulator is not running."
            )
            return

        # 等待截图文件出现
        end_time = time.time() + wait_time
        screenshot_path = None
        while time.time() < end_time:
            current_files = set(os.listdir(mumu_share_path))
            new_files = current_files - initial_files
            if new_files:
                valid_files = [os.path.join(mumu_share_path, f) for f in
                               new_files if ".pending" not in f]
                if valid_files:
                    screenshot_path = max(valid_files, key=os.path.getmtime)
                    break
            time.sleep(check_interval)

        if not screenshot_path or not os.path.exists(screenshot_path):
            self.logger.error(
                f"Screenshot not found in mumu_share_path: {mumu_share_path}"
            )
            return

        try:
            if move_screenshot is True:
                # 将截图文件移动至指定文件夹.
                if os.path.exists(save_dir) is False:
                    os.mkdir(save_dir)
                save_path = os.path.join(save_dir, file_name)
                copyfile(screenshot_path, save_path)
            else:
                save_path = os.path.join(mumu_share_path, file_name)
                copyfile(screenshot_path, save_path)
            self.logger.info(
                f"Screenshot saved to {os.path.normpath(save_path)}"
            )

            if delete_after_save is True:
                threading.Thread(
                    target=self.delayed_delete, args=(screenshot_path,)
                ).start()

        except FileNotFoundError:
            self.logger.error(
                f"Screenshot not found in mumu_share_path: {mumu_share_path}"
            )

    def delayed_delete(self, file_path, delay=1):
        time.sleep(delay)
        try:
            os.remove(file_path)
            self.logger.info(f"Screenshot {file_path} deleted after delay.")
        except Exception as e:
            self.logger.error(f"Error occurred while deleting after delay: {e}")
    # endregion

    # region mumu adb command
    def adb_error(self, process: subprocess.CompletedProcess) -> bool:
        if process.returncode != 0:
            stdout = json.loads(process.stdout)
            self.logger.error(
                f"ADB failed. errcode: {stdout['errcode']}, errmsg: {stdout['errmsg']}"
            )
            return True
        return False

    def get_screenshot_adb(
            self,
            file_name="E7Automation_screenshot.png",
            save_dir_android=r"'/sdcard/$MuMu12Shared/Pictures/'",
            save_dir_windows="C:/Users/loren/Projects/Epic7_Automation_Python/temp/",
            mumu_share_dir="C:/Users/loren/Documents/MuMu共享文件夹/Pictures"
    ):
        """
        Take a screenshot of the emulator using adb method.
        This method is more stable than get_screenshot.

        :param file_name: The name of the screenshot png.
        :param save_dir_android: the path to the screenshot png in the emulator.
        :param save_dir_windows: the path to save the screenshot.
        :param mumu_share_dir:  the path to the png stored in windows.
        :return: The screenshot read by cv2.imread().
        """
        if os.path.exists(save_dir_windows) is not True:
            os.mkdir(save_dir_windows)

        # 安卓截图存储位置
        save_path_android = save_dir_android + file_name
        # Windows 截图存储位置.
        save_path_windows = save_dir_windows + file_name
        # ADB 截图命令.
        process = self.execute_command(
            f"mumumanager adb -v {self.identifier} -c "
            f"shell screencap -p " + save_path_android
        )
        task_info = json.loads(process.stdout.decode("utf-8").strip())
        if self.adb_error(process):
            return

        # 复制截图文件至目标文件夹.
        file_path_from = os.path.normpath(
            os.path.join(mumu_share_dir, file_name)
        )
        file_path_to = os.path.normpath(
            os.path.join(save_path_windows)
        )
        try:
            copyfile(file_path_from, file_path_to)
        except FileNotFoundError:
            # 没有找到安卓截图文件
            self.logger.error(
                f"Screenshot file not found: "
                f"from: {file_path_from} to {file_path_to}"
            )
        except Exception as e:
            self.logger.fatal(f"Error in taking screenshot {e}")

    def send_touch(self, x: int, y: int):
        process = self.execute_command(
            f"mumumanager adb -v {self.identifier} -c shell input tap {str(x)} {str(y)}"
        )
        if self.adb_error(process):
            return
        else:
            self.logger.info(f"Touching ({str(x)}, {str(y)}).")

    def send_swipe(self, start_point: (int, int), end_point: (int, int)):
        process = self.execute_command(
            f"mumumanager adb -v {self.identifier} -c shell "
            f"input swipe ({start_point[0]}, {start_point[1]}) ({end_point[0]}, {end_point[1]})"
        )
        if self.adb_error(process):
            return
        else:
            self.logger.info(
                f"Swiping from ({start_point[0]}, {start_point[1]}) "
                f"to ({end_point[0]}, {end_point[1]})"
            )

    def send_key(self, keycode):
        process = self.execute_command(
            f"mumumanager adb -v {self.identifier} -c shell "
            f"input keyevent {str(keycode)}"
        )
        if self.adb_error(process):
            return
        else:
            self.logger.info(f"Key input: {str(keycode)}")

    # endregion
