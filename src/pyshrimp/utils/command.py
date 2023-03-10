import os
from typing import Iterable, List, Optional, TextIO, Union, Dict

# noinspection PyProtectedMember
from pyshrimp._internal.utils.subprocess_utils import _ExecutingProcess, _spawn_process
from pyshrimp.execution_pipeline.pipeline_api import PipelineElement, PipelineExecutionResult
from pyshrimp.utils.collections import first_not_null
from pyshrimp.utils.string_wrapper import StringWrapper
from pyshrimp.utils.subprocess_utils import (
    ProcessExecutionResult,
    run_process
)


class SkipConfig:

    def __init__(
        self,
        skip=False,
        skip_when_no_args=False,
        skipped_out='Execution skipped',
        skipped_err='',
        skipped_code=0
    ):
        self._skip = skip
        self._skip_when_no_args = skip_when_no_args
        self.skipped_code = skipped_code
        self.skipped_err = skipped_err
        self.skipped_out = skipped_out

    def should_skip(self, args):
        if self._skip:
            return True

        if self._skip_when_no_args:
            if not any(args):
                return True

        return False


class CommandArgProcessor:
    def process_args(self, *args):
        raise NotImplementedError()


class DefaultCommandArgProcessor(CommandArgProcessor):

    def process_args(self, *args):
        res = []
        for el in args:
            if isinstance(el, str):
                res.append(el)
            elif isinstance(el, Iterable):
                res += [str(sub_el) for sub_el in el]
            else:
                res.append(str(el))

        return res


class _CommandPipelineElement(PipelineElement):

    def __init__(self, command: 'Command', executing_command: _ExecutingProcess) -> None:
        super().__init__()
        self._executing_command = executing_command
        self._command = command
        self._result: Optional[ProcessExecutionResult] = None
        self._stdout = self._executing_command.stdout

    def _close_once(self):
        self._result = self._executing_command.close()
        self._stdout.close()

    def stdout_for_pipe(self):
        self._executing_command.detach_stdout()
        return self._stdout

    @property
    def result(self) -> PipelineExecutionResult:
        return PipelineExecutionResult(
            stdout=self._result.standard_output,
            stderr=self._result.error_output,
            result=self._result,
            exception=self._result.exception
        )


class Command:
    def __init__(
        self,
        command: List[str],
        check: bool = True,
        capture: bool = True,
        argument_processor: CommandArgProcessor = None,
        env: Dict[str, str] = None,
        env_append: bool = True,
        cwd: Optional[str] = None
    ):
        self._env = env
        self._env_append = env_append
        self._check = check
        self._capture = capture
        self._argument_processor = argument_processor or DefaultCommandArgProcessor()
        # by-design we do not use argument processor this list - just cast everything to string to ensure we won't blow up
        self._command = [str(el) for el in command]
        self._cwd = cwd

    def __call__(self, *args, **kwargs):
        return self.exec(*args, **kwargs)

    def exec(
        self, *args, cmd_in=None,
        check: Optional[bool] = None,
        capture: Optional[bool] = None,
        skip: Union[bool, SkipConfig] = False,
        cwd: Optional[str] = None
    ) -> ProcessExecutionResult:

        command = self._build_command(args)

        if isinstance(skip, bool):
            skip = SkipConfig(skip=skip)

        if skip.should_skip(args):
            return ProcessExecutionResult(
                command=command,
                standard_output=StringWrapper(skip.skipped_out),
                error_output=StringWrapper(skip.skipped_err),
                return_code=skip.skipped_code
            )

        _capture = first_not_null(capture, self._capture)

        res = run_process(
            command=command,
            capture_out=_capture,
            capture_err=_capture,
            cmd_in=cmd_in,
            env=self._build_env(),
            cwd=first_not_null(cwd, self._cwd)
        )

        if first_not_null(check, self._check):
            res.raise_if_not_ok()

        return res

    def _build_env(self):
        env = os.environ.copy() if self._env_append else {}
        env.update(self._env or {})
        return env

    def with_args(self, *args):
        return Command(
            command=self._build_command(args=args),
            check=self._check,
            capture=self._capture,
            argument_processor=self._argument_processor,
            env=self._env,
            env_append=self._env_append,
            cwd=self._cwd,
        )

    def __str__(self):
        return f'Command({self.__dict__})'

    def _build_command(self, args=None):
        command_args = self._argument_processor.process_args(*(args or []))
        return self._command + command_args

    def pipe_connect_async(self, left_out: TextIO) -> _CommandPipelineElement:
        return _CommandPipelineElement(
            command=self,
            executing_command=_spawn_process(
                command=self._build_command(),
                cmd_in=left_out,
                env=self._build_env(),
                capture_output=self._capture,
                capture_err_output=self._capture,
                cwd=self._cwd
                # TODO: other params like check
            )
        )

    def _spawn(self):
        return _spawn_process(
            command=self._build_command(),
            env=self._build_env(),
            capture_output=self._capture,
            capture_err_output=self._capture,
            cwd=self._cwd
            # TODO: other params like check
        )


def cmd(command: Union[str, List], *args, check=True, capture=True, env: Dict[str, str] = None, env_append=True, cwd: str = None) -> Command:
    if isinstance(command, str):
        command = [command]

    return Command(
        command=command + list(args),
        check=check,
        capture=capture,
        env=env,
        env_append=env_append,
        cwd=cwd
    )


def shell_cmd(script: str, *args: str, check=True, capture=True, env: Dict[str, str] = None, env_append=True, cwd: str = None) -> Command:
    return Command(
        command=['/bin/bash', '-c', script, 'bash'] + [str(el) for el in args],
        check=check,
        capture=capture,
        env=env,
        env_append=env_append,
        cwd=cwd
    )
