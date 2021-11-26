class IllegalStateException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class IllegalArgumentException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AsyncFunctionInvocationException(BaseException):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
