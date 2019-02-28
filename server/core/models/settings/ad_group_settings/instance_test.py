from decimal import Decimal

from django.test import TestCase
from mock import patch

import core.models
import utils.exc
from dash import constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import model


class InstanceTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)

    def test_b1_sources_group_adjustments_sets_default_cpc_and_daily_budget(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.cpc_cc = Decimal("0.5")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(changes, {"b1_sources_group_enabled": True})

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)

        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpc_cc": min(new_settings.cpc_cc, core.models.AllRTBSource.default_cpc_cc),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_b1_sources_group_cpc_cc": min(new_settings.cpc_cc, core.models.AllRTBSource.default_cpc_cc),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
            },
        )

    def test_b1_sources_group_adjustments_sets_default_cpm_and_daily_budget(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.max_cpm = Decimal("0.8")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(changes, {"b1_sources_group_enabled": True})

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)

        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpm": min(new_settings.max_cpm, core.models.AllRTBSource.default_cpm),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_b1_sources_group_cpm": min(new_settings.max_cpm, core.models.AllRTBSource.default_cpm),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
            },
        )

    def test_b1_sources_group_adjustments_sets_new_cpc_daily_budget(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.cpc_cc = Decimal("0.5")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_daily_budget = Decimal("10.0")
        new_settings.b1_sources_group_cpc_cc = Decimal("0.211")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpc_cc": Decimal("0.211"),
                "b1_sources_group_daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpc_cc": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
            },
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpc_cc": Decimal("0.211"),
                "b1_sources_group_daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpc_cc": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
            },
        )

    def test_b1_sources_group_adjustments_sets_new_cpm_daily_budget(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.max_cpm = Decimal("0.8")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_daily_budget = Decimal("10.0")
        new_settings.b1_sources_group_cpm = Decimal("0.211")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpm": Decimal("0.211"),
                "b1_sources_group_daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpm": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
            },
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpm": Decimal("0.211"),
                "b1_sources_group_daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpm": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
            },
        )

    def test_b1_sources_group_adjustments_obeys_new_adgroup_max_cpc(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.cpc_cc = Decimal("0.5")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.cpc_cc = Decimal("0.05")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes, {"b1_sources_group_enabled": True, "cpc_cc": Decimal("0.05"), "local_cpc_cc": Decimal("0.05")}
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpc_cc": Decimal("0.05"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "cpc_cc": Decimal("0.05"),
                "local_b1_sources_group_cpc_cc": Decimal("0.05"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_cpc_cc": Decimal("0.05"),
            },
        )

    def test_b1_sources_group_adjustments_obeys_new_adgroup_max_cpm(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.max_cpm = Decimal("0.8")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.max_cpm = Decimal("0.05")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes, {"b1_sources_group_enabled": True, "max_cpm": Decimal("0.05"), "local_max_cpm": Decimal("0.05")}
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpm": Decimal("0.05"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "max_cpm": Decimal("0.05"),
                "local_b1_sources_group_cpm": Decimal("0.05"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_max_cpm": Decimal("0.05"),
            },
        )

    @patch("utils.redirector_helper.insert_adgroup")
    def test_get_external_b1_sources_group_daily_budget(self, mock_insert_adgroup):
        account = magic_mixer.blend(core.models.Account, uses_bcm_v2=False)
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])

        self.ad_group.settings.update(
            request,
            b1_sources_group_daily_budget=Decimal("500"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        self.assertEqual(
            Decimal("500"),
            self.ad_group.settings.get_external_b1_sources_group_daily_budget(account, Decimal("0.2"), Decimal("0.1")),
        )

        account.uses_bcm_v2 = True
        self.assertEqual(
            Decimal("360"),
            self.ad_group.settings.get_external_b1_sources_group_daily_budget(account, Decimal("0.2"), Decimal("0.1")),
        )

    @patch("utils.redirector_helper.insert_adgroup")
    def test_update_fields(self, mock_insert_adgroup):
        self.ad_group.settings.update(None, bluekai_targeting=["outbrain:1234"])
        self.assertEqual(["outbrain:1234"], self.ad_group.settings.bluekai_targeting)

        with patch("django.db.models.Model.save") as save_mock:
            self.ad_group.settings.update(None, bluekai_targeting=["outbrain:4321"])
            save_mock.assert_any_call(update_fields=["bluekai_targeting", "created_by", "created_dt", "system_user"])

    @patch("django.db.models.Model.save")
    def test_update_fields_create(self, mock_save):
        model.AdGroupSettings.objects.create_default(self.ad_group, "test-name")
        mock_save.assert_any_call(update_fields=None)

    def test_remove_max_cpc(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, cpc_cc=Decimal("0.5"))
        ad_group.settings.update(None, cpc_cc=None)
        self.assertIsNone(ad_group.settings.cpc_cc)

    def test_remove_max_cpm(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=constants.BiddingType.CPM)
        ad_group.settings.update_unsafe(request, max_cpm=Decimal("0.5"))
        ad_group.settings.update(request, max_cpm=None)
        self.assertIsNone(ad_group.settings.max_cpm)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_enable(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_change_budget(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"))
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_change_allrtb_state(self, mock_autopilot):
        self.ad_group.settings.update(None, b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_state(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update_unsafe(None, state=constants.AdGroupSettingsState.ACTIVE)
        self.ad_group.settings.update(None, state=constants.AdGroupSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_start_date(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update(None, start_date=dates_helper.day_after(self.ad_group.settings.start_date))
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_end_date(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update(None, end_date=dates_helper.utc_today())
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_allrtb_state(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update(None, b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_skip_automation(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"), skip_automation=True)
        mock_autopilot.assert_not_called()

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_max_cpc_change_changes_source_cpcs(self, mock_get_exchange_rate, mock_autopilot):
        # setup
        ad_group = magic_mixer.blend(core.models.AdGroup)
        magic_mixer.cycle(3).blend(core.models.AdGroupSource, ad_group=ad_group)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, cpc_cc=Decimal("0.20"))
        for source in ad_group.adgroupsource_set.all():
            source.settings.update(cpc_cc=Decimal("0.1"), state=1)

        # updating usd value
        ad_group.settings.update(None, cpc_cc=Decimal("0.50"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.5"))
            self.assertEqual(source.settings.local_cpc_cc, Decimal("1.0"))

        # updating local value
        ad_group.settings.update(None, local_cpc_cc=Decimal("1.20"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.6"))
            self.assertEqual(source.settings.local_cpc_cc, Decimal("1.2"))

        # updating just exchange rate shouldn't reset source cpcs
        for source in ad_group.adgroupsource_set.all():
            source.settings.update(cpc_cc=Decimal("0.1"))
        mock_get_exchange_rate.return_value = Decimal("3.0")
        self.assertEqual(ad_group.settings.cpc_cc, Decimal("0.6"))
        ad_group.settings.update(None, local_cpc_cc=Decimal("1.20"))
        self.assertEqual(ad_group.settings.cpc_cc, Decimal("0.4"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.1"))


class MulticurrencyTest(TestCase):
    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_usd(self, mock_get_exchange_rate):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, cpc_cc=Decimal("0.50"))
        self.assertEqual(ad_group.settings.local_cpc_cc, Decimal("1.00"))
        self.assertEqual(ad_group.settings.cpc_cc, Decimal("0.50"))

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_local(self, mock_get_exchange_rate):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, local_cpc_cc=Decimal("0.50"))
        self.assertEqual(ad_group.settings.local_cpc_cc, Decimal("0.50"))
        self.assertEqual(ad_group.settings.cpc_cc, Decimal("0.25"))

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_none(self, mock_get_exchange_rate):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, name="test")
        mock_get_exchange_rate.assert_not_called()


class AdGroupArchiveRestoreTest(TestCase):
    def test_archiving(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update(None, archived=True)
        self.assertTrue(ad_group.is_archived())
        ad_group.settings.update(None, archived=False)
        self.assertFalse(ad_group.is_archived())

    @patch.object(core.models.AdGroup, "is_ad_group_active", return_value=True)
    def test_cant_archive_paused_fail(self, mock_adgroup_is_active):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, archived=True)
        self.assertFalse(ad_group.settings.archived)

    @patch.object(core.models.Campaign, "is_archived", return_value=True)
    def test_cant_restore_campaign_fail(self, mock_campaign_is_archived):
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(None, archived=True)
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, archived=False)
