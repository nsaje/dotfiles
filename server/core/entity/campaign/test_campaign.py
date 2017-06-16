from django.test import TestCase

import zemauth
import dash
from utils.magic_mixer import magic_mixer

from campaign import Campaign


class TestCampaignManager(TestCase):

    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User)
        self.account = magic_mixer.blend(dash.models.Account, users=[self.user])

    def test_create(self):
        campaign = Campaign.objects.create(self.user, self.account, 'xyz')
        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign.account, self.account)
        self.assertEqual(campaign.name, 'xyz')
        self.assertEqual(campaign_settings.campaign_manager, self.user)
        self.assertEqual(campaign_settings.name, 'xyz')
