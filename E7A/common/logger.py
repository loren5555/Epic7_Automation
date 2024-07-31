import os
import sys
import time
import logging
from typing import Optional


class Logger(logging.Logger):
    def __init__(
            self,
            logger_name: Optional[str] = None,
            log_dir: str = "./log",
            log_name: str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time())),
            logger_level: int = logging.DEBUG,
            console_log: bool = True,
            console_log_level: int = logging.NOTSET,
            file_log: bool = False,
            file_log_level: bool = logging.NOTSET,
            fmt: str = "{asctime} | {levelname:<8} | {name:<14} |{message}",
            datefmt: str = "%Y-%m-%d %H:%M:%S",
            propagate: bool = True,
    ):
        """
        Modified logger class to log messages

        :param logger_name: logging中注册的logger name
        :param log_dir: 存储log文件的路径
        :param log_name: log文件的主名
        :param logger_level: logger level
        :param console_log: 是否在console输出
        :param console_log_level: console输出级别
        :param file_log: 是否在文件输出
        :param file_log_level: 文件输出级别
        :param fmt: logger格式化格式
        :param datefmt: logger时间显示格式
        :param propagate: Logger.propagate
        """
        super().__init__(logger_name, level=logger_level)

        if os.path.exists(log_dir) is False:
            os.makedirs(log_dir)
        # file_path = dir + main_name + .log
        log_path = os.path.join(log_dir, log_name + ".log")
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt, style="{")

        if console_log is True:
            # log lower levels to stdout
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setLevel(console_log_level)
            stdout_handler.setFormatter(formatter)
            stdout_handler.addFilter(lambda rec: rec.levelno <= logging.INFO)
            self.addHandler(stdout_handler)

            # log higher levels to stderr (red)
            stderr_handler = logging.StreamHandler(stream=sys.stderr)
            stderr_handler.setLevel(console_log_level)
            stderr_handler.setFormatter(formatter)
            stderr_handler.addFilter(lambda rec: rec.levelno > logging.INFO)
            self.addHandler(stderr_handler)

        if file_log is True:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(file_log_level)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)

        self.propagate = propagate

    def get_child_logger(self, suffix: str) -> logging.Logger:
        """
        Return a child logger whose parent is self.

        :param suffix: child logger suffix
        :return: a child logger whose parent is self
        """
        child_logger = logging.getLogger(suffix)
        child_logger.parent = self
        return child_logger
