import json
import logging
import traceback
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction

from . import models
from . import constants
from . import zwei_actions

from dash import constants as dashconstants

logger = logging.getLogger(__name__)


def stop_ad_group(ad_group, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_stop_campaign(ad_group_network)


def fetch_ad_group_status(ad_group, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_fetch_status(ad_group_network)


def fetch_ad_group_reports(ad_group, date, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_fetch_reports(ad_group_network, date)


def set_ad_group_property(ad_group, network=None, prop=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_set_campaign_property(ad_group_network, prop)


def is_waiting(ad_group):
    actions = (constants.Action.SET_CAMPAIGN_STATE, constants.Action.SET_PROPERTY)
    states = (constants.ActionState.FAILED, constants.ActionState.WAITING)
    exists = models.ActionLog.objects.\
        filter(
            action__in=actions,
            state__in=states,
            ad_group_network__ad_group_id=ad_group.id
        ).\
        exists()

    return exists


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


def _init_stop_campaign(ad_group_network):
    msg = '_init_stop started: ad_group_network.id: {}'.format(ad_group_network.id)
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.SET_CAMPAIGN_STATE,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key,
                    'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

        zwei_actions.send(action)
    except Exception as e:
        _handle_error(action, e)


def _init_fetch_status(ad_group_network):
    msg = '_init_fetch_status started: ad_group_network.id: {}'.format(
        ad_group_network.id
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_id': ad_group_network.network_campaign_key
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

        zwei_actions.send(action)
    except Exception as e:
        _handle_error(action, e)


def _init_fetch_reports(ad_group_network, date):
    msg = '_init_fetch_reports started: ad_group_network.id: {}, date: {}'.format(
        ad_group_network.id,
        repr(date)
    )
    logger.info(msg)

    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group_network=ad_group_network,
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            payload = {
                'action': action.action,
                'network': ad_group_network.network.type,
                'credentials': ad_group_network.network_credentials.credentials,
                'args': {
                    'partner_campaign_ids': [ad_group_network.network_campaign_key],
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback,
            }

            action.payload = payload
            action.save()

        zwei_actions.send(action)
    except Exception as e:
        _handle_error(action, e)


def _init_set_campaign_property(ad_group_network, prop):
    models.ActionLog.objects.create(
        action=constants.Action.SET_PROPERTY,
        action_type=constants.ActionType.MANUAL,
        ad_group_network=ad_group_network,
        payload=json.dumps({
            'property': prop,
        })
    )
