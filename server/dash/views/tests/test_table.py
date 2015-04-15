import datetime
import json
from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse

from utils.test_helper import QuerySetMatcher
from zemauth.models import User
from dash import models
from actionlog.models import ActionLog
import actionlog.constants


@patch('dash.views.table.reports.api_contentads.query')
class AdGroupAdsPlusTableTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)
            self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('last_change', result['data'])
        self.assertEqual(result['data']['last_change'], '2015-02-22T19:00:00')

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], 'title')

        self.assertIn('pagination', result['data'])
        self.assertEqual(result['data']['pagination'], {
            'count': 2,
            'currentPage': 1,
            'endIndex': 2,
            'numPages': 1,
            'size': 2,
            'startIndex': 1
        })

        self.assertIn('rows', result['data'])
        self.assertEqual(result['data']['rows'], [{
            'status_setting': 2,
            'upload_time': '2015-02-22T19:00:00',
            'ctr': None,
            'title': 'Article with no content_ad_sources',
            'url': 'http://testurl.com',
            'clicks': None,
            'cpc': None,
            'image_urls': {
                'square': '/123456789/120x120.jpg',
                'landscape': '/123456789/193x120.jpg'},
            'editable_fields': ['status_setting'],
            'submission_status': [],
            'cost': None,
            'batch_name': 'batch 1',
            'impressions': None,
            'id': '2'
        }, {
            'batch_name': 'batch 1',
            'clicks': 1000,
            'cost': 100,
            'cpc': '0.0100',
            'ctr': '12.5000',
            'editable_fields': ['status_setting'],
            'id': '1',
            'image_urls': {
                'landscape': '/123456789/193x120.jpg',
                'square': '/123456789/120x120.jpg'
            },
            'impressions': 1000000,
            'status_setting': 1,
            'submission_status': [{
                'name': 'AdsNative',
                'status': 1,
                'text': 'Pending / Paused'
            }, {
                'name': 'Gravity',
                'status': 2,
                'text': 'Approved / Paused'
            }],
            'title': 'Test Article',
            'upload_time': '2015-02-22T19:00:00',
            'url': 'http://testurl.com'
        }])

        self.assertIn('totals', result['data'])
        self.assertEqual(result['data']['totals'], {
            'clicks': 1500,
            'cost': 200,
            'cpc': '0.0200',
            'ctr': '15.5000',
            'impressions': 2000000
        })

    def test_get_filtered_sources(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'filtered_sources': '1,2'
        }

        response = self.client.get(
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.filter(id__in=[1, 2]))

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)
        self.assertEqual(result['data']['rows'][0]['id'], '1')

    def test_get_order(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': '-title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], '-title')

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 2)
        self.assertEqual(result['data']['rows'][0]['title'], 'Test Article')
        self.assertEqual(result['data']['rows'][1]['title'], 'Article with no content_ad_sources')


class AdGroupAdsPlusTableUpdatesTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)
            self.client.login(username=self.user.email, password=password)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        content_ad_source = models.ContentAdSource.objects.get(pk=1)

        ActionLog(
            state=actionlog.constants.ActionState.WAITING,
            content_ad_source=content_ad_source,
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.UPDATE_CONTENT_AD,
            action_type=actionlog.constants.ActionType.AUTOMATIC
        ).save()

        params = {}
        response = self.client.get(
            reverse('ad_group_ads_plus_table_updates', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('last_change', result['data'])
        self.assertEqual(result['data']['last_change'], '2015-02-22T19:00:00')

        self.assertIn('notifications', result['data'])
        self.assertEqual(result['data']['notifications'], {
            '1': {
                'message': 'Status is being changed from Paused to Enabled',
                'in_progress': True
            }
        })

        self.assertIn('in_progress', result['data'])
        self.assertEqual(result['data']['in_progress'], True)

        self.assertIn('rows', result['data'])
        self.assertEqual(result['data']['rows'], {
            '1': {
                'submission_status': [{
                    'status': 1,
                    'text': 'Pending / Paused',
                    'name': 'AdsNative'
                }, {
                    'status': 2,
                    'text': 'Approved / Paused',
                    'name': 'Gravity'
                }],
                'status_setting': 1
            }
        })
