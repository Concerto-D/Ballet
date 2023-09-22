import unittest

from ballet.utils.io_utils import *

class TestIOUtils(unittest.TestCase):

    def test_makeDir(self):
        path = 'test_dir'
        makeDir(path)
        self.assertTrue(os.path.isdir(path))
        delDir(path)

    def test_delDir(self):
        path = 'test_dir'
        makeDir(path)
        self.assertTrue(os.path.isdir(path))
        delDir(path)
        self.assertFalse(os.path.exists(path))

    def test_makeDir_existing_dir(self):
        path = 'test_dir'
        os.makedirs(path)
        self.assertTrue(os.path.isdir(path))
        makeDir(path)
        self.assertTrue(os.path.isdir(path))
        delDir(path)

    def test_delDir_nonexistent_dir(self):
        path = 'test_dir'
        delDir(path)
        self.assertFalse(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
