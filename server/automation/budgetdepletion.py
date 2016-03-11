import datetime
import logging
import pytz
import traceback
import decimal

import influx

from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import models as authmodels

import automation.models
import automation.settings
import automation.helpers
from utils import pagerduty_helper, url_helper
from utils.statsd_helper import statsd_timer

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


def _allowed_to_automatically_stop_campaign(campaign):
    perm = authmodels.Permission.objects.get(codename='group_campaign_stop_on_budget_depleted')
    return campaign.account.groups.filter(permissions=perm).exists()


def notify_campaign_with_depleting_budget(campaign, available_budget, yesterdays_spend):
    campaign_manager = campaign.get_current_settings().campaign_manager
    sales_rep = campaign.get_sales_representative()
    emails = []
    if campaign_manager is not None:
        emails.append(campaign_manager.email)
    if sales_rep is not None:
        emails.append(sales_rep.email)
    total_daily_budget = automation.helpers.get_total_daily_budget_amount(campaign)
    campaign_url = url_helper.get_full_z1_url('/campaigns/{}/budget'.format(campaign.pk))

    _send_depleting_budget_notification_email(
        campaign.name,
        campaign_url,
        campaign.account.name,
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
        campaign_name,
        campaign_url,
        account_name,
        emails,
        available_budget,
        yesterdays_spend,
        total_daily_budget
        ):
    body = u'''Hi account manager of {camp}

We'd like to notify you that campaign {camp}, {account} is about to run out of available budget.

The available budget remaining today is ${avail}, current daily cap is ${cap} and yesterday's spend was ${yest}.

Please check {camp_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=campaign_url,
        avail=_round_budget(available_budget),
        cap=_round_budget(total_daily_budget),
        yest=_round_budget(yesterdays_spend)
    )
    try:
        send_mail(
            u'Campaign budget low - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            'Zemanta <{}>'.format(automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(u'Budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         ', '.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ''.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_budget_depletion_notification_email',
            description='Budget depletion e-mail for campaign was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )


def _round_budget(budget):
    return decimal.Decimal(budget).quantize(
        decimal.Decimal('0.01'),
        rounding=decimal.ROUND_HALF_UP)


def _send_campaign_stopped_notification_email(
        campaign_name,
        campaign_url,
        account_name,
        emails
        ):
    body = u'''Hi account manager of {camp}

We'd like to notify you that campaign {camp}, {account} has run out of available budget and was stopped.

Please check {camp_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        camp=campaign_name,
        account=account_name,
        camp_url=campaign_url
    )
    try:
        send_mail(
            'Campaign stopped - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            'Zemanta <{}>'.format(automation.settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL),
            emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception('Campaign stop because of budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         ', '.join(emails))
        desc = {
            'campaign_name': campaign_name,
            'email': ', '.join(emails)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='automation_budget_stop_notification_email',
            description='Campaign stop because of budget depletion e-mail was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )


@influx.timer('automation.budgetdepletion.budget_campaigns', operation='notify_depleting')
@statsd_timer('automation.budgetdepletion', 'notify_depleting_budget_campaigns')
def notify_depleting_budget_campaigns():
    campaigns = automation.helpers.get_active_campaigns()
    available_budgets = automation.helpers.get_available_budgets(campaigns)
    yesterdays_spends = automation.helpers.get_yesterdays_spends(campaigns)

    for camp in campaigns:
        if budget_is_depleting(available_budgets.get(camp.id), yesterdays_spends.get(camp.id)) and \
                not manager_has_been_notified(camp):
            notify_campaign_with_depleting_budget(
                camp,
                available_budgets.get(camp.id),
                yesterdays_spends.get(camp.id)
            )


@influx.timer('automation.budgetdepletion.budget_campaigns', operation='stop_and_notify_depleted')
@statsd_timer('automation.budgetdepletion', 'stop_and_notify_depleted_budget_campaigns')
def stop_and_notify_depleted_budget_campaigns():
    campaigns = automation.helpers.get_active_campaigns()
    available_budgets = automation.helpers.get_available_budgets(campaigns)
    yesterdays_spends = automation.helpers.get_yesterdays_spends(campaigns)

    for camp in campaigns:
        if not _allowed_to_automatically_stop_campaign(camp):
            continue
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
    emails = []
    if campaign_manager is not None:
        emails.append(campaign_manager.email)
    if sales_rep is not None:
        emails.append(sales_rep.email)

    campaign_url = url_helper.get_full_z1_url('/campaigns/{}/budget'.format(campaign.pk))
    _send_campaign_stopped_notification_email(
        campaign.name,
        campaign_url,
        campaign.account.name,
        emails
        )
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=campaign_manager,
        stopped=True).save()
