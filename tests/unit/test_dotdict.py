import re
from unittest import TestCase

from pyshrimp import as_dot_dict


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
