import unittest
from utils.list_helper import list_chunker


class SortHelperTestCase(unittest.TestCase):
    def test_chunk_list(self):
        sample_list = ['cat', 'dog', 'rabbit', 'duck', 'bird', 'cow', 'gnu', 'fish']
        chunked_list = list_chunker(sample_list, 3)
        self.assertEqual(list(chunked_list), [['cat', 'dog', 'rabbit'], ['duck', 'bird', 'cow'], ['gnu', 'fish']])
