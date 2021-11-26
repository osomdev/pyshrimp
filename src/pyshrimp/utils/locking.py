import fcntl
import os
from contextlib import contextmanager


class FileBasedLock:

    def __init__(self, lock_file_path):
        self._lock_file_path = lock_file_path
        self._lock_fd = None

    def try_lock(self):
        if self._lock_fd is not None:
            raise Exception('Cannot lock twice!')

        fd = os.open(
            self._lock_file_path,
            os.O_RDWR | os.O_CREAT | os.O_APPEND
        )

        try:
            fcntl.flock(
                fd,
                # obtain exclusive lock, fail if unable to lock
                fcntl.LOCK_EX | fcntl.LOCK_NB
            )
        except (IOError, OSError):
            # failed to lock
            os.close(fd)
            return False

        # let's open file again to erase it and store our PID for reference
        with open(self._lock_file_path, 'w') as f:
            f.write(f'PID: {os.getpid()}')

        # lock acquired
        self._lock_fd = fd

        return True

    def release_lock(self):
        self._assert_locked()

        # clear lock file
        open(self._lock_file_path, 'w').close()

        # release lock
        fd = self._lock_fd
        self._lock_fd = None
        fcntl.flock(fd, fcntl.F_UNLCK)
        os.close(fd)

    def _assert_locked(self):
        if self._lock_fd is None:
            raise Exception('Illegal state: not locked')

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
    lock = FileBasedLock(lock_file_path)
    locked = lock.try_lock()
    try:
        yield locked
    finally:
        if locked:
            lock.release_lock()
