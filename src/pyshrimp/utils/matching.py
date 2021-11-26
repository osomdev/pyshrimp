import re


def re_match_all(elements, pattern, capture_group=1):
    matches = [
        re.match(pattern, el) for el in elements
    ]

    return [
        m.group(capture_group) for m in matches if m
    ]
