import os
import re
import signal
from tempfile import TemporaryDirectory

from common.background_execution import run_with_timeout
from common.extended_test_case import ExtendedTestCase
from pyshrimp import glob_ls
from pyshrimp.utils.command import cmd

# useful for debugging
_log_enabled = False

_expected_script_result = {
    'complex/send_keys_to_window.py': (1, r'.* Usage: ./send_keys_to_window.py window_name keys...')
}


def _log(message: str):
    if _log_enabled:
        print(message)


def _get_utils_script_path(name):
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'utils', name)
    )


class TestScriptRunner(ExtendedTestCase):

    def setUp(self) -> None:
        self._tmp_dir = TemporaryDirectory('_pyshrimp_script_runner_test')
        self._cache_dir = os.path.join(self._tmp_dir.name, 'pyshrimp_cache')
        os.mkdir(self._cache_dir)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_examples_should_run_successfully(self):
        examples = glob_ls(
            # we are in tests/smoke/ and want to be in examples/ -> ../../examples/**/*.py
            os.path.dirname(__file__), os.pardir, os.pardir, 'examples', '**', '*.py',
            files_only=True,
            recursive=True
        )

        for example_script in examples:
            if not example_script.endswith('.test_runner.py'):
                self._run_example(example_script)

    def _run_example(self, example_script):
        _log(f'Testing: {example_script}')
        example_script_short_name = re.match('.*/examples/(.*)', example_script).group(1)

        self.assertTrue(
            os.access(example_script, os.X_OK),
            f'Example script is not executable: {example_script}'
        )

        # some examples use sudo, let's mock it to no-op
        fake_sudo = _get_utils_script_path('fake_sudo.py')

        # use script runner if one exists - some examples require extra execution setup
        test_runner_path = re.sub(r'\.py$', '.test_runner.py', example_script)
        if os.path.exists(test_runner_path) and not os.access(test_runner_path, os.X_OK):
            self.fail(f'Example script have test runner which is NOT executable: {test_runner_path}')

        script_cmd = [test_runner_path, os.path.abspath(example_script)] if os.path.exists(test_runner_path) else [example_script]

        _log(f'Spawning process: {script_cmd}')

        # spawn process in background - some scripts use devloop so we should be ready for this
        proc = cmd(
            script_cmd,
            env=dict(
                # execute script with fake sudo - instead of running script we capture the process details
                PYSHRIMP_SUDO_PATH=fake_sudo,
                # use temporary directory for cache
                PYSHRIMP_CACHE_DIR=self._cache_dir,
                # reset python path
                PYTHONPATH=''
            )
        )._spawn()

        captured_lines = []

        def _process_output():
            try:
                for line in proc.stdout:
                    _log(f'=> {line.rstrip()}')
                    captured_lines.append(line.rstrip())
                    if 'Waiting until file changes:' not in line:
                        continue

                    # script was executed and dev loop is waiting for changes
                    # trigger ctrl+c to stop it
                    proc.send_signal(signal.SIGINT)

            except Exception as ex:
                _log(f'Got exception while reading process output: {ex}')

            finally:
                _log('Output processing loop completed')

        _log(f'Processing lines of PID:{proc.pid} in background...')

        # process the output with timeout
        processing_result = run_with_timeout(
            target=_process_output,
            timeout_sec=30,
            on_error=lambda: proc.send_signal(signal.SIGKILL),
            raise_on_timeout=False
        )

        _log(f'after wait for processing, result={processing_result}')

        # wait for process termination
        terminate_result = run_with_timeout(
            target=lambda: proc.close(1),
            timeout_sec=10,
            on_error=lambda: proc.send_signal(signal.SIGKILL),
            raise_on_exception=False
        )

        captured_output = "\n".join(captured_lines) + (terminate_result.result.error_output if terminate_result.result else '')
        self.assertFalse(
            terminate_result.timed_out or processing_result.timed_out,
            f'Execution of {example_script} timed out, captured output:\n'
            f'{captured_output}'
        )

        # all examples should be successful unless specified otherwise
        expected_exit_code, output_matcher = _expected_script_result.get(example_script_short_name, (0, None))

        if any('Waiting until file changes:' in line for line in captured_lines):
            # we stopped script with ctrl+c so it should exit with 130 code
            self.assertEqual(
                130, terminate_result.result.return_code,
                f'Example script finished with unexpected exit code: {example_script}\n'
                f'Captured output:\n'
                f'{captured_output}'
            )
            # as all examples should be successful we expect to see 0 exit code message
            self.assertRegex(
                captured_output, rf'.* Script finished, exit code: {expected_exit_code}\n.*',
                f'Example script finished without expected finish message (bad status code? expected {expected_exit_code}): {example_script}\n'
                f'Captured output:\n'
                f'{captured_output}'
            )
        else:
            self.assertEqual(
                expected_exit_code, terminate_result.result.return_code,
                f'Example script finished with unexpected exit code ({expected_exit_code} != {terminate_result.result.return_code}): {example_script}\n'
                f'Captured output:\n'
                f'{captured_output}'
            )

        if output_matcher is not None:
            self.assertRegex(
                captured_output, output_matcher,
                f'Example script output did not match expected pattern: {example_script}\n'
                f'Captured output:\n'
                f'{captured_output}'
            )
