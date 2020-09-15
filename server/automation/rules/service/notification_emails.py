from typing import Dict
from typing import List

from django.conf import settings

import core.models
import dash.constants
from utils import email_helper

from .. import Rule
from .. import RuleHistory
from .. import constants


def send_notification_email_if_enabled(rule: Rule, ad_group: core.models.AdGroup, history: RuleHistory):
    if rule.notification_type == constants.NotificationType.NONE:
        return

    if history.status == constants.ApplyStatus.SUCCESS:
        _send_changes_email(rule, ad_group, history)
    elif rule.notification_type == constants.NotificationType.ON_RULE_RUN:
        if history.status == constants.ApplyStatus.FAILURE:
            _send_exception_email(rule, ad_group, history)
        elif history.status == constants.ApplyStatus.SUCCESS_NO_CHANGES:
            _send_no_action_email(rule, ad_group)


def _send_changes_email(rule: Rule, ad_group: core.models.AdGroup, history: RuleHistory):
    changes_text = history.get_formatted_changes()

    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_RUN,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
            "changes_text": changes_text,
        },
    )


def _send_exception_email(rule: Rule, ad_group: core.models.AdGroup, history: RuleHistory):
    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_ERRORS,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
            "history_link": history.get_dashboard_link(),
        },
    )


def _send_no_action_email(rule: Rule, ad_group: core.models.AdGroup):
    _send_email_from_template(
        ad_group.campaign.account.agency,
        rule.notification_recipients,
        dash.constants.EmailTemplateType.AUTOMATION_RULE_NO_CHANGES,
        {
            "rule_name": rule.name,
            "ad_group_name": ad_group.name,
            "ad_group_link": settings.BASE_URL + f"/v2/analytics/adgroup/{ad_group.id}",
        },
    )


def _send_email_from_template(
    agency: core.models.Agency, recipient_list: List[str], template_type: int, template_params: Dict[str, str]
):
    for recipient in recipient_list:
        email_helper.send_official_email(
            agency_or_user=agency,
            recipient_list=[recipient],
            **email_helper.params_from_template(template_type, **template_params),
        )
