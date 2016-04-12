# -*- coding: utf-8 -*-
from collections import defaultdict
import datetime
import logging
import decimal

from django.db import transaction

import actionlog.api
from actionlog import zwei_actions

from automation import autopilot_budgets, autopilot_cpc, autopilot_plus, autopilot_settings, models

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
        yesterday_spend = _get_yesterday_budget_spend(campaign)
        if available_tomorrow < max_daily_budget_sum:
            with transaction.atomic():
                actions = _switch_campaign_to_landing_mode(campaign)
            zwei_actions.send(actions)
            _send_campaign_stop_notification_email(campaign, remaining_today, max_daily_budget_sum, yesterday_spend)
        elif available_tomorrow < max_daily_budget_sum * 2:
            _send_depleting_budget_notification_email(campaign, remaining_today, max_daily_budget_sum, yesterday_spend)


def update_campaigns_in_landing():
    for campaign in dash.models.Campaign.objects.all().filter_landing().iterator():
        logger.info('updating in landing campaign with id %s', campaign.id)
        actions = []
        try:
            with transaction.atomic():
                actions.extend(_set_new_daily_budgets(campaign))
                actions.extend(_set_end_date_to_today(campaign))
        except:
            logger.exception('Updating landing mode campaign with id %s not successful', campaign.id)
            continue

        zwei_actions.send(actions)


def get_max_settable_daily_budget(ad_group_source):
    remaining_today, available_tomorrow, max_daily_budget_per_ags = _get_minimum_remaining_budget(
        ad_group_source.ad_group.campaign)

    ags_max_daily_budget = 0
    if ad_group_source.id in max_daily_budget_per_ags:  # ad group was running today
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


def _set_new_daily_budgets(campaign):
    stop_non_spending_actions = _stop_non_spending_sources(campaign)
    per_date_spend, per_source_spend = _get_past_7_days_data(campaign)

    daily_caps = _calculate_daily_caps(campaign, per_date_spend)
    daily_cap_actions = _prepare_active_sources_for_autopilot(campaign, daily_caps, per_source_spend)
    daily_caps = _calculate_daily_caps(campaign, per_date_spend)  # recalculate in case any ad groups were stopped

    autopilot_actions = _run_autopilot(campaign, daily_caps)
    return stop_non_spending_actions + daily_cap_actions + autopilot_actions


def _switch_campaign_to_landing_mode(campaign):
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='Switched to landing mode.'
    )
    new_campaign_settings = campaign.get_current_settings().copy_settings()
    new_campaign_settings.landing_mode = True
    new_campaign_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
    new_campaign_settings.save(None)

    for ad_group in campaign.adgroup_set.all().filter_active():
        new_ad_group_settings = ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.landing_mode = True
        new_ad_group_settings.system_user = dash.constants.SystemUserType.CAMPAIGN_STOP
        new_ad_group_settings.save(None)

        for ad_group_source in ad_group.adgroupsource_set.all().filter_active():
            new_ags_settings = ad_group_source.get_current_settings().copy_settings()
            new_ags_settings.landing_mode = True
            new_ags_settings.save(None)

    actions = _set_end_date_to_today(campaign)
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


def _restore_user_ad_group_settings(ad_group):
    user_end_date = _get_ad_groups_user_end_dates([ad_group])[ad_group.id]
    current_settings = ad_group.get_current_settings()
    if current_settings.state == dash.constants.AdGroupSettingsState.INACTIVE:
        return []

    new_settings = current_settings.copy_settings()
    new_settings.landing_mode = False
    new_settings.end_date = user_end_date
    new_settings.save(None)

    actions = dash.api.order_ad_group_settings_update(
        ad_group,
        current_settings,
        new_settings,
        request=None,
        send=False,
    )

    actions.extend(_restore_user_sources_settings(ad_group))
    return actions


def _restore_user_sources_settings(ad_group):
    actions = []

    ad_group_sources = ad_group.adgroupsource_set.all()
    ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
            landing_mode=False,
        ).group_current_settings()
    }

    for ad_group_source in ad_group.adgroupsource_set.all():
        settings_writer = dash.api.AdGroupSourceSettingsWriter(ad_group_source)
        old_settings = ad_group_sources_settings[ad_group_source.id]
        actions.extend(
            settings_writer.set(
                {
                    'state': old_settings.state,
                    'cpc_cc': old_settings.cpc_cc,
                    'daily_budget_cc': old_settings.daily_budget_cc,
                },
                request=None,
                send_to_zwei=False,
                system_user=dash.constants.SystemUserType.CAMPAIGN_STOP,
                landing_mode=False
            )
        )

    return actions


def _stop_ad_group(ad_group):
    actions = []
    actions.extend(_restore_user_ad_group_settings(ad_group))

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
        actions.extend(_set_ad_group_end_date(ad_group, today))
    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes='End date set to {}'.format(today)
    )
    return actions


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
        yesterday_spends[(row['ad_group'], row['source'])] = row['cost'] + row['data_cost']

    return yesterday_spends


def _get_active_ad_group_sources(ad_groups):
    active_sources = dash.models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups
    ).filter_active()
    active_sources_dict = defaultdict(list)
    for ags in active_sources:
        active_sources_dict[ags.ad_group_id].append(ags)

    return active_sources_dict


def _stop_non_spending_sources(campaign):
    actions = []

    ad_groups = campaign.adgroup_set.all().filter_active()
    yesterday_spends = _get_yesterday_source_spends(ad_groups)

    active_sources_dict = _get_active_ad_group_sources(ad_groups)
    for ad_group in ad_groups:
        ad_group_sources = active_sources_dict[ad_group.id]
        to_stop = set()

        for ags in ad_group_sources:
            if yesterday_spends.get((ad_group.id, ags.source_id), 0) == 0:
                to_stop.add(ags)

        if len(to_stop) == len(ad_group_sources):
            actions.extend(_stop_ad_group(ad_group))
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping non spending ad group {}. Yesterday spend per source was:\n{}'.format(
                    ad_group.id,
                    '\n'.join(['{}: ${}'.format(
                        ags.source.name,
                        yesterday_spends.get(ags.ad_group_id, ags.source_id)
                    ) for ags in ad_group_sources])
                )
            )
            continue

        if to_stop:
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping non spending ad group sources on ad group {}. '
                      'Yesterday spend per source was:\n{}'.format(
                          ad_group.id,
                          '\n'.join(['{}: Yesterday spend was ${}'.format(
                              ags.source.name,
                              yesterday_spends.get(ags.ad_group_id, ags.source_id)
                          ) for ags in to_stop])
                      )
            )
            for ags in to_stop:
                actions.extend(_stop_ad_group_source(ags))

    return actions


def _get_min_autopilot_budget(ad_group_sources):
    min_daily_budgets = []
    for ags in ad_group_sources:
        min_source_budget = autopilot_settings.BUDGET_AP_MIN_SOURCE_BUDGET
        if ags.source.source_type.min_daily_budget:
            min_source_budget = max(min_source_budget, ags.source.source_type.min_daily_budget)
        min_daily_budgets.append(min_source_budget)
    return sum(min_daily_budgets)


def _persist_new_daily_caps_to_log(campaign, daily_caps, ad_groups, remaining_today, per_date_spend):
    notes = 'Calculated ad group daily caps to:\n'
    for ad_group in ad_groups:
        notes += 'Ad group: {}, Daily cap: ${}\n'.format(ad_group.id, daily_caps[ad_group.id])
    notes = 'Remaining budget today: {}\n\n'.format(remaining_today)
    notes += '\nPast spends:\n'
    for ad_group in ad_groups:
        notes += 'Ad group: {}, Per date spends: '.format(ad_group.id)
        notes += ', '.join(['{}: ${}'.format(key[1], per_date_spend[key])
                            for key in sorted(per_date_spend.keys(), key=lambda x: x[1]) if key[0] == ad_group.id])
        notes += '\n'

    models.CampaignStopLog.objects.create(
        campaign=campaign,
        notes=notes
    )


def _calculate_daily_caps(campaign, per_date_spend):
    ad_groups = campaign.adgroup_set.all().filter_active()
    daily_cap_ratios = _get_ad_group_ratios(ad_groups, per_date_spend)
    remaining_today, _, _ = _get_minimum_remaining_budget(campaign)

    daily_caps = {}
    for ad_group in ad_groups:
        daily_caps[ad_group.id] = int(float(remaining_today) * float(daily_cap_ratios.get(ad_group.id, 0)))

    _persist_new_daily_caps_to_log(campaign, daily_caps, ad_groups, remaining_today, per_date_spend)
    return daily_caps


def _prepare_active_sources_for_autopilot(campaign, daily_caps, per_source_spend):
    actions = []

    ad_groups = campaign.adgroup_set.all().filter_active()
    active_sources_dict = _get_active_ad_group_sources(ad_groups)
    for ad_group in ad_groups:
        ag_daily_cap = daily_caps[ad_group.id]
        active_sources = sorted(
            active_sources_dict[ad_group.id],
            key=lambda x: per_source_spend.get((x.ad_group_id, x.source_id), 0),
        )

        to_stop = []
        while len(active_sources) > 0 and ag_daily_cap < _get_min_autopilot_budget(active_sources):
            to_stop.append(active_sources[0])
            active_sources = active_sources[1:]

        if len(active_sources) == 0:
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping ad group {} - lowering minimum autopilot budget not possible.'
                      'Minimum autopilot budget: {}, Daily cap: {}.'.format(
                          ad_group.id,
                          _get_min_autopilot_budget(active_sources + to_stop),
                          ag_daily_cap,
                      )
            )
            actions.extend(_stop_ad_group(ad_group))
            continue

        if to_stop:
            models.CampaignStopLog.objects.create(
                campaign=campaign,
                notes='Stopping sources {} on ad group {} - lowering minimum autopilot budget not possible.'
                      'Minimum autopilot budget: {}, Daily cap: {}.'.format(
                          ', '.join([ags.source.name for ags in to_stop]),
                          ad_group.id,
                          _get_min_autopilot_budget(to_stop),
                          ag_daily_cap,
                      )
            )
            for ags in to_stop:
                actions.extend(_stop_ad_group_source(ags))

    return actions


def _run_autopilot(campaign, daily_caps):
    actions = []

    ad_groups = campaign.adgroup_set.all().filter_active()
    per_ad_group_autopilot_data, campaign_goals = autopilot_plus.prefetch_autopilot_data(ad_groups)
    for ad_group in ad_groups:
        # TODO: set autopilot_daily_budget setting to daily_cap on ad group settings
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
                '\n'.join(['{}: Daily budget ${}, CPC ${}'.format(
                    ags.source.name,
                    budget_changes.get(ags, {}).get('new_budget', -1),
                    cpc_changes.get(ags, {}).get('new_cpc_cc', -1),
                ) for ags in sorted(set(budget_changes.keys() + cpc_changes.keys()))])
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


def _get_ad_group_ratios(ad_groups, per_date_data):
    today = dates_helper.local_today()
    before_7_days = today - datetime.timedelta(days=7)

    spend_per_ad_group = defaultdict(list)
    for date in dates_helper.date_range(before_7_days, today):
        active_ad_groups = _get_ad_groups_running_on_date(date, ad_groups, user_end_dates=True)
        for ad_group in active_ad_groups:
            ad_group_spend = per_date_data.get((ad_group.id, date), 0)
            spend_per_ad_group[ad_group.id].append(ad_group_spend)

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
        spend = item['cost'] + item['data_cost']
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


def _get_ad_groups_latest_end_dates(ad_groups):
    ag_settings = dash.models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups,
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


def _get_ad_groups_running_on_date(date, ad_groups, user_end_dates=False):
    if user_end_dates:
        ad_group_end_dates = _get_ad_groups_user_end_dates(ad_groups)
    else:
        ad_group_end_dates = _get_ad_groups_latest_end_dates(ad_groups)
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

The remaining media budget today is ${remaining_today:.2f}, current media daily cap is ${max_daily_budget:.2f} and yesterday's media spend was ${yesterday_spend:.2f}.

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
        campaign_budgets_url=url_helper.get_full_z1_url('/campaigns/{}/budget-plus'.format(campaign.pk)),
        remaining_today=remaining_today,
        max_daily_budget=max_daily_budget,
        yesterday_spend=yesterday_spend,
    )

    email_helper.send_notification_mail(TEMP_EMAILS, subject, body)
