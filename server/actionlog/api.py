import logging
import sys
import traceback
import urlparse
import collections
from operator import attrgetter

from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from . import exceptions
from . import models
from . import constants
from . import zwei_actions

import dash.constants
import dash.models

logger = logging.getLogger(__name__)


def init_enable_ad_group(ad_group, request, order=None):
    source_settings_qs = dash.models.AdGroupSourceSettings.objects \
        .distinct('ad_group_source_id') \
        .filter(ad_group_source__ad_group=ad_group) \
        .order_by('ad_group_source_id', '-created_dt')

    for source_settings in source_settings_qs:
        if source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE:
            changes = {
                'state': dash.constants.AdGroupSourceSettingsState.ACTIVE,
            }
            set_ad_group_source_settings(changes, source_settings.ad_group_source, request, order=order)


def init_pause_ad_group(ad_group, request, order=None):
    for ad_group_source in dash.models.AdGroupSource.objects.filter(ad_group=ad_group):
        changes = {
            'state': dash.constants.AdGroupSourceSettingsState.INACTIVE,
        }

        set_ad_group_source_settings(changes, ad_group_source, request, order=order)


def init_set_ad_group_property_order(ad_group, request, source=None, prop=None, value=None):
    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
        )
        _set_ad_group_property(ad_group, request, source=source, prop=prop, value=value, order=order)


def set_ad_group_source_settings(changes, ad_group_source, request, order=None):
    if changes.get('cpc_cc') is not None:
        changes['cpc_cc'] = int(changes['cpc_cc'] * 10000)
    if changes.get('daily_budget_cc') is not None:
        changes['daily_budget_cc'] = int(changes['daily_budget_cc'] * 10000)

    _init_set_ad_group_source_settings(
        ad_group_source=ad_group_source,
        conf=changes,
        request=request,
        order=order
    )
    send_delayed_actionlogs([ad_group_source])


def _set_ad_group_property(ad_group, request, source=None, prop=None, value=None, order=None):
    ad_group_sources = _get_ad_group_sources(ad_group, source)
    for ad_group_source in ad_group_sources:
        try:
            _init_set_campaign_property(ad_group_source, prop, value, order, request)
        except exceptions.InsertActionException:
            continue


def create_campaign(ad_group_source, name, request):
    try:
        action = _init_create_campaign(ad_group_source, name, request)
    except exceptions.InsertActionException:
        pass
    else:
        zwei_actions.send(action)


@transaction.atomic
def cancel_expired_actionlogs():
    waiting_actionlogs = models.ActionLog.objects.\
        filter(
            state=constants.ActionState.WAITING,
            expiration_dt__lt=datetime.utcnow()
        )

    for actionlog in waiting_actionlogs:
        logger.info(
            'Action log %s has expired. Updating state to: %s.',
            actionlog,
            constants.ActionState.FAILED
        )

        actionlog.message = 'Action log has expired.'
        actionlog.state = constants.ActionState.FAILED
        actionlog.save()


@transaction.atomic
def send_delayed_actionlogs(ad_group_sources=None):
    delayed_actionlogs = models.ActionLog.objects.filter(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        state=constants.ActionState.DELAYED,
    ).order_by('created_dt')

    if ad_group_sources is not None:
        delayed_actionlogs = delayed_actionlogs.filter(ad_group_source__in=ad_group_sources)

    for actionlog in delayed_actionlogs:
        waiting_actionlogs = models.ActionLog.objects.filter(
            state=constants.ActionState.WAITING,
            action=constants.Action.SET_CAMPAIGN_STATE,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=actionlog.ad_group_source,
        )

        if waiting_actionlogs.exists():
            continue

        logger.info(
            'Sending delayed action log %s. Updating state to: %s.',
            actionlog,
            constants.ActionState.WAITING
        )
        actionlog.state = constants.ActionState.WAITING
        actionlog.expiration_dt = models._due_date_default()
        actionlog.payload['expiration_dt'] = actionlog.expiration_dt
        actionlog.save()

        zwei_actions.send(actionlog)


def get_ad_group_sources_waiting(**kwargs):
    constraints = {}

    if 'ad_group' in kwargs:
        key = 'ad_group_source__ad_group'
        if isinstance(kwargs['ad_group'], collections.Sequence):
            key += '__in'
        constraints[key] = kwargs['ad_group']
    if 'campaign' in kwargs:
        key = 'ad_group_source__ad_group__campaign'
        if isinstance(kwargs['campaign'], collections.Sequence):
            key += '__in'
        constraints[key] = kwargs['campaign']
    if 'account' in kwargs:
        key = 'ad_group_source__ad_group__campaign__account'
        if isinstance(kwargs['account'], collections.Sequence):
            key += '__in'
        constraints[key] = kwargs['account']

    actions = models.ActionLog.objects.filter(
        action=constants.Action.CREATE_CAMPAIGN,
        state__in=[constants.ActionState.WAITING, constants.ActionState.FAILED],
        action_type=constants.ActionType.AUTOMATIC,
        **constraints
    )

    return [action.ad_group_source for action in actions]


def is_waiting_for_set_actions(ad_group):
    action_types = (constants.Action.SET_CAMPAIGN_STATE, constants.Action.SET_PROPERTY)
    ad_group_sources = ad_group.adgroupsource_set.all()
    # get latest action for ad_group where order != null
    # using two queries for performance reasons
    try:
        latest_set_campaign_state_action = models.ActionLog.objects.filter(
            action=constants.Action.SET_CAMPAIGN_STATE,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        latest_set_campaign_state_action = None

    try:
        latest_set_property_action = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        latest_set_property_action = None

    if latest_set_campaign_state_action is None and latest_set_property_action is None:
        return False

    latest_action = max(
        [a for a in [latest_set_campaign_state_action, latest_set_property_action] if a is not None],
        key=attrgetter('created_dt'))

    # check whether there are unsuccessful actions in this order
    is_fail_in_latest_group = models.ActionLog.objects.filter(
        action__in=action_types,
        state=constants.ActionState.FAILED,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources],
        order=latest_action.order
    ).exists()

    is_any_waiting_action = models.ActionLog.objects.filter(
        action__in=action_types,
        state=constants.ActionState.WAITING,
        ad_group_source_id__in=[ags.id for ags in ad_group_sources],
    ).exists()

    return is_fail_in_latest_group or is_any_waiting_action


def count_waiting_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) | Q(action=constants.Action.CREATE_CAMPAIGN),
        state=constants.ActionState.WAITING
    ).count()


def count_delayed_stats_actions():
    return models.ActionLog.objects.filter(
        state=constants.ActionState.DELAYED
    ).count()


def count_failed_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) |
        Q(action=constants.Action.CREATE_CAMPAIGN) |
        Q(action=constants.Action.SET_CAMPAIGN_STATE),
        state=constants.ActionState.FAILED
    ).count()


def age_oldest_waiting_action(manual_action=True):
    if manual_action:
        filter_constraints = Q(action_type=constants.ActionType.MANUAL)
    else:
        filter_constraints = Q(action_type=constants.ActionType.AUTOMATIC)

    waiting_actions = models.ActionLog.objects.filter(
        filter_constraints,
        state=constants.ActionState.WAITING
    ).order_by('created_dt')

    if not waiting_actions.exists():
        return 0

    return int((datetime.utcnow() - waiting_actions[0].created_dt).total_seconds() / 3600)


def is_sync_in_progress(ad_groups=None, campaigns=None, accounts=None, sources=None):
    '''
    sync is in progress if one of the following is true:
    - a get reports action for this ad_group is in 'waiting' state
    - a fetch status action for this ad_group is in 'waiting' state
    '''

    if ad_groups and accounts:
        raise Exception('Please set only one, ad_groups or accounts.')

    q = models.ActionLog.objects.filter(
        state=constants.ActionState.WAITING,
        action_type=constants.ActionType.AUTOMATIC,
        action__in=(constants.Action.FETCH_REPORTS,
                    constants.Action.FETCH_CAMPAIGN_STATUS)
    )

    if ad_groups:
        q = q.filter(ad_group_source__ad_group__in=ad_groups)
    elif campaigns:
        q = q.filter(ad_group_source__ad_group__campaign__in=campaigns)
    elif accounts:
        q = q.filter(ad_group_source__ad_group__campaign__account__in=accounts)

    if sources:
        q = q.filter(ad_group_source__source__in=sources)

    waiting_actions = q.exists()

    return waiting_actions


def _handle_error(action, e, request=None):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save(request)


def _get_ad_group_sources(ad_group, source):
    inactive_ad_group_sources = get_ad_group_sources_waiting(ad_group=ad_group)

    active_ad_group_sources = dash.models.AdGroupSource.objects \
        .filter(ad_group=ad_group) \
        .exclude(pk__in=[ags.id for ags in inactive_ad_group_sources])

    if not source:
        return active_ad_group_sources.all()

    return active_ad_group_sources.filter(source=source)


def _get_ad_group_settings(ad_group):
    s = dash.models.AdGroupSettings.objects.filter(ad_group=ad_group)
    if s:
        return s.latest('created_dt')

    return None


def _get_campaign_settings(campaign):
    s = dash.models.CampaignSettings.objects.filter(campaign=campaign)
    if s:
        return s.latest('created_dt')

    return None


def _create_manual_action(ad_group_source, conf, request, order=None, message=''):
    for prop, val in conf.iteritems():
        action = models.ActionLog(
            action=constants.Action.SET_PROPERTY,
            action_type=constants.ActionType.MANUAL,
            expiration_dt=None,
            state=constants.ActionState.WAITING,
            ad_group_source=ad_group_source,
            payload={
                'property': prop,
                'value': val
            },
            order=order,
            message=message
        )
    action.save(request)


def _init_set_ad_group_source_settings(ad_group_source, conf, request, order=None):
    logger.info('_init_set_ad_group_source_settings started: ad_group_source.id: %s, settings: %s',
                ad_group_source.id, str(conf))

    if ad_group_source.source.maintenance:
        _create_manual_action(
            ad_group_source,
            conf,
            request,
            order=order,
            message="Due to media source being in maintenance mode a manual action is required."
        )
        return

    action = models.ActionLog(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        expiration_dt=None,
        state=constants.ActionState.DELAYED,
        ad_group_source=ad_group_source,
        order=order
    )
    action.save(request)

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_source.source_credentials and
                    ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'conf': conf
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

    except Exception as e:
        logger.exception('An exception occurred while initializing set_campaign_state action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_fetch_status(ad_group_source, order, request=None):
    msg = '_init_fetch_status started: ad_group_source.id: {}'.format(
        ad_group_source.id
    )
    logger.info(msg)

    action = models.ActionLog(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )
    action.save(request)

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_source.source_credentials and
                    ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_campaign_status action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_fetch_reports(ad_group_source, date, order, request=None):
    msg = '_init_fetch_reports started: ad_group_source.id: {}, date: {}'.format(
        ad_group_source.id,
        repr(date)
    )
    logger.info(msg)

    action = models.ActionLog(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )
    action.save(request)

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_source.source_credentials and
                    ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_reports action')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _init_set_campaign_property(ad_group_source, prop, value, order, request):
    msg = "_init_set_campaign_property started: ad_group_source.id: {}, prop: {}, value: {}, order.id: {}".format(
        ad_group_source.id,
        prop,
        value,
        order.id if order else order
    )
    logger.info(msg)
    try:
        existing_actions = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL
        )
        existing_actions = [a for a in existing_actions if a.payload['property'] == prop]
        action = models.ActionLog(
            action=constants.Action.SET_PROPERTY,
            action_type=constants.ActionType.MANUAL,
            expiration_dt=None,
            state=constants.ActionState.WAITING,
            ad_group_source=ad_group_source,
            payload={
                'property': prop,
                'value': value,
            },
            order=order
        )
        action.save(request)

        if existing_actions:
            for a in existing_actions:
                a.state = constants.ActionState.ABORTED
                a.save(request)

    except Exception as e:
        logger.exception('An exception occurred while initializing set_property action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


def _combine_tracking_codes(ad_group_source, ad_group_settings):
    ad_group_settings_tracking_ids = ad_group_settings.get_tracking_ids()
    ad_group_source_tracking_ids = ad_group_source.get_tracking_ids()

    if ad_group_settings_tracking_ids:
        # Ad group settings tracking code is always first
        return ad_group_settings_tracking_ids + '&' + ad_group_source_tracking_ids

    return ad_group_source_tracking_ids


def _init_create_campaign(ad_group_source, name, request):
    if ad_group_source.source_campaign_key:
        msg = 'Unable to create external campaign for AdGroupSource with existing connection'\
              'ad_group_source.id={ad_group_source_id}, name={name}'.format(
                  ad_group_source_id=ad_group_source.id,
                  name=name,
              )
        logger.error(msg)

        raise exceptions.InsertCreateCampaignActionException(msg)

    msg = "_init_create_campaign started: ad_group_source.id: {}, name: {}".format(
        ad_group_source.id,
        name,
    )
    logger.info(msg)

    order = models.ActionLogOrder.objects.create(
        order_type=constants.ActionLogOrderType.CREATE_CAMPAIGN
    )

    action = models.ActionLog(
        action=constants.Action.CREATE_CAMPAIGN,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )
    action.save(request)

    ad_group_settings = _get_ad_group_settings(ad_group_source.ad_group)
    campaign_settings = _get_campaign_settings(ad_group_source.ad_group.campaign)

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_source.source_credentials and
                    ad_group_source.source_credentials.credentials,
                'args': {
                    'name': name,
                    'extra': {},
                },
                'callback_url': callback,
            }

            if ad_group_source.source.source_type.type == dash.constants.SourceType.OUTBRAIN:
                payload['args']['marketer_id'] = _get_outbrain_marketer_id(
                    ad_group_source.ad_group.campaign.account,
                    request
                )

            if ad_group_source.source.source_type.type == dash.constants.SourceType.B1:
                payload['args']['extra']['ad_group_id'] = ad_group_source.ad_group.id
                payload['args']['extra']['exchange'] = ad_group_source.source.bidder_slug

            if hasattr(ad_group_source.source, 'defaultsourcesettings'):
                params = ad_group_source.source.defaultsourcesettings.params
                if 'create_campaign' in params:
                    payload['args']['extra'].update(params['create_campaign'])

            if ad_group_settings:
                payload['args']['extra'].update({
                    'target_devices': ad_group_settings.target_devices,
                    'target_regions': ad_group_settings.target_regions,
                    'brand_name': ad_group_settings.brand_name,
                    'display_url': ad_group_settings.display_url,
                    'start_date': ad_group_settings.start_date,
                    'end_date': ad_group_settings.end_date,
                })

            payload['args']['extra'].update({
                'tracking_code': _combine_tracking_codes(ad_group_source, ad_group_settings),
                'tracking_slug': ad_group_source.source.tracking_slug
            })

            if campaign_settings:
                payload['args']['extra'].update({
                    'iab_category': campaign_settings.iab_category,
                })

            action.payload = payload
            action.save(request)

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing create_campaign action.')
        _handle_error(action, e, request)

        et, ei, tb = sys.exc_info()
        raise exceptions.InsertActionException, ei, tb


@transaction.atomic()
def _get_outbrain_marketer_id(account, request):
    if account.outbrain_marketer_id:
        return account.outbrain_marketer_id

    try:
        outbrain_account = dash.models.OutbrainAccount.objects.\
            filter(used=False).order_by('created_dt')[0]
    except IndexError:
        raise Exception('No unused Outbrain accounts available.')

    outbrain_account.used = True
    outbrain_account.save()

    account.outbrain_marketer_id = outbrain_account.marketer_id
    account.save(request)

    return account.outbrain_marketer_id
