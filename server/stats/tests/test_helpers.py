import copy
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
            'account': models.Account.objects.get(pk=1),
            'campaign': models.Campaign.objects.get(pk=1),
            'ad_group': models.AdGroup.objects.get(pk=1),
            'content_ad': models.ContentAd.objects.get(pk=1),
            'publisher': 'gimme.beer.com',
            'dma': '502',
            'state': 'US-FL',
        }

        initial_constraints = copy.copy(constraints)

        stats_constraints = helpers.extract_stats_constraints(constraints)

        self.assertDictEqual(
            stats_constraints,
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source_id': test_helper.ListMatcher([1, 3, 4]),
                'account_id': 1,
                'campaign_id': 1,
                'ad_group_id': 1,
                'content_ad_id': 1,
                'publisher': 'gimme.beer.com',
                'dma': '502',
                'state': 'US-FL',
            },
        )

        self.assertEqual(constraints, initial_constraints, 'Input Constraints should not be modified')

    def test_extract_breakdown_id(self):
        self.assertDictEqual(
            helpers.extract_breakdown_id(
                ['ad_group', 'publisher', 'state', 'month'],
                "23||gimme.beer.com||FL"
            ),
            {
                'ad_group_id': 23,
                'publisher': 'gimme.beer.com',
                'state': 'FL',
            }
        )

        self.assertDictEqual(
            helpers.extract_breakdown_id(
                ['source', 'content_ad', 'country'],
                "11||20284"
            ),
            {
                'source_id': 11,
                'content_ad_id': 20284,
            }
        )

    def test_extract_stats_breakdown(self):
        self.assertListEqual(
            helpers.extract_stats_breakdown(['account', 'source', 'dma', 'day']),
            ['account_id', 'source_id', 'dma', 'day'],
        )

        self.assertListEqual(
            helpers.extract_stats_breakdown(['content_ad', 'publisher', 'device', 'week']),
            ['content_ad_id', 'publisher', 'device', 'week'],
        )

    def test_create_breakdown_id(self):
        self.assertEqual(
            helpers.create_breakdown_id(
                ['campaign', 'publisher', 'gender'],
                {'campaign_id': 13, 'publisher': 'gimme.beer.com', 'gender': 'M', 'clicks': 666}
            ),
            "13-gimme.beer.com-M"
        )

        self.assertEqual(
            helpers.create_breakdown_id(
                ['gender'],
                {'campaign_id': 13, 'publisher': 'gimme.beer.com', 'gender': 'M', 'clicks': 666}
            ),
            "M"
        )
