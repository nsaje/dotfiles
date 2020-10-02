import re
from functools import partial

from django.core.validators import ValidationError
from django.core.validators import validate_email

import utils.exc
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
            partial(self._validate_if_present, "agency"),
            partial(self._validate_if_present, "account"),
            partial(self._validate_if_present, "accounts_included"),
            partial(self._validate_if_present, "campaigns_included"),
            partial(self._validate_if_present, "ad_groups_included"),
            partial(self._validate_agency_account),
            partial(self._validate_included_entities),
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
        if action_type not in config.ADJUSTMENT_ACTION_TYPES and change_step is not None:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidChangeStep(
                f"Change step not expected to be set for action type: {action_type_name}."
            )
        if action_type in config.ADJUSTMENT_ACTION_TYPES:
            action_type_config = config.ADJUSTMENT_ACTION_TYPES[action_type]
            sign = self._get_sign(action_type_config)
            if change_step is None:
                raise exceptions.InvalidChangeStep("Please provide change step")
            elif change_step < action_type_config.min_step:
                min_step = self._get_action_type_min_step_amount(action_type_config)
                raise exceptions.InvalidChangeStep(f"Please provide a value greater or equal to {min_step:.2f}{sign}.")
            elif change_step > action_type_config.max_step:
                max_step = self._get_action_type_max_step_amount(action_type_config)
                raise exceptions.InvalidChangeStep(f"Please provide a value lower than {max_step:.2f}{sign}.")

    def _get_action_type_max_step_amount(self, action_type_config):
        return self._get_action_type_step_value(action_type_config.max_step, action_type_config.type)

    def _get_action_type_min_step_amount(self, action_type_config):
        return self._get_action_type_step_value(action_type_config.min_step, action_type_config.type)

    def _get_action_type_step_value(self, value, type_):
        if type_ == config.ADJUSTMENT_ACTION_TYPE_CURRENCY:
            return value
        elif type_ == config.ADJUSTMENT_ACTION_TYPE_PERCENTAGE:
            return value * 100
        else:
            raise Exception("Unknown type")

    def _validate_change_limit(self, changes, change_limit):
        action_type = changes.get("action_type", self.action_type)
        if action_type not in config.ADJUSTMENT_ACTION_TYPES and change_limit is not None:
            action_type_name = constants.ActionType.get_name(action_type)
            raise exceptions.InvalidChangeLimit(
                f"Change limit not expected to be set for action type: {action_type_name}."
            )
        if action_type in config.ADJUSTMENT_ACTION_TYPES:
            action_type_config = config.ADJUSTMENT_ACTION_TYPES[action_type]
            sign = self._get_sign(action_type_config)
            if change_limit is None:
                raise exceptions.InvalidChangeLimit("Please provide change limit")
            elif change_limit < action_type_config.min_limit:
                min_limit = self._get_action_type_min_limit_amount(action_type_config)
                raise exceptions.InvalidChangeLimit(
                    action_type_config.min_limit_error_message.format(min_limit=min_limit, sign=sign)
                )
            elif change_limit > action_type_config.max_limit:
                max_limit = self._get_action_type_max_limit_amount(action_type_config)
                raise exceptions.InvalidChangeLimit(
                    action_type_config.max_limit_error_message.format(max_limit=max_limit, sign=sign)
                )

    def _get_action_type_max_limit_amount(self, action_type_config):
        return self._get_action_type_limit_value(action_type_config.max_limit, action_type_config.type)

    def _get_action_type_min_limit_amount(self, action_type_config):
        return self._get_action_type_limit_value(action_type_config.min_limit, action_type_config.type)

    def _get_action_type_limit_value(self, value, type_):
        if type_ == config.ADJUSTMENT_ACTION_TYPE_CURRENCY:
            return value
        elif type_ == config.ADJUSTMENT_ACTION_TYPE_PERCENTAGE:
            return (value - 1) * 100
        else:
            raise Exception("Unknown type")

    def _get_sign(self, action_type_config):
        if action_type_config.type == config.ADJUSTMENT_ACTION_TYPE_PERCENTAGE:
            return "%"
        if action_type_config.type == config.ADJUSTMENT_ACTION_TYPE_CURRENCY:
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
                raise exceptions.InvalidSendEmailSubject("Email subject should not contain multiple lines of text.")
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
            if target_type not in config.VALID_TARGET_TYPES_FOR_ACTION[constants.ActionType.ADD_TO_PUBLISHER_GROUP]:
                raise exceptions.InvalidPublisherGroup("Invalid target type")

            agency = changes.get("agency", self.agency)
            account = changes.get("account", self.account)

            if (publisher_group.agency and agency and publisher_group.agency_id != agency.id) or (
                publisher_group.agency and account and publisher_group.agency_id != account.agency.id
            ):
                raise exceptions.InvalidPublisherGroup("Publisher group has to belong to the rule's agency")

            if (publisher_group.account and agency and publisher_group.account.agency_id != agency.id) or (
                publisher_group.account and account and publisher_group.account_id != account.id
            ):
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
                    if isinstance(e, exceptions.InvalidConversionPixel):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"].setdefault("conversion_pixel", []).append(str(e))
                    if isinstance(e, exceptions.InvalidConversionPixelWindow):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"].setdefault("conversion_pixel_window", []).append(str(e))
                    if isinstance(e, exceptions.InvalidConversionPixelAttribution):
                        condition_errors.setdefault("metric", {})
                        condition_errors["metric"].setdefault("conversion_pixel_attribution", []).append(str(e))
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

    def _validate_agency_account(self, changes):
        agency = changes.get("agency", self.agency)
        account = changes.get("account", self.account)

        if agency and account:
            raise exceptions.InvalidParents("Only one of either account or agency must be set.")

        if not agency and not account:
            raise exceptions.InvalidParents("One of either account or agency must be set.")

    def _validate_agency(self, changes, agency):
        if agency is None:
            return

        accounts_included = changes.get("accounts_included", self.accounts_included.all().only("agency_id"))
        if any(account.agency_id != agency.id for account in accounts_included):
            raise exceptions.InvalidAgency("Rule already runs on accounts not belonging to the selected agency.")

        campaigns_included = changes.get("campaigns_included", self.campaigns_included.all().only("account__agency_id"))
        if any(campaign.account.agency_id != agency.id for campaign in campaigns_included):
            raise exceptions.InvalidAgency("Rule already runs on campaigns not belonging to the selected agency.")

        ad_groups_included = changes.get(
            "ad_groups_included", self.ad_groups_included.all().only("campaign__account__agency_id")
        )
        if any(ad_group.campaign.account.agency_id != agency.id for ad_group in ad_groups_included):
            raise exceptions.InvalidAgency("Rule already runs on ad groups not belonging to the selected agency.")

    def _validate_account(self, changes, account):
        if account is None:
            return

        accounts_included = changes.get("accounts_included", self.accounts_included.all().only("id"))
        if any(account_included.id != account.id for account_included in accounts_included):
            raise exceptions.InvalidAccount("Rule already runs on accounts not belonging to the selected account.")

        campaigns_included = changes.get("campaigns_included", self.campaigns_included.all().only("account_id"))
        if any(campaign.account_id != account.id for campaign in campaigns_included):
            raise exceptions.InvalidAccount("Rule already runs on campaigns not belonging to the selected account.")

        ad_groups_included = changes.get(
            "ad_groups_included", self.ad_groups_included.all().only("campaign__account_id")
        )
        if any(ad_group.campaign.account_id != account.id for ad_group in ad_groups_included):
            raise exceptions.InvalidAccount("Rule already runs on ad groups not belonging to the selected account.")

    def _validate_accounts_included(self, changes, accounts_included):
        if not accounts_included:
            return

        agency = changes.get("agency", self.agency)
        account = changes.get("account", self.account)

        if agency:
            if any(account_included.agency_id != agency.id for account_included in accounts_included):
                raise exceptions.InvalidIncludedAccounts("Included accounts have to belong of the rule's agency")

        if account:
            if any(account_included.id != account.id for account_included in accounts_included):
                raise exceptions.InvalidIncludedAccounts(
                    "Included accounts have to belong to an account of the rule's agency"
                )

    def _validate_campaigns_included(self, changes, campaigns_included):
        if not campaigns_included:
            return

        agency = changes.get("agency", self.agency)
        account = changes.get("account", self.account)

        if agency:
            if any(campaign.account.agency_id != agency.id for campaign in campaigns_included):
                raise exceptions.InvalidIncludedCampaigns("Included campaigns have to belong of the rule's agency")

        if account:
            if any(campaign.account.id != account.id for campaign in campaigns_included):
                raise exceptions.InvalidIncludedCampaigns(
                    "Included campaigns have to belong to an account of the rule's agency"
                )

    def _validate_ad_groups_included(self, changes, ad_groups_included):
        if not ad_groups_included:
            return

        agency = changes.get("agency", self.agency)
        account = changes.get("account", self.account)

        if agency:
            if any(ad_group.campaign.account.agency_id != agency.id for ad_group in ad_groups_included):
                raise exceptions.InvalidIncludedAdGroups("Included ad groups have to belong of the rule's agency")

        if account:
            if any(ad_group.campaign.account.id != account.id for ad_group in ad_groups_included):
                raise exceptions.InvalidIncludedAdGroups(
                    "Included ad groups have to belong to an account of the rule's agency"
                )

    def _validate_included_entities(self, changes):
        if self.id:
            accounts_included = changes.get("accounts_included", self.accounts_included.all())
            campaigns_included = changes.get("campaigns_included", self.campaigns_included.all())
            ad_groups_included = changes.get("ad_groups_included", self.ad_groups_included.all())
        else:
            accounts_included = changes.get("accounts_included", [])
            campaigns_included = changes.get("campaigns_included", [])
            ad_groups_included = changes.get("ad_groups_included", [])

        if not (accounts_included or campaigns_included or ad_groups_included):
            raise exceptions.MissingIncludedEntities(
                "Rule must have set either accounts_included, campaigns_included or ad_groups_included"
            )
