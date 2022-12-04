import platform
from unittest import skipIf

def runOnUnixOnly(target):
    skip_decorator = skipIf(
        platform.system().lower() in {'windows', 'java'},
        "test ignored under non-unix systems"
    )
    return skip_decorator(target)