import logging
import traceback
import urlparse
import time

from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min

from . import models
from . import constants
from . import zwei_actions

from dash import constants as dashconstants

logger = logging.getLogger(__name__)


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
        actionlogs.append(_init_stop_campaign(ad_group_source, order))

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def set_ad_group_property(ad_group, source=None, prop=None, value=None, order=None):
    ad_group_sources = _get_ad_group_sources(ad_group, source)
    for ad_group_source in ad_group_sources:
        _init_set_campaign_property(ad_group_source, prop, value, order)


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


def is_waiting_for_set_actions(ad_group):
    action_types = (constants.Action.SET_CAMPAIGN_STATE, constants.Action.SET_PROPERTY)
    # get latest action for ad_group where order != null
    try:
        latest_action = models.ActionLog.objects.filter(
            action__in=action_types,
            ad_group_source__ad_group_id=ad_group.id,
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        return False
    # check whether there are unsuccessful actions in this order
    is_fail_in_latest_group = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.FAILED,
            ad_group_source__ad_group_id=ad_group.id,
            order=latest_action.order
        ).\
        exists()

    is_any_waiting_action = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.WAITING,
            ad_group_source__ad_group_id=ad_group.id,
        ).\
        exists()

    return is_fail_in_latest_group or is_any_waiting_action


def count_waiting_manual_actions():
    result = -1
    try:
        result = models.ActionLog.objects.filter(
            action_type=constants.ActionType.MANUAL,
            state=constants.ActionState.WAITING
        ).count()
    except Exception as e:
        msg = traceback.format_exc(e)
        logger.error(msg)
    return result


def count_failed_manual_actions():
    result = -1
    try:
        result = models.ActionLog.objects.filter(
            action_type=constants.ActionType.MANUAL,
            state=constants.ActionState.FAILED
        ).count()
    except Exception as e:
        msg = traceback.format_exc(e)
        logger.error(msg)
    return result


def age_oldest_waiting_action():
    n_hours = -1
    try:
        result = models.ActionLog.objects.filter(
            action_type=constants.ActionType.MANUAL,
            state=constants.ActionState.WAITING
        ).aggregate(Min('created_dt'))

        if result.get('created_dt__min') is None:
            n_hours = 0
        else:
            t_now = time.mktime(datetime.utcnow().timetuple())
            t_created = time.mktime(result['created_dt__min'].timetuple())
            n_hours = int((t_now - t_created) / 3600)
    except Exception as e:
        msg = traceback.format_exc(e)
        logger.error(msg)
    return n_hours


def _handle_error(action, e):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


def _get_ad_group_sources(ad_group, source):
    if not source:
        return ad_group.adgroupsource_set.all()

    return ad_group.adgroupsource_set.filter(source=source)


def _init_stop_campaign(ad_group_source, order):
    msg = '_init_stop started: ad_group_source.id: {}'.format(ad_group_source.id)
    logger.info(msg)

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
                'source': ad_group_source.source.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_source.source_credentials and
                    ad_group_source.source_credentials.credentials,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'state': dashconstants.AdGroupSourceSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

    except Exception as e:
        _handle_error(action, e)

    return action


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
                'source': ad_group_source.source.type,
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

    except Exception as e:
        _handle_error(action, e)

    return action


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
                'source': ad_group_source.source.type,
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

    except Exception as e:
        _handle_error(action, e)

    return action


def _init_set_campaign_property(ad_group_source, prop, value, order):
    msg = "_init_set_campaign_property started:"
    "ad_group_source.id: {}, prop: {}, value: {}, order.id: {}".format(
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
        _handle_error(action, e)
