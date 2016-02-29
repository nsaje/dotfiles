from decimal import Decimal
from mock import patch

from django import test

from automation import autopilot_plus
import dash.models
import dash.views.helpers
import dash.api
from dash.constants import AdGroupSettingsState
from reports import refresh


class AutopilotBudgetsTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_only_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        cpc_changes = {ag_source: {
            'old_cpc_cc': Decimal('0.1'),
            'new_cpc_cc': Decimal('0.2')
        }}
        autopilot_plus.set_autopilot_changes(cpc_changes=cpc_changes)
        mock_update_values.assert_called_with(ag_source, {'cpc_cc': Decimal('0.2')})
        mock_update_values.assert_called_once()

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_only_budget(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {
            'old_budget': Decimal('100'),
            'new_budget': Decimal('200')
        }}
        autopilot_plus.set_autopilot_changes(budget_changes=budget_changes)
        mock_update_values.assert_called_with(ag_source, {'daily_budget_cc': Decimal('200')})
        mock_update_values.assert_called_once()

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_budget_and_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {
            'old_budget': Decimal('100'),
            'new_budget': Decimal('200')
        }}
        cpc_changes = {ag_source: {
            'old_cpc_cc': Decimal('0.1'),
            'new_cpc_cc': Decimal('0.2')
        }}
        autopilot_plus.set_autopilot_changes(cpc_changes=cpc_changes, budget_changes=budget_changes)
        mock_update_values.assert_called_with(ag_source, {'cpc_cc': Decimal('0.2'), 'daily_budget_cc': Decimal('200')})
        mock_update_values.assert_called_once()

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_budget_and_cpc_no_change(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {
            'old_budget': Decimal('100'),
            'new_budget': Decimal('100')
        }}
        cpc_changes = {ag_source: {
            'old_cpc_cc': Decimal('0.1'),
            'new_cpc_cc': Decimal('0.1')
        }}
        autopilot_plus.set_autopilot_changes(cpc_changes=cpc_changes, budget_changes=budget_changes)
        self.assertEqual(mock_update_values.called, False)

    def test_get_autopilot_active_sources_settings(self):
        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 2, 3])
        active_enabled_sources = autopilot_plus._get_autopilot_active_sources_settings(adgroups)
        for ag_source_setting in active_enabled_sources:
            self.assertTrue(ag_source_setting.state == AdGroupSettingsState.ACTIVE)
            self.assertTrue(ag_source_setting.ad_group_source.ad_group in adgroups)

        source = dash.models.AdGroupSource.objects.get(id=1)
        self.assertTrue(source in [setting.ad_group_source for setting in active_enabled_sources])
        settings_writer = dash.api.AdGroupSourceSettingsWriter(source)
        settings_writer.set({'state': AdGroupSettingsState.INACTIVE}, None)
        self.assertEqual(source.get_current_settings().state, AdGroupSettingsState.INACTIVE)
        self.assertFalse(source in [setting.ad_group_source for setting in
                                    autopilot_plus._get_autopilot_active_sources_settings(adgroups)])

    def test_find_corresponding_source_data(self):
        source1 = dash.models.AdGroupSource.objects.get(id=1)
        source2 = dash.models.AdGroupSource.objects.get(id=2)
        days_ago_data = (
            {'ad_group': 1, 'source': 1, 'rand': 1},
            {'ad_group': 1, 'source': 2, 'rand': 0},
            {'ad_group': 2, 'source': 2, 'rand': 0},
            {'ad_group': 2, 'source': 1, 'rand': 2}
        )
        yesterday_data = (
            {'ad_group': 1, 'source': 1, 'billing_cost': 1, 'clicks': 1},
            {'ad_group': 1, 'source': 2, 'billing_cost': 0, 'clicks': 0},
            {'ad_group': 2, 'source': 2, 'billing_cost': 0, 'clicks': 0},
            {'ad_group': 2, 'source': 1, 'billing_cost': 2, 'clicks': 2}
        )
        self.assertEqual(autopilot_plus._find_corresponding_source_data(source1, days_ago_data, yesterday_data),
                         (days_ago_data[0], 1, 1))
        self.assertEqual(autopilot_plus._find_corresponding_source_data(source2, days_ago_data, yesterday_data),
                         (days_ago_data[3], 2, 2))
