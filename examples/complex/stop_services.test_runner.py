#!/usr/bin/env pyshrimp

import os
import stat
import sys
from multiprocessing.pool import AsyncResult
from tempfile import TemporaryDirectory

from pyshrimp import run, run_process, log, write_to_file, chmod_set, wait_until, cmd, exit_error, in_background


class ExampleRunner:

    def __init__(self):
        self._actual_script = sys.argv[1]
        self._temp_dir = TemporaryDirectory(prefix='pyshrimp_example_stop_services_')
        self._service_name = 'pyshrimp-test-service1-7be86577-98ce-4c7f-9082-2c8075cba980'
        self._services_root_dir = os.path.join(self._temp_dir.name, 'services')
        self._svscan_proc: AsyncResult

    def _prepare(self):
        log('--- Setting up test environment...')

        # setup service for test
        service_dir = os.path.join(self._services_root_dir, self._service_name)
        os.makedirs(service_dir)

        # setup service entry point
        run_file = os.path.join(service_dir, 'run')
        write_to_file(
            run_file,
            # NOTE: exec here is very important - without it the svc -d will produce zombie process instead of killing sleep
            '#!/bin/sh\n'
            'exec sleep 7\n'
        )
        chmod_set(run_file, stat.S_IXUSR)

        # run services with svscan
        # noinspection PyProtectedMember
        self._svscan_proc = in_background(
            cmd(['/usr/bin/svscan', self._services_root_dir], capture=True, check=False)
        )

        # wait until service starts
        success, service_supervisor_pid = wait_until(
            'Service supervisor starts',
            collect=lambda: cmd(['pgrep', '-f', f'supervise {self._service_name}'], check=False).exec().standard_output.strip(),
            check_interval_sec=0.1,
            timeout_sec=5
        )

        if not success:
            exit_error('Execution setup failed - service did not start in time!')

        log('Test environment setup completed.')

    def _cleanup(self):
        log('--- Cleaning after test...')

        # force-kill any remaining processes
        cmd(['pkill', '-9', '-f', f'supervise {self._service_name}']).exec(check=False)
        cmd(['pkill', '-9', '-f', f'/usr/bin/svscan {self._services_root_dir}']).exec(check=False)

        # cleanup temp dir
        self._temp_dir.cleanup()

        log('Cleanup completed')

    def main(self):
        self._prepare()
        exit_code = 127
        try:
            log(f'--- Running script {self._actual_script}\n\n\n')
            result = run_process(
                command=[
                    self._actual_script, f'--services-dir={self._services_root_dir}'
                ],
                timeout=30,
                capture_out=False,
                capture_err=False
            )
            exit_code = result.exit_code

            print('\n\n')

            if exit_code != 0:
                exit_error(f'Got unexpected non zero exit code: {exit_code}. Result: {result}', exit_code=exit_code)

            service_supervisor_pid = cmd(['pgrep', '-f', f'supervise {self._service_name}'], check=False).exec().standard_output.strip()
            svscan_pid = cmd(['pgrep', '-f', f'/usr/bin/svscan {self._services_root_dir}'], check=False).exec().standard_output.strip()

            if svscan_pid:
                exit_error(f'svscan process did not terminate, pid={svscan_pid}')

            if service_supervisor_pid:
                exit_error(f'service supervisor process did not terminate, pid={service_supervisor_pid}')

            if not self._svscan_proc.get(timeout=0):
                exit_error(f'svscan process terminated but did not completed?! is there zombie process maybe?')

            log('===> TEST RESULT: OK')

        finally:
            log(f'--- Script finished with exit code: {exit_code}')
            self._cleanup()


try:
    run(ExampleRunner().main)
finally:
    log('~~~ AFTER RUN')
