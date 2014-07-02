import json

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from utils import test_decorators

from dash.models import AdGroupNetwork
from actionlog.models import ActionLog
from actionlog import constants

from zweiapi.views import zwei_callback


class CampaignStatusTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.factory = RequestFactory()

    @test_decorators.integration_test
    def test_update_status(self):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'daily_budget_cc': 100000,
                'state': 1,
                'cpc_cc': 3000
            }
        }

        ad_group_network = AdGroupNetwork.objects.get(id=1)
        current_settings = ad_group_network.settings.latest()
        action_log = ActionLog(
            action=constants.Action.FETCH_CAMPAIGN_STATUS,
            action_status=constants.ActionStatus.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_network=ad_group_network,
        )
        action_log.save()

        request = self.factory.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )

        response = zwei_callback(request, action_log.id)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(ad_group_network.settings.latest(), current_settings)
