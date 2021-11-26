#!/usr/bin/env pyshrimp
# $opts: magic
import os
import sys

from pyshrimp import cmd, log, exit_error, wait_until

if len(sys.argv) < 2:
    raise exit_error(f'Usage: ./{os.path.basename(sys.argv[0])} window_name keys...')

target_window_name = sys.argv[1]
keys_args = sys.argv[2:]

xdotool = cmd('xdotool')

active_window = xdotool('getactivewindow').out.strip()

# searching for window is flaky, try few times
_, target_window = wait_until(
    'target window is found',
    collect=lambda: xdotool('search', '--name', target_window_name, check=False).out.strip(),
    timeout_sec=0.5,
    check_interval_sec=0.1,
    on_timeout=lambda res: exit_error('Target window not found'),
)

log(f'WINDOWS: target_window={target_window} active={active_window}')

if not target_window:
    raise exit_error('Target window not found')

window_activate = xdotool.with_args('windowactivate', '--sync')
window_activate(target_window)
xdotool('key', keys_args)
window_activate(active_window)
