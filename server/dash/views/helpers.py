import datetime
import dateutil.parser
import pytz
import newrelic.agent

from django.conf import settings
from django.db.models import Q

import actionlog.api
import actionlog.constants
import actionlog.models
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
            ).exclude(pk__in=[ags.id for ags in _inactive_ad_group_sources])

    return active_ad_group_sources


@newrelic.agent.function_trace()
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


def _get_keys_in_progress(ad_group_source):
    actions = ad_group_source.actionlog_set.filter(
        state__in=(actionlog.constants.ActionState.WAITING, actionlog.constants.ActionState.DELAYED),
        action=actionlog.constants.Action.SET_CAMPAIGN_STATE
    )

    keys_in_progress = set()
    for action in actions:
        keys = action.payload.get('args', {}).get('conf', {}).keys()

        for key in keys:
            keys_in_progress.add(key)

    return keys_in_progress


@newrelic.agent.function_trace()
def get_ad_group_sources_notifications(ad_group_sources):
    notifications = {}

    for ags in ad_group_sources:
        notification = {}

        latest_settings = _get_latest_settings(ags)
        latest_state = _get_latest_state(ags)

        messages = []
        in_progress = False
        important = False
        state_message = None

        keys_in_progress = _get_keys_in_progress(ags)

        ad_group_settings = ags.ad_group.get_current_settings()
        if ad_group_settings.state == constants.AdGroupSettingsState.INACTIVE:
            if latest_settings and latest_settings.state == constants.AdGroupSettingsState.ACTIVE:
                state_message = 'This media source is enabled but will not run until you enable ad group in Settings tab.'
                messages.append(state_message)

                if len(keys_in_progress):
                    if 'state' in keys_in_progress:
                        messages.append(_get_state_update_notification(ags, ad_group_settings, latest_state))
                important = True

        if len(keys_in_progress):
            update_messages = []

            if state_message is None and 'state' in keys_in_progress:
                update_messages.append(_get_state_update_notification(ags, latest_settings, latest_state))

            if 'cpc_cc' in keys_in_progress:
                update_messages.append(_get_cpc_update_notification(ags, latest_settings, latest_state))

            if 'daily_budget_cc' in keys_in_progress:
                update_messages.append(_get_budget_update_notification(ags, latest_settings, latest_state))

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


def get_content_ad_last_change_dt(ad_group, sources, last_change_dt=None):
    content_ad_sources = models.ContentAdSource.objects.filter(
        content_ad__ad_group=ad_group,
        source=sources
    ).select_related('content_ad')

    if last_change_dt is not None:
        content_ad_sources = content_ad_sources.filter(modified_dt__gt=last_change_dt)

    changed_content_ads = set(s.content_ad for s in content_ad_sources)

    last_change_dt = None
    if len(content_ad_sources):
        last_change_dt = max([s.modified_dt for s in content_ad_sources])

    return last_change_dt, changed_content_ads


def get_content_ad_submission_status(user, content_ad_sources):
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
            adgs = models.AdGroupSource.objects.filter(ad_group=cas_ad_group, source=cas_source)
            if len(adgs) > 0:
                cas_ad_group_source_state = _get_latest_state(adgs[0])
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


@newrelic.agent.function_trace()
def get_data_status(objects, last_sync_messages, state_messages=None):
    data_status = {}
    for obj in objects:
        messages, state_ok = [], True
        if state_messages:
            messages, state_ok = state_messages[obj.id]

        last_sync_message_parts, last_sync_ok = last_sync_messages[obj.id]
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


def get_content_ad_data_status(content_ads):
    data_status = {}
    for content_ad in content_ads:
        in_sync = True
        for ad_group_source in content_ad.sources.all():
            content_ad_source = models.ContentAdSource.objects.filter(
                content_ad=content_ad,
                source=ad_group_source
            ).first()

            if content_ad_source is not None and\
                content_ad_source.state != content_ad_source.source_state:
                in_sync = False
                break

        message = ''
        if in_sync:
            message = 'All data is OK.'
        else:
            message = 'The status of this Content Ad differs from the one in the 3rd party dashboard.'

        data_status[str(content_ad.id)] = {
            'message': message,
            'ok': in_sync,
        }

    return data_status


@newrelic.agent.function_trace()
def get_last_sync_messages(objects, last_sync_times):
    last_sync_messages = {}
    for obj in objects:
        message_parts, ok = [], True

        last_sync = last_sync_times.get(obj.id)
        if last_sync is not None:
            ok = is_sync_recent([last_sync])

            last_sync = pytz.utc.localize(last_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))
            message_parts.append('Last OK sync was on: <b>{}</b>'.format(last_sync.strftime('%m/%d/%Y %-I:%M %p')))

        if hasattr(obj, 'is_archived') and obj.is_archived():
            ok = True

        last_sync_messages[obj.id] = message_parts, ok

    return last_sync_messages


@newrelic.agent.function_trace()
def get_ad_group_sources_state_messages(ad_group_sources):
    sources_messages = {}

    for ad_group_source in ad_group_sources:
        sources_messages[ad_group_source.source_id] = _get_state_messages(ad_group_source)

    return sources_messages


def get_selected_content_ads(
        ad_group_id, select_all, select_batch_id, content_ad_ids_selected, content_ad_ids_not_selected):
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

    return content_ads.order_by('created_dt')


def _get_state_messages(ad_group_source):
    message_template = '<b>{name}</b> for this Media Source differs from '\
                       '{name} in the Media Source\'s 3rd party dashboard.'

    if ad_group_source.actionlog_set.filter(
        state=actionlog.constants.ActionState.WAITING,
        action=actionlog.constants.Action.SET_CAMPAIGN_STATE
    ).exists():
        # there are updates in progress
        return [], True

    latest_settings = _get_latest_settings(ad_group_source)
    latest_state = _get_latest_state(ad_group_source)

    if latest_settings is None:
        return [], True

    messages = []
    if ad_group_source.source.can_update_cpc() and latest_settings.cpc_cc is not None and (
            latest_state is None or latest_settings.cpc_cc != latest_state.cpc_cc):
        messages.append(message_template.format(name='Bid CPC'))

    if (ad_group_source.source.can_update_daily_budget_automatic() or
            ad_group_source.source.can_update_daily_budget_manual()) and\
        latest_settings.daily_budget_cc is not None and (
            latest_state is None or latest_settings.daily_budget_cc != latest_state.daily_budget_cc):
        messages.append(message_template.format(name='Daily Budget'))

    if ad_group_source.ad_group.get_current_settings().state == constants.AdGroupSettingsState.INACTIVE:
        expected_state = constants.AdGroupSourceSettingsState.INACTIVE
    else:
        expected_state = latest_settings.state

    if latest_settings.state is not None and (
            latest_state is None or expected_state != latest_state.state):
        messages.append(message_template.format(name='Status'))

    return messages, len(messages) == 0


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
