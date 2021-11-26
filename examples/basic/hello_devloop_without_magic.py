#!/usr/bin/env pyshrimp

from pyshrimp import run, log


def main():
    log('Hello devloop!')
    log('When you run this script it will execute and wait for change.')
    log('Once the script is modified it should automatically re-run.')
    log('As this script does not run with magic wrapper the run needs to be invoked manually')


run(main, devloop=True)
