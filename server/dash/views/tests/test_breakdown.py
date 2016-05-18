import json
import datetime
from mock import patch

from django.test import TestCase, Client
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse

from zemauth.models import User
from utils import test_helper

from dash import models
from dash.views import breakdown


class ExtractConstraintsTest(TestCase):
    def test_extract_constraints(self):
        form_data = {
            'breakdown': ['account', 'source', 'dma', 'day'],
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 3, 4]),
            'show_archived': True,
            'breakdown_page': ['123', '323'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        }

        self.assertDictEqual(breakdown.extract_constraints(form_data), {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'source': test_helper.QuerySetMatcher(
                models.Source.objects.filter(pk__in=[1, 3, 4])),
            'show_archived': True,
        })

    def test_add_kwargs(self):
        form_data = {
            'breakdown': ['account', 'source', 'dma', 'day'],
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk__in=[1, 3, 4]),
            'show_archived': True,
            'breakdown_page': ['123', '323'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        }

        self.assertDictEqual(
            breakdown.extract_constraints(
                form_data,
                account=models.Account.objects.get(pk=1),
                campaign=models.Campaign.objects.get(pk=1)
            ),
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
            }
        )



@patch('stats.api_breakdowns.query')
class AllAccountsBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_post(self, mock_query):

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': ['1-2-33','1-2-34','1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_all_accounts', kwargs={
                'breakdown': '/account/campaign/dma/day'
            }),
            data=json.dumps(params),
            content_type='application/json'
        )

        print response
        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            self.user,
            ['account', 'campaign', 'dma', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
            },
            ['1-2-33','1-2-34','1-3-22'],
            '-clicks',
            33,
            5
        )


@patch('stats.api_breakdowns.query')
class AccountBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_post(self, mock_query):

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': ['1-2-33','1-2-34','1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_accounts', kwargs={
                'account_id': 1,
                'breakdown': '/campaign/source/dma/day'
            }),
            data=json.dumps(params),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            self.user,
            ['campaign', 'source', 'dma', 'day'],
            {
                'account': models.Account.objects.get(pk=1),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
            },
            ['1-2-33','1-2-34','1-3-22'],
            '-clicks',
            33,
            5
        )


@patch('stats.api_breakdowns.query')
class CampaignBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_post(self, mock_query):

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': ['1-2-33','1-2-34','1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_campaigns', kwargs={
                'campaign_id': 1,
                'breakdown': '/ad_group/source/dma/day'
            }),
            data=json.dumps(params),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            self.user,
            ['ad_group', 'source', 'dma', 'day'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
            },
            ['1-2-33','1-2-34','1-3-22'],
            '-clicks',
            33,
            5
        )


@patch('stats.api_breakdowns.query')
class AdGroupBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_post(self, mock_query):

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': ['1-2-33','1-2-34','1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_ad_groups', kwargs={
                'ad_group_id': 1,
                'breakdown': '/content_ad/source/dma/day'
            }),
            data=json.dumps(params),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            self.user,
            ['content_ad', 'source', 'dma', 'day'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'source': test_helper.QuerySetMatcher(
                    models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
            },
            ['1-2-33','1-2-34','1-3-22'],
            '-clicks',
            33,
            5
        )
