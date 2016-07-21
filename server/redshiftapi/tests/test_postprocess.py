import datetime

from django.test import TestCase

from stats import constants
from redshiftapi import postprocess


class PostprocessTest(TestCase):
    def test_get_representative_dates_days(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lte': datetime.date(2016, 2, 5),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.DAY, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 2),
            datetime.date(2016, 2, 3),
            datetime.date(2016, 2, 4),
            datetime.date(2016, 2, 5),
        ])

        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lt': datetime.date(2016, 2, 5),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.DAY, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 2),
            datetime.date(2016, 2, 3),
            datetime.date(2016, 2, 4),
        ])

    def test_get_representative_dates_weeks(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lte': datetime.date(2016, 2, 29),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.WEEK, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 1),
            datetime.date(2016, 2, 8),
            datetime.date(2016, 2, 15),
            datetime.date(2016, 2, 22),
            datetime.date(2016, 2, 29),
        ])

        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lt': datetime.date(2016, 2, 29),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.WEEK, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 1),
            datetime.date(2016, 2, 8),
            datetime.date(2016, 2, 15),
            datetime.date(2016, 2, 22),
        ])

    def test_get_representative_dates_months(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lte': datetime.date(2016, 4, 1),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.MONTH, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 1),
            datetime.date(2016, 3, 1),
            datetime.date(2016, 4, 1),
        ])

        constraints = {
            'date__gte': datetime.date(2016, 2, 2),
            'date__lt': datetime.date(2016, 4, 1),
        }

        dates = postprocess._get_representative_dates(constants.TimeDimension.MONTH, constraints)
        self.assertItemsEqual(dates, [
            datetime.date(2016, 2, 1),
            datetime.date(2016, 3, 1),
        ])

    def test_postprocess_time_dimension(self):
        rows = []
        postprocess.postprocess_time_dimension(
            constants.TimeDimension.DAY,
            rows,
            {'ad_group_id': None, 'clicks': None},
            ['ad_group_id', 'day'],
            {'date__gte': datetime.date(2016, 7, 1), 'date__lte': datetime.date(2016, 7, 5)},
            [{'ad_group_id': 1}]
        )

        self.assertItemsEqual(rows, [
            {'ad_group_id': 1, 'clicks': None, 'day': datetime.date(2016, 7, 1)},
            {'ad_group_id': 1, 'clicks': None, 'day': datetime.date(2016, 7, 2)},
            {'ad_group_id': 1, 'clicks': None, 'day': datetime.date(2016, 7, 3)},
            {'ad_group_id': 1, 'clicks': None, 'day': datetime.date(2016, 7, 4)},
            {'ad_group_id': 1, 'clicks': None, 'day': datetime.date(2016, 7, 5)},
        ])
