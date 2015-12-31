import collections
import datetime
import dateutil.parser
import pytz

from decimal import Decimal

from django.conf import settings
from django.db.models import Q, Max

import actionlog.api
import actionlog.constants
import actionlog.models
from dash import models
from dash import constants
from dash import api
from dash import budget
from utils import exc
from utils import statsd_helper
import automation.autopilot

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


def get_by_day(by_day):
    return by_day == 'true'


def get_filtered_sources(user, sources_filter):
    filtered_sources = models.Source.objects.all()
    if not user.has_perm('zemauth.filter_sources') or not sources_filter:
        return filtered_sources

    filtered_ids = []
    for i in sources_filter.split(','):
        try:
            filtered_ids.append(int(i))
        except ValueError:
            pass

    if filtered_ids:
        filtered_sources = filtered_sources.filter(id__in=filtered_ids)

    return filtered_sources


def get_additional_columns(additional_columns):
    if additional_columns:
        return additional_columns.split(',')
    return []


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
            .filter(
                # deprecated sources are not shown in the demo at all
                Q(ad_group__in=real_corresponding_adgroups, source__deprecated=False) |
                Q(ad_group__in=normal_adgroups)
            ).exclude(pk__in=[ags.id for ags in _inactive_ad_group_sources]).\
            select_related('source__source_type').\
            select_related('ad_group')

    return active_ad_group_sources


def join_last_success_with_pixel_sync(user, last_success_actions, last_pixel_sync):
    if not user.has_perm('zemauth.conversion_reports'):
        return last_success_actions

    last_success_actions_joined = {}
    for id_, last_sync_time in last_success_actions.items():
        if last_sync_time is None or last_pixel_sync is None:
            last_success_actions_joined[id_] = None
            continue
        last_success_actions_joined[id_] = min(last_sync_time, last_pixel_sync)
    return last_success_actions_joined


def get_ad_group_sources_last_change_dt(ad_group_sources, ad_group_sources_settings,
                                        ad_group_sources_states, last_change_dt=None):
    def get_last_change(ad_group_source):
        current_settings = _get_ad_group_source_settings_from_filter_qs(ad_group_source, ad_group_sources_settings)
        current_state = _get_ad_group_source_state_from_filter_qs(ad_group_source, ad_group_sources_states)

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


def _get_keys_in_progress(ad_group_source, waiting_delayed_actions):
    keys_in_progress = set()
    for action in waiting_delayed_actions:
        if action.ad_group_source_id != ad_group_source.id:
            continue

        keys = action.payload.get('args', {}).get('conf', {}).keys()

        for key in keys:
            keys_in_progress.add(key)

    return keys_in_progress


def get_ad_group_sources_notifications(ad_group_sources, ad_group_settings,
                                       ad_group_sources_settings, ad_group_sources_states):
    notifications = {}

    waiting_delayed_actions = actionlog.models.ActionLog.objects.filter(
        state__in=(actionlog.constants.ActionState.WAITING, actionlog.constants.ActionState.DELAYED),
        action=actionlog.constants.Action.SET_CAMPAIGN_STATE,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources],
    )

    for ags in ad_group_sources:
        notification = {}

        ad_group_source_settings = _get_ad_group_source_settings_from_filter_qs(ags, ad_group_sources_settings)
        ad_group_source_state = _get_ad_group_source_state_from_filter_qs(ags, ad_group_sources_states)

        messages = []
        in_progress = False
        important = False
        state_message = None

        keys_in_progress = _get_keys_in_progress(ags, waiting_delayed_actions)

        if not models.AdGroup.is_ad_group_active(ad_group_settings):
            if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSettingsState.ACTIVE:
                state_message = 'This media source is enabled but will not run until you enable ad group in Settings tab.'
                messages.append(state_message)

                if len(keys_in_progress):
                    if 'state' in keys_in_progress:
                        messages.append(_get_state_update_notification(ags, ad_group_settings, ad_group_source_state))
                important = True

        if len(keys_in_progress):
            update_messages = []

            if state_message is None and 'state' in keys_in_progress:
                update_messages.append(
                    _get_state_update_notification(
                        ags,
                        ad_group_source_settings,
                        ad_group_source_state
                    )
                )

            if 'cpc_cc' in keys_in_progress:
                update_messages.append(
                    _get_cpc_update_notification(
                        ags,
                        ad_group_source_settings,
                        ad_group_source_state
                    )
                )

            if 'daily_budget_cc' in keys_in_progress:
                update_messages.append(
                    _get_budget_update_notification(
                        ags,
                        ad_group_source_settings,
                        ad_group_source_state
                    )
                )

            in_progress = len(update_messages) > 0

            messages += update_messages

        message = '<br />'.join([t for t in messages if t is not None])

        if not len(message):
            continue

        notification['message'] = message
        notification['in_progress'] = in_progress
        notification['important'] = important

        notifications[ags.source_id] = notification

    return notifications


def get_content_ad_notifications(ad_group):
    actions = actionlog.models.ActionLog.objects.filter(
        state=actionlog.constants.ActionState.WAITING,
        content_ad_source__isnull=False,
        ad_group_source__ad_group=ad_group,
        action=actionlog.constants.Action.UPDATE_CONTENT_AD
    ).select_related('content_ad_source__content_ad')

    content_ads = {}
    for action in actions:
        content_ad_id = action.content_ad_source.content_ad.id

        if content_ad_id not in content_ads:
            content_ads[content_ad_id] = []

        content_ads[content_ad_id].append(action.content_ad_source)

    notifications = {}
    for content_ad_id, content_ad_sources in content_ads.items():
        if any(c.state != c.source_state for c in content_ad_sources):
            state = content_ad_sources[0].state  # take first since all are equal

            if state == constants.ContentAdSourceState.ACTIVE:
                old_state = constants.ContentAdSourceState.INACTIVE
            else:
                old_state = constants.ContentAdSourceState.ACTIVE

            notifications[str(content_ad_id)] = {
                'message': 'Status is being changed from {} to {}'.format(
                    constants.ContentAdSourceState.get_text(old_state),
                    constants.ContentAdSourceState.get_text(state)
                ),
                'in_progress': True
            }

    return notifications


def _get_changed_content_ad_sources(ad_group, sources, last_change_dt):
    content_ad_sources = models.ContentAdSource.objects.filter(
        content_ad__ad_group=ad_group,
        source=sources
    )

    if last_change_dt is not None:
        content_ad_sources = content_ad_sources.filter(modified_dt__gt=last_change_dt)

    return content_ad_sources


def get_changed_content_ads(ad_group, sources, last_change_dt=None):
    content_ad_sources = _get_changed_content_ad_sources(ad_group, sources, last_change_dt).select_related('content_ad')
    return set(s.content_ad for s in content_ad_sources)


def get_content_ad_last_change_dt(ad_group, sources, last_change_dt=None):
    content_ad_sources = _get_changed_content_ad_sources(ad_group, sources, last_change_dt)
    return content_ad_sources.aggregate(Max('modified_dt'))['modified_dt__max']


def get_content_ad_submission_status(user, ad_group_sources_states, content_ad_sources):
    submission_status = []
    for content_ad_source in content_ad_sources:
        cas_source_state = content_ad_source.source_state
        if cas_source_state is None:
            cas_source_state = constants.ContentAdSourceState.INACTIVE

        cas_submission_status = content_ad_source.submission_status
        if cas_submission_status != constants.ContentAdSubmissionStatus.APPROVED and\
           cas_submission_status != constants.ContentAdSubmissionStatus.REJECTED:
            cas_submission_status = constants.ContentAdSubmissionStatus.PENDING

        status = {
            'name': content_ad_source.source.name,
            'status': cas_submission_status,
        }

        cas_source = content_ad_source.source
        cas_ad_group = content_ad_source.content_ad.ad_group

        ad_group_source_state_text = ''
        if user.has_perm('zemauth.can_see_media_source_status_on_submission_popover'):
            cas_ad_group_source_state = None
            for agss in ad_group_sources_states:
                if agss.ad_group_source.ad_group_id == cas_ad_group.id and\
                   agss.ad_group_source.source_id == cas_source.id:
                    cas_ad_group_source_state = agss
                    break

            if cas_ad_group_source_state is not None:
                if cas_ad_group_source_state.state == constants.AdGroupSourceSettingsState.ACTIVE:
                    ad_group_source_state_text = ''
                else:
                    ad_group_source_state_text = '(paused)'

        status['source_state'] = ad_group_source_state_text

        text = constants.ContentAdSubmissionStatus.get_text(cas_submission_status)
        if (cas_submission_status == constants.ContentAdSubmissionStatus.REJECTED and
                content_ad_source.submission_errors is not None):
            text = '{} ({})'.format(text, content_ad_source.submission_errors)
        else:
            text = '{} / {}'.format(
                text,
                constants.ContentAdSourceState.get_text(cas_source_state)
            )

        status['text'] = text
        submission_status.append(status)

    return submission_status


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
    if ags.source.can_update_daily_budget_automatic() and\
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


def get_data_status(objects, last_sync_messages, state_messages=None, last_pixel_sync_message=None):
    data_status = {}
    for obj in objects:
        messages, state_ok = [], True
        if state_messages:
            messages, state_ok = state_messages[obj.id]

        last_sync_message_parts = last_sync_messages[obj.id][0][:]  # create a copy
        last_sync_ok = last_sync_messages[obj.id][1]
        if last_pixel_sync_message is not None:
            pixel_sync_message, pixel_sync_ok = last_pixel_sync_message
            last_sync_ok = last_sync_ok and pixel_sync_ok
            last_sync_message_parts.append(pixel_sync_message)

        if last_sync_ok and state_ok:
            last_sync_message_parts.insert(0, 'All data is OK.')

        if hasattr(obj, 'maintenance') and obj.maintenance and not last_sync_ok:
            last_sync_ok = True
            messages.insert(0, 'This source is in maintenance mode.')

        if hasattr(obj, 'deprecated') and obj.deprecated and not last_sync_ok:
            last_sync_ok = True
            messages.insert(0, 'This source is deprecated.')

        if not last_sync_ok:
            last_sync_message_parts.insert(0, 'Reporting data is stale.')

        messages.append(' '.join(last_sync_message_parts))

        data_status[obj.id] = {
            'message': '<br />'.join(messages),
            'ok': last_sync_ok and state_ok,
        }

    return data_status


def get_content_ad_data_status(ad_group, content_ads):
    ad_group_sources = models.AdGroupSource.objects.filter(ad_group=ad_group)
    ad_group_sources_states = get_ad_group_sources_states(ad_group_sources)
    content_ad_sources = models.ContentAdSource.objects.filter(
        content_ad__in=content_ads
    ).select_related('source')

    data_status = {}
    for content_ad in content_ads:
        out_of_sync = []
        for content_ad_source in content_ad_sources:
            if content_ad_source.content_ad_id != content_ad.id:
                continue

            # we ignore deprecated and in maintenance sources
            if content_ad_source.source.deprecated or content_ad_source.source.maintenance:
                continue

            # we ignore pending content ads
            if content_ad_source.submission_status == constants.ContentAdSubmissionStatus.PENDING:
                continue

            # we ignore rejected content ads
            if content_ad_source.submission_status == constants.ContentAdSubmissionStatus.REJECTED:
                continue

            ad_group_source = None
            for ags in ad_group_sources:
                if content_ad_source.source.id == ags.source_id:
                    ad_group_source = ags
                    break

            if ad_group_source is not None:
                latest_state = _get_ad_group_source_state_from_filter_qs(ad_group_source, ad_group_sources_states)
                if latest_state is not None and latest_state.state == constants.AdGroupSourceSettingsState.INACTIVE:
                    # in case media source is disabled we ignore content ad state
                    # difference
                    continue

            if content_ad_source.state != content_ad_source.source_state:
                out_of_sync.append(content_ad_source.source.name)

        message = ''
        if not out_of_sync:
            message = 'All data is OK.'
        else:
            message = 'The status of this Content Ad differs on these media sources: {}.'.format(", ".join(out_of_sync))

        data_status[str(content_ad.id)] = {
            'message': message,
            'ok': len(out_of_sync) == 0,
        }

    return data_status


def get_last_sync_messages(objects, last_sync_times):
    last_sync_messages = {}
    for obj in objects:
        message_parts, ok = [], True

        last_sync = last_sync_times.get(obj.id)
        if last_sync is not None:
            ok = is_sync_recent([last_sync])

            last_sync = pytz.utc.localize(last_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))
            message_parts.append('Last OK sync was on: <b>{}</b>.'.format(last_sync.strftime('%m/%d/%Y %-I:%M %p')))

        if hasattr(obj, 'is_archived') and obj.is_archived():
            ok = True

        last_sync_messages[obj.id] = message_parts, ok

    return last_sync_messages


def get_last_pixel_sync_message(last_pixel_sync):
    ok = False
    message = 'Last OK conversion pixel sync was on: <b>{}</b>.'
    if last_pixel_sync is not None:
        ok = is_sync_recent([last_pixel_sync])
        last_pixel_sync = pytz.utc.localize(last_pixel_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))
        message = message.format(last_pixel_sync.strftime('%m/%d/%Y %-I:%M %p'))
    else:
        message = message.format('N/A')

    return message, ok


def get_selected_content_ads(
        ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected, include_archived):
    if select_all:
        content_ads = models.ContentAd.objects.filter(
            Q(ad_group__id=ad_group_id) | Q(id__in=content_ad_ids_selected)).exclude(
                id__in=content_ad_ids_not_selected)
    elif select_batch_id is not None:
        content_ads = models.ContentAd.objects.filter(
            Q(batch__id=select_batch_id) | Q(id__in=content_ad_ids_selected)).exclude(
                id__in=content_ad_ids_not_selected)
    else:
        content_ads = models.ContentAd.objects.filter(id__in=content_ad_ids_selected)

    if not include_archived:
        content_ads = content_ads.exclude_archived()

    return content_ads.order_by('created_dt')


def get_ad_group_sources_state_messages(ad_group_sources, ad_group_settings,
                                        ad_group_sources_settings, ad_group_sources_states):
    sources_messages = {}

    waiting_delayed_actionlogs = actionlog.models.ActionLog.objects.filter(
        state__in=(actionlog.constants.ActionState.WAITING, actionlog.constants.ActionState.DELAYED),
        action=actionlog.constants.Action.SET_CAMPAIGN_STATE,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources]
    )

    for ad_group_source in ad_group_sources:
        ags_settings = _get_ad_group_source_settings_from_filter_qs(ad_group_source, ad_group_sources_settings)
        ags_state = _get_ad_group_source_state_from_filter_qs(ad_group_source, ad_group_sources_states)
        sources_messages[ad_group_source.source_id] = _get_state_messages(ad_group_source, ad_group_settings,
                                                                          ags_settings, ags_state,
                                                                          waiting_delayed_actionlogs)

    return sources_messages


def _get_state_messages(ad_group_source, ad_group_settings, ad_group_source_settings,
                        ad_group_source_state, actionlogs):
    message_template = '<b>{name}</b> for this Media Source differs from '\
                       '{name} in the Media Source\'s 3rd party dashboard.'

    for al in actionlogs:
        if al.ad_group_source.id == ad_group_source.id:
            # there are updates in progress
            return [], True

    if ad_group_source_settings is None:
        return [], True

    messages = []
    if ad_group_source.source.can_update_cpc() and ad_group_source_settings.cpc_cc is not None and (
            ad_group_source_state is None or ad_group_source_settings.cpc_cc != ad_group_source_state.cpc_cc):
        messages.append(message_template.format(name='Bid CPC'))

    if (ad_group_source.source.can_update_daily_budget_automatic() or
            ad_group_source.source.can_update_daily_budget_manual()) and\
        ad_group_source_settings.daily_budget_cc is not None and (
            ad_group_source_state is None or ad_group_source_settings.daily_budget_cc != ad_group_source_state.daily_budget_cc):
        messages.append(message_template.format(name='Daily Budget'))

    if ad_group_settings.state == constants.AdGroupSettingsState.INACTIVE:
        expected_state = constants.AdGroupSourceSettingsState.INACTIVE
    else:
        expected_state = ad_group_source_settings.state

    if ad_group_source_settings.state is not None and (
            ad_group_source_state is None or expected_state != ad_group_source_state.state):
        messages.append(message_template.format(name='Status'))

    return messages, len(messages) == 0


def _get_ad_group_source_settings_from_filter_qs(ad_group_source, ad_group_sources_settings):
        for ags_settings in ad_group_sources_settings:
            if ags_settings.ad_group_source_id == ad_group_source.id:
                return ags_settings

        return None


def _get_ad_group_source_state_from_filter_qs(ad_group_source, ad_group_sources_states):
        for ags_state in ad_group_sources_states:
            if ags_state.ad_group_source_id == ad_group_source.id:
                return ags_state

        return None


def get_ad_group_sources_states(ad_group_sources):
    return models.AdGroupSourceState.objects\
                                    .filter(ad_group_source__in=ad_group_sources)\
                                    .group_current_states()\
                                    .select_related('ad_group_source')


def get_ad_group_sources_settings(ad_group_sources):
    return models.AdGroupSourceSettings.objects\
        .filter(ad_group_source__in=ad_group_sources)\
        .group_current_settings()\
        .select_related('ad_group_source')


def get_ad_group_state_by_sources_running_status(ad_groups, ad_groups_settings,
                                                 ad_groups_sources_settings, group_by_key):

    # TODO: temporary disabled for performance observations - should by running status by source settings
    running_status_per_ag = map_per_ad_group_flight_running_status(ad_groups_settings)

    status_dict = collections.defaultdict(lambda: constants.AdGroupSettingsState.INACTIVE)

    for ag in ad_groups.values('id', group_by_key):
        ad_group_id = ag['id']
        key = ag[group_by_key]
        if running_status_per_ag[ad_group_id] == constants.AdGroupRunningStatus.ACTIVE:
            status_dict[key] = constants.AdGroupSettingsState.ACTIVE

    return status_dict


def map_per_ad_group_flight_running_status(ad_groups_settings):
    running_status_dict = collections.defaultdict(lambda: constants.AdGroupRunningStatus.INACTIVE)
    for ags in ad_groups_settings:
        running_status_dict[ags.ad_group_id] = models.AdGroup.get_running_status_by_flight_time(
            ags)

    return running_status_dict


def map_per_ad_group_source_running_status(ad_groups_settings, ad_groups_sources_settings):
    """
    Return a dict with ad group ids as keys and running status of selected ad
    group sources as values.
    """

    sources_settings_dict = collections.defaultdict(list)
    for agss in ad_groups_sources_settings:
        sources_settings_dict[agss.ad_group_source.ad_group_id].append(agss)

    running_status_dict = collections.defaultdict(lambda: constants.AdGroupRunningStatus.INACTIVE)
    for ags in ad_groups_settings:
        running_status_dict[ags.ad_group_id] = models.AdGroup.get_running_status_by_sources_setting(
            ags, sources_settings_dict[ags.ad_group_id])

    return running_status_dict


def parse_get_request_content_ad_ids(request_data, param_name):
    content_ad_ids = request_data.get(param_name)

    if not content_ad_ids:
        return []

    try:
        return map(int, content_ad_ids.split(','))
    except ValueError:
        raise exc.ValidationError()


def parse_post_request_content_ad_ids(request_data, param_name):
    content_ad_ids = request_data.get(param_name, [])

    try:
        return map(int, content_ad_ids)
    except ValueError:
        raise exc.ValidationError()


def get_user_full_name_or_email(user):
    if user is None:
        return '/'

    result = user.get_full_name() or user.email
    return result.encode('utf-8')


def get_target_regions_string(regions):
    if not regions:
        return 'worldwide'

    return ', '.join(constants.AdTargetLocation.get_text(x) for x in regions)


def copy_stats_to_row(stat, row):
    for key in ['impressions', 'clicks', 'cost', 'data_cost', 'cpc', 'ctr',
                'visits', 'click_discrepancy', 'pageviews', 'media_cost',
                'percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos', 
                'e_media_cost', 'e_data_cost', 'total_cost', 'billing_cost',
                'license_fee', ]:
        row[key] = stat.get(key)

    for key in [k for k in stat.keys() if k.startswith('conversion_goal_')]:
        row[key] = stat.get(key)


def _is_end_date_past(ad_group_settings):
    end_utc_datetime = ad_group_settings.get_utc_end_datetime()

    if end_utc_datetime is None:  # user will stop adgroup manually
        return False

    # if end date is in the past then we can't edit cpc and budget
    return end_utc_datetime < datetime.datetime.utcnow()


def get_editable_fields(ad_group_source, ad_group_settings, ad_group_source_settings, user, allowed_sources):
    editable_fields = {}

    if not user.has_perm('zemauth.set_ad_group_source_settings'):
        return editable_fields

    editable_fields['status_setting'] = _get_editable_fields_status_setting(
        ad_group_source,
        ad_group_settings,
        ad_group_source_settings,
        allowed_sources,
    )
    editable_fields['bid_cpc'] = _get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)
    editable_fields['daily_budget'] = _get_editable_fields_daily_budget(ad_group_source, ad_group_settings)

    return editable_fields


def _get_editable_fields_bid_cpc(ad_group_source, ad_group_settings):
    enabled = True
    message = None

    if not ad_group_source.source.can_update_cpc() or\
            _is_end_date_past(ad_group_settings) or\
            automation.autopilot.ad_group_source_is_on_autopilot(ad_group_source):
        enabled = False
        message = _get_bid_cpc_daily_budget_disabled_message(ad_group_source, ad_group_settings)

    return {
        'enabled': enabled,
        'message': message
    }


def _get_editable_fields_daily_budget(ad_group_source, ad_group_settings):
    enabled = True
    message = None

    if not ad_group_source.source.can_update_daily_budget_automatic() and\
       not ad_group_source.source.can_update_daily_budget_manual() or\
       _is_end_date_past(ad_group_settings):
        enabled = False
        message = _get_bid_cpc_daily_budget_disabled_message(ad_group_source, ad_group_settings)

    return {
        'enabled': enabled,
        'message': message
    }


def _get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings, allowed_sources):
    message = None

    if not ad_group_source.source.can_update_state() or (
       ad_group_source.ad_group.content_ads_tab_with_cms and not ad_group_source.can_manage_content_ads):
        message = _get_status_setting_disabled_message(ad_group_source)
    elif ad_group_source_settings is not None and\
            ad_group_source_settings.state == constants.AdGroupSourceSettingsState.INACTIVE:
        message = _get_status_setting_disabled_message_for_target_regions(
            ad_group_source, ad_group_settings, ad_group_source_settings)

    if ad_group_source.source_id not in allowed_sources:
        message = 'Please contact support to enable this source.'

    return {
        'enabled': message is None,
        'message': message
    }


def _get_status_setting_disabled_message(ad_group_source):
    if ad_group_source.source.maintenance:
        return 'This source is currently in maintenance mode.'

    if ad_group_source.ad_group.content_ads_tab_with_cms and not ad_group_source.can_manage_content_ads:
        return 'Please contact support to enable this source.'

    return 'This source must be managed manually.'


def _get_status_setting_disabled_message_for_target_regions(
                 ad_group_source, ad_group_settings, ad_group_source_settings):
    source = ad_group_source.source
    unsupported_targets = []
    manual_targets = []

    for region_type in constants.RegionType.get_all():
        if ad_group_settings.targets_region_type(region_type):
            if not source.source_type.supports_targeting_region_type(region_type):
                unsupported_targets.append(constants.RegionType.get_text(region_type))
            elif not source.source_type.can_modify_targeting_for_region_type_automatically(region_type):
                manual_targets.append(constants.RegionType.get_text(region_type))

    if unsupported_targets:
        return 'This source can not be enabled because it does not support {} targeting.'.format(" and ".join(unsupported_targets))

    activation_settings = models.AdGroupSourceSettings.objects.filter(
        ad_group_source=ad_group_source, state=constants.AdGroupSourceSettingsState.ACTIVE)

    # disable when waiting for manual actions for target_regions after campaign creation
    # message this only when the source is about to be enabled for the first time
    if manual_targets and\
       actionlog.api.is_waiting_for_manual_set_target_regions_action(ad_group_source) and\
       not activation_settings.exists():
        return 'This source needs to set {} targeting manually, please contact support to enable this source.'.format(" and ".join(manual_targets))

    return None


def _get_bid_cpc_daily_budget_disabled_message(ad_group_source, ad_group_settings):
    if ad_group_source.source.maintenance:
        return 'This value cannot be edited because the media source is currently in maintenance.'

    if _is_end_date_past(ad_group_settings):
        return 'The ad group has end date set in the past. No modifications to media source parameters are possible.'

    if automation.autopilot.ad_group_source_is_on_autopilot(ad_group_source):
        return 'This value cannot be edited because the media source is on Auto-Pilot'

    return 'This media source doesn\'t support setting this value through the dashboard.'


def add_source_to_ad_group(default_source_settings, ad_group):
    ad_group_source = models.AdGroupSource(
        source=default_source_settings.source,
        ad_group=ad_group,
        source_credentials=default_source_settings.credentials,
        can_manage_content_ads=default_source_settings.source.can_manage_content_ads(),
    )

    if default_source_settings.source.source_type.type == constants.SourceType.GRAVITY:
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

    return ad_group_source


def set_ad_group_source_defaults(default_source_settings, ad_group_settings, ad_group_source,
                                 request, send_action=False):

    # set defaults if available
    cpc_cc = default_source_settings.mobile_cpc_cc if ad_group_settings.is_mobile_only() else\
        default_source_settings.default_cpc_cc

    daily_budget_cc = default_source_settings.daily_budget_cc

    resource = {}
    if daily_budget_cc is not None:
        resource['daily_budget_cc'] = daily_budget_cc
    if cpc_cc is not None:
        resource['cpc_cc'] = cpc_cc

    if resource:
        settings_writer = api.AdGroupSourceSettingsWriter(ad_group_source)
        settings_writer.set(resource, request, send_action=send_action)


def format_decimal_to_percent(num):
    return '{:.2f}'.format(num * 100).rstrip('0').rstrip('.')


def format_percent_to_decimal(num):
    return Decimal(str(num).replace(',', '').strip('%')) / 100


def log_useraction_if_necessary(request, user_action_type, account=None, campaign=None, ad_group=None):
    if request.user.is_self_managed():

        user_action_log = models.UserActionLog(
            action_type=user_action_type,
            created_by=request.user,
            account=account,
            campaign=campaign,
            ad_group=ad_group,
            account_settings_id=account.get_current_settings().id if account else None,
            campaign_settings_id=campaign.get_current_settings().id if campaign else None,
            ad_group_settings_id=ad_group.get_current_settings().id if ad_group else None
        )
        user_action_log.save()


def adgroup_has_available_budget(adgroup):
    campaign_budget = budget.CampaignBudget(adgroup.campaign)

    total = campaign_budget.get_total()
    spend = campaign_budget.get_spend()

    available = total - spend

    return bool(available)
