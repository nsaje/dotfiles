import logging
import sys
import traceback
import urlparse
import urllib
import collections

from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from . import models
from . import constants
from . import zwei_actions

import dash.constants
import dash.models

logger = logging.getLogger(__name__)


class InsertActionException(Exception):
    pass


class InsertCreateCampaignActionException(InsertActionException):
    pass


def init_stop_ad_group_order(ad_group, source=None):
    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.STOP_ALL
        )
        actionlogs = stop_ad_group(ad_group, source, order, commit=False)

    zwei_actions.send_multiple(actionlogs)


def init_set_ad_group_property_order(ad_group, source=None, prop=None, value=None):
    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
        )
        set_ad_group_property(ad_group, source=source, prop=prop, value=value, order=order)


def stop_ad_group(ad_group, source=None, order=None, commit=True):
    ad_group_sources = _get_ad_group_sources(ad_group, source)

    actionlogs = []
    for ad_group_source in ad_group_sources:
        try:
            actionlogs.append(_init_stop_campaign(ad_group_source, order))
        except InsertActionException:
            continue

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def set_ad_group_source_settings(changes, ad_group_source_settings):
    if changes.get('cpc_cc') is not None:
        changes['cpc_cc'] = int(changes['cpc_cc'] * 10000)
    if changes.get('daily_budget_cc') is not None:
        changes['daily_budget_cc'] = int(changes['daily_budget_cc'] * 10000)

    action = _init_set_ad_group_source_settings(
        ad_group_source=ad_group_source_settings.ad_group_source,
        settings_id=ad_group_source_settings.id,
        conf=changes
    )

    zwei_actions.send_multiple([action])


def set_ad_group_property(ad_group, source=None, prop=None, value=None, order=None):
    ad_group_sources = _get_ad_group_sources(ad_group, source)
    for ad_group_source in ad_group_sources:
        try:
            _init_set_campaign_property(ad_group_source, prop, value, order)
        except InsertActionException:
            continue


def create_campaign(ad_group_source, name):
    try:
        action = _init_create_campaign(ad_group_source, name)
    except InsertActionException:
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
    try:
        latest_action = models.ActionLog.objects.filter(
            action__in=action_types,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        return False
    # check whether there are unsuccessful actions in this order
    is_fail_in_latest_group = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.FAILED,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
            order=latest_action.order
        ).\
        exists()

    is_any_waiting_action = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.WAITING,
            ad_group_source_id__in=[ags.id for ags in ad_group_sources],
        ).\
        exists()

    return is_fail_in_latest_group or is_any_waiting_action


def count_waiting_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) | Q(action=constants.Action.CREATE_CAMPAIGN),
        state=constants.ActionState.WAITING
    ).count()


def count_failed_stats_actions():
    return models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) |
        Q(action=constants.Action.CREATE_CAMPAIGN) |
        Q(action=constants.Action.SET_CAMPAIGN_STATE),
        state=constants.ActionState.FAILED
    ).count()


def age_oldest_waiting_stats_action():
    waiting_actions = models.ActionLog.objects.filter(
        Q(action_type=constants.ActionType.MANUAL) | Q(action=constants.Action.CREATE_CAMPAIGN),
        state=constants.ActionState.WAITING
    ).order_by('created_dt')

    if not waiting_actions.exists():
        return 0

    return int((datetime.utcnow() - waiting_actions[0].created_dt).total_seconds() / 3600)


def is_sync_in_progress(ad_groups=None, campaigns=None, accounts=None):
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

    waiting_actions = q.exists()

    return waiting_actions


def _handle_error(action, e):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


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


def _init_stop_campaign(ad_group_source, order):
    logger.info('_init_stop started: ad_group_source.id: %s', ad_group_source.id)

    action = models.ActionLog.objects.create(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )

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
                    'conf': {
                        'state': dash.constants.AdGroupSourceSettingsState.INACTIVE,
                    }
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing set_campaign_state action.')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb


def _init_set_ad_group_source_settings(ad_group_source, settings_id, conf):
    msg = '_init_set_ad_group_source_settings started: ad_group_source.id: {}, settings: {}'.format(
        ad_group_source.id, str(conf)
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse(
                    'api.zwei_settings_callback',
                    kwargs={'action_id': action.id, 'settings_id': settings_id})
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
            action.save()

            return action
    except Exception as e:
        logger.exception('An exception occurred while initializing set_campaign_state action.')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb


def _init_fetch_status(ad_group_source, order):
    msg = '_init_fetch_status started: ad_group_source.id: {}'.format(
        ad_group_source.id
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )

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
            action.save()

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_campaign_status action.')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb


def _init_fetch_reports(ad_group_source, date, order):
    msg = '_init_fetch_reports started: ad_group_source.id: {}, date: {}'.format(
        ad_group_source.id,
        repr(date)
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )

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
                    'source_campaign_keys': [ad_group_source.source_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing get_reports action')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb


def _init_set_campaign_property(ad_group_source, prop, value, order):
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
        action.save()

        if existing_actions:
            for a in existing_actions:
                a.state = constants.ActionState.ABORTED
                a.save()

    except Exception as e:
        logger.exception('An exception occurred while initializing set_property action.')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb


def _init_create_campaign(ad_group_source, name):
    if ad_group_source.source_campaign_key:
        msg = 'Unable to create external campaign for AdGroupSource with existing connection'\
              'ad_group_source.id={ad_group_source_id}, name={name}'.format(
                  ad_group_source_id=ad_group_source.id,
                  name=name,
              )
        logger.error(msg)

        raise InsertCreateCampaignActionException(msg)

    msg = "_init_create_campaign started: ad_group_source.id: {}, name: {}".format(
        ad_group_source.id,
        name,
    )
    logger.info(msg)

    order = models.ActionLogOrder.objects.create(
        order_type=constants.ActionLogOrderType.CREATE_CAMPAIGN
    )

    action = models.ActionLog.objects.create(
        action=constants.Action.CREATE_CAMPAIGN,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
        order=order
    )

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

            if hasattr(ad_group_source.source, 'defaultsourcesettings'):
                params = ad_group_source.source.defaultsourcesettings.params
                if 'create_campaign' in params:
                    payload['args']['extra'].update(params['create_campaign'])

            tracking_code = ''
            if ad_group_settings:
                if ad_group_settings.tracking_code:
                    # Strip the first '?' as we don't want to send it as a part of query string
                    tracking_code = ad_group_settings.tracking_code.lstrip('?')

                payload['args']['extra'].update({
                    'target_devices': ad_group_settings.target_devices,
                    'target_regions': ad_group_settings.target_regions,
                })

            # Using OrderedDict because order should remain the same (only append additional tracking codes)
            tracking_code_dict = collections.OrderedDict(urlparse.parse_qsl(tracking_code))
            for k, v in ad_group_source.get_tracking_ids().items():
                if k not in tracking_code_dict:
                    tracking_code_dict[k] = v

            payload['args']['extra'].update({
                # Unquoting is necessary because we want to forward parameters as they were
                # entered, even if they contain characters such as '{', '}' or ' ' because
                # they should get handeled by supply source (urllib.urlencode() quotes by
                # default)
                'tracking_code': urllib.unquote(urllib.urlencode(tracking_code_dict)),
            })

            if campaign_settings:
                payload['args']['extra'].update({
                    'iab_category': campaign_settings.iab_category,
                })

            action.payload = payload
            action.save()

            return action

    except Exception as e:
        logger.exception('An exception occurred while initializing create_campaign action.')
        _handle_error(action, e)

        et, ei, tb = sys.exc_info()
        raise InsertActionException, ei, tb
