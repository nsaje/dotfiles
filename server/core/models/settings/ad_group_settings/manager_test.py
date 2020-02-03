import datetime
from decimal import Decimal

from django.test import TestCase
from mock import patch

import core.features.multicurrency
from dash import constants
from dash import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import model


class AdGroupSettingsCreate(TestCase):
    def test_create_default(self):
        ad_group = magic_mixer.blend(models.AdGroup)
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
        ad_group = magic_mixer.blend(models.AdGroup, campaign__account__currency="XYZ")
        ad_group_settings = model.AdGroupSettings.objects.create_default(ad_group, "test")

        self.assertEqual(ad_group_settings.ad_group, ad_group)
        for field in models.AdGroupSettings.multicurrency_fields:
            if not getattr(ad_group_settings, field):
                continue
            self.assertEqual(getattr(ad_group_settings, "local_%s" % field), 2 * getattr(ad_group_settings, field))

    def test_create_restapi_default(self):
        ad_group = magic_mixer.blend(models.AdGroup)
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
        source_ad_group = magic_mixer.blend(models.AdGroup)
        source_ad_group.settings.update_unsafe(None, end_date=end_date)

        ad_group_settings = model.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(), magic_mixer.blend(models.AdGroup, name="AAAA"), source_ad_group.settings
        )

        self.assertEqual(ad_group_settings.state, source_ad_group.settings.state)
        self.assertEqual(ad_group_settings.archived, False)
        self.assertEqual(ad_group_settings.ad_group_name, "AAAA")

        for field in set(model.AdGroupSettings._settings_fields) - {"archived", "state", "ad_group_name"}:
            self.assertEqual(getattr(ad_group_settings, field), getattr(source_ad_group.settings, field))

    def test_clone_with_set_state(self):
        source_ad_group = magic_mixer.blend(core.models.AdGroup)
        self.assertEqual(source_ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)

        ad_group_settings = model.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(),
            magic_mixer.blend(core.models.AdGroup, name="AAAA"),
            source_ad_group.settings,
            state_override=constants.AdGroupSettingsState.ACTIVE,
        )

        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.ACTIVE)

    def test_clone_ends_in_past(self):
        end_date = dates_helper.local_yesterday()
        source_ad_group = magic_mixer.blend(models.AdGroup)
        source_ad_group.settings.update_unsafe(None, end_date=end_date)

        ad_group_settings = model.AdGroupSettings.objects.clone(
            magic_mixer.blend_request_user(), magic_mixer.blend(models.AdGroup), source_ad_group.settings
        )

        self.assertEqual(ad_group_settings.start_date, dates_helper.local_today())
        self.assertEqual(ad_group_settings.end_date, None)
        self.assertEqual(ad_group_settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_settings.archived, False)


class AdGroupSettingsGetDefault(TestCase):
    def test_no_campaign_goal(self):
        campaign = magic_mixer.blend(models.Campaign)
        ad_group = models.AdGroup(campaign=campaign, name="")
        default_settings = models.AdGroupSettings.objects.get_default(ad_group, name="")
        self.assertEqual(default_settings.cpc, model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(default_settings.local_cpc, model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.local_cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_no_campaign_goal_multicurrency(self, mock_exchange_rate):
        exchange_rate = Decimal("2.0")
        mock_exchange_rate.return_value = exchange_rate
        campaign = magic_mixer.blend(models.Campaign)
        ad_group = models.AdGroup(campaign=campaign, name="")
        default_settings = models.AdGroupSettings.objects.get_default(ad_group, name="")
        self.assertEqual(default_settings.cpc, model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(default_settings.local_cpc, exchange_rate * model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.local_cpm, exchange_rate * model.AdGroupSettings.DEFAULT_CPM_VALUE)

    def test_no_cpc_campaign_goal(self):
        campaign = magic_mixer.blend(models.Campaign)
        campaign_goal = magic_mixer.blend(models.CampaignGoal, campaign=campaign, type=constants.CampaignGoalKPI.CPA)
        magic_mixer.blend(
            models.CampaignGoalValue, campaign_goal=campaign_goal, value=Decimal("1.5"), local_value=Decimal("1.5")
        )
        ad_group = models.AdGroup(campaign=campaign, name="")
        default_settings = models.AdGroupSettings.objects.get_default(ad_group, name="")
        self.assertEqual(default_settings.cpc, model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(default_settings.local_cpc, model.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(default_settings.local_cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)

    def test_campaign_goal(self):
        campaign = magic_mixer.blend(models.Campaign)
        campaign_goal = magic_mixer.blend(models.CampaignGoal, campaign=campaign, type=constants.CampaignGoalKPI.CPC)
        campaign_goal_value = magic_mixer.blend(
            models.CampaignGoalValue, campaign_goal=campaign_goal, value=Decimal("1.5"), local_value=Decimal("1.5")
        )
        ad_group = models.AdGroup(campaign=campaign, name="")
        default_settings = models.AdGroupSettings.objects.get_default(ad_group, name="")
        self.assertEqual(default_settings.cpc, campaign_goal_value.value)
        self.assertEqual(default_settings.cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(default_settings.local_cpc, campaign_goal_value.local_value)
        self.assertEqual(default_settings.local_cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_campaign_goal_multicurrency(self, mock_exchange_rate):
        exchange_rate = Decimal("2.0")
        mock_exchange_rate.return_value = exchange_rate
        campaign = magic_mixer.blend(models.Campaign)
        campaign_goal = magic_mixer.blend(models.CampaignGoal, campaign=campaign, type=constants.CampaignGoalKPI.CPC)
        campaign_goal_value = magic_mixer.blend(
            models.CampaignGoalValue,
            campaign_goal=campaign_goal,
            value=Decimal("1.5"),
            local_value=exchange_rate * Decimal("1.5"),
        )
        ad_group = models.AdGroup(campaign=campaign, name="")
        default_settings = models.AdGroupSettings.objects.get_default(ad_group, name="")
        self.assertEqual(default_settings.cpc, campaign_goal_value.value)
        self.assertEqual(default_settings.cpm, model.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(default_settings.local_cpc, campaign_goal_value.local_value)
        self.assertEqual(default_settings.local_cpm, exchange_rate * model.AdGroupSettings.DEFAULT_CPM_VALUE)
