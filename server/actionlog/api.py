import json

from django.core.urlresolvers import reverse

from . import models
from . import constants
from . import zwei_actions


def stop_ad_group(ad_group, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_stop_campaign(ad_group_network)


def fetch_ad_group_status(ad_group, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_fetch_status(ad_group_network)


def fetch_ad_group_reports(ad_group, network=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_fetch_reports(ad_group_network)


def set_ad_group_property(ad_group, network=None, prop=None):
    ad_group_networks = _get_ad_group_networks(ad_group, network)
    for ad_group_network in ad_group_networks:
        _init_set_campaign_property(ad_group_network, prop)


def _get_ad_group_networks(ad_group, network):
    if not network:
        return ad_group.adgroupnetwork_set.all()

    return ad_group.adgroupnetwork_set.filter(network=network)


def _init_stop_campaign(ad_group_network):
    network_campaign_key = json.loads(ad_group_network.network_campaign_key)
    action = models.ActionLog.objects.create(
        action=constants.Action.STOP_CAMPAIGN,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group=ad_group_network.ad_group,
        network=ad_group_network.network,
    )
    payload = json.dumps({
        'network': ad_group_network.network.slug,
        'action': action.action,
        'network_campaign_key': network_campaign_key,
        'callback': reverse(
            'actions.zwei_callback',
            kwargs={'action_id': action.id},
        ),
    })

    action.payload = payload
    action.save()

    zwei_actions.send(action)


def _init_fetch_status(ad_group_network):
    network_campaign_key = json.loads(ad_group_network.network_campaign_key)
    action = models.ActionLog.objects.create(
        action=constants.Action.GET_CAMPAIGN_STATUS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group=ad_group_network.ad_group,
        network=ad_group_network.network,
    )
    payload = json.dumps({
        'action': action.action,
        'network': ad_group_network.network.slug,
        'network_campaign_key': network_campaign_key,
        'callback': reverse(
            'actions.zwei_callback',
            kwargs={'action_id': action.id},
        ),
    })

    action.payload = payload
    action.save()

    zwei_actions.send(action)


def _init_fetch_reports(ad_group_network, date):
    network_campaign_key = json.loads(ad_group_network.network_campaign_key)
    action = models.ActionLog.objects.create(
        action=constants.Action.FETCH_REPORTS,
        action_type=constants.ActionType.AUTOMATIC,
        ad_group=ad_group_network.ad_group,
        network=ad_group_network.network,
    )
    payload = json.dumps({
        'action': action.action,
        'network': ad_group_network.slug,
        'network_campaign_key': network_campaign_key,
        'date': date,
        'callback': reverse(
            'actions.zwei_callback',
            kwargs={'action_id': action.id},
        ),
    })

    action.payload = payload
    action.save()

    zwei_actions.send(action)


def _init_set_campaign_property(ad_group_network, prop):
    models.ActionLog.objects.create(
        action=constants.Action.FETCH_CAMPAIGN_STATUS,
        action_type=constants.ActionType.MANUAL,
        ad_group=ad_group_network.ad_group,
        network=ad_group_network.network,
        payload=json.dumps({
            'property': prop,
        })
    )
