import re
import threading
from functools import partial
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from pyshrimp.exception import IllegalArgumentException
from pyshrimp.execution_pipeline.pipeline import ExecutionPipeline
from pyshrimp.execution_pipeline.pipeline_starter import PIPE, PIPE_END, PIPE_END_STDOUT
from pyshrimp.utils.command import cmd, shell_cmd
from common.platform_utils import runOnUnixOnly

@runOnUnixOnly
class TestExecutionPipeline(TestCase):

    def test_example_object_oriented_syntax(self):
        p = ExecutionPipeline()
        # feed pipeline with text input
        p.attach_text('Hello world!')
        # run the wc command
        p.attach(cmd('wc'))
        # run awk, using the shell wrapper
        p.attach("awk '{print $3}'")
        # process the output with function - pad with zeros
        p.attach_function(
            lambda stdin: f'{int(stdin.strip()):05}'
        )
        # close pipeline and collect output
        res = p.close().stdout
        self.assertEqual(res, '00012')

    def test_example_pipe_syntax(self):
        res = (
            # feed pipeline with text input
            PIPE.text('Hello world!')
            # run the wc command
            | cmd('wc')
            # run awk, using the shell wrapper
            | "awk '{print $3}'"
            # process the output with function - pad with zeros
            | (lambda stdin: f'{int(stdin.strip()):05}')
            # close pipeline and collect output
            | PIPE_END_STDOUT
        )
        self.assertEqual(res, '00012')

    def test_example_mixed_pipe_and_object_oriented_syntax(self):
        p = (
            # feed pipeline with text input
            PIPE.text('Hello world!')
            # run the wc command
            | cmd('wc')
            # run awk, using the shell wrapper
            | "awk '{print $3}'"
        )
        # process the output with function - pad with zeros
        p.attach_function(lambda stdin: f'{int(stdin.strip()):05}')
        # close pipeline and collect output
        res = p.close().stdout
        self.assertEqual(res, '00012')

    def test_mixed_pipeline_execution_without_pipe_syntax(self):
        p = ExecutionPipeline()
        p.attach(shell_cmd('echo hello'))
        p.attach('wc')
        p.attach("awk '{print $3}'")
        p.attach_function(
            lambda stdin: f'<<{stdin.strip()}>>'
        )
        p.attach('wc -c')
        p.attach_function(
            lambda stdin: f'::{stdin.strip()}::'
        )
        p.attach_function(
            lambda stdin: f'//{stdin.strip()}//'
        )
        res = p.close().stdout
        self.assertEqual(res, '//::5:://')

    def test_mixed_pipeline_with_pipe_syntax(self):
        echo = cmd('echo')
        res = (
            PIPE
            | echo.with_args('-n', '1234')
            | 'cat'
            | shell_cmd("wc | awk '{print $3}'")
            | (lambda stdin: f'out={stdin.strip()}')
            | partial(re.sub, '=', '> ')
            | (lambda stdin: f'{stdin} :)')
        ).close().stdout
        self.assertEqual(res, 'out> 4 :)')

    def test_pipeline_with_simple_shell_command_string(self):
        res = (
            PIPE
            | 'echo -n hello world'
        ).close().stdout
        self.assertEqual(res, 'hello world')

    def test_pipeline_terminator_should_close_pipe(self):
        res = (
            PIPE
            | 'echo -n hello world'
            | PIPE_END
        ).stdout
        self.assertEqual(res, 'hello world')

    def test_pipeline_stdout_terminator_should_close_pipe_and_return_stdout(self):
        res = PIPE | 'echo -n hello world' | PIPE_END_STDOUT
        self.assertEqual(res, 'hello world')

    def test_pipeline_with_command_object(self):
        res = (
            PIPE
            | cmd(['/bin/echo', 'hello world'])
        ).close().stdout
        self.assertEqual(res, 'hello world\n')

    def test_pipeline_with_command_chain(self):
        res = (
            PIPE
            | cmd(['/bin/echo', '-n', 'hello world'])
            | cmd(['cat'])
            | cmd(['wc', '-c'])
        ).close().stdout
        self.assertEqual(res, '11\n')

    def test_pipeline_with_text_input_and_command(self):
        res = (
            PIPE.text('hello world')
            | cmd(['wc', '-c'])
        ).close().stdout
        self.assertEqual(res, '11\n')

    def test_pipeline_with_stdin_only_should_collect_input(self):
        with patch('sys.stdin', StringIO('Hello!')):
            res = PIPE.stdin().close().stdout
            self.assertEqual(res, 'Hello!')

    def test_pipeline_with_mixed_commands_and_sync_functions(self):
        res = (
            PIPE.text('hello world')
            | 'cat'
            | 'wc -c'
            | (lambda out: f'<{out.strip()}>')
            | (lambda out: re.sub('[<>]', '|', out))
            | 'cat'
            | (lambda out: out.replace('|', ':'))
            | 'cat'
            | (lambda out: out.replace(':', '/'))
        ).close().stdout
        self.assertEqual(res, '/11/')

    def test_pipeline_with_background_functions_should_process_line_by_line(self):
        output_in_order = []
        line_processed_event = threading.Event()

        # noinspection PyUnusedLocal
        def _numbers_producer(stream_input, stream_output):
            for i in range(1, 6):
                stream_output.write(f'{i}\n')
                stream_output.flush()

                # wait until consumer reads - to prove the streaming
                line_processed_event.wait(timeout=5)
                if not line_processed_event.is_set():
                    self.fail(f'Line {i} was not read in time!')

                line_processed_event.clear()

        def _bg_processor_1(stream_input, stream_output):
            for line in stream_input:
                output_in_order.append(f'processor 1: {line.strip()}')
                stream_output.write(line)
                stream_output.flush()

        def _bg_processor_2(stream_input, stream_output):
            for line in stream_input:
                output_in_order.append(f'processor 2: {line.strip()}')
                stream_output.write(line)
                stream_output.flush()
                line_processed_event.set()

        res = (
            PIPE
            # produce numbers stream (line by line)
            | _numbers_producer
            # capture stream elements
            | _bg_processor_1
            # process stream with sed
            | "sed -u 's/^/=> /'"
            # capture stream (also signals number producer)
            | _bg_processor_2
        ).close().stdout

        self.assertEqual(
            res,
            '=> 1\n'
            '=> 2\n'
            '=> 3\n'
            '=> 4\n'
            '=> 5\n'
        )

        self.assertEqual(
            output_in_order,
            [
                'processor 1: 1',
                'processor 2: => 1',
                'processor 1: 2',
                'processor 2: => 2',
                'processor 1: 3',
                'processor 2: => 3',
                'processor 1: 4',
                'processor 2: => 4',
                'processor 1: 5',
                'processor 2: => 5'
            ]
        )

    def test_should_raise_when_async_function_is_missing_stream_input(self):
        with self.assertRaisesRegex(
            IllegalArgumentException,
            r'Asynchronous function must accept both stream_input and stream_output but found only one. Function args: stream_output'
        ):
            (PIPE | (lambda stream_output: None)).close()

    def test_should_raise_when_async_function_is_missing_stream_output(self):
        with self.assertRaisesRegex(
            IllegalArgumentException,
            r'Asynchronous function must accept both stream_input and stream_output but found only one. Function args: stream_input'
        ):
            (PIPE | (lambda stream_input: None)).close()
