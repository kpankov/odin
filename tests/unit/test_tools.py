import unittest

from flows import get_tools


class TestTools(unittest.TestCase):
    def test_sanity_0(self):
        tools = get_tools()
        self.assertIsNotNone(tools)

    def test_sanity_1(self):
        tools = get_tools()
        self.assertIs(len(tools.groups), 4)

    def test_sanity_2(self):
        tools = get_tools()
        self.assertEqual(tools.groups[0], "common")


if __name__ == '__main__':
    unittest.main()
