# noinspection PyMethodMayBeStatic
from dataclasses import dataclass
from typing import Optional, Any

# noinspection PyProtectedMember
from pyshrimp._internal.pipes.utils import _collect_stream_to_string


@dataclass
class PipelineExecutionResult:
    stdout: Optional[str]
    stderr: Optional[str]
    result: Optional[Any]
    exception: Optional[Exception]


class PipelineElement:

    def __init__(self):
        self._closed = False

    def _close_once(self):
        pass

    def close(self):
        if not self._closed:
            self._close_once()
            self._closed = True

    def stdout_for_pipe(self):
        raise NotImplementedError()

    @property
    def result(self) -> PipelineExecutionResult:
        raise NotImplementedError


class StringPipelineElement(PipelineElement):

    def __init__(self, out: str) -> None:
        super().__init__()
        self._out = out

    def stdout_for_pipe(self):
        return self._out

    @property
    def result(self) -> PipelineExecutionResult:
        return PipelineExecutionResult(
            result=None,
            stdout=self._out,
            stderr=None,
            exception=None
        )


class StreamPipelineElement(PipelineElement):

    def __init__(self, out) -> None:
        super().__init__()
        self._out = out
        self._out_collected = None

    def stdout_for_pipe(self):
        return self._out

    def _close_once(self):
        self._out_collected = _collect_stream_to_string(self._out)

    @property
    def result(self) -> PipelineExecutionResult:
        return PipelineExecutionResult(
            result=None,
            stdout=self._out_collected,
            stderr=None,
            exception=None
        )


class PipelineTerminator:
    pass


class PipelineTerminatorStdout:
    pass
