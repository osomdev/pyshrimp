import subprocess
from typing import Union, Iterable

from pyshrimp.utils.string_wrapper import StringWrapper

RETURN_CODE_EXECUTION_FAILED = 300


class ProcessExecutionResult(object):
    def __init__(
            self,
            command: Union[str, Iterable],
            standard_output: StringWrapper,
            error_output: StringWrapper,
            return_code: int,
            exception=None
    ):
        self.command = command
        self.standard_output = standard_output
        self.error_output = error_output
        self.return_code = return_code
        self.exception = exception

    def is_ok(self):
        return self.return_code == 0

    def raise_if_not_ok(self):
        if not self.is_ok():
            reason = (
                f'Got exception: {self.exception}'
                if self.return_code == RETURN_CODE_EXECUTION_FAILED
                else f'Command returned non zero exit code: {self.return_code}'
            )

            raise ProcessExecutionException(
                message=f'Command execution failed: {reason}',
                result=self
            )
        return self

    def execution_report(self, message: str):
        command_as_string = self.command if isinstance(self.command, str) else ' '.join(self.command)
        report = (
            f'{message}\n'
            f'  Command: {command_as_string}\n'
            f'  Exit code: {self.return_code}\n'
            f'  Stdout: {self.standard_output!r}\n'
            f'  Error: {self.error_output!r}'
        )
        if self.exception:
            report += f'\n  Exception: {self.exception}'

        return report

    def __str__(self, *args, **kwargs):
        return 'CommandExecutionResult{}'.format(repr(self.__dict__))

    @property
    def out(self):
        return self.standard_output

    @property
    def err(self):
        return self.error_output

    @property
    def exit_code(self):
        return self.return_code


class ProcessExecutionException(Exception):

    def __init__(self, message: str, result: ProcessExecutionResult) -> None:
        super().__init__(message)
        self.result = result
        self.message = message

    def __str__(self):
        return self.result.execution_report(self.message)


def run_process(command: Union[str, Iterable], timeout=None, cmd_in=None, capture_out=True, capture_err=True,
                run_in_shell=False, cwd=None, env=None) -> ProcessExecutionResult:
    try:
        p = subprocess.Popen(
            command,
            stdin=None if cmd_in is None else subprocess.PIPE,
            stdout=subprocess.PIPE if capture_out else None,
            stderr=subprocess.PIPE if capture_err else None,
            universal_newlines=True,
            shell=run_in_shell,
            cwd=cwd,
            env=env
        )

        (out, err) = p.communicate(input=cmd_in, timeout=timeout)

        return ProcessExecutionResult(
            command=command,
            standard_output=StringWrapper(out or ''),
            error_output=StringWrapper(err or ''),
            return_code=p.returncode
        )

    except Exception as e:
        return ProcessExecutionResult(
            command=command,
            standard_output=StringWrapper(''),
            error_output=StringWrapper(str(e)),
            return_code=RETURN_CODE_EXECUTION_FAILED,
            exception=e
        )
