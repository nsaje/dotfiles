import re
from functools import partial

from django.core.validators import ValidationError
from django.core.validators import validate_email

import utils.validation_helper

from ... import config
from ... import constants
from ... import exceptions
from ...common import macros
from ..rule_condition import RuleCondition

EMAIL_CONTAINS_NESTED_MACRO_REGEX = re.compile(r"{[^}]*{")
EMAIL_EXTRACT_MACROS_REGEX = re.compile(r"{([^}]*)}")
EMAIL_MACRO_WITHOUT_WINDOW_REGEX = re.compile(r"(.*)_LAST_(?:\d+_)?DAYS?$")


class RuleValidationMixin:
    def clean(self, changes):
        utils.validation_helper.validate_multiple(
            partial(self._validate_if_present, "state"),
            partial(self._validate_if_present, "target_type"),
            partial(self._validate_if_present, "action_type"),
            partial(self._validate_if_present, "cooldown"),
            partial(self._validate_if_present, "window"),
            partial(self._validate_if_present, "send_email_subject"),
            partial(self._validate_if_present, "send_email_body"),
            partial(self._validate_if_present, "send_email_recipients"),
            partial(self._validate_if_present, "change_step"),
            partial(self._validate_if_present, "change_limit"),
            partial(self._validate_if_present, "publisher_group"),
            partial(self._validate_if_present, "conditions"),
            partial(self._validate_if_present, "notification_type"),
            partial(self._validate_if_present, "notification_recipients"),
            changes=changes,
        )

    def _validate_if_present(self, key, changes):
        if key in changes:
            getattr(self, "_validate_" + key)(changes, changes[key])

    def _validate_state(self, changes, state):
        if state not in constants.RuleState.get_all():
            raise exceptions.InvalidRuleState("Invalid state")

    def _validate_cooldown(self, changes, cooldown):
        if not cooldown or cooldown % 24 != 0:
            raise exceptions.InvalidCooldown("Invalid action frequency")

    def _validate_window(self, changes, window):
        if window not in constants.MetricWindow.get_all():
            raise exceptions.InvalidWindow("Invalid time range")

    def _validate_target_type(self, changes, target_type):
        if len(config.VALID_ACTION_TYPES_FOR_TARGET.get(target_type, [])) == 0:
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
            raise exceptions.InvalidChangeStep(
                f"Change step not expected to be set for action type: {action_type_name}."
            )
        if action_type in config.ADJUSTEMENT_ACTION_TYPES:
            action_type_config = config.ADJUSTEMENT_ACTION_TYPES[action_type]
            if change_step is None:
                raise exceptions.InvalidChangeStep("Please provide change step")
            elif change_step < action_type_config.min_step:
                raise exceptions.InvalidChangeStep(
                    f"Change step is too small. Please provide a value greater or equal to {action_type_config.min_step:.2f}{self._get_sign(action_type_config)}."
                )
            elif change_step > action_type_config.max_step:
                raise exceptions.InvalidChangeStep(
                    f"Change step is too big. Please provide a value lower than {action_type_config.max_step:.2f}{self._get_sign(action_type_config)}."
                )

    def _validate_change_limit(self, changes, change_limit):
        action_type = changes.get("action_type", self.action_type)
        if action_type not in config.ADJUSTEMENT_ACTION_TYPES and change_limit is not None:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidChangeLimit(
                f"Change limit not expected to be set for action type: {action_type_name}."
            )
        if action_type in config.ADJUSTEMENT_ACTION_TYPES:
            action_type_config = config.ADJUSTEMENT_ACTION_TYPES[action_type]
            if change_limit is None:
                raise exceptions.InvalidChangeLimit("Please provide change limit")
            elif change_limit < action_type_config.min_limit:
                raise exceptions.InvalidChangeLimit(
                    f"Change limit is too small. Please provide a value greater or equal to {action_type_config.min_limit:.2f}{self._get_sign(action_type_config)}."
                )
            elif change_limit > action_type_config.max_limit:
                raise exceptions.InvalidChangeLimit(
                    f"Change limit is too big. Please provide a value lower than {action_type_config.max_limit:.2f}{self._get_sign(action_type_config)}."
                )

    def _get_sign(self, action_type_config):
        if action_type_config.sign == "percentage":
            return "%"
        if action_type_config.sign == "currency":
            return "$"
        return ""

    def _validate_send_email_subject(self, changes, send_email_subject):
        action_type = changes.get("action_type", self.action_type)
        if action_type == constants.ActionType.SEND_EMAIL and not send_email_subject:
            raise exceptions.InvalidSendEmailSubject("Please provide email subject.")
        elif action_type != constants.ActionType.SEND_EMAIL and send_email_subject:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidSendEmailSubject(
                f"Email subject not expected to be set for action type {action_type_name}."
            )
        elif send_email_subject:
            if "\n" in send_email_subject or "\r" in send_email_subject:
                raise exceptions.InvalidSendEmailSubject(f"Email subject should not contain multiple lines of text.")
            try:
                macros.validate(send_email_subject)
            except exceptions.InvalidMacros as e:
                raise exceptions.InvalidSendEmailSubject(str(e))

    def _validate_send_email_body(self, changes, send_email_body):
        action_type = changes.get("action_type", self.action_type)
        if action_type == constants.ActionType.SEND_EMAIL and not send_email_body:
            raise exceptions.InvalidSendEmailBody("Please provide email body.")
        elif action_type != constants.ActionType.SEND_EMAIL and send_email_body:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidSendEmailBody(
                f"Email body not expected to be set for action type {action_type_name}."
            )
        elif send_email_body:
            try:
                macros.validate(send_email_body)
            except exceptions.InvalidMacros as e:
                raise exceptions.InvalidSendEmailBody(str(e))

    def _validate_send_email_recipients(self, changes, send_email_recipients):
        action_type = changes.get("action_type", self.action_type)
        if action_type == constants.ActionType.SEND_EMAIL and not send_email_recipients:
            raise exceptions.InvalidSendEmailRecipients("Please provide email recipients.")
        elif action_type != constants.ActionType.SEND_EMAIL and send_email_recipients:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidSendEmailRecipients(
                f"Email recipients not expected to be set for action type {action_type_name}."
            )

        try:
            self._validate_email_list(send_email_recipients)
        except ValidationError:
            raise exceptions.InvalidSendEmailRecipients("Invalid format.")

    def _validate_notification_type(self, changes, notification_type):
        action_type = changes.get("action_type", self.action_type)
        if notification_type != constants.NotificationType.NONE and action_type == constants.ActionType.SEND_EMAIL:
            raise exceptions.InvalidNotificationType('Notification cannot be sent for "Send email" action')

    def _validate_notification_recipients(self, changes, notification_recipients):
        notification_type = changes.get("notification_type", self.notification_type)
        if notification_type == constants.NotificationType.NONE and notification_recipients:
            raise exceptions.InvalidNotificationRecipients(
                "Notification recipients should be left empty when notification is not to be sent."
            )
        elif notification_type != constants.NotificationType.NONE and not notification_recipients:
            raise exceptions.InvalidNotificationRecipients("Please provide at least one email recipient.")

        try:
            self._validate_email_list(notification_recipients)
        except ValidationError:
            raise exceptions.InvalidNotificationRecipients("Invalid format.")

    def _validate_email_list(self, email_list):
        for email in email_list:
            validate_email(email)

    def _validate_publisher_group(self, changes, publisher_group):
        action_type = changes.get("action_type", self.action_type)
        if action_type != constants.ActionType.ADD_TO_PUBLISHER_GROUP:
            if publisher_group:
                raise exceptions.InvalidPublisherGroup("Invalid action type")
        else:
            if not publisher_group:
                raise exceptions.InvalidPublisherGroup("Please specify a publisher group.")

            target_type = changes.get("target_type", self.target_type)
            if target_type != constants.TargetType.PUBLISHER:
                raise exceptions.InvalidPublisherGroup("Invalid target type")

            if publisher_group.agency and publisher_group.agency_id != self.agency_id:
                raise exceptions.InvalidPublisherGroup("Publisher group has to belong to the rule's agency")
            if publisher_group.account and publisher_group.account.agency_id != self.agency_id:
                raise exceptions.InvalidPublisherGroup(
                    "Publisher group has to belong to an account of the rule's agency"
                )

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
