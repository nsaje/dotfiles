import decimal
from collections import namedtuple

import core.features.bcm
import core.features.multicurrency
import core.models
import realtimeapi.api

EntityIds = namedtuple("EntityIds", ["account_id", "campaign_id"])


class InvalidBreakdown(Exception):
    pass


def groupby(
    *, breakdown=None, marker=None, limit=100, account_id=None, campaign_id=None, ad_group_id=None, content_ad_id=None
):
    rows = realtimeapi.api.groupby(
        breakdown=breakdown,
        marker=marker,
        limit=limit,
        account_id=account_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        content_ad_id=content_ad_id,
    )
    return _augment_rows(breakdown, campaign_id, ad_group_id, content_ad_id, rows)


def topn(*, breakdown, order, limit=100, campaign_id=None, ad_group_id=None, content_ad_id=None):
    assert campaign_id or ad_group_id or content_ad_id
    rows = realtimeapi.api.topn(
        breakdown=breakdown,
        order=order,
        limit=limit,
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        content_ad_id=content_ad_id,
    )
    return _augment_rows(breakdown, campaign_id, ad_group_id, content_ad_id, rows)


def _augment_rows(breakdown, campaign_id, ad_group_id, content_ad_id, rows):
    entity_lookup_dict = _prepare_entity_lookup_dict(breakdown, campaign_id, ad_group_id, content_ad_id, rows)
    bcm_factors = _prepare_bcm_factors(entity_lookup_dict)
    currency_exchange_rates = _prepare_currency_exchange_rates(entity_lookup_dict)
    return _apply(
        breakdown,
        campaign_id,
        ad_group_id,
        content_ad_id,
        bcm_factors,
        currency_exchange_rates,
        entity_lookup_dict,
        rows,
    )


def _prepare_bcm_factors(entity_lookup_dict):
    campaign_ids = [entities.campaign_id for entities in entity_lookup_dict.values()]
    campaigns_qs = core.models.Campaign.objects.filter(id__in=campaign_ids)
    return {campaign.id: campaign.get_todays_fees_and_margin() for campaign in campaigns_qs}


def _prepare_currency_exchange_rates(entity_lookup_dict):
    account_ids = [entities.account_id for entities in entity_lookup_dict.values()]
    accounts_qs = core.models.Account.objects.filter(id__in=account_ids).only("id", "currency")
    currencies = set(account.currency for account in accounts_qs)
    currency_exchange_rates = {
        currency: core.features.multicurrency.get_current_exchange_rate(currency) for currency in currencies
    }
    return {account.id: currency_exchange_rates[account.currency] for account in accounts_qs}


def _apply(
    breakdown, campaign_id, ad_group_id, content_ad_id, bcm_factors, currency_exchange_rates, entity_lookup_dict, rows
):
    for row in rows:
        entity_ids = _get_entity_ids_for_row(
            breakdown, campaign_id, ad_group_id, content_ad_id, entity_lookup_dict, row
        )
        _apply_fees_and_margin(bcm_factors, entity_ids.campaign_id, row)
        _apply_currency_exchange_rate(currency_exchange_rates, entity_ids.account_id, row)
        _add_calculated_columns(row)
    return rows


def _apply_fees_and_margin(bcm_factors, campaign_id, row):
    service_fee, license_fee, margin = bcm_factors[campaign_id]
    row["spend"] = core.features.bcm.calculations.apply_fees_and_margin(
        decimal.Decimal(row["spend"]), service_fee, license_fee, margin
    )


def _apply_currency_exchange_rate(currency_exchange_rates, account_id, row):
    currency_exchange_rate = currency_exchange_rates[account_id]
    row["spend"] *= currency_exchange_rate


def _add_calculated_columns(row):
    row["ctr"] = row["clicks"] / row["impressions"] if row["impressions"] else None
    row["cpc"] = row["spend"] / row["clicks"] if row["clicks"] else None
    row["cpm"] = (row["spend"] / row["impressions"]) * 1000 if row["impressions"] else None


def _get_entity_ids_for_row(breakdown, campaign_id, ad_group_id, content_ad_id, entity_lookup_dict, row):
    if campaign_id:
        return entity_lookup_dict[campaign_id]
    elif ad_group_id:
        return entity_lookup_dict[ad_group_id]
    elif content_ad_id:
        return entity_lookup_dict[content_ad_id]
    elif "campaign_id" in breakdown:
        row_campaign_id = row["campaign_id"]
        return entity_lookup_dict[row_campaign_id]
    elif "ad_group_id" in breakdown:
        row_ad_group_id = row["ad_group_id"]
        return entity_lookup_dict[row_ad_group_id]
    elif "content_ad_id" in breakdown:
        row_content_ad_id = row["content_ad_id"]
        return entity_lookup_dict[row_content_ad_id]
    raise InvalidBreakdown("Invalid filter/breakdown")


def _prepare_entity_lookup_dict(breakdown, campaign_id, ad_group_id, content_ad_id, rows):
    if campaign_id:
        campaign = core.models.Campaign.objects.only("id", "account_id").get(id=campaign_id)
        return {str(campaign_id): EntityIds(campaign.account_id, campaign.id)}
    elif ad_group_id:
        ad_group = core.models.AdGroup.objects.only("id", "campaign_id", "campaign__account_id").get(id=ad_group_id)
        return {str(ad_group.id): EntityIds(ad_group.campaign.account_id, ad_group.campaign_id)}
    elif content_ad_id:
        content_ad = core.models.ContentAd.objects.filter(id=content_ad_id).only("id", "ad_group__campaign_id").get()
        return {str(content_ad.id): EntityIds(content_ad.ad_group.campaign.account_id, content_ad.ad_group.campaign_id)}
    elif "campaign_id" in breakdown:
        campaign_ids = [row["campaign_id"] for row in rows]
        campaigns = core.models.Campaign.objects.filter(id__in=campaign_ids).only("id", "account_id")
        return {str(campaign.id): EntityIds(campaign.account_id, campaign.id) for campaign in campaigns}
    elif "ad_group_id" in breakdown:
        ad_group_ids = [row["ad_group_id"] for row in rows]
        ad_groups = core.models.AdGroup.objects.filter(id__in=ad_group_ids).only(
            "id", "campaign_id", "campaign__account_id"
        )
        return {
            str(ad_group.id): EntityIds(ad_group.campaign.account_id, ad_group.campaign_id) for ad_group in ad_groups
        }
    elif "content_ad_id" in breakdown:
        content_ad_ids = [row["content_ad_id"] for row in rows]
        content_ads = core.models.ContentAd.objects.filter(id__in=content_ad_ids).only(
            "id", "ad_group__campaign_id", "ad_group__campaign__account_id"
        )
        return {
            str(content_ad.id): EntityIds(content_ad.ad_group.campaign.account_id, content_ad.ad_group.campaign_id)
            for content_ad in content_ads
        }
    else:
        raise InvalidBreakdown("Invalid filter/breakdown")
