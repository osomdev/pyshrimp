import logging
import time
from typing import Callable, TypeVar

T = TypeVar('T')
_log = logging.getLogger()


def wait_until_gen(
    waiting_until: str,
    timeout_seconds=60,
    sleep_interval_sec=1
):
    _log.info(f'Waiting until {waiting_until} (max wait: {timeout_seconds}s)')
    timeout_at = time.time() + timeout_seconds - sleep_interval_sec

    try:
        step = 0
        while True:
            yield step

            if time.time() >= timeout_at:
                _log.warning(f' ! WARNING: got timeout while waiting until {waiting_until}')
                return False

            time.sleep(sleep_interval_sec)
            step += 1

    except GeneratorExit:
        _log.info(f' + OK')


def wait_until(
    waiting_until: str,
    collect: Callable[[], T],
    timeout_sec=60,
    check_interval_sec=1,
    before_check=lambda res: None,
    before_sleep=lambda res: None,
    check=lambda res: bool(res),
    on_timeout=lambda res: None,
    silent=False
) -> (bool, T):
    if not silent:
        _log.info(f'Waiting until {waiting_until} (max wait: {timeout_sec}s)')

    timeout_at = time.time() + timeout_sec - check_interval_sec

    while True:
        res = collect()

        before_check(res)

        if check(res):
            if not silent:
                _log.info(f' + OK')
                _log.info(f'')

            return True, res
        else:
            if time.time() >= timeout_at:
                if not silent:
                    _log.warning(f' ! WARNING: got timeout while waiting until {waiting_until}')
                    _log.info(f'')

                on_timeout(res)
                return False, res

        before_sleep(res)
        time.sleep(check_interval_sec)
