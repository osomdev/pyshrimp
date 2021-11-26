#!/usr/bin/env pyshrimp
import os

from pyshrimp import log, run


def main():
    log(f'This script should be automatically wrapped with sudo.')
    log(f'Current user id: {os.getuid()}')
    log(f'                 ^ this should be ZERO')
    log(f'')
    log(f'Are those values preserved correctly?')
    log(f'HOME={os.path.expanduser("~")}')
    log(f'CWD={os.getcwd()}')


run(main, elevate=True)
