# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging
import decimal

from dateutil import rrule
from django.db import transaction

import actionlog.api
from actionlog import zwei_actions

from automation import autopilot_budgets, autopilot_plus

import dash.constants
import dash.models

import reports.api_contentads
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
    for campaign in dash.models.Campaign.objects.all().exclude_landing().iterator():
        remaining_today, available_tomorrow, max_daily_budget_per_ags = _get_minimum_remaining_budget(campaign)
        max_daily_budget_sum = sum(max_daily_budget_per_ags.itervalues())
        yesterday_spend = _get_yesterday_spend(campaign)
        if available_tomorrow < max_daily_budget_sum:
            with transaction.atomic():
                _switch_campaign_to_landing_mode(campaign)
                actions = _set_end_date_to_today(campaign)
            zwei_actions.send(actions)
            _send_campaign_stop_notification_email(campaign, remaining_today, max_daily_budget_sum, yesterday_spend)
        elif available_tomorrow < max_daily_budget_sum * 2:
            _send_depleting_budget_notification_email(campaign, remaining_today, max_daily_budget_sum, yesterday_spend)


def update_campaigns_in_landing():
    for campaign in dash.models.Campaign.objects.all().filter_landing().iterator():
        actions = []
        try:
            with transaction.atomic():
                actions.extend(_set_new_daily_budgets(campaign))
                actions.extend(_set_end_date_to_today(campaign))
        except:
            logger.exception('Updating landing mode campaign with id %s not successful', campaign.id)
        zwei_actions.send(actions)


def get_max_settable_daily_budget(ad_group_source):
    remaining_today, available_tomorrow, max_daily_budget_per_ags = _get_minimum_remaining_budget(
        ad_group_source.ad_group.campaign)

    ags_max_daily_budget = max_daily_budget_per_ags[ad_group_source.id]
    other_sources_max_sum = sum(max_daily_budget_per_ags.values()) - ags_max_daily_budget

    max_today = decimal.Decimal(remaining_today + ags_max_daily_budget)\
                       .to_integral_exact(rounding=decimal.ROUND_CEILING)
    max_tomorrow = decimal.Decimal(available_tomorrow - other_sources_max_sum)\
                          .to_integral_exact(rounding=decimal.ROUND_CEILING)

    return max(min(max_today, max_tomorrow), 0)


def _get_minimum_remaining_budget(campaign):
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

    remaining_today = sum(per_budget_remaining_today.itervalues())
    available_tomorrow = 0
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * spend_without_fee_pct)

    return remaining_today, available_tomorrow, max_daily_budget


def _switch_campaign_to_landing_mode(campaign):
    new_campaign_settings = campaign.get_current_settings().copy_settings()
    new_campaign_settings.landing_mode = True
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_campaign_settings.save(None)

    for ad_group in campaign.adgroup_set.all().filter_active():
        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.landing_mode = True
        new_ad_group_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
        new_ad_group_settings.save(None)


def _set_ad_group_end_date(ad_group, end_date):
    current_ag_settings = ad_group.get_current_settings()
    new_ag_settings = current_ag_settings.copy_settings()
    new_ag_settings.end_date = end_date
    new_ag_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_ag_settings.save(None)

    return dash.api.order_ad_group_settings_update(
        ad_group,
        current_ag_settings,
        new_ag_settings,
        request=None,
        send=False,
    )


def _stop_ad_group(ad_group):
    current_settings = ad_group.get_current_settings()
    if current_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return []

    new_settings = current_settings.copy_settings()
    new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
    new_settings.save(None)

    return actionlog.api.init_set_ad_group_state(ad_group, new_settings.state, request=None, send=False)


def _set_end_date_to_today(campaign):
    actions = []
    for ad_group in campaign.adgroup_set.all().filter_active():
        actions.extend(_set_ad_group_end_date(ad_group, dates_helper.utc_today()))
    return actions


def _set_new_daily_budgets(campaign):
    ad_groups = campaign.adgroup_set.all().filter_active()

    per_ad_group_autopilot_data, _ = autopilot_plus.prefetch_autopilot_data(ad_groups)
    remaining_today, _, _ = _get_minimum_remaining_budget(campaign)
    ad_group_daily_cap_ratios = _get_ad_group_ratios(ad_groups)

    actions = []
    for ad_group in ad_groups:
        ad_group_daily_cap = int(float(remaining_today) * ad_group_daily_cap_ratios.get(ad_group.id, 0))

        budget_changes = autopilot_budgets.get_autopilot_daily_budget_recommendations(
            ad_group,
            ad_group_daily_cap,
            per_ad_group_autopilot_data[ad_group],
            goal=None  # use default goal to maximize spend
        )

        ap_budget_sum = sum(bc['new_budget'] for bc in budget_changes.values())
        if ap_budget_sum > ad_group_daily_cap:
            actions.extend(_stop_ad_group(ad_group))
            continue

        actions.extend(autopilot_plus.set_autopilot_changes(
            budget_changes=budget_changes,
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
            landing_mode=True))

    return actions


def _get_past_data(ad_groups, start_date, end_date):
    data = reports.api_contentads.query(
        start_date=start_date,
        end_date=end_date,
        breakdown=['date', 'ad_group'],
        ad_group=ad_groups
    )

    by_breakdown = {}
    for item in data:
        by_breakdown[(item['ad_group'], item['date'])] = item['cost'] + item['data_cost']

    return by_breakdown


def _get_ad_group_ratios(ad_groups):
    before_7_days = dates_helper.local_today() - datetime.timedelta(days=7)
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
    data = _get_past_data(ad_groups, start_date=before_7_days, end_date=yesterday)

    spend_per_ad_group = defaultdict(list)
    for date in rrule.rrule(rrule.DAILY, dtstart=before_7_days, until=yesterday):
        date = date.date()
        active_ad_groups = _get_ad_groups_active_on_date(date, ad_groups)
        for ad_group in active_ad_groups:
            spend_per_ad_group[ad_group.id].append(data[ad_group.id, date])

    avg_spends = {}
    for ad_group_id, spends in spend_per_ad_group.iteritems():
        avg_spends[ad_group_id] = sum(spends) / len(spends)

    total = sum(avg_spends.itervalues())
    normalized = {}
    for ad_group_id, avg_spend in avg_spends.iteritems():
        normalized[ad_group_id] = avg_spend / total

    return normalized


def _get_yesterday_spend(campaign):
    yesterday = dates_helper.utc_today() - datetime.timedelta(days=1)
    statements = reports.models.BudgetDailyStatement.objects.filter(
        budget__campaign=campaign,
        date=yesterday,
    )
    spend_data = reports.budget_helpers.calculate_spend_data(statements, use_decimal=True)

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
    ad_groups = _get_ad_groups_running_on_date(date, campaign.adgroup_set.all())
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


def _get_ad_groups_user_end_dates(ad_groups):
    ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
        landing_mode=False
    ).group_current_settings().values('ad_group_id', 'end_date')
    return {sett['ad_group_id']: sett['end_date'] for sett in ag_settings}


def _get_ag_ids_active_on_date(date, ad_groups):
    ag_ids_active_on_date = set(
        dash.models.AdGroupSettings.objects.filter(
            ad_group__in=ad_groups,
            created_dt__lt=date+datetime.timedelta(days=1),
            created_dt__gte=date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        ).order_by('-created_dt').values_list('ad_group_id', flat=True).iterator()
    )

    latest_ad_group_settings_before_date = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
        created_dt__lt=date,
    ).group_current_settings().values('ad_group_id', 'state')
    for ag_sett in latest_ad_group_settings_before_date.iterator():
        if ag_sett['state'] == dash.constants.AdGroupSettingsState.ACTIVE:
            ag_ids_active_on_date.add(ag_sett['ad_group_id'])

    return ag_ids_active_on_date


def _get_ad_groups_running_on_date(date, ad_groups):
    ad_group_end_dates = _get_ad_groups_user_end_dates(ad_groups)
    ag_ids_active_on_date = _get_ag_ids_active_on_date(date, ad_groups)

    running_ad_groups = set()
    for ad_group in ad_groups:
        end_date = ad_group_end_dates.get(ad_group.id)
        if ad_group.id in ag_ids_active_on_date and (end_date is None or end_date >= date):
            running_ad_groups.add(ad_group)

    return running_ad_groups


def _send_campaign_stop_notification_email(campaign, remaining_today, max_daily_budget, yesterday_spend):
    subject = '[REAL CAMPAIGN STOP] Your campaign {campaign_name} ({account_name}) is switching to landing mode'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) has been switched to automated landing mode because it is approaching the budget limit.

The available media budget remaining today is ${remaining_today:.2f}, current media daily cap is ${max_daily_budget:.2f} and yesterday's media spend was ${yesterday_spend:.2f}.

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
        remaining_today=remaining_today,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)


def _send_depleting_budget_notification_email(campaign, remaining_today, max_daily_budget, yesterday_spend):
    subject = '[REAL CAMPAIGN STOP] Your campaign {campaign_name} ({account_name}) is running out of budget'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) will soon run out of budget.

The available media budget remaining today is ${remaining_today:.2f}, current media daily cap is ${max_daily_budget:.2f} and yesterday's media spend was ${yesterday_spend:.2f}.

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
        remaining_today=remaining_today,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)
