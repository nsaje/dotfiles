from decimal import Decimal
from mock import patch, MagicMock, ANY

from django import test

from automation import autopilot_helpers
import dash.models
from dash.constants import AdGroupSettingsAutopilotState, AdGroupRunningStatus, AdGroupSettingsState
from reports import refresh


class AutopilotHelpersTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    @patch('dash.models.AdGroup.get_running_status_by_sources_setting')
    @patch('dash.models.AdGroup.get_running_status')
    def test_get_active_ad_groups_on_autopilot(self, mock_running_status, mock_running_status_by_sources):
        mock_running_status.return_value = AdGroupRunningStatus.ACTIVE
        mock_running_status_by_sources.return_value = AdGroupRunningStatus.ACTIVE
        all_ap_adgs, all_ap_adgs_settings = autopilot_helpers.get_active_ad_groups_on_autopilot()
        cpc_ap_adgs, cpc_ap_adgs_settings = autopilot_helpers.get_active_ad_groups_on_autopilot(autopilot_state=3)
        budget_ap_adgs, budget_ap_adgs_settings = autopilot_helpers.get_active_ad_groups_on_autopilot(autopilot_state=1)
        self.assertEqual(len(all_ap_adgs), 3)
        self.assertTrue(adg in all_ap_adgs for adg in cpc_ap_adgs + budget_ap_adgs)
        for adg_settings in all_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state in [
                AdGroupSettingsAutopilotState.ACTIVE_CPC,
                AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET])
        for adg_settings in cpc_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC)
        for adg_settings in budget_ap_adgs_settings:
            self.assertEqual(adg_settings, adg_settings.ad_group.get_current_settings())
            self.assertTrue(adg_settings.autopilot_state == AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
        self.assertFalse(dash.models.AdGroup.objects.get(id=2) in cpc_ap_adgs + budget_ap_adgs + all_ap_adgs)

    def test_update_ad_group_source_values(self):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag_source_settings = ag_source.get_current_settings()
        old_daily_budget = ag_source_settings.daily_budget_cc
        old_cpc = ag_source_settings.cpc_cc
        autopilot_helpers.update_ad_group_source_values(ag_source, {
            'daily_budget_cc': old_daily_budget + Decimal('10'),
            'cpc_cc': old_cpc + Decimal('0.5')})
        new_ag_source_settings = ag_source.get_current_settings()
        self.assertNotEqual(ag_source_settings, new_ag_source_settings)
        self.assertEqual(new_ag_source_settings.daily_budget_cc, old_daily_budget + Decimal('10'))
        self.assertEqual(new_ag_source_settings.cpc_cc, old_cpc + Decimal('0.5'))

    def test_get_autopilot_active_sources_settings(self):
        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 2, 3])
        ad_groups_and_settings = {adg: adg.get_current_settings() for adg in adgroups}
        active_enabled_sources = autopilot_helpers.get_autopilot_active_sources_settings(ad_groups_and_settings)
        for ag_source_setting in active_enabled_sources:
            self.assertTrue(ag_source_setting.state == AdGroupSettingsState.ACTIVE)
            self.assertTrue(ag_source_setting.ad_group_source.ad_group in adgroups)

        source = dash.models.AdGroupSource.objects.get(id=1)
        self.assertTrue(source in [setting.ad_group_source for setting in active_enabled_sources])
        dash.api.set_ad_group_source_settings(
            source,
            {'state': AdGroupSettingsState.INACTIVE},
            None
        )
        self.assertEqual(source.get_current_settings().state, AdGroupSettingsState.INACTIVE)
        self.assertFalse(source in [setting.ad_group_source for setting in
                                    autopilot_helpers.get_autopilot_active_sources_settings(ad_groups_and_settings)])

    @patch('utils.k1_helper.update_ad_group')
    @patch('dash.models.AdGroupSettings.copy_settings')
    @patch('dash.views.helpers.set_ad_group_sources_cpcs')
    def test_update_ad_group_b1_sources_group_values(self, mock_set_ad_group_sources_cpcs,
                                                     mock_copy_settings, mock_k1_update_ad_group):
        ag = dash.models.AdGroup.objects.get(id=1)

        current_ag_settings = MagicMock()
        mock_copy_settings.return_value = current_ag_settings

        changes = {
            'cpc_cc': Decimal('0.123'),
            'daily_budget_cc': Decimal('123')
        }
        ap = dash.constants.SystemUserType.AUTOPILOT
        autopilot_helpers.update_ad_group_b1_sources_group_values(ag, changes, system_user=ap)

        mock_copy_settings.assert_called_once()

        mock_set_ad_group_sources_cpcs.assert_called_with(ANY, ag, current_ag_settings)
        mock_set_ad_group_sources_cpcs.assert_called_once()

        mock_k1_update_ad_group.assert_called_once()

        self.assertEqual(current_ag_settings.b1_sources_group_cpc_cc, Decimal('0.123'))
        self.assertEqual(current_ag_settings.b1_sources_group_daily_budget, Decimal('123'))
        self.assertEqual(current_ag_settings.system_user, ap)
