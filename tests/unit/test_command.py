import os
from unittest import TestCase, skipIf

from pyshrimp.utils.command import shell_cmd, cmd, SkipConfig, Command, CommandArgProcessor
from pyshrimp.utils.subprocess_utils import ProcessExecutionException
from common.platform_utils import runOnUnixOnly


class _TextWrapper:

    def __init__(self, text):
        self._text = text

    def __str__(self) -> str:
        return self._text


class _PrefixArgumentProcessor(CommandArgProcessor):

    def __init__(self, prefix):
        self._prefix = prefix

    def process_args(self, *args):
        return [f'{self._prefix}{arg}' for arg in args]

@runOnUnixOnly
class TestCommand(TestCase):

    def test_cmd(self):
        wc_c = cmd('wc', '-c', check=True)
        res = wc_c(cmd_in='1234').standard_output.strip()
        self.assertEqual(
            '4',
            res
        )

    def test_shell_cmd(self):
        wc_c = shell_cmd('echo -n "$1" | wc -c', check=True)
        self.assertEqual(
            '9',
            wc_c('123456789').standard_output.strip()
        )

    def test_cmd_should_raise_exception_on_error_when_instructed(self):
        exception = None
        try:
            cmd('/bin/false', check=True).exec()
        except ProcessExecutionException as ex:
            exception = ex

        self.assertIsNotNone(exception)
        self.assertEqual(exception.result.return_code, 1)

    def test_command_should_respect_skip_config_no_args(self):
        res = cmd('/bin/echo', '-n', '123').exec(skip=SkipConfig(skip_when_no_args=True, skipped_code=42))
        self.assertEqual(42, res.return_code)
        self.assertEqual('Execution skipped', res.standard_output)

    def test_command_should_respect_skip_config_skip(self):
        res = cmd('/bin/echo', '-n', '123').exec(skip=SkipConfig(skip=True, skipped_code=42))
        self.assertEqual(42, res.return_code)
        self.assertEqual('Execution skipped', res.standard_output)

    def test_command_should_not_skip_when_args_were_provided(self):
        res = cmd('/bin/echo', '-n', '123').exec('abc', skip=SkipConfig(skip_when_no_args=True, skipped_code=42))
        self.assertEqual(0, res.return_code)
        self.assertEqual('123 abc', res.standard_output)

    def test_command_should_change_arguments_to_string(self):
        res = cmd('/bin/echo', '-n', _TextWrapper('123')).exec(_TextWrapper('abc'))
        self.assertEqual(0, res.return_code)
        self.assertEqual('123 abc', res.standard_output)

    def test_command_should_use_arguments_processor_on_exec_args(self):
        command = Command(
            command=['/bin/echo', '-n', _TextWrapper('123')],
            argument_processor=_PrefixArgumentProcessor('arg:')
        )
        res = command.exec(_TextWrapper('abc'))
        self.assertEqual(0, res.return_code)
        self.assertEqual('123 arg:abc', res.standard_output)

    def test_command_should_capture_both_stdout_and_stderr(self):
        res = shell_cmd('echo -n err_text >&2 ; echo -n out_text', capture=True).exec()
        self.assertEqual(0, res.return_code)
        self.assertEqual('out_text', res.standard_output)
        self.assertEqual('err_text', res.error_output)

    def test_command_should_not_capture_output_when_instructed(self):
        res = shell_cmd('echo -n err_text >&2 ; echo -n out_text', capture=False).exec()
        self.assertEqual(0, res.return_code)
        self.assertEqual('', res.standard_output)
        self.assertEqual('', res.error_output)

    def test_command_should_respect_cwd_argument(self):
        # grab some known directory
        dir1 = os.path.dirname(os.path.abspath(__file__))
        dir2 = os.path.dirname(dir1)

        # run with pre-set cwd
        pwd1 = cmd('bash', '-c', 'echo -n `pwd`', check=True, capture=True, cwd=dir1)
        self.assertEqual(dir1, pwd1.exec().standard_output)
        
        pwd2 = cmd('bash', '-c', 'echo -n `pwd`', check=True, capture=True, cwd=dir2)
        self.assertEqual(dir2, pwd2.exec().standard_output)

        # now check with overrides
        self.assertEqual(dir2, pwd1.exec(cwd=dir2).standard_output)
        self.assertEqual(dir1, pwd2.exec(cwd=dir1).standard_output)

        # check with default empty and overrides
        pwd = cmd('bash', '-c', 'echo -n `pwd`')
        self.assertEqual(dir1, pwd.exec(cwd=dir1).standard_output)
        self.assertEqual(dir2, pwd.exec(cwd=dir2).standard_output)

        # shell command should also work
        self.assertEqual(dir2, shell_cmd('echo -n `pwd`', cwd=dir2).exec().standard_output)