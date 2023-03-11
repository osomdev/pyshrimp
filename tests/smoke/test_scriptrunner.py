import json
import os
import re
import signal
import textwrap
import time
from tempfile import TemporaryDirectory

from common.background_execution import run_with_timeout
from common.extended_test_case import ExtendedTestCase
from pyshrimp import ls
from pyshrimp.utils.command import cmd


def _get_script_path(name):
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'pyshrimp', name)
    )


def _get_utils_script_path(name):
    return os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'utils', name)
    )


def _write_script(file_path: str, content: str):
    content_lines = content.split('\n')
    while content_lines[0] == '':
        # remove first empty line
        content_lines.pop(0)

    file_content = textwrap.dedent('\n'.join(content_lines))
    with open(file_path, 'w') as f:
        f.write(file_content)


class TestScriptRunner(ExtendedTestCase):

    def _make_temp_script(self, contents):
        script_name = f'temp_script_{time.time_ns()}.py'
        script_path = os.path.join(self._tmp_dir.name, script_name)
        _write_script(script_path, contents)
        os.chmod(script_path, 0o700)
        return script_path

    def _exec_inline_script(self, contents, check=True):
        return self._exec_script_by_path(
            self._make_temp_script(contents),
            check
        )

    def _exec_test_script(self, script_name, check=True):
        return self._exec_script_by_path(
            _get_script_path(script_name),
            check
        )

    def _exec_script_by_path(self, script_path, check=True):
        return cmd(
            script_path,
            env=self._get_script_env()
        ).exec(check=check)

    def _get_script_env(self, **extra_env):
        script_env = {
            'PYSHRIMP_CACHE_DIR': self._cache_dir,
            # enable log - useful for debugging
            # 'PYSHRIMP_LOG': '1',
            # clear python path, otherwise the testing path will get populated
            'PYTHONPATH': ''
        }
        script_env.update(**extra_env)
        return script_env

    def setUp(self) -> None:
        self._tmp_dir = TemporaryDirectory('_pyshrimp_script_runner_test')
        self._cache_dir = os.path.join(self._tmp_dir.name, 'pyshrimp_cache')
        os.mkdir(self._cache_dir)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_simple_script_should_run_correctly(self):
        res = self._exec_test_script('hello_world.py')
        self.assertRegex(res.standard_output, r'.* INFO \| Hello world!\n')
        self._assert_virtual_env_created_correctly()

    def test_virtual_environment_initialization_collision_should_be_detected(self):
        target_script = _get_script_path('hello_world.py')

        # run script two times - should (almost ;)) guarantee collision
        p1 = cmd(target_script, env=self._get_script_env())._spawn()
        p2 = cmd(target_script, env=self._get_script_env())._spawn()

        p1res = p1.close()
        p2res = p2.close()

        # one of the processes should run fine and the other should fail
        if p1res.return_code == 0:
            success_proc, error_proc = p1res, p2res
        else:
            success_proc, error_proc = p2res, p1res

        self.assertRegex(success_proc.standard_output, r'.* INFO \| Hello world!\n')
        self.assertRegex(error_proc.error_output, r'.*ERROR: Failed to setup virtualenv! Could not obtain lock under .*')

        # there should be no problem with running the script again
        p3res = self._exec_script_by_path(target_script)
        self.assertRegex(p3res.standard_output, r'.* INFO \| Hello world!\n')

        self._assert_virtual_env_created_correctly()

    def test_simple_script_with_magic_initialization_should_run_correctly(self):
        res = self._exec_test_script('hello_magic.py')

        self.assertRegex(res.standard_output, r'.* INFO \| Hello magic!\n')
        self._assert_virtual_env_created_correctly()

    def test_script_with_illegal_config_should_fail_fast(self):
        res = self._exec_inline_script(
            '''
            #!/usr/bin/env pyshrimp
            # $opts: devloop,elevate
            print('Missing magic, this should fail')
            ''',
            check=False
        )
        self.assertRegex(res.error_output, r'.*ERROR: Script configuration is invalid, please see previous messages..*')
        self.assertRegex(res.error_output, r'.*Detected invalid configuration - devloop is enabled but magic is not, this will not work as expected.*')
        self.assertRegex(res.error_output, r'.*Detected invalid configuration - elevate is enabled but magic is not, this will not work as expected.*')
        self.assertEqual(1, res.return_code)
        self.assertEqual('', res.standard_output)

    def test_script_with_requirements_should_run_correctly(self):
        res = self._exec_test_script('with_requirements.py')

        self.assertEqual('\x1b[32mClick is with us!\x1b[0m\n', res.standard_output)
        self._assert_virtual_env_created_correctly()

    def test_script_with_requirements_file_should_run_correctly(self):
        res = self._exec_test_script('with_requirements_file.py')

        self.assertEqual('\x1b[32mClick is with us and it was required from external file!\x1b[0m\n', res.standard_output)
        self._assert_virtual_env_created_correctly()

    def test_script_with_magic_and_elevate_should_use_sudo_to_elevate_permissions(self):
        target_script = _get_script_path('with_magic_elevate.py')
        dump_process_info_script = _get_utils_script_path('dump_process_info.py')
        res = cmd(
            target_script,
            env=self._get_script_env(
                # execute script with fake sudo - instead of running script we capture the process details
                PYSHRIMP_SUDO_PATH=dump_process_info_script
            )
        ).exec()

        # parse the process details
        self.assertRegex(res.standard_output, r'PROCESS INFO:.*')
        proc_info = json.loads(re.match('PROCESS INFO:(.*)', res.standard_output).group(1))

        # check expected sudo invocation shape
        expected_sudo_call = [
            dump_process_info_script,
            "-E",
            "--preserve-env=PATH,PYTHONPATH",
            "--",
            self._lookup_virtual_env_python_path(),
            target_script
        ]
        self.assertEqual(expected_sudo_call, proc_info['argv'])

        # check wrapper options in env
        self.assertDictContainsElements(
            {
                'magic': 'true',
                'elevate': 'true'
            },
            json.loads(proc_info['env']['PYSHRIMP_MAGIC_WRAPPER_OPTS']),
            'Should contain expected wrapper options'
        )

    def test_script_with_devloop_should_re_run_script_on_change_and_stop_after_keyboard_interruption_signal(self):
        script_content_v1 = '''
            #!/usr/bin/env pyshrimp
            # $opts: magic,devloop
            print(f'The script with magic devloop was executed. Magic number: 1')
            '''

        script_content_v2 = '''
            #!/usr/bin/env pyshrimp
            # $opts: magic,devloop
            print(f'The script with magic devloop was executed. Magic number: 2')
            '''

        target_script = os.path.join(self._tmp_dir.name, 'script_with_magic_devloop.py')

        # Scenario:
        # (1) Execute first version of script
        # (2) After the first execution modify script - write second version
        #       expected result: devloop should re-run script
        # (3) After second execution simulate keyboard interrupt
        #       expected result: devloop should exit
        # (4) Process should terminate

        # (1): Start execution of V2
        _write_script(target_script, script_content_v1)
        os.chmod(target_script, 0o700)
        proc = cmd(target_script, env=self._get_script_env())._spawn()

        captured_lines = []

        def _process_output():
            phase = 'first_script_run'
            for line in proc.stdout:
                captured_lines.append(line.rstrip())
                if 'Waiting until file changes:' not in line:
                    continue

                if phase == 'first_script_run':
                    # (2) first script execution completed, change script to v2
                    _write_script(target_script, script_content_v2)
                    phase = 'second_script_run'

                elif phase == 'second_script_run':
                    # (3) second execution completed, simulate ctrl+c
                    proc._process.send_signal(signal.SIGINT)
                    phase = 'wait_till_script_terminates'

                else:
                    self.fail('FAIL: unexpected 3rd occurrence of wait!')

            self.assertEqual('wait_till_script_terminates', phase)

        # process the output with timeout
        processing_result = run_with_timeout(
            target=_process_output,
            timeout_sec=30,
            on_error=lambda: proc._process.send_signal(signal.SIGKILL),
            raise_on_timeout=False
        )

        # (4) wait for process termination
        terminate_result = run_with_timeout(
            target=lambda: proc.close(5),
            timeout_sec=10,
            on_error=lambda: proc._process.send_signal(signal.SIGKILL),
            raise_on_exception=False
        )

        captured_output = "\n".join(captured_lines)
        self.assertFalse(
            terminate_result.timed_out or processing_result.timed_out,
            f'Execution timed out, captured output:\n{captured_output}'
        )
        self.assertIn(
            'The script with magic devloop was executed. Magic number: 1',
            captured_lines
        )
        self.assertIn(
            'The script with magic devloop was executed. Magic number: 2',
            captured_lines
        )
        self._assert_virtual_env_created_correctly()

    def _assert_virtual_env_created_correctly(self):
        venvs_path = os.path.join(self._cache_dir, 'virtual_envs')
        venvs = ls(venvs_path, dirs_only=True)
        self.assertEqual(1, len(venvs), f'Expected to find one virtual env but found: {venvs}')

    def _lookup_virtual_env_path(self):
        self._assert_virtual_env_created_correctly()
        venvs_path = os.path.join(self._cache_dir, 'virtual_envs')
        venvs = ls(venvs_path, dirs_only=True)
        return os.path.join(venvs_path, venvs[0])

    def _lookup_virtual_env_python_path(self):
        return os.path.join(self._lookup_virtual_env_path(), 'bin', 'python')
