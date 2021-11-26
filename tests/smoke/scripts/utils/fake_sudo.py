#!/usr/bin/env python
import os
import sys

# Runs the target script - does not really execute sudo
# we set the PYSHRIMP_RUNNING_UNDER_FAKE_SUDO instead

if '--' not in sys.argv:
    print(f'FAKE SUDO ERROR: Unexpected invocation args - missing "--" param: {sys.argv}')
    sys.exit(1)

separator_index = sys.argv.index('--')
args = sys.argv[separator_index + 1:]
os.environ['PYSHRIMP_RUNNING_UNDER_FAKE_SUDO'] = 'true'
os.execlp(args[0], *args)
