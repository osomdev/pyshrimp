from dataclasses import dataclass
from typing import List

from pyshrimp.utils.dotdict import DotDict
from pyshrimp.utils.splitter import Splitter, default_splitter


@dataclass
class ParsedTable:
    header: List[str]
    rows: List[List[str]]

    def dict_rows(self, use_dot_dict=True):
        for row in self.rows:
            row_dict = dict(zip(self.header, row))
            yield DotDict(row_dict) if use_dot_dict else row_dict


def parse_table(
    lines: List[str],
    splitter: Splitter = default_splitter,
) -> ParsedTable:
    header = None
    maxsplit = 0
    rows = []
    for line in lines:
        if not header:
            # parse header
            header = splitter(line)
            maxsplit = len(header) - 1
        else:
            # parse row
            if maxsplit == 0:
                # special case: single column == whole line should be used (no split at all)
                rows.append([line])
            else:
                rows.append(splitter(line, maxsplit=maxsplit))

    return ParsedTable(header, rows)
