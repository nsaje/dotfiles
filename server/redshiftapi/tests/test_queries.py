import backtosql
import copy
import datetime
import mock

from django.test import TestCase

from stats import constants
from utils import exc

from redshiftapi import queries
from redshiftapi import models


class PrepareTimeConstraintsTest(TestCase):

    def test_dimension_day(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        # fits into time span
        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 0, 5)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lt': datetime.date(2016, 2, 6),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 10, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 11),
            'date__lt': datetime.date(2016, 2, 14),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 10, 10)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 11),
            'date__lte': datetime.date(2016, 2, 16),  # should use the end date
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 20, 10)

        self.assertEquals(constraints, {
            # offset is above date range - constraints should not select any row
            'date__gte': datetime.date(2016, 2, 21),
            'date__lte': datetime.date(2016, 2, 16),
        })

    def test_dimension_week(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 0, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lt': datetime.date(2016, 2, 15),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 1, 1)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 8),
            'date__lt': datetime.date(2016, 2, 15),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 1, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 8),
            'date__lte': datetime.date(2016, 2, 16),  # should use end date
        })

    def test_dimension_month(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lte': datetime.date(2016, 4, 16),
        }

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 0, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lt': datetime.date(2016, 4, 1),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 2, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 4, 16),
        })


class TestPrepareQuery(TestCase):

    def test_lvl1_required_breakdown_constraints(self):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        context = {
            'constraints': backtosql.Q(models.RSContentAdStats, **constraints)
        }

        with self.assertRaises(exc.MissingBreakdownConstraintsError):
            queries.prepare_lvl1_top_rows(context)

    def test_lvl2required_breakdown_constraints(self):
        constraints = {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
        }

        context = {
            'constraints': backtosql.Q(models.RSContentAdStats, **constraints)
        }

        with self.assertRaises(exc.MissingBreakdownConstraintsError):
            queries.prepare_lvl2_top_rows(context)

    def test_top_time_rows_prepares_time(self):
        constraints = {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 16),
        }

        _, params = queries.prepare_time_top_rows(
            models.RSContentAdStats,
            constants.TimeDimension.DAY, {}, constraints, 1, 2)

        self.assertItemsEqual(params, [datetime.date(2016, 2, 2), datetime.date(2016, 2, 4)])
