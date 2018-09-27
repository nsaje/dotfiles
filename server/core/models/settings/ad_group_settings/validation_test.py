import mock
from decimal import Decimal

from django.test import TestCase
from utils.magic_mixer import magic_mixer

import core.models
from dash import constants

from . import model
from . import exceptions


class ValidationTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(core.models.AdGroup)

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_to_full_ap_wo_all_rtb_enabled(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
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

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_all_rtb_cpc(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
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
        mock_get_min_budget.assert_called_with(self.ad_group, new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.b1_sources_group_cpc_cc = Decimal("0.1")
        new_settings.b1_sources_group_cpc_cc = Decimal("0.2")

        with self.assertRaises(exceptions.CPCAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_all_rtb_cpm(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
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
        mock_get_min_budget.assert_called_with(self.ad_group, new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.b1_sources_group_cpm = Decimal("1.1")
        new_settings.b1_sources_group_cpm = Decimal("1.2")

        with self.assertRaises(exceptions.CPMAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_all_rtb_daily_budget(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
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
        mock_get_min_budget.assert_called_with(self.ad_group, new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        with self.assertRaises(exceptions.DailyBudgetAutopilotNotDisabled):
            current_settings._validate_autopilot_settings(new_settings)

    @mock.patch("automation.autopilot.get_adgroup_minimum_daily_budget", autospec=True)
    def test_validate_autopilot_settings_autopilot_daily_budget(self, mock_get_min_budget):
        current_settings = self.ad_group.settings
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
