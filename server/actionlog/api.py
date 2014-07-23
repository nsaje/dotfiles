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


def fetch_ad_group_status(ad_group, source=None, order=None, commit=True):
    ad_group_sources = _get_ad_group_sources(ad_group, source)

    actionlogs = []
    for ad_group_source in ad_group_sources:
        actionlogs.append(_init_fetch_status(ad_group_source, order))

    if commit:
        zwei_actions.send_multiple(actionlogs)

    return actionlogs


def fetch_ad_group_reports(ad_group, date, source=None, order=None, commit=True):
    ad_group_sources = _get_ad_group_sources(ad_group, source)

    actionlogs = []
    for ad_group_source in ad_group_sources:
        actionlogs.append(_init_fetch_reports(ad_group_source, date, order))

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


def is_fetch_all_data_recent(ad_group=None):
    check_from_hour = datetime.utcnow() - timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS)

    recent_fetch_all_orders = models.ActionLogOrder.objects.filter(
        order_type=constants.ActionLogOrderType.FETCH_ALL,
        created_dt__gte=check_from_hour
    ).order_by('-created_dt')

    if ad_group:
        recent_fetch_all_orders = recent_fetch_all_orders.filter(
            actionlog__ad_group_source__ad_group=ad_group)

    for order in recent_fetch_all_orders:
        if _is_fetch_all_order_successful(order):
            return True

    return False


def get_last_successful_fetch_all_order(ad_group=None):
    q = '''
        SELECT alo.*
        FROM actionlog_actionlogorder AS alo
        INNER JOIN actionlog_actionlog AS al ON alo.id=al.order_id
        INNER JOIN dash_adgroupsource AS agn ON al.ad_group_source_id=agn.id
        INNER JOIN dash_source AS n ON agn.source_id=n.id
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


def get_last_succesfull_fetch_all_sources_dates(ad_group):
    q = '''
        SELECT t.source_id, MAX(t.created_dt)
        FROM (
            SELECT agn.source_id, alo.created_dt
            FROM actionlog_actionlog AS al
            INNER JOIN actionlog_actionlogorder AS alo ON al.order_id=alo.id
            INNER JOIN dash_adgroupsource AS agn ON al.ad_group_source_id=agn.id
            INNER JOIN dash_source AS n ON agn.source_id=n.id
            WHERE alo.order_type=%s AND n.maintenance=False AND (1=%s OR agn.ad_group_id=%s)
            GROUP BY agn.source_id, alo.created_dt
            HAVING EVERY(al.state=%s)
        ) AS t
        GROUP BY t.source_id;
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


def is_sync_in_progress(ad_group):
    '''
    sync is in progress if one of the following is true:
    - a get reports action for this ad_group is in 'waiting' state
    - a fetch status action for this ad_group is in 'waiting' state
    '''

    n_waiting_actions = models.ActionLog.objects.filter(
        ad_group_source__ad_group=ad_group,
        state=constants.ActionState.WAITING,
        action_type=constants.ActionType.AUTOMATIC,
        action__in=(constants.Action.FETCH_REPORTS,
            constants.Action.FETCH_CAMPAIGN_STATUS)
    ).count()

    return n_waiting_actions > 0


def _is_fetch_all_order_successful(order):
    result = order.actionlog_set.\
        exclude(state=constants.ActionState.SUCCESS).\
        filter(ad_group_source__source__maintenance=False).\
        exists()

    return not result


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
