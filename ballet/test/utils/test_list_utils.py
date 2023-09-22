import unittest

from ballet.utils.list_utils import *

class TestListUtils(unittest.TestCase):

    def test_map_index(self):
        self.assertEqual(map_index(lambda x, i: x + i, [1, 2, 3]), [1, 3, 5])

    def test_flatmap(self):
        self.assertEqual(flatmap(lambda x: [x, x+1], [1, 2, 3]), [1, 2, 2, 3, 3, 4])

    def test_find(self):
        self.assertEqual(find(lambda x: x == 2, [1, 2, 3]), 2)
        self.assertIsNone(find(lambda x: x == 4, [1, 2, 3]))

    def test_exists(self):
        self.assertTrue(exists(lambda x: x == 2, [1, 2, 3]))
        self.assertFalse(exists(lambda x: x == 4, [1, 2, 3]))

    def test_findAll(self):
        self.assertEqual(findAll(lambda x: x % 2 == 0, [1, 2, 3, 4, 5]), [2, 4])

    def test_difference(self):
        self.assertEqual(difference([1, 2, 3], [3, 4, 5]), [4, 5, 1, 2])

    def test_add_if_no_exist(self):
        self.assertEqual(add_if_no_exist([1, 2, 3], 4), [1, 2, 3, 4])
        self.assertEqual(add_if_no_exist([1, 2, 3], 2), [1, 2, 3])

    def test_intersection(self):
        self.assertEqual(intersection([1, 2, 3], [3, 4, 5]), [3])

    def test_reverse(self):
        self.assertEqual(reverse([1, 2, 3]), [3, 2, 1])

    def test_count(self):
        self.assertEqual(count(lambda x: x % 2 == 0, [1, 2, 3, 4, 5]), 2)

    def test_split(self):
        self.assertEqual(split(lambda x: x % 2 == 0, [1, 2, 3, 4, 5]), ([2, 4], [1, 3, 5]))

    def test_sum_lists(self):
        self.assertEqual(sum_lists([1, 2], [3, 4]), [1, 2, 3, 4])

    def test_indexOf(self):
        self.assertEqual(indexOf(2, [1, 2, 3]), 1)
        self.assertEqual(indexOf(4, [1, 2, 3]), -1)

    def test_forall(self):
        self.assertTrue(forall(lambda x: x < 5, [1, 2, 3, 4]))
        self.assertFalse(forall(lambda x: x < 5, [1, 2, 3, 4, 5]))


if __name__ == '__main__':
    unittest.main()
