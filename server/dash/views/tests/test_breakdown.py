import datetime
from mock import patch

from django.test import TestCase, Client
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse

from zemauth.models import User
from utils import test_helper

from dash import models
from dash.views import breakdown


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
            'page': 5,
            'size': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': """{
                "1": {
                    "6": ["501","502"],
                    "7": ["501","522"]
                },
                "2": {
                    "33": ["502"],
                    "2": ["650","677","23"]
                },
                "3": []
            }""",
        }

        response = self.client.post(
            reverse('breakdown_all_accounts', kwargs={
                'breakdown': '/account/campaign/dma/day'
            }),
            data=params,
        )

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
            test_helper.ListMatcher([
                {'account': 1, 'campaign': 7, 'dma': ['501', '522']},
                {'account': 1, 'campaign': 6, 'dma': ['501', '502']},
                {'account': 2, 'campaign': 33, 'dma': ['502']},
                {'account': 2, 'campaign': 2, 'dma': ['650', '677', '23']},
                {'account': 3, 'campaign': []},
            ]),
            '-clicks',
            5,
            33
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
            'page': 5,
            'size': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': """{
                "1": {
                    "6": ["501","502"],
                    "7": ["501","522"]
                },
                "2": {
                    "33": ["502"],
                    "2": ["650","677","23"]
                },
                "3": []
            }""",
        }

        response = self.client.post(
            reverse('breakdown_accounts', kwargs={
                'account_id': 1,
                'breakdown': '/campaign/source/dma/day'
            }),
            data=params,
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
            test_helper.ListMatcher([
                {'campaign': 1, 'source': 7, 'dma': ['501', '522']},
                {'campaign': 1, 'source': 6, 'dma': ['501', '502']},
                {'campaign': 2, 'source': 33, 'dma': ['502']},
                {'campaign': 2, 'source': 2, 'dma': ['650', '677', '23']},
                {'campaign': 3, 'source': []},
            ]),
            '-clicks',
            5,
            33
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
            'page': 5,
            'size': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': """{
                "1": {
                    "6": ["501","502"],
                    "7": ["501","522"]
                },
                "2": {
                    "33": ["502"],
                    "2": ["650","677","23"]
                },
                "3": []
            }""",
        }

        response = self.client.post(
            reverse('breakdown_campaigns', kwargs={
                'campaign_id': 1,
                'breakdown': '/ad_group/source/dma/day'
            }),
            data=params,
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
            test_helper.ListMatcher([
                {'ad_group': 1, 'source': 7, 'dma': ['501', '522']},
                {'ad_group': 1, 'source': 6, 'dma': ['501', '502']},
                {'ad_group': 2, 'source': 33, 'dma': ['502']},
                {'ad_group': 2, 'source': 2, 'dma': ['650', '677', '23']},
                {'ad_group': 3, 'source': []},
            ]),
            '-clicks',
            5,
            33
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
            'page': 5,
            'size': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': """{
                "1": {
                    "6": ["501","502"],
                    "7": ["501","522"]
                },
                "2": {
                    "33": ["502"],
                    "2": ["650","677","23"]
                },
                "3": []
            }""",
        }

        response = self.client.post(
            reverse('breakdown_ad_groups', kwargs={
                'ad_group_id': 1,
                'breakdown': '/content_ad/source/dma/day'
            }),
            data=params,
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
            test_helper.ListMatcher([
                {'content_ad': 1, 'source': 7, 'dma': ['501', '522']},
                {'content_ad': 1, 'source': 6, 'dma': ['501', '502']},
                {'content_ad': 2, 'source': 33, 'dma': ['502']},
                {'content_ad': 2, 'source': 2, 'dma': ['650', '677', '23']},
                {'content_ad': 3, 'source': []},
            ]),
            '-clicks',
            5,
            33
        )
