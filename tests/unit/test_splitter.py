from unittest import TestCase

from pyshrimp import regex_splitter, create_regex_splitter
from pyshrimp.utils.splitter import default_splitter

data1 = '    a,b  c\t\t\td   e f         g          '


class TestSplitter(TestCase):

    def test_default_splitter_should_split(self):
        self.assertEqual(
            ['a,b', 'c', 'd', 'e', 'f', 'g'],
            default_splitter(data1)
        )
        self.assertEqual(
            ['a', 'b', 'c', 'd'],
            default_splitter('a b c d')
        )

    def test_default_splitter_should_respect_max_split(self):
        self.assertEqual(
            ['a', 'b', 'c d'],
            default_splitter('a b c d', maxsplit=2)
        )

    def test_regex_splitter_should_split(self):
        self.assertEqual(
            ['a,b', 'c', 'd', 'e', 'f', 'g'],
            regex_splitter(data1)
        )
        self.assertEqual(
            ['a', 'b', 'c', 'd'],
            regex_splitter('a b c d')
        )

    def test_regex_splitter_should_not_strip_when_asked(self):
        self.assertEqual(
            ['', 'a', 'b', ''],
            regex_splitter('  a b  ', strip_before_split=False)
        )

    def test_regex_splitter_should_respect_max_split(self):
        self.assertEqual(
            ['a', 'b', 'c d'],
            regex_splitter('a b c d', maxsplit=2)
        )

    def test_regex_splitter_should_use_provided_pattern(self):
        self.assertEqual(
            ['a b', 'c d', 'e'],
            regex_splitter('a b,c d,e', split_pattern=',')
        )

    def test_create_regex_splitter_should_create_splitter(self):
        splitter = create_regex_splitter(split_pattern=',', strip_before_split=False)
        self.assertEqual(
            ['  ', '', 'a b', 'c d', 'e'],
            splitter('  ,,a b,c d,e')
        )
