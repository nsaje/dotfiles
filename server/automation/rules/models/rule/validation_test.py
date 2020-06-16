from contextlib import contextmanager

from django import test

import core.features.publisher_groups
import core.models
import utils.exc
from core.features.bid_modifiers import MODIFIER_MAX
from core.features.bid_modifiers import MODIFIER_MIN
from utils.magic_mixer import magic_mixer

from ... import constants
from ... import exceptions
from . import model


class RuleValidationTest(test.TestCase):
    def setUp(self):
        agency = magic_mixer.blend(core.models.Agency)
        self.rule = magic_mixer.blend(model.Rule, agency=agency)

    def test_validate_state(self):
        self.rule.clean({"state": constants.RuleState.ENABLED})
        with self._assert_multiple_validation_error([exceptions.InvalidRuleState]):
            self.rule.clean({"state": 999})

    def test_validate_target_type(self):
        self.rule.clean({"target_type": constants.TargetType.PUBLISHER})
        with self._assert_multiple_validation_error([exceptions.InvalidTargetType]):
            self.rule.clean({"target_type": 999})

    def test_validate_action_type(self):
        self.rule.target_type = constants.TargetType.PUBLISHER
        self.rule.clean({"action_type": constants.ActionType.INCREASE_BID_MODIFIER})
        with self._assert_multiple_validation_error([exceptions.InvalidActionType]):
            self.rule.clean({"action_type": 999})

    def test_validate_window(self):
        self.rule.clean({"window": constants.MetricWindow.LAST_30_DAYS})
        with self._assert_multiple_validation_error([exceptions.InvalidWindow]):
            self.rule.clean({"window": 999})

    def test_validate_cooldown(self):
        self.rule.clean({"cooldown": 24})
        with self._assert_multiple_validation_error([exceptions.InvalidCooldown]):
            self.rule.clean({"cooldown": 0})
        with self._assert_multiple_validation_error([exceptions.InvalidCooldown]):
            self.rule.clean({"cooldown": 40})

    def test_validate_change_step_bid_modifier(self):
        self.rule.target_type = constants.TargetType.PUBLISHER
        for action_type in [constants.ActionType.INCREASE_BID_MODIFIER, constants.ActionType.DECREASE_BID_MODIFIER]:
            self.rule.clean({"action_type": action_type, "change_step": 0.01, "change_limit": 5})
            self.rule.clean({"action_type": action_type, "change_step": 1, "change_limit": 5})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeStep]):
                self.rule.clean({"action_type": action_type, "change_step": 0.001, "change_limit": 5})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeStep]):
                self.rule.clean({"action_type": action_type, "change_step": 0, "change_limit": 5})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeStep]):
                self.rule.clean({"action_type": action_type, "change_step": -0.01, "change_limit": 5})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeStep]):
                self.rule.clean({"action_type": action_type, "change_step": 1.01, "change_limit": 5})

    def test_validate_change_limit_bid_modifier(self):
        self.rule.target_type = constants.TargetType.PUBLISHER
        for action_type in [constants.ActionType.INCREASE_BID_MODIFIER, constants.ActionType.DECREASE_BID_MODIFIER]:
            self.rule.clean({"action_type": action_type, "change_limit": float(MODIFIER_MIN), "change_step": 0.01})
            self.rule.clean({"action_type": action_type, "change_limit": float(MODIFIER_MAX), "change_step": 0.01})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
                self.rule.clean({"action_type": action_type, "change_limit": 0, "change_step": 0.01})
            with self._assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
                self.rule.clean(
                    {"action_type": action_type, "change_limit": float(MODIFIER_MAX) + 0.01, "change_step": 0.01}
                )
            with self._assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
                self.rule.clean({"action_type": action_type, "change_limit": -0.01, "change_step": 0.01})

    def test_validate_send_email_subject(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        # TODO: uncomment when send email isn't the only action type on ad group anymore
        # self.rule.clean({"send_email_subject": "", "action_type": constants.ActionType.TURN_OFF})
        # with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
        #     self.rule.clean({"send_email_subject": "test", "action_type": constants.ActionType.TURN_OFF})
        self.rule.clean(
            {
                "send_email_subject": "test",
                "send_email_body": "test",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_subject": "",
                    "send_email_body": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_subject_fixed_window_macros(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        self.rule.clean(
            {
                "send_email_body": "test",
                "send_email_subject": "This is a macro test {ACCOUNT_NAME} ({ACCOUNT_ID})",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {INVALID_MACRO}",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME ({ACCOUNT_ID}})",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": """This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}
                        that spans two lines""",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}\rthat spans two lines",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_subject_adjustable_window_macros(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        self.rule.clean(
            {
                "send_email_body": "test",
                "send_email_subject": "This is a macro test {TOTAL_SPEND_LAST_30_DAYS}",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {TOTAL_SPEND}",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_body(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        # TODO: uncomment when send email isn't the only action type on ad group anymore
        # self.rule.clean({"send_email_body": "", "action_type": constants.ActionType.TURN_OFF})
        # with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
        #     self.rule.clean({"send_email_body": "test", "action_type": constants.ActionType.TURN_OFF})
        self.rule.clean(
            {
                "send_email_body": "test",
                "send_email_subject": "test",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_body_fixed_window_macros(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        self.rule.clean(
            {
                "send_email_body": "This is a macro test {ACCOUNT_NAME} ({ACCOUNT_ID})",
                "send_email_subject": "test",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {INVALID_MACRO}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {ACCOUNT_NAME ({ACCOUNT_ID}})",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_body_adjustable_window_macros(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        self.rule.clean(
            {
                "send_email_body": "This is a macro test {TOTAL_SPEND_LAST_30_DAYS}",
                "send_email_subject": "test",
                "send_email_recipients": ["user@test.com"],
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {TOTAL_SPEND}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_send_email_recipients(self):
        self.rule.target_type = constants.TargetType.AD_GROUP
        # TODO: uncomment when send email isn't the only action type on ad group anymore
        # self.rule.clean({"send_email_recipients": [], "action_type": constants.ActionType.TURN_OFF})
        self.rule.clean(
            {
                "send_email_recipients": ["user@test.com"],
                "send_email_subject": "test",
                "send_email_body": "test",
                "action_type": constants.ActionType.SEND_EMAIL,
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailRecipients]):
            self.rule.clean(
                {
                    "send_email_recipients": [],
                    "send_email_subject": "test",
                    "send_email_body": "test",
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidSendEmailRecipients]):
            self.rule.clean(
                {
                    "send_email_recipients": ["usertest.com"],
                    "send_email_subject": "test",
                    "send_email_body": "test",
                    "action_type": constants.ActionType.SEND_EMAIL,
                }
            )

    def test_validate_notification_type(self):
        self.rule.clean({"notification_type": constants.NotificationType.NONE})
        with self._assert_multiple_validation_error([exceptions.InvalidNotificationType]):
            self.rule.clean(
                {
                    "notification_type": constants.NotificationType.ON_RULE_RUN,
                    "action_type": constants.ActionType.SEND_EMAIL,
                    "target_type": constants.TargetType.AD_GROUP,
                }
            )

    def test_validate_notification_recipients(self):
        self.rule.action_type = (
            constants.ActionType.INCREASE_BID_MODIFIER
        )  # fixed action type to avoid SEND_EMAIL being set
        self.rule.clean({"notification_recipients": [], "notification_type": constants.NotificationType.NONE})
        self.rule.clean(
            {"notification_recipients": ["user@test.com"], "notification_type": constants.NotificationType.ON_RULE_RUN}
        )
        with self._assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {"notification_recipients": [], "notification_type": constants.NotificationType.ON_RULE_RUN}
            )
        with self._assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {
                    "notification_recipients": [],
                    "notification_type": constants.NotificationType.ON_RULE_ACTION_TRIGGERED,
                }
            )
        with self._assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {
                    "notification_recipients": ["usertest.com"],
                    "notification_type": constants.NotificationType.ON_RULE_RUN,
                }
            )

    def test_validate_valid_publisher_group_agency_on_agency_rule(self):
        valid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=self.rule.agency, account=None
        )
        self.rule.clean(
            {
                "publisher_group": valid_publisher_group,
                "target_type": constants.TargetType.PUBLISHER,
                "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            }
        )

    def test_validate_valid_publisher_group_account_on_agency_rule(self):
        valid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account__agency=self.rule.agency, agency=None
        )
        self.rule.clean(
            {
                "publisher_group": valid_publisher_group,
                "target_type": constants.TargetType.PUBLISHER,
                "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            }
        )

    def test_validate_invalid_publisher_group_agency_on_agency_rule(self):
        unconnected_agency = magic_mixer.blend(core.models.Agency)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=None, agency=unconnected_agency
        )
        with self._assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            self.rule.clean(
                {
                    "publisher_group": invalid_publisher_group,
                    "target_type": constants.TargetType.PUBLISHER,
                    "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
                }
            )

    def test_validate_invalid_publisher_group_account_on_agency_rule(self):
        unconnected_account = magic_mixer.blend(core.models.Account)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=unconnected_account, agency=None
        )
        with self._assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            self.rule.clean(
                {
                    "publisher_group": invalid_publisher_group,
                    "target_type": constants.TargetType.PUBLISHER,
                    "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
                }
            )

    def test_validate_valid_publisher_group_agency_on_account_rule(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account_rule = magic_mixer.blend(model.Rule, account=account)
        valid_publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        account_rule.clean(
            {
                "publisher_group": valid_publisher_group,
                "target_type": constants.TargetType.PUBLISHER,
                "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            }
        )

    def test_validate_valid_publisher_group_account_on_account_rule(self):
        account = magic_mixer.blend(core.models.Account)
        account_rule = magic_mixer.blend(model.Rule, account=account)
        valid_publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        account_rule.clean(
            {
                "publisher_group": valid_publisher_group,
                "target_type": constants.TargetType.PUBLISHER,
                "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            }
        )

    def test_validate_invalid_publisher_group_agency_on_account_rule(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account_rule = magic_mixer.blend(model.Rule, account=account)

        unconnected_agency = magic_mixer.blend(core.models.Agency)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=unconnected_agency
        )
        with self._assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            account_rule.clean(
                {
                    "publisher_group": invalid_publisher_group,
                    "target_type": constants.TargetType.PUBLISHER,
                    "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
                }
            )

    def test_validate_invalid_publisher_group_account_on_account_rule(self):
        unconnected_account = magic_mixer.blend(core.models.Account)
        account = magic_mixer.blend(core.models.Account)
        account_rule = magic_mixer.blend(model.Rule, account=account)

        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=unconnected_account
        )
        with self._assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            account_rule.clean(
                {
                    "publisher_group": invalid_publisher_group,
                    "target_type": constants.TargetType.PUBLISHER,
                    "action_type": constants.ActionType.ADD_TO_PUBLISHER_GROUP,
                }
            )

    def test_validate_conditions(self):
        self.rule.clean(
            {
                "conditions": [
                    {
                        "operator": constants.Operator.GREATER_THAN,
                        "left_operand_type": constants.MetricType.TOTAL_SPEND,
                        "left_operand_window": None,
                        "left_operand_modifier": None,
                        "right_operand_type": constants.ValueType.ABSOLUTE,
                        "right_operand_window": None,
                        "right_operand_value": 300,
                    }
                ]
            }
        )
        with self._assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
            self.rule.clean({"conditions": []})
        with self._assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
            self.rule.clean({"conditions": [{}]})
        with self._assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
            self.rule.clean(
                {
                    "conditions": [
                        {
                            "operator": None,
                            "left_operand_type": None,
                            "left_operand_window": None,
                            "left_operand_modifier": None,
                            "right_operand_type": None,
                            "right_operand_window": None,
                            "right_operand_value": 300,
                        }
                    ]
                }
            )

    @contextmanager
    def _assert_multiple_validation_error(self, exceptions):
        try:
            yield
        except utils.exc.MultipleValidationError as e:
            for err in e.errors:
                self.assertTrue(type(err) in exceptions)
