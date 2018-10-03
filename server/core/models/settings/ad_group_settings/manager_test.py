from mock import patch
from decimal import Decimal
import datetime
from django.test import TestCase

from utils import dates_helper
from utils.magic_mixer import magic_mixer

from dash import constants

import core.models
import core.features.multicurrency
from . import model


class AdGroupSettingsCreate(TestCase):
    def test_create_default(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.campaign.settings.update(None, target_devices=[constants.AdTargetDevice.DESKTOP])
        ad_group_settings = model.AdGroupSettings.objects.create_default(ad_group, "test")

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        self.assertEqual(ad_group_settings.ad_group_name, "test")
        self.assertEqual(ad_group_settings.target_devices, ad_group.campaign.settings.target_devices)
        self.assertEqual(ad_group_settings.target_regions, ad_group.campaign.settings.target_regions)
        self.assertEqual(
            ad_group_settings.exclusion_target_regions, ad_group.campaign.settings.exclusion_target_regions
        )
        self.assertTrue(ad_group_settings.b1_sources_group_enabled)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_create_multicurrency(self, mock_exchange_rate):
        mock_exchange_rate.return_value = Decimal("2.0")
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__currency="XYZ")
        ad_group_settings = model.AdGroupSettings.objects.create_default(ad_group, "test")

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        for field in core.models.settings.AdGroupSettings.multicurrency_fields:
            if not getattr(ad_group_settings, field):
                continue
            self.assertEqual(getattr(ad_group_settings, "local_%s" % field), 2 * getattr(ad_group_settings, field))

    def test_create_restapi_default(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.campaign.settings.update(None, target_devices=[constants.AdTargetDevice.DESKTOP])
        ad_group_settings = model.AdGroupSettings.objects.create_restapi_default(ad_group, "test")

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        self.assertEqual(ad_group_settings.ad_group_name, "test")
        self.assertEqual(ad_group_settings.target_devices, ad_group.campaign.settings.target_devices)
        self.assertEqual(ad_group_settings.target_regions, ad_group.campaign.settings.target_regions)
        self.assertEqual(
            ad_group_settings.exclusion_target_regions, ad_group.campaign.settings.exclusion_target_regions
        )
        self.assertFalse(ad_group_settings.b1_sources_group_enabled)

    def test_clone(self):
        end_date = dates_helper.local_today() + datetime.timedelta(days=1)
        source_ad_group = magic_mixer.blend(core.models.AdGroup)
        source_ad_group.settings.update_unsafe(None, end_date=end_date)

        ad_group_settings = model.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(),
            magic_mixer.blend(core.models.AdGroup, name="AAAA"),
            source_ad_group.settings,
        )

        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_settings.archived, False)
        self.assertEqual(ad_group_settings.ad_group_name, "AAAA")

        for field in set(model.AdGroupSettings._settings_fields) - {"archived", "state", "ad_group_name"}:
            self.assertEqual(getattr(ad_group_settings, field), getattr(source_ad_group.settings, field))

    def test_clone_ends_in_past(self):
        end_date = dates_helper.local_yesterday()
        source_ad_group = magic_mixer.blend(core.models.AdGroup)
        source_ad_group.settings.update_unsafe(None, end_date=end_date)

        ad_group_settings = model.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(), magic_mixer.blend(core.models.AdGroup), source_ad_group.settings
        )

        self.assertEqual(ad_group_settings.start_date, dates_helper.local_today())
        self.assertEqual(ad_group_settings.end_date, None)
        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_settings.archived, False)
