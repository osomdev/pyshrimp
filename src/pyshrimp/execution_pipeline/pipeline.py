import inspect
import os
import sys
from threading import Thread
from typing import Callable, List

# noinspection PyProtectedMember
from pyshrimp._internal.pipes.async_function import _AsyncFunctionPipelineElement
from pyshrimp.exception import IllegalStateException, IllegalArgumentException
from pyshrimp.execution_pipeline.pipeline_api import PipelineElement, StringPipelineElement, StreamPipelineElement, PipelineExecutionResult, PipelineTerminator, PipelineTerminatorStdout
from pyshrimp.utils.command import cmd, shell_cmd


class ExecutionPipeline:

    def __init__(self) -> None:
        self._items: List[PipelineElement] = []

    def attach_stdin(self):
        if self._items:
            raise IllegalStateException('Attaching STDIN makes only sense at the start of pipeline.')

        self._items.append(StreamPipelineElement(sys.stdin))
        return self

    def attach_text(self, text: str):
        if self._items:
            raise IllegalStateException('Attaching text makes only sense at the start of pipeline.')

        self._items.append(StringPipelineElement(text))
        return self

    def attach_function(self, fn):
        fn_args = dict(inspect.signature(fn).parameters.items())

        if 'stream_input' in fn_args and 'stream_output' in fn_args:
            # async function
            self._attach_async_connector(
                connect_method=lambda left_out: _AsyncFunctionPipelineElement(function=fn, left_out=left_out)
            )

        elif 'stream_input' in fn_args or 'stream_output' in fn_args:
            # invalid async function
            raise IllegalArgumentException(
                f'Asynchronous function must accept both stream_input and stream_output but found only one.'
                f' Function args: {", ".join(fn_args.keys())}'
            )

        else:
            # sync function
            self._attach_sync_connector(
                connect_method=lambda left_out: StringPipelineElement(fn(left_out))
            )

        return self

    def _get_left(self):
        return self._items[-1] if self._items else None

    def _attach_async_connector(self, connect_method):
        left = self._get_left()
        left_out = left.stdout_for_pipe() if left else None

        if isinstance(left_out, str):
            # Connector expects to see streaming input, transform the string to TextIO
            pipe_r, pipe_w = os.pipe()

            input_for_pipe = left_out

            def _write_to_pipe():
                os.write(pipe_w, input_for_pipe.encode('utf-8'))
                os.close(pipe_w)

            # write to pipe in new thread
            # this should workaround any deadlock situations
            Thread(target=_write_to_pipe).start()

            left_out = pipe_r

        self._items.append(connect_method(left_out))

    def _attach_sync_connector(self, connect_method: Callable[[str], PipelineElement]):
        left = self._get_left()

        # We need to consume output as the connector does not support streaming
        if left:
            left.close()
            left_out = left.result.stdout
        else:
            left_out = None

        self._items.append(connect_method(left_out))

    def attach(self, right):
        if isinstance(right, PipelineTerminator):
            return self.close()

        elif isinstance(right, PipelineTerminatorStdout):
            return self.close().stdout

        elif isinstance(right, str):
            self.attach(
                shell_cmd(
                    script=right,
                    check=False
                )
            )

        elif isinstance(right, list):
            self.attach(
                cmd(
                    command=right,
                    check=False
                )
            )

        elif hasattr(right, 'pipe_connect_async'):
            self._attach_async_connector(right.pipe_connect_async)

        elif hasattr(right, 'pipe_connect_sync'):
            self._attach_sync_connector(right.pipe_connect_sync)

        elif callable(right):
            self.attach_function(right)

        else:
            raise Exception(f'Unsupported type for right: {type(right)}')

        return self

    def attach_all(self, *elements):
        for el in elements:
            self.attach(el)

        return self

    def close(self) -> PipelineExecutionResult:
        for el in self._items:
            el.close()

        return self._get_left().result

    def __or__(self, other) -> 'ExecutionPipeline':
        return self.attach(other)

    def __ror__(self, other):
        raise Exception(
            f'Unsupported pipe - left side is not a pipe! Tried to connect the {other} with {self}'
        )


def pipe(*elements) -> PipelineExecutionResult:
    return ExecutionPipeline().attach_all(*elements).close()
