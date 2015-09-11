import logging
import dash
from automation import models
import datetime
import pytz
import decimal
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger(__name__)


def update_ad_group_source_cpc(ad_group_source, new_cpc):
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
    try:
        current_budget = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source
            ).latest('created_dt').daily_budget_cc
        budget_before_yesterday_midnight = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source
            ).filter(
            created_dt__lte=yesterday,
            ).latest('created_dt').daily_budget_cc
    except ObjectDoesNotExist:
        return True

    if current_budget != budget_before_yesterday_midnight:
        return True

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
        if (current_source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE
                and current_source_settings.autopilot):
            autopilot_sources_settings.append(current_source_settings)
    return autopilot_sources_settings


def calculate_new_autopilot_cpc(current_cpc, current_daily_budget, yesterdays_spend):
    if current_cpc < 0:
        return decimal.Decimal(0)
    if any([
        current_daily_budget is None,
        yesterdays_spend is None,
        current_cpc is None,
        current_daily_budget <= 0,
        yesterdays_spend <= 0
    ]):
        return current_cpc
    if type(current_daily_budget) != float:
        current_daily_budget = float(current_daily_budget)
    if type(yesterdays_spend) != float:
        yesterdays_spend = float(yesterdays_spend)
    if type(current_cpc) != decimal.Decimal:
        current_cpc = decimal.Decimal(current_cpc)
    spending_perc = yesterdays_spend / current_daily_budget - 1
    for row in settings.AUTOPILOT_CPC_CHANGE_TABLE:
        if row[0] <= spending_perc <= row[1]:
            current_cpc += current_cpc * decimal.Decimal(row[2])
            current_cpc = current_cpc.quantize(
                decimal.Decimal('0.01'),
                rounding=decimal.ROUND_HALF_UP)
            break
    # TODO: Maybe add AUTOPILOT_OVERSPENDING_PANIC_LIMIT, and send email if overspending is higher than it?
    # TODO: What to do with Lorand's suggestion of minimum CPC for autopilot?
    return current_cpc
