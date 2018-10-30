import unittest

from utils import list_helper


class SortHelperTestCase(unittest.TestCase):
    def test_chunk_list(self):
        sample_list = ["cat", "dog", "rabbit", "duck", "bird", "cow", "gnu", "fish"]
        chunked_list = list_helper.list_chunker(sample_list, 3)
        self.assertEqual(list(chunked_list), [["cat", "dog", "rabbit"], ["duck", "bird", "cow"], ["gnu", "fish"]])

    def test_flatten(self):
        self.assertEqual(list(range(5)), list(list_helper.flatten([[0, 1, 2], [], [3, 4]])))
