import decimal
import logging

from django.db import transaction

from dash.models import AdGroupNetworkSettings

logger = logging.getLogger(__name__)


def cc_to_decimal(val_cc):
    return decimal.Decimal(val_cc) / 10000


@transaction.atomic
def campaign_status_upsert(ad_group_network, data):
    '''
    Creates new AdGroupNetworkSettings if settings are modified.
    '''

    new_state = data['state']
    new_cpc = cc_to_decimal(data['cpc_cc'])
    new_daily_budget = cc_to_decimal(data['daily_budget_cc'])

    try:
        current_settings = ad_group_network.settings.latest()
    except AdGroupNetworkSettings.DoesNotExist:
        current_settings = None

    if current_settings is not None and (
        current_settings.state == new_state and
        current_settings.cpc_cc == new_cpc and
        current_settings.daily_budget_cc == new_daily_budget
    ):
        logger.info('Campaign settings for ad_group_network %s unmodified', ad_group_network)
        return

    ad_group_network.settings.create(
        state=new_state,
        cpc_cc=new_cpc,
        daily_budget_cc=new_daily_budget,
    )
