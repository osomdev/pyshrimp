import io
import os
from threading import Thread
from typing import Callable

from pyshrimp._internal.pipes.utils import _collect_stream_to_string
from pyshrimp.execution_pipeline.pipeline_api import PipelineElement, PipelineExecutionResult


class _AsyncFunctionPipelineElement(PipelineElement):

    def __init__(self, function: Callable, left_out):
        super().__init__()

        self._left_out = left_out
        self._function = function
        self._result = None
        self._stdout_collected = None
        self._exception = None

        # create output pipe for function
        pipe_r, pipe_w = os.pipe()

        self._open_write_pipe = io.open(pipe_w, 'wb')

        # TODO: add support for binary streams
        self._right_out_writer = io.TextIOWrapper(
            self._open_write_pipe,
            write_through=True,
            line_buffering=False,
            encoding='UTF-8'
        )

        open_read_pipe = io.open(pipe_r, 'rb')
        self._right_out = io.TextIOWrapper(
            open_read_pipe,
            encoding='UTF-8'
        )

        self._thread = Thread(target=self._thread_main)
        self._thread.start()

    def _thread_main(self):
        try:
            self._result = self._function(
                stream_input=self._left_out,
                stream_output=self._right_out_writer
            )
        except Exception as ex:
            self._exception = ex
        finally:
            self._right_out_writer.close()

    def _close_once(self):
        self._thread.join()
        self._stdout_collected = _collect_stream_to_string(self._right_out)
        # TODO: ?? if should_raise and self._exception: raise AsyncFunctionInvocationException(self._exception)

    def stdout_for_pipe(self):
        return self._right_out

    @property
    def result(self) -> PipelineExecutionResult:
        return PipelineExecutionResult(
            result=self._result,
            exception=self._exception,
            stdout=self._stdout_collected,
            stderr=None
        )
