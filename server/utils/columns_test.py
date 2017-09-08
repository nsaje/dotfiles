from django.test import TestCase

import dash.models
from utils import columns


class ColumnNamesTest(TestCase):
    fixtures = ['test_augmenter.yaml']

    def test_get_pixel_field_names_mapping(self):
        self.maxDiff = None
        self.assertDictEqual(
            columns.get_pixel_field_names_mapping(dash.models.ConversionPixel.objects.all()),
            {
                'Test 1 day': 'pixel_1_24',
                'CPA (Test 1 day)': 'avg_cost_per_pixel_1_24',
                'ROAS (Test 1 day)': 'roas_pixel_1_24',
                'Test 7 days': 'pixel_1_168',
                'CPA (Test 7 days)': 'avg_cost_per_pixel_1_168',
                'ROAS (Test 7 days)': 'roas_pixel_1_168',
                'Test 30 days': 'pixel_1_720',
                'CPA (Test 30 days)': 'avg_cost_per_pixel_1_720',
                'ROAS (Test 30 days)': 'roas_pixel_1_720',
                'Test 90 days': 'pixel_1_2160',
                'CPA (Test 90 days)': 'avg_cost_per_pixel_1_2160',
                'ROAS (Test 90 days)': 'roas_pixel_1_2160',
            }
        )

    def test_get_conversion_goals_field_names_mapping(self):
        self.assertDictEqual(
            columns.get_conversion_goals_field_names_mapping(dash.models.ConversionGoal.objects.all()),
            {
                'test conversion goal 2': 'conversion_goal_2',
                'CPA (test conversion goal 2)': 'avg_cost_per_conversion_goal_2',
                'test conversion goal 3': 'conversion_goal_3',
                'CPA (test conversion goal 3)': 'avg_cost_per_conversion_goal_3',
                'test conversion goal 4': 'conversion_goal_4',
                'CPA (test conversion goal 4)': 'avg_cost_per_conversion_goal_4',
                'test conversion goal 5': 'conversion_goal_5',
                'CPA (test conversion goal 5)': 'avg_cost_per_conversion_goal_5',
            }
        )

    def test_from_human_readable(self):
        self.assertEqual(columns.FieldNames.from_column_name('Unique Users'), 'unique_users')
        self.assertEqual(columns.FieldNames.from_column_name('Publisher'), 'publisher')

        with self.assertRaises(Exception):
            columns.FieldNames.from_column_name('')
