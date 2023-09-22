import unittest

from ballet.utils.iterable_utils import *

class TestIterableUtils(unittest.TestCase):

    def test_find_in_iterable(self):
        even_check = lambda x: x % 2 == 0
        lst = [1, 3, 5, 2, 4, 6]

        result = find_in_iterable(even_check, lst)
        expected = 2

        self.assertEqual(result, expected)

    def test_find_in_iterable_not_found(self):
        negative_check = lambda x: x < 0
        lst = [1, 3, 5, 2, 4, 6]

        result = find_in_iterable(negative_check, lst)
        expected = None

        self.assertEqual(result, expected)

    def test_find_in_iterable_empty_iterable(self):
        always_true = lambda x: True
        empty_list = []

        result = find_in_iterable(always_true, empty_list)
        expected = None

        self.assertEqual(result, expected)

    def test_find_in_iterable_set(self):
        positive_check = lambda x: x > 0
        s = {1, 2, 3, 4, 5}

        result = find_in_iterable(positive_check, s)
        expected = 1

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
