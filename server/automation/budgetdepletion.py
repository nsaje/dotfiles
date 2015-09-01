import datetime
import logging
from dash import budget, models, constants
import reports.api
import automation.models
from django.db.models import Q
import pytz
from django.conf import settings
import traceback
from django.core.mail import send_mail
from utils import pagerduty_helper
logger = logging.getLogger(__name__)


def manager_has_been_notified(campaign):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(
        pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = today - datetime.timedelta(days=1, hours=-1)
    account_manager = campaign.get_current_settings().account_manager
    return automation.models.CampaignBudgetDepletionNotification.objects.filter(
        Q(campaign=campaign),
        Q(account_manager=account_manager),
        Q(created_dt__gte=yesterday)).count() > 0


def notify_campaign_with_depleting_budget(campaign, available_budget, yesterdays_spend):
    account_manager = campaign.get_current_settings().account_manager
    campaign_url = settings.BASE_URL + '/campaigns/{}/ad_groups'.format(campaign.pk)
    _send_depleted_budget_notification_email(
        campaign.name,
        campaign_url,
        campaign.account.name,
        account_manager.email)
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=account_manager).save()


def budget_is_depleting(available_budget, yesterdays_spend):
    return (available_budget < yesterdays_spend * settings.DEPLETING_AVAILABLE_BUDGET_SCALAR) & (yesterdays_spend > 0)


def get_yesterdays_spends(campaigns):
    return {campaign.id:
            sum(reports.api.get_yesterday_cost(campaign=campaign).values())
            for campaign in campaigns}


def get_available_budgets(campaigns):
    total_budgets = _get_total_budgets(campaigns)
    total_spends = _get_total_spends(campaigns)
    return {k: float(total_budgets[k]) - float(total_spends[k])
            for k in total_budgets if k in total_spends}


def _get_total_budgets(campaigns):
    return {campaign.id: budget.CampaignBudget(campaign).get_total()
            for campaign in campaigns}


def _get_total_spends(campaigns):
    return {campaign.id: budget.CampaignBudget(campaign).get_spend()
            for campaign in campaigns}


def get_active_campaigns():
    return _get_active_campaigns_subset(models.Campaign.objects.all())


def _get_active_campaigns_subset(campaigns):
    for campaign in campaigns:
        adgroups = models.AdGroup.objects.filter(campaign=campaign)
        is_active = False
        for adgroup in adgroups:
            adgroup_settings = adgroup.get_current_settings()
            if adgroup_settings.state == constants.AdGroupSettingsState.ACTIVE and \
                    not adgroup_settings.archived and \
                    not adgroup.is_demo:
                is_active = True
                break
        if not is_active:
            campaigns = campaigns.exclude(pk=campaign.pk)
    return campaigns


def _send_depleted_budget_notification_email(campaign_name, campaign_url, account_name, email):
    body = u'''Hi account manager of {camp}

We'd like to notify you that campaign {camp}, {account} is about to run out of available budget.
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
            'Campaign budget low - {camp}, {account}'.format(
                camp=campaign_name,
                account=account_name
            ),
            body,
            'Zemanta <{}>'.format(settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL),
            settings.DEPLETING_CAMPAIGN_BUDGET_DEBUGGING_EMAILS,
            fail_silently=False
        )
    except Exception as e:
        logger.exception('Budget depletion e-mail for campaign %s to %s was not sent because an exception was raised:',
                         campaign_name,
                         email)
        desc = {
            'campaign_name': campaign_name,
            'email': email
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='Budget depletion e-mail for campaign was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc
        )
