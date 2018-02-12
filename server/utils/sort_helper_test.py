import collections
import unittest
from utils import sort_helper


class SortHelperTestCase(unittest.TestCase):
    def test_sort_results_single_item(self):
        result = {}
        self.assertIs(sort_helper.sort_results(result), result)

    def test_sort_results_clone_results(self):
        results = [{'name': 'one'}]
        self.assertIsNot(sort_helper.sort_results(results), results)

    def test_sort_results_single_field(self):
        results = [
            {'name': 'bbb'},
            {'name': 'ccc'},
            {'name': 'aaa'},
            {'name': None}
        ]

        sorted_results = sort_helper.sort_results(results, ['name'])
        self.assertEqual(
            [result['name'] for result in sorted_results],
            ['aaa', 'bbb', 'ccc', None]
        )

        sorted_results = sort_helper.sort_results(results, ['-name'])
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

        sorted_results = sort_helper.sort_results(results, ['group', 'name'])
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

        self.assertCountEqual(sort_helper.map_by_breakdown(rows, ['source'], lambda row: row['value']), {
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

        self.assertCountEqual(
            sort_helper.map_by_breakdown(rows, ['source', 'ad_group', 'day_index'], lambda row: row['value']), {
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


class DissectOrderTest(unittest.TestCase):
    def test_dissect(self):
        self.assertEqual(sort_helper.dissect_order('-clicks'), ('-', 'clicks'))
        self.assertEqual(sort_helper.dissect_order('clicks'), ('', 'clicks'))
        self.assertEqual(sort_helper.dissect_order('-field_name'), ('-', 'field_name'))


class GroupRowsByBreakdownTest(unittest.TestCase):
    def test_get_breakdown_key(self):

        self.assertEqual(
            sort_helper.get_breakdown_key({'account_id': 1, 'source_id': 2}, ['account_id']),
            (1,)
        )

        self.assertEqual(
            sort_helper.get_breakdown_key({'account_id': 1, 'source_id': 2}, ['account_id', 'source_id']),
            (1, 2)
        )

    def test_group_rows_by_breakdown_key_breakdown_0(self):
        # should preserve order
        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key([], [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 1, 'clicks': 2},
                {'account_id': 2, 'clicks': 3},
            ]),
            {
                tuple([]): [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ]
            })

    def test_group_rows_by_breakdown_key_breakdown_1(self):
        # should preserve order
        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key(
                ['account_id'],
                [
                    {'account_id': 2, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                    {'account_id': 5, 'clicks': 3},
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 5},
                    {'account_id': 1, 'clicks': 2},
                ]),
            collections.OrderedDict([
                ((2,), [
                    {'account_id': 2, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ]),

                ((5,), [
                    {'account_id': 5, 'clicks': 3},
                ]),

                ((1,), [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 5},
                    {'account_id': 1, 'clicks': 2},
                ])
            ]))

    def test_group_rows_by_breakdown_key_breakdown_2(self):
        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key(
                ['account_id', 'source_id'],
                [
                    {'account_id': 1, 'source_id': 1, 'clicks': 1},
                    {'account_id': 2, 'source_id': 1, 'clicks': 3},
                    {'account_id': 2, 'source_id': 1, 'clicks': 1},
                    {'account_id': 1, 'source_id': 2, 'clicks': 2},
                ]),
            collections.OrderedDict([
                ((1, 1), [
                    {'account_id': 1, 'source_id': 1, 'clicks': 1},
                ]),

                ((2, 1), [
                    {'account_id': 2, 'source_id': 1, 'clicks': 3},
                    {'account_id': 2, 'source_id': 1, 'clicks': 1},
                ]),

                ((1, 2), [
                    {'account_id': 1, 'source_id': 2, 'clicks': 2},
                ]),
            ]))

        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key(
                ['account_id', 'source_id'],
                [
                    {'source_id': 1, 'bla': 11, 'account_id': 1},
                    {'source_id': 2, 'bla': 22, 'account_id': 1},
                    {'source_id': 3, 'bla': 33, 'account_id': 1},
                ]),
            collections.OrderedDict([
                ((1, 1), [{'source_id': 1, 'bla': 11, 'account_id': 1}]),
                ((1, 2), [{'source_id': 2, 'bla': 22, 'account_id': 1}]),
                ((1, 3), [{'source_id': 3, 'bla': 33, 'account_id': 1}]),
            ])
        )

    def test_group_rows_by_breakdown_key_max_1(self):
        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key(
                ['account_id', 'source_id'],
                [
                    {'source_id': 1, 'bla': 11, 'account_id': 1},
                    {'source_id': 2, 'bla': 22, 'account_id': 1},
                    {'source_id': 3, 'bla': 33, 'account_id': 1},
                ],
                max_1=True
            ),
            collections.OrderedDict([
                ((1, 1), {'source_id': 1, 'bla': 11, 'account_id': 1}),
                ((1, 2), {'source_id': 2, 'bla': 22, 'account_id': 1}),
                ((1, 3), {'source_id': 3, 'bla': 33, 'account_id': 1}),
            ])
        )

        self.assertEqual(
            sort_helper.group_rows_by_breakdown_key(
                ['account_id'],
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 2, 'clicks': 3},
                ],
                max_1=True
            ),
            collections.OrderedDict([
                ((1,), {'account_id': 1, 'clicks': 1}),
                ((2,), {'account_id': 2, 'clicks': 3}),
            ])
        )

        with self.assertRaises(Exception):
            sort_helper.group_rows_by_breakdown_key(
                ['account_id'],
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                max_1=True
            )


class ApplyOffsetLimitTest(unittest.TestCase):

    def test_apply_offset_limit(self):
        self.assertEqual(
            sort_helper.apply_offset_limit(
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                1, 1
            ),
            [
                {'account_id': 1, 'clicks': 2},
            ]
        )

        self.assertEqual(
            sort_helper.apply_offset_limit(
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                0, 2
            ),
            [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 1, 'clicks': 2},
            ]
        )

        self.assertEqual(
            sort_helper.apply_offset_limit(
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                2, 2
            ),
            [
                {'account_id': 2, 'clicks': 3},
            ]
        )

    def test_apply_offset_limit_to_breakdown(self):
        self.assertCountEqual(
            sort_helper.apply_offset_limit_to_breakdown(
                ['account_id'],
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                0, 1
            ),
            [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 2, 'clicks': 3},
            ]
        )

        self.assertCountEqual(
            sort_helper.apply_offset_limit_to_breakdown(
                ['account_id'],
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 1, 'clicks': 2},
                    {'account_id': 2, 'clicks': 3},
                ],
                1, 1
            ),
            [
                {'account_id': 1, 'clicks': 2},
            ]
        )

        rows = sort_helper.apply_offset_limit_to_breakdown(
            ['account_id'],
            [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 1, 'clicks': 2},
                {'account_id': 2, 'clicks': 3},
            ],
            0, 2
        )

        # there are two possible results - depends where group key was placed
        self.assertIn(rows, [
            [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 1, 'clicks': 2},
                {'account_id': 2, 'clicks': 3},
            ],
            [
                {'account_id': 2, 'clicks': 3},
                {'account_id': 1, 'clicks': 1},
                {'account_id': 1, 'clicks': 2},
            ],
        ])
