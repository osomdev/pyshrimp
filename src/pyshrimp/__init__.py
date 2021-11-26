# noinspection PyProtectedMember
from pyshrimp._internal.wrapper.mainwrapper import _run as run
from pyshrimp.execution_pipeline.pipeline import pipe, ExecutionPipeline
from pyshrimp.execution_pipeline.pipeline_api import PipelineExecutionResult
from pyshrimp.execution_pipeline.pipeline_starter import PIPE, PIPE_END, PIPE_END_STDOUT
from pyshrimp.utils.command import cmd, shell_cmd, Command, SkipConfig, CommandArgProcessor, DefaultCommandArgProcessor
from pyshrimp.utils.dotdict import as_dot_dict
from pyshrimp.utils.filesystem import ls, glob_ls
from pyshrimp.utils.locking import acquire_file_lock, FileBasedLock
from pyshrimp.utils.logging import log, exit_error
from pyshrimp.utils.matching import re_match_all
from pyshrimp.utils.parallel import in_background
from pyshrimp.utils.string_wrapper import StringWrapper
from pyshrimp.utils.subprocess_utils import run_process, ProcessExecutionException, ProcessExecutionResult
from pyshrimp.utils.wait import wait_until, wait_until_gen
