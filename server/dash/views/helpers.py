import collections
import datetime
import dateutil.parser
import pytz
import logging
import json

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Max

import automation

from dash import models
from dash import constants
from dash import api

from dash.dashapi import data_helper

from utils import exc
from utils import email_helper
from utils import k1_helper
from utils import columns
from utils import redirector_helper

import zemauth.models

STATS_START_DELTA = 30
STATS_END_DELTA = 1

SPECIAL_COLUMNS = ['performance', 'styles']

logger = logging.getLogger(__name__)


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


class ViewFilter(object):
    '''Convenience class for extracting filters from requests'''

    def __init__(self, request=None, user=None, data=None):
        self.filtered_sources = None
        self.filtered_agencies = None
        self.filtered_account_types = None

        # table breakdowns specific code
        if data:
            self._init_breakdowns(user, data)
        else:
            self._init_old(request)

    def _init_old(self, request):
        if not request:
            return

        if request.method == 'GET':
            data = request.GET
            filtered_sources = data.get('filtered_sources')
            filtered_agencies = data.getlist('filtered_agencies')
            filtered_account_types = data.get('filtered_account_types')
        elif request.method == 'PUT':
            data = json.loads(request.body)
            filtered_sources = data.get('filtered_sources')
            filtered_agencies_raw = data.get('filtered_agencies')
            filtered_agencies = filtered_agencies_raw.split(',') if\
                filtered_agencies_raw else None
            filtered_account_types_raw = data.get('filtered_account_types')
            filtered_account_types = filtered_account_types_raw.split(',') if\
                filtered_account_types_raw else None

        if request.user is not None:
            self.filtered_sources = get_filtered_sources(request.user, filtered_sources)
        self.filtered_agencies = get_filtered_agencies(filtered_agencies)
        self.filtered_account_types = get_filtered_account_types(filtered_account_types)

    def _init_breakdowns(self, user, data):
        self.filtered_sources = None
        if user is not None:
            self.filtered_sources = data.get('filtered_sources')
        self.filtered_agencies = data.get('filtered_agencies')
        self.filtered_account_types = data.get('filtered_account_types')


def get_filtered_sources(user, sources_filter):
    filtered_sources = models.Source.objects.all()
    if not sources_filter:
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


def get_filtered_agencies(agency_filter):
    filtered_agencies = None
    if not agency_filter:
        return filtered_agencies

    filtered_ids = map(int, agency_filter)
    if filtered_ids:
        filtered_agencies = models.Agency.objects.all().filter(
            id__in=filtered_ids
        )
    return filtered_agencies


def get_filtered_account_types(account_type_filter):
    filtered_account_types = None
    if not account_type_filter:
        return filtered_account_types

    filtered_account_types = constants.AccountType.get_all()
    filtered_ids = map(int, account_type_filter)
    return list(set(filtered_account_types) & set(filtered_ids))


def get_additional_columns(additional_columns):
    if additional_columns:
        return additional_columns.split(',')
    return []


def get_account(user, account_id, sources=None):
    try:
        account = models.Account.objects.all().filter_by_user(user)

        if sources:
            account = account.filter_by_sources(sources)

        return account.filter(id=int(account_id)).get()
    except models.Account.DoesNotExist:
        raise exc.MissingDataError('Account does not exist')


def get_ad_group(user, ad_group_id, select_related=False, sources=None):
    try:
        ad_group = models.AdGroup.objects.all().filter_by_user(user).\
            filter(id=int(ad_group_id))

        if sources:
            ad_group = ad_group.filter_by_sources(sources)

        if select_related:
            ad_group = ad_group.select_related('campaign__account')

        return ad_group.get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Ad Group does not exist')


def get_content_ad(user, content_ad_id, select_related=False):
    try:
        content_ad = models.ContentAd.objects.all().filter_by_user(user). \
            filter(id=int(content_ad_id))

        if select_related:
            content_ad = content_ad.select_related('ad_group')

        return content_ad.get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Content Ad does not exist')


def get_campaign(user, campaign_id, sources=None):
    try:
        campaign = models.Campaign.objects.all()\
                                          .filter_by_user(user)\
                                          .filter(id=int(campaign_id))
        if sources:
            campaign = campaign.filter_by_sources(sources)

        return campaign.get()
    except models.Campaign.DoesNotExist:
        raise exc.MissingDataError('Campaign does not exist')


def get_user_agency(user):
    try:
        return user.agency_set.get()
    except models.Agency.DoesNotExist:
        pass
    return None


def is_agency_manager(user, account):
    if account.agency is None:
        return False

    return get_user_agency(user) == account.agency


def _get_adgroups_for(modelcls, modelobjects):
    if modelcls is models.Account:
        return models.AdGroup.objects.filter(campaign__account__in=modelobjects)
    if modelcls is models.Campaign:
        return models.AdGroup.objects.filter(campaign__in=modelobjects)
    assert modelcls is models.AdGroup
    return modelobjects


def get_active_ad_group_sources(modelcls, modelobjects):
    adgroups = _get_adgroups_for(modelcls, modelobjects)

    adgroup_settings = models.AdGroupSettings.objects.\
        filter(ad_group__in=adgroups).\
        group_current_settings()
    archived_adgroup_ids = [setting.ad_group_id for setting in adgroup_settings if setting.archived]

    active_ad_group_sources = models.AdGroupSource.objects \
        .filter(ad_group__in=adgroups).\
        exclude(ad_group__in=archived_adgroup_ids).\
        select_related('source__source_type').\
        select_related('ad_group')

    return active_ad_group_sources


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


def get_ad_group_sources_notifications(ad_group_sources, ad_group_settings,
                                       ad_group_sources_settings, ad_group_sources_states):
    notifications = {}

    for ags in ad_group_sources:
        notification = {}

        ad_group_source_settings = _get_ad_group_source_settings_from_filter_qs(ags, ad_group_sources_settings)

        messages = []
        important = False
        state_message = None

        if not models.AdGroup.is_ad_group_active(ad_group_settings):
            if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSettingsState.ACTIVE:
                state_message = ('This media source is enabled but will not run until'
                                 ' you enable ad group in Ad groups tab on Campaign level.')
                messages.append(state_message)

                important = True

        message = '<br />'.join([t for t in messages if t is not None])

        if not len(message):
            continue

        notification['message'] = message
        notification['in_progress'] = False
        notification['important'] = important

        notifications[ags.source_id] = notification

    return notifications


def _get_changed_content_ad_sources(ad_group, sources, last_change_dt):
    content_ad_sources = models.ContentAdSource.objects.filter(
        content_ad__ad_group=ad_group,
        source__in=sources
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
        cas_submission_status = content_ad_source.get_submission_status()

        status = {
            'name': content_ad_source.source.name,
            'status': cas_submission_status,
        }

        cas_source = content_ad_source.source

        ad_group_source_state_text = ''
        if user.has_perm('zemauth.can_see_media_source_status_on_submission_popover'):
            cas_ad_group_source_state = ad_group_sources_states.get(cas_source.id)

            if cas_ad_group_source_state is not None:
                if cas_ad_group_source_state != constants.AdGroupSourceSettingsState.ACTIVE:
                    ad_group_source_state_text = '(paused)'

        status['source_state'] = ad_group_source_state_text

        text = constants.ContentAdSubmissionStatus.get_text(cas_submission_status)
        if (cas_submission_status == constants.ContentAdSubmissionStatus.REJECTED and
                content_ad_source.submission_errors is not None):
            text = '{} ({})'.format(text, content_ad_source.submission_errors)

        status['text'] = text
        submission_status.append(status)

    return submission_status


def get_data_status(objects):
    data_status = {}
    for obj in objects:
        messages = []

        if hasattr(obj, 'maintenance') and obj.maintenance:
            messages.insert(0, 'This source is in maintenance mode.')

        if hasattr(obj, 'deprecated') and obj.deprecated:
            messages.insert(0, 'This source is deprecated.')

        data_status[obj.id] = {
            'message': '<br />'.join(messages),
            'ok': True,
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
            message = 'The status of this Content Ad differs on these media sources: {}.'.format(
                ", ".join(sorted(out_of_sync)))

        data_status[str(content_ad.id)] = {
            'message': message,
            'ok': len(out_of_sync) == 0,
        }

    return data_status


def get_selected_entities(objects, select_all, selected_ids, not_selected_ids, include_archived, select_batch_id=None, **constraints):
    if select_all:
        if constraints:
            entities = objects.filter(Q(**constraints) | Q(id__in=selected_ids)).exclude(id__in=not_selected_ids)
        else:
            entities = objects.exclude(id__in=not_selected_ids)
    elif select_batch_id is not None:
        entities = objects.filter(Q(batch__id=select_batch_id) | Q(
            id__in=selected_ids)).exclude(id__in=not_selected_ids)
    else:
        entities = objects.filter(id__in=selected_ids)

    if not include_archived:
        entities = entities.exclude_archived()

    return entities.order_by('created_dt', 'id')


def get_selected_adgroup_sources(objects, data, **constraints):
    select_all = data.get('select_all', False)

    selected_ids = parse_post_request_ids(data, 'selected_ids')
    not_selected_ids = parse_post_request_ids(data, 'not_selected_ids')

    entities = objects.filter(Q(**constraints))
    if select_all:
        entities = entities.exclude(source_id__in=not_selected_ids)
    else:
        entities = entities.filter(source_id__in=selected_ids)

    return entities.order_by('id')


def get_selected_entities_post_request(objects, data, include_archived=False, **constraints):
    select_all = data.get('select_all', False)
    select_batch_id = data.get('select_batch')

    selected_ids = parse_post_request_ids(data, 'selected_ids')
    not_selected_ids = parse_post_request_ids(data, 'not_selected_ids')

    return get_selected_entities(objects, select_all, selected_ids, not_selected_ids, include_archived, select_batch_id, **constraints)


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
    """
    Return ad group sources states in a list.
    NOTE: uses a workaround function that calculates AdGroupSourceState as those are not
    saved anymore.
    """

    ad_group_sources_settings = {
        ags.ad_group_source_id: ags for ags in models.AdGroupSourceSettings.objects.filter(
            ad_group_source__in=ad_group_sources,
        ).group_current_settings()
    }

    ad_groups_settings = {
        ag.ad_group_id: ag for ag in models.AdGroupSettings.objects.filter(
            ad_group__in=[ags.ad_group_id for ags in ad_group_sources],
        ).group_current_settings()
    }

    return get_fake_ad_group_source_states(ad_group_sources, ad_group_sources_settings, ad_groups_settings)


def get_fake_ad_group_source_states(ad_group_sources, ad_group_sources_settings_map, ad_groups_settings_map):
    states = []
    for ags in ad_group_sources:
        ad_group_settings = ad_groups_settings_map.get(ags.ad_group.id)
        agss = ad_group_sources_settings_map.get(ags.id)

        if ad_group_settings is None or agss is None:
            logger.error("Missing settings got ad group source: %s", ags.id)
            continue

        state = ad_group_settings.state
        if state == constants.AdGroupSettingsState.ACTIVE:
            state = agss.state

        states.append(
            models.AdGroupSourceState(
                ad_group_source=ags,

                state=state,
                cpc_cc=agss.cpc_cc,
                daily_budget_cc=agss.daily_budget_cc,
                created_dt=agss.created_dt,
            )
        )

    return states


def get_source_status_from_ad_group_source_states(ad_group_source_states):
    if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE for s in ad_group_source_states):
        return constants.AdGroupSourceSettingsState.ACTIVE

    return constants.AdGroupSourceSettingsState.INACTIVE


def get_ad_group_sources_settings(ad_group_sources):
    return models.AdGroupSourceSettings.objects\
        .filter(ad_group_source__in=ad_group_sources)\
        .group_current_settings()\
        .select_related('ad_group_source')


def get_ad_group_table_running_state_by_obj_id(ad_group_id_with_group, ad_groups_settings):
    by_ad_group = {}
    for settings in ad_groups_settings:
        by_ad_group[settings.ad_group_id] = settings.state

    by_group_key = collections.defaultdict(list)
    for ad_group_id, key in ad_group_id_with_group:
        state = by_ad_group.get(ad_group_id)
        if state is not None:
            by_group_key[key].append(state)

    status_dict = collections.defaultdict(lambda: constants.AdGroupSettingsState.INACTIVE)
    for group_key, states in by_group_key.iteritems():
        if constants.AdGroupSettingsState.ACTIVE in states:
            status_dict[group_key] = constants.AdGroupRunningStatus.ACTIVE

    return status_dict


def parse_get_request_content_ad_ids(request_data, param_name):
    content_ad_ids = request_data.get(param_name)

    if not content_ad_ids:
        return []

    try:
        return map(int, content_ad_ids.split(','))
    except ValueError:
        raise exc.ValidationError()


def parse_post_request_ids(request_data, param_name):
    ids = request_data.get(param_name, [])

    try:
        return map(int, ids)
    except ValueError:
        raise exc.ValidationError()


def get_user_full_name_or_email(user, default_value='/'):
    if user is None:
        return default_value

    result = user.get_full_name() or user.email
    return result.encode('utf-8')


def get_target_regions_string(regions):
    if not regions:
        return 'worldwide'

    return ', '.join(constants.AdTargetLocation.get_text(x) for x in regions)


def get_conversion_goals_wo_pixels(conversion_goals):
    """
    Returns conversions goals not of pixel type to be used by in client. Pixels
    are to be returned separately.
    """
    return [{'id': k, 'name': v} for k, v in
            columns.get_conversion_goals_column_names_mapping(conversion_goals).items()]


def get_pixels_list(pixels):
    pixels_list = []
    for pixel in sorted(pixels, key=lambda x: x.name.lower()):
        pixels_list.append({
            'prefix': pixel.get_prefix(),
            'name': pixel.name,
        })
    return pixels_list


def copy_stats_to_row(stat, row):
    for key in ['impressions', 'clicks', 'data_cost', 'cpc', 'ctr', 'cpm',
                'visits', 'click_discrepancy', 'pageviews', 'media_cost',
                'percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos',
                'e_media_cost', 'e_data_cost', 'billing_cost',
                'license_fee', 'margin', 'agency_total', 'unique_users', 'returning_users', 'new_users',
                'bounced_visits', 'total_seconds', 'avg_cost_per_minute', 'non_bounced_visits',
                'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview', 'avg_cost_for_new_visitor',
                'avg_cost_per_visit']:
        row[key] = stat.get(key)

    for key in stat.keys():
        if key.startswith('conversion_goal_') or key.startswith('pixel_') or key.startswith('avg_cost_per_pixel_'):
            row[key] = stat.get(key)

    for key in SPECIAL_COLUMNS:
        if key in stat:
            row[key] = stat[key]


def get_editable_fields(ad_group, ad_group_source, ad_group_settings, ad_group_source_settings,
                        campaign_settings, allowed_sources, can_enable_source):
    editable_fields = {}
    editable_fields['status_setting'] = _get_editable_fields_status_setting(
        ad_group,
        ad_group_source,
        ad_group_settings,
        ad_group_source_settings,
        allowed_sources,
        can_enable_source,
    )

    editable_fields['bid_cpc'] = _get_editable_fields_bid_cpc(
        ad_group,
        ad_group_source,
        ad_group_settings,
        campaign_settings
    )

    editable_fields['daily_budget'] = _get_editable_fields_daily_budget(
        ad_group,
        ad_group_source,
        ad_group_settings,
        campaign_settings
    )

    return editable_fields


def _get_editable_fields_bid_cpc(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    message = None

    if not ad_group_source.source.can_update_cpc() or\
            ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE:
        message = _get_bid_cpc_daily_budget_disabled_message(
            ad_group, ad_group_source, ad_group_settings, campaign_settings)

    return {
        'enabled': message is None,
        'message': message
    }


def _get_editable_fields_daily_budget(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    message = None

    if not ad_group_source.source.can_update_daily_budget_automatic() and\
       not ad_group_source.source.can_update_daily_budget_manual() or\
       campaign_settings.landing_mode or\
       ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        message = _get_daily_budget_disabled_message(
            ad_group, ad_group_source, ad_group_settings, campaign_settings)

    return {
        'enabled': message is None,
        'message': message
    }


def _get_editable_fields_status_setting(ad_group, ad_group_source, ad_group_settings,
                                        ad_group_source_settings, allowed_sources,
                                        can_enable_source):
    message = None

    if ad_group_source.source_id not in allowed_sources:
        message = 'Please contact support to enable this source.'
    elif not can_enable_source:
        message = 'Please add additional budget to your campaign to make changes.'
    elif not ad_group_source.source.can_update_state() or\
            not ad_group_source.can_manage_content_ads:
        message = _get_status_setting_disabled_message(ad_group_source)
    elif ad_group_source_settings is not None and\
            ad_group_source_settings.state == constants.AdGroupSourceSettingsState.INACTIVE:
        message = _get_status_setting_disabled_message_for_target_regions(
            ad_group_source, ad_group_settings, ad_group_source_settings)

    # there are cases where a condition is entered(region targeting) but no
    # error message is output - this is why this is a separate loop
    if message is None and (ad_group_settings.retargeting_ad_groups or
                            ad_group_settings.exclusion_retargeting_ad_groups or
                            ad_group_settings.audience_targeting or
                            ad_group_settings.exclusion_audience_targeting) and \
            not (ad_group_source.source.can_modify_retargeting_automatically() or
                 ad_group_source.source.can_modify_retargeting_manually()):
        message = 'This source can not be enabled because it does not support retargeting.'
    elif message is None and not check_facebook_source(ad_group_source):
        message = 'Please connect your Facebook page to add Facebook as media source.'
    elif message is None and not check_yahoo_min_cpc(ad_group_settings, ad_group_source_settings):
        message = 'This source can not be enabled with the current settings - CPC too low for desktop targeting.'
    elif message is None and not check_max_cpm(ad_group_source, ad_group_settings):
        message = 'This source can not be enabled because it does not support max CPM restriction.'

    return {
        'enabled': message is None,
        'message': message
    }


def get_source_supply_dash_disabled_message(ad_group_source, source):
    if not source.has_3rd_party_dashboard():
        return "This media source doesn't have a dashboard of its own. " \
            "All campaign management is done through Zemanta One dashboard."

    return None


def check_facebook_source(ad_group_source):
    if ad_group_source.source.source_type.type != constants.SourceType.FACEBOOK:
        return True

    try:
        facebook_account_status = ad_group_source.ad_group.campaign.account.facebookaccount.status
        return facebook_account_status == constants.FacebookPageRequestType.CONNECTED
    except models.FacebookAccount.DoesNotExist:
        return False


def check_yahoo_min_cpc(ad_group_settings, ad_group_source_settings):
    source_type = ad_group_source_settings.ad_group_source.source.source_type
    if source_type.type != constants.SourceType.YAHOO:
        return True

    min_cpc = source_type.get_min_cpc(ad_group_settings)
    if min_cpc and ad_group_source_settings.cpc_cc < min_cpc:
        return False

    return True


def check_max_cpm(ad_group_source, ad_group_settings):
    if ad_group_settings.max_cpm and not ad_group_source.source.source_type.can_set_max_cpm():
            return False

    return True


def _get_status_setting_disabled_message(ad_group_source):
    if ad_group_source.source.maintenance:
        return 'This source is currently in maintenance mode.'

    if not ad_group_source.can_manage_content_ads:
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


def _get_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    if campaign_settings.landing_mode:
        return 'This value cannot be edited because campaign is in landing mode.'

    return _get_bid_cpc_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings)


def _get_bid_cpc_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    if ad_group_source.source.maintenance:
        return 'This value cannot be edited because the media source is currently in maintenance.'

    if ad_group_settings.autopilot_state in [constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                                             constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET]:
        return 'This value cannot be edited because the ad group is on Autopilot.'

    return 'This media source doesn\'t support setting this value through the dashboard.'


def enabling_autopilot_sources_allowed(ad_group_settings, number_of_sources_to_enable=1):
    if ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return True
    required_budget = number_of_sources_to_enable * automation.autopilot_settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC
    return ad_group_settings.autopilot_daily_budget - required_budget >=\
        automation.autopilot_budgets.get_adgroup_minimum_daily_budget(ad_group_settings.ad_group)


def add_source_to_ad_group(default_source_settings, ad_group):
    ad_group_source = models.AdGroupSource(
        source=default_source_settings.source,
        ad_group=ad_group,
        source_credentials=default_source_settings.credentials,
        can_manage_content_ads=default_source_settings.source.can_manage_content_ads(),
    )

    return ad_group_source


def set_ad_group_source_settings(
        request, ad_group_source, mobile_only=False, active=False, max_cpc=None):
    cpc_cc = ad_group_source.source.default_cpc_cc
    if mobile_only:
        cpc_cc = ad_group_source.source.default_mobile_cpc_cc
    ag_settings = ad_group_source.ad_group.get_current_settings()
    if (ag_settings.b1_sources_group_enabled and
            ag_settings.b1_sources_group_cpc_cc > 0.0 and
            ad_group_source.source.source_type.type == constants.SourceType.B1):
        cpc_cc = ag_settings.b1_sources_group_cpc_cc
    if max_cpc:
        cpc_cc = min(max_cpc, cpc_cc)

    resource = {
        'daily_budget_cc': ad_group_source.source.default_daily_budget_cc,
        'cpc_cc': cpc_cc,
        'state': constants.ContentAdSourceState.ACTIVE if active else constants.ContentAdSourceState.INACTIVE
    }

    api.set_ad_group_source_settings(
        ad_group_source,
        resource,
        request,
        ping_k1=False,
    )


def format_decimal_to_percent(num):
    return '{:.2f}'.format(num * 100).rstrip('0').rstrip('.')


def format_percent_to_decimal(num):
    return Decimal(str(num).replace(',', '').strip('%')) / 100


def get_source_default_settings(source):
    try:
        default_settings = models.DefaultSourceSettings.objects.get(source=source)
    except models.DefaultSourceSettings.DoesNotExist:
        raise exc.MissingDataError('No default settings set for {}.'.format(source.name))

    if not default_settings.credentials:
        raise exc.MissingDataError('No default credentials set in {}.'.format(default_settings))

    return default_settings


def _update_ad_groups_redirector_settings(campaign, campaign_settings):
    for ad_group in campaign.adgroup_set.all():
        ad_group_settings = ad_group.get_current_settings()
        redirector_helper.insert_adgroup(
            ad_group,
            ad_group_settings,
            campaign_settings,
        )


def save_campaign_settings_and_propagate(campaign, old_settings, new_settings, request):
    with transaction.atomic():
        campaign.save(request)
        new_settings.save(request)

        # propagate setting changes to all adgroups(adgroup sources) belonging to campaign
        campaign_ad_groups = models.AdGroup.objects.filter(campaign=campaign)

        any_tracking_changes = any(prop in old_settings.get_setting_changes(new_settings) for prop in
                                   ['enable_ga_tracking', 'enable_adobe_tracking', 'adobe_tracking_param'])
        if any_tracking_changes:
            _update_ad_groups_redirector_settings(campaign, new_settings)

    k1_helper.update_ad_groups((ad_group.pk for ad_group in campaign_ad_groups),
                               msg='views.helpers.save_campaign_settings_and_propagate')


def log_and_notify_campaign_settings_change(campaign, old_settings, new_settings, request):
    changes = old_settings.get_setting_changes(new_settings)
    if changes:
        history_changes_text = models.CampaignSettings.get_changes_text(
            old_settings,
            new_settings,
            separator=', ')
        campaign.write_history(
            history_changes_text,
            user=request.user,
            action_type=constants.HistoryActionType.SETTINGS_CHANGE)

        if len(changes) > 1 or 'iab_category' not in changes:
            changes_text = models.CampaignSettings.get_changes_text(
                old_settings,
                new_settings,
                separator='\n')
            email_helper.send_campaign_notification_email(campaign, request, changes_text)


def get_users_for_manager(user, account, current_manager=None):
    if user.has_perm('zemauth.can_see_all_users_for_managers'):
        users = zemauth.models.User.objects.all()
    else:
        users = account.users.all()
        if account.is_agency():
            users |= account.agency.users.all()

    if current_manager is not None:
        users |= zemauth.models.User.objects.filter(pk=current_manager.id)

    return users.filter(is_active=True).distinct()


def validate_ad_groups_state(ad_groups, campaign, campaign_settings, state):
    if state is None or state not in constants.AdGroupSettingsState.get_all():
        raise exc.ValidationError()

    if not automation.campaign_stop.can_enable_all_ad_groups(campaign, campaign_settings, ad_groups):
        raise exc.ValidationError('Please add additional budget to your campaign to make changes.')

    if state == constants.AdGroupSettingsState.ACTIVE:
        if not data_helper.campaign_has_available_budget(campaign):
            raise exc.ValidationError('Cannot enable ad group without available budget.')

        if models.CampaignGoal.objects.filter(campaign=campaign).count() == 0:
            raise exc.ValidationError('Please add a goal to your campaign before enabling this ad group.')


def get_upload_batches_for_ad_group(ad_group):
    batch_ids = models.ContentAd.objects.filter(ad_group_id=ad_group.id).distinct('batch_id').values_list('batch_id')
    return models.UploadBatch.objects.filter(pk__in=batch_ids)
