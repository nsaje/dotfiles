from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from django.conf import settings

import core.features.bcm
import dash.constants
import zemauth.models
from utils import email_helper
from utils import zlogging

from . import models

logger = zlogging.getLogger(__name__)


def check_and_notify_depleting_credits() -> None:
    credits: Iterable[core.features.bcm.CreditLineItem] = (
        core.features.bcm.CreditLineItem.objects.exclude(account_id=settings.HARDCODED_ACCOUNT_ID_OEN)
        .exclude(agency_id=settings.HARDCODED_AGENCY_ID_OUTBRAIN)
        .filter_active()
        .select_related("account__settings", "agency")
    )
    for credit in credits:
        _check_credit(credit)


def _check_credit(credit: core.features.bcm.CreditLineItem):
    notifications, _ = models.CreditNotifications.objects.get_or_create(credit=credit)
    budgets_spend = credit.get_total_budgets_spend()
    credit_spend_percent = budgets_spend / credit.amount
    agency_or_user = credit.agency or credit.account.settings.default_account_manager
    recipients = _get_recipients(credit)
    if credit_spend_percent > 0.9:
        if not notifications.sent_90_percent:
            template_type = dash.constants.EmailTemplateType.CREDIT_DEPLETED_90_PERCENT
            logger.info(
                "Sending credit notification email",
                template_type=dash.constants.EmailTemplateType.get_name(template_type),
                credit_id=credit.id,
                recipients=",".join(recipients),
                credit_amount=str(credit.amount),
                budgets_spend=str(budgets_spend),
                credit_spend_percent=str(credit_spend_percent),
            )
            _send_email_from_template(agency_or_user, recipients, template_type, template_params={"credit": credit})
            notifications.set_all()
    elif credit_spend_percent > 0.8:
        if not notifications.sent_80_percent:
            template_type = dash.constants.EmailTemplateType.CREDIT_DEPLETED_80_PERCENT
            logger.info(
                "Sending credit notification email",
                template_type=dash.constants.EmailTemplateType.get_name(template_type),
                credit_id=credit.id,
                recipients=",".join(recipients),
                credit_amount=str(credit.amount),
                budgets_spend=str(budgets_spend),
                credit_spend_percent=str(credit_spend_percent),
            )
            _send_email_from_template(agency_or_user, recipients, template_type, template_params={"credit": credit})
            notifications.set_sent_80_percent()
        if notifications.sent_90_percent:
            notifications.unset_sent_90_percent()
    else:
        if notifications.sent_80_percent or notifications.sent_90_percent:
            notifications.unset_all()


def _get_recipients(credit: core.features.bcm.CreditLineItem):
    recipients = []
    if credit.agency:
        if credit.agency.sales_representative:
            recipients.append(credit.agency.sales_representative.email)
        if credit.agency.cs_representative:
            recipients.append(credit.agency.cs_representative.email)
    elif credit.account:
        if credit.account.settings.default_account_manager:
            recipients.append(credit.account.settings.default_account_manager.email)
        if credit.account.settings.default_sales_representative:
            recipients.append(credit.account.settings.default_sales_representative.email)
        if credit.account.settings.default_cs_representative:
            recipients.append(credit.account.settings.default_cs_representative.email)
    return recipients


def _send_email_from_template(
    agency_or_user: zemauth.models.User, recipients: List[str], template_type: int, *, template_params: Dict[Any, Any]
):
    params = email_helper.params_from_template(template_type, **template_params)
    email_helper.send_official_email(agency_or_user=agency_or_user, recipient_list=recipients, **params)
