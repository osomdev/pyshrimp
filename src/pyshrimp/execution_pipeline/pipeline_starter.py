from pyshrimp.execution_pipeline.pipeline import ExecutionPipeline
from pyshrimp.execution_pipeline.pipeline_api import PipelineTerminator, PipelineTerminatorStdout


# noinspection PyMethodMayBeStatic
class PipelineStarter:

    def empty(self):
        return ExecutionPipeline()

    def stdin(self):
        return self.empty().attach_stdin()

    def text(self, text: str):
        return self.empty().attach_text(text)

    def close(self) -> PipelineTerminator:
        return PipelineTerminator()

    def __or__(self, other) -> ExecutionPipeline:
        return self.empty() | other

    def __ror__(self, other):
        return self.empty() | other


PIPE = PipelineStarter()
PIPE_END = PipelineTerminator()
PIPE_END_STDOUT = PipelineTerminatorStdout()
