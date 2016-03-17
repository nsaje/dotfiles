# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging

import newrelic.agent

import dash.constants
import dash.models
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
        available_tomorrow, max_daily_budget = _get_minimum_remaining_budget(campaign)
        if available_tomorrow < max_daily_budget:
            # TODO: switch to landing mode
            _send_campaign_stop_notification_email(campaign)
        elif available_tomorrow < max_daily_budget * 2:
            _send_depleting_budget_notification_email(campaign)


@newrelic.agent.background_task()
def _get_minimum_remaining_budget(campaign):
    today = dates_helper.local_today()

    max_daily_budget = _get_max_daily_budget(today, campaign)
    budgets_active_today = _get_budgets_active_on_date(today, campaign)
    budgets_active_tomorrow = _get_budgets_active_on_date(today + datetime.timedelta(days=1), campaign)

    per_budget_remaining_today = {}
    budget_to_distribute = max_daily_budget
    for bli in budgets_active_today.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        spend_available = bli.get_available_amount(date=today - datetime.timedelta(days=1)) * spend_without_fee_pct
        per_budget_remaining_today[bli.id] = max(0, spend_available - budget_to_distribute)
        budget_to_distribute = max(0, budget_to_distribute - spend_available)

    if budget_to_distribute > 0:
        logger.warning('campaign %s could overspend - daily budgets are set wrong', campaign.id)

    available_tomorrow = 0
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * spend_without_fee_pct)

    return available_tomorrow, max_daily_budget


@newrelic.agent.function_trace()
def _get_budgets_active_on_date(date, campaign):
    return campaign.budgets.filter(
        start_date__lte=date,
        end_date__gte=date,
    ).select_related('credit')


@newrelic.agent.function_trace()
def _get_ags_settings_dict(date, ad_group_sources):
    ad_group_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources,
        created_dt__lt=date+datetime.timedelta(days=1)
    ).order_by('-created_dt')

    ret = defaultdict(list)
    for ags_sett in ad_group_sources_settings:
        ret[ags_sett.ad_group_source_id].append(ags_sett)

    return ret


@newrelic.agent.function_trace()
def _get_max_daily_budget(date, campaign):
    ad_groups = _get_ad_groups_active_on_date(date, campaign)
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')
    ad_group_sources_settings = _get_ags_settings_dict(date, ad_group_sources)

    max_daily_budget = 0
    for ags in ad_group_sources:
        max_daily_budget += _get_source_max_daily_budget(date, ags, ad_group_sources_settings[ags.id])

    return max_daily_budget


@newrelic.agent.function_trace()
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


@newrelic.agent.function_trace()
def _get_ag_settings_dict(date, campaign):
    ad_group_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=campaign.adgroup_set.all(),
        created_dt__lt=date+datetime.timedelta(days=1),
    ).order_by('-created_dt')

    ret = defaultdict(list)
    for ag_sett in ad_group_settings:
        ret[ag_sett.ad_group_id].append(ag_sett)

    return ret


@newrelic.agent.function_trace()
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
    body = u'''Hi, campaign manager of {campaign_name},

your campaign {campaign_name} ({account_name}) has been switched to automated landing mode because it is approaching the budget limit.

While in landing mode CPCs and daily budgets of media sources will not be available for any changes.

If you don’t want campaign to be switched to the landing mode please visit {campaign_budgets_url} and assign additional budget.

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


def _send_depleting_budget_notification_email(campaign):
    subject = '[REAL CAMPAIGN STOP] Your campaign {campaign_name} ({account_name}) is running out of budget'
    body = u'''Hi, campaign manager of {campaign_name},

your campaign {campaign_name} ({account_name}) will run out of budget in approximately 3 days. System will automatically turn on the landing mode to hit your budget. While in landing mode CPCs and daily budgets of media sources will not be available for any changes.

If you don’t want campaign to end in a few days please add the budget and continue to adjust media sources settings by your needs. To do so please visit {campaign_budgets_url} and assign budget to your campaign.

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
