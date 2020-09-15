import datetime
import textwrap

import mock
from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import RuleHistory
from .. import constants
from . import notification_emails


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
            change_step=2,
            ad_groups_included=[self.ad_group],
            notification_type=constants.NotificationType.ON_RULE_RUN,
            notification_recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
        )

    def test_execute_rule_send_email_changes(self, mock_send_email):
        history = magic_mixer.blend(
            RuleHistory,
            rule=self.rule,
            changes={
                "pub1.com__12": dict(old_value=1.0, new_value=2.0),
                "pub2.com__21": dict(old_value=2.0, new_value=1.0),
            },
        )
        notification_emails.send_notification_email_if_enabled(self.rule, self.ad_group, history)

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” performed actions on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} with message:

                        Increased bid modifier for 2.0% on publishers: pub1.com__12 (2.0%), pub2.com__21 (1.0%)

                        Yours truly,
                        Zemanta"""
            ),
        )

    def test_execute_rule_send_email_no_changes(self, mock_send_email):
        history = magic_mixer.blend(RuleHistory, rule=self.rule, status=constants.ApplyStatus.SUCCESS_NO_CHANGES)
        notification_emails.send_notification_email_if_enabled(self.rule, self.ad_group, history)

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” ran on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was successfully executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} without making any changes.

                        Yours truly,
                        Zemanta"""
            ),
        )

    def test_execute_rule_send_email_no_changes_on_rule_action_triggered(self, mock_send_email):
        self.rule.update(None, notification_type=constants.NotificationType.ON_RULE_ACTION_TRIGGERED)
        history = magic_mixer.blend(RuleHistory, rule=self.rule, status=constants.ApplyStatus.SUCCESS_NO_CHANGES)
        notification_emails.send_notification_email_if_enabled(self.rule, self.ad_group, history)

        self.assertFalse(mock_send_email.called)

    def test_execute_rule_send_email_known_exception(self, mock_send_email):
        history = magic_mixer.blend(
            RuleHistory,
            rule=self.rule,
            status=constants.ApplyStatus.FAILURE,
            failure_reason=constants.RuleFailureReason.BUDGET_AUTOPILOT_INACTIVE,
        )
        notification_emails.send_notification_email_if_enabled(self.rule, self.ad_group, history)

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” encountered errors on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and has encountered errors. View in history: https://one.zemanta.com/v2/rules/history?agencyId={self.rule.agency_id}&ruleId={self.rule.id}

                        Yours truly,
                        Zemanta"""
            ),
        )

    def test_execute_rule_send_email_unknown_exception(self, mock_send_email):
        history = magic_mixer.blend(
            RuleHistory,
            rule=self.rule,
            status=constants.ApplyStatus.FAILURE,
            failure_reason=constants.RuleFailureReason.UNEXPECTED_ERROR,
        )
        notification_emails.send_notification_email_if_enabled(self.rule, self.ad_group, history)

        self._assert_email_sent_to_all_recipients_separately(
            mock_send_email,
            recipients=["testuser1@zemanta.com", "testuser2@zemanta.com"],
            subject="Rule “Test rule” encountered errors on ad group Test ad group",
            body=textwrap.dedent(
                f"""\
                        Hi,

                        We’re letting you know that your rule “Test rule” was executed on your ad group https://one.zemanta.com/v2/analytics/adgroup/{self.ad_group.id} and has encountered errors. View in history: https://one.zemanta.com/v2/rules/history?agencyId={self.rule.agency_id}&ruleId={self.rule.id}

                        Yours truly,
                        Zemanta"""
            ),
        )

    def _assert_email_sent_to_all_recipients_separately(self, mock_send_email, recipients, subject, body):
        actual_recipients = []
        for call_args in mock_send_email.call_args_list:
            self.assertEqual(1, len(call_args[1]["recipient_list"]))
            actual_recipients.extend(call_args[1]["recipient_list"])
            self.assertEqual(call_args[1]["subject"], subject)
            self.assertEqual(call_args[1]["body"], body)
        self.assertCountEqual(recipients, actual_recipients)
