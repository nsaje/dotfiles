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
import automation.autopilot

from dash import models
from dash import constants
from dash import cpc_constraints

from dash.dashapi import data_helper

from utils import exc
from utils import columns

from restapi.access import get_content_ad, get_ad_group, get_campaign, get_account, get_upload_batch  # noqa

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
            filtered_agencies_raw = data.get('filtered_agencies')
            filtered_agencies = filtered_agencies_raw.split(',') if\
                filtered_agencies_raw else None
            filtered_account_types_raw = data.get('filtered_account_types')
            filtered_account_types = filtered_account_types_raw.split(',') if\
                filtered_account_types_raw else None
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

    filtered_ids = list(map(int, agency_filter))
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
    filtered_ids = list(map(int, account_type_filter))
    return list(set(filtered_account_types) & set(filtered_ids))


def get_additional_columns(additional_columns):
    if additional_columns:
        return additional_columns.split(',')
    return []


def get_publisher_group(user, account_id, publisher_group_id):
    try:
        account = get_account(user, account_id)
        return models.PublisherGroup.objects.all().filter_by_account(account)\
                                                  .get(pk=publisher_group_id)
    except models.PublisherGroup.DoesNotExist:
        raise exc.MissingDataError('Publisher group does not exist')


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


def get_source_initial_state(ad_group_source):
    if ad_group_source.source.source_type.type in (constants.SourceType.FACEBOOK, ):
        return check_facebook_source(ad_group_source)
    if ad_group_source.source.maintenance or ad_group_source.source.deprecated:
        return False
    return True


def get_ad_group_sources_last_change_dt(
        ad_group_sources, ad_group_sources_settings, last_change_dt=None):

    changed_ad_group_sources = []
    last_change_dts = []

    for ad_group_source in ad_group_sources:
        current_settings = _get_ad_group_source_settings_from_filter_qs(ad_group_source, ad_group_sources_settings)

        if not current_settings or not current_settings.created_dt:
            continue

        source_last_change = current_settings.created_dt
        if last_change_dt is not None and source_last_change <= last_change_dt:
            continue

        changed_ad_group_sources.append(ad_group_source)
        last_change_dts.append(source_last_change)

    if len(last_change_dts) == 0:
        return None, []

    return max(last_change_dts), changed_ad_group_sources


def get_ad_group_sources_notifications(ad_group_sources, ad_group_settings,
                                       ad_group_sources_settings):
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
                                 ' you enable ad group.')
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


def get_selected_entities(objects, select_all, selected_ids, not_selected_ids, include_archived, select_batch_id=None, **constraints):
    objects = objects.filter(Q(**constraints))
    if select_all:
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


def get_ad_group_sources_settings(ad_group_sources):
    return models.AdGroupSourceSettings.objects\
        .filter(ad_group_source__in=ad_group_sources)\
        .group_current_settings()\
        .select_related('ad_group_source')


def parse_get_request_content_ad_ids(request_data, param_name):
    content_ad_ids = request_data.get(param_name)

    if not content_ad_ids:
        return []

    try:
        return list(map(int, content_ad_ids.split(',')))
    except ValueError:
        raise exc.ValidationError()


def parse_post_request_ids(request_data, param_name):
    ids = request_data.get(param_name, [])

    try:
        return list(map(int, ids))
    except ValueError:
        raise exc.ValidationError()


def get_user_full_name_or_email(user, default_value='/'):
    if user is None:
        return default_value

    result = user.get_full_name() or user.email
    return result


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
            sorted(columns.get_conversion_goals_column_names_mapping(conversion_goals).items())]


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
                'license_fee', 'margin', 'agency_cost', 'unique_users', 'returning_users', 'new_users',
                'bounced_visits', 'total_seconds', 'avg_cost_per_minute', 'non_bounced_visits',
                'avg_cost_per_non_bounced_visit', 'avg_cost_per_pageview', 'avg_cost_for_new_visitor',
                'avg_cost_per_visit']:
        row[key] = stat.get(key)

    for key in list(stat.keys()):
        if key.startswith('conversion_goal_') or key.startswith('pixel_') or key.startswith('avg_cost_per_pixel_'):
            row[key] = stat.get(key)

    for key in SPECIAL_COLUMNS:
        if key in stat:
            row[key] = stat[key]


def get_editable_fields(ad_group, ad_group_source, ad_group_settings, ad_group_source_settings,
                        campaign_settings, allowed_sources):
    editable_fields = {}
    editable_fields['status_setting'] = _get_editable_fields_status_setting(
        ad_group,
        ad_group_source,
        ad_group_settings,
        ad_group_source_settings,
        allowed_sources,
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

    if (not ad_group_source.source.can_update_cpc() or
            ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE or
            campaign_settings.autopilot):
        message = _get_bid_cpc_daily_budget_disabled_message(
            ad_group, ad_group_source, ad_group_settings, campaign_settings)

    return {
        'enabled': message is None,
        'message': message
    }


def _get_editable_fields_daily_budget(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    message = None

    if (not ad_group_source.source.can_update_daily_budget_automatic() and
            not ad_group_source.source.can_update_daily_budget_manual() or
            campaign_settings.landing_mode or
            ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET or
            campaign_settings.autopilot):
        message = _get_daily_budget_disabled_message(
            ad_group, ad_group_source, ad_group_settings, campaign_settings)

    return {
        'enabled': message is None,
        'message': message
    }


def _get_editable_fields_status_setting(ad_group, ad_group_source, ad_group_settings,
                                        ad_group_source_settings, allowed_sources):
    message = None

    if ad_group_source.source_id not in allowed_sources:
        message = 'Please contact support to enable this source.'
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
    elif message is None and not check_yahoo_min_cpc(ad_group_settings, ad_group_source, ad_group_source_settings):
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


def check_yahoo_min_cpc(ad_group_settings, ad_group_source, ad_group_source_settings):
    source_type = ad_group_source.source.source_type
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
        return 'This source can not be enabled because it does not support {} targeting.'.format(" and ".join(sorted(unsupported_targets)))


def _get_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    if campaign_settings.landing_mode:
        return 'This value cannot be edited because campaign is in landing mode.'

    return _get_bid_cpc_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings)


def _get_bid_cpc_daily_budget_disabled_message(ad_group, ad_group_source, ad_group_settings, campaign_settings):
    if ad_group_source.source.maintenance:
        return 'This value cannot be edited because the media source is currently in maintenance.'

    if campaign_settings.autopilot:
        return 'This value cannot be edited because the campaign is on Autopilot.'

    if ad_group_settings.autopilot_state in [constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                                             constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET]:
        return 'This value cannot be edited because the ad group is on Autopilot.'

    return 'This media source doesn\'t support setting this value through the dashboard.'


def enabling_autopilot_sources_allowed(ad_group, ad_group_sources):
    if not ad_group.settings.b1_sources_group_enabled:
        num_sources = len(ad_group_sources)
    else:
        num_sources = sum(
            1 for ags in ad_group_sources
            if ags.source.source_type.type != constants.SourceType.B1
        )

    return _enabling_autopilot_sources_allowed(ad_group, num_sources)


def enabling_autopilot_single_source_allowed(ad_group):
    return _enabling_autopilot_sources_allowed(ad_group, 1)


def _enabling_autopilot_sources_allowed(ad_group, number_of_sources_to_enable):
    if ad_group.campaign.settings.autopilot:
        return True
    if ad_group.settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
        return True

    required_budget = (
        number_of_sources_to_enable *
        automation.autopilot.settings.BUDGET_AUTOPILOT_MIN_DAILY_BUDGET_PER_SOURCE_CALC
    )
    return ad_group.settings.autopilot_daily_budget - required_budget >=\
        automation.autopilot.get_adgroup_minimum_daily_budget(ad_group, ad_group.settings)


def get_adjusted_ad_group_sources_cpcs(ad_group, ad_group_settings):
    adjusted_cpcs = {}
    for ad_group_source in ad_group.adgroupsource_set.all().select_related('source__source_type', 'settings', 'ad_group__settings', 'ad_group__campaign__settings', 'ad_group__campaign__account__agency'):
        proposed_cpc = ad_group_source.get_current_settings().cpc_cc
        adjusted_cpc = _get_adjusted_ad_group_source_cpc(proposed_cpc, ad_group_source, ad_group_settings)
        if ad_group_source.source.source_type.type != constants.SourceType.B1\
           and ad_group_source.get_current_settings().state == constants.AdGroupSourceSettingsState.INACTIVE:
            continue
        adjusted_cpcs[ad_group_source] = adjusted_cpc
    return adjusted_cpcs


def validate_ad_group_sources_cpc_constraints(bcm_modifiers, ad_group_sources_cpcs, ad_group):
    rules_per_source = cpc_constraints.get_rules_per_source(ad_group, bcm_modifiers)
    for ad_group_source, proposed_cpc in list(ad_group_sources_cpcs.items()):
        if proposed_cpc:
            cpc_constraints.validate_cpc(
                proposed_cpc,
                rules=rules_per_source[ad_group_source.source],
            )


@transaction.atomic
def set_ad_group_sources_cpcs(ad_group_sources_cpcs, ad_group, ad_group_settings, skip_validation=False):
    rules_per_source = cpc_constraints.get_rules_per_source(ad_group)
    for ad_group_source, proposed_cpc in list(ad_group_sources_cpcs.items()):
        adjusted_cpc = _get_adjusted_ad_group_source_cpc(proposed_cpc, ad_group_source, ad_group_settings)
        if adjusted_cpc:
            adjusted_cpc = cpc_constraints.adjust_cpc(adjusted_cpc, rules=rules_per_source[ad_group_source.source])

        ad_group_source_settings = ad_group_source.get_current_settings()
        if ad_group_source_settings.cpc_cc == adjusted_cpc:
            continue
        ad_group_source.settings.update(
            cpc_cc=adjusted_cpc,
            k1_sync=False,
            skip_validation=skip_validation,
        )


def _get_adjusted_ad_group_source_cpc(proposed_cpc, ad_group_source, ad_group_settings):
    if (
            ad_group_settings.b1_sources_group_enabled and
            ad_group_source.source.source_type.type == constants.SourceType.B1 and
            ad_group_settings.autopilot_state != constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    ):
        proposed_cpc = ad_group_settings.b1_sources_group_cpc_cc
    return adjust_max_cpc(proposed_cpc, ad_group_settings)


def adjust_max_cpc(proposed_cpc, ad_group_settings):
    if not (proposed_cpc and ad_group_settings.cpc_cc):
        return proposed_cpc

    if proposed_cpc > ad_group_settings.cpc_cc:
        return ad_group_settings.cpc_cc

    return proposed_cpc


def format_decimal_to_percent(num):
    return '{:.2f}'.format(num * 100).rstrip('0').rstrip('.')


def format_percent_to_decimal(num):
    return Decimal(str(num).replace(',', '').strip('%')) / 100


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

    if state == constants.AdGroupSettingsState.ACTIVE:
        if not data_helper.campaign_has_available_budget(campaign):
            raise exc.ValidationError('Cannot enable ad group without available budget.')

        if models.CampaignGoal.objects.filter(campaign=campaign).count() == 0:
            raise exc.ValidationError('Please add a goal to your campaign before enabling this ad group.')


def get_upload_batches_for_ad_group(ad_group):
    batch_ids = models.ContentAd.objects.filter(ad_group_id=ad_group.id).distinct('batch_id').values_list('batch_id')
    return models.UploadBatch.objects.filter(pk__in=batch_ids)
