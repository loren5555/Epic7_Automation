import subprocess
import os
import re
import ast
from shutil import copyfile
from enum import Enum

import cv2

from E7A.utils.logger import Logger
from E7A.utils.error_handler import ErrorHandlingMixin


# emulator states
class EmulatorState(Enum):
    UNINITIALIZED = "uninitialized"
    STOPPED = "stopped"
    BOOTING = "booting"
    READY = "ready"


# app states
class AppState(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    OTHER = "other_state"
    INEXISTENCE = "inexistence"


class MumuReturnCode(Enum):
    PLAYER_NOT_RUNNING = 4294967294
    ADB_FAIL = 4294967295    # may be adb fail


class MuMuEmulator(ErrorHandlingMixin):
    def __init__(self, vm_index: int = 0, vm_name: str = None, logger=None):
        super().__init__(logger)
        # 定义vm_name后name代替index指定命令对象。
        self.index = str(vm_index)
        self.name = vm_name
        self.identifier = self.index if self.name is None else self.name
        if logger is not None:
            self.logger = logger.get_child_logger("Emulator")
        else:
            self.logger = Logger("Emulator")

        self.app_list = {"App list not initialized": None}

        self.state = EmulatorState.UNINITIALIZED
        self.update_player_state()

    def execute_command(self, command: str, shell=False):
        self.logger.debug("Command: [" + command + "]")
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        return process

    # region mumu api command
    def launch(self):
        # launch emulator
        self.execute_command(f"mumumanager api -v {self.identifier} launch_player")
        self.logger.info("Emulator starting.")

    def shutdown(self):
        self.execute_command(f"mumumanager api -v {self.identifier} shutdown_player")
        self.logger.info("Emulator shutting down.")

    def update_player_state(self):
        process = self.execute_command(f"mumumanager api -v {self.identifier} player_state")
        state_info = process.stdout.decode("utf-8").strip()

        if process.returncode == MumuReturnCode.PLAYER_NOT_RUNNING.value:
            self.state = EmulatorState.STOPPED
        elif process.returncode == 0:
            if "starting_rom" in state_info:
                self.state = EmulatorState.BOOTING
            elif "start_finished" in state_info:
                self.state = EmulatorState.READY
            else:
                self.state = f"Unhandled state info:{process.stdout.decode('utf-8')}"
        else:
            raise RuntimeError(f"Check player state failed, return code {process.returncode}")

    def get_app_state(self, app_name: str):
        try:
            process = self.execute_command(
                f"mumumanager api -v {self.identifier} app_state {self.app_list[app_name]['packageName']}"
            )
        except KeyError:
            # 检测应用给是否存在
            self.logger.error(f"App [{app_name}] not found.")
            return AppState.INEXISTENCE

        state_info = process.stdout.decode("utf-8").strip()
        if "running" in state_info:
            app_state = AppState.RUNNING
        elif "stopped" in state_info:
            app_state = AppState.STOPPED
        else:
            app_state = AppState.OTHER

        return app_state

    def update_installed_apps(self, pattern=r"\{.*?}", dict_key="appName"):
        """
        get installed apps info including appName, packageName and version.

        :param pattern:
        :param dict_key:
        :return: list of infos. key is appName, value is info.
        """
        if self.state != EmulatorState.READY:
            self.logger.error("Emulator state is not ready.")
            return

        self.app_list = {}
        process = self.execute_command(f"mumumanager api -v {self.identifier} get_installed_apps")
        info = process.stdout.decode("utf-8").strip()
        # 使用正则提取mumu api返回的应用信息
        pattern = re.compile(pattern)
        matches = re.finditer(pattern, info)
        for match in matches:
            app_info = ast.literal_eval(match.group(0))
            self.app_list[app_info[dict_key]] = app_info

    def launch_app(self, app_name: str):
        app_state = self.get_app_state(app_name)

        if app_state == AppState.INEXISTENCE.value:
            # app不存在
            self.error(f"App [{app_name}] not found.")
        elif app_state == AppState.RUNNING.value:
            # app正在运行
            self.warning(f"App [{app_name}] already running.")
        elif app_state == AppState.STOPPED.value:
            # app没有运行，启动app
            self.info(f"Starting app [{app_name}].")
            self.execute_command(
                f"mumumanager api -v {self.identifier} launch_app {self.app_list[app_name]['packageName']}"
            )
        elif app_state == AppState.OTHER.value:
            # state返回值为other或其他未知情况
            self.error(f"Unexpected state info: {app_state}")

    def close_app(self, app_name: str):
        self.execute_command(
            f"mumumanager api -v {self.identifier} close_app {self.app_list[app_name]['packageName']}"
        )

    # endregion

    # region mumu adb command
    def get_screenshot(
            self,
            file_name="E7Automation_screenshot.png",
            save_path_android="'/sdcard/$MuMu12Shared/Screenshots/E7Automation_screenshot.png'",
            save_path_windows="C:/Users/loren/Projects/Epic7_Automation_Python/temp",
            mumu_share_path="C:/Users/loren/Documents/MuMu共享文件夹/Screenshots"
    ):
        """
        Take a screenshot of the emulator using adb method.

        :param file_name: The name of the screenshot png.
        :param save_path_android: the path to the screenshot png in the emulator.
        :param save_path_windows: the path to save the screenshot.
        :param mumu_share_path:  the path to the png stored in windows.
        :return: The screenshot read by cv2.imread().
        """
        if file_name != "E7Automation_screenshot.png":
            save_path_android = save_path_android.replace("E7Automation_screenshot.png", file_name)

        process = self.execute_command(f"mumumanager adb -v {self.identifier} shell screencap -p " + save_path_android)
        if process.returncode == MumuReturnCode.ADB_FAIL.value:
            # 截图失败，返回错误代码
            self.logger.error(f"Update screenshot failed: ADB fail.")
            return None

        file_path_from = os.path.join(mumu_share_path, file_name)
        file_path_to = os.path.join(save_path_windows, file_name)
        try:
            copyfile(file_path_from, file_path_to)
        except FileNotFoundError:
            # 没有找到安卓截图文件
            self.logger.error(f"Screenshot file not found: {file_path_from}")
            return None
        except Exception as e:
            self.logger.fatal(f"Error in taking screenshot {e}")

        image = cv2.imread(file_path_to)
        return image

    def send_touch(self, x: int, y: int):
        progress = self.execute_command(f"mumumanager adb -v {self.identifier} shell input tap {str(x)} {str(y)}")
        if progress.returncode == 0:
            self.logger.info(f"Tap {str(x)} {str(y)}")
        elif progress.returncode == MumuReturnCode.ADB_FAIL.value:
            self.logger.error(f"Touch failed: ADB fail.")
        else:
            self.logger.error("Unhandled error")

    def send_swipe(self, start_point: (int, int), end_point: (int, int)):
        progress = self.execute_command(
            f"mumumanager adb -v {self.identifier} shell "
            f"input swipe ({start_point[0]}, {start_point[1]}) ({end_point[0]}, {end_point[1]})"
        )
        if progress.returncode == 0:
            self.logger.info(f"Swipe ({start_point[0]}, {start_point[1]}) ({end_point[0]}, {end_point[1]})")
        elif progress.returncode == MumuReturnCode.ADB_FAIL.value:
            self.logger.error(f"Swipe failed: ADB fail.")
        else:
            self.logger.error("Unhandled error")

    def send_key(self, keycode):
        progress = self.execute_command(f"mumumanager adb -v {self.identifier} shell input keyevent {str(keycode)}")
        if progress.returncode == 0:
            self.logger.info(f"Key input: {str(keycode)}")
        elif progress.returncode == MumuReturnCode.ADB_FAIL.value:
            self.logger.error(f"Keyevent failed: ADB fail.")
        else:
            self.logger.error("Unhandled error")
    # endregion
