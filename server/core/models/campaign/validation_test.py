from django.test import TestCase

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)

    def test_user_changes_type_for_new_campaign(self):
        self.assertEqual(self.campaign.type, constants.CampaignType.CONTENT)
        self.campaign.update_type(constants.CampaignType.VIDEO)
        self.assertEqual(self.campaign.type, constants.CampaignType.VIDEO)

    def test_user_changes_type_for_campaign_with_ad_group(self):
        magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        with self.assertRaises(exceptions.CannotChangeType):
            self.campaign.update_type(constants.CampaignType.VIDEO)

    def test_user_changes_type_for_campaign_with_multiple_ad_groups(self):
        magic_mixer.cycle(10).blend(core.models.AdGroup, campaign=self.campaign)
        with self.assertRaises(exceptions.CannotChangeType):
            self.campaign.update_type(constants.CampaignType.VIDEO)
