import unittest

from ballet.utils.dict_utils import *

class TestDictUtils(unittest.TestCase):

    def test_sum_dicts(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'b': 3, 'c': 4}

        result = sum_dicts(dict1, dict2)
        expected = {'a': 1, 'b': 3, 'c': 4}

        self.assertEqual(result, expected)

    def test_sum_dicts_empty_dict(self):
        dict1 = {}
        dict2 = {'a': 1, 'b': 2}

        result = sum_dicts(dict1, dict2)
        expected = {'a': 1, 'b': 2}

        self.assertEqual(result, expected)

    def test_sum_dicts_no_common_keys(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'c': 3, 'd': 4}

        result = sum_dicts(dict1, dict2)
        expected = {'a': 1, 'b': 2, 'c': 3, 'd': 4}

        self.assertEqual(result, expected)

    def test_sum_dicts_empty_dicts(self):
        dict1 = {}
        dict2 = {}

        result = sum_dicts(dict1, dict2)
        expected = {}

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
