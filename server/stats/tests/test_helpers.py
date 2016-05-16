import datetime
from django.test import TestCase

from dash import models
from utils import test_helper

from stats import helpers


class HelpersTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def test_extract_stats_constraints(self):
        constraints = {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'source': models.Source.objects.filter(pk__in=[1, 3, 4]),
            'show_archived': True,
        }

        stats_constraints = helpers.extract_stats_constraints(constraints)

        self.assertDictEqual(
            stats_constraints,
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
            }
        )

        self.assertNotEqual(constraints, stats_constraints, 'Constraints should be copied')
