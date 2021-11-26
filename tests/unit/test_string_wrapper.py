from unittest import TestCase

from pyshrimp.utils.string_wrapper import StringWrapper


class TestStringWrapper(TestCase):

    def test_lines(self):
        sut = StringWrapper(
            '\n'
            'a\n'
            'b\n'
            'c\n'
            '\n'
            '\n'
        )
        self.assertEqual(
            [
                'a',
                'b',
                'c'
            ],
            sut.lines()
        )

    def test_match_lines(self):
        sut = StringWrapper(
            '\n'
            'x=1\n'
            'y=2\n'
            'a=1 x=3\n'
            '\n'
            '\n'
        )
        self.assertEqual(
            [
                '1',
                '3'
            ],
            sut.match_lines(r'(?:.+\s)?x=(\d+)')
        )

    def test_match_lines_with_named_group(self):
        sut = StringWrapper(
            '\n'
            'x=1\n'
            'y=2\n'
            'a=1 x=3\n'
            '\n'
            '\n'
        )
        self.assertEqual(
            [
                '1',
                '3'
            ],
            sut.match_lines(
                r'(?:.+\s)?x=(?P<x_val>\d+)',
                capture_group='x_val'
            )
        )

    def test_match_lines_multi_group(self):
        sut = StringWrapper(
            '\n'
            '\n'
            'x=1 y=2\n'
            'x=3 y=4\n'
            '\n'
            '\n'
        )
        self.assertEqual(
            [
                ['1', '2'],
                ['3', '4']
            ],
            sut.match_lines_multi_group(
                r'x=(?P<x_val>\d+)\s+y=(?P<y_val>\d+)',
                capture_groups=['x_val', 'y_val']
            )
        )

    def test_columns(self):
        sut = StringWrapper(
            '\n'
            'a b c\n'
            '  d e   f   \n'
            'g\t \th\t\ti\n'
            'j k\n'
            '\n'
            '\n'
        )
        self.assertEqual(
            [
                ['a', 'b', 'c'],
                ['d', 'e', 'f'],
                ['g', 'h', 'i'],
                ['j', 'k', None]
            ],
            sut.columns(0, 1, 2)
        )
