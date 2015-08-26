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
logger = logging.getLogger(__name__)


def manager_has_been_notified(campaign):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = today - datetime.timedelta(days=1, hours=-1)
    account_manager = campaign.get_current_settings().account_manager
    return automation.models.CampaignBudgetDepletionNotification.objects.filter(
        Q(campaign=campaign),
        Q(account_manager=account_manager),
        Q(created_dt__gte=yesterday)).count() > 0


def notify_campaign_with_depleting_budget(campaign, available_budget, yesterdays_spend):
    account_manager = campaign.get_current_settings().account_manager
    _send_depleted_budget_notification_email(account_manager.first_name, account_manager.email, campaign.name)
    automation.models.CampaignBudgetDepletionNotification(
        campaign=campaign,
        available_budget=available_budget,
        yesterdays_spend=yesterdays_spend,
        account_manager=account_manager).save()


def budget_is_depleting(available_budget, yesterdays_spend):
    return (available_budget < yesterdays_spend * settings.DEPLETING_AVAILABLE_BUDGET_SCALAR) & (yesterdays_spend > 0)


def get_yesterdays_spends(campaigns):
    return {campaign.id: sum(reports.api.get_yesterday_cost(campaign=campaign).values()) for campaign in campaigns}


def get_available_budgets(campaigns):
    total_budgets = _get_total_budgets(campaigns)
    total_spends = _get_total_spends(campaigns)
    return {k: float(total_budgets[k]) - float(total_spends[k]) for k in total_budgets if k in total_spends}


def _get_total_budgets(campaigns):
    return {campaign.id: budget.CampaignBudget(campaign).get_total() for campaign in campaigns}


def _get_total_spends(campaigns):
    return {campaign.id: budget.CampaignBudget(campaign).get_spend() for campaign in campaigns}


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


def _send_depleted_budget_notification_email(first_name, email, campaign_name):
    body = u'''<p>Hi {name},</p>
<p>
Your campaign {camp} is about to run out of available budget.
</p>
<p>
As always, please don't hesitate to contact help@zemanta.com with any questions.
</p>
<p>
Thanks,<br/>
Zemanta Client Services
</p>
    '''

    body = body.format(
        name=first_name,
        camp=campaign_name
    )
    try:
        send_mail(
            '{} - Campaign budget depletion approaching'.format(campaign_name),
            body,
            'Zemanta <{}>'.format(settings.DEPLETING_CAMPAIGN_BUDGET_EMAIL),
            ['davorin.kopic@zemanta.com','bostjan@zemanta.com'],
            fail_silently=False
        ) #Emails will initially only be sent to davorin and bostjan for testing
    except Exception as e:
        logger.error('Budget depletion e-mail for campaign %s to %s was not sent because an exception was raised: %s', campaign_name, email, traceback.format_exc(e))
