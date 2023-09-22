import unittest

from ballet.utils.set_utils import *

class TestSetUtils(unittest.TestCase):

    def test_find_in_set(self):
        even_check = lambda x: x % 2 == 0
        s = {1, 3, 5, 2, 4, 6}

        result = find_in_set(even_check, s)
        expected = 2

        self.assertEqual(result, expected)

    def test_find_in_set_not_found(self):
        negative_check = lambda x: x < 0
        s = {1, 3, 5, 2, 4, 6}

        result = find_in_set(negative_check, s)
        expected = None

        self.assertEqual(result, expected)

    def test_findAll_in_set(self):
        even_check = lambda x: x % 2 == 0
        s = {1, 3, 5, 2, 4, 6}

        result = findAll_in_set(even_check, s)
        expected = [2, 4, 6]

        self.assertEqual(result, expected)

    def test_findAll_in_set_not_found(self):
        negative_check = lambda x: x < 0
        s = {1, 3, 5, 2, 4, 6}

        result = findAll_in_set(negative_check, s)
        expected = []

        self.assertEqual(result, expected)

    def test_remove_in_set(self):
        even_check = lambda x: x % 2 == 0
        s = {1, 3, 5, 2, 4, 6}

        result = remove_in_set(even_check, s)
        expected = {1, 3, 5}

        self.assertEqual(result, expected)

    def test_remove_in_set_not_found(self):
        negative_check = lambda x: x < 0
        s = {1, 3, 5, 2, 4, 6}

        result = remove_in_set(negative_check, s)
        expected = {1, 3, 5, 2, 4, 6}

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
