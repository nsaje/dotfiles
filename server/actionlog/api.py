import logging
import traceback
import urlparse
import time

from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min

from . import models
from . import constants
from . import zwei_actions

from dash import constants as dashconstants
from dash import models as dashmodels

logger = logging.getLogger(__name__)


def init_fetch_all_order(dates):
    ad_groups = dashmodels.AdGroup.objects.all()

    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.FETCH_ALL
        )

        actionlogs = []
        for ad_group in ad_groups:
            actionlogs += fetch_ad_group_status(ad_group, order=order, commit=False)

            for date in dates:
                actionlogs += fetch_ad_group_reports(ad_group, date, order=order, commit=False)

    zwei_actions.send_multiple(actionlogs)


def init_fetch_reports_order(dates, ad_groups=None):
    if ad_groups is None:
        ad_groups = dashmodels.AdGroup.objects.all()

    if not ad_groups:
        return

    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.FETCH_REPORTS
        )

        actionlogs = []
        for ad_group in ad_groups:
            for date in dates:
                actionlogs += fetch_ad_group_reports(ad_group, date, order=order, commit=False)

    zwei_actions.send_multiple(actionlogs)


def init_fetch_status_order(ad_groups=None):
    if ad_groups is None:
        ad_groups = dashmodels.AdGroup.objects.all()

    if not ad_groups:
        return

    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.FETCH_STATUS
        )

        actionlogs = []
        for ad_group in ad_groups:
            actionlogs += fetch_ad_group_status(ad_group, order=order, commit=False)

    zwei_actions.send_multiple(actionlogs)


def init_stop_ad_group_order(ad_group, network=None):
    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.STOP_ALL
        )
        actionlogs = stop_ad_group(ad_group, network, order, commit=False)

    zwei_actions.send_multiple(actionlogs)


def init_set_ad_group_property_order(ad_group, network=None):
    with transaction.atomic():
        order = models.ActionLogOrder.objects.create(
            order_type=constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
        )
        set_ad_group_property(ad_group, network, order, commit=False)


def stop_ad_group(ad_group, network=None, order=None, commit=True):
    ad_group_networks = _get_ad_group_networks(ad_group, network)

    actionlogs = []
    for ad_group_network in ad_group_networks:
        actionlogs.append(_init_stop_campaign(ad_group_network, order))

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def fetch_ad_group_status(ad_group, network=None, order=None, commit=True):
    ad_group_networks = _get_ad_group_networks(ad_group, network)

    actionlogs = []
    for ad_group_network in ad_group_networks:
        actionlogs.append(_init_fetch_status(ad_group_network, order))

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def fetch_ad_group_reports(ad_group, date, network=None, order=None, commit=True):
    ad_group_networks = _get_ad_group_networks(ad_group, network)

    actionlogs = []
    for ad_group_network in ad_group_networks:
        actionlogs.append(_init_fetch_reports(ad_group_network, date, order))

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def set_ad_group_property(ad_group, network=None, prop=None, value=None, order=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_set_campaign_property(ad_group_network, prop, value, order)


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
            ad_group_network__ad_group_id=ad_group.id,
            order__isnull=False
        ).latest('created_dt')
    except ObjectDoesNotExist:
        return False
    # check whether there are unsuccessful actions in this order
    is_fail_in_latest_group = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.FAILED,
            ad_group_network__ad_group_id=ad_group.id,
            order=latest_action.order
        ).\
        exists()

    is_any_waiting_action = models.ActionLog.objects.\
        filter(
            action__in=action_types,
            state=constants.ActionState.WAITING,
            ad_group_network__ad_group_id=ad_group.id,
        ).\
        exists()

    return is_fail_in_latest_group or is_any_waiting_action


def is_fetch_all_data_recent(ad_group=None):
    check_from_hour = datetime.utcnow() - timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS)

    recent_fetch_all_orders = models.ActionLogOrder.objects.filter(
        order_type=constants.ActionLogOrderType.FETCH_ALL,
        created_dt__gte=check_from_hour
    ).order_by('-created_dt')

    if ad_group:
        recent_fetch_all_orders = recent_fetch_all_orders.filter(
            actionlog__ad_group_network__ad_group=ad_group)

    for order in recent_fetch_all_orders:
        if _is_fetch_all_order_successful(order):
            return True

    return False


def get_last_successful_fetch_all_order(ad_group=None):
    q = '''
        SELECT alo.*
        FROM actionlog_actionlogorder AS alo
        INNER JOIN actionlog_actionlog AS al ON alo.id=al.order_id
        INNER JOIN dash_adgroupnetwork AS agn ON al.ad_group_network_id=agn.id
        INNER JOIN dash_network AS n ON agn.network_id=n.id
        WHERE alo.order_type=%s AND n.maintenance=False AND (1=%s OR agn.ad_group_id=%s)
        GROUP BY alo.id
        HAVING EVERY(al.state=%s)
        ORDER BY alo.created_dt DESC
        LIMIT 1
    '''

    if ad_group:
        params = [
            constants.ActionLogOrderType.FETCH_ALL,
            0,
            ad_group.pk,
            constants.ActionState.SUCCESS
        ]
    else:
        params = [
            constants.ActionLogOrderType.FETCH_ALL,
            1,
            None,
            constants.ActionState.SUCCESS
        ]

    orders = models.ActionLogOrder.objects.raw(q, params)
    if list(orders):
        order = orders[0]
    else:
        order = None

    return order


def get_last_succesfull_fetch_all_networks_dates(ad_group):
    q = '''
        SELECT t.network_id, MAX(t.created_dt)
        FROM (
            SELECT agn.network_id, alo.created_dt
            FROM actionlog_actionlog AS al
            INNER JOIN actionlog_actionlogorder AS alo ON al.order_id=alo.id
            INNER JOIN dash_adgroupnetwork AS agn ON al.ad_group_network_id=agn.id
            INNER JOIN dash_network AS n ON agn.network_id=n.id
            WHERE alo.order_type=%s AND n.maintenance=False AND (1=%s OR agn.ad_group_id=%s)
            GROUP BY agn.network_id, alo.created_dt
            HAVING EVERY(al.state=%s)
        ) AS t
        GROUP BY t.network_id;
    '''

    if ad_group:
        params = [
            constants.ActionLogOrderType.FETCH_ALL,
            0,
            ad_group.pk,
            constants.ActionState.SUCCESS
        ]
    else:
        params = [
            constants.ActionLogOrderType.FETCH_ALL,
            1,
            None,
            constants.ActionState.SUCCESS
        ]

    result = {}
    with connection.cursor() as c:
        c.execute(q, params)
        result = dict(c.fetchall())

    return result


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


def _is_fetch_all_order_successful(order):
    result = order.actionlog_set.\
        exclude(state=constants.ActionState.SUCCESS).\
        filter(ad_group_network__network__maintenance=False).\
        exists()

    return not result


def _handle_error(action, e):
    msg = traceback.format_exc(e)

    logger.error(msg)

    action.state = constants.ActionState.FAILED
    action.message = msg
    action.save()


def _get_ad_group_networks(ad_group, network):
    if not network:
        return ad_group.adgroupnetwork_set.all()

    return ad_group.adgroupnetwork_set.filter(network=network)


def _init_stop_campaign(ad_group_network, order):
    msg = '_init_stop started: ad_group_network.id: {}'.format(ad_group_network.id)
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
        order=order
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_network.network_credentials and
                    ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                    'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

    except Exception as e:
        _handle_error(action, e)

    return action


def _init_fetch_status(ad_group_network, order):
    msg = '_init_fetch_status started: ad_group_network.id: {}'.format(
        ad_group_network.id
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
        order=order
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_network.network_credentials and
                    ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

    except Exception as e:
        _handle_error(action, e)

    return action


def _init_fetch_reports(ad_group_network, date, order):
    msg = '_init_fetch_reports started: ad_group_network.id: {}, date: {}'.format(
        ad_group_network.id,
        repr(date)
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
        order=order
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'expiration_dt': action.expiration_dt,
                'credentials':
                    ad_group_network.network_credentials and
                    ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_ids': [ad_group_network.network_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

    except Exception as e:
        _handle_error(action, e)

    return action


def _init_set_campaign_property(ad_group_network, prop, value, order):
    msg = "_init_set_campaign_property started:"
    "ad_group_network.id: {}, prop: {}, value: {}, order.id: {}".format(
        ad_group_network.id,
        prop,
        value,
        order.id if order else order
    )
    logger.info(msg)

    try:
        existing_actions = models.ActionLog.objects.filter(
            ad_group_network=ad_group_network,
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
            ad_group_network=ad_group_network,
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
