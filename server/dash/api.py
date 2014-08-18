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
def campaign_status_upsert(ad_group_source, data):
    '''
    Creates new AdGroupSourceSettings if settings are modified.
    '''

    new_settings = {
        'state': data.get('state'),
        'cpc_cc': cc_to_decimal(data.get('cpc_cc')),
        'daily_budget_cc': cc_to_decimal(data.get('daily_budget_cc')),
    }

    try:
        current_settings = ad_group_source.settings.latest()
    except models.AdGroupSourceSettings.DoesNotExist:
        current_settings = None

    if current_settings is not None and (
        current_settings.state == new_settings['state'] and
        current_settings.cpc_cc == new_settings['cpc_cc'] and
        current_settings.daily_budget_cc == new_settings['daily_budget_cc']
    ):
        logger.info('Campaign settings for ad_group_source %s unmodified', ad_group_source)
        return

    ad_group_source.settings.create(**new_settings)


@transaction.atomic
def update_campaign_state(ad_group_source, state):
    '''
    Creates new AdGroupSourceSettings if settings are modified.
    '''
    try:
        current_settings = ad_group_source.settings.latest()
    except models.AdGroupSourceSettings.DoesNotExist:
        current_settings = None

    if current_settings is not None:
        if state == current_settings.state:
            logger.info('Campaign settings for ad_group_source %s unmodified', ad_group_source)
            return
        else:
            current_settings.pk = None  # create a new settings object as a copy of the old one
            current_settings.state = state
            current_settings.save()


def order_ad_group_settings_update(ad_group, current_settings, new_settings):
    changes = current_settings.get_setting_changes(new_settings)

    if not changes:
        return

    for field_name, field_value in changes.iteritems():
        if field_name == 'state' and field_value == constants.AdGroupSettingsState.INACTIVE:
            actionlog.api.init_stop_ad_group_order(ad_group)
        else:
            actionlog.api.init_set_ad_group_property_order(ad_group, prop=field_name, value=field_value)
