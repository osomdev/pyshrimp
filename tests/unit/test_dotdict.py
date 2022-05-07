import re
from unittest import TestCase

from pyshrimp import as_dot_dict
from pyshrimp.utils.dotdict import unwrap_dot_dict


class Test(TestCase):

    def test_dot_dict_should_read_data_from_dict(self):
        sut = as_dot_dict(
            {
                'a': 42
            }
        )
        self.assertEqual(42, sut.a)

    def test_dot_dict_should_read_nested_data_from_dict(self):
        sut = as_dot_dict(
            {
                'a': {
                    'b': {
                        'c': {
                            'd': 42
                        }
                    }
                }
            }
        )
        self.assertEqual(42, sut.a.b.c.d)

    def test_dot_dict_should_support_in_condition(self):
        sut = as_dot_dict(
            {
                'a': 42
            }
        )
        self.assertIn('a', sut)


    def test_dot_dict_should_read_data_from_list_value(self):
        sut = as_dot_dict(
            {
                'a': [42]
            }
        )
        self.assertEqual(42, sut.a[0])

    def test_dot_dict_should_read_data_from_dict_contained_in_list(self):
        sut = as_dot_dict(
            {
                'a': [{
                    'b': 42
                }]
            }
        )
        self.assertEqual(42, sut.a[0].b)

    def test_dot_dict_should_read_data_from_dict_contained_in_nested_list(self):
        sut = as_dot_dict(
            {
                'a': [
                    [
                        [
                            {
                                'b': 42
                            }
                        ]
                    ]
                ]
            }
        )
        self.assertEqual(42, sut.a[0][0][0].b)

    def test_dot_dict_should_produce_useful_key_error_message(self):
        sut = as_dot_dict(
            {
                'a': [{
                    'b': {
                        'c': 1
                    }
                }]
            },
            'sut'
        )

        # direct path
        with self.assertRaisesRegex(KeyError, re.escape("'sut.a[0].b.nosuchelement'")):
            self.assertEqual(None, sut.a[0].b.nosuchelement)

        # values stored in variable
        a = sut.a
        b = a[0].b

        with self.assertRaisesRegex(KeyError, re.escape("'sut.a[0].b.nosuchelement'")):
            self.assertEqual(None, b.nosuchelement)

        # should also work with iteration
        for a in sut.a:
            with self.assertRaisesRegex(KeyError, re.escape("'sut.a[0].b.nosuchelement'")):
                self.assertEqual(None, a.b.nosuchelement)

    def test_dot_dict_should_produce_same_string_representation_as_base_types(self):
        data = {
            'a': 1,
            'b': ['a', 1, {
                'x': 'y'
            }]
        }
        sut = as_dot_dict(data)
        self.assertEqual(str(data), str(sut))
        self.assertEqual(str(data['a']), str(sut.a))
        self.assertEqual(str(data['a']), str(sut.a))
        self.assertEqual(str(data['b']), str(sut.b))
        self.assertEqual(str(data['b'][2]), str(sut.b[2]))

    def test_dot_dict_should_produce_same_repr_representation_as_base_types(self):
        data = {
            'a': 1,
            'b': ['a', 1, {
                'x': 'y'
            }]
        }
        sut = as_dot_dict(data)
        self.assertEqual(repr(data), repr(sut))
        self.assertEqual(repr(data['a']), repr(sut.a))
        self.assertEqual(repr(data['a']), repr(sut.a))
        self.assertEqual(repr(data['b']), repr(sut.b))
        self.assertEqual(repr(data['b'][2]), repr(sut.b[2]))

    def test_dot_dict_should_be_subscriptable(self):
        sut = as_dot_dict({'a': 1})
        self.assertEqual(1, sut.a)
        self.assertEqual(1, sut['a'])

    def test_dot_dict_should_support_writing(self):
        sut = as_dot_dict({'a': 1})
        self.assertEqual(1, sut.a)
        sut.a = 2
        self.assertEqual(2, sut.a)
        sut['a'] = 3
        self.assertEqual(3, sut.a)

    def test_dot_dict_should_handle_equal_check_between_dot_dicts(self):
        d1 = as_dot_dict({'a': 42})
        d2 = as_dot_dict({'a': 42})
        self.assertTrue(d1 == d2)
        self.assertTrue(d2 == d1)

    def test_dot_dict_should_ignore_path_when_comparing_two_dot_dicts(self):
        d = as_dot_dict(
            {
                'a': {'x': 42},
                'b': {'x': 42}
            }
        )
        d1 = d.a
        d2 = d.b
        self.assertTrue(d1 == d2)
        self.assertTrue(d2 == d1)

    def test_dot_dict_should_spot_difference_between_values_of_dot_dicts(self):
        d1 = as_dot_dict({'a': 1})
        d2 = as_dot_dict({'a': 7})
        self.assertFalse(d1 == d2)
        self.assertFalse(d2 == d1)

    def test_dot_dict_should_handle_equal_check_between_dot_dict_and_raw_dict(self):
        d1 = as_dot_dict({'a': 42})
        d2 = {'a': 42}
        self.assertTrue(d1 == d2)
        self.assertTrue(d2 == d1)

    def test_dot_dict_should_spot_difference_between_values_of_dot_dict_and_raw_dict(self):
        d1 = as_dot_dict({'a': 1})
        d2 = {'a': 7}
        self.assertFalse(d1 == d2)
        self.assertFalse(d2 == d1)

    def test_unwrap_should_return_raw_data(self):
        d = {'a': 1}
        sut = as_dot_dict(d)
        d_unwrapped = unwrap_dot_dict(sut)
        self.assertEqual(d, d_unwrapped)
        self.assertIsInstance(d_unwrapped, dict)
        self.assertIs(d, d_unwrapped)

    def test_unwrap_should_return_raw_data_from_nested_objects(self):
        d = {
            'a': {
                'b': 3
            }
        }
        sut = as_dot_dict(d)
        d_unwrapped = unwrap_dot_dict(sut.a)
        self.assertEqual(d['a'], d_unwrapped)
        self.assertIsInstance(d['a'], dict)
        self.assertIs(d['a'], d_unwrapped)

    def test_unwrap_should_unwrap_lists(self):
        d = {
            'a': [
                [
                    {
                        'b': 3
                    }
                ]
            ]
        }
        dot_dict = as_dot_dict(d)
        wrapped_list = dot_dict.a
        unwrapped_list = unwrap_dot_dict(wrapped_list)
        original_list = d['a']
        self.assertEqual(original_list, unwrapped_list)
        # While list instances will be different then doc instance should be the same
        self.assertIs(original_list[0][0], unwrapped_list[0][0])
