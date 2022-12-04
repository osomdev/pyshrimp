import os
from typing import Type

from pyshrimp._internal.locking.file_based_lock_internal import \
    FileBasedLockInternal


def get_file_based_lock_impl_for_windows() -> Type[FileBasedLockInternal]:
    import ctypes
    import ctypes.wintypes
    import msvcrt
    from ctypes.wintypes import BOOL, DWORD, HANDLE

    # https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
    W32_ERROR_LOCK_VIOLATION = 33

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    # https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfile
    win_lock_file_fn_ref = kernel32.LockFile
    win_lock_file_fn_ref.restype = BOOL
    win_lock_file_fn_ref.argtypes = [HANDLE, DWORD, DWORD, DWORD, DWORD]

    def win_lock_file(hFile, dwFileOffsetLow, dwFileOffsetHigh, nNumberOfBytesToLockLow, nNumberOfBytesToLockHigh) -> bool:
        return win_lock_file_fn_ref(hFile, dwFileOffsetLow, dwFileOffsetHigh, nNumberOfBytesToLockLow, nNumberOfBytesToLockHigh)

    # https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-unlockfile
    win_unlock_file_fn_ref = kernel32.LockFile
    win_unlock_file_fn_ref.restype = BOOL
    win_unlock_file_fn_ref.argtypes = [HANDLE, DWORD, DWORD, DWORD, DWORD]

    def win_unlock_file(hFile, dwFileOffsetLow, dwFileOffsetHigh, nNumberOfBytesToLockLow, nNumberOfBytesToLockHigh) -> bool:
        return win_unlock_file_fn_ref(hFile, dwFileOffsetLow, dwFileOffsetHigh, nNumberOfBytesToLockLow, nNumberOfBytesToLockHigh)

    class _FileBasedLockWindows(FileBasedLockInternal):

        def __init__(self, lock_file_path):
            super().__init__(lock_file_path)
            self._hFile = None
            self._lock_fd = None
        
        def try_lock(self):
            if self._lock_fd is not None:
                raise Exception('Cannot lock twice!')

            _lock_fd = open(self._lock_file_path, 'a+')
            try:
                _hFile = msvcrt.get_osfhandle(_lock_fd.fileno())
                lock_acquired = win_lock_file(_hFile, 0, 0, 1, 0)
                if lock_acquired:
                    self._lock_fd = _lock_fd
                    self._hFile = _hFile
                    _lock_fd.seek(0)
                    _lock_fd.write(self._get_lock_info())
                    _lock_fd.truncate()
                    _lock_fd.flush()
                    return True


                lock_error = ctypes.get_last_error()

                if lock_error == W32_ERROR_LOCK_VIOLATION:
                    return False
                else:
                    raise Exception(f'Got an unexpected error while attempting to lock: {lock_error}')

            finally:
                if self._lock_fd == None:
                    # failed to acquire lock, close the file
                    _lock_fd.close()

        def release_lock(self):
            self._assert_locked()

            # clear lock file
            self._lock_fd.seek(0)
            self._lock_fd.truncate()
            self._lock_fd.close()

            # remove lock file
            os.unlink(self._lock_file_path)

            # release lock
            win_unlock_file(self._hFile, 0, 0, 1, 0)

            self._hFile = None
            self._lock_fd = None
        
        def _assert_locked(self):
            if self._hFile is None:
                raise Exception('Illegal state: not locked')


    return _FileBasedLockWindows
