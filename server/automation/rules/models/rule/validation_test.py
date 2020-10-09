import core.features.publisher_groups
import core.models
from core.features.bid_modifiers import MODIFIER_MAX
from core.features.bid_modifiers import MODIFIER_MIN
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from ... import constants
from ... import exceptions
from . import model


class RuleValidationTest(BaseTestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)

    def _prepare_rule(self, **kwargs):
        rule_kwargs = {"agency": self.agency, "accounts_included": [self.account]}
        rule_kwargs.update(kwargs)
        self.rule = magic_mixer.blend(model.Rule, **rule_kwargs)

    def test_validate_state(self):
        self._prepare_rule()
        self.rule.clean({"state": constants.RuleState.ENABLED})
        with self.assert_multiple_validation_error([exceptions.InvalidRuleState]):
            self.rule.clean({"state": 999})

    def test_validate_target_type(self):
        rule = model.Rule(agency=self.agency)
        rule.clean({"target_type": constants.TargetType.PUBLISHER, "accounts_included": [self.account]})
        with self.assert_multiple_validation_error([exceptions.InvalidTargetType]):
            rule.clean({"target_type": 999, "accounts_included": [self.account]})

    def test_prevent_changing_target_type(self):
        self._prepare_rule(target_type=constants.TargetType.PUBLISHER)
        with self.assert_multiple_validation_error([exceptions.InvalidTargetType]):
            self.rule.clean({"target_type": constants.TargetType.PLACEMENT})

    def test_validate_action_type(self):
        rule = model.Rule(agency=self.agency)
        rule.target_type = constants.TargetType.PUBLISHER
        rule.clean({"action_type": constants.ActionType.INCREASE_BID_MODIFIER, "accounts_included": [self.account]})
        with self.assert_multiple_validation_error([exceptions.InvalidActionType]):
            rule.clean({"action_type": 999, "accounts_included": [self.account]})

    def test_prevent_changing_action_type(self):
        self._prepare_rule(action_type=constants.ActionType.INCREASE_BID_MODIFIER)
        with self.assert_multiple_validation_error([exceptions.InvalidActionType]):
            self.rule.clean({"action_type": constants.ActionType.DECREASE_BID_MODIFIER})

    def test_validate_window(self):
        self._prepare_rule()
        self.rule.clean({"window": constants.MetricWindow.LAST_30_DAYS})
        with self.assert_multiple_validation_error([exceptions.InvalidWindow]):
            self.rule.clean({"window": 999})

    def test_validate_cooldown(self):
        self._prepare_rule()
        self.rule.clean({"cooldown": 24})
        with self.assert_multiple_validation_error([exceptions.InvalidCooldown]):
            self.rule.clean({"cooldown": 0})
        with self.assert_multiple_validation_error([exceptions.InvalidCooldown]):
            self.rule.clean({"cooldown": 40})

    def test_validate_change_step_increase_bid_modifier(self):
        self._prepare_rule(
            action_type=constants.ActionType.INCREASE_BID_MODIFIER, target_type=constants.TargetType.PUBLISHER
        )
        self.rule.clean({"change_step": 0.01, "change_limit": 5})
        self.rule.clean({"change_step": 1, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 0.001, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 0, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": -0.01, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 1.01, "change_limit": 5})

    def test_validate_change_step_decrease_bid_modifier(self):
        self._prepare_rule(
            action_type=constants.ActionType.DECREASE_BID_MODIFIER, target_type=constants.TargetType.PUBLISHER
        )
        self.rule.clean({"change_step": 0.01, "change_limit": 5})
        self.rule.clean({"change_step": 1, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 0.001, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 0, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": -0.01, "change_limit": 5})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeStep]):
            self.rule.clean({"change_step": 1.01, "change_limit": 5})

    def test_validate_change_limit_increase_bid_modifier(self):
        self._prepare_rule(
            action_type=constants.ActionType.INCREASE_BID_MODIFIER, target_type=constants.TargetType.PUBLISHER
        )
        self.rule.clean({"change_limit": float(MODIFIER_MIN), "change_step": 0.01})
        self.rule.clean({"change_limit": float(MODIFIER_MAX), "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": 0, "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": float(MODIFIER_MAX) + 0.01, "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": -0.01, "change_step": 0.01})

    def test_validate_change_limit_decrease_bid_modifier(self):
        self._prepare_rule(
            action_type=constants.ActionType.DECREASE_BID_MODIFIER, target_type=constants.TargetType.PUBLISHER
        )
        self.rule.clean({"change_limit": float(MODIFIER_MIN), "change_step": 0.01})
        self.rule.clean({"change_limit": float(MODIFIER_MAX), "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": 0, "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": float(MODIFIER_MAX) + 0.01, "change_step": 0.01})
        with self.assert_multiple_validation_error([exceptions.InvalidChangeLimit]):
            self.rule.clean({"change_limit": -0.01, "change_step": 0.01})

    def test_validate_send_email_subject(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {"send_email_subject": "test", "send_email_body": "test", "send_email_recipients": ["user@test.com"]}
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {"send_email_subject": "", "send_email_body": "test", "send_email_recipients": ["user@test.com"]}
            )

    def test_validate_send_email_subject_fixed_window_macros(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {
                "send_email_body": "test",
                "send_email_subject": "This is a macro test {ACCOUNT_NAME} ({ACCOUNT_ID})",
                "send_email_recipients": ["user@test.com"],
            }
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {INVALID_MACRO}",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME ({ACCOUNT_ID}})",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": """This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}
                        that spans two lines""",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}\rthat spans two lines",
                    "send_email_recipients": ["user@test.com"],
                }
            )

    def test_validate_send_email_subject_adjustable_window_macros(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {
                "send_email_body": "test",
                "send_email_subject": "This is a macro test {TOTAL_SPEND_LAST_30_DAYS}",
                "send_email_recipients": ["user@test.com"],
            }
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailSubject]):
            self.rule.clean(
                {
                    "send_email_body": "test",
                    "send_email_subject": "This is a macro test {TOTAL_SPEND}",
                    "send_email_recipients": ["user@test.com"],
                }
            )

    def test_validate_send_email_body(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {"send_email_body": "test", "send_email_subject": "test", "send_email_recipients": ["user@test.com"]}
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {"send_email_body": "", "send_email_subject": "test", "send_email_recipients": ["user@test.com"]}
            )

    def test_validate_send_email_body_fixed_window_macros(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {
                "send_email_body": "This is a macro test {ACCOUNT_NAME} ({ACCOUNT_ID})",
                "send_email_subject": "test",
                "send_email_recipients": ["user@test.com"],
            }
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {INVALID_MACRO}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {ACCOUNT_NAME ({ACCOUNT_ID}})",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                }
            )

    def test_validate_send_email_body_adjustable_window_macros(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {
                "send_email_body": "This is a macro test {TOTAL_SPEND_LAST_30_DAYS}",
                "send_email_subject": "test",
                "send_email_recipients": ["user@test.com"],
            }
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailBody]):
            self.rule.clean(
                {
                    "send_email_body": "This is a macro test {TOTAL_SPEND}",
                    "send_email_subject": "test",
                    "send_email_recipients": ["user@test.com"],
                }
            )

    def test_validate_send_email_recipients(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean(
            {"send_email_recipients": ["user@test.com"], "send_email_subject": "test", "send_email_body": "test"}
        )
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailRecipients]):
            self.rule.clean({"send_email_recipients": [], "send_email_subject": "test", "send_email_body": "test"})
        with self.assert_multiple_validation_error([exceptions.InvalidSendEmailRecipients]):
            self.rule.clean(
                {"send_email_recipients": ["usertest.com"], "send_email_subject": "test", "send_email_body": "test"}
            )

    def test_validate_notification_type(self):
        self._prepare_rule(target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.SEND_EMAIL)
        self.rule.clean({"notification_type": constants.NotificationType.NONE})
        with self.assert_multiple_validation_error([exceptions.InvalidNotificationType]):
            self.rule.clean({"notification_type": constants.NotificationType.ON_RULE_RUN})

    def test_validate_notification_recipients(self):
        self._prepare_rule(action_type=constants.ActionType.INCREASE_BID_MODIFIER)
        self.rule.clean({"notification_recipients": [], "notification_type": constants.NotificationType.NONE})
        self.rule.clean(
            {"notification_recipients": ["user@test.com"], "notification_type": constants.NotificationType.ON_RULE_RUN}
        )
        with self.assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {"notification_recipients": [], "notification_type": constants.NotificationType.ON_RULE_RUN}
            )
        with self.assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {
                    "notification_recipients": [],
                    "notification_type": constants.NotificationType.ON_RULE_ACTION_TRIGGERED,
                }
            )
        with self.assert_multiple_validation_error([exceptions.InvalidNotificationRecipients]):
            self.rule.clean(
                {
                    "notification_recipients": ["usertest.com"],
                    "notification_type": constants.NotificationType.ON_RULE_RUN,
                }
            )

    def test_validate_valid_publisher_group_agency_on_agency_rule(self):
        self._prepare_rule(
            target_type=constants.TargetType.PUBLISHER, action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP
        )
        valid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=self.rule.agency, account=None
        )
        self.rule.clean({"publisher_group": valid_publisher_group})

    def test_validate_valid_publisher_group_account_on_agency_rule(self):
        self._prepare_rule(
            target_type=constants.TargetType.PUBLISHER, action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP
        )
        valid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account__agency=self.rule.agency, agency=None
        )
        self.rule.clean({"publisher_group": valid_publisher_group})

    def test_validate_invalid_publisher_group_agency_on_agency_rule(self):
        unconnected_agency = magic_mixer.blend(core.models.Agency)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=None, agency=unconnected_agency
        )
        self._prepare_rule(
            target_type=constants.TargetType.PUBLISHER, action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP
        )
        with self.assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            self.rule.clean({"publisher_group": invalid_publisher_group})

    def test_validate_invalid_publisher_group_account_on_agency_rule(self):
        unconnected_account = magic_mixer.blend(core.models.Account)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=unconnected_account, agency=None
        )
        self._prepare_rule(
            target_type=constants.TargetType.PUBLISHER, action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP
        )
        with self.assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            self.rule.clean({"publisher_group": invalid_publisher_group})

    def test_validate_valid_publisher_group_agency_on_account_rule(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account_rule = magic_mixer.blend(
            model.Rule,
            account=account,
            accounts_included=[account],
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
        )
        valid_publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        account_rule.clean({"publisher_group": valid_publisher_group})

    def test_validate_valid_publisher_group_account_on_account_rule(self):
        account = magic_mixer.blend(core.models.Account)
        account_rule = magic_mixer.blend(
            model.Rule,
            account=account,
            accounts_included=[account],
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
        )
        valid_publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        account_rule.clean({"publisher_group": valid_publisher_group})

    def test_validate_invalid_publisher_group_agency_on_account_rule(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account_rule = magic_mixer.blend(
            model.Rule,
            account=account,
            accounts_included=[account],
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
        )

        unconnected_agency = magic_mixer.blend(core.models.Agency)
        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=unconnected_agency
        )
        with self.assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            account_rule.clean({"publisher_group": invalid_publisher_group})

    def test_validate_invalid_publisher_group_account_on_account_rule(self):
        unconnected_account = magic_mixer.blend(core.models.Account)
        account = magic_mixer.blend(core.models.Account)
        account_rule = magic_mixer.blend(
            model.Rule,
            account=account,
            accounts_included=[account],
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
        )

        invalid_publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=unconnected_account
        )
        with self.assert_multiple_validation_error([exceptions.InvalidPublisherGroup]):
            account_rule.clean({"publisher_group": invalid_publisher_group})

    def test_validate_missing_included_entities(self):
        agency = magic_mixer.blend(core.models.Agency)
        account_rule = magic_mixer.blend(model.Rule, agency=agency)

        with self.assert_multiple_validation_error([exceptions.MissingIncludedEntities]):
            account_rule.clean({"name": "New name"})

    def test_validate_conditions(self):
        self._prepare_rule()
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
        with self.assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
            self.rule.clean({"conditions": []})
        with self.assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
            self.rule.clean({"conditions": [{}]})
        with self.assert_multiple_validation_error([exceptions.InvalidRuleConditions]):
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
