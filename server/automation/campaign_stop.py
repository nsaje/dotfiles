# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging
import decimal
from itertools import tee, izip_longest

from django.db import transaction
from django.db.models import Min, Max

import pytz

import actionlog.api
from actionlog import zwei_actions

from automation import autopilot_budgets, autopilot_cpc, autopilot_plus, autopilot_settings, models

import dash.constants
import dash.models

import reports.api_contentads
import reports.budget_helpers
import reports.models

import utils.k1_helper
from utils import dates_helper, email_helper, url_helper, pagerduty_helper

logger = logging.getLogger(__name__)

NON_SPENDING_SOURCE_THRESHOLD_DOLLARS = decimal.Decimal('1')


def run_job():
    not_landing = list(dash.models.Campaign.objects.all().exclude_landing().iterator())
    in_landing = list(dash.models.Campaign.objects.all().filter_landing().iterator())

    switch_low_budget_campaigns_to_landing_mode(not_landing, pagerduty_on_fail=True)
    update_campaigns_in_landing(in_landing, pagerduty_on_fail=True)


def switch_low_budget_campaigns_to_landing_mode(campaigns, pagerduty_on_fail=False):
    campaign_settings = {
        sett.campaign_id: sett
        for sett in dash.models.CampaignSettings.objects.filter(campaign__in=campaigns).group_current_settings()
    }
    actions = []
    for campaign in campaigns:
        try:
            changed, new_actions = _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings[campaign.id])
        except:
            logger.exception('Campaign stop check for campaign with id %s not successful', campaign.id)
            if pagerduty_on_fail:
                _trigger_check_pagerduty(campaign)
            continue
        actions.extend(new_actions)
        if changed:
            utils.k1_helper.update_ad_groups(
                (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
                msg='campaign_stop.switch_low_budget_campaign'
            )
    zwei_actions.send(actions)


def perform_landing_mode_check(campaign, campaign_settings):
    switched_to_landing, actions = _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings)
    if switched_to_landing:
        zwei_actions.send(actions)
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.perform_landing_mode_check_switch'
        )
        return True

    resumed, actions = _check_and_resume_campaign(campaign, campaign_settings)
    if resumed:
        zwei_actions.send(actions)
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.perform_landing_mode_check_resume'
        )
        return True

    return False


def _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return False, []

    if campaign_settings.landing_mode:
        return False, []

    today = dates_helper.local_today()
    max_daily_budget = _get_max_daily_budget(today, campaign)
    current_daily_budget = _get_current_daily_budget(campaign)
    _, available_tomorrow, _ = _get_minimum_remaining_budget(campaign, max_daily_budget)
    yesterday_spend = _get_yesterday_budget_spend(campaign)

    switched_to_landing = available_tomorrow < current_daily_budget
    is_near_depleted = available_tomorrow < current_daily_budget * 2
    actions = []
    if switched_to_landing:
        with transaction.atomic():
            actions.extend(_switch_campaign_to_landing_mode(campaign))
        _send_campaign_stop_notification_email(
            campaign, campaign_settings, available_tomorrow, current_daily_budget, yesterday_spend)
    elif is_near_depleted:
        _send_depleting_budget_notification_email(
            campaign, campaign_settings, available_tomorrow, current_daily_budget, yesterday_spend)

    if switched_to_landing:
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.check_and_switch_campaign_to_landing_mode'
        )

    return switched_to_landing, actions


def _check_and_resume_campaign(campaign, campaign_settings):
    if _can_resume_campaign(campaign, campaign_settings):
        with transaction.atomic():
            actions = _resume_campaign(campaign)
            return True, actions
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.check_and_resume_campaign'
        )
    return False, []


def get_minimum_budget_amount(budget_item):
    if budget_item.state() != dash.constants.BudgetLineItemState.ACTIVE:
        return None
    today = dates_helper.local_today()

    covered_amount = _combined_active_budget_from_other_items(budget_item)

    spend = budget_item.get_spend_data(use_decimal=True)['total']
    max_daily_budget = _get_max_daily_budget(today, budget_item.campaign)

    daily_budgets = max_daily_budget / (1 - budget_item.credit.license_fee)
    return max(
        spend + daily_budgets - covered_amount,
        0
    )


def is_current_time_valid_for_amount_editing(campaign):
    """
    Check if current time is not between first midnight
    on all enabled sources' time zones and UTC noon.
    """
    utc_now = dates_helper.utc_now()
    utc_today = utc_now.date()

    today = dates_helper.local_today()

    ad_groups = _get_ad_groups_running_on_date(today, campaign.adgroup_set.all())
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')

    timezones = [
        ags.source.source_type.budgets_tz for ags in ad_group_sources
    ]
    current_times = [
        dates_helper.utc_to_tz_datetime(utc_now, tz) for tz in timezones
    ]

    any_source_after_midnight = any(dt.date() >= utc_today for dt in current_times)
    return not (utc_now.hour < 12 and any_source_after_midnight)


def update_campaigns_in_landing(campaigns, pagerduty_on_fail=True):
    for campaign in campaigns:
        logger.info('updating in landing campaign with id %s', campaign.id)
        actions = []
        try:
            with transaction.atomic():
                actions.extend(_update_landing_campaign(campaign))
        except:
            logger.exception('Updating landing mode campaign with id %s not successful', campaign.id)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Failed to update landing campaign.'
            )
            if pagerduty_on_fail:
                _trigger_update_pagerduty(campaign)
            continue

        zwei_actions.send(actions)
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='update_campaigns_in_landing'
        )


def can_enable_ad_group(ad_group, campaign, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return True

    if campaign_settings.landing_mode:
        return False

    ad_groups = [ad_group]
    return _can_enable_ad_groups(ad_groups, campaign)


def can_enable_ad_groups(campaign, campaign_settings):
    ad_groups = campaign.adgroup_set.all().exclude_archived()
    if not campaign_settings.automatic_campaign_stop:
        return {ag.id: True for ag in ad_groups}

    if campaign_settings.landing_mode:
        return {ag.id: False for ag in ad_groups}

    return _can_enable_ad_groups(ad_groups, campaign)


def can_enable_media_source(ad_group_source, campaign, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return True

    if campaign_settings.landing_mode:
        return False

    ad_group_sources = [ad_group_source]
    return _can_enable_media_sources(ad_group_sources, campaign)


def can_enable_media_sources(ad_group, campaign, campaign_settings):
    ad_group_sources = ad_group.adgroupsource_set.all()
    if not campaign_settings.automatic_campaign_stop:
        return {ags.id: True for ags in ad_group_sources}

    if campaign_settings.landing_mode:
        return {ags.id: False for ags in ad_group_sources}

    return _can_enable_media_sources(ad_group_sources, campaign)


def get_max_settable_source_budget(ad_group_source, new_daily_budget, campaign,
                                   ad_group_source_settings, ad_group_settings, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return None

    if campaign_settings.landing_mode:
        return 0

    today = dates_helper.local_today()
    max_daily_budget_per_ags = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, sum(max_daily_budget_per_ags.values()))

    max_ags_daily_budget = max_daily_budget_per_ags.get(ad_group_source.id, 0)
    if new_daily_budget <= max_ags_daily_budget:
        return max_ags_daily_budget

    ags_max_daily_budget = max_daily_budget_per_ags.get(ad_group_source.id, 0)
    other_sources_max_sum = sum(max_daily_budget_per_ags.values()) - ags_max_daily_budget

    max_today = decimal.Decimal(ags_max_daily_budget + remaining_today)\
                       .to_integral_exact(rounding=decimal.ROUND_CEILING)
    max_tomorrow = decimal.Decimal(available_tomorrow - other_sources_max_sum)\
                          .to_integral_exact(rounding=decimal.ROUND_CEILING)

    return max(min(max_today, max_tomorrow), 0)


def _can_enable_media_sources(ad_group_sources, campaign):
    current_ags_settings = {}
    for ags_settings in dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources,
    ).group_current_settings().select_related('ad_group_source__source'):
        current_ags_settings[ags_settings.ad_group_source] = ags_settings

    today = dates_helper.local_today()
    max_daily_budget_per_ags = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, sum(max_daily_budget_per_ags.values()))

    ret = {}
    for ad_group_source, ags_settings in current_ags_settings.iteritems():
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            ret[ad_group_source.id] = True
            continue

        daily_budget_cc = ags_settings.daily_budget_cc
        if not daily_budget_cc:
            daily_budget_cc = ad_group_source.source.default_daily_budget_cc

        daily_budget_added = daily_budget_cc - max_daily_budget_per_ags.get(ad_group_source.id, 0)
        can_enable_today = daily_budget_added <= remaining_today
        can_enable_tomorrow = daily_budget_cc <= available_tomorrow

        ret[ad_group_source.id] = can_enable_today and can_enable_tomorrow

    return ret


def _can_enable_ad_groups(ad_groups, campaign):
    today = dates_helper.local_today()
    max_daily_budget_per_ags = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, sum(max_daily_budget_per_ags.values()))

    current_ag_settings = {}
    for ag_settings in dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups
    ).group_current_settings().select_related('ad_group'):
        current_ag_settings[ag_settings.ad_group] = ag_settings

    current_ags_settings = {}
    for ags_settings in dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups,
    ).group_current_settings().select_related('ad_group_source__source'):
        current_ags_settings[ags_settings.ad_group_source] = ags_settings

    ret = {}
    for ad_group in ad_groups:
        ret[ad_group.id] = _can_enable_ad_group(ad_group, current_ag_settings[ad_group], current_ags_settings,
                                                max_daily_budget_per_ags, remaining_today, available_tomorrow)
    return ret


def _can_enable_ad_group(ad_group, ad_group_settings, ad_group_sources_settings_dict,
                         max_daily_budget_per_ags, remaining_today, available_tomorrow):
    if ad_group_settings.state == dash.constants.AdGroupSettingsState.ACTIVE:
        return True

    daily_budget_total = 0
    daily_budget_added = 0
    for ad_group_source, ad_group_source_settings in ad_group_sources_settings_dict.iteritems():
        if ad_group_source_settings.state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
            continue

        max_daily_budget = max_daily_budget_per_ags.get(ad_group_source.id, 0)
        current_daily_budget = ad_group_source_settings.daily_budget_cc
        if not current_daily_budget:
            current_daily_budget = ad_group_source_settings.ad_group_source.source.default_daily_budget_cc

        daily_budget_total += current_daily_budget
        daily_budget_added += max(0, current_daily_budget - max_daily_budget)

    can_enable_today = daily_budget_added <= remaining_today
    can_enable_tomorrow = daily_budget_total <= available_tomorrow

    return can_enable_today and can_enable_tomorrow


def get_min_budget_increase(campaign):
    today = dates_helper.local_today()
    user_daily_budget_per_ags = _get_user_daily_budget_per_ags(campaign)
    max_daily_budgets_per_ags = _get_max_daily_budget_per_ags(today, campaign)

    max_daily_budget = 0
    all_keys = set(user_daily_budget_per_ags.keys()) | set(max_daily_budgets_per_ags.keys())
    for ags_id in all_keys:
        user_ags_daily_budget = user_daily_budget_per_ags.get(ags_id, 0)
        max_ags_daily_budget = max_daily_budgets_per_ags.get(ags_id, 0)
        max_daily_budget += max(user_ags_daily_budget, max_ags_daily_budget)

    _, available_tomorrow, min_needed_today = _get_minimum_remaining_budget(campaign, max_daily_budget)

    user_daily_budget_sum = sum(user_db for user_db in user_daily_budget_per_ags.values() if user_db is not None)
    min_needed_tomorrow = user_daily_budget_sum - available_tomorrow
    return max(min_needed_today, min_needed_tomorrow, 0)


def _combined_active_budget_from_other_items(budget_item):
    other_active_budgets = dash.models.BudgetLineItem.objects.filter(
        campaign=budget_item.campaign
    ).filter_active().exclude(pk=budget_item.pk)
    return sum(
        b.get_available_amount() for b in other_active_budgets
    )


def _can_resume_campaign(campaign, campaign_settings):
    return campaign_settings.landing_mode and get_min_budget_increase(campaign) == 0


def _get_minimum_remaining_budget(campaign, max_daily_budget):
    today = dates_helper.local_today()

    budgets_active_today = _get_budgets_active_on_date(today, campaign)
    budgets_active_tomorrow = _get_budgets_active_on_date(today + datetime.timedelta(days=1), campaign)

    per_budget_remaining_today = {}
    unattributed_budget = max_daily_budget
    for bli in budgets_active_today.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        spend_available = bli.get_available_amount(date=today - datetime.timedelta(days=1)) * spend_without_fee_pct
        per_budget_remaining_today[bli.id] = max(0, spend_available - unattributed_budget)
        unattributed_budget = max(0, unattributed_budget - spend_available)

    remaining_today = sum(per_budget_remaining_today.itervalues())
    available_tomorrow = 0
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        spend_without_fee_pct = 1 - bli.credit.license_fee
        available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * spend_without_fee_pct)

    return remaining_today, available_tomorrow, unattributed_budget


def _update_landing_campaign(campaign):
    """
    Stops ad groups and sources that have no spend yesterday, prepares remaining for autopilot and runs it.

    If at any point the campaign has no running ad groups left, landing mode is turned off. In that case it can happen
    that multiple actions are sent for same ad group sources and same change (state) but the updates aren't conflicing
    so it's not an issue.
    """
    actions = []
    campaign_settings = campaign.get_current_settings()
    if _can_resume_campaign(campaign, campaign_settings):
        return _resume_campaign(campaign)

    if not campaign.adgroup_set.all().filter_active().count() > 0:
        return _wrap_up_landing(campaign)

    actions.extend(_stop_non_spending_sources(campaign))
    if not campaign.adgroup_set.all().filter_active().count() > 0:
        return actions + _wrap_up_landing(campaign)

    actions.extend(_check_ad_groups_end_date(campaign))
    if not campaign.adgroup_set.all().filter_active().count() > 0:
        return actions + _wrap_up_landing(campaign)

    per_date_spend, per_source_spend = _get_past_7_days_data(campaign)
    daily_caps = _calculate_daily_caps(campaign, per_date_spend)
    ap_stop_actions, any_ad_group_stopped = _prepare_for_autopilot(campaign, daily_caps, per_source_spend)
    actions.extend(ap_stop_actions)
    if not campaign.adgroup_set.all().filter_active().count() > 0:
        return actions + _wrap_up_landing(campaign)

    if any_ad_group_stopped:
        daily_caps = _calculate_daily_caps(campaign, per_date_spend)

    _persist_new_autopilot_settings(daily_caps)

    actions.extend(_run_autopilot(campaign, daily_caps))
    actions.extend(_set_end_date_to_today(campaign))

    return actions


def _check_ad_groups_end_date(campaign):
    today = dates_helper.local_today()
    actions, finished = [], []
    for ad_group in campaign.adgroup_set.all().filter_active():
        user_settings = _get_last_user_ad_group_settings(ad_group)
        if user_settings.end_date and user_settings.end_date < today:
            finished.append(ad_group)
            actions.extend(_stop_ad_group(ad_group))

    if finished:
        models.CampaignStopLog.objects.create(
            campaign=campaign,
            notes='Stopped finished ad groups {}'.format(', '.join(
                str(ad_group) for ad_group in finished
            ))
        )
    return actions


def _persist_new_autopilot_settings(daily_caps):
    adgroup_settings_list = dash.models.AdGroupSettings.objects.filter(
        ad_group_id__in=daily_caps.keys()
    ).group_current_settings()
    for settings in adgroup_settings_list:
        dcap = decimal.Decimal(daily_caps.get(settings.ad_group_id, 0))
        new_settings = settings.copy_settings()
        new_settings.autopilot_state = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        new_settings.autopilot_daily_budget = dcap
        new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
        new_settings.save(None)


def _stop_non_spending_sources(campaign):
    """
    Stops sources without yesterday spend. If no source had spend, the whole ad group will be stopped.
    """
    active_sources = _get_active_ad_group_sources(campaign)
    active_ad_groups = active_sources.keys()

    yesterday_spends = _get_yesterday_source_spends(active_ad_groups)
    actions = []
    for ad_group in active_ad_groups:
        active_ad_group_sources = active_sources[ad_group]

        to_stop = set()
        for ags in active_ad_group_sources:
            if yesterday_spends.get((ags.ad_group_id, ags.source_id), 0) < NON_SPENDING_SOURCE_THRESHOLD_DOLLARS:
                to_stop.add(ags)

        if len(to_stop) == len(active_ad_group_sources):
            actions.extend(_stop_ad_group(ad_group))
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping non spending ad group {}. Yesterday spend per source was:\n{}'.format(
                    ad_group.id,
                    '\n'.join(['{}: ${}'.format(
                        ags.source.name,
                        yesterday_spends.get((ags.ad_group_id, ags.source_id), 0)
                    ) for ags in sorted(active_ad_group_sources, key=lambda x: x.source.name)])
                )
            )
            continue

        if to_stop:
            for ags in to_stop:
                actions.extend(_stop_ad_group_source(ags))
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping non spending ad group sources on ad group {}. '
                      'Yesterday spend per source was:\n{}'.format(
                          ad_group.id,
                          '\n'.join(['{}: ${}'.format(
                              ags.source.name,
                              yesterday_spends.get((ags.ad_group_id, ags.source_id), 0)
                          ) for ags in sorted(to_stop, key=lambda x: x.source.name)])
                      )
            )
    return actions


def _prepare_for_autopilot(campaign, daily_caps, per_source_spend):
    """
    Stops as many sources as needed to lower autopilot's minimum daily budget limit so that it' lower or equal to
    calculated daily cap for each ad group. If no source is left running, the whole ad group will be stopped.
    """
    actions = []
    active_sources = _get_active_ad_group_sources(campaign)
    any_ad_group_stopped = False
    for ad_group, ad_group_sources in active_sources.iteritems():
        ag_daily_cap = daily_caps[ad_group.id]
        sorted_ad_group_sources = sorted(
            ad_group_sources,
            key=lambda x: per_source_spend.get((x.ad_group_id, x.source_id), 0),
        )

        to_stop = set()
        while len(sorted_ad_group_sources) > 0 and ag_daily_cap < _get_min_ap_budget(sorted_ad_group_sources):
            to_stop.add(sorted_ad_group_sources.pop(0))

        if len(sorted_ad_group_sources) == 0:
            any_ad_group_stopped = True
            actions.extend(_stop_ad_group(ad_group))
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping ad group {} - lowering minimum autopilot budget not possible.\n'
                      'Minimum budget: {}, Daily cap: {}.'.format(
                          ad_group.id,
                          _get_min_ap_budget(ad_group_sources),
                          ag_daily_cap,
                      )
            )
            continue

        if to_stop:
            for ags in to_stop:
                actions.extend(_stop_ad_group_source(ags))
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping sources on ad group {}:\n\n{}\nLowering minimum autopilot budget not possible.\n'
                      'Minimum budget: {}, Daily cap: {}.'.format(
                          ad_group.id,
                          '\n'.join([ags.source.name for ags in sorted(to_stop, key=lambda x: x.source.name)]),
                          _get_min_ap_budget(ad_group_sources),
                          ag_daily_cap,
                      )
            )

    return actions, any_ad_group_stopped


def _run_autopilot(campaign, daily_caps):
    actions = []

    active_ad_groups = campaign.adgroup_set.all().filter_active()
    per_ad_group_autopilot_data, campaign_goals = autopilot_plus.prefetch_autopilot_data(active_ad_groups)
    for ad_group in active_ad_groups:
        daily_cap = daily_caps[ad_group.id]
        ap_data = per_ad_group_autopilot_data[ad_group]
        campaign_goal = campaign_goals[ad_group.campaign]

        budget_changes = autopilot_budgets.get_autopilot_daily_budget_recommendations(
            ad_group,
            daily_cap,
            ap_data,
            campaign_goal=campaign_goal,
        )
        cpc_changes = autopilot_cpc.get_autopilot_cpc_recommendations(ad_group, ap_data, budget_changes)

        ap_budget_sum = sum(bc['new_budget'] for bc in budget_changes.values())
        if ap_budget_sum > daily_cap:
            logger.error('Campaign stop - budget allocation error, ad group: %s could overspend', ad_group.id)

        models.CampaignStopLog.objects.create(
            campaign=campaign,
            notes='Applying autopilot recommendations for ad group {}:\n{}'.format(
                ad_group.id,
                '\n'.join(['{}: Daily budget: ${:.0f} to ${:.0f}, CPC: ${:.3f} to ${:.3f}'.format(
                    ags.source.name,
                    budget_changes.get(ags, {}).get('old_budget', -1),
                    budget_changes.get(ags, {}).get('new_budget', -1),
                    cpc_changes.get(ags, {}).get('old_cpc_cc', -1),
                    cpc_changes.get(ags, {}).get('new_cpc_cc', -1),
                ) for ags in sorted(set(budget_changes.keys() + cpc_changes.keys()), key=lambda x: x.source.name)])
            )
        )
        actions.extend(
            autopilot_plus.set_autopilot_changes(
                budget_changes=budget_changes,
                cpc_changes=cpc_changes,
                system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
                landing_mode=True
            )
        )

    return actions


def _switch_campaign_to_landing_mode(campaign):
    new_campaign_settings = campaign.get_current_settings().copy_settings()
    new_campaign_settings.landing_mode = True
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_campaign_settings.save(None)

    actions = []
    today = dates_helper.local_today()
    for ad_group in campaign.adgroup_set.all().filter_active():
        new_ag_settings = ad_group.get_current_settings().copy_settings()

        new_ag_settings.landing_mode = True
        new_ag_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
        new_ag_settings.save(None)

        if new_ag_settings.end_date and new_ag_settings.end_date < today:
            actions.extend(_stop_ad_group(ad_group))
        else:
            actions.extend(_set_ad_group_end_date(ad_group, today))

        for ad_group_source in ad_group.adgroupsource_set.all().filter_active():
            new_ags_settings = ad_group_source.get_current_settings().copy_settings()
            new_ags_settings.landing_mode = True
            new_ags_settings.save(None)

    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='Switched to landing mode.'
    )
    return actions


def _resume_campaign(campaign):
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='Campaign returned to normal mode - enough campaign budget '
              'today and tomorrow to cover daily budgets set before landing mode.'
    )
    return _turn_off_landing_mode(campaign, pause_ad_groups=False)


def _wrap_up_landing(campaign):
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='Campaign landed - no ad groups are left running.'
    )
    return _turn_off_landing_mode(campaign, pause_ad_groups=True)


def _turn_off_landing_mode(campaign, pause_ad_groups=False):
    current_settings = campaign.get_current_settings()
    new_campaign_settings = current_settings.copy_settings()
    new_campaign_settings.landing_mode = False
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    if new_campaign_settings.get_setting_changes(current_settings):
        new_campaign_settings.save(None)

    actions = []
    for ad_group in campaign.adgroup_set.all().filter_landing():
        actions.extend(_restore_user_ad_group_settings(ad_group, pause_ad_group=pause_ad_groups))

    return actions


def _get_last_user_ad_group_settings(ad_group):
    return dash.models.AdGroupSettings.objects.filter(
        ad_group=ad_group,
        landing_mode=False
    ).latest('created_dt')


def _restore_user_ad_group_settings(ad_group, pause_ad_group=False):
    user_settings = _get_last_user_ad_group_settings(ad_group)

    current_settings = ad_group.get_current_settings()

    new_settings = current_settings.copy_settings()
    new_settings.state = user_settings.state
    new_settings.end_date = user_settings.end_date
    new_settings.autopilot_state = user_settings.autopilot_state
    new_settings.autopilot_daily_budget = user_settings.autopilot_daily_budget
    new_settings.landing_mode = False
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP

    if pause_ad_group:
        new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE

    actions = []
    if current_settings.get_setting_changes(new_settings):
        new_settings.save(None)
        actions.extend(
            dash.api.order_ad_group_settings_update(
                ad_group,
                current_settings,
                new_settings,
                request=None,
                send=False,
            )
        )

    actions.extend(_restore_user_sources_settings(ad_group))
    return actions


def _restore_user_sources_settings(ad_group):
    actions = []

    ad_group_sources = ad_group.adgroupsource_set.all()
    user_ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
            landing_mode=False,
        ).group_current_settings()
    }
    current_ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
        ).group_current_settings()
    }

    for ad_group_source in ad_group.adgroupsource_set.all():
        settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
        user_settings = user_ad_group_sources_settings[ad_group_source.id]
        current_settings = current_ad_group_sources_settings[ad_group_source.id]

        for key in ['state', 'cpc_cc', 'daily_budget_cc']:
            if getattr(user_settings, key) == getattr(current_settings, key):
                continue

            actions.extend(
                settings_writer.set(
                    {
                        key: getattr(user_settings, key),
                    },
                    request=None,
                    send_to_zwei=False,
                    system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
                )
            )

        if current_settings.landing_mode:
            new_settings = ad_group_source.get_current_settings().copy_settings()
            new_settings.landing_mode = False
            new_settings.save(None)

    return actions


def _stop_ad_group(ad_group):
    actions = []

    new_settings = ad_group.get_current_settings().copy_settings()
    new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_settings.save(None)

    actions.extend(
        actionlog.api.init_set_ad_group_state(
            ad_group,
            dash.constants.AdGroupSettingsState.INACTIVE,
            request=None,
            send=False
        )
    )
    return actions


def _set_end_date_to_today(campaign):
    actions = []
    today = dates_helper.local_today()
    for ad_group in campaign.adgroup_set.all().filter_active():
        actions.extend(
            _set_ad_group_end_date(ad_group, today)
        )
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='End date set to {}'.format(today)
    )
    return actions


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


def _stop_ad_group_source(ad_group_source):
    settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
    actions = settings_writer.set(
        {'state': dash.constants.AdGroupSourceSettingsState.INACTIVE},
        request=None,
        create_action=True,
        send_to_zwei=False,
        system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
        landing_mode=True
    )
    return actions


def _get_yesterday_source_spends(ad_groups):
    rows = reports.api_contentads.query(
        dates_helper.local_today() - datetime.timedelta(days=1),
        dates_helper.local_today() - datetime.timedelta(days=1),
        breakdown=['ad_group', 'source'],
        ad_group=ad_groups
    )

    yesterday_spends = {}
    for row in rows:
        media_cost = row['cost'] or 0
        data_cost = row['data_cost'] or 0
        yesterday_spends[(row['ad_group'], row['source'])] = media_cost + data_cost

    return yesterday_spends


def _get_active_ad_group_sources(campaign):
    active_ad_groups = campaign.adgroup_set.all().filter_active()
    active_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=active_ad_groups
    ).filter_active().select_related('ad_group', 'source')
    active_sources_dict = defaultdict(set)
    for ags in active_sources:
        active_sources_dict[ags.ad_group].add(ags)

    return active_sources_dict


def _get_min_ap_budget(ad_group_sources):
    min_daily_budgets = []
    for ags in ad_group_sources:
        min_source_budget = autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET
        if ags.source.source_type.min_daily_budget:
            min_source_budget = max(min_source_budget, ags.source.source_type.min_daily_budget)
        min_daily_budgets.append(min_source_budget)
    return sum(min_daily_budgets)


def _persist_new_daily_caps_to_log(campaign, daily_caps, ad_groups, remaining_today, per_date_spend, daily_cap_ratios):
    notes = 'Calculated ad group daily caps to:\n'
    for ad_group in ad_groups:
        notes += 'Ad group: {}, Daily cap: ${}\n'.format(ad_group.id, daily_caps[ad_group.id])
    notes += '\nRemaining budget today: {:.2f}\n\n'.format(remaining_today)
    notes += 'Past spends:\n'
    for ad_group in sorted(ad_groups, key=lambda ag: ag.name):
        per_date_ag_spend = [amount for key, amount in per_date_spend.iteritems() if key[0] == ad_group.id]
        notes += 'Ad group: {} ({}), Past 7 day spend: {:.2f}, Avg: {:.2f} (was running for {} days), '\
                 'Calculated ratio: {:.2f}\n'.format(
                     ad_group.name,
                     ad_group.id,
                     sum(per_date_ag_spend),
                     sum(per_date_ag_spend) / len(per_date_ag_spend) if len(per_date_ag_spend) > 0 else 0,
                     len(per_date_ag_spend),
                     daily_cap_ratios.get(ad_group.id, 0),
                 )

    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=notes
    )


def _calculate_daily_caps(campaign, per_date_spend):
    active_ad_groups = campaign.adgroup_set.all().filter_active()
    daily_cap_ratios = _get_ad_group_ratios(active_ad_groups, per_date_spend)
    today = dates_helper.local_today()
    max_daily_budget = _get_max_daily_budget(today, campaign)
    remaining_today, _, _ = _get_minimum_remaining_budget(campaign, max_daily_budget)

    daily_caps = {}
    for ad_group in active_ad_groups:
        daily_caps[ad_group.id] = int(round(int(remaining_today) * float(daily_cap_ratios.get(ad_group.id, 0))))

    _persist_new_daily_caps_to_log(campaign, daily_caps, active_ad_groups,
                                   remaining_today, per_date_spend, daily_cap_ratios)
    return daily_caps


def _get_ad_group_ratios(active_ad_groups, per_date_data):
    active_ids = set(ag.id for ag in active_ad_groups)
    spend_per_ad_group = defaultdict(list)
    for key, val in per_date_data.iteritems():
        ad_group_id, _ = key
        if ad_group_id not in active_ids:
            continue

        spend_per_ad_group[ad_group_id].append(val)

    avg_spends = {}
    for ad_group_id, spends in spend_per_ad_group.iteritems():
        if len(spends) > 0:
            avg_spends[ad_group_id] = sum(spends) / len(spends)

    total = sum(avg_spends.itervalues())
    normalized = {}
    for ad_group_id, avg_spend in avg_spends.iteritems():
        if total > 0:
            normalized[ad_group_id] = avg_spend / total

    return normalized


def _get_past_7_days_data(campaign):
    data = reports.api_contentads.query(
        start_date=dates_helper.local_today() - datetime.timedelta(days=7),
        end_date=dates_helper.local_today() - datetime.timedelta(days=1),
        breakdown=['date', 'ad_group', 'source'],
        campaign=campaign,
    )

    date_spend = defaultdict(int)
    source_spend = defaultdict(int)
    for item in data:
        media_cost = item['cost'] or 0
        data_cost = item['data_cost'] or 0
        spend = media_cost + data_cost
        date_spend[(item['ad_group'], item['date'])] += spend
        source_spend[(item['ad_group'], item['source'])] += spend

    return date_spend, source_spend


def _get_yesterday_budget_spend(campaign):
    yesterday = dates_helper.local_today() - datetime.timedelta(days=1)
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


def _get_sources_by_tz(ad_group_sources):
    sources_by_tz = defaultdict(list)
    for ad_group_source in ad_group_sources:
        sources_by_tz[ad_group_source.source.source_type.budgets_tz].append(ad_group_source)
    return sources_by_tz


def _get_sources_settings_dict(date, ad_group_sources):
    sources_by_tz = _get_sources_by_tz(ad_group_sources)

    ret = defaultdict(list)
    for budgets_tz, tz_sources in sources_by_tz.items():
        dt_tz = budgets_tz.localize(datetime.datetime(date.year, date.month, date.day)).astimezone(pytz.utc)
        latest_settings_before = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=tz_sources,
            created_dt__lt=dt_tz,
        ).select_related('ad_group_source__source').group_current_settings()

        settings_on_date = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=tz_sources,
            created_dt__gte=dt_tz,
            created_dt__lt=dt_tz + datetime.timedelta(days=1),
        ).select_related('ad_group_source__source').order_by('created_dt')

        for ags_sett in latest_settings_before.iterator():
            ret[ags_sett.ad_group_source_id].append(ags_sett)

        for ags_sett in settings_on_date.iterator():
            ret[ags_sett.ad_group_source_id].append(ags_sett)

    return ret


def _get_ad_groups_min_max_tzs(ad_groups):
    min_max_tzs = dash.models.AdGroupSource.objects.filter(ad_group__in=ad_groups)\
                                                   .aggregate(min_tz=Min('source__source_type__budgets_tz'),
                                                              max_tz=Max('source__source_type__budgets_tz'))

    min_tz = min_max_tzs['min_tz']
    if min_tz is None:
        min_tz = pytz.utc

    max_tz = min_max_tzs['max_tz']
    if max_tz is None:
        max_tz = pytz.utc

    return min_tz, max_tz


def _get_ag_settings_dict(date, ad_groups):
    min_tz, max_tz = _get_ad_groups_min_max_tzs(ad_groups)

    dt_min_tz = min_tz.localize(datetime.datetime(date.year, date.month, date.day)).astimezone(pytz.utc)
    dt_max_tz = max_tz.localize(datetime.datetime(date.year, date.month, date.day)).astimezone(pytz.utc)

    # this is true only for min_tz - last setting before date has to be found for sources with other tzs
    latest_settings_before = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
        created_dt__lt=dt_min_tz,
    ).select_related('ad_group').group_current_settings()

    settings_on_date = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
        created_dt__gte=dt_min_tz,
        created_dt__lt=dt_max_tz + datetime.timedelta(days=1),
    ).select_related('ad_group').order_by('created_dt')

    ret = defaultdict(list)
    for ag_sett in latest_settings_before.iterator():
        ret[ag_sett.ad_group_id].append(ag_sett)

    for ag_sett in settings_on_date.iterator():
        ret[ag_sett.ad_group_id].append(ag_sett)

    return ret


def _get_current_daily_budget_per_ags(campaign):
    ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__campaign=campaign, landing_mode=False).group_current_settings().values_list('id', flat=True)
    active_ag_ids = dash.models.AdGroupSettings.objects.filter(
        id__in=ag_settings,
        state=dash.constants.AdGroupSettingsState.ACTIVE,
    ).values_list('ad_group_id', flat=True)

    ags_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group_id__in=active_ag_ids
    ).group_current_settings().select_related('ad_group_source__source')

    ret = {}
    for ags_settings in ags_settings:
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
            continue

        current_daily_budget = ags_settings.daily_budget_cc
        if not current_daily_budget:
            current_daily_budget = ags_settings.ad_group_source.source.default_daily_budget_cc

        ret[ags_settings.ad_group_source_id] = current_daily_budget
    return ret


def _get_current_daily_budget(campaign):
    return sum(_get_current_daily_budget_per_ags(campaign).values())


def _get_user_daily_budget_per_ags(campaign):
    ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__campaign=campaign, landing_mode=False).group_current_settings().values_list('id', flat=True)
    active_ag_ids = dash.models.AdGroupSettings.objects.filter(
        id__in=ag_settings,
        state=dash.constants.AdGroupSettingsState.ACTIVE,
    ).values_list('ad_group_id', flat=True)

    ags_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group_id__in=active_ag_ids, landing_mode=False
    ).group_current_settings().select_related('ad_group_source__source')

    ret = {}
    for ags_settings in ags_settings:
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
            continue

        current_daily_budget = ags_settings.daily_budget_cc
        if not current_daily_budget:
            current_daily_budget = ags_settings.ad_group_source.source.default_daily_budget_cc

        ret[ags_settings.ad_group_source_id] = current_daily_budget
    return ret


def _get_max_daily_budget_per_ags(date, campaign):
    ad_groups = campaign.adgroup_set.all()
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')

    ad_group_settings = _get_ag_settings_dict(date, ad_groups)
    ad_group_sources_settings = _get_sources_settings_dict(date, ad_group_sources)

    max_daily_budget = {}
    for ags in ad_group_sources:
        max_daily_budget[ags.id] = _get_source_max_daily_budget(
            date,
            ags,
            ad_group_settings[ags.ad_group_id],
            ad_group_sources_settings[ags.id],
        )

    return max_daily_budget


def _get_max_daily_budget(date, campaign):
    return sum(_get_max_daily_budget_per_ags(date, campaign).values())


def _get_effective_daily_budget(date, ad_group_source, ag_settings, ags_settings):
    if ag_settings.state != dash.constants.AdGroupSettingsState.ACTIVE or\
       ags_settings.state != dash.constants.AdGroupSourceSettingsState.ACTIVE or\
       (ag_settings.end_date and ag_settings.end_date < date):
        return 0

    daily_budget_cc = ags_settings.daily_budget_cc
    if not daily_budget_cc:
        daily_budget_cc = ad_group_source.source.default_daily_budget_cc

    return daily_budget_cc


def _get_lookahead_iter(iterable):
    """
    Returns iterable over [(el_1, el_2), (el_2, el_3), ..., (el_n, None)]
    """
    it1, it2 = tee(iterable)
    next(it2, None)
    return izip_longest(it1, it2)


def _prepare_valid_ad_group_settings(date, ad_group_source, ad_group_settings):
    """
    Prepare ad group settings array so it contains at most one setting from the
    previous day taking the ad group source timezone into account.
    """
    if not ad_group_settings:
        return []

    budgets_tz = ad_group_source.source.source_type.budgets_tz
    ag_settings_iter = _get_lookahead_iter(ad_group_settings)
    for i, (ag_settings, next_ag_settings) in enumerate(ag_settings_iter):
        if not next_ag_settings or\
           dates_helper.utc_to_tz_datetime(next_ag_settings.created_dt, budgets_tz).date() == date:
            return ad_group_settings[i:]


def _get_matching_settings_pairs(ad_group_settings, ad_group_source_settings):
    """
    Return pairs of ad group and ad group source settings that were active at the same time.
    Inputs are expected to be sorted.
    """
    if not ad_group_settings or not ad_group_source_settings:
        return []

    ag_settings_iter = _get_lookahead_iter(ad_group_settings)
    ag_settings, next_ag_settings = next(ag_settings_iter)

    pairs = []
    for ags_settings, next_ags_settings in _get_lookahead_iter(ad_group_source_settings):
        pairs.append((ag_settings, ags_settings))
        if not next_ags_settings and next_ag_settings:
            pairs.append((next_ag_settings, ags_settings))
            continue

        if next_ag_settings and next_ags_settings.created_dt > next_ag_settings.created_dt:
            pairs.append((next_ag_settings, ags_settings))
            ag_settings, next_ag_settings = next(ag_settings_iter)

    return pairs


def _get_source_max_daily_budget(date, ad_group_source, ad_group_settings, ad_group_source_settings):
    ad_group_settings = _prepare_valid_ad_group_settings(date, ad_group_source, ad_group_settings)
    pairs = _get_matching_settings_pairs(ad_group_settings, ad_group_source_settings)
    if not pairs:
        return 0

    max_daily_budget = max(_get_effective_daily_budget(date, ad_group_source, pair[0], pair[1]) for pair in pairs)
    return max_daily_budget


def _get_ad_groups_latest_end_dates(ad_groups):
    ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
    ).group_current_settings().values('ad_group_id', 'end_date')
    return {sett['ad_group_id']: sett['end_date'] for sett in ag_settings}


def _get_ag_ids_active_on_date(date, ad_groups):
    ag_ids_active_on_date = set(
        dash.models.AdGroupSettings.objects.filter(
            ad_group__in=ad_groups,
            created_dt__lt=date + datetime.timedelta(days=1),
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
    ad_group_end_dates = _get_ad_groups_latest_end_dates(ad_groups)
    ag_ids_active_on_date = _get_ag_ids_active_on_date(date, ad_groups)

    running_ad_groups = set()
    for ad_group in ad_groups:
        end_date = ad_group_end_dates.get(ad_group.id)
        if ad_group.id in ag_ids_active_on_date and (end_date is None or end_date >= date):
            running_ad_groups.add(ad_group)

    return running_ad_groups


def _trigger_update_pagerduty(campaign):
    incident_key = 'campaign_stop_update_failed'
    description = 'Campaign stop update failed'
    _trigger_pagerduty(campaign, incident_key, description)


def _trigger_check_pagerduty(campaign):
    incident_key = 'campaign_stop_check_failed'
    description = 'Campaign stop check failed'
    _trigger_pagerduty(campaign, incident_key, description)


def _trigger_pagerduty(campaign, incident_key, description):
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
        incident_key=incident_key,
        description=description,
        details={
            'campaign_id': campaign.id,
        }
    )


def _send_campaign_stop_notification_email(campaign, campaign_settings, available_tomorrow,
                                           max_daily_budget, yesterday_spend):
    subject = 'Campaign is switching to landing mode'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) has been switched to automated landing mode because it is approaching the budget limit.

The available media budget remaining tomorrow is ${available_tomorrow:.2f}, current media daily cap is ${max_daily_budget:.2f} and yesterday's media spend was ${yesterday_spend:.2f}.

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
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget'.format(campaign.pk)),
        available_tomorrow=available_tomorrow,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    account_settings = campaign.account.get_current_settings()
    _send_notification_email(subject, body, campaign_settings, account_settings)


def _send_depleting_budget_notification_email(campaign, campaign_settings, available_tomorrow,
                                              max_daily_budget, yesterday_spend):
    subject = 'Campaign is running out of budget'
    body = u'''Hi, campaign manager,

your campaign {campaign_name} ({account_name}) will soon run out of budget.

The available media budget remaining tomorrow is ${available_tomorrow:.2f}, current media daily cap is ${max_daily_budget:.2f} and yesterday's media spend was ${yesterday_spend:.2f}.

Please add the budget to continue to adjust media sources settings by your needs, if you don’t want campaign to end in a few days. To do so please visit {campaign_budgets_url} and assign budget to your campaign.

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
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget'.format(campaign.pk)),
        available_tomorrow=available_tomorrow,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    account_settings = campaign.account.get_current_settings()
    _send_notification_email(subject, body, campaign_settings, account_settings)


def _send_notification_email(subject, body, campaign_settings, account_settings):
    emails = []
    if account_settings.default_account_manager:
        emails.append(account_settings.default_account_manager.email)
    if campaign_settings.campaign_manager:
        emails.append(campaign_settings.campaign_manager.email)

    email_helper.send_notification_mail(emails, subject, body)
    email_helper.send_notification_mail(['luka.silovinac@zemanta.com'], subject, body)
