import dataclasses
import threading
from typing import Callable, Optional, Any, TypeVar, Generic

T = TypeVar('T')


@dataclasses.dataclass
class ExecutionResult(Generic[T]):
    exception: Optional[Exception]
    result: Optional[T]
    timed_out: bool


class _BackgroundFunctionWrapper:

    def __init__(self, target: Callable):
        self._wrapped = target
        self.exception = None
        self.result = None
        self.completed = False

    def run(self):
        # noinspection PyBroadException
        try:
            self.result = self._wrapped()
        except Exception as ex:
            self.exception = ex

        self.completed = True

    def __call__(self, *args, **kwargs):
        return self.run()


def run_with_timeout(target: Callable[[], T], timeout_sec: float, on_error: Callable = None, raise_on_exception=True, raise_on_timeout=True) -> ExecutionResult[T]:
    fn = _BackgroundFunctionWrapper(target)

    t = threading.Thread(target=fn)
    t.start()
    t.join(timeout_sec)

    on_error = on_error or (lambda: True)

    result = ExecutionResult(
        exception=fn.exception,
        result=fn.result,
        timed_out=not fn.completed
    )

    if result.timed_out:
        on_error()
        if raise_on_timeout:
            raise TimeoutError()

    elif result.exception is not None:
        on_error()
        if raise_on_exception:
            raise fn.exception

    return result
