import logging
import sys


class Logger(logging.Logger):
    """
    Modified logger class to log messages
    """
    def __init__(
            self,
            name,
            log_console=True,
            log_file=None,
            log_level=logging.NOTSET,
            formatter=None):
        """
        :param name: Logger name
        :param log_file: Logger file name. If not provided, the logger won't be logged to file
        :param log_level: Logging level
        """
        super().__init__(name, level=log_level)

        if formatter is None:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if log_console:
            # log lower levels to stdout
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setLevel(log_level)
            stdout_handler.setFormatter(formatter)
            stdout_handler.addFilter(lambda rec: rec.levelno <= logging.INFO)
            self.addHandler(stdout_handler)

            # log higher levels to stderr (red)
            stderr_handler = logging.StreamHandler(stream=sys.stderr)
            stderr_handler.setLevel(log_level)
            stderr_handler.setFormatter(formatter)
            stderr_handler.addFilter(lambda rec: rec.levelno > logging.INFO)
            self.addHandler(stderr_handler)

        if log_file is not None:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)

    def get_child_logger(self, suffix):
        # Return a child logger whose parent is self.
        child_logger = logging.getLogger(suffix)
        child_logger.parent = self
        return child_logger
