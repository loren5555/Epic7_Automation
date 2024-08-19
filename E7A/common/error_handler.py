import subprocess
from contextlib import contextmanager
from E7A.common.logger import Logger


@contextmanager
def error_handler(logger: Logger):
    try:
        yield
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed with return code: {e.returncode}: {e.output.decode('utf-8')}"
        )
    except Exception as e:
        logger.error(f"Unhandled {e.__class__.__name__}: {e}")
        # raise e from e
