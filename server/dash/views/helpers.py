import datetime
import dateutil.parser
import pytz
from urlparse import urlparse

from django.conf import settings
from django.core.urlresolvers import resolve

import actionlog.api
import actionlog.constants
from dash import models
from dash import constants
from utils import exc
from utils import statsd_helper

STATS_START_DELTA = 30
STATS_END_DELTA = 1


def parse_datetime(dt_string):
    if dt_string is None or not len(dt_string):
        return

    dt = dateutil.parser.parse(dt_string, ignoretz=True)

    # since this is a client datetime where times are in EST,
    # convert it to UTC
    dt = pytz.timezone(settings.DEFAULT_TIME_ZONE).localize(dt)
    dt = dt.astimezone(pytz.utc)

    return dt.replace(tzinfo=None)


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


def get_last_sync(sync_times):
    if not len(sync_times) or None in sync_times:
        return None

    return min(sync_times)


def is_sync_recent(sync_times):
    if not len(sync_times):
        return True  # Sync is recent if there is no children

    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS
    )

    last_sync = get_last_sync(sync_times)

    if last_sync is None:
        return False

    return last_sync >= min_sync_date


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


def get_ad_group_sources_last_change_dt(ad_group_sources, last_change_dt=None):
    def get_last_change(ad_group_source):
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

    changed_ad_group_sources = []
    last_change_dts = []

    for ad_group_source in ad_group_sources:
        source_last_change = get_last_change(ad_group_source)

        if source_last_change is None:
            continue

        if last_change_dt is not None and source_last_change <= last_change_dt:
            continue

        changed_ad_group_sources.append(ad_group_source)
        last_change_dts.append(source_last_change)

    if len(last_change_dts) == 0:
        return None, []

    return max(last_change_dts), changed_ad_group_sources


def get_ad_group_sources_notifications(ad_group_sources):
    notifications = {}

    for ags in ad_group_sources:
        notification = {}

        latest_settings = _get_latest_settings(ags)
        latest_state = _get_latest_state(ags)

        if ags.ad_group.get_current_settings().state == constants.AdGroupSettingsState.INACTIVE:
            if latest_settings and latest_settings.state == constants.AdGroupSettingsState.ACTIVE:
                notification['message'] = 'This media source is enabled but will not run until you enable ad group in Settings tab. Other media source settings will be synced at the same time.'
                notification['important'] = True

            elif (_get_state_update_notification(ags, latest_settings, latest_state) or
                    _get_cpc_update_notification(ags, latest_settings, latest_state) or
                    _get_budget_update_notification(ags, latest_settings, latest_state)):
                notification['message'] = 'Media source settings will be synced once the ad group is enabled in Settings tab.'
                notification['important'] = False

            if not len(notification):
                continue

            notification['in_progress'] = False
            notifications[ags.source_id] = notification

        elif ags.actionlog_set.filter(
                state=actionlog.constants.ActionState.WAITING,
                action=actionlog.constants.Action.SET_CAMPAIGN_STATE
        ).exists():
            messages = []
            messages.append(_get_state_update_notification(ags, latest_settings, latest_state))
            messages.append(_get_cpc_update_notification(ags, latest_settings, latest_state))
            messages.append(_get_budget_update_notification(ags, latest_settings, latest_state))

            message = '<br />'.join([t for t in messages if t is not None])

            if not len(message):
                continue

            notification['message'] = message
            notification['in_progress'] = True
            notification['important'] = False

            notifications[ags.source_id] = notification

    return notifications


def _get_state_update_notification(ags, settings, state):
    if ags.source.can_update_state() and\
       settings is not None and settings.state is not None and\
       (state is None or state.state != settings.state):
        msg = 'Status is being changed from <strong>{old_state}</strong> ' +\
              'to <strong>{new_state}</strong>.'

        return msg.format(
            new_state=constants.AdGroupSettingsState.get_text(settings.state),
            old_state=constants.AdGroupSettingsState.get_text(
                (state and state.state) or 'N/A'
            )
        )

    return None


def _get_cpc_update_notification(ags, settings, state):
    if ags.source.can_update_cpc() and\
       settings is not None and settings.cpc_cc is not None and\
       (state is None or state.cpc_cc != settings.cpc_cc):
        msg = 'Bid CPC is being changed from <strong>{old_cpc}</strong> ' +\
              'to <strong>{new_cpc}</strong>.'

        if state and state.cpc_cc:
            old_cpc = '{:.3f}'.format(state.cpc_cc)
        else:
            old_cpc = 'N/A'

        return msg.format(
            old_cpc=old_cpc,
            new_cpc='{:.3f}'.format(settings.cpc_cc),
        )

    return None


def _get_budget_update_notification(ags, settings, state):
    if ags.source.can_update_daily_budget() and\
       settings is not None and settings.daily_budget_cc is not None and\
       (state is None or state.daily_budget_cc != settings.daily_budget_cc):
        msg = 'Daily budget is being changed from <strong>{old_daily_budget}</strong> ' +\
              'to <strong>{new_daily_budget}</strong>.'

        if state and state.daily_budget_cc is not None:
            old_daily_budget = '{:.2f}'.format(state.daily_budget_cc)
        else:
            old_daily_budget = 'N/A'

        return msg.format(
            old_daily_budget=old_daily_budget,
            new_daily_budget='{:.2f}'.format(settings.daily_budget_cc),
        )

    return None


def get_ad_group_sources_data_status_messages(ad_group_sources):
    messages_dict = {}

    for ags in ad_group_sources:
        messages = []

        latest_settings = _get_latest_non_waiting_settings(ags)
        latest_state = _get_latest_state(ags)

        message_template = '<b>{name}</b> for this Media Source differs from {name} in the Media Source\'s 3rd party dashboard.'

        if latest_settings is not None:
            if latest_state is None or latest_settings.cpc_cc != latest_state.cpc_cc:
                messages.append(message_template.format(name='Bid CPC'))
            if latest_state is None or latest_settings.daily_budget_cc != latest_state.daily_budget_cc:
                messages.append(message_template.format(name='Daily Budget'))
            if latest_state is None or latest_settings.state != latest_state.state:
                messages.append(message_template.format(name='Status'))

        if len(messages):
            messages_dict[ags.source_id] = '<br/>'.join(messages)
        else:
            ok_message = 'Everything is OK.'

            last_sync = actionlog.sync.AdGroupSourceSync(ags).get_latest_source_success(
                recompute=False)[ags.source_id]

            if last_sync is not None:
                last_sync = pytz.utc.localize(last_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))

                ok_message += ' Last OK sync was on: <b>{}</b>'.format(
                    last_sync.strftime('%m/%d/%Y %-I:%M %p'))

            messages_dict[ags.source_id] = ok_message

    return messages_dict


def get_ad_group_source_data_status(ad_group_source):
    settings = _get_latest_non_waiting_settings(ad_group_source)
    state = _get_latest_state(ad_group_source)

    if settings is None:
        return True
    elif state is None:
        return False

    return (
        settings.state == state.state
        and settings.cpc_cc == state.cpc_cc
        and settings.daily_budget_cc == state.daily_budget_cc
    )


def _get_latest_non_waiting_settings(ad_group_source):
    latest_settings_qs = models.AdGroupSourceSettings.objects.\
        filter(ad_group_source=ad_group_source).\
        exclude(pk__in=_get_waiting_actions_settings_ids(ad_group_source)).\
        order_by('ad_group_source_id', '-created_dt')
    return latest_settings_qs[0] if latest_settings_qs.exists() else None


def _get_waiting_actions_settings_ids(ad_group_source):
    waiting_actions = ad_group_source.actionlog_set.filter(
        state=actionlog.constants.ActionState.WAITING,
        action=actionlog.constants.Action.SET_CAMPAIGN_STATE)

    for action in waiting_actions:
        url_path = urlparse(action.payload['callback_url']).path
        yield int(resolve(url_path).kwargs['settings_id'])


def _get_latest_settings(ad_group_source):
    latest_settings_qs = models.AdGroupSourceSettings.objects.\
        filter(ad_group_source=ad_group_source).\
        order_by('ad_group_source_id', '-created_dt')
    return latest_settings_qs[0] if latest_settings_qs.exists() else None


def _get_latest_state(ad_group_source):
    latest_state_qs = models.AdGroupSourceState.objects.\
        filter(ad_group_source=ad_group_source).\
        order_by('ad_group_source_id', '-created_dt')
    return latest_state_qs[0] if latest_state_qs.exists() else None
