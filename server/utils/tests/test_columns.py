from django.test import TestCase

import dash.models
from utils import columns


class ColumnNamesTest(TestCase):
    fixtures = ['test_augmenter.yaml']

    def test_get_pixel_column_names_mapping(self):
        self.assertDictEqual(
            columns.get_pixel_column_names_mapping(dash.models.ConversionPixel.objects.all()),
            {
                'pixel_1_24': 'Test 1 day',
                'avg_cost_per_pixel_1_24': 'CPA (Test 1 day)',
                'pixel_1_168': 'Test 7 days',
                'avg_cost_per_pixel_1_168': 'CPA (Test 7 days)',
                'pixel_1_720': 'Test 30 days',
                'avg_cost_per_pixel_1_720': 'CPA (Test 30 days)',
                'pixel_1_2160': 'Test 90 days',
                'avg_cost_per_pixel_1_2160': 'CPA (Test 90 days)',
            }
        )

    def test_get_conversion_goals_column_names_mapping(self):
        self.assertDictEqual(
            columns.get_conversion_goals_column_names_mapping(dash.models.ConversionGoal.objects.all()),
            {
                'conversion_goal_2': 'test conversion goal 2',
                'conversion_goal_3': 'test conversion goal 3',
                'conversion_goal_4': 'test conversion goal 4',
                'conversion_goal_5': 'test conversion goal 5',
            }
        )

    def test_get_keys(self):
        self.assertListEqual(columns.Names.get_keys(['Unique Users', 'Publisher']), ['unique_users', 'publisher'])

        with self.assertRaises(Exception):
            columns.Names.get_keys([''])
