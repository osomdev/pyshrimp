import re
from functools import partial
from typing import Protocol, List


class Splitter(Protocol):
    def __call__(self, text: str, maxsplit: int = 0) -> List[str]:
        raise NotImplementedError()


def regex_splitter(text: str, split_pattern=r'\s+', strip_before_split=True, maxsplit=0):
    return re.split(
        split_pattern,
        text.strip() if strip_before_split else text,
        maxsplit=maxsplit
    )


def create_regex_splitter(split_pattern=r'\s+', strip_before_split=True) -> Splitter:
    # noinspection PyTypeChecker
    return partial(
        regex_splitter,
        split_pattern=split_pattern,
        strip_before_split=strip_before_split
    )


default_splitter = create_regex_splitter(
    split_pattern=r'\s+',
    strip_before_split=True
)
