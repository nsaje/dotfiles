from decimal import Decimal
from mock import patch
import mock

from django import test

from automation import autopilot_plus
import automation.constants
import dash.models
import dash.views.helpers
import dash.api
from dash.constants import AdGroupSettingsState
from reports import refresh


class AutopilotPlusTestCase(test.TestCase):
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

    @patch('automation.autopilot_settings.MIN_SOURCE_BUDGET', Decimal('0.3'))
    def test_set_paused_ad_group_sources_to_minimum_values(self):
        adg = dash.models.AdGroup.objects.get(id=4)
        paused_ad_group_source_setting = dash.models.AdGroupSourceSettings.objects.get(id=6).copy_settings()
        paused_ad_group_source_setting.state = 2
        paused_ad_group_source_setting.daily_budget_cc = Decimal('100.')
        paused_ad_group_source_setting.save(None)
        paused_ad_group_source = paused_ad_group_source_setting.ad_group_source
        active_ad_group_source = dash.models.AdGroupSource.objects.get(id=6)
        active_ad_group_source_old_budget = active_ad_group_source.get_current_settings().daily_budget_cc
        new_budgets = autopilot_plus._set_paused_ad_group_sources_to_minimum_values(adg)
        self.assertEqual(new_budgets.get(paused_ad_group_source)['old_budget'], Decimal('100.'))
        self.assertEqual(new_budgets.get(paused_ad_group_source)['new_budget'], Decimal('5'))
        self.assertEqual(new_budgets.get(paused_ad_group_source)['budget_comments'],
                         [automation.constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE])
        self.assertEqual(paused_ad_group_source.get_current_settings().daily_budget_cc, Decimal('5'))
        self.assertEqual(active_ad_group_source.get_current_settings().daily_budget_cc,
                         active_ad_group_source_old_budget)
        self.assertTrue(active_ad_group_source not in new_budgets)

    @patch('automation.autopilot_plus.run_autopilot')
    def test_initialize_budget_autopilot_on_ad_group(self, mock_run_autopilot):
        adg = dash.models.AdGroup.objects.get(id=4)
        paused_ad_group_source_setting = dash.models.AdGroupSourceSettings.objects.get(id=6).copy_settings()
        paused_ad_group_source_setting.state = 2
        paused_ad_group_source_setting.daily_budget_cc = Decimal('100.')
        paused_ad_group_source_setting.save(None)
        paused_ad_group_source = paused_ad_group_source_setting.ad_group_source
        changed_source = dash.models.AdGroupSource.objects.get(id=1)
        not_changed_source = dash.models.AdGroupSource.objects.get(id=2)
        mock_run_autopilot.return_value = {
            adg.campaign: {adg: {
                changed_source: {
                    'old_budget': Decimal('20'),
                    'new_budget': Decimal('30')
                },
                not_changed_source: {
                    'old_budget': Decimal('20'),
                    'new_budget': Decimal('20')
                },

            }}
        }
        changed_sources = autopilot_plus.initialize_budget_autopilot_on_ad_group(adg)
        self.assertTrue(paused_ad_group_source in changed_sources)
        self.assertTrue(changed_source in changed_sources)
        self.assertTrue(not_changed_source not in changed_sources)

    @patch('reports.api_contentads.query')
    @patch('utils.statsd_helper.statsd_gauge')
    def test_report_adgroups_data_to_statsd(self, mock_statsd, mock_query):
        mock_query.return_value = [
            {'ad_group': 1, 'billing_cost': Decimal('15')},
            {'ad_group': 3, 'billing_cost': Decimal('10')},
            {'ad_group': 4, 'billing_cost': Decimal('20')}]

        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 2, 3, 4])
        autopilot_plus._report_adgroups_data_to_statsd([adg.get_current_settings() for adg in adgroups])

        mock_statsd.assert_has_calls(
            [
                mock.call('automation.autopilot_plus.adgroups_on_budget_autopilot', 2),
                mock.call('automation.autopilot_plus.adgroups_on_cpc_autopilot', 1),
                mock.call('automation.autopilot_plus.adgroups_on_budget_autopilot_expected_budget', Decimal('50')),
                mock.call('automation.autopilot_plus.adgroups_on_budget_autopilot_yesterday_spend', Decimal('35')),
                mock.call('automation.autopilot_plus.adgroups_on_cpc_autopilot_yesterday_spend', Decimal('10'))
            ]
        )

    @patch('reports.api_contentads.query')
    @patch('utils.statsd_helper.statsd_gauge')
    def test_report_new_budgets_on_ap_to_statsd(self, mock_statsd, mock_query):
        mock_query.return_value = [
            {'ad_group': 1, 'billing_cost': Decimal('15')},
            {'ad_group': 3, 'billing_cost': Decimal('10')},
            {'ad_group': 4, 'billing_cost': Decimal('20')}]

        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 3, 4])
        autopilot_plus._report_new_budgets_on_ap_to_statsd([adg.get_current_settings() for adg in adgroups])

        mock_statsd.assert_has_calls(
            [
                mock.call('automation.autopilot_plus.adgroups_on_budget_autopilot_actual_budget', Decimal('210')),
                mock.call('automation.autopilot_plus.adgroups_on_cpc_autopilot_actual_budget', Decimal('50')),
                mock.call('automation.autopilot_plus.adgroups_on_all_autopilot_actual_budget', Decimal('260')),
                mock.call('automation.autopilot_plus.num_sources_on_cpc_ap', 1),
                mock.call('automation.autopilot_plus.num_sources_on_budget_ap', 4)
            ]
        )
