import datetime

import mock
from django.test import TestCase

import automation.models
import core.models
import dash.constants
import etl.models
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleHistory
from .. import constants
from . import exceptions
from . import service
from .actions import ValueChangeData
from .apply import ErrorData


class ServiceTest(TestCase):
    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("core.features.bid_modifiers.converters.TargetConverter.from_target")
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rules(self, mock_stats, mock_format, mock_apply, mock_from_target, mock_time):
        ad_groups = magic_mixer.cycle(10).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [123]
        mock_format.return_value = {ag.id: {} for ag in ad_groups}
        mock_apply.return_value = (
            [
                ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
                ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
            ],
            [
                ErrorData(
                    target="error_target_1", exc=exceptions.CampaignAutopilotActive("test1"), stack_trace="traceback 1"
                ),
                ErrorData(
                    target="error_target_2", exc=exceptions.CampaignAutopilotActive("test2"), stack_trace="traceback 2"
                ),
                ErrorData(
                    target="error_target_3", exc=exceptions.BudgetAutopilotInactive("test3"), stack_trace="traceback 3"
                ),
                ErrorData(
                    target="error_target_4", exc=exceptions.BudgetAutopilotInactive("test4"), stack_trace="traceback 4"
                ),
                ErrorData(target="error_target_5", exc=exceptions.AutopilotActive("test5"), stack_trace="traceback 5"),
                ErrorData(target="error_target_6", exc=exceptions.AutopilotActive("test6"), stack_trace="traceback 6"),
                ErrorData(target="error_target_7", exc=Exception("test7"), stack_trace="traceback 7"),
                ErrorData(target="error_target_8", exc=Exception("test8"), stack_trace="traceback 8"),
            ],
        )
        mock_from_target.return_value = "readable target"

        ad_group_rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD_GROUP, ad_groups_included=ad_groups[:10]
        )
        ad_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, ad_groups_included=ad_groups[:9])
        publisher_rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, ad_groups_included=ad_groups[:8]
        )
        device_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.DEVICE, ad_groups_included=ad_groups[:7])
        country_rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.COUNTRY, ad_groups_included=ad_groups[:6]
        )
        state_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.STATE, ad_groups_included=ad_groups[:5])
        dma_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.DMA, ad_groups_included=ad_groups[:4])
        os_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.OS, ad_groups_included=ad_groups[:3])
        environment_rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.ENVIRONMENT, ad_groups_included=ad_groups[:2]
        )
        source_rule = magic_mixer.blend(Rule, target_type=constants.TargetType.SOURCE, ad_groups_included=ad_groups[:1])

        magic_mixer.blend(
            Rule,
            state=constants.RuleState.PAUSED,
            target_type=constants.TargetType.PUBLISHER,
            ad_groups_included=ad_groups,
        )
        magic_mixer.blend(etl.models.MaterializationRun)
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules()

        # daily job
        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())

        # query stats
        self.assertEqual(
            [
                mock.call(target_type, [mock.ANY] * (10 - i))
                for i, target_type in enumerate(constants.TargetType.get_all())
            ],
            mock_stats.call_args_list,
        )
        for i in range(10):
            self.assertCountEqual(ad_groups[: 10 - i], mock_stats.call_args_list[i][0][1])

        # format stats
        self.assertEqual(
            [mock.call(target_type, [123]) for target_type in constants.TargetType.get_all()],
            mock_format.call_args_list,
        )

        # apply
        self.assertEqual(sum(range(1, 11)), mock_apply.call_count)

        # history
        self.assertEqual(sum(range(1, 11)) * 2, RuleHistory.objects.all().count())
        self._test_history(ad_group_rule)
        self._test_history(ad_rule)
        self._test_history(publisher_rule)
        self._test_history(device_rule)
        self._test_history(country_rule)
        self._test_history(state_rule)
        self._test_history(dma_rule)
        self._test_history(os_rule)
        self._test_history(environment_rule)
        self._test_history(source_rule)

    def _test_history(self, rule):
        rule_history = RuleHistory.objects.filter(rule=rule, status=constants.ApplyStatus.SUCCESS)
        rule_fail_history = RuleHistory.objects.filter(rule=rule, status=constants.ApplyStatus.FAILURE)
        self.assertTrue(rule_history.count() > 0)
        self.assertTrue(rule_fail_history.count() > 0)
        self.assertEqual(rule.ad_groups_included.count(), rule_history.count())
        self.assertEqual(rule.ad_groups_included.count(), rule_fail_history.count())

        for history in rule_history:
            self.assertEqual(rule, history.rule)
            self.assertTrue(history.ad_group in rule.ad_groups_included.all())
            self.assertEqual(constants.ApplyStatus.SUCCESS, history.status)
            self.assertEqual(
                {
                    "pub1.com__12": {"old_value": 1.0, "new_value": 2.0},
                    "pub2.com__21": {"old_value": 2.0, "new_value": 1.0},
                },
                history.changes,
            )
            self.assertIn("Updated targets: ", history.changes_text)
            self.assertTrue(
                any(text in history.changes_text for text in ["readable target", "pub1.com__12", "pub2.com__21"])
            )

        for fail_history in rule_fail_history:
            self.assertEqual(rule, fail_history.rule)
            self.assertTrue(fail_history.ad_group in rule.ad_groups_included.all())
            self.assertEqual(constants.ApplyStatus.FAILURE, fail_history.status)
            self.assertEqual(
                {
                    "error_target_1": {"message": "test1", "stack_trace": "traceback 1"},
                    "error_target_2": {"message": "test2", "stack_trace": "traceback 2"},
                    "error_target_3": {"message": "test3", "stack_trace": "traceback 3"},
                    "error_target_4": {"message": "test4", "stack_trace": "traceback 4"},
                    "error_target_5": {"message": "test5", "stack_trace": "traceback 5"},
                    "error_target_6": {"message": "test6", "stack_trace": "traceback 6"},
                    "error_target_7": {"message": "test7", "stack_trace": "traceback 7"},
                    "error_target_8": {"message": "test8", "stack_trace": "traceback 8"},
                },
                fail_history.changes,
            )
            self.assertEqual(
                "To change the autopilot daily budget the campaign budget optimization must not be active. "
                + "To change the autopilot daily budget the autopilot goal optimization must be active. "
                + "To change the source bid modifier the campaign budget optimization and autopilot goal optimization must not be active; "
                + "rule failed to make changes on 2 sources. "
                + "An error has occured.",
                fail_history.changes_text,
            )

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rules_fail(self, mock_stats, mock_format, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [123]
        mock_format.return_value = {ad_group.id: {}}
        mock_apply.return_value = (
            [],
            [ErrorData(target="test", exc=Exception("error message"), stack_trace="traceback")],
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            ad_groups_included=[ad_group],
        )
        magic_mixer.blend(etl.models.MaterializationRun)
        self.assertFalse(RuleHistory.objects.exists())
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules()

        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())
        history = RuleHistory.objects.get()
        self.assertEqual(rule, history.rule)
        self.assertEqual(constants.ApplyStatus.FAILURE, history.status)
        self.assertEqual({"test": {"message": "error message", "stack_trace": "traceback"}}, history.changes)
        self.assertEqual("An error has occured.", history.changes_text)

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.service._format_stats")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rules_no_changes(self, mock_stats, mock_format, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [123]
        mock_format.return_value = {ad_group.id: {}}
        mock_apply.return_value = ([], [])
        for target_type in constants.TargetType.get_all():
            magic_mixer.blend(Rule, target_type=target_type, ad_groups_included=[ad_group])

        magic_mixer.blend(etl.models.MaterializationRun)
        self.assertFalse(RuleHistory.objects.exists())
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules()

        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())
        self.assertEqual(10, mock_stats.call_count)
        self.assertEqual(10, mock_format.call_count)
        self.assertEqual(10, mock_apply.call_count)
        self.assertFalse(RuleHistory.objects.exists())

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rules_daily_run_completed(self, mock_stats, mock_time):
        magic_mixer.blend(automation.models.RulesDailyJobLog)
        magic_mixer.blend(etl.models.MaterializationRun)

        service.execute_rules()

        mock_stats.assert_not_called()

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rules_no_materialized_data(self, mock_stats, mock_time):
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())
        self.assertFalse(etl.models.MaterializationRun.objects.exists())

        service.execute_rules()
        mock_stats.assert_not_called()
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        etl_run = magic_mixer.blend(etl.models.MaterializationRun)
        etl_run.finished_dt = "2018-12-31 09:59:59"
        etl_run.save()

        service.execute_rules()
        mock_stats.assert_not_called()
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        etl_run.finished_dt = "2018-12-31 10:00:00"
        etl_run.save()

        service.execute_rules()
        self.assertEqual(10, mock_stats.call_count)
        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())

    def test_get_rules_by_ad_group_map(self):
        ad_groups_archived = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=True)
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups + ad_groups_archived:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        ad_groups_inactive = magic_mixer.cycle(5).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups_inactive:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)

        rule_1 = magic_mixer.blend(
            Rule, ad_groups_included=ad_groups[:3] + ad_groups_inactive[:3] + ad_groups_archived[:3]
        )
        rule_2 = magic_mixer.blend(
            Rule, ad_groups_included=ad_groups[3:5] + ad_groups_inactive[3:5] + ad_groups_archived[3:5]
        )
        rule_3 = magic_mixer.blend(
            Rule, ad_groups_included=ad_groups[1:4] + ad_groups_inactive[1:4] + ad_groups_archived[1:4]
        )

        rules_map = service._get_rules_by_ad_group_map([rule_1, rule_2, rule_3])
        self.assertEqual(
            {
                ad_groups[0]: [rule_1],
                ad_groups[1]: [rule_1, rule_3],
                ad_groups[2]: [rule_1, rule_3],
                ad_groups[3]: [rule_2, rule_3],
                ad_groups[4]: [rule_2],
            },
            rules_map,
        )

    def test_format_publisher_stats(self):
        target_type = constants.TargetType.PUBLISHER
        stats = [
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.3,
                "cpm": 0.1,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.5,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": "pub2.com",
                "window_key": constants.MetricWindow.LIFETIME,
                "cpc": None,
                "cpm": 0.8,
            },
            {
                "ad_group_id": 321,
                "source_id": 32,
                "publisher": "pub1.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.1,
                "cpm": 0.2,
            },
            {
                "ad_group_id": 321,
                "source_id": 21,
                "publisher": "pub3.com",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.2,
                "cpm": 0.1,
            },
            {
                "ad_group_id": None,
                "source_id": 12,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                "source_id": 12,
                "publisher": None,
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                "source_id": None,
                "publisher": "pub4.com",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {"ad_group_id": 321, "source_id": 12, "publisher": "pub5", "window_key": None, "cpc": 0.7, "cpm": 0.9},
            {
                "ad_group_id": 321,
                "publisher": "pub5",
                "window_key": constants.MetricWindow.LAST_DAY,
                "cpc": 0.7,
                "cpm": 0.9,
            },
        ]
        formatted_stats = service._format_stats(target_type, stats)
        self.assertEqual(
            {
                123: {
                    "pub1.com__12": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    },
                    "pub2.com__12": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    },
                },
                321: {
                    "pub1.com__32": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "pub3.com__21": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )

    def test_format_ad_group_stats(self):
        target_type = constants.TargetType.AD_GROUP
        stats = [
            {"ad_group_id": 123, "window_key": constants.MetricWindow.LAST_3_DAYS, "cpc": 0.5, "cpm": 0.7},
            {"ad_group_id": 123, "window_key": constants.MetricWindow.LAST_30_DAYS, "cpc": 0.3, "cpm": 0.1},
            {"ad_group_id": 111, "window_key": constants.MetricWindow.LAST_DAY, "cpc": 0.5, "cpm": 0.2},
            {"ad_group_id": 111, "window_key": constants.MetricWindow.LIFETIME, "cpc": None, "cpm": 0.8},
            {"ad_group_id": 321, "window_key": constants.MetricWindow.LAST_3_DAYS, "cpc": 0.1, "cpm": 0.2},
            {"ad_group_id": 222, "window_key": constants.MetricWindow.LAST_DAY, "cpc": 0.2, "cpm": 0.1},
            {"ad_group_id": None, "window_key": constants.MetricWindow.LAST_3_DAYS, "cpc": 0.7, "cpm": 0.9},
            {"ad_group_id": 333, "window_key": None, "cpc": 0.7, "cpm": 0.9},
        ]
        formatted_stats = service._format_stats(target_type, stats)
        self.assertEqual(
            {
                123: {
                    "123": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    }
                },
                111: {
                    "111": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    }
                },
                321: {
                    "321": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    }
                },
                222: {
                    "222": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    }
                },
            },
            formatted_stats,
        )

    def test_format_stats(self):
        test_cases = {
            target_type: constants.TARGET_TYPE_STATS_MAPPING[target_type][0]
            for target_type in [
                constants.TargetType.AD,
                constants.TargetType.DEVICE,
                constants.TargetType.COUNTRY,
                constants.TargetType.STATE,
                constants.TargetType.DMA,
                constants.TargetType.OS,
                constants.TargetType.ENVIRONMENT,
                constants.TargetType.SOURCE,
            ]
        }

        for target_type, mv_column in test_cases.items():
            self._test_format_stats(target_type, mv_column)

    def _test_format_stats(self, target_type, mv_column):
        stats = [
            {
                "ad_group_id": 123,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.5,
                "cpm": 0.7,
            },
            {
                "ad_group_id": 123,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_30_DAYS,
                "cpc": 0.3,
                "cpm": 0.1,
            },
            {"ad_group_id": 111, mv_column: 12, "window_key": constants.MetricWindow.LAST_DAY, "cpc": 0.5, "cpm": 0.2},
            {"ad_group_id": 111, mv_column: 12, "window_key": constants.MetricWindow.LIFETIME, "cpc": None, "cpm": 0.8},
            {
                "ad_group_id": 321,
                mv_column: "32",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.1,
                "cpm": 0.2,
            },
            {"ad_group_id": 321, mv_column: 21, "window_key": constants.MetricWindow.LAST_DAY, "cpc": 0.2, "cpm": 0.1},
            {
                "ad_group_id": None,
                mv_column: "12",
                "window_key": constants.MetricWindow.LAST_3_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {
                "ad_group_id": 123,
                mv_column: None,
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {
                "ad_group_id": 222,
                mv_column: "Other",
                "window_key": constants.MetricWindow.LAST_7_DAYS,
                "cpc": 0.7,
                "cpm": 0.9,
            },
            {"ad_group_id": 321, mv_column: "12", "window_key": None, "cpc": 0.7, "cpm": 0.9},
            {"ad_group_id": 321, "window_key": constants.MetricWindow.LAST_DAY, "cpc": 0.7, "cpm": 0.9},
        ]
        formatted_stats = service._format_stats(target_type, stats)
        self.assertEqual(
            {
                123: {
                    "12": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.5, constants.MetricWindow.LAST_30_DAYS: 0.3},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.7, constants.MetricWindow.LAST_30_DAYS: 0.1},
                    }
                },
                111: {
                    "12": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.5, constants.MetricWindow.LIFETIME: None},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.2, constants.MetricWindow.LIFETIME: 0.8},
                    }
                },
                321: {
                    "32": {
                        "cpc": {constants.MetricWindow.LAST_3_DAYS: 0.1},
                        "cpm": {constants.MetricWindow.LAST_3_DAYS: 0.2},
                    },
                    "21": {
                        "cpc": {constants.MetricWindow.LAST_DAY: 0.2},
                        "cpm": {constants.MetricWindow.LAST_DAY: 0.1},
                    },
                },
            },
            formatted_stats,
        )
