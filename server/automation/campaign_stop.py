# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging
import decimal

import dash.constants
import dash.models
import reports.budget_helpers
import reports.models
from utils import dates_helper, email_helper, url_helper

logger = logging.getLogger(__name__)

TEMP_EMAILS = [
    'luka.silovinac@zemanta.com',
    'urska.kosec@zemanta.com',
    'ana.dejanovic@zemanta.com',
    'tadej.pavlic@zemanta.com',
]


def switch_low_budget_campaigns_to_landing_mode():
    for campaign in dash.models.Campaign.objects.filter(landing_mode=False).iterator():
        available_today, available_tomorrow, max_daily_budget_per_ags = get_minimum_remaining_budget(campaign)
        max_daily_budget = sum(max_daily_budget_per_ags.itervalues())
        if available_tomorrow < max_daily_budget:
            # TODO: switch to landing mode
            _send_campaign_stop_notification_email(campaign)
        elif available_tomorrow < max_daily_budget * 2:
            yesterday_spend = _get_yesterday_spend(campaign)
            _send_depleting_budget_notification_email(campaign, available_today, max_daily_budget, yesterday_spend)


def get_minimum_remaining_budget(campaign):
    today = dates_helper.local_today()

    max_daily_budget = _get_max_daily_budget_per_ags(today, campaign)
    budgets_active_today = _get_budgets_active_on_date(today, campaign)
    budgets_active_tomorrow = _get_budgets_active_on_date(today + datetime.timedelta(days=1), campaign)

    per_budget_remaining_today = {}
    budget_to_distribute = sum(max_daily_budget.itervalues())
    for bli in budgets_active_today.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        spend_available = bli.get_available_amount(date=today - datetime.timedelta(days=1)) * spend_without_fee_pct
        per_budget_remaining_today[bli.id] = max(0, spend_available - budget_to_distribute)
        budget_to_distribute = max(0, budget_to_distribute - spend_available)

    if budget_to_distribute > 0:
        logger.warning('campaign %s could overspend - daily budgets are set wrong', campaign.id)

    available_today = sum(per_budget_remaining_today.itervalues())
    available_tomorrow = 0
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * spend_without_fee_pct)

    return available_today, available_tomorrow, max_daily_budget


def get_max_settable_daily_budget(ad_group_source):
    available_today, available_tomorrow, max_daily_budget_per_ags = get_minimum_remaining_budget(
        ad_group_source.ad_group.campaign)

    max_daily_budget_per_ags[ad_group_source.id] = 0
    max_daily_budget_sum = sum(max_daily_budget_per_ags.itervalues())

    max_today = decimal.Decimal(available_today - max_daily_budget_sum)\
                       .to_integral_exact(rounding=decimal.ROUND_CEILING)
    max_tomorrow = decimal.Decimal(available_tomorrow - max_daily_budget_sum)\
                          .to_integral_exact(rounding=decimal.ROUND_CEILING)

    return max(min(max_today, max_tomorrow), 0)


def _get_yesterday_spend(campaign):
    yesterday = dates_helper.utc_today() - datetime.timedelta(days=1)
    statements = reports.models.BudgetDailyStatement.objects.filter(budget__campaign=campaign)
    spend_data = reports.budget_helpers.calculate_spend_data(statements, date=yesterday, use_decimal=True)

    return spend_data['media'] + spend_data['data']


def _get_budgets_active_on_date(date, campaign):
    return campaign.budgets.filter(
        start_date__lte=date,
        end_date__gte=date,
    ).select_related('credit')


def _get_ags_settings_dict(date, ad_group_sources):
    settings_on_date = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources,
        created_dt__lt=date+datetime.timedelta(days=1),
    ).order_by('-created_dt')

    ret = defaultdict(list)
    for ags_sett in settings_on_date.iterator():
        ret[ags_sett.ad_group_source_id].append(ags_sett)

    return ret


def _get_max_daily_budget_per_ags(date, campaign):
    ad_groups = _get_ad_groups_active_on_date(date, campaign)
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')
    ad_group_sources_settings = _get_ags_settings_dict(date, ad_group_sources)

    max_daily_budget = {}
    for ags in ad_group_sources:
        max_daily_budget[ags.id] = _get_source_max_daily_budget(date, ags, ad_group_sources_settings[ags.id])

    return max_daily_budget


def _get_source_max_daily_budget(date, ad_group_source, ad_group_source_settings):
    ags_max_daily_budget = 0
    reached_day_before = False
    for sett in ad_group_source_settings:
        if reached_day_before:
            break

        tz = ad_group_source.source.source_type.budgets_tz
        if dates_helper.utc_to_tz_datetime(sett.created_dt, tz).date() < date:
            reached_day_before = True

        if sett.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue

        ags_max_daily_budget = max(ags_max_daily_budget, sett.daily_budget_cc)

    return ags_max_daily_budget


def _get_ag_settings_dict(date, campaign):
    ad_group_settings_on_date = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=campaign.adgroup_set.all(),
        created_dt__lt=date+datetime.timedelta(days=1),
        created_dt__gte=date,
    ).order_by('-created_dt')

    ret = defaultdict(list)
    for ag_sett in ad_group_settings_on_date.iterator():
        ret[ag_sett.ad_group_id].append(ag_sett)

    latest_ad_group_settings_before_date = dash.models.AdGroupSettings.objects.filter(
        created_dt__lt=date,
    ).group_current_settings()

    for ag_sett in latest_ad_group_settings_before_date.iterator():
        ret[ag_sett.ad_group_id].append(ag_sett)

    return ret


def _get_ad_groups_active_on_date(date, campaign):
    ad_groups_settings = _get_ag_settings_dict(date, campaign)
    active_ad_groups = set()
    for ad_group in campaign.adgroup_set.all():
        for sett in ad_groups_settings[ad_group.id]:
            if (not sett.end_date or sett.end_date >= date) and\
               sett.state == dash.constants.AdGroupSettingsState.ACTIVE:
                active_ad_groups.add(ad_group)
                break

            if sett.created_dt.date() < date:
                break

    return active_ad_groups


def _send_campaign_stop_notification_email(campaign):
    subject = '[REAL CAMPAIGN STOP] Your campaign {campaign_name} ({account_name}) is switching to landing mode'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) has been switched to automated landing mode because it is approaching the budget limit.

Please visit {campaign_budgets_url} and assign additional budget, if you don’t want campaign to be switched to the landing mode.

While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes, to ensure accurate delivery.

Yours truly,
Zemanta'''  # noqa

    subject = subject.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name
    )
    body = body.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name,
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget-plus'.format(campaign.pk)),
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)


def _send_depleting_budget_notification_email(campaign, available_today, max_daily_budget, yesterday_spend):
    subject = '[REAL CAMPAIGN STOP] Your campaign {campaign_name} ({account_name}) is running out of budget'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) will soon run out of budget.

The available budget remaining today is ${available_today}, current daily cap is ${max_daily_budget} and yesterday's spend was ${yesterday_spend}.

Please add the budget and continue to adjust media sources settings by your needs, if you don’t want campaign to end in a few days. To do so please visit {campaign_budgets_url} and assign budget to your campaign.

If you don’t take any actions, system will automatically turn on the landing mode to hit your budget. While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes.

Yours truly,
Zemanta'''  # noqa

    subject = subject.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name
    )
    body = body.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name,
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget-plus'.format(campaign.pk)),
        available_today=available_today,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)
