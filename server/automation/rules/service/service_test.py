import datetime
import textwrap

import mock
from django.test import TestCase

import automation.models
import core.models
import dash.constants
import etl.models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleCondition
from .. import RuleHistory
from .. import constants
from . import exceptions
from . import service
from .actions import ValueChangeData
from .apply import ErrorData


@mock.patch("automation.rules.service.helpers._remove_inactive_ad_groups", mock.MagicMock())
class ExecuteRulesDailyRunTest(TestCase):
    @mock.patch("utils.dates_helper.utc_now", mock.MagicMock(return_value=datetime.datetime(2019, 1, 1, 0, 0, 0)))
    @mock.patch("core.features.bid_modifiers.converters.TargetConverter.from_target")
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run(self, mock_stats, mock_format, mock_apply, mock_from_target):
        ad_groups = magic_mixer.cycle(10).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [{"ad_group_id": 123}]
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
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules_daily_run()

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
            [mock.call(target_type, [{"ad_group_id": 123}]) for target_type in constants.TargetType.get_all()],
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
                + "An error has occurred.",
                fail_history.changes_text,
            )

    @mock.patch("utils.dates_helper.utc_now", mock.MagicMock(return_value=datetime.datetime(2019, 1, 1, 0, 0, 0)))
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_history(self, mock_stats, mock_format, mock_apply):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {ad_group.id: {}}
        mock_apply.return_value = (
            [
                ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
                ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
            ],
            [],
        )

        publisher_rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, ad_groups_included=[ad_group]
        )

        service.execute_rules_daily_run()

        latest_ad_group_history = ad_group.history.latest("created_dt")
        latest_rule_history = RuleHistory.objects.get(rule=publisher_rule, status=constants.ApplyStatus.SUCCESS)
        expected_history_text = "Updated targets: pub1.com__12, pub2.com__21"
        expected_history_changes = {
            "pub2.com__21": {"old_value": 2.0, "new_value": 1.0},
            "pub1.com__12": {"old_value": 1.0, "new_value": 2.0},
        }

        self.assertEqual(expected_history_text, latest_ad_group_history.changes_text)
        self.assertEqual(expected_history_changes, latest_ad_group_history.changes)
        self.assertEqual(dash.constants.SystemUserType.RULES, latest_ad_group_history.system_user)
        self.assertEqual(None, latest_ad_group_history.created_by)

        self.assertEqual(expected_history_text, latest_rule_history.changes_text)
        self.assertEqual(expected_history_changes, latest_ad_group_history.changes)

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run_fail(self, mock_stats, mock_format, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [{"ad_group_id": 123}]
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

        self.assertFalse(RuleHistory.objects.exists())
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules_daily_run()

        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())
        history = RuleHistory.objects.get()
        self.assertEqual(rule, history.rule)
        self.assertEqual(constants.ApplyStatus.FAILURE, history.status)
        self.assertEqual({"test": {"message": "error message", "stack_trace": "traceback"}}, history.changes)
        self.assertEqual("An error has occurred.", history.changes_text)

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run_no_changes(self, mock_stats, mock_format, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {ad_group.id: {}}
        mock_apply.return_value = ([], [])
        for target_type in constants.TargetType.get_all():
            magic_mixer.blend(Rule, target_type=target_type, ad_groups_included=[ad_group])

        self.assertFalse(RuleHistory.objects.exists())
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules_daily_run()

        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())
        self.assertEqual(10, mock_stats.call_count)
        self.assertEqual(10, mock_format.call_count)
        self.assertEqual(10, mock_apply.call_count)
        self.assertFalse(RuleHistory.objects.exists())

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("redshiftapi.api_rules.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run_completed(self, mock_stats, mock_time):
        magic_mixer.blend(automation.models.RulesDailyJobLog)

        service.execute_rules_daily_run()

        mock_stats.assert_not_called()

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("redshiftapi.api_rules.query", return_value=[])
    def test_execute_rules_daily_run_no_materialized_data(self, mock_stats, mock_time):
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())
        self.assertFalse(etl.models.MaterializationRun.objects.exists())

        materialization_data = magic_mixer.blend(
            etl.models.EtlBooksClosed, date=dates_helper.local_yesterday(), etl_books_closed=False
        )
        service.execute_rules_daily_run()
        mock_stats.assert_not_called()
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        service.execute_rules_daily_run()
        mock_stats.assert_not_called()
        self.assertFalse(automation.models.RulesDailyJobLog.objects.exists())

        materialization_data.etl_books_closed = True
        materialization_data.save()

        service.execute_rules_daily_run()
        self.assertEqual(10, mock_stats.call_count)
        self.assertTrue(automation.models.RulesDailyJobLog.objects.exists())


@mock.patch("utils.dates_helper.utc_now", mock.MagicMock(return_value=datetime.datetime(2019, 1, 1, 0, 0, 0)))
@mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
@mock.patch("etl.materialization_run.materialization_completed_for_local_today", mock.MagicMock(return_value=True))
@mock.patch("automation.rules.service.helpers._remove_inactive_ad_groups", mock.MagicMock())
@mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
@mock.patch("utils.email_helper.send_official_email")
class NotificationEmailTestCase(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.ad_group = magic_mixer.blend(
            core.models.AdGroup, archived=False, name="Test ad group", campaign__account__agency=self.agency
        )
        self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.rule = magic_mixer.blend(
            Rule,
            name="Test rule",
            agency=self.agency,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            ad_groups_included=[self.ad_group],
            notification_type=constants.NotificationType.ON_RULE_RUN,
            notification_recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
        )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_changes(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.return_value = (
            [
                ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
                ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
            ],
            [],
        )

        service.execute_rules_daily_run()

        self.assertEqual(["testuser1@zemanta.com"], mock_send_email.call_args_list[0][1]["recipient_list"])
        self.assertEqual(["testuser2@zemanta.com"], mock_send_email.call_args_list[1][1]["recipient_list"])

        for call_args in mock_send_email.call_args_list:
            self.assertEqual(call_args[1]["subject"], "Rule “Test rule” performed actions on ad group Test ad group")
            self.assertEqual(
                call_args[1]["body"],
                textwrap.dedent(
                    f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} with message:

                        Updated targets: pub1.com__12, pub2.com__21

                        Yours truly,
                        Zemanta"""
                ),
            )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_changes_with_error(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.return_value = (
            [
                ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
                ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
            ],
            [
                ErrorData(
                    target="error_target_2", exc=exceptions.CampaignAutopilotActive("test2"), stack_trace="traceback 2"
                ),
                ErrorData(
                    target="error_target_3", exc=exceptions.BudgetAutopilotInactive("test3"), stack_trace="traceback 3"
                ),
            ],
        )

        service.execute_rules_daily_run()

        self.assertEqual(["testuser1@zemanta.com"], mock_send_email.call_args_list[0][1]["recipient_list"])
        self.assertEqual(["testuser2@zemanta.com"], mock_send_email.call_args_list[1][1]["recipient_list"])

        for call_args in mock_send_email.call_args_list:
            self.assertEqual(call_args[1]["subject"], "Rule “Test rule” performed actions on ad group Test ad group")
            self.assertEqual(
                call_args[1]["body"],
                textwrap.dedent(
                    f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} with message:

                        Updated targets: pub1.com__12, pub2.com__21

                        The following errors were encountered during rule execution:

                        To change the autopilot daily budget the campaign budget optimization must not be active. To change the autopilot daily budget the autopilot goal optimization must be active.

                        Yours truly,
                        Zemanta"""
                ),
            )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_only_error(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.return_value = (
            [],
            [
                ErrorData(
                    target="error_target_2", exc=exceptions.CampaignAutopilotActive("test2"), stack_trace="traceback 2"
                ),
                ErrorData(
                    target="error_target_3", exc=exceptions.BudgetAutopilotInactive("test3"), stack_trace="traceback 3"
                ),
            ],
        )

        service.execute_rules_daily_run()

        self.assertEqual(["testuser1@zemanta.com"], mock_send_email.call_args_list[0][1]["recipient_list"])
        self.assertEqual(["testuser2@zemanta.com"], mock_send_email.call_args_list[1][1]["recipient_list"])

        for call_args in mock_send_email.call_args_list:
            self.assertEqual(call_args[1]["subject"], "Rule “Test rule” encountered errors on ad group Test ad group")
            self.assertEqual(
                call_args[1]["body"],
                textwrap.dedent(
                    f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and encountered the following errors:

                        To change the autopilot daily budget the campaign budget optimization must not be active. To change the autopilot daily budget the autopilot goal optimization must be active.

                        Yours truly,
                        Zemanta"""
                ),
            )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_no_changes(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.return_value = ([], [])

        service.execute_rules_daily_run()

        self.assertEqual(["testuser1@zemanta.com"], mock_send_email.call_args_list[0][1]["recipient_list"])
        self.assertEqual(["testuser2@zemanta.com"], mock_send_email.call_args_list[1][1]["recipient_list"])

        for call_args in mock_send_email.call_args_list:
            self.assertEqual(call_args[1]["subject"], "Rule “Test rule” ran on ad group Test ad group")
            self.assertEqual(
                call_args[1]["body"],
                textwrap.dedent(
                    f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} without doing any changes.

                        Yours truly,
                        Zemanta"""
                ),
            )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_no_changes_on_rule_action_triggered(
        self, mock_stats, mock_format, mock_apply, mock_send_email
    ):
        self.rule.update(None, notification_type=constants.NotificationType.ON_RULE_ACTION_TRIGGERED)
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.return_value = ([], [])

        service.execute_rules_daily_run()

        self.assertFalse(mock_send_email.called)


@mock.patch("automation.rules.service.service.apply_rule", return_value=([], []))
@mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
@mock.patch("redshiftapi.api_rules.query", mock.MagicMock(return_value={}))
@mock.patch("automation.rules.service.helpers._remove_inactive_ad_groups", mock.MagicMock())
class FetchSettingsTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)

        budget_settings = {
            constants.MetricType.CAMPAIGN_BUDGET_START_DATE,
            constants.MetricType.DAYS_SINCE_CAMPAIGN_BUDGET_START,
            constants.MetricType.CAMPAIGN_BUDGET_END_DATE,
            constants.MetricType.DAYS_UNTIL_CAMPAIGN_BUDGET_END,
            constants.MetricType.CAMPAIGN_BUDGET_MARGIN,
            constants.MetricType.CAMPAIGN_REMAINING_BUDGET,
        }
        additional_settings = {
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE,
            constants.MetricType.AD_GROUP_DAILY_CAP,
        }
        self.basic_metric_types = (
            set(constants.METRIC_SETTINGS_MAPPING)
            - budget_settings
            - additional_settings
            - constants.CONTENT_AD_SETTINGS
        )

    def test_fetch_ad_group_settings(self, mock_apply):
        self._prepare_ad_group_rule()

        service.execute_rules_daily_run()
        self.assertEqual(1, mock_apply.call_count)
        self.assertEqual(
            self._get_settings_fields(self.basic_metric_types) | {"ad_group_id"}, set(mock_apply.call_args[0][3])
        )

    def test_fetch_ad_group_settings_primary_campaign_goal(self, mock_apply):
        rule = self._prepare_ad_group_rule()
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_type=constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        service.execute_rules_daily_run()
        self.assertEqual(1, mock_apply.call_count)
        additional_metric_types = {
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE,
        }
        self.assertEqual(
            self._get_settings_fields(self.basic_metric_types | additional_metric_types) | {"ad_group_id"},
            set(mock_apply.call_args[0][3]),
        )

    def test_fetch_ad_group_settings_primary_campaign_goal_value(self, mock_apply):
        rule = self._prepare_ad_group_rule()
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_type=constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        service.execute_rules_daily_run()
        self.assertEqual(1, mock_apply.call_count)
        additional_metric_types = {
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL,
            constants.MetricType.CAMPAIGN_PRIMARY_GOAL_VALUE,
        }
        self.assertEqual(
            self._get_settings_fields(self.basic_metric_types | additional_metric_types) | {"ad_group_id"},
            set(mock_apply.call_args[0][3]),
        )

    def test_fetch_ad_group_settings_daily_caps(self, mock_apply):
        rule = self._prepare_ad_group_rule()
        magic_mixer.blend(
            RuleCondition,
            rule=rule,
            left_operand_type=constants.MetricType.AD_GROUP_DAILY_CAP,
            right_operand_type=constants.ValueType.ABSOLUTE,
        )

        service.execute_rules_daily_run()
        self.assertEqual(1, mock_apply.call_count)
        additional_metric_types = {constants.MetricType.AD_GROUP_DAILY_CAP}
        self.assertEqual(
            self._get_settings_fields(self.basic_metric_types | additional_metric_types) | {"ad_group_id"},
            set(mock_apply.call_args[0][3]),
        )

    def test_fetch_content_ad_settings(self, mock_apply):
        self._prepare_content_ad_rule()

        service.execute_rules_daily_run()
        self.assertEqual(1, mock_apply.call_count)
        self.assertEqual(
            self._get_settings_fields(self.basic_metric_types) | {"ad_group_id"}, set(mock_apply.call_args[0][3])
        )
        self.assertEqual(
            self._get_settings_fields(constants.CONTENT_AD_SETTINGS) | {"ad_group_id", "content_ad_id"},
            set(mock_apply.call_args[0][4][self.content_ad.id]),
        )

    def _get_settings_fields(self, metric_types):
        return {constants.METRIC_SETTINGS_MAPPING[metric] for metric in metric_types}

    def _prepare_ad_group_rule(self):
        return magic_mixer.blend(Rule, target_type=constants.TargetType.AD_GROUP, ad_groups_included=[self.ad_group])

    def _prepare_content_ad_rule(self):
        return magic_mixer.blend(Rule, target_type=constants.TargetType.AD, ad_groups_included=[self.ad_group])
