from mock import patch
import datetime
import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from utils.test_helper import QuerySetMatcher
from zemauth.models import User
from dash import models


class BaseDailyStatsTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.client.login(username=self.user.email, password=password)

        self.patcher = patch('dash.views.daily_stats.reports.api.query')
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
                'goals': {},
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


class AccountsDailyStatsTest(BaseDailyStatsTest):
    def test_get_by_source(self):
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
            self.date,
            self.date,
            ['date'],
            ['date'],
            account=accounts_matcher,
            source=sources_matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'source'],
            ['date'],
            account=accounts_matcher,
            source_id=[source_id]
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
            self.date,
            self.date,
            ['date'],
            ['date'],
            account=1,
            source=matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'source'],
            ['date'],
            account=1,
            source_id=[source_id]
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
            self.date,
            self.date,
            ['date'],
            ['date'],
            account=1,
            source=matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'campaign'],
            ['date'],
            account=1,
            ad_group__campaign__id=[campaign_id]
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
        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date'],
            ['date'],
            campaign=1,
            source=matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'source'],
            ['date'],
            campaign=1,
            source_id=[source_id]
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
        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date'],
            ['date'],
            campaign=1,
            source=matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'ad_group'],
            ['date'],
            campaign=1,
            ad_group_id=[ad_group_id]
        )

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self._assert_response(response, ad_group_id, ad_group.name)


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
        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date'],
            ['date'],
            ad_group=1,
            source=matcher
        )

        self.mock_query.assert_any_call(
            self.date,
            self.date,
            ['date', 'source'],
            ['date'],
            ad_group=1,
            source_id=[source_id]
        )

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)


@patch('dash.views.daily_stats.reports.api_contentads.query')
class AdGroupAdsPlusDailyStatsTest(TestCase):
    fixtures = ['test_views']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
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
            breakdown = ['date'],
            constraints = { 'ad_group': 1,
                            'source': matcher}
        )

        self.assertJSONEqual(response.content, {
            'data': {
                'goals': {},
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
                }]
            },
            'success': True
        })
