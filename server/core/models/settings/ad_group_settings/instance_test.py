from decimal import Decimal

import mock
from django.test import TestCase
from mock import patch

import core.features.publisher_groups
import core.models
import dash.constants
import utils.exc
from core.features import bid_modifiers
from core.features.multicurrency import CurrencyExchangeRate
from dash import constants
from utils.magic_mixer import magic_mixer

from . import model


class InstanceTest(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=False)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=self.agency)

    def test_update(self):
        initial = {"cpc": Decimal("0.4"), "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE}
        self.ad_group.settings.update(None, **initial)
        user_changes = {"cpc": Decimal("0.5")}
        applied_changes = self.ad_group.settings.update(None, **user_changes)
        expected_changes = {
            "cpc": Decimal("0.5"),
            "local_cpc": Decimal("0.5"),
            "cpc_cc": Decimal("0.5"),
            "local_cpc_cc": Decimal("0.5"),
        }
        self.assertEqual(applied_changes, expected_changes)

    def test_b1_sources_group_adjustments_sets_default_cpc_and_daily_budget(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.daily_budget = Decimal("100.0")
        new_settings.cpc = Decimal("0.5")
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
                "b1_sources_group_cpc_cc": Decimal("0.5"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_b1_sources_group_cpc_cc": Decimal("0.5"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
            },
        )

    def test_b1_sources_group_adjustments_sets_default_cpm_and_daily_budget(self):
        request = magic_mixer.blend_request_user()
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.daily_budget = Decimal("100.0")
        new_settings.cpm = Decimal("0.8")
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
                "b1_sources_group_cpm": Decimal("0.8"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_b1_sources_group_cpm": Decimal("0.8"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
            },
        )

    def test_b1_sources_group_adjustments_sets_new_cpc_daily_budget(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.cpc = Decimal("0.5")
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
                "daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpc_cc": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
                "local_daily_budget": Decimal("10.0"),
            },
        )

    def test_b1_sources_group_adjustments_sets_new_cpm_daily_budget(self):
        request = magic_mixer.blend_request_user()
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.cpm = Decimal("0.8")
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
                "daily_budget": Decimal("10.0"),
                "local_b1_sources_group_cpm": Decimal("0.211"),
                "local_b1_sources_group_daily_budget": Decimal("10.0"),
                "local_daily_budget": Decimal("10.0"),
            },
        )

    def test_b1_sources_group_adjustments_obeys_new_adgroup_cpc(self):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpc_cc = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.daily_budget = Decimal("100.0")
        new_settings.cpc = Decimal("0.5")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.cpc = Decimal("0.05")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes, {"b1_sources_group_enabled": True, "cpc": Decimal("0.05"), "local_cpc": Decimal("0.05")}
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpc_cc": Decimal("0.05"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "cpc": Decimal("0.05"),
                "local_b1_sources_group_cpc_cc": Decimal("0.05"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_cpc": Decimal("0.05"),
            },
        )

    def test_b1_sources_group_adjustments_obeys_new_adgroup_cpm(self):
        request = magic_mixer.blend_request_user()
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(request)
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_cpm = Decimal("0.111")
        new_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.daily_budget = Decimal("100.0")
        new_settings.cpm = Decimal("0.8")
        new_settings.save(None)

        # turn on rtb as one
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.cpm = Decimal("0.05")
        new_settings.save(None)

        changes = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes, {"b1_sources_group_enabled": True, "cpm": Decimal("0.05"), "local_cpm": Decimal("0.05")}
        )

        current_settings._handle_b1_sources_group_adjustments(new_settings)
        changes_new = current_settings.get_setting_changes(new_settings)
        self.assertDictEqual(
            changes_new,
            {
                "b1_sources_group_enabled": True,
                "b1_sources_group_cpm": Decimal("0.05"),
                "b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "cpm": Decimal("0.05"),
                "local_b1_sources_group_cpm": Decimal("0.05"),
                "local_b1_sources_group_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
                "local_cpm": Decimal("0.05"),
                "local_daily_budget": core.models.AllRTBSource.default_daily_budget_cc,
            },
        )

    def test_sync_legacy_fields(self):
        def _reset_test_settings(b1_sources_group_enabled=True):
            current_settings = self.ad_group.get_current_settings()
            new_settings = current_settings.copy_settings()

            new_settings.b1_sources_group_enabled = b1_sources_group_enabled
            new_settings.daily_budget = Decimal("100.0")
            new_settings.b1_sources_group_daily_budget = Decimal("100.0")
            new_settings.autopilot_daily_budget = Decimal("100.0")
            new_settings.cpc = Decimal("3.0")
            new_settings.cpm = Decimal("3.0")
            new_settings.b1_sources_group_cpc_cc = Decimal("3.0")
            new_settings.b1_sources_group_cpm = Decimal("3.0")
            new_settings.max_autopilot_bid = Decimal("3.0")
            new_settings.save(None)

            return new_settings

        self.ad_group.campaign.account.agency.uses_realtime_autopilot = True
        budget_fields_values = {
            "daily_budget": Decimal("101.0"),
            "b1_sources_group_daily_budget": Decimal("102.0"),
            "autopilot_daily_budget": Decimal("103.0"),
        }
        cpc_fields_values = {
            "cpc": Decimal("7.0"),
            "b1_sources_group_cpc_cc": Decimal("8.0"),
            "max_autopilot_bid": Decimal("9.0"),
        }
        cpm_fields_values = {
            "cpm": Decimal("9.0"),
            "b1_sources_group_cpm": Decimal("7.0"),
            "max_autopilot_bid": Decimal("8.0"),
        }

        # Budget (sources group)
        _reset_test_settings()

        for field, value in budget_fields_values.items():
            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.daily_budget)
            self.assertEqual(value, self.ad_group.settings.b1_sources_group_daily_budget)
            self.assertEqual(value, self.ad_group.settings.autopilot_daily_budget)

        # Budget (sources separately)
        _reset_test_settings(b1_sources_group_enabled=False)

        for field, value in budget_fields_values.items():
            old_b1_budget = self.ad_group.settings.b1_sources_group_daily_budget

            if field == "b1_sources_group_daily_budget":
                continue

            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.daily_budget)
            self.assertEqual(old_b1_budget, self.ad_group.settings.b1_sources_group_daily_budget)
            self.assertEqual(value, self.ad_group.settings.autopilot_daily_budget)

        # CPC (sources group)
        _reset_test_settings()

        for field, value in cpc_fields_values.items():
            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.cpc)
            self.assertEqual(value, self.ad_group.settings.b1_sources_group_cpc_cc)
            self.assertEqual(value, self.ad_group.settings.max_autopilot_bid)

        # CPC (sources separately)
        _reset_test_settings(b1_sources_group_enabled=False)

        for field, value in cpc_fields_values.items():
            old_b1_cpc = self.ad_group.settings.b1_sources_group_cpc_cc

            if field == "b1_sources_group_cpc_cc":
                continue

            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.cpc)
            self.assertEqual(old_b1_cpc, self.ad_group.settings.b1_sources_group_cpc_cc)
            self.assertEqual(value, self.ad_group.settings.max_autopilot_bid)

        # CPM (sources group)
        self.ad_group.bidding_type = constants.BiddingType.CPM
        _reset_test_settings()

        for field, value in cpm_fields_values.items():
            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.cpm)
            self.assertEqual(value, self.ad_group.settings.b1_sources_group_cpm)
            self.assertEqual(value, self.ad_group.settings.max_autopilot_bid)

        # CPM (sources separately)
        _reset_test_settings(b1_sources_group_enabled=False)

        for field, value in cpm_fields_values.items():
            old_b1_cpm = self.ad_group.settings.b1_sources_group_cpm

            if field == "b1_sources_group_cpm":
                continue

            self.ad_group.settings.update(None, **{field: value})

            self.assertEqual(value, self.ad_group.settings.cpm)
            self.assertEqual(old_b1_cpm, self.ad_group.settings.b1_sources_group_cpm)
            self.assertEqual(value, self.ad_group.settings.max_autopilot_bid)

    @patch("utils.redirector_helper.insert_adgroup")
    def test_get_external_cpc(self, mock_insert_adgroup):
        self.ad_group.settings.update(
            None, cpc=Decimal("1.0"), autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        self.assertEqual(
            Decimal("0.648"), self.ad_group.settings.get_external_bid(Decimal("0.1"), Decimal("0.2"), Decimal("0.1"))
        )

    @patch("utils.redirector_helper.insert_adgroup")
    def test_get_external_cpm(self, mock_insert_adgroup):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.settings.update(
            None, cpm=Decimal("10.0"), autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        self.assertEqual(
            Decimal("6.48"), self.ad_group.settings.get_external_bid(Decimal("0.1"), Decimal("0.2"), Decimal("0.1"))
        )

    @patch("utils.redirector_helper.insert_adgroup")
    def test_get_external_b1_sources_group_daily_budget(self, mock_insert_adgroup):
        self.ad_group.settings.update(
            None,
            b1_sources_group_daily_budget=Decimal("500"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        self.assertEqual(
            Decimal("324"),
            self.ad_group.settings.get_external_b1_sources_group_daily_budget(
                Decimal("0.1"), Decimal("0.2"), Decimal("0.1")
            ),
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

    @patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_recalculate_autopilot_enable(self, mock_autopilot):
        self.agency.uses_realtime_autopilot = True
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        with self.assertRaises(utils.exc.ForbiddenError):
            self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)

        self.ad_group.campaign.settings.update_unsafe(None, autopilot=False)
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        mock_autopilot.assert_not_called()

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_enable_legacy(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_recalculate_autopilot_change_budget(self, mock_autopilot):
        self.agency.uses_realtime_autopilot = True
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        with self.assertRaises(utils.exc.ForbiddenError):
            self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"))

        self.ad_group.campaign.settings.update_unsafe(None, autopilot=False)
        self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"))
        mock_autopilot.assert_not_called()

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_change_budget_legacy(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"))
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_change_allrtb_state(self, mock_autopilot):
        self.ad_group.settings.update(None, b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_state(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update_unsafe(None, state=constants.AdGroupSettingsState.ACTIVE)
        self.ad_group.settings.update(None, state=constants.AdGroupSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_campaign_change_allrtb_state(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group.settings.update(None, b1_sources_group_state=constants.AdGroupSourceSettingsState.INACTIVE)
        mock_autopilot.assert_called_once_with(self.ad_group)

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_recalculate_autopilot_skip_automation(self, mock_autopilot):
        self.ad_group.settings.update(None, autopilot_daily_budget=Decimal("10.0"), skip_automation=True)
        mock_autopilot.assert_not_called()

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_cpc_change_changes_source_cpcs(self, mock_get_exchange_rate, mock_autopilot):
        # setup
        ad_group = magic_mixer.blend(core.models.AdGroup, b1_sources_group=True, b1_sources_group_cpc_cc=Decimal("0.1"))
        ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        ad_group_sources = magic_mixer.cycle(3).blend(core.models.AdGroupSource, ad_group=ad_group)
        magic_mixer.cycle(3).blend(
            bid_modifiers.models.BidModifier,
            ad_group=ad_group,
            type=bid_modifiers.constants.BidModifierType.SOURCE,
            target=(str(e.source.id) for e in ad_group_sources),
            modifier=1.0,
        )
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, cpc=Decimal("0.20"))
        for source in ad_group.adgroupsource_set.all():
            source.settings.update(cpc_cc=Decimal("0.2"), state=1)

        # updating usd value
        ad_group.settings.update(None, cpc=Decimal("0.50"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.5"))
            self.assertEqual(source.settings.local_cpc_cc, Decimal("1.0"))

        # updating local value
        ad_group.settings.update(None, local_cpc=Decimal("1.20"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.6"))
            self.assertEqual(source.settings.local_cpc_cc, Decimal("1.2"))

        # updating just exchange rate shouldn't reset source bid modifiers
        mock_get_exchange_rate.return_value = Decimal("3.0")
        self.assertEqual(ad_group.settings.cpc, Decimal("0.6"))
        # call again with same local cpc, but usd will change due to exchange rate change
        ad_group.settings.update(None, local_cpc=Decimal("1.20"))
        self.assertEqual(ad_group.settings.cpc, Decimal("0.4"))
        # assert source bids haven't changed
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpc_cc, Decimal("0.4"))

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_max_cpm_change_changes_source_cpms(self, mock_get_exchange_rate, mock_autopilot):
        # setup
        ad_group = magic_mixer.blend(
            core.models.AdGroup,
            b1_sources_group=True,
            b1_sources_group_max_cpm=Decimal("0.1"),
            bidding_type=constants.BiddingType.CPM,
        )
        ad_group.settings.update(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        ad_group_sources = magic_mixer.cycle(3).blend(core.models.AdGroupSource, ad_group=ad_group)
        magic_mixer.cycle(3).blend(
            bid_modifiers.models.BidModifier,
            ad_group=ad_group,
            type=bid_modifiers.constants.BidModifierType.SOURCE,
            target=(str(e.source.id) for e in ad_group_sources),
            modifier=1.0,
        )
        mock_get_exchange_rate.return_value = Decimal("2.0")
        ad_group.settings.update(None, cpm=Decimal("0.20"))
        for source in ad_group.adgroupsource_set.all():
            source.settings.update(cpm=Decimal("0.2"), state=1)

        # updating usd value
        ad_group.settings.update(None, cpm=Decimal("0.50"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpm, Decimal("0.5"))
            self.assertEqual(source.settings.local_cpm, Decimal("1.0"))

        # updating local value
        ad_group.settings.update(None, local_cpm=Decimal("1.20"))
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpm, Decimal("0.6"))
            self.assertEqual(source.settings.local_cpm, Decimal("1.2"))

        # updating just exchange rate shouldn't reset source bid modifiers
        mock_get_exchange_rate.return_value = Decimal("3.0")
        self.assertEqual(ad_group.settings.cpm, Decimal("0.6"))
        # call again with same local cpc, but usd will change due to exchange rate change
        ad_group.settings.update(None, local_cpm=Decimal("1.20"))
        self.assertEqual(ad_group.settings.cpm, Decimal("0.4"))
        # assert source bids haven't changed
        for source in ad_group.adgroupsource_set.all():
            self.assertEqual(source.settings.cpm, Decimal("0.4"))

    @patch("utils.redirector_helper.insert_adgroup")
    def test_redirector_update(self, mock_insert_adgroup):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update(None, name="test")
        mock_insert_adgroup.assert_not_called()

        ad_group.settings.update(None, tracking_code="123")
        mock_insert_adgroup.assert_called_once_with(ad_group)

    @patch("utils.k1_helper.update_ad_group")
    def test_k1_priority(self, mock_update_ad_group):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)

        ad_group.settings.update(None, name="test")
        mock_update_ad_group.assert_called_once_with(ad_group, msg=mock.ANY, priority=False)
        mock_update_ad_group.reset_mock()

        ad_group.settings.update(None, b1_sources_group_cpc_cc=Decimal("0.6"))
        mock_update_ad_group.assert_called_once_with(ad_group, msg=mock.ANY, priority=False)
        mock_update_ad_group.reset_mock()

        ad_group.settings.update_unsafe(None, state=constants.AdGroupSettingsState.ACTIVE)
        ad_group.settings.update(None, b1_sources_group_cpc_cc=Decimal("0.5"))
        mock_update_ad_group.assert_called_once_with(ad_group, msg=mock.ANY, priority=True)

    @patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_change_forbidden_fields(self, mock_autopilot):
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        with self.assertRaises(utils.exc.ForbiddenError):
            self.ad_group.settings.update(None, autopilot_state=False, autopilot_daily_budget=Decimal("10.0"))


@patch("automation.autopilot_legacy.recalculate_budgets_ad_group", mock.MagicMock())
class DefaultBidsTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.ad_group.settings.update_unsafe(
            self.request, cpc="8.0000", cpm="8.0000", autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        self.ad_group.settings.refresh_from_db()

    def test_set_empty_cpc(self):
        self.ad_group.settings.update(self.request, cpc=None)
        self.assertEqual(core.models.settings.AdGroupSettings.DEFAULT_CPC_VALUE, self.ad_group.settings.cpc)

    def test_set_empty_cpm(self):
        self.ad_group.update(self.request, bidding_type=constants.BiddingType.CPM)
        self.ad_group.settings.update(self.request, cpm=None)
        self.assertEqual(core.models.settings.AdGroupSettings.DEFAULT_CPM_VALUE, self.ad_group.settings.cpm)


class MulticurrencyTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_usd(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal("2.0")
        self.ad_group.settings.update(None, cpc=Decimal("0.50"))
        self.assertEqual(self.ad_group.settings.local_cpc, Decimal("1.00"))
        self.assertEqual(self.ad_group.settings.cpc, Decimal("0.50"))

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_local(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal("2.0")
        self.ad_group.settings.update(None, local_cpc=Decimal("0.50"))
        self.assertEqual(self.ad_group.settings.local_cpc, Decimal("0.50"))
        self.assertEqual(self.ad_group.settings.cpc, Decimal("0.25"))

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
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        ad_group.settings.update(None, archived=True)
        ad_group.settings.update(None, archived=False)
        self.assertFalse(ad_group.is_archived())
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)

    @patch.object(core.models.AdGroup, "is_ad_group_active", return_value=True)
    def test_archive_active(self, mock_adgroup_is_active):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, state=constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(constants.AdGroupSettingsState.ACTIVE, ad_group.settings.state)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        ad_group.settings.update(None, archived=True)
        ad_group.refresh_from_db()
        self.assertEqual(constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)

    @patch.object(core.models.Campaign, "is_archived", return_value=True)
    def test_cant_restore_campaign_fail(self, mock_campaign_is_archived):
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(None, archived=True)
        ad_group.archived = True
        ad_group.save(None)
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, archived=False)
        ad_group.refresh_from_db()
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        ad_group.settings.update(None, archived=True)

    @patch.object(core.models.Campaign, "is_archived", return_value=True)
    def test_update_campaign_archived_fail(self, mock_campaign_is_archived):
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, ad_group_name="new name")

    def test_update_archived_ad_group(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.archive(None)
        ad_group.refresh_from_db()
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, ad_group_name="new name")
        ad_group.settings.update(None, archived=True)
        ad_group.settings.update(None, archived=False)
        ad_group.refresh_from_db()
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_restore_multicurrency_ad_group_settings(self, mock_get_exchange_rate):
        CurrencyExchangeRate.objects.create(
            date="2018-01-01", currency=dash.constants.Currency.EUR, exchange_rate="0.8"
        )
        request = magic_mixer.blend_request_user(is_superuser=True)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account_currency=dash.constants.Currency.EUR)
        ad_group.settings.update_unsafe(
            request,
            local_cpc="0.8",
            local_autopilot_daily_budget=100,
            local_b1_sources_group_daily_budget=72,
            local_b1_sources_group_cpc_cc="0.35",
            local_cpm="1.3",
        )
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group)
        ad_group_source.settings.update_unsafe(request, local_cpc_cc="0.62", local_daily_budget_cc=28)

        self.assertEqual(Decimal("28"), ad_group_source.settings.local_daily_budget_cc)
        self.assertEqual(Decimal("100"), ad_group.settings.local_autopilot_daily_budget)
        self.assertEqual(Decimal("72"), ad_group.settings.local_b1_sources_group_daily_budget)
        self.assertEqual("0.35", ad_group.settings.local_b1_sources_group_cpc_cc)
        self.assertEqual("1.3", ad_group.settings.local_cpm)
        self.assertEqual("0.8", ad_group.settings.local_cpc)
        self.assertEqual(Decimal("0.45"), ad_group.settings.cpc)
        self.assertEqual("0.62", ad_group_source.settings.local_cpc_cc)

        ad_group.settings.update_unsafe(None, archived=True)
        mock_get_exchange_rate.return_value = Decimal("3.0")
        ad_group.restore(None)
        ad_group.refresh_from_db()
        ad_group_source.refresh_from_db()
        self.assertEqual(Decimal("0.2667"), ad_group.settings.cpc)
        self.assertEqual(Decimal("33.3333"), ad_group.settings.autopilot_daily_budget)
        self.assertEqual(Decimal("24.0000"), ad_group.settings.b1_sources_group_daily_budget)
        self.assertEqual(Decimal("0.1167"), ad_group.settings.b1_sources_group_cpc_cc)
        self.assertEqual(Decimal("0.4333"), ad_group.settings.cpm)
        self.assertEqual(Decimal("28.0000"), ad_group_source.settings.local_daily_budget_cc)
        self.assertEqual(Decimal("0.8001"), ad_group_source.settings.local_cpc_cc)

    def test_update_archived_ad_group_publisher_groups(self):
        account = magic_mixer.blend(core.models.Account)
        publisher_group_1 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        publisher_group_2 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        publisher_group_3 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, name="test publisher group", account=account
        )
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(
            None,
            whitelist_publisher_groups=[publisher_group_1.id, publisher_group_2.id],
            blacklist_publisher_groups=[publisher_group_1.id, publisher_group_2.id],
        )
        ad_group.archive(None)
        ad_group.refresh_from_db()
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        ad_group.settings.update(None, whitelist_publisher_groups=[publisher_group_2.id])
        ad_group.settings.update(None, blacklist_publisher_groups=[publisher_group_2.id])
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, whitelist_publisher_groups=[publisher_group_3.id])
        with self.assertRaises(utils.exc.ForbiddenError):
            ad_group.settings.update(None, blacklist_publisher_groups=[publisher_group_3.id])
        ad_group.settings.update(None, whitelist_publisher_groups=[])
        ad_group.settings.update(None, blacklist_publisher_groups=[])
