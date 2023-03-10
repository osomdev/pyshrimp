from unittest import TestCase

from pyshrimp.utils.collections import first_not_null


class TestCollectionsUtils(TestCase):

    def test_first_not_null_should_return_expected_value(self):
        self.assertEqual(42, first_not_null(42))
        self.assertEqual(42, first_not_null(42, None))
        self.assertEqual(42, first_not_null(None, 42))
        self.assertEqual(42, first_not_null(None, None, 42, 3))
        self.assertEqual(42, first_not_null(None, 42, 3, None))
        self.assertEqual(42, first_not_null(42, 3, None))
        self.assertEqual(3, first_not_null(None, 3, 42, None))

        # mix types
        self.assertEqual('a', first_not_null(None, 'a', 42, None))
        self.assertEqual(42, first_not_null(None, 42, 'a', None))

        # defaults
        self.assertEqual(42, first_not_null(None, default=42))
        self.assertEqual(42, first_not_null(None, None, default=42))
        self.assertEqual(42, first_not_null(default=42))