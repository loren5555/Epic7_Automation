import os
import subprocess
import json

from shutil import copyfile
from typing import Optional
from pprint import pformat

from E7A.common.logger import Logger


class MuMuEmulator:
    """
    A Class for controlling the mu-mu emulator through MuMuManager.
    For MuMuManager API, see "doc/MuMuManager.html"
    """
    def __init__(
        self,
        logger: Logger = None,
    ):
        # Initialize self.logger
        if logger is None:
            self.logger = Logger(self.__class__.__name__)
        else:
            self.logger = logger.get_child_logger(self.__class__.__name__)

        self._emulator_info: dict = {}    # key: emulator index, value: emulator info
        self._app_info: dict = {}

        # initialize emulator info and app info.
        self.update()

        self._target_emulator_index: int = 0    # Default emulator index
        self._target_adb: Optional[dict] = self._app_info.get(self._target_emulator_index)

    @property
    def available_emulators(self) -> list:
        return list(self._emulator_info.keys())

    @property
    def target_emulator_index(self) -> int:
        """
        :return: the index of the emulator the class is communicating with.
        """
        return self._target_emulator_index

    @target_emulator_index.setter
    def target_emulator_index(self, identifier: int | str):
        """
        Set target emulator index which operation sent to.

        :param identifier: target emulator index
        """
        if self._is_valid_identifier(identifier):
            if identifier == "all":
                self.logger.error("Target emulator can only be set to a single emulator.")
            else:
                self._target_emulator_index = int(identifier)
        # identifier invalid
        else:
            self.logger.error(
                f"Failed to set target emulator index: {identifier}."
                f"Valid identifiers: {self.available_emulators}"
            )

    @property
    def target_emulator_info(self) -> Optional[dict]:
        return self._emulator_info.get(self._target_emulator_index)

    @property
    def target_emulator_state(self) -> str:
        state = self.target_emulator_info.get("player_state")
        if state is not None:
            return state
        else:
            return "stopped"

    @property
    def target_emulator_adb_address(self) -> (str, int):
        if self.target_emulator_state == "start_finished":
            adb_host_ip = self.target_emulator_info["adb_host_ip"]
            adb_port = self.target_emulator_info["adb_port"]
            return adb_host_ip, adb_port
        else:
            self.logger.warning(
                f"Get adb address failed, target emulator info: {self.target_emulator_info}"
            )
            return None, None

    @property
    def target_emulator_apps_info(self) -> Optional[dict]:
        if self.target_emulator_state == "start_finished":
            return self.get_app_info(self.target_emulator_index)
        else:
            return {}

    def get_emulator_info(self, identifier: int | str = "all") -> dict:
        """
        Get the info of the emulator and update the emulator_info dictionary.
        :param identifier:
        :return: Emulator info dictionary.
        """
        if self._is_valid_identifier(identifier):
            if identifier == "all":
                return self._emulator_info
            else:
                return self._emulator_info.get(int(identifier))
        else:
            self.logger.error(
                f"Failed to get emulator info: {identifier}."
                f"Valid identifiers: {self.available_emulators + ['all']}"
            )

    def get_app_info(self, identifier: int | str = "all") -> dict:
        if self._is_valid_identifier(identifier):
            if identifier == "all":
                return self._app_info
            else:
                return self._app_info.get(int(identifier))
        else:
            self.logger.error(
                f"Failed to get app info: {identifier}."
                f"Valid identifiers: {self.available_emulators + ['all']}"
            )

    def get_app_state(self, identifier: int, pkg: str) -> str:
        # Check identifier
        if self._is_valid_identifier(identifier):
            if self.target_emulator_state == "start_finished":
                process = self._execute_command(f"MuMuManager.exe control -v {identifier} app info -pkg {pkg}")
                info: dict = json.loads(process.stdout)
                return info.get("state")
            else:
                self.logger.error(
                    f"Emulator {identifier} not ready. Get app state failed."
                )
                return "not_ready"

        else:
            self.logger.error(
                f"Failed to get app info with invalid identifier: {identifier}. "
                f"Valid identifiers: {self.available_emulators + ['all']}"
            )
            return "wrong_identifier"

    def update(self) -> None:
        self._update_emulator_info()
        self._update_app_info()

    def launch_target_emulator(self) -> subprocess.CompletedProcess:
        """
        Launch the target emulator.

        :return: CompletedProcess instance.
        """
        if self.target_emulator_info["is_process_started"]:
            self.logger.warning(f"Target emulator is already started.")
        process = self._execute_command(
            f"mumumanager control -v {self.target_emulator_index} launch"
        )
        self.logger.info("Emulator starting...")
        return process

    def shutdown_target_emulator(self) -> subprocess.CompletedProcess:
        """
        Shutdown the target emulator.

        :return: CompletedProcess instance.
        """
        if not self.target_emulator_info["is_process_started"]:
            self.logger.warning(f"Target emulator is not running.")
        process = self._execute_command(
            f"mumumanager control -v {self.target_emulator_index} shutdown"
        )
        self.logger.info("Emulator shutting down...")
        return process

    def launch_app_on_target_emulator(self, pkg: str) -> subprocess.CompletedProcess:
        match app_state := self.get_app_state(self.target_emulator_index, pkg):
            case "not_installed":
                self.logger.info(f"Pkg [{pkg}] does not exist.")
            case "running":
                self.logger.info(f"App [{pkg}] is already running.")
            case "stopped":
                process = self._execute_command(
                    f"mumumanager control -v {self.target_emulator_index} app launch -pkg {pkg}"
                )
                self.logger.info(f"Starting app [{pkg}]...")
                return process
            case "not_ready":
                self.logger.error(f"The emulator needs to be started to launch APP.")
            case "wrong_identifier":
                self.logger.error(f"The target emulator index is wrong: {self.target_emulator_index}")
            case _:
                self.logger.error(f"Unknown app state: {app_state}, package name: {pkg}")

    def close_app_on_target_emulator(self, pkg: str) -> subprocess.CompletedProcess:
        process = self._execute_command(
            f"mumumanager control -v {self.target_emulator_index} app close -pkg {pkg}"
        )
        self.logger.info(f"Closing app {pkg}")
        return process

    def take_screenshot(
            self,
            file_name="E7Automation_screenshot.png",
            save_dir_android=r"'/sdcard/$MuMu12Shared/Screenshots/E7Automation_screenshot.png'",
            save_dir_windows="C:/Users/loren/Projects/Epic7_Automation_Python/temp/",
            mumu_share_dir="C:/Users/loren/Documents/MuMu共享文件夹/Screenshots"
    ) -> str:
        """
        Take a screenshot of the emulator using adb method.
        Note that the process is slow, do not call this function multiple times quickly.
        Or the Screenshot file might be incomplete.
        Also, due to limitation in MuMuManager, do not delete the screenshot file in
        mumu_share_dir. Or the file won't be accessible.

        :param file_name: The name of the screenshot png.
        :param save_dir_android: the path to the screenshot png in the emulator.
        :param save_dir_windows: the path to save the screenshot.
        :param mumu_share_dir:  the path to the png stored in windows.
        :return: The screenshot file path.
        """
        if self.target_emulator_state != "start_finished":
            self.logger.error(
                f"Emulator {self.target_emulator_index} not ready. Failed to take screenshot.")
            return ""

        if os.path.exists(save_dir_windows) is not True:
            os.mkdir(save_dir_windows)

        # 安卓截图存储位置
        if file_name != "E7Automation_screenshot.png":
            save_path_android = save_dir_android.replace("E7Automation_screenshot.png", rf"{file_name}")
        else:
            save_path_android = save_dir_android
        # Windows 截图存储位置.
        save_path_windows = save_dir_windows + file_name
        # ADB 截图命令.
        process = self._execute_command(
            f"mumumanager adb -v {self.target_emulator_index} -c shell screencap -p {save_path_android}"
        )
        process.check_returncode()

        # 复制截图文件至目标文件夹.
        file_path_from = os.path.normpath(
            os.path.join(mumu_share_dir, file_name)
        )
        file_path_to = os.path.normpath(
            os.path.join(save_path_windows)
        )
        copyfile(file_path_from, file_path_to)
        self.logger.info(
            f"Screenshot saved to {os.path.normpath(file_path_to)}"
        )

        return file_path_to

    def send_tap(self, x: int, y: int) -> subprocess.CompletedProcess:
        if self.target_emulator_state != "start_finished":
            self.logger.warning(f"Emulator {self.target_emulator_index} not ready.")
        process = self._execute_command(
            f"mumumanager adb -v {self.target_emulator_index} -c shell input tap {str(x)} {str(y)}"
        )
        return process

    def send_swipe(
            self, start_point: (int, int), end_point: (int, int), swap_time: int = 200
    ) -> subprocess.CompletedProcess:
        if self.target_emulator_state != "start_finished":
            self.logger.warning(f"Emulator {self.target_emulator_index} not ready.")
        process = self._execute_command(
            f"mumumanager adb -v {self.target_emulator_index} -c shell "
            f"input swipe {start_point[0]} {start_point[1]} {end_point[0]} {end_point[1]} {swap_time}"
        )
        return process

    def send_key(self, keycode) -> subprocess.CompletedProcess:
        if self.target_emulator_state != "start_finished":
            self.logger.warning(f"Emulator {self.target_emulator_index} not ready.")
        process = self._execute_command(
            f"mumumanager adb -v {self.target_emulator_index} -c shell "
            f"input keyevent {str(keycode)}"
        )
        return process

    def _execute_command(self, command: str, **kwargs) -> subprocess.CompletedProcess:
        """
        Run command and return process.

        :param command: A CMD command in string format.
        :return: Process output.
        """
        self.logger.debug("Command received: $ " + command)
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs
        )
        return process

    def _is_valid_identifier(self, identifier: int | str) -> bool:
        # 整型是否在可用例表中
        if isinstance(identifier, int):
            if identifier in self.available_emulators:
                return True
        elif isinstance(identifier, str):
            # 字符型是否是all
            if identifier == "all":
                return True
            # 字符型是否在列表中
            elif identifier.isdigit():
                if int(identifier) in self.available_emulators:
                    return True
        return False

    def _update_emulator_info(self, identifier: int | str = "all") -> None:
        """
        Update the info of the existing emulator and update the emulator_info dictionary.

        :param identifier: selected emulator identifier.
        """
        if self._is_valid_identifier(identifier):
            identifier = "all" if identifier == "all" else int(identifier)
            process = self._execute_command(f"Mumumanager info -v {identifier}")
            emulators_info: dict = json.loads(process.stdout)

            if identifier == "all":
                self._emulator_info = {int(key): value for key, value in emulators_info.items()}
            else:
                self._emulator_info.update({identifier: emulators_info})

        else:
            # Invalid identifier.
            self.logger.error(
                f"Failed to update emulator info with invalid identifier: {identifier}. "
                f"Valid identifiers: {self.available_emulators + ['all']}"
            )

    def _update_app_info(self, identifier: int | str = "all") -> None:
        """
        Update the info of the Apps installed on the emulators.

        :param identifier:
        """
        if self._is_valid_identifier(identifier):
            process = self._execute_command(f"MuMuManager.exe control -v {identifier} app info -i")
            info: dict = json.loads(process.stdout)

            if identifier == "all":
                self._app_info = {int(key): value for key, value in info.items()}
            else:
                self._app_info.update({identifier: info})

        # Check identifier
        else:
            # Invalid identifier.
            self.logger.error(
                f"Failed to update app info with invalid identifier: {identifier}. "
                f"Valid identifiers: {self.available_emulators + ['all']}"
            )

    @staticmethod
    def app_name2pkg_dict(app_info: dict) -> dict:
        reverse_dict = {}
        if "errcode" in app_info.keys():
            return reverse_dict
        else:
            for key, value in app_info.items():
                if isinstance(value, dict):
                    reverse_dict[value["app_name"]] = key
        return reverse_dict

    def __repr__(self):
        return pformat(self.__dict__)
