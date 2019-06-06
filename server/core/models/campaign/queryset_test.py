import mock
from django.test import TestCase

import automation.campaignstop
from utils.magic_mixer import magic_mixer

from . import model


class CampaignQuerysetTest(TestCase):
    @mock.patch.object(automation.campaignstop, "get_campaignstop_states")
    def test_filter_active(self, mock_get_campaign_states):
        campaigns = magic_mixer.cycle(3).blend(model.Campaign)
        mock_get_campaign_states.return_value = {
            campaigns[0].id: {"allowed_to_run": True},
            campaigns[1].id: {"allowed_to_run": True},
            campaigns[2].id: {"allowed_to_run": False},
        }
        self.assertEqual(set(model.Campaign.objects.filter_active()), set(campaigns[0:2]))
