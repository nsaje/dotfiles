import datetime
import logging
import pytz
import decimal

import influx

from django.db.models import Q
from django.conf import settings
from dash.constants import EmailTemplateType

import automation.models
import automation.settings
import automation.helpers
from utils import url_helper, email_helper

logger = logging.getLogger(__name__)


def manager_has_been_notified(campaign):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(
        pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = today - datetime.timedelta(days=1, hours=-1)
    campaign_manager = campaign.get_current_settings().campaign_manager
    return automation.models.CampaignBudgetDepletionNotification.objects.filter(
        Q(campaign=campaign),
        Q(account_manager=campaign_manager),
        Q(created_dt__gte=yesterday)).count() > 0


def notify_campaign_with_depleting_budget(campaign, available_budget, yesterdays_spend):
    campaign_manager = campaign.get_current_settings().campaign_manager
    sales_rep = campaign.get_sales_representative()
    emails = email_helper.email_manager_list(campaign)
    if sales_rep is not None:
        emails.append(sales_rep.email)

    total_daily_budget = automation.helpers.get_total_daily_budget_amount(campaign)
    campaign_url = url_helper.get_full_z1_url(
        '/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings'.format(campaign.pk)
    )

    _send_depleting_budget_notification_email(
        campaign,
        campaign_url,
        emails,
        available_budget,
        yesterdays_spend,
        total_daily_budget)
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=campaign_manager).save()


def budget_is_depleting(available_budget, yesterdays_spend):
    return (available_budget < yesterdays_spend * automation.settings.DEPLETING_AVAILABLE_BUDGET_SCALAR) and (yesterdays_spend > 0)


def _send_depleting_budget_notification_email(
        campaign,
        campaign_url,
        emails,
        available_budget,
        yesterdays_spend,
        total_daily_budget
):
    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': campaign_url,
        'available_budget': _round_budget(available_budget),
        'cap': _round_budget(total_daily_budget),
        'yesterday_spend': _round_budget(yesterdays_spend)
    }

    try:
        email_helper.send_official_email(
            agency_or_user=campaign.account.agency,
            recipient_list=emails,
            from_email=automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL,
            **email_helper.params_from_template(
                EmailTemplateType.BUDGET_DEPLETING, **args
            )
        )
    except Exception:
        logger.exception(u'Budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign.name,
                         ', '.join(emails))


def _round_budget(budget):
    return decimal.Decimal(budget).quantize(
        decimal.Decimal('0.01'),
        rounding=decimal.ROUND_HALF_UP)


def _send_campaign_stopped_notification_email(
        campaign,
        campaign_url,
        emails
):
    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': campaign_url,
    }
    try:
        email_helper.send_official_email(
            agency_or_user=campaign.account.agency,
            recipient_list=emails,
            from_email=automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL,
            **email_helper.params_from_template(
                EmailTemplateType.CAMPAIGN_STOPPED, **args
            )
        )
    except Exception:
        logger.exception('Campaign stop because of budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign.name,
                         ', '.join(emails))


def _is_automatic_campaign_stop_disabled(camp):
    return not camp.get_current_settings().automatic_campaign_stop


@influx.timer('automation.budgetdepletion.budget_campaigns', operation='notify_depleting')
def notify_depleting_budget_campaigns():
    campaigns = automation.helpers.get_active_campaigns()
    available_budgets = automation.helpers.get_available_budgets(campaigns)
    yesterdays_spends = automation.helpers.get_yesterdays_spends(campaigns)

    for camp in campaigns:
        budgets = available_budgets.get(camp.id)
        spends = yesterdays_spends.get(camp.id)
        if _is_automatic_campaign_stop_disabled(camp) and budget_is_depleting(budgets, spends) and not manager_has_been_notified(camp):
            notify_campaign_with_depleting_budget(
                camp,
                available_budgets.get(camp.id),
                yesterdays_spends.get(camp.id)
            )


@influx.timer('automation.budgetdepletion.budget_campaigns', operation='stop_and_notify_depleted')
def stop_and_notify_depleted_budget_campaigns():
    campaigns = automation.helpers.get_active_campaigns()
    available_budgets = automation.helpers.get_available_budgets(campaigns)
    yesterdays_spends = automation.helpers.get_yesterdays_spends(campaigns)

    for camp in campaigns:
        if available_budgets.get(camp.id) <= 0:
            automation.helpers.stop_campaign(camp)
            _notify_depleted_budget_campaign_stopped(
                camp,
                available_budgets.get(camp.id),
                yesterdays_spends.get(camp.id)
            )


def _notify_depleted_budget_campaign_stopped(campaign, available_budget, yesterdays_spend):
    campaign_manager = campaign.get_current_settings().campaign_manager
    sales_rep = campaign.get_sales_representative()

    emails = email_helper.email_manager_list(campaign)
    if sales_rep is not None:
        emails.append(sales_rep.email)

    campaign_url = url_helper.get_full_z1_url(
        '/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings'.format(campaign.pk)
    )
    _send_campaign_stopped_notification_email(
        campaign,
        campaign_url,
        emails
    )
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=campaign_manager,
        stopped=True).save()
