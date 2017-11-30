# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging
import decimal
from itertools import tee, izip_longest

from django.db import transaction
from django.db.models import Min, Max, Q

import pytz

from automation import autopilot_settings, models

import dash.constants
import dash.models

import redshiftapi.api_breakdowns

import utils.k1_helper
from utils import dates_helper, email_helper, url_helper, pagerduty_helper

logger = logging.getLogger(__name__)

NON_SPENDING_SOURCE_THRESHOLD_DOLLARS = decimal.Decimal('1')
DECIMAL_ZERO = decimal.Decimal(0)
JOB_HOUR_UTC = 12


def run_job():
    not_landing = list(dash.models.Campaign.objects.all().exclude_landing().iterator())
    in_landing = list(dash.models.Campaign.objects.all().select_related('account').filter_landing().iterator())

    try:
        switch_low_budget_campaigns_to_landing_mode(not_landing, pagerduty_on_fail=True)
        update_campaigns_in_landing(in_landing, pagerduty_on_fail=True)
    except Exception:
        _trigger_job_pagerduty()


def switch_low_budget_campaigns_to_landing_mode(campaigns, pagerduty_on_fail=False):
    campaign_settings = {
        sett.campaign_id: sett
        for sett in dash.models.CampaignSettings.objects.filter(campaign__in=campaigns).group_current_settings()
    }

    for campaign in campaigns:
        try:
            changed = _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings[campaign.id])
        except Exception:
            logger.exception('Campaign stop check for campaign with id %s not successful', campaign.id)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes=u'Failed to check non-landing campaign.'
            )
            if pagerduty_on_fail:
                _trigger_check_pagerduty()
            continue
        if changed:
            utils.k1_helper.update_ad_groups(
                (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
                msg='campaign_stop.switch_low_budget_campaign'
            )


def perform_landing_mode_check(campaign, campaign_settings):
    switched_to_landing = _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings)
    if switched_to_landing:
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.perform_landing_mode_check_switch'
        )
        return True

    resumed = _check_and_resume_campaign(campaign, campaign_settings)
    if resumed:
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.perform_landing_mode_check_resume'
        )
        return True

    return False


def is_campaign_running_out_of_budget(campaign, campaign_settings):
    return _check_campaign_for_landing_mode(campaign, campaign_settings)[1]


def _check_campaign_for_landing_mode(campaign, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return False, False

    if campaign_settings.landing_mode:
        return False, False

    today = dates_helper.local_today()
    max_daily_budget = _get_max_daily_budget(today, campaign)
    current_daily_budget = _get_user_daily_budget(today, campaign)
    _, available_tomorrow, _ = _get_minimum_remaining_budget(campaign, max_daily_budget)

    should_switch = available_tomorrow < current_daily_budget
    is_near_depleted = current_daily_budget <= available_tomorrow < current_daily_budget * 2

    return should_switch, is_near_depleted


def _check_and_switch_campaign_to_landing_mode(campaign, campaign_settings):
    should_switch, is_near_depleted = _check_campaign_for_landing_mode(campaign, campaign_settings)
    if should_switch:
        with transaction.atomic():
            _switch_campaign_to_landing_mode(campaign)
        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all().filter_active()),
            msg='campaign_stop.check_and_switch_campaign_to_landing_mode'
        )
        _send_campaign_stop_notification_email(campaign)
    elif is_near_depleted:
        _send_depleting_budget_notification_email(campaign)

    return should_switch


def _check_and_resume_campaign(campaign, campaign_settings):
    if _can_resume_campaign(campaign, campaign_settings):
        with transaction.atomic():
            _resume_campaign(campaign)
            return True
    return False


def get_minimum_budget_amount(budget_item):
    if budget_item.campaign.account.uses_bcm_v2:
        return _get_minimum_budget_amount_bcm_v2(budget_item)

    if budget_item.state() != dash.constants.BudgetLineItemState.ACTIVE:
        return None

    if not budget_item.campaign.get_current_settings().automatic_campaign_stop:
        return None

    today = dates_helper.local_today()
    covered_amount = _combined_active_budget_from_other_items(budget_item)
    spend = budget_item.get_spend_data()['etf_total']

    max_daily_budget = _get_max_daily_budget(today, budget_item.campaign)
    daily_budgets = max_daily_budget / (1 - budget_item.credit.license_fee)
    return spend + max(daily_budgets - covered_amount, DECIMAL_ZERO)


def _get_minimum_budget_amount_bcm_v2(budget_item):
    if budget_item.state() != dash.constants.BudgetLineItemState.ACTIVE:
        return None

    if not budget_item.campaign.get_current_settings().automatic_campaign_stop:
        return None

    today = dates_helper.local_today()
    covered_amount = _combined_active_budget_from_other_items_bcm_v2(budget_item)
    spend = budget_item.get_spend_data()['etfm_total']

    max_daily_budget = _get_max_daily_budget(today, budget_item.campaign)
    return spend + max(max_daily_budget - covered_amount, DECIMAL_ZERO)


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
    return not (utc_now.hour < JOB_HOUR_UTC and any_source_after_midnight)


def update_campaigns_in_landing(campaigns, pagerduty_on_fail=True):
    for campaign in campaigns:
        logger.info('updating in landing campaign with id %s', campaign.id)
        try:
            with transaction.atomic():
                _update_landing_campaign(campaign)
        except Exception:
            logger.exception('Updating landing mode campaign with id %s not successful', campaign.id)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes=u'Failed to update landing campaign.'
            )
            if pagerduty_on_fail:
                _trigger_update_pagerduty()
            continue

        utils.k1_helper.update_ad_groups(
            (ad_group.pk for ad_group in campaign.adgroup_set.all()),
            msg='update_campaigns_in_landing'
        )


def can_enable_all_ad_groups(campaign, campaign_settings, ad_groups):
    if not campaign_settings.automatic_campaign_stop:
        return True

    if campaign_settings.landing_mode:
        return False

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    current_ag_settings = {}
    for ag_settings in dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
    ).group_current_settings().select_related('ad_group'):
        current_ag_settings[ag_settings.ad_group] = ag_settings

    current_ags_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups,
    ).group_current_settings().select_related('ad_group_source__source')

    inactive_ad_group_settings = [
        s for s in current_ag_settings.values() if s.state != dash.constants.AdGroupSettingsState.ACTIVE
    ]

    inactive_ad_group_active_ags_settings = [
        agss for agss in current_ags_settings if
        current_ag_settings[agss.ad_group_source.ad_group].state != dash.constants.AdGroupSettingsState.ACTIVE and
        agss.state == dash.constants.AdGroupSourceSettingsState.ACTIVE
    ]

    inactive_ad_groups_with_active_b1_group = [
        ags.ad_group for ags in inactive_ad_group_settings if ags.b1_sources_group_enabled and
        ags.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE
    ]

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    return _can_enable_all_sources(
        campaign,
        [s.ad_group_source for s in inactive_ad_group_active_ags_settings],
        inactive_ad_groups_with_active_b1_group,
        current_ag_settings.values(),
        current_ags_settings,
        max_daily_budget_per_ags,
        max_group_daily_budget_per_ag,
        remaining_today,
        available_tomorrow
    )


def can_enable_ad_groups(campaign, campaign_settings):
    ad_groups = campaign.adgroup_set.all().exclude_archived()

    if not campaign_settings.automatic_campaign_stop:
        return {ag.id: True for ag in ad_groups}

    if campaign_settings.landing_mode:
        return {ag.id: False for ag in ad_groups}

    current_ag_settings = {}
    for ag_settings in dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups
    ).group_current_settings().select_related('ad_group'):
        current_ag_settings[ag_settings.ad_group] = ag_settings

    current_active_ags_settings = defaultdict(list)
    for ags_settings in dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups,
    ).group_current_settings().select_related('ad_group_source__source'):
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            current_active_ags_settings[ags_settings.ad_group_source.ad_group].append(ags_settings)

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    ret = {}
    for ad_group in ad_groups:
        ag_settings = current_ag_settings[ad_group]
        if ag_settings.state == dash.constants.AdGroupSettingsState.ACTIVE:
            ret[ad_group.id] = True
            continue

        ad_groups = []
        if ag_settings.b1_sources_group_enabled and\
           ag_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            ad_groups = [ad_group]  # b1 sources group is active - it adds budget if enabled

        active_ad_group_sources = [s.ad_group_source for s in current_active_ags_settings[ad_group]]
        ret[ad_group.id] = _can_enable_all_sources(
            campaign,
            active_ad_group_sources,
            ad_groups,
            [ag_settings],
            current_active_ags_settings[ad_group],
            max_daily_budget_per_ags,
            max_group_daily_budget_per_ag,
            remaining_today,
            available_tomorrow
        )

    return ret


def can_enable_media_source(ad_group_source, campaign, campaign_settings, ad_group_settings):
    return can_enable_all_media_sources(campaign, campaign_settings, [ad_group_source], ad_group_settings)


def can_enable_media_sources(ad_group, campaign, campaign_settings, ad_group_settings):
    ad_group_sources = ad_group.adgroupsource_set.all()
    if not campaign_settings.automatic_campaign_stop or\
       ad_group_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return {ags.id: True for ags in ad_group_sources}

    if campaign_settings.landing_mode:
        return {ags.id: False for ags in ad_group_sources}

    return _can_enable_media_sources(ad_group_sources, campaign)


def can_enable_b1_sources_group(ad_group, campaign, ad_group_settings, campaign_settings):
    if not campaign_settings.automatic_campaign_stop:
        return True

    if campaign_settings.landing_mode:
        return False

    if ad_group_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return True

    if ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
        return True

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    return _can_enable_all_sources(
        campaign,
        [],
        [ad_group],
        [ad_group_settings],
        [],
        max_daily_budget_per_ags,
        max_group_daily_budget_per_ag,
        remaining_today,
        available_tomorrow
    )


def can_enable_all_media_sources(campaign, campaign_settings, ad_group_sources, ad_group_settings):
    if not campaign_settings.automatic_campaign_stop:
        return True

    if campaign_settings.landing_mode:
        return False

    if ad_group_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return True

    current_ags_settings = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources,
    ).group_current_settings().select_related('ad_group_source__source')

    inactive_ad_group_sources = [
        agss.ad_group_source for agss in current_ags_settings if
        agss.state == dash.constants.AdGroupSourceSettingsState.INACTIVE
    ]
    current_ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=set(ags.ad_group for ags in ad_group_sources)
    ).group_current_settings().select_related('ad_group')

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    return _can_enable_all_sources(
        campaign,
        inactive_ad_group_sources,
        [],  # NOTE: assumes b1 group can't be enabled in bulk actions
        current_ag_settings,
        current_ags_settings,
        max_daily_budget_per_ags,
        max_group_daily_budget_per_ag,
        remaining_today,
        available_tomorrow
    )


def get_max_settable_source_budget(
        ad_group_source,
        campaign,
        ad_group_source_settings,
        ad_group_settings,
        campaign_settings
):

    if _is_ags_always_in_budget_group(ad_group_source, [ad_group_settings]):
        return None

    if not campaign_settings.automatic_campaign_stop:
        return None

    if campaign_settings.landing_mode:
        return DECIMAL_ZERO

    if ad_group_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return None

    if ad_group_source_settings.state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
        return None

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    user_daily_budget_per_ags, user_group_daily_budget_per_ag = _get_user_daily_budget_per_ags(today, campaign)
    max_ags_daily_budget = max_daily_budget_per_ags.get(ad_group_source.id, DECIMAL_ZERO)
    user_ags_daily_budget = user_daily_budget_per_ags.get(ad_group_source.id, DECIMAL_ZERO)
    return _get_max_settable_daily_budget(
        campaign,
        max_ags_daily_budget,
        user_ags_daily_budget,
        max_daily_budget_per_ags,
        user_daily_budget_per_ags,
        max_group_daily_budget_per_ag,
        user_group_daily_budget_per_ag,
    )


def get_max_settable_b1_sources_group_budget(
        ad_group,
        campaign,
        ad_group_settings,
        campaign_settings
):
    if not campaign_settings.automatic_campaign_stop:
        return None

    if campaign_settings.landing_mode:
        return DECIMAL_ZERO

    if ad_group_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return None

    if ad_group_settings.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
        return None

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    user_daily_budget_per_ags, user_group_daily_budget_per_ag = _get_user_daily_budget_per_ags(today, campaign)
    max_group_daily_budget = max_group_daily_budget_per_ag.get(ad_group.id, DECIMAL_ZERO)
    user_group_daily_budget = user_group_daily_budget_per_ag.get(ad_group.id, DECIMAL_ZERO)
    return _get_max_settable_daily_budget(
        campaign,
        max_group_daily_budget,
        user_group_daily_budget,
        max_daily_budget_per_ags,
        user_daily_budget_per_ags,
        max_group_daily_budget_per_ag,
        user_group_daily_budget_per_ag,
    )


def get_max_settable_autopilot_budget(
        ad_group,
        campaign,
        ad_group_settings,
        campaign_settings,
):
    if not campaign_settings.automatic_campaign_stop:
        return None

    if campaign_settings.landing_mode:
        return DECIMAL_ZERO

    if ad_group_settings.state != dash.constants.AdGroupSettingsState.ACTIVE:
        return None

    if ad_group_settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return None

    today = dates_helper.local_today()
    max_daily_budgets = _get_max_daily_budget_per_ags(today, campaign)
    user_daily_budgets = _get_user_daily_budget_per_ags(today, campaign)

    # NOTE: takes sums of all max and user daily budgets because autopilot is potentially
    # changing all budgets
    return _get_max_settable_daily_budget(
        campaign,
        _sum_daily_budget(*max_daily_budgets),
        _sum_daily_budget(*user_daily_budgets),
        max_daily_budgets[0],
        user_daily_budgets[0],
        max_daily_budgets[1],
        user_daily_budgets[1],
    )


def _get_max_settable_daily_budget(campaign,
                                   max_budget_today,
                                   user_budget_today,
                                   max_daily_budget_per_ags,
                                   user_daily_budget_per_ags,
                                   max_group_daily_budget_per_ag,
                                   user_group_daily_budget_per_ag):
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign,
        _sum_daily_budget(max_daily_budget_per_ags,
                          max_group_daily_budget_per_ag)
    )

    utc_now = dates_helper.utc_now()
    max_today = decimal.Decimal(max_budget_today + remaining_today)\
                       .to_integral_exact(rounding=decimal.ROUND_CEILING)
    if utc_now.hour < JOB_HOUR_UTC:
        # NOTE: if there wont' be enough budget for tomorrow, landing mode
        # should trigger when job runs
        return max(max_today, max_budget_today)

    other_sources_user_sum = _sum_daily_budget(
        user_daily_budget_per_ags,
        user_group_daily_budget_per_ag,
    ) - user_budget_today
    max_tomorrow = decimal.Decimal(available_tomorrow - other_sources_user_sum)\
                          .to_integral_exact(rounding=decimal.ROUND_CEILING)
    return max(min(max_today, max_tomorrow), max_budget_today)


def _can_enable_media_sources(ad_group_sources, campaign):
    current_ags_settings = {}
    for ags_settings in dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__in=ad_group_sources,
    ).group_current_settings().select_related('ad_group_source__source'):
        current_ags_settings[ags_settings.ad_group_source] = ags_settings

    current_ag_settings = {}
    for ag_settings in (dash.models.AdGroupSettings.objects.filter(
            ad_group__in=set(ags.ad_group for ags in ad_group_sources))
            .group_current_settings().select_related('ad_group')):
        current_ag_settings[ag_settings.ad_group] = ag_settings

    today = dates_helper.local_today()
    max_daily_budget_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)
    remaining_today, available_tomorrow, _ = _get_minimum_remaining_budget(
        campaign, _sum_daily_budget(max_daily_budget_per_ags, max_group_daily_budget_per_ag))

    ret = {}
    for ad_group_source, ags_settings in current_ags_settings.iteritems():
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            ret[ad_group_source.id] = True
            continue

        ag_settings = current_ag_settings[ad_group_source.ad_group]

        daily_budget_cc = 0
        daily_budget_added = 0

        if _is_ags_always_in_budget_group(ad_group_source, [ag_settings]):
            daily_budget_cc = ag_settings.b1_sources_group_daily_budget
            daily_budget_added = daily_budget_cc - max_group_daily_budget_per_ag.get(ad_group_source.ad_group_id, DECIMAL_ZERO)
        else:
            daily_budget_cc = ags_settings.daily_budget_cc
            if not daily_budget_cc:
                daily_budget_cc = ad_group_source.source.default_daily_budget_cc
            daily_budget_added = daily_budget_cc - max_daily_budget_per_ags.get(ad_group_source.id, DECIMAL_ZERO)

        can_enable_today = daily_budget_added <= remaining_today
        can_enable_tomorrow = daily_budget_added + daily_budget_cc <= available_tomorrow

        ret[ad_group_source.id] = can_enable_today and can_enable_tomorrow

    return ret


def _can_enable_all_sources(
        campaign,
        ad_group_sources,
        b1_group_ad_groups,
        ad_groups_settings,
        ad_group_sources_settings,
        max_daily_budget_per_ags, max_group_daily_budget,
        remaining_today, available_tomorrow):

    ad_groups_settings_map = {ags.ad_group_id: ags for ags in ad_groups_settings}
    ad_group_sources_settings_map = {agss.ad_group_source_id: agss for agss in ad_group_sources_settings}

    ags_daily_budget_added, ags_daily_budget_total = _get_ad_group_sources_daily_budget_change(
        ad_group_sources,
        ad_groups_settings_map,
        ad_group_sources_settings_map,
        max_daily_budget_per_ags,
    )
    b1_groups_daily_budget_added, b1_groups_daily_budget_total = _get_b1_groups_daily_budget_change(
        b1_group_ad_groups,
        ad_groups_settings_map,
        max_group_daily_budget,
    )

    daily_budget_added = ags_daily_budget_added + b1_groups_daily_budget_added
    daily_budget_total = ags_daily_budget_total + b1_groups_daily_budget_total

    can_enable_today = daily_budget_added <= remaining_today
    can_enable_tomorrow = daily_budget_added + daily_budget_total <= available_tomorrow

    return can_enable_today and can_enable_tomorrow


def _get_ad_group_sources_daily_budget_change(ad_group_sources, ad_groups_settings_map,
                                              ad_group_sources_settings_map, max_daily_budget_per_ags):
    daily_budget_added = 0
    daily_budget_total = 0

    for ad_group_source in ad_group_sources:
        ad_group_source_settings = ad_group_sources_settings_map[ad_group_source.id]
        ad_group_settings = ad_groups_settings_map[ad_group_source.ad_group_id]
        if _is_ags_always_in_budget_group(ad_group_source, [ad_group_settings]):
            continue

        max_daily_budget = max_daily_budget_per_ags.get(ad_group_source.id, DECIMAL_ZERO)
        current_daily_budget = ad_group_source_settings.daily_budget_cc
        if not current_daily_budget:
            current_daily_budget = ad_group_source.source.default_daily_budget_cc

        daily_budget_total += current_daily_budget
        daily_budget_added += max(0, current_daily_budget - max_daily_budget)

    return daily_budget_added, daily_budget_total


def _get_b1_groups_daily_budget_change(ad_groups, ad_groups_settings_map, max_group_daily_budget):
    daily_budget_added = 0
    daily_budget_total = 0

    for ad_group in ad_groups:
        ad_group_settings = ad_groups_settings_map[ad_group.id]
        if not ad_group_settings.b1_sources_group_enabled:
            continue

        max_daily_budget = max_group_daily_budget.get(ad_group_settings.ad_group_id, DECIMAL_ZERO)
        current_daily_budget = ad_group_settings.b1_sources_group_daily_budget

        daily_budget_total += current_daily_budget
        daily_budget_added += max(0, current_daily_budget - max_daily_budget)

    return daily_budget_added, daily_budget_total


def get_min_budget_increase(campaign):
    today = dates_helper.local_today()
    user_daily_budget_per_ags, user_group_daily_budget_per_ag = _get_user_daily_budget_per_ags(today, campaign)
    max_daily_budgets_per_ags, max_group_daily_budget_per_ag = _get_max_daily_budget_per_ags(today, campaign)

    max_daily_budget = DECIMAL_ZERO
    all_ags_keys = set(user_daily_budget_per_ags.keys()) | set(max_daily_budgets_per_ags.keys())
    for ags_id in all_ags_keys:
        user_ags_daily_budget = user_daily_budget_per_ags.get(ags_id, DECIMAL_ZERO)
        max_ags_daily_budget = max_daily_budgets_per_ags.get(ags_id, DECIMAL_ZERO)
        max_daily_budget += max(user_ags_daily_budget, max_ags_daily_budget)

    all_ag_keys = set(user_group_daily_budget_per_ag.keys()) | set(max_group_daily_budget_per_ag.keys())
    for ag_id in all_ag_keys:
        user_daily_budget = user_group_daily_budget_per_ag.get(ag_id, DECIMAL_ZERO)
        max_ag_daily_budget = max_group_daily_budget_per_ag.get(ag_id, DECIMAL_ZERO)
        max_daily_budget += max(user_daily_budget, max_ag_daily_budget)

    _, available_tomorrow, min_needed_today = _get_minimum_remaining_budget(campaign, max_daily_budget)

    user_daily_budget_sum = _sum_daily_budget(user_daily_budget_per_ags, user_group_daily_budget_per_ag)
    min_needed_tomorrow = max(user_daily_budget_sum - available_tomorrow, DECIMAL_ZERO)

    max_license_fee = dash.models.BudgetLineItem.objects.filter(
        campaign=campaign
    ).filter_active().aggregate(Max('credit__license_fee'))['credit__license_fee__max']

    budget_needed = min_needed_today + min_needed_tomorrow
    if not campaign.account.uses_bcm_v2 and budget_needed and max_license_fee:
        budget_needed = budget_needed / (1 - max_license_fee)

    return budget_needed


def _combined_active_budget_from_other_items(budget_item):
    other_active_budgets = dash.models.BudgetLineItem.objects.filter(
        campaign=budget_item.campaign
    ).filter_active().exclude(pk=budget_item.pk)
    return sum(
        b.get_available_amount() for b in other_active_budgets
    )


def _combined_active_budget_from_other_items_bcm_v2(budget_item):
    other_active_budgets = dash.models.BudgetLineItem.objects.filter(
        campaign=budget_item.campaign
    ).filter_active().exclude(pk=budget_item.pk)
    return sum(
        b.get_available_etfm_amount() for b in other_active_budgets
    )


def _can_resume_campaign(campaign, campaign_settings):
    if not campaign_settings.landing_mode:
        return False

    if not campaign_settings.automatic_campaign_stop:
        return True

    return get_min_budget_increase(campaign) == 0


def _get_minimum_remaining_budget(campaign, max_daily_budget):
    today = dates_helper.local_today()

    budgets_active_today = _get_budgets_active_on_date(today, campaign)
    budgets_active_tomorrow = _get_budgets_active_on_date(today + datetime.timedelta(days=1), campaign)

    per_budget_remaining_today = {}
    unattributed_budget = max_daily_budget
    for bli in budgets_active_today.order_by('created_dt'):
        if campaign.account.uses_bcm_v2:
            spend_available = bli.get_available_etfm_amount(date=dates_helper.local_yesterday())
        else:
            spend_without_fee_pct = 1 - bli.credit.license_fee
            spend_available = bli.get_available_amount(date=dates_helper.local_yesterday())
            spend_available = spend_available * spend_without_fee_pct
        # this is a workaround for a bug when a budget line item can have negative amount available
        spend_available = max(0, spend_available)
        per_budget_remaining_today[bli.id] = max(0, spend_available - unattributed_budget)
        unattributed_budget = max(0, unattributed_budget - spend_available)

    remaining_today = decimal.Decimal(sum(per_budget_remaining_today.itervalues()))
    available_tomorrow = DECIMAL_ZERO
    for bli in budgets_active_tomorrow.order_by('created_dt'):
        if campaign.account.uses_bcm_v2:
            available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount)
        else:
            spend_without_fee_pct = 1 - bli.credit.license_fee
            available_tomorrow += per_budget_remaining_today.get(bli.id, bli.amount * spend_without_fee_pct)

    return remaining_today, available_tomorrow, unattributed_budget


def _update_landing_campaign(campaign):
    """
    Stops ad groups and sources that have no spend yesterday and divide remaining budget between the rest
    """
    campaign_settings = campaign.get_current_settings()
    if _can_resume_campaign(campaign, campaign_settings):
        _resume_campaign(campaign)
        return

    if not campaign.adgroup_set.all().filter_active().count() > 0:
        _wrap_up_landing(campaign)
        return

    _check_ad_groups_end_date(campaign)
    if not campaign.adgroup_set.all().filter_active().count() > 0:
        _wrap_up_landing(campaign)
        return

    per_date_spend, _ = _get_past_7_days_data(campaign)
    daily_caps = _calculate_daily_caps(campaign, per_date_spend)
    _adjust_source_caps(campaign, daily_caps)
    if not campaign.adgroup_set.all().filter_active().count() > 0:
        _wrap_up_landing(campaign)
        return

    _set_end_date_to_today(campaign)


def _check_ad_groups_end_date(campaign):
    today = dates_helper.local_today()
    finished = []
    for ad_group in campaign.adgroup_set.all().filter_active():
        user_settings = _get_last_user_ad_group_settings(ad_group)
        if user_settings.end_date and user_settings.end_date < today:
            finished.append(ad_group)
            _stop_ad_group(ad_group)

    if finished:
        models.CampaignStopLog.objects.create(
            campaign=campaign,
            notes=u'Stopped finished ad groups {}'.format(', '.join(
                unicode(ad_group) for ad_group in finished
            ))
        )


def _adjust_source_caps(campaign, daily_caps):
    bcm_modifiers = campaign.get_bcm_modifiers()
    active_sources = _get_active_ad_group_sources(campaign)

    flat_ag_group_sources = [ags for ags_list in active_sources.values() for ags in ags_list]
    current_ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=flat_ag_group_sources,
        ).group_current_settings()
    }

    active_ad_groups = active_sources.keys()
    current_ad_group_settings = {
        ags.ad_group_id: ags for ags in dash.models.AdGroupSettings.objects.filter(
            ad_group__in=active_ad_groups,
        ).group_current_settings()
    }

    yesterday_spends = _get_yesterday_source_spends(campaign, active_ad_groups)
    user_daily_budget_per_ags, user_group_daily_budget_per_ag = _get_user_daily_budget_per_ags(
        dates_helper.local_today(), campaign)

    for ad_group, ad_group_sources in active_sources.iteritems():
        ag_settings = current_ad_group_settings[ad_group.id]
        ag_daily_cap = daily_caps[ad_group.id]
        current_daily_cap = DECIMAL_ZERO

        sources_to_stop = set()

        b1_group_spend = DECIMAL_ZERO
        b1_group_stop = True

        active_ad_group_sources = set()

        for ags in ad_group_sources:
            ags_settings = current_ad_group_sources_settings[ags.id]
            spend = yesterday_spends.get((ags.ad_group_id, ags.source_id), DECIMAL_ZERO)

            if _is_ags_always_in_budget_group(ags, [ag_settings]):
                b1_group_spend += decimal.Decimal(spend)
                continue

            if spend < NON_SPENDING_SOURCE_THRESHOLD_DOLLARS:
                sources_to_stop.add(ags)
                continue

            active_ad_group_sources.add(ags)
            current_daily_cap += ags_settings.daily_budget_cc

        if _is_b1_group_enabled(ag_settings):
            if b1_group_spend >= NON_SPENDING_SOURCE_THRESHOLD_DOLLARS:
                current_daily_cap += ag_settings.b1_sources_group_daily_budget
                b1_group_stop = False

        sources_to_stop, sources_new_cap, b1_group_stop, b1_group_new_cap = _calculate_daily_source_caps(
            ag_settings,
            bcm_modifiers,
            current_ad_group_sources_settings,
            user_daily_budget_per_ags,
            user_group_daily_budget_per_ag,
            active_ad_group_sources,
            sources_to_stop,
            b1_group_stop,
            yesterday_spends,
            b1_group_spend,
            ag_daily_cap,
        )

        if len(sources_new_cap) == 0 and b1_group_stop:
            _stop_ad_group(ad_group)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes=u'Stopping ad group {} - lowering budget not possible.\n'
                      'Minimum budget: {}, Daily cap: {}.'.format(
                          ad_group.id,
                          _get_min_ap_budget(ad_group_sources, bcm_modifiers),
                          ag_daily_cap,
                      )
            )
            continue

        if sources_to_stop:
            for ags in sources_to_stop:
                _stop_ad_group_source(ags)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes=u'Stopping sources on ad group {}:\n{}\n\nLowering budget not possible.\n'
                      'Minimum budget: {}, Daily cap: {}.'.format(
                          ad_group.id,
                          '\n'.join([ags.source.name for ags in sorted(sources_to_stop, key=lambda x: x.source.name)]),
                          _get_min_ap_budget(ad_group_sources, bcm_modifiers),
                          ag_daily_cap,
                      )
            )

        if sources_new_cap:
            for ags, cap in sources_new_cap:
                _update_ad_group_source_cap(ags, cap)
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes=u'Updating sources on ad group {}:\n'
                      u'New daily caps:\n{}.'.format(
                          ad_group.id,
                          '\n'.join(["{}: {}".format(ags.source.name, c)
                                     for ags, c in sorted(sources_new_cap, key=lambda x: x[1])]),
                      )
            )

        if _is_b1_group_enabled(ag_settings):
            if b1_group_stop:
                _stop_b1_group(ad_group)
                models.CampaignStopLog.objects.create(
                    campaign=campaign,
                    notes=u'Stopping rtb sources on ad group {}.\n'
                          'Lowering minimum autopilot budget not possible.'.format(
                              ad_group.id,
                          )
                )
            elif b1_group_new_cap:
                _update_b1_group_cap(ad_group, b1_group_new_cap)
                models.CampaignStopLog.objects.create(
                    campaign=campaign,
                    notes=u'Updating rtb sources on ad group {}:\n'
                          u'New daily cap: {}'.format(
                              ad_group.id,
                              b1_group_new_cap,
                          )
                )


def _calculate_daily_source_caps(
        ad_group_settings,
        bcm_modifiers,
        ad_group_sources_settings,
        user_daily_budget_per_ags,
        user_group_daily_budget_per_ag,
        active_ad_group_sources,
        sources_to_stop,
        b1_group_stop,
        yesterday_spends,
        b1_group_yesterday_spend,
        available_daily_cap):

    sorted_ad_group_sources = sorted(
        active_ad_group_sources,
        key=lambda x: yesterday_spends.get((x.ad_group_id, x.source_id), 0),
    )

    total_yesterday_spend = sum(
        decimal.Decimal(yesterday_spends.get((ags.ad_group_id, ags.source_id), 0))
        for ags in active_ad_group_sources if ags.ad_group_id == ad_group_settings.ad_group_id
    ) + b1_group_yesterday_spend
    user_daily_budgets_sum = _sum_daily_budget(user_daily_budget_per_ags, user_group_daily_budget_per_ag)

    sources_new_cap = {}
    for ags in sorted_ad_group_sources:

        if ags in sources_to_stop:
            continue

        min_source_cap = autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET
        source_type_min_daily_budget = ags.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
        if source_type_min_daily_budget:
            min_source_cap = max(min_source_cap, source_type_min_daily_budget)

        source_yesterday_spend = decimal.Decimal(yesterday_spends.get((ags.ad_group_id, ags.source_id), 0))
        user_source_daily_budget = user_daily_budget_per_ags.get(ags.id)

        if total_yesterday_spend:
            cap_ratio = source_yesterday_spend / total_yesterday_spend
        else:
            cap_ratio = user_source_daily_budget / user_daily_budgets_sum
        cap = min(cap_ratio * available_daily_cap, user_source_daily_budget)
        cap = cap.to_integral_exact(rounding=decimal.ROUND_FLOOR)

        if cap < min_source_cap:
            sources_to_stop.add(ags)
            total_yesterday_spend -= source_yesterday_spend
        else:
            sources_new_cap[ags] = cap

    b1_group_new_cap = None
    if _is_b1_group_enabled(ad_group_settings) and not b1_group_stop:
        min_group_cap = dash.constants.SourceAllRTB.get_etfm_min_daily_budget(bcm_modifiers)

        user_group_daily_budget = user_group_daily_budget_per_ag.get(ad_group_settings.ad_group_id, DECIMAL_ZERO)
        if total_yesterday_spend:
            cap_ratio = b1_group_yesterday_spend / total_yesterday_spend
        else:
            cap_ratio = user_group_daily_budget / user_daily_budgets_sum
        cap = min(cap_ratio * available_daily_cap, user_group_daily_budget)
        cap = cap.to_integral_exact(rounding=decimal.ROUND_FLOOR)

        if cap < min_group_cap:
            b1_group_stop = True
        else:
            b1_group_new_cap = cap

    return sources_to_stop, sources_new_cap.items(), b1_group_stop, b1_group_new_cap


def _switch_campaign_to_landing_mode(campaign):
    new_campaign_settings = campaign.get_current_settings().copy_settings()
    new_campaign_settings.landing_mode = True
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_campaign_settings.save(None)

    today = dates_helper.local_today()
    for ad_group in campaign.adgroup_set.all().filter_active():
        new_ag_settings = ad_group.get_current_settings().copy_settings()

        new_ag_settings.landing_mode = True
        new_ag_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
        new_ag_settings.save(None)

        if new_ag_settings.end_date and new_ag_settings.end_date < today:
            _stop_ad_group(ad_group)
        else:
            _set_ad_group_end_date(ad_group, today)

        for ad_group_source in ad_group.adgroupsource_set.all().filter_active():
            new_ags_settings = ad_group_source.get_current_settings().copy_settings()
            new_ags_settings.landing_mode = True
            new_ags_settings.save(None)

    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=u'Switched to landing mode.'
    )


def _resume_campaign(campaign):
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=u'Campaign returned to normal mode - enough campaign budget '
              'today and tomorrow to cover daily spend caps set before landing mode.'
    )
    return _turn_off_landing_mode(campaign, pause_ad_groups=False)


def _wrap_up_landing(campaign):
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=u'Campaign landed - no ad groups are left running.'
    )
    return _turn_off_landing_mode(campaign, pause_ad_groups=True)


def _turn_off_landing_mode(campaign, pause_ad_groups=False):
    current_settings = campaign.get_current_settings()
    new_campaign_settings = current_settings.copy_settings()
    new_campaign_settings.landing_mode = False
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    if new_campaign_settings.get_setting_changes(current_settings):
        new_campaign_settings.save(None)

    for ad_group in campaign.adgroup_set.all().filter_landing():
        _restore_user_ad_group_settings(ad_group, pause_ad_group=pause_ad_groups)


def _get_last_user_ad_group_settings(ad_group):
    try:
        return dash.models.AdGroupSettings.objects.filter(
            ad_group=ad_group,
            landing_mode=False
        ).latest('created_dt')
    except dash.models.AdGroupSettings.DoesNotExist:
        # ad group created by copying while in landing
        # mode doesn't have previous settings
        return None


def _restore_user_ad_group_settings(ad_group, pause_ad_group=False):
    user_settings = _get_last_user_ad_group_settings(ad_group)

    current_settings = ad_group.get_current_settings()

    new_settings = current_settings.copy_settings()
    new_settings.landing_mode = False
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP

    if user_settings:
        new_settings.state = user_settings.state
        new_settings.end_date = user_settings.end_date
        new_settings.b1_sources_group_state = user_settings.b1_sources_group_state
        new_settings.b1_sources_group_daily_budget = user_settings.b1_sources_group_daily_budget

    if pause_ad_group:
        new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE

    new_settings.save(None)
    _restore_user_sources_settings(ad_group)


def _restore_user_sources_settings(ad_group):
    ad_group_sources = ad_group.adgroupsource_set.all()
    user_ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
            landing_mode=False,
        ).latest_per_entity()
    }
    current_ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
        ).group_current_settings()
    }

    for ad_group_source in ad_group.adgroupsource_set.all():
        user_settings = user_ad_group_sources_settings[ad_group_source.id]
        current_settings = current_ad_group_sources_settings[ad_group_source.id]

        changes = {}
        for key in ['state', 'cpc_cc', 'daily_budget_cc', 'landing_mode']:
            if getattr(user_settings, key) == getattr(current_settings, key):
                continue

            changes[key] = getattr(user_settings, key)

        ad_group_source.update(
            request=None,
            system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            **changes
        )


def _stop_ad_group(ad_group):
    new_settings = ad_group.get_current_settings().copy_settings()
    new_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_settings.save(None)


def _set_end_date_to_today(campaign):
    today = dates_helper.local_today()
    for ad_group in campaign.adgroup_set.all().filter_active():
        _set_ad_group_end_date(ad_group, today)
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=u'End date set to {}'.format(today)
    )


def _set_ad_group_end_date(ad_group, end_date):
    current_ag_settings = ad_group.get_current_settings()
    new_ag_settings = current_ag_settings.copy_settings()
    new_ag_settings.end_date = end_date
    new_ag_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_ag_settings.save(None)


def _stop_ad_group_source(ad_group_source):
    ad_group_source.update(
        request=None,
        system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
        k1_sync=False,
        landing_mode=True,
        skip_automation=True,
        skip_validation=True,
        state=dash.constants.AdGroupSourceSettingsState.INACTIVE,
    )


def _update_ad_group_source_cap(ad_group_source, cap):
    ad_group_source.update(
        request=None,
        system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
        k1_sync=False,
        landing_mode=True,
        skip_automation=True,
        skip_validation=True,
        daily_budget_cc=cap,
    )


def _stop_b1_group(ad_group):
    new_settings = ad_group.get_current_settings().copy_settings()
    new_settings.b1_sources_group_state = dash.constants.AdGroupSourceSettingsState.INACTIVE
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_settings.save(None)


def _update_b1_group_cap(ad_group, cap):
    new_settings = ad_group.get_current_settings().copy_settings()
    new_settings.b1_sources_group_daily_budget = cap
    new_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_settings.save(None)


def _get_yesterday_source_spends(campaign, ad_groups):
    yesterday = dates_helper.local_yesterday()
    rows = redshiftapi.api_breakdowns.query_all(
        ['ad_group_id', 'source_id'],
        {
            'date__gte': yesterday,
            'date__lte': yesterday,
            'campaign_id': campaign.id,
            'ad_group_id': [ad_group.id for ad_group in ad_groups],
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )

    yesterday_spends = {}
    for row in rows:
        if campaign.account.uses_bcm_v2:
            spend = decimal.Decimal(row['etfm_cost'] or 0)
        else:
            spend = decimal.Decimal(row['et_cost'] or 0)
        yesterday_spends[(row['ad_group_id'], row['source_id'])] = spend

    return yesterday_spends


def _get_active_ad_group_sources(campaign):
    active_ad_groups = campaign.adgroup_set.all().filter_active()
    active_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=active_ad_groups
    ).filter_active().select_related('ad_group', 'source__source_type')
    active_sources_dict = defaultdict(set)
    for ags in active_sources:
        active_sources_dict[ags.ad_group].add(ags)

    return active_sources_dict


def _get_min_ap_budget(ad_group_sources, bcm_modifiers):
    min_daily_budgets = []
    for ags in ad_group_sources:
        min_source_budget = autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET
        source_type_min_daily_budget = ags.source.source_type.get_etfm_min_daily_budget(bcm_modifiers)
        if source_type_min_daily_budget:
            min_source_budget = max(min_source_budget, source_type_min_daily_budget)
        min_daily_budgets.append(min_source_budget)
    return sum(min_daily_budgets)


def _persist_new_daily_caps_to_log(campaign, daily_caps, ad_groups, remaining_today, per_date_spend, daily_cap_ratios):
    notes = u'Calculated ad group daily caps to:\n'
    for ad_group in ad_groups:
        notes += 'Ad group: {}, Daily cap: ${}\n'.format(ad_group.id, daily_caps[ad_group.id])
    notes += u'\nRemaining budget today: {:.2f}\n\n'.format(remaining_today)
    notes += u'Past spends:\n'
    for ad_group in sorted(ad_groups, key=lambda ag: ag.name):
        per_date_ag_spend = [amount for key, amount in per_date_spend.iteritems() if key[0] == ad_group.id]
        notes += u'Ad group: {} ({}), Past 7 day spend: {:.2f}, Avg: {:.2f} (was running for {} days), '\
                 u'Calculated ratio: {:.2f}\n'.format(
                     ad_group.name,
                     ad_group.id,
                     sum(per_date_ag_spend),
                     sum(per_date_ag_spend) / len(per_date_ag_spend) if len(per_date_ag_spend) > 0 else 0,
                     len(per_date_ag_spend),
                     daily_cap_ratios.get(ad_group.id, DECIMAL_ZERO),
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
    overflow = DECIMAL_ZERO
    for ad_group in active_ad_groups:
        cap_dec = remaining_today * decimal.Decimal(daily_cap_ratios.get(ad_group.id, DECIMAL_ZERO)) + overflow
        cap_rounded = cap_dec.to_integral_exact(rounding=decimal.ROUND_FLOOR)
        overflow = cap_dec - cap_rounded

        daily_caps[ad_group.id] = cap_rounded

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
    today = dates_helper.local_today()
    rows = redshiftapi.api_breakdowns.query_all(
        ['date', 'ad_group_id', 'source_id'],
        {
            'date__gte': today - datetime.timedelta(days=7),
            'date__lte': today - datetime.timedelta(days=1),
            'campaign_id': campaign.id,
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )

    date_spend = defaultdict(int)
    source_spend = defaultdict(int)
    for row in rows:
        if campaign.account.uses_bcm_v2:
            spend = decimal.Decimal(row['etfm_cost'] or 0)
        else:
            spend = decimal.Decimal(row['et_cost'] or 0)
        date_spend[(row['ad_group_id'], row['date'])] += spend
        source_spend[(row['ad_group_id'], row['source_id'])] += spend

    return date_spend, source_spend


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
        ).select_related('ad_group_source__source').latest_per_entity()

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
    ).select_related('ad_group').latest_per_entity()

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


def _get_user_daily_budget_per_ags(date, campaign):
    ag_settings = {}
    for s in dash.models.AdGroupSettings.objects.filter(
            ad_group__campaign=campaign, landing_mode=False).latest_per_entity():
        ag_settings[s.ad_group_id] = s

    active_ag_ids = dash.models.AdGroupSettings.objects.filter(
        Q(end_date=None) | Q(end_date__gte=date),
        id__in=[s.id for s in ag_settings.values()],
        state=dash.constants.AdGroupSettingsState.ACTIVE,
    ).values_list('ad_group_id', flat=True)

    ags_settings_list = dash.models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group_id__in=active_ag_ids, landing_mode=False
    ).latest_per_entity().select_related('ad_group_source__source__source_type')

    ags_budget = {}
    for ags_settings in ags_settings_list:
        if ags_settings.state == dash.constants.AdGroupSourceSettingsState.INACTIVE:
            continue

        if _is_ags_always_in_budget_group(
                ags_settings.ad_group_source, [ag_settings[ags_settings.ad_group_source.ad_group_id]]):
            continue

        current_daily_budget = ags_settings.daily_budget_cc
        if not current_daily_budget:
            current_daily_budget = ags_settings.ad_group_source.source.default_daily_budget_cc

        ags_budget[ags_settings.ad_group_source_id] = current_daily_budget

    group_budget_per_ag = {}
    for ad_group_id in active_ag_ids:
        ags_ag_settings = [s for s in ags_settings_list if s.ad_group_source.ad_group_id == ad_group_id]
        b1_group_budget = _get_b1_group_max_daily_budget(date, [ag_settings[ad_group_id]], [ags_ag_settings])
        if b1_group_budget > 0:
            group_budget_per_ag[ad_group_id] = b1_group_budget

    return ags_budget, group_budget_per_ag


def _get_max_daily_budget_per_ags(date, campaign):
    ad_groups = campaign.adgroup_set.all()
    ad_group_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups,
    ).select_related('source__source_type')

    ad_groups_settings = _get_ag_settings_dict(date, ad_groups)
    ad_group_sources_settings = _get_sources_settings_dict(date, ad_group_sources)

    ags_budget = {}
    for ags in ad_group_sources:
        ag_settings, ags_settings = ad_groups_settings[ags.ad_group_id], ad_group_sources_settings[ags.id]

        if _is_ags_always_in_budget_group(ags, ag_settings):
            continue

        ags_budget[ags.id] = _get_source_max_daily_budget(date, ags, ag_settings, ags_settings)

    ad_group_sources_settings_per_ag = defaultdict(list)
    for ags in ad_group_sources:
        ad_group_sources_settings_per_ag[ags.ad_group_id].append(ad_group_sources_settings[ags.id])

    group_budget_per_ag = {}
    for ad_group_id, ad_group_settings in ad_groups_settings.iteritems():
        ad_group_source_settings = ad_group_sources_settings_per_ag[ad_group_id]
        b1_group_budget = _get_b1_group_max_daily_budget(date, ad_group_settings, ad_group_source_settings)
        if b1_group_budget > 0:
            group_budget_per_ag[ad_group_id] = b1_group_budget

    return ags_budget, group_budget_per_ag


def _get_max_daily_budget(date, campaign):
    return _sum_daily_budget(*_get_max_daily_budget_per_ags(date, campaign))


def _get_user_daily_budget(date, campaign):
    return _sum_daily_budget(*_get_user_daily_budget_per_ags(date, campaign))


def _sum_daily_budget(per_ags, per_group):
    return sum(per_ags.values()) + sum(per_group.values())


def _is_b1_group_enabled(ad_group_settings):
    if not ad_group_settings.b1_sources_group_enabled:
        return False
    if ad_group_settings.b1_sources_group_state != dash.constants.AdGroupSourceSettingsState.ACTIVE:
        return False
    return True


def _is_ags_always_in_budget_group(ad_group_source, ad_group_settings):
    if ad_group_source.source.source_type.type != dash.constants.SourceType.B1:
        return False

    if not all(s.b1_sources_group_enabled for s in ad_group_settings):
        return False

    return True


def _get_b1_group_max_daily_budget(date, ad_group_settings, ad_group_sources_settings):
    if not any(s.b1_sources_group_enabled for s in ad_group_settings):
        return DECIMAL_ZERO

    if not any(s.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE for s in ad_group_settings):
        return DECIMAL_ZERO

    running_sources = False
    for ags_list in ad_group_sources_settings:
        if any(s.ad_group_source.source.source_type.type == dash.constants.SourceType.B1 and
                s.state == dash.constants.AdGroupSourceSettingsState.ACTIVE for s in ags_list):
            running_sources = True
            break

    if not running_sources:
        return DECIMAL_ZERO

    if not any(s.state == dash.constants.AdGroupSettingsState.ACTIVE and
               (s.end_date is None or s.end_date >= date) and
               s.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE
               for s in ad_group_settings):
        return DECIMAL_ZERO

    return max(s.b1_sources_group_daily_budget
               for s in ad_group_settings if
               s.state == dash.constants.AdGroupSettingsState.ACTIVE and
               (s.end_date is None or s.end_date >= date) and
               s.b1_sources_group_state == dash.constants.AdGroupSourceSettingsState.ACTIVE)


def _get_effective_daily_budget(date, ad_group_source, ag_settings, ags_settings):
    if ag_settings.state != dash.constants.AdGroupSettingsState.ACTIVE or\
       ags_settings.state != dash.constants.AdGroupSourceSettingsState.ACTIVE or\
       (ag_settings.end_date and ag_settings.end_date < date):
        return DECIMAL_ZERO

    if _is_ags_always_in_budget_group(ad_group_source, [ag_settings]):
        return DECIMAL_ZERO

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

    ags_settings_iter = _get_lookahead_iter(ad_group_source_settings)
    ags_settings, next_ags_settings = next(ags_settings_iter)

    pairs = [(ag_settings, ags_settings)]
    while True:
        if not next_ag_settings and not next_ags_settings:
            break

        if next_ag_settings and not next_ags_settings:
            ag_settings, next_ag_settings = next(ag_settings_iter)
        elif not next_ag_settings and next_ags_settings:
            ags_settings, next_ags_settings = next(ags_settings_iter)
        elif next_ag_settings.created_dt > next_ags_settings.created_dt:
            ags_settings, next_ags_settings = next(ags_settings_iter)
        else:
            ag_settings, next_ag_settings = next(ag_settings_iter)
        pairs.append((ag_settings, ags_settings))

    return pairs


def _get_source_max_daily_budget(date, ad_group_source, ad_group_settings, ad_group_source_settings):
    ad_group_settings = _prepare_valid_ad_group_settings(date, ad_group_source, ad_group_settings)
    pairs = _get_matching_settings_pairs(ad_group_settings, ad_group_source_settings)
    if not pairs:
        return DECIMAL_ZERO

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
    ).latest_per_entity().values('ad_group_id', 'state')
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


def _trigger_job_pagerduty():
    incident_key = 'campaign_stop_job_failed'
    description = 'Exception in campaign stop job'
    _trigger_pagerduty(incident_key, description)


def _trigger_update_pagerduty():
    incident_key = 'campaign_stop_update_failed'
    description = 'Campaign stop update failed'
    _trigger_pagerduty(incident_key, description)


def _trigger_check_pagerduty():
    incident_key = 'campaign_stop_check_failed'
    description = 'Campaign stop check failed'
    _trigger_pagerduty(incident_key, description)


def _trigger_pagerduty(incident_key, description):
    pagerduty_helper.trigger(
        event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
        incident_key=incident_key,
        description=description,
        details={}
    )


def _send_campaign_stop_notification_email(campaign):
    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url(
            '/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings'.format(campaign.pk)
        ),
    }
    subject, body, _ = email_helper.format_email(
        dash.constants.EmailTemplateType.CAMPAIGN_LANDING_MODE_SWITCH,
        **args
    )
    _send_notification_email(subject, body, campaign)


def _send_depleting_budget_notification_email(campaign):
    args = {
        'campaign': campaign,
        'account': campaign.account,
        'link_url': url_helper.get_full_z1_url(
            '/v2/analytics/campaign/{}?settings&settingsScrollTo=zemCampaignBudgetsSettings'.format(campaign.pk)
        ),
    }

    subject, body, _ = email_helper.format_email(
        dash.constants.EmailTemplateType.CAMPAIGN_BUDGET_LOW,
        **args
    )
    _send_notification_email(subject, body, campaign)


def _send_notification_email(subject, body, campaign):
    emails = email_helper.email_manager_list(campaign)
    email_helper.send_notification_mail(emails, subject, body, agency=campaign.account.agency)
