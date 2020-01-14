import decimal
from decimal import Decimal

import mock
from django.test import TestCase

import core.features.audiences
import core.models
import core.models.settings.ad_group_source_settings.exceptions
from dash import constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import exceptions
from . import model


class ValidationTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(core.models.AdGroup)

    def test_validate_bidding_type_bid_fail(self):
        self.ad_group.bidding_type = constants.BiddingType.CPC
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()

        current_settings.local_cpc_cc = Decimal("1.1")
        new_settings.local_cpc_cc = Decimal("1.2")
        current_settings.local_max_cpm = Decimal("1.1")
        new_settings.local_max_cpm = Decimal("1.2")

        changes = current_settings.get_setting_changes(new_settings)

        with self.assertRaises(exceptions.CannotSetCPM):
            current_settings._validate_max_cpm(changes)

        current_settings.ad_group.bidding_type = constants.BiddingType.CPM
        with self.assertRaises(exceptions.CannotSetCPC):
            current_settings._validate_cpc_cc(changes)

    def test_validate_autopilot_settings_to_full_ap_wo_all_rtb_enabled(self):
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = False

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        with self.assertRaises(exceptions.AutopilotB1SourcesNotEnabled):
            current_settings._validate_autopilot_settings(new_settings)

        new_settings.state = constants.AdGroupSettingsState.INACTIVE
        with self.assertRaises(exceptions.AutopilotB1SourcesNotEnabled):
            current_settings._validate_autopilot_settings(new_settings)

    def test_validate_autopilot_settings_all_rtb_cpc(self):
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        current_settings.b1_sources_group_cpc_cc = Decimal("0.1")
        new_settings.b1_sources_group_cpc_cc = Decimal("0.2")
        current_settings._validate_autopilot_settings(new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.b1_sources_group_cpc_cc = Decimal("0.1")
        new_settings.b1_sources_group_cpc_cc = Decimal("0.2")

        with self.assertRaises(exceptions.CPCAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    def test_validate_autopilot_settings_all_rtb_cpm(self):
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        current_settings.b1_sources_group_cpm = Decimal("1.1")
        new_settings.b1_sources_group_cpm = Decimal("1.2")
        current_settings._validate_autopilot_settings(new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.b1_sources_group_cpm = Decimal("1.1")
        new_settings.b1_sources_group_cpm = Decimal("1.2")

        with self.assertRaises(exceptions.CPMAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    def test_validate_autopilot_settings_all_rtb_cpc_multicurrency(self):
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            currency=constants.Currency.AUD, date=dates_helper.local_today(), exchange_rate=decimal.Decimal("1.38")
        )
        self.ad_group.campaign.account.currency = constants.Currency.AUD
        self.ad_group.settings.update(None, local_cpc_cc=decimal.Decimal("2.00"))

        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        self.ad_group.settings.update(None, local_b1_sources_group_cpc_cc=decimal.Decimal("2.00"))

        with self.assertRaises(core.models.settings.ad_group_source_settings.exceptions.MaximalCPCTooHigh):
            self.ad_group.settings.update(None, local_b1_sources_group_cpc_cc=decimal.Decimal("2.01"))

    def test_validate_autopilot_settings_all_rtb_cpm_multicurrency(self):
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            currency=constants.Currency.AUD, date=dates_helper.local_today(), exchange_rate=decimal.Decimal("1.38")
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.campaign.account.currency = constants.Currency.AUD
        self.ad_group.settings.update(None, local_max_cpm=decimal.Decimal("2.00"))

        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        self.ad_group.settings.update(None, local_b1_sources_group_cpm=decimal.Decimal("2.00"))

        with self.assertRaises(core.models.settings.ad_group_source_settings.exceptions.MaximalCPMTooHigh):
            self.ad_group.settings.update(None, local_b1_sources_group_cpm=decimal.Decimal("2.01"))

    def test_validate_autopilot_settings_all_rtb_daily_budget_multicurrency(self):
        exchange_rate = decimal.Decimal("2.00")
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            currency=constants.Currency.AUD, date=dates_helper.local_today(), exchange_rate=exchange_rate
        )
        self.ad_group.campaign.account.currency = constants.Currency.AUD

        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        max_daily_budget = core.models.all_rtb.AllRTBSourceType.max_daily_budget
        self.ad_group.settings.update(None, local_b1_sources_group_daily_budget=max_daily_budget * exchange_rate)

        with self.assertRaises(core.models.settings.ad_group_source_settings.exceptions.MaximalDailyBudgetTooHigh):
            self.ad_group.settings.update(
                None, local_b1_sources_group_daily_budget=max_daily_budget * exchange_rate + Decimal("2.00")
            )

    def test_validate_all_rtb_bidding_type_bid_fail(self):
        self.ad_group.bidding_type = constants.BiddingType.CPC
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()

        current_settings.local_b1_sources_group_cpc_cc = Decimal("1.1")
        new_settings.local_b1_sources_group_cpc_cc = Decimal("1.2")
        current_settings.local_b1_sources_group_cpm = Decimal("1.1")
        new_settings.local_b1_sources_group_cpm = Decimal("1.2")

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        with self.assertRaises(exceptions.CannotSetB1SourcesCPM):
            current_settings._validate_b1_sources_group_cpm(new_settings)

        self.ad_group.bidding_type = constants.BiddingType.CPM
        with self.assertRaises(exceptions.CannotSetB1SourcesCPC):
            current_settings._validate_b1_sources_group_cpc_cc(new_settings)

    def test_validate_autopilot_settings_all_rtb_daily_budget(self):
        current_settings = self.ad_group.settings
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        current_settings.b1_sources_group_daily_budget = Decimal("100.0")
        new_settings.b1_sources_group_daily_budget = Decimal("200.0")
        current_settings._validate_autopilot_settings(new_settings)  # no exception

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        with self.assertRaises(exceptions.DailyBudgetAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_autopilot_daily_budget(self, mock_get_min_budget):
        current_settings = self.ad_group.settings
        current_settings.autopilot_daily_budget = Decimal(50)
        new_settings = current_settings.copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        mock_get_min_budget.return_value = 0
        new_settings.b1_sources_group_enabled = True
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_daily_budget = Decimal(100)
        current_settings._validate_autopilot_settings(new_settings)
        mock_get_min_budget.assert_called_with(self.ad_group, new_settings)

        mock_get_min_budget.return_value = 1000000
        with self.assertRaises(exceptions.AutopilotDailyBudgetTooLow):
            current_settings._validate_autopilot_settings(new_settings)

        # already too low on old settings and not changed
        mock_get_min_budget.return_value = 1000000
        current_settings.autopilot_daily_budget = Decimal(50)
        new_settings.autopilot_daily_budget = Decimal(50)
        current_settings._validate_autopilot_settings(new_settings)

    def test_validate_all_rtb_state_adgroup_inactive(self):
        settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.INACTIVE

        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_enabled = True
        settings._validate_all_rtb_state(new_settings)

        settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True
        settings._validate_all_rtb_state(new_settings)

        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        settings._validate_all_rtb_state(new_settings)

    def test_validate_all_rtb_state(self):
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = False
        with self.assertRaises(exceptions.AdGroupNotPaused):
            current_settings._validate_all_rtb_state(new_settings)

        current_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_enabled = True
        with self.assertRaises(exceptions.AdGroupNotPaused):
            current_settings._validate_all_rtb_state(new_settings)

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True
        current_settings._validate_all_rtb_state(new_settings)

    def test_validate_audience_targeting(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(request, "test", pixel, 1, 1, [])

        new_settings = model.AdGroupSettings()

        new_settings.audience_targeting = [audience.id + 1]
        with self.assertRaises(exceptions.AudienceTargetingInvalid):
            ad_group.settings._validate_custom_audiences(new_settings)

        new_settings.audience_targeting = [audience.id]
        ad_group.settings._validate_custom_audiences(new_settings)

    def test_validate_exclusion_audience_targeting(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(request, "test", pixel, 1, 1, [])

        new_settings = model.AdGroupSettings()

        new_settings.exclusion_audience_targeting = [audience.id + 1]
        with self.assertRaises(exceptions.ExclusionAudienceTargetingInvalid):
            ad_group.settings._validate_custom_audiences(new_settings)

        new_settings.exclusion_audience_targeting = [audience.id]
        ad_group.settings._validate_custom_audiences(new_settings)
