from functools import partial

from django.core.validators import ValidationError
from django.core.validators import validate_email

import utils.validation_helper

from ... import config
from ... import constants
from ... import exceptions
from ..rule_condition import RuleCondition


class RuleValidationMixin:
    def clean(self, changes):
        utils.validation_helper.validate_multiple(
            partial(self._validate_if_present, "state"),
            partial(self._validate_if_present, "target_type"),
            partial(self._validate_if_present, "action_type"),
            partial(self._validate_if_present, "change_step"),
            partial(self._validate_if_present, "change_limit"),
            partial(self._validate_if_present, "conditions"),
            changes=changes,
        )

    def _validate_if_present(self, key, changes):
        if key in changes:
            getattr(self, "_validate_" + key)(changes, changes[key])

    def _validate_state(self, changes, state):
        if state not in constants.RuleState.get_all():
            raise exceptions.InvalidRuleState("Invalid state")

    def _validate_target_type(self, changes, target_type):
        if target_type not in config.VALID_TARGET_TYPES:
            # TODO(luka): for v1, remove when all target types are supported
            raise exceptions.InvalidTargetType("Invalid target type")
        if target_type not in constants.TargetType.get_all():
            raise exceptions.InvalidTargetType("Invalid target type")

    def _validate_action_type(self, changes, action_type):
        target_type = changes.get("target_type", self.target_type)
        if action_type not in config.VALID_ACTION_TYPES_FOR_TARGET[target_type]:
            valid_action_types = ", ".join(
                [constants.ActionType.get_name(at) for at in config.VALID_ACTION_TYPES_FOR_TARGET[target_type]]
            )
            raise exceptions.InvalidActionType(f"Invalid action type for target. Valid choices: {valid_action_types}.")

    def _validate_change_step(self, changes, change_step):
        action_type = changes.get("action_type", self.action_type)
        if action_type not in config.ADJUSTEMENT_ACTION_TYPES and change_step is not None:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidChangeStep(f"Change step shouldn't be set for action type: {action_type_name}.")
        if action_type in config.ADJUSTEMENT_ACTION_TYPES:
            if change_step is None:
                raise exceptions.InvalidChangeStep("Please provide change step")
            elif change_step < config.ADJUSTEMENT_ACTION_TYPES[action_type].min_step:
                raise exceptions.InvalidChangeStep("Change step is too small")
            elif change_step > config.ADJUSTEMENT_ACTION_TYPES[action_type].max_step:
                raise exceptions.InvalidChangeStep("Change step is too big")

    def _validate_change_limit(self, changes, change_limit):
        action_type = changes.get("action_type", self.action_type)
        if action_type not in config.ADJUSTEMENT_ACTION_TYPES and change_limit is not None:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidChangeLimit(f"Change limit shouldn't be set for action type: {action_type_name}.")
        if action_type in config.ADJUSTEMENT_ACTION_TYPES:
            if change_limit is None:
                raise exceptions.InvalidChangeLimit("Please provide change limit")
            elif change_limit < config.ADJUSTEMENT_ACTION_TYPES[action_type].min_limit:
                raise exceptions.InvalidChangeLimit("Change limit is too small")
            elif change_limit > config.ADJUSTEMENT_ACTION_TYPES[action_type].max_limit:
                raise exceptions.InvalidChangeLimit("Change limit is too big")

    def _validate_notification_recipients(self, changes, notification_recipients):
        notification_type = changes.get("notification_type", self.notification_type)
        if notification_type == constants.NotificationType.NONE and notification_recipients:
            raise exceptions.InvalidNotificationRecipients(
                "Notification recipients should be left empty when notification is not to be sent."
            )
        elif notification_type != constants.NotificationType.NONE and not notification_recipients:
            raise exceptions.InvalidNotificationRecipients("Notification recipients should be set.")
        for email in notification_recipients:
            try:
                validate_email(email)
            except ValidationError:
                raise exceptions.InvalidNotificationRecipients("Invalid format.")

    def _validate_conditions(self, changes, conditions):
        if len(conditions) < 1:
            raise exceptions.InvalidRuleConditions("Please define at least one condition")
        errors = []
        for i, condition in enumerate(conditions):
            # NOTE(luka): This code assumes:
            # 1. That every condition contains all fields, even if it's only being updated.
            #    This way we can construct a RuleCondition object and in case of errors
            #    return them along with Rule errors.
            # 2. That conditions are always modified as part of rule update. The design
            #    under this assumption doesn't foresee a separate RuleCondition endpoint.
            condition_errors = {}
            try:
                RuleCondition().clean(condition)
            except utils.exc.MultipleValidationError as err:
                for e in err.errors:
                    if isinstance(e, exceptions.InvalidOperator):
                        condition_errors["operator"] = str(e)
                    if isinstance(e, exceptions.InvalidLeftOperandType):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"]["type"] = str(e)
                    if isinstance(e, exceptions.InvalidLeftOperandModifier):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"]["modifier"] = str(e)
                    if isinstance(e, exceptions.InvalidLeftOperandWindow):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"]["window"] = str(e)
                    if isinstance(e, exceptions.InvalidRightOperandType):
                        condition_errors.setdefault("value", {})
                        condition_errors["value"]["type"] = str(e)
                    if isinstance(e, exceptions.InvalidRightOperandValue):
                        condition_errors.setdefault("value", {})
                        condition_errors["value"]["value"] = str(e)
                    if isinstance(e, exceptions.InvalidRightOperandWindow):
                        condition_errors.setdefault("value", {})
                        condition_errors["value"]["window"] = str(e)
            errors.append(condition_errors)
        if any(errors):
            raise exceptions.InvalidRuleConditions(conditions_errors=errors)
