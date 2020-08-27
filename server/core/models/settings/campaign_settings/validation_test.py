from django.test import TestCase

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer


class ValidationTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)

    def test_user_changes_language_for_new_campaign(self):
        self.assertEqual(self.campaign.settings.language, constants.Language.ENGLISH)
        self.campaign.settings.update(None, language=constants.Language.SPANISH)
        self.assertEqual(self.campaign.settings.language, constants.Language.SPANISH)

    def test_user_changes_language_for_campaign_with_ad_group(self):
        magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.campaign.settings.update(None, language=constants.Language.SPANISH)
        self.assertEqual(self.campaign.settings.language, constants.Language.SPANISH)
