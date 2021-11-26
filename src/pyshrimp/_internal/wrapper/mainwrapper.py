import datetime
import hashlib
import inspect
import logging
import os
import subprocess
import sys
import time
import traceback
from builtins import KeyboardInterrupt

from time import sleep
from typing import Callable

# noinspection PyProtectedMember
from pyshrimp._internal.utils.errors import _exit_error
from pyshrimp._internal.wrapper.magicwrapper_state import _is_magic_active


def _init_logging():
    # TODO: consider level coloring...
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)8s | %(message)s',
        level=logging.INFO,
        stream=sys.stdout,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def _re_run_script():
    args = [sys.executable] + sys.argv
    os.execlp(args[0], *args)


def _calculate_file_checksum(script_path):
    with open(script_path, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()


def _elevate_with_sudo(devloop: bool):
    sudo_path = os.environ.get('PYSHRIMP_SUDO_PATH', 'sudo')
    os.environ['PYTHONPATH'] = ':'.join(sys.path)
    args = [sudo_path, '-E', '--preserve-env=PATH,PYTHONPATH', '--', sys.executable] + sys.argv

    if devloop:
        # cannot use exec, run sub-process
        return subprocess.run(args).returncode
    else:
        os.execlp(args[0], *args)
        # this will be never invoked as we exec:
        return -1


def _run(
    script: Callable,
    elevate=False,
    init_logging=_init_logging,
    devloop=False,
    check_main=True,
    re_run_script=_re_run_script,
    script_path=None
):
    if check_main and inspect.currentframe().f_back.f_locals['__name__'] != '__main__':
        return

    if _is_magic_active() and not inspect.currentframe().f_back.f_code.co_filename.endswith('magicwrapper.py'):
        raise _exit_error(
            'Looks like "run(...)" was invoked manually while running with magic enabled. '
            'This will likely cause unexpected behavior and hence such invocation is not supported. '
            'Please either remove explicit "run(...)" invocation or the "magic" from $opts.'
        )

    # remember file checksum before executing
    main_script_path = os.path.abspath(script_path or sys.modules['__main__'].__file__)
    main_script_checksum = _calculate_file_checksum(main_script_path) if devloop else None
    main_script_change_time = os.stat(main_script_path).st_mtime
    execution_start = time.time()

    if elevate and os.getuid() != 0 and os.environ.get('PYSHRIMP_RUNNING_UNDER_FAKE_SUDO', 'false') != 'true':
        exit_code = _elevate_with_sudo(devloop)

    else:
        if init_logging:
            init_logging()

        # noinspection PyBroadException
        try:
            exit_code = script() or 0
        except KeyboardInterrupt:
            exit_code = 130
        except SystemExit as ex:
            exit_code = ex.code
        except BaseException:
            if devloop:
                print('ERROR: Got exception while running script:')
                traceback.print_exc()
                exit_code = 1
            else:
                raise

    if devloop:
        # TODO: wait until script changes or user input is given
        print()
        print(f' /' + '-' * 60)
        print(f' | Script finished, exit code: {exit_code}')
        print(f' | Execution took: {datetime.timedelta(seconds=time.time() - execution_start)}')
        print(f' | Waiting until file changes:')
        print(f' |   {main_script_path}')
        sys.stdout.flush()

        try:
            last_mtime = main_script_change_time
            while True:
                current_mtime = os.stat(main_script_path).st_mtime
                if last_mtime != current_mtime:
                    last_mtime = current_mtime
                    if main_script_checksum != _calculate_file_checksum(main_script_path):
                        break

                sleep(0.2)
        except KeyboardInterrupt:
            sys.exit(130)

        print(f' | File changed, re-running script * at: {datetime.datetime.now()}')
        print(f' /' + '-' * 60)
        print()
        sys.stdout.flush()
        re_run_script()
    else:
        sys.exit(exit_code)
