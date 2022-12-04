from unittest import TestCase

from pyshrimp.utils.subprocess_utils import run_process, ProcessExecutionException
from common.platform_utils import runOnUnixOnly


@runOnUnixOnly
class TestSubprocessUtils(TestCase):
    def test_run_process_should_return_output(self):
        self.assertEqual(
            '3\n',
            run_process('echo -n 123 | wc -c', run_in_shell=True).raise_if_not_ok().standard_output
        )

    def test_run_process_should_raise_exception_when_return_code_is_non_zero(self):
        exception = None
        try:
            run_process('exit 1', run_in_shell=True).raise_if_not_ok()
        except ProcessExecutionException as ex:
            exception = ex

        self.assertIsNotNone(exception)
        self.assertEqual('Command execution failed: Command returned non zero exit code: 1', exception.message)
        self.assertEqual(
            'Command execution failed: Command returned non zero exit code: 1\n'
            '  Command: exit 1\n'
            '  Exit code: 1\n'
            '  Stdout: \'\'\n'
            '  Error: \'\'',
            str(exception)
        )
