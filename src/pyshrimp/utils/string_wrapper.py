import re
from typing import Union, List


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

    def columns(self, *column_index, split_pattern=r'\s+', strip_before_split=True, include_empty_lines=False):
        def _process_line(line):
            if strip_before_split:
                line = line.strip()

            split_line = re.split(split_pattern, line)
            return [(split_line[i:i + 1] or [None])[0] for i in column_index]

        return [
            _process_line(line) for line in self.lines(include_empty_lines)
        ]
