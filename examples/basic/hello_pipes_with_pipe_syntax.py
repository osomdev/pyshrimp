#!/usr/bin/env pyshrimp
import re
from functools import partial

from pyshrimp import log, cmd, run, pipe, shell_cmd, PIPE, PIPE_END


def _peak(s):
    log(
        f'Current value:\n'
        f'{s.rstrip()}\n'
        f'--\n'
    )
    return s


def main():
    ps = cmd('ps')
    res = (
        PIPE

        # Run prepared commands with customized args
        | ps.with_args('a')

        # Use bash where it's more convenient
        | 'head -n 10 | tail -n 3'

        # Pass function to process output
        | _peak

        # You can pass params to inlined shell commands
        | shell_cmd('grep -v -- "$1"', 'NoSuchLine-ThisOnlyShowsHowToUseParams')

        # Array shorthand supported
        | ['sort', '-r']

        # Use inline commands
        | ['awk', '{print $1}']

        # Partial is useful to prepare function with arguments
        | partial(re.sub, '1', 'X')

        # Lambdas fit well
        | (lambda s: re.sub('[5]', 'F', s))
    ).close()
    log(f'Standard output:\n{res.stdout}\n')
    log(f'Error output:\n{res.stderr}\n')
    log(f'Exception:\n{res.exception}\n')


run(main)
