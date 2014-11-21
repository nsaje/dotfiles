import datetime
import dateutil.parser

from django.conf import settings

import actionlog.api
from dash import models
from dash import constants
from utils import exc
from utils import statsd_helper

STATS_START_DELTA = 30
STATS_END_DELTA = 1


def get_stats_start_date(start_date):
    if start_date:
        date = dateutil.parser.parse(start_date)
    else:
        date = datetime.datetime.utcnow() - datetime.timedelta(days=STATS_START_DELTA)

    return date.date()


def get_stats_end_date(end_time):
    if end_time:
        date = dateutil.parser.parse(end_time)
    else:
        date = datetime.datetime.utcnow() - datetime.timedelta(days=STATS_END_DELTA)

    return date.date()


def get_account(user, account_id, select_related=False):
    try:
        account = models.Account.objects.all().filter_by_user(user)
        if select_related:
            account = account.select_related('campaign_set')

        return account.filter(id=int(account_id)).get()
    except models.Account.DoesNotExist:
        raise exc.MissingDataError('Account does not exist')


def get_ad_group(user, ad_group_id, select_related=False):
    try:
        ad_group = models.AdGroup.objects.all().filter_by_user(user).\
            filter(id=int(ad_group_id))

        if select_related:
            ad_group = ad_group.select_related('campaign__account')

        return ad_group.get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Ad Group does not exist')


def get_campaign(user, campaign_id):
    try:
        return models.Campaign.objects.all().filter_by_user(user).\
            filter(id=int(campaign_id)).get()
    except models.Campaign.DoesNotExist:
        raise exc.MissingDataError('Campaign does not exist')


def is_sync_recent(last_sync_datetime):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS
    )

    if not last_sync_datetime:
        return None

    result = last_sync_datetime >= min_sync_date

    return result


def _get_adgroups_for(modelcls, modelobjects):
    if modelcls is models.Account:
        return models.AdGroup.objects.filter(campaign__account__in=modelobjects)
    if modelcls is models.Campaign:
        return models.AdGroup.objects.filter(campaign__in=modelobjects)
    assert modelcls is models.AdGroup
    return modelobjects


def get_active_ad_group_sources(modelcls, modelobjects):
    all_demo_qs = modelcls.demo_objects.all()
    demo_objects = filter(lambda x: x in all_demo_qs, modelobjects)
    normal_objects = filter(lambda x: x not in all_demo_qs, modelobjects)

    timer_name = 'get_active_ad_group_sources'
    if len(demo_objects) > 0:
        timer_name += '_demo'

    with statsd_helper.statsd_block_timer('dash.views.table', timer_name):
        demo_adgroups = _get_adgroups_for(modelcls, demo_objects)
        real_corresponding_adgroups = [x.real_ad_group
                                       for x in models.DemoAdGroupRealAdGroup.objects
                                       .filter(demo_ad_group__in=demo_adgroups)]
        normal_adgroups = _get_adgroups_for(modelcls, normal_objects)
        adgroups = list(real_corresponding_adgroups) + list(normal_adgroups)

        _inactive_ad_group_sources = actionlog.api.get_ad_group_sources_waiting(
            ad_group=adgroups
        )

        active_ad_group_sources = models.AdGroupSource.objects \
            .filter(ad_group__in=adgroups) \
            .exclude(pk__in=[ags.id for ags in _inactive_ad_group_sources])

    return active_ad_group_sources


def get_ad_group_sources_last_change_dt(ad_group_sources):
    def last_change(ad_group_source):
        current_state = None
        if ad_group_source.states.exists():
            current_state = ad_group_source.states.latest('created_dt')

        current_settings = None
        if ad_group_source.settings.exists():
            current_settings = ad_group_source.settings.latest('created_dt')

        if current_state is None and current_settings is None:
            return None

        if current_state and current_settings is None:
            return current_state.created_dt

        if current_settings and current_state is None:
            return current_settings.created_dt

        return max(
            current_state.created_dt,
            current_settings.created_dt
        )

    return max([last_change(ad_group_source) for ad_group_source in ad_group_sources])


def get_ad_group_sources_notifications(ad_group_sources):
    notifications = {}

    for ags in ad_group_sources:
        notification = ''

        latest_settings_qs = models.AdGroupSourceSettings.objects.\
            filter(ad_group_source=ags).\
            order_by('ad_group_source_id', '-created_dt')
        latest_settings = latest_settings_qs[0] if latest_settings_qs.exists() else None

        latest_state_qs = models.AdGroupSourceState.objects.\
            filter(ad_group_source=ags).\
            order_by('ad_group_source_id', '-created_dt')
        latest_state = latest_state_qs[0] if latest_state_qs.exists() else None

        if ags.ad_group.get_current_settings().state == constants.AdGroupSettingsState.INACTIVE and\
           latest_settings and latest_settings.state == constants.AdGroupSettingsState.ACTIVE:
            notification += 'This media source is enabled but will not run ' +\
                            'until you enable the ad group in the Settings.'

        if ags.ad_group.get_current_settings().state != constants.AdGroupSettingsState.INACTIVE and\
           ags.source.source_type.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_STATE).exists() and\
           latest_settings is not None and latest_settings.state is not None and\
           (latest_state is None or latest_settings.state != latest_state.state):
            if notification:
                notification += '<br />'

            if latest_state and latest_settings.created_dt > latest_state.created_dt:
                msg = 'Status is being changed from <strong>{state_state}</strong> ' +\
                      'to <strong>{settings_state}</strong>.'
            else:
                msg = 'The actual status on media source is <strong>{state_state}</strong> ' +\
                      'instead of <strong>{settings_state}</strong>.'

            notification += msg.format(
                settings_state=constants.AdGroupSettingsState.get_text(latest_settings.state),
                state_state=constants.AdGroupSettingsState.get_text(
                    (latest_state and latest_state.state) or 'N/A'
                )
            )

        if ags.source.source_type.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_CPC).exists() and\
           latest_settings is not None and latest_settings.cpc_cc is not None and\
           (latest_state is None or latest_settings.cpc_cc != latest_state.cpc_cc):
            if notification:
                notification += '<br />'

            if latest_state and latest_settings.created_dt > latest_state.created_dt:
                msg = 'Bid CPC is being changed from <strong>{state_cpc}</strong> ' +\
                      'to <strong>{settings_cpc}</strong>.'
            else:
                msg = 'The actual CPC on media source is <strong>{state_cpc}</strong> ' +\
                      'instead of <strong>{settings_cpc}</strong>.'

            notification += msg.format(
                settings_cpc='{:.3f}'.format(latest_settings.cpc_cc) if latest_settings.cpc_cc else 'N/A',
                state_cpc='{:.3f}'.format(latest_state.cpc_cc) if latest_state else 'N/A'
            )

        if ags.source.source_type.available_actions.filter(action=constants.SourceAction.CAN_UPDATE_DAILY_BUDGET).exists() and\
           latest_settings is not None and latest_settings.daily_budget_cc is not None and\
           (latest_state is None or latest_settings.daily_budget_cc != latest_state.daily_budget_cc):
            if notification:
                notification += '<br />'

            if latest_state and latest_settings.created_dt > latest_state.created_dt:
                msg = 'Daily budget is being changed from <strong>{state_daily_budget}</strong> ' +\
                      'to <strong>{settings_daily_budget}</strong>.'
            else:
                msg = 'The actual daily budget on media source is <strong>{state_daily_budget}</strong> ' +\
                      'instead of <strong>{settings_daily_budget}</strong>.'

            notification += msg.format(
                settings_daily_budget='{:.2f}'.format(latest_settings.daily_budget_cc) if latest_settings.daily_budget_cc else 'N/A',
                state_daily_budget='{:.2f}'.format(latest_state.daily_budget_cc) if latest_state else 'N/A'
            )

        notifications[ags.source_id] = notification

    return notifications
