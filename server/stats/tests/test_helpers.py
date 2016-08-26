import copy
import datetime
from django.test import TestCase

from dash import models
from dash import constants
from utils import test_helper
from utils import exc

from stats import helpers


class HelpersTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def test_extract_stats_constraints(self):
        constraints = {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 3, 4]),
            'show_archived': True,
            'account': models.Account.objects.get(pk=1),
            'campaign': models.Campaign.objects.get(pk=1),
            'ad_group': models.AdGroup.objects.get(pk=1),
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
            },
        )

        self.assertEqual(constraints, initial_constraints, 'Input Constraints should not be modified')

    def test_extract_stats_constraints_allowed_objects(self):
        constraints = {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 3, 4]),
            'show_archived': True,
            'allowed_accounts': models.Account.objects.all(),
            'allowed_campaigns': models.Campaign.objects.all(),
        }
        stats_constraints = helpers.extract_stats_constraints(constraints)

        self.assertDictEqual(
            stats_constraints,
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source_id': test_helper.ListMatcher([1, 3, 4]),
                'account_id': test_helper.ListMatcher([1, 2, 3, 4]),
                'campaign_id': test_helper.ListMatcher([1, 2, 3, 4, 5, 6]),
            },
        )

        self.assertDictEqual(
            stats_constraints,
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source_id': test_helper.TypeMatcher(list),
                'account_id': test_helper.TypeMatcher(list),
                'campaign_id': test_helper.TypeMatcher(list),
            },
        )

    def test_decode_breakdown_id(self):
        self.assertDictEqual(
            helpers.decode_breakdown_id(
                ['ad_group_id', 'publisher', 'state', 'month'],
                "23||gimme.beer.com||FL"
            ),
            {
                'ad_group_id': 23,
                'publisher': 'gimme.beer.com',
                'state': 'FL',
            }
        )

        self.assertDictEqual(
            helpers.decode_breakdown_id(
                ['source_id', 'content_ad_id', 'country'],
                "11||20284"
            ),
            {
                'source_id': 11,
                'content_ad_id': 20284,
            }
        )

        self.assertDictEqual(
            helpers.decode_breakdown_id(
                ['source_id', 'content_ad_id', 'country'],
                "11||-None-"
            ),
            {
                'source_id': 11,
                'content_ad_id': None,
            }
        )

        self.assertDictEqual(
            helpers.decode_breakdown_id(
                ['source_id', 'country', 'content_ad_id'],
                "11||-None-"
            ),
            {
                'source_id': 11,
                'country': None,
            }
        )

    def test_encode_breakdown_id(self):
        self.assertEqual(
            helpers.encode_breakdown_id(
                ['campaign_id', 'publisher', 'gender'],
                {'campaign_id': 13, 'publisher': 'gimme.beer.com', 'gender': 'M', 'clicks': 666}
            ),
            "13||gimme.beer.com||M"
        )

        self.assertEqual(
            helpers.encode_breakdown_id(
                ['gender'],
                {'campaign_id': 13, 'publisher': 'gimme.beer.com', 'gender': 'M', 'clicks': 666}
            ),
            "M"
        )
        self.assertEqual(
            helpers.encode_breakdown_id(
                ['campaign_id', 'publisher', 'gender'],
                {'campaign_id': 13, 'publisher': None, 'gender': 'M', 'clicks': 666}
            ),
            "13||-None-||M"
        )

    def test_extract_order_field(self):
        self.assertEqual(
            helpers.extract_order_field('clicks', ['source_id', 'day']),
            'day'
        )

        self.assertEqual(
            helpers.extract_order_field('clicks', ['source_id', 'week']),
            'week'
        )

        self.assertEqual(
            helpers.extract_order_field('clicks', ['source_id', 'month']),
            'month'
        )

        self.assertEqual(
            helpers.extract_order_field('clicks', ['source_id', 'age']),
            'age'
        )

        self.assertEqual(
            helpers.extract_order_field('clicks', ['source_id', 'age_gender']),
            'age_gender'
        )

        self.assertEqual(
            helpers.extract_order_field('clicks', []),
            'clicks'
        )

        self.assertEqual(
            helpers.extract_order_field('-media_cost', []),
            '-media_cost'
        )

        self.assertEqual(
            helpers.extract_order_field('account_id', []),
            'account_name'
        )

    def test_get_supported_order(self):
        self.assertEqual('-media_cost', helpers.get_supported_order('-cost'))
        self.assertEqual('-clicks', helpers.get_supported_order('-account_name'))
        self.assertEqual('-clicks', helpers.get_supported_order('-campaign_name'))
        self.assertEqual('-clicks', helpers.get_supported_order('-ad_group_name'))
        self.assertEqual('-clicks', helpers.get_supported_order('-content_ad_title'))


class CheckConstraintsSupportedTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def test_check_constraints_are_supported(self):
        # should succeed, no exception
        helpers.check_constraints_are_supported({
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 2]),
            'filtered_agencies': models.Agency.objects.all(),
            'filtered_account_types': constants.AccountType.get_all(),
            'allowed_accounts': models.Account.objects.all(),
            'allowed_campaigns': models.Campaign.objects.all(),
            'account': models.Account.objects.get(pk=1),
            'campaign': models.Campaign.objects.get(pk=1),
            'ad_group': models.AdGroup.objects.get(pk=1),
            'show_archived': True,
        })

        with self.assertRaises(exc.UnknownFieldBreakdownError):
            helpers.check_constraints_are_supported({
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': [1, 2],  # should be source_id
                'show_archived': True,
            })
