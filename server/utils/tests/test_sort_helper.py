import unittest
from utils.sort_helper import sort_results


class SortHelperTestCase(unittest.TestCase):
    def test_sort_results_single_item(self):
        result = {}
        self.assertIs(sort_results(result), result)

    def test_sort_results_clone_results(self):
        results = [{'name': 'one'}]
        self.assertIsNot(sort_results(results), results)

    def test_sort_results_single_field(self):
        results = [
            {'name': 'bbb'},
            {'name': 'ccc'},
            {'name': 'aaa'},
            {'name': None}
        ]

        sorted_results = sort_results(results, ['name'])
        self.assertEqual(
            [result['name'] for result in sorted_results],
            ['aaa', 'bbb', 'ccc', None]
        )

        sorted_results = sort_results(results, ['-name'])
        self.assertEqual(
            [result['name'] for result in sorted_results],
            ['ccc', 'bbb', 'aaa', None]
        )

    def test_sort_results_multiple_fields(self):
        results = [
            {'name': 'aaa', 'group': 1},
            {'name': 'ccc', 'group': 0},
            {'name': None, 'group': 1},
            {'name': 'bbb', 'group': 0}
        ]

        sorted_results = sort_results(results, ['group', 'name'])
        self.assertEqual(
            [(result['group'], result['name']) for result in sorted_results],
            [(0, 'bbb'), (0, 'ccc'), (1, 'aaa'), (1, None)]
        )
