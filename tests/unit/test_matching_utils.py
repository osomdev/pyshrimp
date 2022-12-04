from unittest import TestCase

from pyshrimp import re_match_all


class TestMatchingUtils(TestCase):

    def test_should_return_matching_group(self):
        self.assertEqual(
            [
                '1',
                '2',
                '3'
            ],
            re_match_all(
                [
                    'boo 1',
                    'baa 2',
                    'no match',
                    'bee 3'
                ],
                r'.* (\d+)',
                capture_group=1
            )
        )

    def test_should_return_empty_list_when_no_match_found(self):
        self.assertEqual(
            [],
            re_match_all(
                [
                    'no match'
                ],
                r'.* (\d+)',
                capture_group=1
            )
        )
