import os
import sys
import time
import logging
from typing import Optional


class Logger(logging.Logger):
    """
    Custom logger class to log messages with a specific format and handlers.
    """
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
        Initialize the Logger.

        :param logger_name: Logger name for registration in logging
        :param log_dir: Directory to store log files
        :param log_name: Main name for the log file
        :param logger_level: Logging level for the logger
        :param console_log: Whether to log to console
        :param console_log_level: Logging level for console output
        :param file_log: Whether to log to a file
        :param file_log_level: Logging level for file output
        :param fmt: Log format
        :param datefmt: Date format for log entries
        :param propagate: Logger propagation setting
        """
        super().__init__(logger_name, level=logger_level)

        # Store settings to inherit for child loggers
        self.log_dir = log_dir
        self.log_name = log_name
        self.logger_level = logger_level
        self.console_log = console_log
        self.console_log_level = console_log_level
        self.file_log = file_log
        self.file_log_level = file_log_level
        self.fmt = fmt
        self.datefmt = datefmt
        self.propagate = propagate
        self.formatter = logging.Formatter(fmt=fmt, datefmt=datefmt, style="{")

        if not os.path.exists(log_dir) and file_log:
            os.makedirs(log_dir)

        log_path = os.path.join(log_dir, log_name + ".log")

        if console_log is True:
            self._setup_console_logging()

        if file_log is True:
            self._setup_file_logging(log_path)

        self.propagate = propagate

    def _setup_console_logging(self):
        """
        Set up console logging with different handlers for stdout and stderr.
        """
        # log lower levels to stdout
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(self.console_log_level)
        stdout_handler.setFormatter(self.formatter)
        stdout_handler.addFilter(lambda rec: rec.levelno <= logging.INFO)
        self.addHandler(stdout_handler)

        # log higher levels to stderr (red)
        stderr_handler = logging.StreamHandler(stream=sys.stderr)
        stderr_handler.setLevel(self.console_log_level)
        stderr_handler.setFormatter(self.formatter)
        stderr_handler.addFilter(lambda rec: rec.levelno > logging.INFO)
        self.addHandler(stderr_handler)

    def _setup_file_logging(self, log_path: str):
        """
        Set up file logging.
        :param log_path: Path to the log file
        """
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(self.file_log_level)
        file_handler.setFormatter(self.formatter)
        self.addHandler(file_handler)

    def get_child_logger(self, name: str) -> "Logger":
        """
        Return a child logger whose parent is self.

        :param name: Child logger name
        :return: A child logger whose parent is self
        """
        child_logger = Logger(
            logger_name=name,
            log_dir=self.log_dir,
            log_name=self.log_name,
            logger_level=self.logger_level,
            console_log=self.console_log,
            console_log_level=self.console_log_level,
            file_log=self.file_log,
            file_log_level=self.file_log_level,
            fmt=self.fmt,
            datefmt=self.datefmt,
            propagate=self.propagate
        )
        child_logger.handlers = []
        child_logger.parent = self
        return child_logger
