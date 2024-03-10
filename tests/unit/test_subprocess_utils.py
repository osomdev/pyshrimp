from unittest import TestCase

from common.platform_utils import runOnUnixOnly
from common.resources_accessor import get_test_resource_file_as_text
from pyshrimp.utils.subprocess_utils import run_process, ProcessExecutionException


@runOnUnixOnly
class TestSubprocessUtils(TestCase):
    def test_run_process_should_return_output(self):
        data_file_path, data_file_content = get_test_resource_file_as_text('data_hello_no_nl.txt')

        self.assertEqual(
            data_file_content,
            run_process(['cat', data_file_path]).raise_if_not_ok().standard_output
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
