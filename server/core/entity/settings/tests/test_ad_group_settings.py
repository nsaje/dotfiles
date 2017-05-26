import datetime
from django.test import TestCase

from utils import dates_helper
from utils.magic_mixer import magic_mixer

from dash import constants

import core.entity


class AdGroupSettingsCreate(TestCase):
    def test_create_default(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        campaign_settings = magic_mixer.blend(
            core.entity.settings.CampaignSettings, campaign=ad_group.campaign,
            target_devices=[constants.AdTargetDevice.DESKTOP])
        ad_group_settings = core.entity.settings.AdGroupSettings.objects.create_default(ad_group)

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        self.assertEqual(ad_group_settings.target_devices, campaign_settings.target_devices)
        self.assertEqual(ad_group_settings.target_regions, campaign_settings.target_regions)
        self.assertTrue(ad_group_settings.b1_sources_group_enabled)

    def test_create_restapi_default(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        campaign_settings = magic_mixer.blend(
            core.entity.settings.CampaignSettings, campaign=ad_group.campaign,
            target_devices=[constants.AdTargetDevice.DESKTOP])
        ad_group_settings = core.entity.settings.AdGroupSettings.objects.create_restapi_default(ad_group)

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        self.assertEqual(ad_group_settings.target_devices, campaign_settings.target_devices)
        self.assertEqual(ad_group_settings.target_regions, campaign_settings.target_regions)
        self.assertFalse(ad_group_settings.b1_sources_group_enabled)

    def test_clone(self):
        source_ad_group_settings = magic_mixer.blend(
            core.entity.settings.AdGroupSettings,
            end_date=dates_helper.local_today() + datetime.timedelta(days=1))

        ad_group_settings = core.entity.settings.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(),
            magic_mixer.blend(core.entity.AdGroup),
            source_ad_group_settings)

        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_settings.archived, False)

        for field in set(core.entity.settings.AdGroupSettings._settings_fields) - {'archived', 'state'}:
            self.assertEqual(getattr(ad_group_settings, field), getattr(source_ad_group_settings, field))

    def test_clone_ends_in_past(self):
        end_date = dates_helper.local_yesterday()
        source_ad_group_settings = magic_mixer.blend(core.entity.settings.AdGroupSettings, end_date=end_date)

        ad_group_settings = core.entity.settings.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(),
            magic_mixer.blend(core.entity.AdGroup),
            source_ad_group_settings)

        self.assertEqual(ad_group_settings.start_date, dates_helper.local_today())
        self.assertEqual(ad_group_settings.end_date, None)
        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_settings.archived, False)
