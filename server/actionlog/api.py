import binascii
import json
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction

from . import models
from . import constants
from zweiapi import zwei_actions

from dash import constants as dashconstants
from utils import encryption_helpers


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


def _get_ad_group_networks(ad_group, network):
    if not network:
        return ad_group.adgroupnetwork_set.all()

    return ad_group.adgroupnetwork_set.filter(network=network)


def _init_stop_campaign(ad_group_network):
    with transaction.atomic():
        action = models.ActionLog.objects.create(
            action=constants.Action.SET_CAMPAIGN_STATE,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_network=ad_group_network,
        )

        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        credentials = json.loads(encryption_helpers.aes_decrypt(
            binascii.a2b_base64(
                ad_group_network.network_credentials.credentials
            ),
            settings.CREDENTIALS_ENCRYPTION_KEY
        ))
        payload = json.dumps({
            'action': action.action,
            'network': ad_group_network.network.type,
            'credentials': credentials,
            'args': {
                'partner_campaign_id': ad_group_network.network_campaign_key,
                'state': dashconstants.AdGroupNetworkSettingsState.INACTIVE,
            },
            'callback_url': callback,
        })

        action.payload = payload
        action.save()

    zwei_actions.send(action)


def _init_fetch_status(ad_group_network):
    with transaction.atomic():
        action = models.ActionLog.objects.create(
            action=constants.Action.FETCH_CAMPAIGN_STATUS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_network=ad_group_network,
        )

        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        credentials = json.loads(encryption_helpers.aes_decrypt(
            binascii.a2b_base64(
                ad_group_network.network_credentials.credentials
            ),
            settings.CREDENTIALS_ENCRYPTION_KEY
        ))
        payload = json.dumps({
            'action': action.action,
            'network': ad_group_network.network.type,
            'credentials': credentials,
            'args': {
                'partner_campaign_id': ad_group_network.network_campaign_key
            },
            'callback_url': callback,
        })

        action.payload = payload
        action.save()

    zwei_actions.send(action)


def _init_fetch_reports(ad_group_network, date):
    with transaction.atomic():
        action = models.ActionLog.objects.create(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_network=ad_group_network,
        )

        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        credentials = json.loads(encryption_helpers.aes_decrypt(
            binascii.a2b_base64(
                ad_group_network.network_credentials.credentials
            ),
            settings.CREDENTIALS_ENCRYPTION_KEY
        ))
        payload = json.dumps({
            'action': action.action,
            'network': ad_group_network.network.type,
            'credentials': credentials,
            'args': {
                'partner_campaign_ids': [ad_group_network.network_campaign_key],
                'date': date.strftime('%Y-%m-%d'),
            },
            'callback_url': callback,
        })

        action.payload = payload
        action.save()

    zwei_actions.send(action)


def _init_set_campaign_property(ad_group_network, prop):
    models.ActionLog.objects.create(
        action=constants.Action.SET_PROPERTY,
        action_type=constants.ActionType.MANUAL,
        ad_group_network=ad_group_network,
        payload=json.dumps({
            'property': prop,
        })
    )
