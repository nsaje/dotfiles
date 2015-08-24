import datetime
import logging
from dash import budget, models, constants
from django.core.management.base import BaseCommand
import reports.api
import automation.models
import actionlog.api
#import utils.email_helper
from django.db.models import Q
import pytz
from django.conf import settings

availableBudgetScaler = 1.0
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Notifying depleted budget campaigns.')
        campaigns = _get_active_campaigns(models.Campaign.objects.all())
        total_budgets = {campaign.id: budget.CampaignBudget(campaign).get_total() for campaign in campaigns}
        total_spends = {campaign.id: budget.CampaignBudget(campaign).get_spend() for campaign in campaigns}
        available_budgets = {k: float(total_budgets[k]) - float(total_spends[k]) for k in total_budgets if k in total_spends}
        yesterdays_spends = {campaign.id: sum(reports.api.get_yesterday_cost(campaign=campaign).values()) for campaign in campaigns}

        today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
        today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
        yesterday = today - datetime.timedelta(days=1, hours=-1)

        for camp, avail in available_budgets.iteritems():
            if (avail < yesterdays_spends.get(camp) * availableBudgetScaler) & (yesterdays_spends.get(camp) > 0):
                print 'sending email', camp, avail, yesterdays_spends.get(camp)
                account_manager = getattr(actionlog.api._get_campaign_settings(camp), 'account_manager')
                if automation.models.CampaignBudgetDepletionNotifaction.objects.filter(
                        Q(campaign=campaigns.get(pk=camp)),
                        Q(account_manager=account_manager),
                        Q(created_dt__gte=yesterday)).count() < 1:
                    #utils.email_helper.send_depleted_budget_notification_email(account_manager, campaigns.get(pk=camp))
                    notifLog = automation.models.CampaignBudgetDepletionNotifaction(
                        campaign=campaigns.get(pk=camp),
                        available_budget=avail,
                        yesterdays_spend=yesterdays_spends.get(camp),
                        account_manager=account_manager)
                    notifLog.save()


def _get_active_campaigns(campaigns):
    for campaign in campaigns:
        adgroups = models.AdGroup.objects.filter(campaign=campaign)
        isActive = False
        for adgroup in adgroups:
            try:
                adgroup_settings = adgroup.get_current_settings()
                if getattr(adgroup_settings, 'state') == constants.AdGroupSettingsState.ACTIVE and \
                        not getattr(adgroup_settings, 'archived') and \
                        not getattr(adgroup, 'is_demo'):
                    isActive = True
                    break
            except Exception:
                continue
        if not isActive:
            campaigns = campaigns.exclude(pk=campaign.pk)
    return campaigns
