from decimal import Decimal
from mock import patch
import mock
import json
import traceback

from django import test

from automation import autopilot_plus
import automation.constants
import dash.models
import dash.views.helpers
import dash.api
from reports import refresh


class AutopilotPlusTestCase(test.TestCase):
    fixtures = ['test_automation.yaml']

    def setUp(self):
        refresh.refresh_adgroup_stats()

        # patcher = patch('dash.api.k1_helper')
        # self.k1_helper_mock = patcher.start()
        # self.addCleanup(patcher.stop)

    @patch('urllib2.urlopen')
    @test.override_settings(
        HOSTNAME='testhost',
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL='http://pagerduty.example.com',
        PAGER_DUTY_ENGINEERS_SERVICE_KEY='123abc'
    )
    def test_report_autopilot_exception(self, mock_urlopen):
        ad_group = dash.models.AdGroup.objects.get(id=1)
        ex = Exception()
        autopilot_plus._report_autopilot_exception(ad_group, ex)
        desc = 'Autopilot failed operating on element because an exception was raised: {}'.format(
            traceback.format_exc(ex)
        )
        mock_urlopen.assert_called_with(
            'http://pagerduty.example.com',
            json.dumps({
                'service_key': '123abc',
                'incident_key': 'automation_autopilot_error',
                'event_type': 'trigger',
                'description': desc,
                'client': 'Zemanta One - testhost',
                'details': {
                    'element': ''  # '<AdGroup: Test AdGroup 1>'
                },
            })
        )

    @patch('automation.autopilot_plus.prefetch_autopilot_data')
    @patch('automation.autopilot_helpers.get_active_ad_groups_on_autopilot')
    @patch('automation.autopilot_plus._get_autopilot_predictions')
    @patch('automation.autopilot_plus.set_autopilot_changes')
    @patch('automation.autopilot_plus.persist_autopilot_changes_to_log')
    @patch('automation.autopilot_plus._get_autopilot_campaign_changes_data')
    @patch('automation.autopilot_plus._report_autopilot_exception')
    @patch('utils.k1_helper.update_ad_group')
    def test_dry_run(self, mock_k1, mock_exc, mock_get_changes, mock_log, mock_set,
                     mock_predict, mock_active, mock_prefetch):
        ad_groups = list(dash.models.AdGroup.objects.all())
        mock_prefetch.return_value = (
            {
                a: {} for a in ad_groups
            },
            {},
        )
        mock_active.return_value = (
            ad_groups,
            [a.get_current_settings() for a in ad_groups],
        )
        mock_predict.return_value = (
            {}, {}
        )
        autopilot_plus.run_autopilot(
            send_mail=False,
            report_to_influx=False,
            dry_run=True
        )
        self.assertEqual(mock_exc.called, False)
        self.assertEqual(mock_k1.called, False)
        self.assertEqual(mock_log.called, False)

        self.assertEqual(mock_predict.called, True)
        self.assertEqual(mock_get_changes.called, True)
        mock_set.assert_called_with(
            {}, {}, dry_run=True
        )

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_only_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        cpc_changes = {ag_source: {
            'old_cpc_cc': Decimal('0.1'),
            'new_cpc_cc': Decimal('0.2')
        }}
        autopilot_plus.set_autopilot_changes(cpc_changes=cpc_changes)
        mock_update_values.assert_called_with(ag_source, {'cpc_cc': Decimal('0.2')},
                                              dash.constants.SystemUserType.AUTOPILOT, None)
        mock_update_values.assert_called_once()

    @patch('automation.autopilot_helpers.update_ad_group_source_values')
    def test_set_autopilot_changes_only_budget(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {
            'old_budget': Decimal('100'),
            'new_budget': Decimal('200')
        }}
        autopilot_plus.set_autopilot_changes(budget_changes=budget_changes)
        mock_update_values.assert_called_with(ag_source, {'daily_budget_cc': Decimal('200')},
                                              dash.constants.SystemUserType.AUTOPILOT, None)
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
        mock_update_values.assert_called_with(
            ag_source, {'cpc_cc': Decimal('0.2'), 'daily_budget_cc': Decimal('200')},
            dash.constants.SystemUserType.AUTOPILOT, None)
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
            {'ad_group': 1, 'source': 1, 'media_cost': 1, 'clicks': 1, 'data_cost': 0},
            {'ad_group': 1, 'source': 2, 'media_cost': 0, 'clicks': 0, 'data_cost': 0},
            {'ad_group': 2, 'source': 2, 'media_cost': 0, 'clicks': 0, 'data_cost': 0},
            {'ad_group': 2, 'source': 1, 'media_cost': 2, 'clicks': 2, 'data_cost': 0}
        )
        self.assertEqual(autopilot_plus._find_corresponding_source_data(source1, days_ago_data, yesterday_data),
                         (days_ago_data[0], 1, 1))
        self.assertEqual(autopilot_plus._find_corresponding_source_data(source2, days_ago_data, yesterday_data),
                         (days_ago_data[3], 2, 2))

    @patch('automation.autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET', Decimal('0.3'))
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
    @patch('influx.gauge')
    def test_report_adgroups_data_to_influx(self, mock_influx, mock_query):
        mock_query.return_value = [
            {'ad_group': 1, 'media_cost': Decimal('15'), 'data_cost': 0},
            {'ad_group': 3, 'media_cost': Decimal('10'), 'data_cost': 0},
            {'ad_group': 4, 'media_cost': Decimal('20'), 'data_cost': 0}]

        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 2, 3, 4])
        autopilot_plus._report_adgroups_data_to_influx([adg.get_current_settings() for adg in adgroups])

        mock_influx.assert_has_calls(
            [
                mock.call(
                    'automation.autopilot_plus.adgroups_on',
                    2,
                    autopilot='budget_autopilot'
                ),
                mock.call(
                    'automation.autopilot_plus.adgroups_on',
                    1,
                    autopilot='cpc_autopilot'
                ),
                mock.call(
                    'automation.autopilot_plus.spend',
                    Decimal('50'),
                    autopilot='budget_autopilot',
                    type='expected'
                ),
                mock.call(
                    'automation.autopilot_plus.spend',
                    Decimal('35'),
                    autopilot='budget_autopilot',
                    type='yesterday'
                ),
                mock.call(
                    'automation.autopilot_plus.spend',
                    Decimal('10'),
                    autopilot='cpc_autopilot',
                    type='yesterday'
                )
            ]
        )

    @patch('reports.api_contentads.query')
    @patch('influx.gauge')
    def test_report_new_budgets_on_ap_to_influx(self, mock_influx, mock_query):
        mock_query.return_value = [
            {'ad_group': 1, 'billing_cost': Decimal('15')},
            {'ad_group': 3, 'billing_cost': Decimal('10')},
            {'ad_group': 4, 'billing_cost': Decimal('20')}]

        adgroups = dash.models.AdGroup.objects.filter(id__in=[1, 3, 4])
        autopilot_plus._report_new_budgets_on_ap_to_influx([adg.get_current_settings() for adg in adgroups])

        mock_influx.assert_has_calls(
            [
                mock.call(
                    'automation.autopilot_plus.spend',
                    Decimal('50'),
                    autopilot='cpc_autopilot',
                    type='actual'
                ),
                mock.call(
                    'automation.autopilot_plus.spend',
                    Decimal('210'),
                    autopilot='budget_autopilot',
                    type='actual'
                ),
                mock.call(
                    'automation.autopilot_plus.sources_on',
                    1,
                    autopilot='cpc_autopilot'
                ),
                mock.call(
                    'automation.autopilot_plus.sources_on',
                    4,
                    autopilot='budget_autopilot'
                )
            ]
        )
