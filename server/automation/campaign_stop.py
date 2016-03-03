# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import logging

import dash.constants
import dash.models
from utils import dates_helper, email_helper, url_helper

logger = logging.getLogger(__name__)

TEMP_EMAILS = ['luka.silovinac@zemanta.com', 'urska.kosec@zemanta.com']


def switch_low_budget_campaigns_to_landing_mode():
    for campaign in dash.models.Campaign.objects.filter(landing_mode=False):
        available_tomorrow, max_daily_budget = _get_minimum_remaining_budget(campaign)
        if available_tomorrow < max_daily_budget:
            # TODO: switch to landing mode
            _send_campaign_stop_notification_email(campaign)
        elif available_tomorrow < max_daily_budget * 2:
            _send_depleting_budget_notification_email(campaign)


def _get_minimum_remaining_budget(campaign):
    today = dates_helper.local_today()

    max_daily_budget = _get_max_daily_budget(today, campaign)
    budgets_active_today = _get_budgets_active_on_date(today, campaign)
    budgets_active_tomorrow = _get_budgets_active_on_date(today + datetime.timedelta(days=1), campaign)

    per_budget_remaining_today = {}
    budget_to_distribute = max_daily_budget
    for bli in budgets_active_today.order_by('created_dt'):
        media_spend_pct = 1 - bli.credit.license_fee
        spend_available = bli.get_available_amount(date=today - datetime.timedelta(days=1)) * media_spend_pct
        per_budget_remaining_today[bli.id] = max(0, spend_available - budget_to_distribute)
        budget_to_distribute = max(0, budget_to_distribute - spend_available)

    if budget_to_distribute > 0:
        logger.warning('campaign %s could overspend - daily budgets are set wrong', campaign.id)

    available_tomorrow = 0
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        media_spend_pct = 1 - bli.credit.license_fee
        available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * media_spend_pct)

    return available_tomorrow, max_daily_budget


def _get_budgets_active_on_date(date, campaign):
    return campaign.budgets.filter(
        start_date__lte=date,
        end_date__gte=date,
    ).select_related('credit')


def _get_max_daily_budget(date, campaign):
    ad_groups = _get_ad_groups_active_on_date(date, campaign)
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')
    ad_group_sources_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source_id=ad_group_sources,
        created_dt__lt=date+datetime.timedelta(days=1)
    )

    max_daily_budget = 0
    for ad_group_source in ad_group_sources:
        max_daily_budget += _get_ags_max_daily_budget(date, ad_group_source, ad_group_sources_settings)

    return max_daily_budget


def _get_ags_max_daily_budget(date, ad_group_source, ad_group_sources_settings):
    ad_group_sources_settings = ad_group_sources_settings.order_by('-created_dt')

    ags_max_daily_budget = 0
    reached_day_before = False
    for sett in ad_group_sources_settings:
        if sett.ad_group_source_id != ad_group_source.id:
            continue

        if reached_day_before:
            break

        tz = ad_group_source.source.source_type.budgets_tz
        if dates_helper.utc_to_tz_datetime(sett.created_dt, tz).date() < date:
            reached_day_before = True

        if sett.state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
            continue

        ags_max_daily_budget = max(ags_max_daily_budget, sett.daily_budget_cc)

    return ags_max_daily_budget


def _get_ad_groups_active_on_date(date, campaign):
    ad_group_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=campaign.adgroup_set.all(),
        created_dt__lt=date+datetime.timedelta(days=1),
    ).order_by('-created_dt')

    active_ad_groups = set()
    for ad_group in campaign.adgroup_set.all():
        for sett in ad_group_settings:
            if sett.ad_group_id != ad_group.id:
                continue

            if sett.end_date and sett.end_date < date:
                continue

            if sett.state == dash.constants.AdGroupSettingsState.ACTIVE:
                active_ad_groups.add(ad_group)
                break

            if sett.created_dt.date() < date:
                break

    return active_ad_groups


def _send_campaign_stop_notification_email(campaign):
    subject = 'Your campaign {campaign_name} ({account_name}) is switching to landing mode'
    body = u'''Hi, campaign manager of {campaign_name}

your campaign {campaign_name} ({account_name}) is being switched to automated landing mode because it is approaching the budget limit.

While landing mode CPCs and daily budgets of media sources will not be available for any changes.

If you don’t want campaign to be switched to the landing mode please visit {campaign_budgets_url} and assign additional budget.
Yours truly,
Zemanta
    '''

    subject.format(
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
    subject = 'Your campaign {campaign_name} ({account_name}) is running out of budget'
    body = u'''Hi, campaign manager of {campaign_name}

your campaign {campaign_name} ({account_name}) will run out of budget in approximately 3 days if running at current pace. System will automatically turn on the landing mode to hit your targeted budget. While landing mode CPCs and daily budgets of media sources will not be available for any changes.

If you don’t want campaign to end in a few days please add the budget and continue to adjust media sources settings by your needs. To do so please visit {campaign_budgets_url} and assign budget to your campaign.

Yours truly,
Zemanta
    '''

    subject.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name
    )
    body = body.format(
        campaign_name=campaign.name,
        account_name=campaign.account.name,
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget-plus'.format(campaign.pk)),
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)
