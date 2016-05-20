import backtosql
import copy
import datetime

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

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 0, 5)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 2, 6),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.DAY, constraints, 10, 18)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 11),
            'date__lte': datetime.date(2016, 2, 19),
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
            'date__lte': datetime.date(2016, 2, 15),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.WEEK, constraints, 2, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 15),
            'date__lte': datetime.date(2016, 2, 22),
        })

    def test_dimension_month(self):
        base_constraints = {
            'date__gte': datetime.date(2016, 2, 5),
            'date__lte': datetime.date(2016, 2, 16),
        }

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 0, 2)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 2, 1),
            'date__lte': datetime.date(2016, 4, 1),
        })

        constraints = copy.copy(base_constraints)
        queries._prepare_time_constraints(constants.TimeDimension.MONTH, constraints, 2, 3)

        self.assertEquals(constraints, {
            'date__gte': datetime.date(2016, 4, 1),
            'date__lte': datetime.date(2016, 5, 1),
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