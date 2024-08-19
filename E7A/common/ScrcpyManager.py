import traceback

import cv2
import scrcpy
import numpy
from adbutils import adb, AdbDevice

from E7A.common import Logger


class ScrcpyManager:
    def __init__(
            self,
            logger: Logger = None,
            device: AdbDevice = None,
            max_frame: int = 30,
            threaded: bool = True
    ):
        super().__init__()
        if logger is not None:
            self.logger = logger.get_child_logger(self.__class__.__name__)
        else:
            self.logger = Logger(self.__class__.__name__)
        self.device = device
        self.max_frame = max_frame
        self.threaded = threaded
        self.client = None
        self._frame = None
        self._initialize_scrcpy()

    @property
    def frame(self):
        return self._frame

    def connect(self, device: AdbDevice, max_frame: int = 30):
        self.client = scrcpy.Client(device, max_fps=max_frame)
        self.client.add_listener(scrcpy.EVENT_FRAME, self._on_frame)
        self.client.add_listener(scrcpy.EVENT_INIT, self._on_init)

    def start(self):
        self.client.start(threaded=self.threaded)

    def _initialize_scrcpy(self):
        if self.device is None:
            self.logger.warning(f"scrcpy failed to initialize with empty adb device list")
        else:
            self._frame = numpy.zeros(self.device.window_size())
            self.connect(self.device, self.max_frame)

    def _on_frame(self, frame):
        if frame is not None:
            self._frame = frame

    def _on_init(self):
        if self.client:
            self.logger.info(f"Scrcpy initialized with device: {self.client.device_name}")

    def capture_screenshot(self, save_path: str):
        cv2.imwrite(save_path, self.current_frame)
        self.logger.info(f"Screenshot saved to {save_path}")
