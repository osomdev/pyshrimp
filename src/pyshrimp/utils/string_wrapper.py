import re
from typing import Union, List

from pyshrimp.utils.splitter import Splitter, default_splitter
from pyshrimp.utils.table_parser import parse_table


class StringWrapper(str):

    def lines(self, include_empty=False):
        all_lines = self.splitlines()
        if include_empty:
            return all_lines
        else:
            return [line for line in all_lines if line]

    def match_lines(self, pattern, capture_group: Union[str, int] = 1, include_empty_lines=False) -> List[Union[str, None]]:
        match_list = (
            re.match(pattern, el) for el in self.lines(include_empty_lines)
        )
        return [
            m.group(capture_group) for m in match_list if m
        ]

    def match_lines_multi_group(self, pattern, capture_groups: List[Union[str, int]], include_empty_lines=False) -> List[List[Union[str, None]]]:
        match_list = (
            re.match(pattern, el) for el in self.lines(include_empty_lines)
        )
        return [
            [
                m.group(g) for g in capture_groups
            ] for m in match_list if m
        ]

    def columns(self, *column_index, splitter: Splitter = default_splitter, maxsplit=0):
        def _process_line(line):
            split_line = splitter(line, maxsplit=maxsplit)
            if not column_index:
                return split_line
            else:
                return [(split_line[i:i + 1] or [None])[0] for i in column_index]

        return [
            _process_line(line) for line in self.lines(include_empty=False)
        ]

    def parse_table(self, splitter: Splitter = default_splitter):
        return parse_table(self.lines(include_empty=False), splitter)
