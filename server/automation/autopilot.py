import logging
import dash
from decimal import Decimal
from automation import models
import datetime
import pytz
from django.conf import settings
logger = logging.getLogger(__name__)


def update_ad_group_source_cpc(ad_group_source, new_cpc):
    # TODO: only actually change cpc if CPC actually changed
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    resource = dict()
    resource['cpc_cc'] = new_cpc
    settings_writer.set(resource, None)


def persist_cpc_change_to_admin_log(ad_group_source, yesterday_spend, previous_cpc, new_cpc, daily_budget):
    models.AutopilotAdGroupSourceBidCpcLog(
        campaign=ad_group_source.ad_group.campaign,
        ad_group=ad_group_source.ad_group,
        ad_group_source=ad_group_source,
        yesterdays_spend_cc=yesterday_spend,
        previous_cpc_cc=previous_cpc,
        new_cpc_cc=new_cpc,
        current_daily_budget_cc=daily_budget
    ).save()


def ad_group_sources_daily_budget_was_changed_recently(ad_group_source):
    now_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    now = now_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    yesterday = datetime.datetime(now.year, now.month, now.day) - datetime.timedelta(days=1)
    current_budget = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source=ad_group_source
        ).latest('created_dt').daily_budget_cc
    source_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source=ad_group_source,
        created_dt__gte=yesterday,
        created_dt__lte=now
        )
    for setting in source_settings:
        if setting.daily_budget_cc != current_budget:
            return True
    return False


def get_autopilot_ad_group_sources_settings(adgroup):
    autopilot_sources_settings = []
    all_ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=adgroup)
    for current_source_settings in dash.views.helpers.get_ad_group_sources_settings(all_ad_group_sources):
        if (current_source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE):
                #and current_source_settings.autopilot): TODO: Remove comment!
            autopilot_sources_settings.append(current_source_settings)
    return autopilot_sources_settings


def calculate_new_autopilot_cpc(current_cpc, current_daily_budget, yesterdays_spend):
    spending_perc = float(yesterdays_spend) / float(current_daily_budget) - 1
    for row in settings.AUTOPILOT_CPC_CHANGE_TABLE:
        cpc_adjustment_multiplier = 0
        if row[0] <= spending_perc <= row[1]:
            cpc_adjustment_multiplier = row[2]
            break
    # TODO: Maybe add AUTOPILOT_OVERSPENDING_PANIC_LIMIT, and send email if overspending is higher than it?
    return current_cpc + current_cpc * cpc_adjustment_multiplier
