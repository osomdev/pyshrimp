
import os
import threading


class FileBasedLockInternal:

    def __init__(self, lock_file_path):
        self._lock_file_path = lock_file_path

    def _get_lock_info(self) -> str:
        return f'PID: {os.getpid()} THREAD: {threading.current_thread().ident}'

    def try_lock(self):
        raise NotImplementedError()

    def release_lock(self):
        raise NotImplementedError()


