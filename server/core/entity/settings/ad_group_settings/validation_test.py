import mock
from decimal import Decimal

from django.test import TestCase
from utils.magic_mixer import magic_mixer

import core.entity
from dash import constants
from utils import exc

from . import validation
from . import model


class ValidationTest(TestCase):

    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    @mock.patch('automation.autopilot.get_adgroup_minimum_daily_budget', autospec=True)
    def test_validate_autopilot_settings_to_full_ap_wo_all_rtb_enabled(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = False

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)

        new_settings.state = constants.AdGroupSettingsState.INACTIVE
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)

    @mock.patch('automation.autopilot.get_adgroup_minimum_daily_budget', autospec=True)
    def test_validate_autopilot_settings_all_rtb_cpc(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        current_settings.b1_sources_group_cpc_cc = '0.1'
        new_settings.b1_sources_group_cpc_cc = '0.2'
        validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)  # no exception
        mock_get_min_budget.assert_called_with(None, new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.b1_sources_group_cpc_cc = '0.1'
        new_settings.b1_sources_group_cpc_cc = '0.2'

        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)

    @mock.patch('automation.autopilot.get_adgroup_minimum_daily_budget', autospec=True)
    def test_validate_autopilot_settings_all_rtb_daily_budget(self, mock_get_min_budget):
        mock_get_min_budget.return_value = 0
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE

        current_settings.b1_sources_group_cpc_cc = '100.0'
        new_settings.b1_sources_group_cpc_cc = '200.0'
        validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)  # no exception
        mock_get_min_budget.assert_called_with(None, new_settings)

        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)

    @mock.patch('automation.autopilot.get_adgroup_minimum_daily_budget', autospec=True)
    def test_validate_autopilot_settings_autopilot_daily_budget(self, mock_get_min_budget):
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        mock_get_min_budget.return_value = 0
        new_settings.b1_sources_group_enabled = True
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_daily_budget = 100
        validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)  # no exception
        mock_get_min_budget.assert_called_with(None, new_settings)

        mock_get_min_budget.return_value = 1000000
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_settings(self.request, None, current_settings, new_settings)

    def test_validate_all_rtb_state_adgroup_inactive(self):
        settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.INACTIVE

        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_enabled = True
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, settings, new_settings)

        settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, settings, new_settings)

        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, settings, new_settings)

    def test_validate_all_rtb_state(self):
        current_settings = model.AdGroupSettings()
        new_settings = model.AdGroupSettings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = False
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, current_settings, new_settings)

        current_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_enabled = True
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, current_settings, new_settings)

        current_settings.b1_sources_group_enabled = True
        new_settings.b1_sources_group_enabled = True
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_state(self.request, current_settings, new_settings)

    @mock.patch('automation.campaign_stop.get_max_settable_b1_sources_group_budget')
    def test_validate_all_rtb_campaign_stop_daily_budget(self, mock_get_max_settable_budget):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_daily_budget = Decimal('100')

        mock_get_max_settable_budget.return_value = None
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_campaign_stop(
            ad_group,
            current_settings,
            new_settings,
            ad_group.campaign.get_current_settings()
        )  # no exception should be raised

        mock_get_max_settable_budget.return_value = Decimal('100')
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_campaign_stop(
            ad_group,
            current_settings,
            new_settings,
            ad_group.campaign.get_current_settings()
        )  # no exception should be raised

        mock_get_max_settable_budget.return_value = Decimal('99')
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_all_rtb_campaign_stop(
                ad_group,
                current_settings,
                new_settings,
                ad_group.campaign.get_current_settings()
            )

    @mock.patch('automation.campaign_stop.can_enable_b1_sources_group')
    def test_validate_all_rtb_campaign_stop_state(self, mock_can_enable):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings().copy_settings()
        current_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.INACTIVE
        current_settings.save(None)

        new_settings = current_settings.copy_settings()
        new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

        mock_can_enable.return_value = True
        validation.AdGroupSettingsValidatorMixin._validate_all_rtb_campaign_stop(
            ad_group,
            current_settings,
            new_settings,
            ad_group.campaign.get_current_settings()
        )  # no exception should be raised

        mock_can_enable.return_value = False
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_all_rtb_campaign_stop(
                ad_group,
                current_settings,
                new_settings,
                ad_group.campaign.get_current_settings()
            )

    @mock.patch('automation.campaign_stop.get_max_settable_autopilot_budget')
    def test_validate_autopilot_campaign(self, mock_get_max_settable_budget, autospec=True):
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        current_settings = ad_group.get_current_settings()

        new_settings = current_settings.copy_settings()
        current_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET

        current_settings.autopilot_daily_budget = Decimal('200')
        new_settings.autopilot_daily_budget = Decimal('400')

        mock_get_max_settable_budget.return_value = None
        validation.AdGroupSettingsValidatorMixin._validate_autopilot_campaign_stop(
            ad_group,
            current_settings,
            new_settings,
            ad_group.campaign.get_current_settings()
        )  # no exception should be raised

        mock_get_max_settable_budget.return_value = Decimal('400')
        validation.AdGroupSettingsValidatorMixin._validate_autopilot_campaign_stop(
            ad_group,
            current_settings,
            new_settings,
            ad_group.campaign.get_current_settings()
        )  # no exception should be raised

        mock_get_max_settable_budget.return_value = Decimal('399')
        with self.assertRaises(exc.ValidationError):
            validation.AdGroupSettingsValidatorMixin._validate_autopilot_campaign_stop(
                ad_group,
                current_settings,
                new_settings,
                ad_group.campaign.get_current_settings()
            )
