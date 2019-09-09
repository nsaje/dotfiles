from django.test import TestCase

import core.features.multicurrency
import core.models
from utils.magic_mixer import magic_mixer

from . import model


class CampaignSettingsManagerTest(TestCase):
    def test_clone(self):
        source_campaign = magic_mixer.blend(core.models.Campaign)

        campaign_settings = model.CampaignSettings.objects.clone(
            magic_mixer.blend_request_user(),
            magic_mixer.blend(core.models.Campaign, name="Cloned Campaign"),
            source_campaign.settings,
        )

        self.assertEqual(campaign_settings.campaign.archived, False)
        self.assertEqual(campaign_settings.archived, False)
        self.assertEqual(campaign_settings.name, "Cloned Campaign")

        for field in set(model.CampaignSettings._settings_fields) - {"archived", "name"}:
            self.assertEqual(getattr(campaign_settings, field), getattr(source_campaign.settings, field))
