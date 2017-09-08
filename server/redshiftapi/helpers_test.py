import datetime

from django.test import TestCase

from stats import constants
from utils import test_helper

from redshiftapi import helpers


class HelperTest(TestCase):
    def test_create_parents(self):
        self.assertEqual(
            helpers.create_parents([
                {'source_id': 3, 'status': 1, 'name': 'asd'},
                {'source_id': 4, 'status': 1, 'name': 'qwe'},
            ], ['source_id']),
            [{'source_id': [3, 4]}]
        )

        self.assertItemsEqual(
            helpers.create_parents([
                {'source_id': 3, 'account_id': 1, 'status': 1, 'name': 'asd'},
                {'source_id': 4, 'account_id': 2, 'status': 1, 'name': 'qwe'},
                {'source_id': 2, 'account_id': 2, 'status': 1, 'name': 'qwere'},
            ], ['account_id', 'source_id']),
            [{'account_id': 1, 'source_id': [3]}, {'account_id': 2, 'source_id': test_helper.ListMatcher([2, 4])}]
        )

    def test_inflate_parent_constraints(self):
        self.assertEqual(
            helpers.inflate_parent_constraints([{'publisher_id': 'sad__2'}]),
            [{'publisher': 'sad', 'source_id': 2}]
        )

        self.assertEqual(
            helpers.inflate_parent_constraints([{'source_id': 1}]),
            [{'source_id': 1}]
        )

    def test_optimize_parent_constraints(self):
        self.assertItemsEqual(
            helpers.optimize_parent_constraints([{'source_id': [3]}, {'source_id': [2, 4]}]),
            [{'source_id': test_helper.ListMatcher([2, 3, 4])}]
        )

        self.assertItemsEqual(
            helpers.optimize_parent_constraints(
                [{'source_id': 1, 'publisher': 'qwe'}, {'source_id': 1, 'publisher': 'sad'}]),
            [{'source_id': 1, 'publisher': ['qwe', 'sad']}]
        )

    def test_get_all_dimensions(self):
        self.assertItemsEqual(
            helpers.get_all_dimensions(
                ['account_id', 'publisher_id'],
                {
                    'date': datetime.date(2016, 7, 7),
                    'content_ad_id': 1,
                },
                [{'source_id': 3}]
            ),
            ['account_id', 'publisher_id', 'content_ad_id', 'source_id']
        )

        self.assertItemsEqual(
            helpers.get_all_dimensions(
                ['account_id'],
                {
                    'date': datetime.date(2016, 7, 7),
                    'content_ad_id': 1,
                },
                [{'source_id': 3}],
            ),
            ['account_id', 'content_ad_id', 'source_id']
        )

    def test_select_relevant_stats_rows(self):
        self.assertItemsEqual(
            helpers.select_relevant_stats_rows(
                ['account_id'], [{'account_id': 1}, {'account_id': 2}, {'account_id': 4}],
                [
                    {'account_id': 1, 'clicks': 1},
                    {'account_id': 2, 'clicks': 2},
                    {'account_id': 3, 'clicks': 3},
                ]),
            [
                {'account_id': 1, 'clicks': 1},
                {'account_id': 2, 'clicks': 2},
            ]
        )


class PrepareTimeConstraintsTest(TestCase):

    def test_dimension_day(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.DAY, constraints, 0, 5),
            {
                'date__gte': datetime.date(2016, 2, 1),
                'date__lte': datetime.date(2016, 2, 5),
            }
        )

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.DAY, constraints, 10, 3),
            {
                'date__gte': datetime.date(2016, 2, 11),
                'date__lte': datetime.date(2016, 2, 13),
            }
        )

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.DAY, constraints, 10, 10),
            {
                'date__gte': datetime.date(2016, 2, 11),
                'date__lte': datetime.date(2016, 2, 16),  # should use the end date
            }
        )

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.DAY, constraints, 20, 10),
            {
                # offset is above date range - constraints should not select any row
                'date__gte': datetime.date(2016, 2, 21),
                'date__lte': datetime.date(2016, 2, 16),
            }
        )

    def test_dimension_week(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.WEEK, constraints, 0, 2),
            {
                'date__gte': datetime.date(2016, 2, 1),
                'date__lte': datetime.date(2016, 2, 14),
            })

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.WEEK, constraints, 1, 1),
            {
                'date__gte': datetime.date(2016, 2, 8),
                'date__lte': datetime.date(2016, 2, 14),
            }
        )

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.WEEK, constraints, 1, 2),
            {
                'date__gte': datetime.date(2016, 2, 8),
                'date__lte': datetime.date(2016, 2, 16),  # should use end date
            }
        )

    def test_dimension_month(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lte': datetime.date(2016, 4, 16),
        }

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.MONTH, constraints, 0, 2),
            {
                'date__gte': datetime.date(2016, 2, 5),
                'date__lte': datetime.date(2016, 3, 31),
            }
        )

        self.assertEquals(
            helpers.get_time_dimension_constraints(constants.TimeDimension.MONTH, constraints, 2, 3),
            {
                'date__gte': datetime.date(2016, 4, 1),
                'date__lte': datetime.date(2016, 4, 16),
            }
        )
