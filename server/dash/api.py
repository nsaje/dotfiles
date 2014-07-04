import decimal
import logging

from django.db import transaction

import actionlog.api
import actionlog.models
import actionlog.constants

from dash import models
from dash import constants

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

    try:
        current_settings = ad_group_network.settings.latest()
    except models.AdGroupNetworkSettings.DoesNotExist:
        current_settings = None

    if current_settings is not None and (
        current_settings.state == new_settings['state'] and
        current_settings.cpc_cc == new_settings['cpc_cc'] and
        current_settings.daily_budget_cc == new_settings['daily_budget_cc']
    ):
        logger.info('Campaign settings for ad_group_network %s unmodified', ad_group_network)
        return

    ad_group_network.settings.create(**new_settings)


def order_ad_group_settings_update(ad_group, current_settings, new_settings):
    changes = _get_setting_changes(current_settings, new_settings)

    if not changes:
        return

    order = actionlog.models.ActionLogOrder.objects.create(
        order_type=actionlog.constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE,
    )

    for field_name, field_value in changes.iteritems():
        if field_name == 'state' and field_value == constants.AdGroupSettingsState.INACTIVE:
            actionlog.api.stop_ad_group(ad_group, order=order)
        else:
            actionlog.api.set_ad_group_property(ad_group, prop=field_name, value=field_value, order=order)


def _get_setting_changes(current_settings, new_settings):
    changes = {}

    current_settings_dict = current_settings.get_settings_dict()
    new_settings_dict = new_settings.get_settings_dict()

    for field_name in models.AdGroupSettings.get_settings_fields():
        if current_settings_dict[field_name] != new_settings_dict[field_name]:
            changes[field_name] = new_settings_dict[field_name]

    return changes
