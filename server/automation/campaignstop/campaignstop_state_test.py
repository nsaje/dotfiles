from mock import patch

from django.test import TestCase

import core.entity
from . import CampaignStopState

from utils.magic_mixer import magic_mixer
from utils import email_helper


class CampaignStopStateTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign)
        self.campaign.settings.update(None, campaign_manager=magic_mixer.blend_user())

    @patch("utils.email_helper.send_official_email", wraps=email_helper.send_official_email)
    def test_almost_depleted_change_sends_email(self, mock_send_official_email):
        campaignstop_state = CampaignStopState.objects.create(campaign=self.campaign, almost_depleted=False)
        campaignstop_state.update_almost_depleted(True)
        self.assertTrue(mock_send_official_email.called)

        mock_send_official_email.reset_mock()
        campaignstop_state.update_almost_depleted(True)
        self.assertFalse(mock_send_official_email.called)

        campaignstop_state.update_almost_depleted(False)
        self.assertFalse(mock_send_official_email.called)

        campaignstop_state.update_almost_depleted(False)
        self.assertFalse(mock_send_official_email.called)
