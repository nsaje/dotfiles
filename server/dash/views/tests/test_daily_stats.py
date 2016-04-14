from mock import patch, MagicMock
import datetime
import json
from decimal import Decimal

from django.contrib.auth import models as authmodels
from django.test import TestCase
from django.core.urlresolvers import reverse

from utils.test_helper import QuerySetMatcher, ListMatcher
from zemauth.models import User
from dash import constants, models, conversions_helper


class BaseDailyStatsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=2)

        self.client.login(username=self.user.email, password=password)

        self.patcher = patch('dash.stats_helper.get_stats_with_conversions')
        self.mock_query = self.patcher.start()

        self.date = datetime.date(2015, 2, 22)

    def tearDown(self):
        self.patcher.stop()

    def _prepare_mock(self, group_key, group_id):
        mock_stats1 = [{
            'date': self.date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000
        }]
        mock_stats2 = [{
            'date': self.date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            group_key: group_id
        }]
        self.mock_query.side_effect = [mock_stats1, mock_stats2]

    def _get_params(self, selected_ids, sources=False):
        params = {
            'metrics': ['cpc', 'clicks'],
            'selected_ids': selected_ids,
            'totals': True,
            'start_date': self.date.isoformat(),
            'end_date': self.date.isoformat(),
        }

        if sources:
            params['sources'] = True

        return params

    def _assert_response(self, response, selected_id, selected_name):
        self.assertEqual(json.loads(response.content), {
            'data': {
                'chart_data': [{
                    'id': selected_id,
                    'name': selected_name,
                    'series_data': {
                        'clicks': [
                            [self.date.isoformat(), 1500]
                        ],
                        'cpc': [
                            [self.date.isoformat(), '0.0200']
                        ]
                    }
                }, {
                    'id': 'totals',
                    'name': 'Totals',
                    'series_data': {
                        'clicks': [
                            [self.date.isoformat(), 1000]
                        ],
                        'cpc': [
                            [self.date.isoformat(), '0.0100']
                        ]
                    }
                }]
            },
            'success': True
        })
        """
            'campaign_goals': {
                'reports': [],
                'conversions': ListMatcher([
                    {'id': 'Test Cg', 'name': 'test conversion goal 5'},
                    {'id': 'conversion_goal_4', 'name': 'test conversion goal 4'},
                    {'id': 'conversion_goal_3', 'name': 'test conversion goal 3'},
                    {'id': 'conversion_goal_2', 'name': 'test conversion goal 2'},
                    {'id': 'conversion_goal_1', 'name': 'test conversion goal'},
                ]),
            },

        """


class AccountsDailyStatsTest(BaseDailyStatsTest):
    def test_get_by_source(self):
        perm = authmodels.Permission.objects.get(codename='all_accounts_accounts_view')
        self.user.user_permissions.add(perm)
        source_id = 3

        self._prepare_mock('source', source_id)

        response = self.client.get(
            reverse('accounts_daily_stats'),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())
        accounts_matcher = QuerySetMatcher(models.Account.objects.all().filter_by_user(self.user))

        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': accounts_matcher, 'source': sources_matcher}
        )

        source_matcher = QuerySetMatcher(models.Source.objects.filter(pk=source_id))
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'source'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': accounts_matcher, 'source': source_matcher}
        )

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)


class AccountDailyStatsTest(BaseDailyStatsTest):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock('source', source_id)

        response = self.client.get(
            reverse('account_daily_stats', kwargs={'account_id': 1}),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': 1, 'source': matcher},
        )

        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'source'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': 1, 'source_id': [source_id]}
        )

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)

    def test_get_by_campaign(self):
        campaign_id = 1

        self._prepare_mock('campaign', campaign_id)

        response = self.client.get(
            reverse('account_daily_stats', kwargs={'account_id': 1}),
            self._get_params(selected_ids=[campaign_id]),
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': 1, 'source': matcher}
        )

        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'campaign'],
            order=['date'],
            conversion_goals=None,
            constraints={'account': 1, 'ad_group__campaign__id': [campaign_id]}
        )

        campaign = models.Campaign.objects.get(pk=campaign_id)
        self._assert_response(response, campaign_id, campaign.name)


class CampaignDailyStatsTest(BaseDailyStatsTest):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock('source', source_id)

        response = self.client.get(
            reverse('campaign_daily_stats', kwargs={'campaign_id': 1}),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        conversion_goals = models.ConversionGoal.objects.filter(campaign_id=1)
        conversion_goals_matcher = QuerySetMatcher(conversion_goals)
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'campaign': 1, 'source': matcher}
        )

        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'source'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'campaign': 1, 'source_id': [source_id]}
        )

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)

    def test_get_by_ad_group(self):
        ad_group_id = 1

        self._prepare_mock('ad_group', ad_group_id)

        response = self.client.get(
            reverse('campaign_daily_stats', kwargs={'campaign_id': 1}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        conversion_goals = models.AdGroup.objects.get(id=1).campaign.conversiongoal_set.all()
        conversion_goals_matcher = QuerySetMatcher(conversion_goals)
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'campaign': 1, 'source': matcher}
        )

        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'ad_group'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'campaign': 1, 'ad_group_id': [ad_group_id]}
        )

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self._assert_response(response, ad_group_id, ad_group.name)

    def test_get_campaign_goals(self):
        ad_group_id = 1

        self._prepare_mock('ad_group', ad_group_id)
        response = self.client.get(
            reverse('campaign_daily_stats', kwargs={'campaign_id': 1}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True
        )

        response_blob = json.loads(response.content)
        self.assertFalse('goal_fields' in response_blob['data'])
        self.assertFalse('campaign_goals' in response_blob['data'])

        perm = authmodels.Permission.objects.get(codename='campaign_goal_performance')
        self.user.user_permissions.add(perm)

        self._prepare_mock('ad_group', ad_group_id)
        response = self.client.get(
            reverse('campaign_daily_stats', kwargs={'campaign_id': 1}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True
        )

        response_blob = json.loads(response.content)
        self.assertTrue('goal_fields' in response_blob['data'])
        self.assertTrue('campaign_goals' in response_blob['data'])


class AdGroupDailyStatsTest(BaseDailyStatsTest):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock('source', source_id)

        response = self.client.get(
            reverse('ad_group_daily_stats', kwargs={'ad_group_id': 1}),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        conversion_goals = models.AdGroup.objects.get(id=1).campaign.conversiongoal_set.all()
        conversion_goals_matcher = QuerySetMatcher(conversion_goals)
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'ad_group': 1, 'source': matcher}
        )

        match_source = QuerySetMatcher(models.Source.objects.filter(pk=source_id))
        self.mock_query.assert_any_call(
            self.user,
            self.date,
            self.date,
            breakdown=['date', 'source'],
            order=['date'],
            conversion_goals=conversion_goals_matcher,
            constraints={'ad_group': 1, 'source': match_source}
        )

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)

    def test_get_campaign_goals(self):
        source_id = 3
        self._prepare_mock('source', source_id)
        response = self.client.get(
            reverse('ad_group_daily_stats', kwargs={'ad_group_id': 1}),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        response_blob = json.loads(response.content)
        self.assertFalse('goal_fields' in response_blob['data'])
        self.assertFalse('campaign_goals' in response_blob['data'])

        perm = authmodels.Permission.objects.get(codename='campaign_goal_performance')
        self.user.user_permissions.add(perm)

        self._prepare_mock('source', source_id)
        response = self.client.get(
            reverse('ad_group_daily_stats', kwargs={'ad_group_id': 1}),
            self._get_params(selected_ids=[source_id], sources=True),
            follow=True
        )

        response_blob = json.loads(response.content)
        self.assertTrue('goal_fields' in response_blob['data'])
        self.assertTrue('campaign_goals' in response_blob['data'])


@patch('dash.stats_helper.reports.api_contentads.query')
@patch('dash.stats_helper.reports.api_touchpointconversions.query')
class AdGroupAdsPlusDailyStatsTest(TestCase):
    fixtures = ['test_views']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_touchpoint_query, mock_query):
        mock_touchpoint_query.return_value = MagicMock()

        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [{
            'date': start_date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000
        }, {
            'date': end_date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500
        }]
        mock_query.return_value = mock_stats

        params = {
            'metrics': ['cpc', 'clicks'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        response = self.client.get(
            reverse('ad_group_ads_plus_daily_stats', kwargs={'ad_group_id': 1}),
            params,
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=['date'],
            order=[],
            ignore_diff_rows=True,
            conversion_goals=ListMatcher(['ga__2', 'ga__3', 'omniture__4', 'omniture__5']),
            ad_group=1,
            source=matcher
        )

        self.assertJSONEqual(response.content, {
            'data': {
                'goal_fields': {
                    'avg_tos': {
                        'id': 'time on site in seconds',
                        'name': 'time on site in seconds'
                    },
                    'avg_cost_per_conversion_goal_1': {
                        'id': 'avg_cost_per_conversion_goal_1',
                        'name': '$CPA - test conversion goal'
                    },
                    'avg_cost_per_conversion_goal_2': {
                        'id': 'avg_cost_per_conversion_goal_2',
                        'name': '$CPA - test conversion goal 2'
                    },
                    'avg_cost_per_conversion_goal_3': {
                        'id': 'avg_cost_per_conversion_goal_3',
                        'name': '$CPA - test conversion goal 3'
                    },
                    'avg_cost_per_conversion_goal_4': {
                        'id': 'avg_cost_per_conversion_goal_4',
                        'name': '$CPA - test conversion goal 4'
                    },
                    'avg_cost_per_conversion_goal_5': {
                        'id': 'avg_cost_per_conversion_goal_5',
                        'name': '$CPA - test conversion goal 5'
                    },
                    'cpc': {
                        'id': '$CPC',
                        'name': '$CPC'
                    },
                    'total_pageviews': {
                        'id': 'pages per session',
                        'name': 'pages per session'
                    },
                    'bounce_rate': {
                        'id': 'max bounce rate %',
                        'name': 'max bounce rate %'
                    },
                    'percent_new_users': {
                        'id': 'new visitors %',
                        'name': 'new visitors %'
                    },
                },
                'chart_data': [{
                    'id': 'totals',
                    'name': 'Totals',
                    'series_data': {
                        'clicks': [
                            [start_date.isoformat(), 1000],
                            [end_date.isoformat(), 1500]
                        ],
                        'cpc': [
                            [start_date.isoformat(), '0.0100'],
                            [end_date.isoformat(), '0.0200']
                        ]
                    }
                }],
                'conversion_goals': ListMatcher([
                    {'id': 'conversion_goal_2', 'name': 'test conversion goal 2'},
                    {'id': 'conversion_goal_1', 'name': 'test conversion goal'},
                    {'id': 'conversion_goal_3', 'name': 'test conversion goal 3'},
                    {'id': 'conversion_goal_4', 'name': 'test conversion goal 4'},
                    {'id': 'conversion_goal_5', 'name': 'test conversion goal 5'}
                ]),
                'campaign_goals': {}
            },
            'success': True
        })

    def test_get_with_conversion_goals(self, mock_touchpoint_query, mock_query):
        created_dt = datetime.datetime.utcnow()

        models.ConversionGoal.objects.filter(name='test conversion goal 5').delete()

        # set up a campaign and conversion goal
        campaign = models.Campaign.objects.get(pk=1)

        cg1 = models.CampaignGoal.objects.create(
            campaign=campaign,
            type=constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS,
            created_dt=created_dt,
        )

        models.CampaignGoalValue.objects.create(
            campaign_goal=cg1,
            value=Decimal('10'),
            created_dt=created_dt,
        )

        convg = models.ConversionGoal.objects.create(
            campaign=campaign,
            type=constants.ConversionGoalType.GA,
            name='Test Cg',
            conversion_window=30,
            goal_id='6',
        )

        convg1 = models.CampaignGoal.objects.create(
            campaign=campaign,
            conversion_goal=convg,
            type=constants.CampaignGoalKPI.CPA,
            created_dt=created_dt,
        )
        models.CampaignGoalValue.objects.create(
            campaign_goal=convg1,
            value=Decimal('5'),
            created_dt=created_dt,
        )

        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [{
            'date': start_date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'conversions': {
                'ga__6': 5,
            }
        }, {
            'date': end_date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'conversions': {
                'ga__6': 6,
            }
        }]
        mock_query.return_value = mock_stats

        mock_touchpoint_stats = []

        mock_touchpoint_query.return_value = mock_touchpoint_stats

        params = {
            'metrics': ['cpc', 'clicks', 'conversion_goal_5'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

        response = self.client.get(
            reverse('ad_group_ads_plus_daily_stats', kwargs={'ad_group_id': 1}),
            params,
            follow=True
        )

        matcher = QuerySetMatcher(models.Source.objects.all())
        mock_query.assert_called_with(
            start_date,
            end_date,
            breakdown=['date'],
            order=[],
            ignore_diff_rows=True,
            conversion_goals=ListMatcher(['ga__2', 'ga__3', 'omniture__4', 'ga__6']),
            ad_group=1,
            source=matcher
        )

        self.maxDiff = None
        self.assertDictEqual(json.loads(response.content), {
            'data': {
                'goal_fields': {
                    'avg_tos': {
                        'id': 'time on site in seconds',
                        'name': 'time on site in seconds'
                    },
                    'avg_cost_per_conversion_goal_1': {
                        'id': 'avg_cost_per_conversion_goal_1',
                        'name': '$CPA - test conversion goal'
                    },
                    'avg_cost_per_conversion_goal_2': {
                        'id': 'avg_cost_per_conversion_goal_2',
                        'name': '$CPA - test conversion goal 2'
                    },
                    'avg_cost_per_conversion_goal_3': {
                        'id': 'avg_cost_per_conversion_goal_3',
                        'name': '$CPA - test conversion goal 3'
                    },
                    'avg_cost_per_conversion_goal_4': {
                        'id': 'avg_cost_per_conversion_goal_4',
                        'name': '$CPA - test conversion goal 4'
                    },
                    'avg_cost_per_conversion_goal_5': {
                        'id': 'avg_cost_per_conversion_goal_5',
                        'name': '$CPA - Test Cg'
                    },
                    'cpc': {
                        'id': '$CPC',
                        'name': '$CPC'
                    },
                    'total_pageviews': {
                        'id': 'pages per session',
                        'name': 'pages per session'
                    },
                    'bounce_rate': {
                        'id': 'max bounce rate %',
                        'name': 'max bounce rate %'
                    },
                    'percent_new_users': {
                        'id': 'new visitors %',
                        'name': 'new visitors %'
                    },
                },
                'chart_data': [{
                    'id': 'totals',
                    'name': 'Totals',
                    'series_data': {
                        'clicks': [
                            [start_date.isoformat(), 1000],
                            [end_date.isoformat(), 1500]
                        ],
                        'cpc': [
                            [start_date.isoformat(), '0.0100'],
                            [end_date.isoformat(), '0.0200']
                        ],
                        'conversion_goal_5': [
                            [start_date.isoformat(), 5],
                            [end_date.isoformat(), 6],
                        ],
                    }
                }],
                'conversion_goals': ListMatcher([
                    {'id': 'conversion_goal_5', 'name': 'Test Cg'},
                    {'id': 'conversion_goal_4', 'name': 'test conversion goal 4'},
                    {'id': 'conversion_goal_3', 'name': 'test conversion goal 3'},
                    {'id': 'conversion_goal_2', 'name': 'test conversion goal 2'},
                    {'id': 'conversion_goal_1', 'name': 'test conversion goal'},
                ]),
                'campaign_goals': {},
            },
            'success': True
        })


@patch('dash.table.reports.api_touchpointconversions.query')
@patch('dash.views.daily_stats.reports.api_publishers.query')
class AdGroupPublishersDailyStatsTest(TestCase):
    fixtures = ['test_views']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query, mock_touchpoint_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [{
            'date': start_date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'conversions': {},
        }, {
            'date': end_date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'conversions': {},
        }]
        mock_query.return_value = mock_stats

        ad_group = models.AdGroup.objects.get(pk=1)
        touchpoint_conversion_goal = \
            ad_group.campaign.conversiongoal_set.filter(type=conversions_helper.PIXEL_GOAL_TYPE)[0]

        mock_stats2 = [{
            'date': start_date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }, {
            'date': start_date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_touchpoint_query.return_value = mock_stats2

        params = {
            'metrics': ['cpc', 'clicks'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'totals': 'true'
        }

        response = self.client.get(
            reverse('ad_group_publishers_daily_stats', kwargs={'ad_group_id': 1}),
            params,
            follow=True
        )

        mock_query.assert_called_with(
            start_date,
            end_date,
            order_fields=['date'],
            breakdown_fields=['date'],
            constraints={'ad_group': ad_group.id},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpoint_query.assert_any_call(
            start_date,
            end_date,
            breakdown=['date'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        self.maxDiff = None
        self.assertJSONEqual(response.content, {
            'data': {
                'goal_fields': {
                    'avg_tos': {
                        'id': 'time on site in seconds',
                        'name': 'time on site in seconds'
                    },
                    'avg_cost_per_conversion_goal_1': {
                        'id': 'avg_cost_per_conversion_goal_1',
                        'name': '$CPA - test conversion goal'
                    },
                    'avg_cost_per_conversion_goal_2': {
                        'id': 'avg_cost_per_conversion_goal_2',
                        'name': '$CPA - test conversion goal 2'
                    },
                    'avg_cost_per_conversion_goal_3': {
                        'id': 'avg_cost_per_conversion_goal_3',
                        'name': '$CPA - test conversion goal 3'
                    },
                    'avg_cost_per_conversion_goal_4': {
                        'id': 'avg_cost_per_conversion_goal_4',
                        'name': '$CPA - test conversion goal 4'
                    },
                    'avg_cost_per_conversion_goal_5': {
                        'id': 'avg_cost_per_conversion_goal_5',
                        'name': '$CPA - test conversion goal 5'
                    },
                    'cpc': {
                        'id': '$CPC',
                        'name': '$CPC'
                    },
                    'total_pageviews': {
                        'id': 'pages per session',
                        'name': 'pages per session'
                    },
                    'bounce_rate': {
                        'id': 'max bounce rate %',
                        'name': 'max bounce rate %'
                    },
                    'percent_new_users': {
                        'id': 'new visitors %',
                        'name': 'new visitors %'
                    },
                },
                'chart_data': [{
                    'id': 'totals',
                    'name': 'Totals',
                    'series_data': {
                        'clicks': [
                            [start_date.isoformat(), 1000],
                            [end_date.isoformat(), 1500]
                        ],
                        'cpc': [
                            [start_date.isoformat(), '0.0100'],
                            [end_date.isoformat(), '0.0200']
                        ]
                    },
                }],
                'conversion_goals': ListMatcher([
                    {
                        'id': 'conversion_goal_5',
                        'name': 'test conversion goal 5'
                    },
                    {
                        'id': 'conversion_goal_4',
                        'name': 'test conversion goal 4'
                    },
                    {
                        'id': 'conversion_goal_3',
                        'name': 'test conversion goal 3'
                    },
                    {
                        'id': 'conversion_goal_2',
                        'name': 'test conversion goal 2'
                    },
                    {
                        'id': 'conversion_goal_1',
                        'name': 'test conversion goal'
                    },
                ]),
                'campaign_goals': {},
            },
            'success': True
        })
