from django.db import transaction

import core.models
import dash.constants
from utils import dates_helper
from utils import zlogging

from ..currency_exchange_rate import CurrencyExchangeRate
from . import ecb

logger = zlogging.getLogger(__name__)


class MissingExchangeRateMappingException(Exception):
    pass


class ProgrammingError(Exception):
    pass


def update_exchange_rates(currencies=None):
    if not currencies:
        currencies = dash.constants.Currency.get_all()

    for currency in currencies:
        if currency == dash.constants.Currency.USD:
            continue

        logger.info("Updating for currency", currency=currency)
        try:
            rate = _get_exchange_rate(currency)
        except MissingExchangeRateMappingException:
            logger.warning("Missing exchange rate mapping for currency", currency=currency)

        _update_exchange_rate(currency, rate)
        _update_accounts(currency)


def _get_exchange_rate(currency):
    try:
        return ecb.try_get_exchange_rate(currency)
    except ecb.NotSupportedByECBException:
        pass
    raise MissingExchangeRateMappingException()


def _update_exchange_rate(currency, rate):
    CurrencyExchangeRate.objects.create(date=dates_helper.local_today(), currency=currency, exchange_rate=rate)


def _update_accounts(currency):
    currency_accounts = core.models.Account.objects.filter(currency=currency)
    for account in currency_accounts:
        _update_account(account)


@transaction.atomic
def _update_account(account):
    for campaign in account.campaign_set.all():
        _recalculate_goals(campaign)
        _recalculate_ad_group_amounts(campaign)


def _recalculate_goals(campaign):
    for goal in campaign.campaigngoal_set.all():
        goal.add_local_value(None, goal.get_current_value().local_value, skip_history=True)


def _recalculate_ad_group_amounts(campaign):
    for ad_group in campaign.adgroup_set.all():
        _recalculate_ad_group_settings_amounts(ad_group)
        _recalculate_ad_group_sources_amounts(ad_group)


def _recalculate_ad_group_settings_amounts(ad_group):
    fields = ["local_" + field for field in ad_group.settings.multicurrency_fields]
    updates = {
        field: getattr(ad_group.settings, field) for field in fields if getattr(ad_group.settings, field) is not None
    }
    changes = ad_group.settings.update(
        None, skip_validation=True, skip_automation=True, skip_permission_check=True, **updates
    )
    _sanity_check(changes, ad_group.settings.multicurrency_fields)


def _recalculate_ad_group_sources_amounts(ad_group):
    for ad_group_source in ad_group.adgroupsource_set.all():
        _recalculate_ad_group_source_settings_amounts(ad_group_source)


def _recalculate_ad_group_source_settings_amounts(ad_group_source):
    fields = ["local_" + field for field in ad_group_source.settings.multicurrency_fields]
    updates = {
        field: getattr(ad_group_source.settings, field)
        for field in fields
        if getattr(ad_group_source.settings, field) is not None
    }
    changes = ad_group_source.settings.update(
        None, skip_automation=True, skip_validation=True, skip_notification=True, **updates
    )
    _sanity_check(changes, ad_group_source.settings.multicurrency_fields)


def _sanity_check(changes, multicurrency_fields):
    changes.pop("cpc_cc", None)
    changes.pop("local_cpc_cc", None)
    changes.pop("max_cpm", None)
    changes.pop("local_max_cpm", None)
    if any(field not in multicurrency_fields for field in changes):
        invalid_field_set = set(changes) - set(multicurrency_fields)
        logger.error("Attempted to change non-multicurrency fields!", fields=invalid_field_set)
        raise ProgrammingError("Attempted to change non-multicurrency fields: %s" % invalid_field_set)
