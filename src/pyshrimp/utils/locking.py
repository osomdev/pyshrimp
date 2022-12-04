from contextlib import contextmanager
import platform
from typing import Type

from pyshrimp._internal.locking.file_based_lock_internal import FileBasedLockInternal


def _get_file_based_lock_impl() -> Type[FileBasedLockInternal]:
    system_id = platform.system().lower()

    if system_id == 'windows':
        from pyshrimp._internal.locking.file_based_lock_windows import get_file_based_lock_impl_for_windows
        return get_file_based_lock_impl_for_windows()
    else:
        from pyshrimp._internal.locking.file_based_lock_posix import get_file_based_lock_impl_for_posix
        return get_file_based_lock_impl_for_posix()


_FileBasedLockImpl = _get_file_based_lock_impl()

class FileBasedLock:

    def __init__(self, lock_file_path):
        self._delegate: FileBasedLockInternal = _FileBasedLockImpl(
            lock_file_path=lock_file_path
        )

    def try_lock(self):
        return self._delegate.try_lock()

    def release_lock(self):
        return self._delegate.release_lock()

    @contextmanager
    def acquire_lock(self):
        locked = self.try_lock()
        try:
            yield locked
        finally:
            if locked:
                self.release_lock()


@contextmanager
def acquire_file_lock(lock_file_path):
    with FileBasedLock(lock_file_path).acquire_lock() as locked:
        yield locked

