#!/usr/bin/env pyshrimp
# $requires:

import pyshrimp
from pyshrimp import run, log


def main():
    log(f'PyShrimp is working. Version: {pyshrimp.__version__}')


run(main)
