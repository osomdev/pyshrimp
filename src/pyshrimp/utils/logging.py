import logging
import sys


def log(message: str, level=logging.INFO):
    logging.log(level, message)


def exit_error(message: str, exit_code: int = 1):
    log(message, level=logging.ERROR)
    raise sys.exit(exit_code)
