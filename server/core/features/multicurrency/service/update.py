import concurrent.futures

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
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        executor.map(_update_account, currency_accounts.all())


@transaction.atomic
def _update_account(account):
    for campaign in account.campaign_set.iterator(100):
        campaign.settings.recalculate_multicurrency_values()
        _recalculate_ad_group_amounts(campaign)


def _recalculate_ad_group_amounts(campaign):
    for ad_group in campaign.adgroup_set.iterator(200):
        changes = ad_group.settings.recalculate_multicurrency_values()
        _sanity_check(changes, ad_group.settings.multicurrency_fields, ad_group_id=ad_group.id)
        _recalculate_ad_group_sources_amounts(ad_group)


def _recalculate_ad_group_sources_amounts(ad_group):
    for ad_group_source in ad_group.adgroupsource_set.all():
        changes = ad_group_source.settings.recalculate_multicurrency_values()
        _sanity_check(
            changes,
            ad_group_source.settings.multicurrency_fields,
            ad_group_id=ad_group.id,
            ad_group_source_id=ad_group_source.id,
        )


def _sanity_check(changes, multicurrency_fields, ad_group_id=None, ad_group_source_id=None):
    if not changes:
        return
    changes.pop("cpc_cc", None)
    changes.pop("local_cpc_cc", None)
    changes.pop("max_cpm", None)
    changes.pop("local_max_cpm", None)
    # TODO temporary fix due to prodops hacks on arhived ad groups
    changes.pop("delivery_type", None)
    # TODO: RTAP: daily_budget updated because of b1_sources_group_enabled=True
    # and b1_sources_group_daily_budget != daily_budget
    # remove after migration to RTA completed
    changes.pop("local_daily_budget", None)
    if any(field not in multicurrency_fields for field in changes):
        invalid_field_set = set(changes) - set(multicurrency_fields)
        logger.error(
            "Attempted to change non-multicurrency fields!",
            fields=invalid_field_set,
            ad_group_id=ad_group_id,
            ad_group_source_id=ad_group_source_id,
        )
        raise ProgrammingError("Attempted to change non-multicurrency fields: %s" % invalid_field_set)
