import datetime
import json
import mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test.client import Client

from dash.models import AdGroupSource, Article, AdGroupSourceState
from actionlog.models import ActionLog
from actionlog import constants
from reports.models import ArticleStats


class CampaignStatusTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_update_status(self, _):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'daily_budget_cc': 100000,
                'state': 1,
                'cpc_cc': 3000
            }
        }

        ad_group_source = AdGroupSource.objects.get(id=1)

        current_state = AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        action_log = ActionLog(
            action=constants.Action.FETCH_CAMPAIGN_STATUS,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
        )
        action_log.save()

        c = Client()
        response = c.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        latest_state = AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        self.assertNotEqual(latest_state, current_state)


class FetchReportsTestCase(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_fetch_reports(self, _):
        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [[["fake"], [article_row]]]
        }

        ad_group_source = AdGroupSource.objects.get(id=1)
        action_log = ActionLog(
            action=constants.Action.FETCH_REPORTS,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            payload={
                'action': constants.Action.FETCH_REPORTS,
                'source': ad_group_source.source.source_type.type,
                'args': {
                    'partner_campaign_id': '"[fake]"',
                    'date': datetime.date(2014, 7, 1)
                },
            }
        )
        action_log.save()

        c = Client()
        response = c.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )

        self.assertEqual(response.status_code, 200)
        article = Article.objects.get(title=article_row['title'], url=article_row['url'])
        article_stats = ArticleStats.objects.get(
            article=article,
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source
        )

        self.assertEqual(article_stats.impressions, article_row['impressions'])
        self.assertEqual(article_stats.clicks, article_row['clicks'])
        self.assertEqual(article_stats.cost_cc, article_row['cost_cc'])
