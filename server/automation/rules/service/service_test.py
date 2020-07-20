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
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @mock.patch("core.features.bid_modifiers.converters.TargetConverter.from_target")
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.query_stats")
    def test_execute_rules_daily_run(self, mock_query_stats, mock_apply, mock_from_target):
        ad_groups = magic_mixer.cycle(10).blend(core.models.AdGroup, archived=False)
        for ag in ad_groups:
            ag.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_query_stats.return_value = {ag.id: {} for ag in ad_groups}
        mock_apply.return_value = (
            [
                ValueChangeData(target="pub1.com__12", old_value=1.0, new_value=2.0),
                ValueChangeData(target="pub2.com__21", old_value=2.0, new_value=1.0),
            ],
            [],
        )

        mock_from_target.return_value = "readable target"

        magic_mixer.blend(Rule, target_type=constants.TargetType.AD_GROUP, ad_groups_included=ad_groups[:10])
        magic_mixer.blend(Rule, target_type=constants.TargetType.AD, ad_groups_included=ad_groups[:9])
        magic_mixer.blend(Rule, target_type=constants.TargetType.PUBLISHER, ad_groups_included=ad_groups[:8])
        magic_mixer.blend(Rule, target_type=constants.TargetType.DEVICE, ad_groups_included=ad_groups[:7])
        magic_mixer.blend(Rule, target_type=constants.TargetType.COUNTRY, ad_groups_included=ad_groups[:6])
        magic_mixer.blend(Rule, target_type=constants.TargetType.STATE, ad_groups_included=ad_groups[:5])
        magic_mixer.blend(Rule, target_type=constants.TargetType.DMA, ad_groups_included=ad_groups[:4])
        magic_mixer.blend(Rule, target_type=constants.TargetType.OS, ad_groups_included=ad_groups[:3])
        magic_mixer.blend(Rule, target_type=constants.TargetType.ENVIRONMENT, ad_groups_included=ad_groups[:2])
        magic_mixer.blend(Rule, target_type=constants.TargetType.SOURCE, ad_groups_included=ad_groups[:1])

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

        all_rules = Rule.objects.filter(state=constants.RuleState.ENABLED)

        expected_stats_calls = []
        for rule in all_rules:
            expected_stats_calls.append(
                mock.call(rule.target_type, {ad_group: [rule] for ad_group in rule.ad_groups_included.all()})
            )
        # format stats
        self.assertCountEqual(mock_query_stats.call_args_list, expected_stats_calls)

        expected_num_applies = sum(rule.ad_groups_included.count() for rule in all_rules)

        # apply
        self.assertEqual(expected_num_applies, mock_apply.call_count)

        # history - one per apply
        self.assertEqual(expected_num_applies, RuleHistory.objects.all().count())

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
    @mock.patch("automation.rules.service.fetch.stats._format", mock.MagicMock())
    @mock.patch("redshiftapi.api_rules.query", mock.MagicMock())
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run_known_error(self, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_apply.side_effect = exceptions.CampaignAutopilotActive
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
        self.assertEqual(None, history.changes)
        self.assertEqual(
            "In order to change the autopilot daily budget the campaign budget optimization must not be active.",
            history.changes_text,
        )
        self.assertFalse(history.stack_trace)

    @mock.patch("utils.dates_helper.utc_now", return_value=datetime.datetime(2019, 1, 1, 0, 0, 0))
    @mock.patch("automation.rules.service.fetch.stats._format", mock.MagicMock())
    @mock.patch("redshiftapi.api_rules.query", mock.MagicMock())
    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_execute_rules_daily_run_unknown_error(self, mock_apply, mock_time):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=False)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        mock_apply.side_effect = Exception
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
        self.assertEqual(None, history.changes)
        self.assertEqual("An error has occurred.", history.changes_text)
        self.assertTrue(history.stack_trace)

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
        self.assertTrue(RuleHistory.objects.exists())

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

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” performed actions on ad group Test ad group",
            body=textwrap.dedent(
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
                ErrorData(target="error_target_2", exc=Exception(), stack_trace="traceback 2"),
                ErrorData(target="error_target_3", exc=Exception(), stack_trace="traceback 3"),
            ],
        )

        service.execute_rules_daily_run()

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” performed actions on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} with message:

                        Updated targets: pub1.com__12, pub2.com__21

                        The following errors were encountered during rule execution:

                        Error occurred while trying to update 2 targets.

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
                ErrorData(target="error_target_2", exc=Exception(), stack_trace="traceback 2"),
                ErrorData(target="error_target_3", exc=Exception(), stack_trace="traceback 3"),
            ],
        )

        service.execute_rules_daily_run()

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” encountered errors on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and encountered the following errors:

                        Error occurred while trying to update 2 targets.

                        Yours truly,
                        Zemanta"""
            ),
        )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_known_exception(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.side_effect = exceptions.CampaignAutopilotActive()

        service.execute_rules_daily_run()

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” encountered errors on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and encountered the following errors:

                        In order to change the autopilot daily budget the campaign budget optimization must not be active.

                        Yours truly,
                        Zemanta"""
            ),
        )

    @mock.patch("automation.rules.service.service.apply_rule")
    @mock.patch("automation.rules.service.fetch.stats._format")
    @mock.patch("redshiftapi.api_rules.query")
    def test_execute_rule_send_email_unknown_exception(self, mock_stats, mock_format, mock_apply, mock_send_email):
        mock_stats.return_value = [{"ad_group_id": 123}]
        mock_format.return_value = {self.ad_group.id: {}}
        mock_apply.side_effect = Exception()

        service.execute_rules_daily_run()

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” encountered errors on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and encountered the following errors:

                        An error has occurred.

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

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” ran on ad group Test ad group",
            body=textwrap.dedent(
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

    def _assert_email_sent_to_all_recipients_separately(self, mock_send_email, recipients, subject, body):
        actual_recipients = []
        for call_args in mock_send_email.call_args_list:
            self.assertEqual(1, len(call_args[1]["recipient_list"]))
            actual_recipients.extend(call_args[1]["recipient_list"])
            self.assertEqual(call_args[1]["subject"], subject)
            self.assertEqual(call_args[1]["body"], body)
        self.assertCountEqual(recipients, actual_recipients)


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
