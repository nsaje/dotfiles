from django.test import TestCase
from mock import patch

import core.models
from utils import exc
from utils.magic_mixer import magic_mixer

from .model import Campaign


class TestCampaignManager(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(core.models.Account, users=[self.request.user])

    @patch("automation.autopilot.recalculate_budgets_campaign")
    def test_create(self, mock_autopilot):
        campaign = Campaign.objects.create(self.request, self.account, "xyz")
        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign.account, self.account)
        self.assertEqual(campaign.name, "xyz")
        self.assertEqual(campaign_settings.campaign_manager, self.request.user)
        self.assertEqual(campaign_settings.name, "xyz")

    def test_create_no_currency(self):
        self.account.currency = None
        self.account.save(None)
        with self.assertRaises(exc.ValidationError):
            Campaign.objects.create(self.request, self.account, "xyz")
