from unittest import TestCase
from unittest.mock import patch

from pyshrimp import log
from pyshrimp.utils.wait import wait_until, wait_until_gen


class MockClock:

    def __init__(self, init_time_value=0):
        self._time = init_time_value
        self._sleep_count = 0

    def time(self):
        return self._time

    def inc_time(self, inc_sec=0):
        self._time += inc_sec


class TestWaitUtils(TestCase):

    def setUp(self) -> None:
        self._clock = MockClock()
        patch('time.time', self._clock.time).start()
        patch('time.sleep', self._clock.inc_time).start()

    def tearDown(self) -> None:
        patch.stopall()

    def test_wait_until_should_wait_for_the_success(self):
        res_collection = []

        with self.assertLogs() as log_context:
            def _collect():
                log(' . collect')
                res = res_collection.copy()
                res_collection.append(len(res_collection))
                return res

            self.assertTrue(
                wait_until(
                    'Collection is not empty',
                    collect=_collect,
                    before_check=lambda res: log(' . before'),
                    before_sleep=lambda res: log(' . after'),
                    check_interval_sec=1,
                )
            )

        self.assertEqual([0, 1], res_collection)
        self.assertEqual(
            [
                'INFO:root:Waiting until Collection is not empty (max wait: 60s)',
                'INFO:root: . collect',
                'INFO:root: . before',
                'INFO:root: . after',
                'INFO:root: . collect',
                'INFO:root: . before',
                'INFO:root: + OK',
                'INFO:root:'
            ],
            log_context.output
        )

    def test_wait_until_should_run_only_once_if_timeout_reached(self):
        invocations = []
        with self.assertLogs() as log_context:
            def _collect():
                log(' . collect')
                invocations.append(len(invocations))
                return False

            self.assertFalse(
                wait_until(
                    'Result is true',
                    collect=_collect,
                    before_check=lambda res: log(' . before'),
                    before_sleep=lambda res: log(' . after'),
                    timeout_sec=0
                )[0]
            )

        self.assertEqual([0], invocations)
        self.assertEqual(
            [
                'INFO:root:Waiting until Result is true (max wait: 0s)',
                'INFO:root: . collect',
                'INFO:root: . before',
                'WARNING:root: ! WARNING: got timeout while waiting until Result is true',
                'INFO:root:'
            ],
            log_context.output
        )

    def test_wait_until_should_return_result_when_completed_successfully(self):
        with self.assertLogs():
            success, result = wait_until(
                'Result is true',
                collect=lambda: 'abc',
                check=lambda res: True,
                timeout_sec=0
            )

            self.assertTrue(success)
            self.assertEqual('abc', result)

    def test_wait_until_should_return_result_when_timeout_is_reached(self):
        with self.assertLogs():
            success, result = wait_until(
                'Result is true',
                collect=lambda: 'abc',
                check=lambda res: False,
                timeout_sec=0
            )

            self.assertFalse(success)
            self.assertEqual('abc', result)

    def test_wait_until_should_rerun_until_timeout(self):
        with self.assertLogs() as log_context:
            def _collect():
                log(' . collect')
                return False

            self.assertFalse(
                wait_until(
                    'Result is true',
                    collect=_collect,
                    before_check=lambda res: log(' . before'),
                    before_sleep=lambda res: log(' . after'),
                    on_timeout=lambda res: log(' ((on timeout))'),
                    check_interval_sec=1,
                    timeout_sec=1.5
                )[0]
            )

        self.assertEqual(
            [
                'INFO:root:Waiting until Result is true (max wait: 1.5s)',
                'INFO:root: . collect',
                'INFO:root: . before',
                'INFO:root: . after',
                'INFO:root: . collect',
                'INFO:root: . before',
                'WARNING:root: ! WARNING: got timeout while waiting until Result is true',
                'INFO:root:',
                'INFO:root: ((on timeout))'
            ],
            log_context.output
        )

    def test_wait_until_generator_should_keep_invoking_until_loop_breaks(self):
        with self.assertLogs() as log_context:
            for step in wait_until_gen('The thing is ready', sleep_interval_sec=1):
                log(f'Running, step: {step}')
                if step >= 1:
                    break

        self.assertEqual(
            [
                'INFO:root:Waiting until The thing is ready (max wait: 60s)',
                'INFO:root:Running, step: 0',
                'INFO:root:Running, step: 1',
                'INFO:root: + OK'
            ],
            log_context.output
        )

    def test_wait_until_generator_should_stop_on_timeout(self):
        with self.assertLogs() as log_context:
            for step in wait_until_gen('The thing is ready', sleep_interval_sec=1, timeout_seconds=1.5):
                log(f'Running, step: {step}')
                if step >= 10:
                    break

        self.assertEqual(
            [
                'INFO:root:Waiting until The thing is ready (max wait: 1.5s)',
                'INFO:root:Running, step: 0',
                'INFO:root:Running, step: 1',
                'WARNING:root: ! WARNING: got timeout while waiting until The thing is ready'
            ],
            log_context.output
        )

    def test_wait_until_should_not_log_when_silent_mode_is_active(self):
        with self.assertLogs() as log_context:
            log('start')
            self.assertTrue(wait_until(
                'Result is true',
                collect=lambda: True,
                timeout_sec=0,
                silent=True
            )[0])
            self.assertFalse(
                wait_until(
                    'Result is true',
                    collect=lambda: False,
                    timeout_sec=0,
                    silent=True
                )[0]
                )
            log('end')

        self.assertEqual(
            [
                'INFO:root:start',
                'INFO:root:end'
            ],
            log_context.output
        )
