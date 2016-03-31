from decimal import Decimal
from mock import patch

from django import test

from automation import autopilot_helpers
import dash.models
from dash.constants import AdGroupSettingsAutopilotState, AdGroupRunningStatus
from reports import refresh


class AutopilotHelpersTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    @patch('dash.models.AdGroup.get_running_status')
    def test_get_active_ad_groups_on_autopilot(self, mock_running_status):
        mock_running_status.return_value = AdGroupRunningStatus.ACTIVE
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

    @patch('dash.models.AdGroup.get_running_status')
    def test_landing_mode(self, mock_running_status):
        mock_running_status.return_value = AdGroupRunningStatus.ACTIVE
        for campaign in dash.models.Campaign.objects.all():
            new_settings = campaign.get_current_settings().copy_settings()
            new_settings.landing_mode = True
            new_settings.save(None)

        all_ap_adgs, all_ap_adgs_settings = autopilot_helpers.get_active_ad_groups_on_autopilot()

        self.assertEqual(len(all_ap_adgs), 0)
        self.assertEqual(len(all_ap_adgs_settings), 0)

    def test_update_ad_group_source_values(self):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag_source_settings = ag_source.get_current_settings()
        old_daily_budget = ag_source_settings.daily_budget_cc
        old_cpc = ag_source_settings.cpc_cc
        autopilot_helpers.update_ad_group_source_values(ag_source, {
            'daily_budget_cc': old_daily_budget+Decimal('10'),
            'cpc_cc': old_cpc+Decimal('0.5')})
        new_ag_source_settings = ag_source.get_current_settings()
        self.assertNotEqual(ag_source_settings, new_ag_source_settings)
        self.assertEqual(new_ag_source_settings.daily_budget_cc, old_daily_budget+Decimal('10'))
        self.assertEqual(new_ag_source_settings.cpc_cc, old_cpc+Decimal('0.5'))
