import subprocess
from typing import Union, Iterable

from pyshrimp.utils.string_wrapper import StringWrapper
from pyshrimp.utils.subprocess_utils import ProcessExecutionResult


class _ExecutingProcess:

    def __init__(self, command: Union[str, Iterable], process: subprocess.Popen) -> None:
        self._process = process
        self._command = command
        self._closed = False
        self._result = None

    def close(self, timeout=None) -> ProcessExecutionResult:
        # TODO: try catch

        if not self._closed:
            (out, err) = self._process.communicate(timeout=timeout)
            self._result = ProcessExecutionResult(
                self._command, StringWrapper(out), StringWrapper(err), self._process.returncode
            )
            self._closed = True

        return self._result

    @property
    def stdout(self):
        return self._process.stdout

    def detach_stdout(self):
        self._process.stdout = None


def _spawn_process(command: Union[str, Iterable], cmd_in=None, cwd=None, env=None, capture_err_output=False) -> _ExecutingProcess:
    # TODO: support for string stdin?
    # TODO: try catch support
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL if cmd_in is None else cmd_in,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if capture_err_output else None,
        # TODO: binary output support
        universal_newlines=True,
        shell=False,
        cwd=cwd,
        env=env
    )

    return _ExecutingProcess(command, process)
