import logging

from reports import aggregate_fields
from reports import api_helpers
from reports import redshift
from reports import exc

from api_helpers import CONTENTADSTATS_FIELD_MAPPING
from api_helpers import CONTENTADSTATS_FIELD_REVERSE_MAPPING


logger = logging.getLogger(__name__)


def query_adgroup_postclick_metrics(start_date, end_date, ad_group, media_sources):
    constraints = {
       'ad_group': ad_group.id
    }
    if media_sources:
        constraints['source'] = tuple([media_source.id for media_source in media_sources])

    return query(
        start_date,
        end_date,
        breakdown=['ad_group'],
        constraints=constraints
    )


def query_campaign_postclick_metrics(start_date, end_date, campaign, ad_groups, media_sources):
    constraints = {
        'campaign': campaign.id
    }
    if ad_groups:
        constraints['ad_group'] = [ad_group.id for ad_group in ad_groups]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    breakdown = ['campaign', 'ad_group']

    return query(
        start_date,
        end_date,
        breakdown=breakdown,
        constraints=constraints
    )


def query_campaign_sources_postclick_metrics(start_date, end_date, campaign, ad_groups, media_sources):
    constraints = {
        'campaign': campaign.id
    }
    if ad_groups:
        constraints['ad_group'] = [ad_group.id for ad_group in ad_groups]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    breakdown = ['source']

    return query(
        start_date,
        end_date,
        breakdown=breakdown,
        constraints=constraints
    )


def query_account_postclick_metrics(start_date, end_date, account, campaigns, media_sources):
    constraints = {
        'account': account.id
    }
    if campaigns:
        constraints['campaign'] = [campaign.id for campaign in campaigns]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    return query(
        start_date,
        end_date,
        breakdown=['account'],
        constraints=constraints
    )


def query_account_sources_postclick_metrics(start_date, end_date, account, campaigns, media_sources):
    constraints = {
        'account': account.id
    }
    if campaigns:
        constraints['campaign'] = [campaign.id for campaign in campaigns]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    return query(
        start_date,
        end_date,
        breakdown=['source'],
        constraints=constraints
    )


def query_all_accounts_postclick_metrics(start_date, end_date, accounts, media_sources):
    constraints = {}
    if accounts:
        constraints['account'] = [acc.id for acc in accounts]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    return query(
        start_date,
        end_date,
        breakdown=['account'],
        constraints=constraints
    )


def query_all_accounts_source_postclick_metrics(start_date, end_date, accounts, media_sources):
    constraints = {}
    if accounts:
        constraints['account'] = [acc.id for acc in accounts]
    if media_sources:
        constraints['source'] = [media_source.id for media_source in media_sources]

    return query(
        start_date,
        end_date,
        breakdown=['source'],
        constraints=constraints
    )


def query(start_date, end_date, breakdown=None, **constraints):
    if breakdown and len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    results = redshift.query_contentadstats(
        start_date,
        end_date,
        aggregate_fields.ALL_AGGREGATE_FIELDS,
        CONTENTADSTATS_FIELD_MAPPING,
        breakdown,
        constraints)

    if breakdown:
        return [_transform_row(row) for row in results]

    return _transform_row(results)


def _transform_row(row):
    result = {}
    for name, val in row.items():
        name = CONTENTADSTATS_FIELD_REVERSE_MAPPING.get(name, name)

        val = aggregate_fields.transform_val(name, val)
        name = aggregate_fields.transform_name(name)

        result[name] = val

    return result
