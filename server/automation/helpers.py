import datetime
import pytz

from django.conf import settings
from django.db import transaction

import dash
import dash.constants
import decimal
import reports.api
import dash.views.helpers
import actionlog.api
import utils.dates_helper
from actionlog import zwei_actions


def get_yesterdays_spends(campaigns):
    yesterday = utils.dates_helper.local_today() - datetime.timedelta(1)
    spends = {
        campaign.id: _get_total_campaign_spend(campaign, yesterday)
        for campaign in campaigns
    }

    return spends


def get_available_budgets(campaigns):
    available_budgets = {
        campaign.id: decimal.Decimal(_get_total_available_budget(campaign))
        for campaign in campaigns
    }

    return available_budgets


def _get_total_available_budget(campaign, date=None):
    date = date or utils.dates_helper.local_today()
    return sum(
        budget.get_available_amount(date) for budget in campaign.budgets.all()
        if budget.state() == dash.constants.BudgetLineItemState.ACTIVE
    )


def _get_total_campaign_spend(campaign, date=None):
    date = date or utils.dates_helper.local_today()
    return sum(
        decimal.Decimal(budget.get_daily_spend(date, use_decimal=True)['total'])
        for budget in campaign.budgets.all()
        if budget.state() == dash.constants.BudgetLineItemState.ACTIVE
    )


def get_active_campaigns():
    return _get_active_campaigns_subset(dash.models.Campaign.objects.all())


def _get_active_campaigns_subset(campaigns):
    for campaign in campaigns:
        adgroups = dash.models.AdGroup.objects.filter(campaign=campaign)
        is_active = False
        for adgroup in adgroups:
            if _is_ad_group_active(adgroup):
                is_active = True
                break
        if not is_active:
            campaigns = campaigns.exclude(pk=campaign.pk)
    return campaigns


def get_active_ad_groups(campaign):
    active_ad_groups = []
    for adg in campaign.adgroup_set.all():
        if _is_ad_group_active(adg):
            active_ad_groups.append(adg)
    return active_ad_groups


def get_all_active_ad_groups():
    active_ad_groups = []
    for adg in dash.models.AdGroup.objects.all():
        if _is_ad_group_active(adg):
            active_ad_groups.append(adg)
    return active_ad_groups


def _is_ad_group_active(adgroup):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None).date()
    adgroup_settings = adgroup.get_current_settings()
    return (adgroup_settings.state == dash.constants.AdGroupSettingsState.ACTIVE and
            not adgroup_settings.archived and
            not adgroup.is_demo and
            (adgroup_settings.end_date is None or
                adgroup_settings.end_date >= today))


def get_active_ad_group_sources_settings(adgroup):
    active_sources_settings = []
    all_ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=adgroup)
    for current_source_settings in dash.views.helpers.get_ad_group_sources_settings(all_ad_group_sources):
        if (current_source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE):
            active_sources_settings.append(current_source_settings)
    return active_sources_settings


def get_total_daily_budget_amount(campaign):
    total_daily_budget = decimal.Decimal(0.0)
    for adg in get_active_ad_groups(campaign):
        for adg_src_set in get_active_ad_group_sources_settings(adg):
            if adg_src_set.daily_budget_cc is not None:
                total_daily_budget += adg_src_set.daily_budget_cc
    return total_daily_budget


def get_latest_ad_group_source_state(ad_group_source):
    try:
        latest_state = dash.models.AdGroupSourceState.objects\
            .filter(ad_group_source=ad_group_source)\
            .latest('created_dt')
        return latest_state
    except dash.models.AdGroupSourceState.DoesNotExist:
        return None


def stop_campaign(campaign):
    for ad_group in get_active_ad_groups(campaign):
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
        new_settings.save(None)
        actionlogs_to_send = []
        with transaction.atomic():
            actionlogs_to_send = actionlog.api.init_pause_ad_group(ad_group, None, send=False)
        zwei_actions.send(actionlogs_to_send)


def update_ad_group_source_value(ad_group_source, field, new_value):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    resource = {field: new_value}
    settings_writer.set(resource, None)
