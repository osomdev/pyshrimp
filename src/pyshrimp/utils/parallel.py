from multiprocessing.pool import AsyncResult, ThreadPool

__thread_pools = {}


def __get_thread_pool(name) -> ThreadPool:
    if name not in __thread_pools:
        __thread_pools[name] = ThreadPool(10)

    return __thread_pools[name]


def in_background(fn) -> AsyncResult:
    return __get_thread_pool('default').apply_async(fn)
