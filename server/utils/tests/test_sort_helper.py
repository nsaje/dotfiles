import unittest
from utils.sort_helper import sort_results, map_by_breakdown


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


class MapByBreakdownTestCase(unittest.TestCase):

    def test_map_single_level(self):
        rows = [
            {
                'source': 1,
                'value': 55
            },
            {
                'source': 2,
                'value': 44
            },
            {
                'source': 3,
                'value': 33
            },
            {
                'source': 4,
                'value': 22
            },
        ]

        self.assertItemsEqual(map_by_breakdown(rows, ['source'], lambda row: row['value']), {
            1: 55,
            2: 44,
            3: 33,
            4: 22
        })

    def test_map_multilevel(self):
        rows = [
            {
                'source': 1,
                'ad_group': 2,
                'day_index': 3,
                'value': 55
            },
            {
                'source': 2,
                'ad_group': 2,
                'day_index': 3,
                'value': 44
            },
            {
                'source': 1,
                'ad_group': 3,
                'day_index': 3,
                'value': 33
            },
            {
                'source': 1,
                'ad_group': 2,
                'day_index': 5,
                'value': 22
            },
        ]

        self.assertItemsEqual(map_by_breakdown(rows, ['source', 'ad_group', 'day_index'], lambda row: row['value']), {
            1: {
                2: {
                    3: 55,
                    5: 22
                },
                3: {
                    3: 33
                }
            },
            2: {
                2: {
                    3: 44
                }
            }
        })
