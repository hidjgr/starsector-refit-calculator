import unittest

from ui import Application


class TestUI(unittest.TestCase):

    def test_method_1(self):
        self.assertEqual('foo'.upper(), 'FOO')


if __name__ == '__main__':
    unittest.main()
