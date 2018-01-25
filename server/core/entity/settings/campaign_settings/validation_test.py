from django.test import TestCase

import core.entity
from dash import constants
from utils.magic_mixer import magic_mixer
from .exceptions import CannotChangeLanguage


class ValidationTestCase(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign)

    def test_user_changes_language_for_new_campaign(self):
        self.assertEqual(self.campaign.settings.language, constants.CampaignSettingsLanguage.ENGLISH)
        self.campaign.settings.update(None, language=constants.CampaignSettingsLanguage.SPANISH)
        self.assertEqual(self.campaign.settings.language, constants.CampaignSettingsLanguage.SPANISH)

    def test_user_changes_language_for_campaign_with_ad_group(self):
        magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)
        with self.assertRaises(CannotChangeLanguage):
            self.campaign.settings.update(None, language=constants.CampaignSettingsLanguage.SPANISH)

    def test_user_changes_language_for_campaign_with_multiple_ad_groups(self):
        magic_mixer.cycle(10).blend(core.entity.AdGroup, campaign=self.campaign)
        with self.assertRaises(CannotChangeLanguage):
            self.campaign.settings.update(None, language=constants.CampaignSettingsLanguage.SPANISH)
