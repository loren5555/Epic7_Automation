import subprocess


class ErrorHandlingMixin:
    def __init__(self, logger):
        self.logger = logger

    @staticmethod
    def __handle_error(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with {e.returncode}: {e.output}")    # 命令行错误
        except Exception as e:
            self.logger.error(f"Unhandled exception: {e}")

    def __getattr__(self, item):
        attr = object.__getattribute__(self, item)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = self.__handle_error(attr, *args, **kwargs)
                return result
            return wrapper
        return attr
