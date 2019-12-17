from contextlib import contextmanager

from django import test

import utils.exc
from core.features.bid_modifiers import MODIFIER_MAX
from core.features.bid_modifiers import MODIFIER_MIN

from ... import constants
from ... import exceptions
from . import model


class RuleValidationTest(test.TestCase):
    def setUp(self):
        self.rule = model.Rule()

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

    def test_validate_notification_recipients(self):
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
