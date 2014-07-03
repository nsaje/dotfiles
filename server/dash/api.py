import decimal
import logging

from django.db import transaction

from dash.models import AdGroupNetworkSettings

logger = logging.getLogger(__name__)


def cc_to_decimal(val_cc):
    if val_cc is None:
        return None
    return decimal.Decimal(val_cc) / 10000


@transaction.atomic
def campaign_status_upsert(ad_group_network, data):
    '''
    Creates new AdGroupNetworkSettings if settings are modified.
    '''

    new_settings = {
        'state': data.get('state'),
        'cpc_cc': cc_to_decimal(data.get('cpc_cc')),
        'daily_budget_cc': cc_to_decimal(data.get('daily_budget_cc')),
    }

    for key, val in new_settings.iteritems():
        if val is None:
            raise AttributeError('Missing network settings data for %s', key)

    try:
        current_settings = ad_group_network.settings.latest()
    except AdGroupNetworkSettings.DoesNotExist:
        current_settings = None

    if current_settings is not None and (
        current_settings.state == new_settings['state'] and
        current_settings.cpc_cc == new_settings['cpc_cc'] and
        current_settings.daily_budget_cc == new_settings['daily_budget_cc']
    ):
        logger.info('Campaign settings for ad_group_network %s unmodified', ad_group_network)
        return

    ad_group_network.settings.create(**new_settings)
