#!/usr/bin/env pyshrimp
# $requires: click==7.1.1, psutil==5.8.0

import os

import click
from psutil import pid_exists

from pyshrimp import run, ls, glob_ls, wait_until, log, cmd, SkipConfig


def get_up_services(service_dirs):
    return cmd('svstat').exec(service_dirs).out.match_lines(r'.*/(.*/.*?): up .*')


def collection_is_empty(col):
    return len(col) == 0


@click.command()
@click.option(
    '--services-dir', 'services_dir', required=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True)
)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--wait-timeout-sec', type=float, default=6.0)
def main(services_dir: str, dry_run: bool, wait_timeout_sec: float):
    user_id = os.getuid()

    service_dirs = ls(services_dir, dirs_only=True)
    service_dirs_including_logs = service_dirs + glob_ls(services_dir + '/*/log', dirs_only=True)

    kill = cmd('/bin/kill')
    svc = cmd('svc')
    pgrep = cmd('pgrep', check=False)

    # The sequence is:
    # 1. stop all services
    # 2. signal svscan to quit
    # 3. terminate supervisors
    # 4. await for svscan to fully terminate - must happen after 3 as supervisors are connected with the parent

    log(f'# Stopping all services in {services_dir}...')

    svc.exec('-d', service_dirs, skip=dry_run)

    wait_until(
        'all services are shutdown',
        collect=lambda: get_up_services(service_dirs),
        check=collection_is_empty,
        before_sleep=lambda up_services: log(f' . still up: {", ".join(up_services)}'),
        timeout_sec=wait_timeout_sec
    )

    svscan_process_ids = [
        int(pid) for pid in pgrep(
            '-U', user_id,  # using short -U as --uid is not supported on macOS
            '-f', f'svscan {services_dir}'
        ).out.lines()
    ]

    log(f'# Requesting svscan to terminate: {svscan_process_ids}')

    kill.exec(*svscan_process_ids, skip=SkipConfig(skip=dry_run, skip_when_no_args=True))

    log('# Terminating supervisors')

    svc.exec('-x', service_dirs_including_logs, skip=dry_run)

    wait_until(
        'all supervisors terminates',
        collect=lambda: get_up_services(service_dirs_including_logs),
        check=collection_is_empty,
        before_sleep=lambda up_services: log(f' . still up: {", ".join(up_services)}'),
        timeout_sec=wait_timeout_sec
    )

    log('# Completing svscan termination')

    wait_until(
        'all svscan processes terminates',
        collect=lambda: list(filter(pid_exists, svscan_process_ids)),
        check=collection_is_empty,
        before_sleep=lambda pids: log(f' . still up: {", ".join(map(str, pids))}'),
        on_timeout=lambda pids: kill.exec('-9', *pids, skip=SkipConfig(skip=dry_run, skip_when_no_args=True)),
        timeout_sec=wait_timeout_sec
    )

    log('# All done.')


run(main)
