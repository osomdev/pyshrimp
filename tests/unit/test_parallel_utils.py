import threading
from unittest import TestCase

from pyshrimp.utils.parallel import in_background


class _BgFunction:

    def __init__(self, result):
        self.result = result
        self.started = threading.Event()
        self.latch = threading.Event()

    def run(self):
        self.started.set()
        self.latch.wait(timeout=10)
        return self.result


class Test(TestCase):

    def test_in_background_should_run_function_in_thread(self):
        fn1 = _BgFunction('res1')
        fn2 = _BgFunction('res2')

        # start both functions
        fn1_res = in_background(fn1.run)
        fn2_res = in_background(fn2.run)

        # both functions should start
        self.assertTrue(fn1.started.wait(1))
        self.assertTrue(fn2.started.wait(1))

        # both functions should be still running
        self.assertFalse(fn1_res.ready())
        self.assertFalse(fn2_res.ready())

        # signal 2nd function to exit and check result
        fn2.latch.set()
        self.assertEqual(fn2.result, fn2_res.get(1))

        # signal 1st function to exit and check result
        fn1.latch.set()
        self.assertEqual(fn1.result, fn1_res.get(1))


