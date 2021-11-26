#!/usr/bin/env pyshrimp
# $requires: click==7.1.1, requests==2.23.0
# $requires: PyYAML==5.3.1

import os

from pyshrimp import run, ls, glob_ls, wait_until, log, cmd, SkipConfig


def get_up_services(service_dirs):
    return cmd('svstat').exec(service_dirs).out.match_lines(r'.*/(.*/.*?): up .*')


def collection_is_empty(col):
    return len(col) == 0


def main():
    dry_run = True
    wait_timeout_sec = 6

    services_root_dir = os.path.expanduser('~/services/bg')
    user_id = os.getuid()

    service_dirs = ls(services_root_dir, dirs_only=True)
    service_dirs_including_logs = service_dirs + glob_ls(services_root_dir + '/*/log', dirs_only=True)

    kill = cmd('/bin/kill')
    svc = cmd('svc')
    pgrep = cmd('pgrep')

    log(f'# Stopping all services in {services_root_dir}...')

    svc.exec('-d', service_dirs, skip=dry_run)

    wait_until(
        'all services are shutdown',
        collect=lambda: get_up_services(service_dirs),
        check=collection_is_empty,
        before_sleep=lambda up_services: log(f' . still up: {", ".join(up_services)}'),
        timeout_sec=wait_timeout_sec
    )

    log('# Killing svscan')

    def _get_svscan_pids():
        return pgrep(
            '--uid', user_id, '-f', f'/usr/bin/svscan {services_root_dir}'
        ).out.lines()

    kill.exec(_get_svscan_pids(), skip=SkipConfig(skip=dry_run, skip_when_no_args=True))

    wait_until(
        'all svscan processes terminates',
        collect=_get_svscan_pids,
        check=collection_is_empty,
        before_sleep=lambda pids: log(f' . still up: {", ".join(pids)}'),
        timeout_sec=wait_timeout_sec
    )

    log('# Killing supervisors')

    svc.exec('-x', service_dirs_including_logs, skip=dry_run)

    wait_until(
        'all supervisors terminates',
        collect=lambda: get_up_services(service_dirs_including_logs),
        check=collection_is_empty,
        before_sleep=lambda up_services: log(f' . still up: {", ".join(up_services)}'),
        timeout_sec=wait_timeout_sec
    )

    log('# All done.')


run(main)
