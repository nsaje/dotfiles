from utils.sort_helper import dissect_order, sort_rows_by_order_and_archived

from dash.dashapi import loaders
from dash.dashapi import augmenter
from dash.dashapi.helpers import apply_offset_limit


"""
All query functions return rows only filled with fields that were relevant to query execution and ordering.
Besides that they return a loader, that can be used to fill in other fields.

General signature of query_* functions:

def query_*(base_query_sets, show_archived, order, offset, limit):
   ...
   return rows, loader
"""


def query_accounts(accounts_qs, filtered_sources_qs, show_archived, order, offset, limit):
    accounts_qs = accounts_qs.filter_by_sources(filtered_sources_qs)

    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(accounts_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.AccountsLoader, 'account_id', augmenter.augment_row_account)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(accounts_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.AccountsLoader, 'account_id', augmenter.augment_row_account)
    else:
        raise Exception("This order field name is not supported")

    return rows, loader


def query_campaigns(campaigns_qs, filtered_sources_qs, show_archived, order, offset, limit):
    campaigns_qs = campaigns_qs.filter_by_sources(filtered_sources_qs)

    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(campaigns_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.CampaignsLoader, 'campaign_id', augmenter.augment_row_campaign)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(campaigns_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.CampaignsLoader, 'campaign_id', augmenter.augment_row_campaign)
    else:
        raise Exception("This order field name is not supported")

    return rows, loader


def query_ad_groups(ad_groups_qs, filtered_sources_qs, show_archived, order, offset, limit):
    ad_groups_qs = ad_groups_qs.filter_by_sources(filtered_sources_qs)

    _, order_field = dissect_order(order)
    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(ad_groups_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.AdGroupsLoader, 'ad_group_id', augmenter.augment_row_ad_group)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(ad_groups_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.AdGroupsLoader, 'ad_group_id', augmenter.augment_row_ad_group)
    else:
        raise Exception("This order field name is not supported")

    return rows, loader


def query_content_ads(content_ads_qs, filtered_sources_qs, show_archived, order, offset, limit):
    content_ads_qs = content_ads_qs.filter_by_sources(filtered_sources_qs)

    _, order_field = dissect_order(order)

    if order_field in ('name', 'title', 'url', 'display_url', 'brand_name', 'description', 'call_to_action',
                       'label', 'state', 'status', 'batch_name', 'upload_time'):
        rows, loader = _query_content_ads_ordered_by_anything(content_ads_qs, filtered_sources_qs, show_archived,
                                                              order, offset, limit)
    else:
        raise Exception("This order field name is not supported")

    return rows, loader


def query_sources(sources_qs, ad_groups_sources, show_archived, order, offset, limit):
    # show_archived is not used because group sources passed are already cleaned of archived items in advance
    # we still require this parameter as it is a part of the api

    sources_qs = sources_qs.filter(adgroupsource__in=ad_groups_sources).distinct()

    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_sources_ordered_by_name(sources_qs, ad_groups_sources,
                                                      order, offset, limit)
    elif order_field in ('status', 'state', 'min_bid_cpc', 'max_bid_cpc', 'daily_budget'):
        rows, loader = _query_sources_ordered_by_settings(sources_qs, ad_groups_sources,
                                                          order, offset, limit)
    else:
        raise Exception("This order field name is not supported")

    return rows, loader


def _query_sources_ordered_by_name(sources_qs, ad_group_sources, order, offset, limit):
    prefix, _ = dissect_order(order)
    sources_qs = apply_offset_limit(sources_qs.order_by(order, prefix + 'pk'), offset, limit)

    loader = loaders.SourcesLoader(sources_qs, ad_group_sources)

    rows = []
    for source in loader.objs_qs:
        row = {'source_id': source.id}
        augmenter.augment_row_source(row, source)
        rows.append(row)

    return rows, loader


def _query_sources_ordered_by_settings(sources_qs, ad_group_sources, order, offset, limit):
    loader = loaders.SourcesLoader(sources_qs, ad_group_sources)

    rows = []
    for source_id, settings in loader.settings_map.iteritems():
        source = loader.objs_map[source_id]

        row = {'source_id': source_id}
        augmenter.augment_row_source(row, source, settings)

        rows.append(row)

    prefix, _ = dissect_order(order)
    rows = sort_rows_by_order_and_archived(rows, [order, prefix + 'name', prefix + 'source_id'])
    rows = apply_offset_limit(rows, offset, limit)

    return rows, loader


def _query_general_ordered_by_status(objs_qs, filtered_sources_qs, show_archived, order, offset, limit,
                                     loader_cls, obj_id_key, augment_fn):
    loader = loader_cls(objs_qs, filtered_sources_qs)
    rows = []

    for obj_id, obj in loader.objs_map.iteritems():

        settings = loader.settings_map[obj_id]
        # exclude archived
        if not show_archived and settings.archived:
            continue

        row = {obj_id_key: obj_id}
        augment_fn(row, obj, settings=settings, status=loader.status_map[obj_id])
        rows.append(row)

    prefix, _ = dissect_order(order)
    rows = sort_rows_by_order_and_archived(rows, [order, prefix + 'name', prefix + obj_id_key])
    rows = apply_offset_limit(rows, offset, limit)

    return rows, loader


def _query_general_ordered_by_name(objs_qs, filtered_sources_qs, show_archived, order, offset, limit,
                                   loader_cls, obj_id_key, augment_fn):
    if not show_archived:
        objs_qs = objs_qs.exclude_archived()

    prefix, _ = dissect_order(order)

    objs_qs = objs_qs.order_by(order, prefix + 'pk')
    objs_qs = apply_offset_limit(objs_qs, offset, limit)

    loader = loader_cls(objs_qs, filtered_sources_qs)

    rows = []
    for obj in loader.objs_qs:
        row = {obj_id_key: obj.id}
        augment_fn(row, obj)
        rows.append(row)

    return rows, loader


def _query_content_ads_ordered_by_anything(content_ads_qs, filtered_sources_qs, show_archived, order, offset, limit):
    order_prefix, order_field = dissect_order(order)
    order_by_batch = order_field in ('batch_name', 'upload_time')

    order_to_field = {
        'name': 'title',
        'status': 'state',
        'batch_name': 'batch__name',
        'upload_time': 'batch__created_dt',
    }

    if order_field in order_to_field:
        order = order_prefix + order_to_field[order_field]

    if not show_archived:
        content_ads_qs = content_ads_qs.exclude_archived()

    content_ads_qs = content_ads_qs.order_by(order, order_prefix + 'title', order_prefix + 'pk')
    content_ads_qs = apply_offset_limit(content_ads_qs, offset, limit)

    loader = loaders.ContentAdsLoader(content_ads_qs, filtered_sources_qs)

    rows = []
    for content_ad in loader.objs_qs:
        row = {'content_ad_id': content_ad.id}
        augmenter.augment_row_content_ad(
            row,
            content_ad=loader.objs_map[content_ad.id],
            batch=loader.batch_map[content_ad.id] if order_by_batch else None
        )
        rows.append(row)

    return rows, loader
