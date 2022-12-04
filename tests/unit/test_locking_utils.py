import os.path
import threading
from collections import Counter
from tempfile import TemporaryDirectory
from unittest import TestCase

from pyshrimp import FileBasedLock


class _LockTester:

    def __init__(self, lock_file_path):
        self.start_latch = threading.Event()
        self.running = threading.Event()
        self.end_latch = threading.Event()
        self.lock_attempted = threading.Event()
        self.lock = FileBasedLock(lock_file_path)
        self.result = None
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.running.set()
        self.start_latch.wait(1)
        self.result = self.lock.try_lock()
        self.lock_attempted.set()
        self.end_latch.wait(1)
        if self.result:
            self.lock.release_lock()

    def join(self):
        return self.thread.join()


class Test(TestCase):

    def test_lock_should_be_only_obtainable_once(self):
        with TemporaryDirectory() as temp_dir:
            lock_file_path = os.path.join(temp_dir, 'lockfile')

            # first attempt should be successful
            lock1 = FileBasedLock(lock_file_path)
            self.assertTrue(lock1.try_lock())

            # next attempts should fail
            for i in range(10):
                lock_n = FileBasedLock(lock_file_path)
                self.assertFalse(lock_n.try_lock())

            # now release lock
            lock1.release_lock()

            # acquire lock again
            lock2 = FileBasedLock(lock_file_path)
            self.assertTrue(lock2.try_lock())
            lock2.release_lock()

    def test_lock_should_be_resilient_to_race_conditions(self):
        for _ in range(10):
            with TemporaryDirectory() as temp_dir:
                lock_file_path = os.path.join(temp_dir, 'lockfile')

                testers = [_LockTester(lock_file_path) for _ in range(10)]

                self.assertTrue(
                    all(t.running.wait(1) for t in testers),
                    'All testers should be running'
                )

                for t in testers:
                    t.start_latch.set()

                self.assertTrue(
                    all(t.lock_attempted.wait(1) for t in testers),
                    'All testers should attempted to acquire lock'
                )

                for t in testers:
                    t.end_latch.set()

                for t in testers:
                    t.join()

                self.assertEqual(
                    {
                        True: 1,
                        False: len(testers) - 1
                    },
                    dict(Counter([t.result for t in testers]).items())
                )

    def test_lock_should_add_lock_details_to_file(self):
        with TemporaryDirectory() as temp_dir:
            lock_file_path = os.path.join(temp_dir, 'lockfile')
    
            lock = FileBasedLock(lock_file_path)

            with lock.acquire_lock() as locked:
                self.assertTrue(locked)

                with open(lock_file_path, 'r') as f:
                    lock_file_contents = f.read()
                    self.assertRegex(lock_file_contents, r'PID: \d+ THREAD: \d+')

    def test_lock_file_should_be_removed_after_lock_release(self):
        with TemporaryDirectory() as temp_dir:
            lock_file_path = os.path.join(temp_dir, 'lockfile')
    
            lock = FileBasedLock(lock_file_path)

            with lock.acquire_lock() as locked:
                self.assertTrue(locked)

                self.assertTrue(os.path.exists(lock_file_path))

            self.assertFalse(os.path.exists(lock_file_path))