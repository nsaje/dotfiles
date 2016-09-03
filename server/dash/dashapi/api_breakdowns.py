import copy

from utils import exc
from utils import sort_helper

from stats.constants import get_target_dimension, get_base_dimension
from dash.constants import Level

from dash.dashapi import queries
from dash.dashapi import loaders
from dash.dashapi import augmenter
from dash.dashapi import helpers
from dash.dashapi import data_helper
from dash.views.helpers import get_active_ad_group_sources
from dash import models


def query(level, breakdown, constraints, parents, order, offset, limit):
    """
    Queries breakdowns by dash data.

    NOTE: special attention is given on how querysets are constructed and that they are not executed if not necessary.
    """

    rows = []

    filtered_sources = constraints['filtered_sources']
    show_archived = constraints['show_archived']

    params = {'show_archived': show_archived, 'order': order, 'offset': offset, 'limit': limit}

    if level is Level.ALL_ACCOUNTS:
        allowed_accounts = constraints['allowed_accounts']
        model = models.Account

        if breakdown == ['account_id']:
            rows, loader = queries.query_accounts(allowed_accounts, filtered_sources, **params)
            augmenter.augment_accounts(rows, loader, is_base_level=True)

        elif breakdown == ['source_id']:
            rows, loader = queries.query_sources(filtered_sources, get_active_ad_group_sources(model, allowed_accounts),
                                                 **params)
            augmenter.augment_sources(rows, loader, is_base_level=True)

        elif breakdown == ['account_id', 'source_id']:
            for parent in parents:
                group_rows, loader = queries.query_sources(
                    filtered_sources,
                    get_active_ad_group_sources(model, allowed_accounts.filter(pk=parent['account_id'])),
                    **params)
                augmenter.augment_sources(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'account_id']:
            for parent in parents:
                group_rows, loader = queries.query_accounts(
                    allowed_accounts, filtered_sources.filter(pk=parent['source_id']), **params)
                augmenter.augment_accounts(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['account_id', 'campaign_id']:
            for parent in parents:
                group_rows, loader = queries.query_campaigns(
                    constraints['allowed_campaigns'].filter(account_id=parent['account_id']), filtered_sources,
                    **params)
                augmenter.augment_campaigns(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'campaign_id']:
            for parent in parents:
                group_rows, loader = queries.query_campaigns(
                    constraints['allowed_campaigns'], filtered_sources.filter(pk=parent['source_id']),
                    **params)
                augmenter.augment_campaigns(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        else:
            raise exc.InvalidBreakdownError()

    elif level is Level.ACCOUNTS:
        account = constraints['account']
        allowed_campaigns = constraints['allowed_campaigns']

        if breakdown == ['campaign_id']:
            rows, loader = queries.query_campaigns(allowed_campaigns, filtered_sources, **params)
            augmenter.augment_campaigns(rows, loader, is_base_level=True)

        elif breakdown == ['source_id']:
            rows, loader = queries.query_sources(filtered_sources, get_active_ad_group_sources(models.Account, [account]),
                                                 **params)
            augmenter.augment_sources(rows, loader, is_base_level=True)

        elif breakdown == ['campaign_id', 'source_id']:
            for parent in parents:
                group_rows, loader = queries.query_sources(
                    filtered_sources,
                    get_active_ad_group_sources(models.Campaign, allowed_campaigns.filter(pk=parent['campaign_id'])),
                    **params)
                augmenter.augment_sources(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'campaign_id']:
            for parent in parents:
                group_rows, loader = queries.query_campaigns(
                    allowed_campaigns, filtered_sources.filter(pk=parent['source_id']), **params)
                augmenter.augment_campaigns(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['campaign_id', 'ad_group_id']:
            for parent in parents:
                group_rows, loader = queries.query_ad_groups(
                    constraints['allowed_ad_groups'].filter(campaign_id=parent['campaign_id']),
                    filtered_sources, **params)
                augmenter.augment_ad_groups(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'ad_group_id']:
            for parent in parents:
                group_rows, loader = queries.query_ad_groups(
                    constraints['allowed_ad_groups'],
                    filtered_sources.filter(pk=parent['source_id']), **params)
                augmenter.augment_ad_groups(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        else:
            raise exc.InvalidBreakdownError()

    elif level is Level.CAMPAIGNS:
        campaign = constraints['campaign']
        ad_groups = constraints['allowed_ad_groups']

        if breakdown == ['ad_group_id']:
            rows, loader = queries.query_ad_groups(ad_groups, filtered_sources, **params)
            augmenter.augment_ad_groups(rows, loader, is_base_level=True)

        elif breakdown == ['source_id']:
            rows, loader = queries.query_sources(filtered_sources,
                                                 get_active_ad_group_sources(models.Campaign, [campaign]),
                                                 **params)
            augmenter.augment_sources(rows, loader, is_base_level=True)

        elif breakdown == ['ad_group_id', 'source_id']:
            for parent in parents:
                group_rows, loader = queries.query_sources(
                    filtered_sources,
                    get_active_ad_group_sources(models.AdGroup, ad_groups.filter(pk=parent['ad_group_id'])),
                    **params)
                augmenter.augment_sources(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'ad_group_id']:
            for parent in parents:
                group_rows, loader = queries.query_ad_groups(
                    ad_groups, filtered_sources.filter(pk=parent['source_id']), **params)
                augmenter.augment_ad_groups(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['source_id', 'content_ad_id']:
            for parent in parents:
                group_rows, loader = queries.query_content_ads(
                    constraints['allowed_content_ads'],
                    filtered_sources.filter(pk=parent['source_id']), **params)
                augmenter.augment_content_ads(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['ad_group_id', 'content_ad_id']:
            for parent in parents:
                group_rows, loader = queries.query_content_ads(
                    constraints['allowed_content_ads'].filter(ad_group_id=parent['ad_group_id']),
                    filtered_sources, **params)
                augmenter.augment_content_ads(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        else:
            raise exc.InvalidBreakdownError()

    elif level is Level.AD_GROUPS:
        ad_group = constraints['ad_group']
        content_ads = constraints['allowed_content_ads']

        if breakdown == ['content_ad_id']:
            rows, loader = queries.query_content_ads(content_ads, filtered_sources, **params)
            augmenter.augment_content_ads(rows, loader, is_base_level=True)

        elif breakdown == ['source_id']:
            rows, loader = queries.query_sources(filtered_sources,
                                                 get_active_ad_group_sources(models.AdGroup, [ad_group]),
                                                 **params)
            augmenter.augment_sources(rows, loader, is_base_level=True)

        elif breakdown == ['source_id', 'content_ad_id']:
            for parent in parents:
                group_rows, loader = queries.query_content_ads(content_ads,
                                                               filtered_sources.filter(pk=parent['source_id']),
                                                               **params)
                augmenter.augment_content_ads(group_rows, loader)
                rows.extend(helpers.apply_parent_to_rows(parent, group_rows))

        elif breakdown == ['content_ad_id', 'source_id']:
            # TODO currently sources are not prefiltered by content ad, we could select that based on content ad sources
            # the result is that all sources of the ad group are shown
            same_rows, loader = queries.query_sources(
                filtered_sources, get_active_ad_group_sources(models.AdGroup, [ad_group]), **params)
            augmenter.augment_sources(same_rows, loader)

            for parent in parents:
                copied_rows = []
                for row in same_rows:
                    copied_rows.append(copy.copy(row))
                rows.extend(helpers.apply_parent_to_rows(parent, copied_rows))
        else:
            # TODO: content ad sources, publishers
            raise NotImplementedError("Breakdown is not yet supported")

    return rows


def augment(rows, level, breakdown, constraints):
    """
    NOTE: does not handle allowed objects
    """

    target_dimension = get_target_dimension(breakdown)
    parent_dimension = get_base_dimension(breakdown[:-1])  # we expect max [base_level, target_level] breakdown depth
    filtered_sources = constraints['filtered_sources']

    if target_dimension in ('account_id', 'campaign_id', 'ad_group_id', 'content_ad_id'):
        for parent_id, breakdown_rows, target_ids in helpers.group_rows_by_parents(
                rows, parent_dimension, target_dimension, flat=('source_id' != parent_dimension)):

            sources = filtered_sources
            if 'source_id' == parent_dimension:
                # parent_id is only needed in case when source_id dimension is one of the parent dimensions
                # this is the only dimension affecting the state of child dimensions.
                sources = sources.filter(pk=parent_id)

            if target_dimension == 'account_id':
                accounts = models.Account.objects.filter(pk__in=target_ids)
                loader = loaders.AccountsLoader(accounts, sources)
                augmenter.augment_accounts(breakdown_rows, loader, is_base_level=(parent_dimension is None))

            elif target_dimension == 'campaign_id':
                campaigns = models.Campaign.objects.filter(pk__in=target_ids)
                loader = loaders.CampaignsLoader(campaigns, sources)
                augmenter.augment_campaigns(breakdown_rows, loader, is_base_level=(parent_dimension is None))

            elif target_dimension == 'ad_group_id':
                ad_groups = models.AdGroup.objects.filter(pk__in=target_ids)
                loader = loaders.AdGroupsLoader(ad_groups, sources)
                augmenter.augment_ad_groups(breakdown_rows, loader, is_base_level=(parent_dimension is None))

            elif target_dimension == 'content_ad_id':
                content_ads = models.ContentAd.objects.filter(pk__in=target_ids)
                loader = loaders.ContentAdsLoader(content_ads, sources)
                augmenter.augment_content_ads(breakdown_rows, loader, is_base_level=(parent_dimension is None))
    elif target_dimension == 'source_id':
        for parent_id, breakdown_rows, target_ids in helpers.group_rows_by_parents(
                rows, parent_dimension, target_dimension, flat=(parent_dimension is None)):

            sources, ad_group_sources = helpers.select_active_ad_group_sources(
                level, constraints, parent_dimension, parent_id, target_ids)
            loader = loaders.SourcesLoader(sources, ad_group_sources)
            augmenter.augment_sources(breakdown_rows, loader, is_base_level=(parent_dimension is None))

    return rows


def query_missing_rows(rows, level, breakdown, constraints, parents, order, offset, limit, structure_with_stats):
    """
    Adds rows that are in dash but do not have statistics.
    """

    if structure_with_stats is None:
        return rows

    target_dimension = get_target_dimension(breakdown)
    parent_dimension = get_base_dimension(breakdown[:-1])  # we expect max [base_level, target_level] breakdown depth
    filtered_sources = constraints['filtered_sources']

    prefix, _ = sort_helper.dissect_order(order)
    order = prefix + 'name'

    flat = parent_dimension is None
    for parent_id, _, target_ids in helpers.group_rows_by_parents(
            rows,
            parent_dimension, target_dimension,
            flat=flat,
            parents=parents):

        if not helpers.needs_to_query_additional_rows(target_ids, limit):
            continue

        # used ids (the ones with stats) that need to be excluded when querying
        all_excluded_ids = helpers.get_used_ids(
            target_dimension, structure_with_stats, parent_dimension, parent_id)

        new_offset, new_limit = helpers.get_adjusted_limits_for_additional_rows(
            target_ids, all_excluded_ids, offset, limit)

        new_constraints = copy.copy(constraints)
        allowed_field = helpers.get_allowed_constraints_field(target_dimension)
        new_constraints[allowed_field] = constraints[allowed_field].exclude(pk__in=all_excluded_ids)

        parents = [{parent_dimension: parent_id}] if parent_dimension else None

        rows.extend(query(level, breakdown, new_constraints, parents, order, new_offset, new_limit))

    return rows


def get_totals(level, breakdown, constraints):
    target_dimension = get_target_dimension(breakdown)

    row = {}
    if breakdown == ['source_id']:
        sources, ad_group_sources = helpers.select_active_ad_group_sources(level, constraints, None, None, None)
        loader = loaders.SourcesLoader(sources, ad_group_sources)

        min_cpcs = [v['min_bid_cpc'] for v in loader.settings_map.values() if v['min_bid_cpc'] is not None]
        row['min_bid_cpc'] = min(min_cpcs) if min_cpcs else none

        max_cpcs = [v['max_bid_cpc'] for v in loader.settings_map.values() if v['max_bid_cpc'] is not None]
        row['max_bid_cpc'] = max(max_cpcs) if max_cpcs else None

        row['daily_budget'] = sum([v['daily_budget'] for v in loader.settings_map.values() if v['daily_budget']])

    return row
