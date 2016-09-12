import copy
import datetime
from django.test import TestCase

from zemauth.models import User

from dash import models
from dash.constants import Level, AccountType
from utils import test_helper
from utils import exc

from stats import helpers
from stats import constants


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

        stats_constraints = helpers.extract_stats_constraints(constraints, ['ad_group_id'])

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
        stats_constraints = helpers.extract_stats_constraints(constraints, ['account_id', 'campaign_id'])

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
        self.assertEqual(helpers.extract_order_field('clicks', 'day'), 'name')
        self.assertEqual(helpers.extract_order_field('clicks', 'week'), 'name')
        self.assertEqual(helpers.extract_order_field('clicks', 'month'), 'name')
        self.assertEqual(helpers.extract_order_field('clicks', 'age'), 'name')
        self.assertEqual(helpers.extract_order_field('clicks', 'age_gender'), 'name')

        self.assertEqual(helpers.extract_order_field('clicks', None), 'clicks')
        self.assertEqual(helpers.extract_order_field('-media_cost', None), '-media_cost')
        self.assertEqual(helpers.extract_order_field('clicks', 'ad_group_id'), 'clicks')

        self.assertEqual(helpers.extract_order_field('name', 'publisher'), 'name')
        self.assertEqual(helpers.extract_order_field('name', 'dma'), 'name')
        self.assertEqual(helpers.extract_order_field('name', 'gender'), 'name')
        self.assertEqual(helpers.extract_order_field('name', 'country'), 'name')
        self.assertEqual(helpers.extract_order_field('name', 'state'), 'name')

        self.assertEqual(helpers.extract_order_field('-status', 'publisher'), '-status')

        self.assertEqual(helpers.extract_order_field('-status', 'dma'), '-status')
        self.assertEqual(helpers.extract_order_field('-status', 'gender'), '-status')
        self.assertEqual(helpers.extract_order_field('-status', 'country'), '-status')
        self.assertEqual(helpers.extract_order_field('-status', 'state'), '-status')

        self.assertEqual(helpers.extract_order_field('-state', 'ad_group_id'), '-status')
        self.assertEqual(helpers.extract_order_field('-state', 'state'), '-status')

    def test_extract_performance_order_field(self):
        self.assertEqual(helpers.extract_order_field('-performance', 'ad_group_id'), '-clicks')
        self.assertEqual(helpers.extract_order_field('performance', 'ad_group_id'), 'clicks')

        primary_goal = models.CampaignGoal(campaign_id=1)
        primary_goal.save()

        self.assertEqual(helpers.extract_order_field('-performance', 'ad_group_id', primary_goal),
                         '-performance_campaign_goal_' + str(primary_goal.id))
        self.assertEqual(helpers.extract_order_field('performance', 'ad_group_id', primary_goal),
                         'performance_campaign_goal_' + str(primary_goal.id))

    def test_extract_rs_order_field(self):
        self.assertEqual(helpers.extract_rs_order_field('name', 'day'), 'day')
        self.assertEqual(helpers.extract_rs_order_field('name', 'week'), 'week')
        self.assertEqual(helpers.extract_rs_order_field('name', 'month'), 'month')
        self.assertEqual(helpers.extract_rs_order_field('name', 'age'), 'age')
        self.assertEqual(helpers.extract_rs_order_field('name', 'age_gender'), 'age_gender')
        self.assertEqual(helpers.extract_rs_order_field('name', 'publisher'), 'publisher')
        self.assertEqual(helpers.extract_rs_order_field('name', 'dma'), 'dma')
        self.assertEqual(helpers.extract_rs_order_field('name', 'gender'), 'gender')
        self.assertEqual(helpers.extract_rs_order_field('name', 'country'), 'country')
        self.assertEqual(helpers.extract_rs_order_field('name', 'state'), 'state')

        self.assertEqual(helpers.extract_rs_order_field('-status', 'publisher'), '-status')

        self.assertEqual(helpers.extract_rs_order_field('-status', 'dma'), '-clicks')
        self.assertEqual(helpers.extract_rs_order_field('-status', 'gender'), '-clicks')
        self.assertEqual(helpers.extract_rs_order_field('-status', 'country'), '-clicks')
        self.assertEqual(helpers.extract_rs_order_field('-status', 'state'), '-clicks')

    def test_get_supported_order(self):
        self.assertEqual('-media_cost', helpers.get_supported_order('-cost', 'ad_group_id'))
        self.assertEqual('-clicks', helpers.get_supported_order('-pacing', 'ad_group_id'))
        self.assertEqual('clicks', helpers.get_supported_order('state', 'publisher'))
        self.assertEqual('media_cost', helpers.get_supported_order('media_cost', 'publisher'))
        self.assertEqual('-name', helpers.get_supported_order('-name', 'ad_group_id'))

    def test_should_query_dashapi_first(self):
        for dimension in ('account_id', 'campaign_id', 'ad_group_id', 'content_ad_id', 'source_id'):
            self.assertTrue(helpers.should_query_dashapi_first('name', dimension))
            self.assertTrue(helpers.should_query_dashapi_first('status', dimension))
            self.assertFalse(helpers.should_query_dashapi_first('clicks', dimension))

        self.assertFalse(helpers.should_query_dashapi_first('name', 'publisher'))
        self.assertTrue(helpers.should_query_dashapi_first('status', 'publisher'))

        for dimension in constants.DeliveryDimension._ALL + constants.TimeDimension._ALL:
            self.assertFalse(helpers.should_query_dashapi_first('name', dimension), dimension)
            self.assertFalse(helpers.should_query_dashapi_first('status', dimension), dimension)
            self.assertFalse(helpers.should_query_dashapi_first('clicks', dimension))


class PrepareConstraints(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def test_prepare_constraints(self):
        sources = models.Source.objects.all()
        user = User.objects.get(pk=1)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ALL_ACCOUNTS, user, ['account_id'], start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
            }
        )

        self.assertDictEqual(
            helpers.prepare_constraints(
                Level.ALL_ACCOUNTS, user, ['account_id', 'campaign_id'], start_date, end_date, sources
            ),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1])),
            }
        )

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ALL_ACCOUNTS, user, ['source_id'], start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
            }
        )

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ACCOUNTS, user, ['source_id', 'campaign_id'],
                                        start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1])),
            }
        )

        account = models.Account.objects.get(pk=1)

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ACCOUNTS, user, ['source_id', 'campaign_id'],
                                        start_date, end_date, sources, account=account),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': account,
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1])),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id=1)),
            }
        )

        campaign = models.Campaign.objects.get(pk=1)

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ACCOUNTS, user, ['campaign_id', 'ad_group_id'],
                                        start_date, end_date, sources, campaign=campaign),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id=1)),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()),
            }
        )

        self.assertDictEqual(
            helpers.prepare_constraints(Level.ACCOUNTS, user, ['campaign_id', 'content_ad_id'],
                                        start_date, end_date, sources, campaign=campaign),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id=1)),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()),
            }
        )

        self.assertDictEqual(
            helpers.prepare_constraints(Level.CAMPAIGNS, user, ['ad_group_id', 'content_ad_id'],
                                        start_date, end_date, sources, ad_group=models.AdGroup.objects.get(pk=1)),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group_id=1).exclude_archived()),
            }
        )


class CampaignGoalTest(TestCase):
    fixtures = ['test_augmenter.yaml']

    def test_get_goals(self):
        sources = models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        campaign = models.Campaign.objects.get(pk=1)
        account = models.Account.objects.get(pk=1)

        goals = helpers.get_goals({
            'date__gte': start_date,
            'date__lte': end_date,
            'show_archived': False,
            'filtered_sources': test_helper.QuerySetMatcher(sources),
            'account': account,
            'campaign': campaign,
            'ad_group': models.AdGroup.objects.get(pk=1),
        })
        self.assertEqual(goals.campaign_goals,
                         test_helper.QuerySetMatcher(models.CampaignGoal.objects.filter(pk__in=[1, 2])))
        self.assertEqual(goals.conversion_goals,
                         test_helper.QuerySetMatcher(models.ConversionGoal.objects.filter(pk__in=[1, 2, 3, 4, 5])))
        self.assertEqual(goals.campaign_goal_values,
                         test_helper.QuerySetMatcher(models.CampaignGoalValue.objects.filter(pk__in=[1, 2])))
        self.assertEqual(goals.pixels,
                         test_helper.QuerySetMatcher(models.ConversionPixel.objects.filter(pk=1)))
        self.assertEqual(goals.primary_goal,
                         models.CampaignGoal.objects.get(pk=2))

    def test_get_goals_no_constraints(self):
        sources = models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        goals = helpers.get_goals({
            'date__gte': start_date,
            'date__lte': end_date,
            'show_archived': False,
            'filtered_sources': test_helper.QuerySetMatcher(sources),
            'ad_group': models.AdGroup.objects.get(pk=1),
        })
        self.assertEqual(goals.campaign_goals, [])
        self.assertEqual(goals.conversion_goals, [])
        self.assertEqual(goals.campaign_goal_values, [])
        self.assertEqual(goals.pixels, [])
        self.assertEqual(goals.primary_goal, None)


class CheckConstraintsSupportedTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def test_check_constraints_are_supported(self):
        # should succeed, no exception
        helpers.check_constraints_are_supported({
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 2]),
            'filtered_agencies': models.Agency.objects.all(),
            'filtered_account_types': AccountType.get_all(),
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
